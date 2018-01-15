# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.3.28

import json

from twisted.enterprise import adbapi
from twisted.internet import defer, reactor
from twisted.internet.protocol import Factory
from twisted.web.http import HTTPFactory

import freetime.aio.mysql as ftmysql
import freetime.aio.redis as ftred
import freetime.util.log as ftlog
from freetime.core.protocol import FTUDPQueryProtocol
from freetime.style import ide_debug
from freetime.util.cache import lfu_cache
from freetime.util.metaclasses import MultiDict, MultiList

# key:redis_pool name  value:redis_pool
# {"config":...,...}
redis_pool_map = {}
# key:redis_pool name  value: redis connection config info, just for some reconnect
redis_config_map = {}
_redis_pool_count = 0

# key:mysql_connection name  value:mysql_connection
# {"tydata0":...,...}
mysql_pool_map = {}

# key:serverid  value:server struct
# {"CO01":{...}, "CO02":{...}, ... }
server_map = {}

# key:target serverid   value:udp query protocol
client_query_udp_map = {}

# key:server_type  value:[server_id1, server_id2...]
# {"CO":["CO01","CO02"], "UT":["UT01","UT02], ...}
server_type_map = MultiDict()

# key:cmd, value:server_type
# {"quick_start":"RO"}
# cmd_route_map = {}  move to the second layer

# key:data key name, value:...
global_config = {}

# 用于服务间的内部通信,对于普通进程,存储了AgentID标识的Agent连接
# 对于Agent进程，存储了和其他Agent之间以及连接的Service的连接protocol
# key:server_id, value:tcp protocol
serverid_protocol_map = {}


def initFromRedis(svrid, conf):
    # load server,redis,cmd,glboal config... 
    ftlog.trace("FreeTime init from redis:", conf[0], conf[1], conf[2])
    import redis
    _rs = redis.StrictRedis(host=conf[0], port=conf[1], db=conf[2])
    sc, rc, glc = _rs.mget("freetime:server", "freetime:db", "freetime:global")
    try:
        _rs.close()
        del _rs
    except:
        pass
    _initByData(svrid, sc, rc, glc, conf)


def _initByData(svrid, sc, rc, glc, conf):
    global global_config
    global_config.update(json.loads(glc))

    # init log system...
    log_file = "%s.log" % svrid
    log_path = global_config["log_path"]
    ftlog.trace_stdout("FreeTime service(%s) up, log to %s/%s..." % (svrid, log_path, log_file))
    log_level = int(global_config.get("log_level", 0))
    # skip twisted noisy in no-debug level...
    if log_level > 0:
        Factory.noisy = False
    if ide_debug():
        ftlog.initLog(log_file, log_path, log_level)
        # ftlog.initLog(log_file, 'stdout', log_level)
    else:
        ftlog.initLog(log_file, log_path, log_level)

    # init maps...
    ftlog.info("init from redis:", conf[0], conf[1], conf[2])
    _initServerMap(json.loads(sc))
    dbs = json.loads(rc)
    global_config['freetime:db'] = dbs
    if "redis" in dbs:
        _initRedisPoolMap(svrid, conf, dbs["redis"])
    if "mysql" in dbs:
        _initMysqlPoolMap(svrid, conf, dbs["mysql"])


def _initServerMap(serverconf):
    # init server maps...
    for s in serverconf:
        sid = s["type"] + s["id"]
        server_map[sid] = s
        if s["type"] in server_type_map:
            server_type_map[s["type"]].append(sid)
        else:
            server_type_map[s["type"]] = [sid]
    ftlog.debug(server_type_map)


@defer.inlineCallbacks
def _initRedisPool(name, h, p, dbid, size):
    global _redis_pool_count
    ftlog.debug('REDIS GO', name, h, p, dbid, size)

    from freetime.util.txredis.client import RedisClientFactory
    factory = RedisClientFactory(db=dbid)
    if h == "unix_socket":
        reactor.connectUNIX(p, factory)
    else:
        reactor.connectTCP(h, p, factory)
    yield factory.deferred
    _rp = factory

    redis_pool_map[name] = _rp
    redis_config_map[name] = [h, p, dbid]
    ftlog.info('REDIS OK', len(redis_pool_map), '/', _redis_pool_count, name, _rp)
    if len(redis_pool_map) == _redis_pool_count:
        import freetime.entity.service as ftsvr
        ftsvr._runInitFun()


def _initRedisPoolMap(sid, conf, redisconf):
    rdbs = []
    # init other redis pool by server config...
    svrconf = getServerConf(sid)
    psize = 30
    if "redis" in svrconf:
        cr = svrconf["redis"]
        for n in redisconf:
            if n in cr:
                c = redisconf[n]
                psize = c[3]
                rdbs.append([n, c[0], c[1], c[2], c[3]])
    rdbs.append(["config", conf[0], conf[1], conf[2], psize])

    global _redis_pool_count
    _redis_pool_count = len(rdbs)
    for rdb in rdbs:
        _initRedisPool(rdb[0], rdb[1], rdb[2], rdb[3], rdb[4])


def _initMysqlPool(name, dbhost, dbport, dbname, dbuser, dbpwd):
    ftlog.debug('MYSQL INIT : ', name, dbhost, dbport, dbname, dbuser, dbpwd)
    rconn = adbapi.ConnectionPool('pymysql', db=dbname, user=dbuser, passwd=dbpwd,
                                  host=dbhost, port=dbport, charset='utf8',
                                  use_unicode=True, cp_reconnect=True)
    mysql_pool_map[name] = rconn
    ftlog.debug('MYSQL', name, rconn)


def _initMysqlPoolMap(sid, conf, mysqlconf):
    # dump all mysql infos 
    rkeys = mysqlconf.keys()
    rkeys.sort()
    for k in rkeys:
        c = mysqlconf[k]

    svrconf = getServerConf(sid)
    if "mysql" in svrconf:
        cr = svrconf["mysql"]
        for n in mysqlconf:
            if n in cr:
                c = mysqlconf[n]
                _initMysqlPool(n, c[0], c[1], c[2], c[3], c[4])
        ftmysql.keepAlive(mysql_pool_map)


def getServerConf(sid):
    try:
        return server_map[sid]
    except:
        ftlog.error("undefined server_id:", sid)
        return None


# Use lfu cache,reduce config redis I/O... 
@lfu_cache(maxsize=1000, cache_key_args_index=0)
def getConf(confname):
    value = ftred.runCmd(redis_pool_map["config"], "GET", confname)
    if value != None:
        value = json.loads(value)
        if isinstance(value, dict):
            value = MultiDict(value)
        if isinstance(value, list):
            value = MultiList(value)
    return value


def getConfNoCache(*cmds):
    value = ftred.runCmd(redis_pool_map["config"], *cmds)
    return value


def _init_query_udp(target_svr_id, target_pro_name):
    try:
        tip = server_map[target_svr_id]["ip"]
        tport = server_map[target_svr_id]["protocols"]["server"][target_pro_name]
        udpqp = FTUDPQueryProtocol(tip, tport)
        reactor.listenUDP(0, udpqp, maxPacketSize=65536)
        client_query_udp_map[target_svr_id] = udpqp
    except:
        ftlog.error("init query-udp error:", target_svr_id, target_pro_name)


def protoParser(protos, proto_func, ptype):
    """
        根据server.json中配置的server和client字段，进行
        监听和连接操作
        #service server protocol config example:
        "protocols": { 
            "server":{"co-udp":5000, "co-tcp":5001},
            "client":{"query-udp":["LO*:co-udp"]}
        } 
        这里只处理业务进程的protocol，
        Agent的相关处理在support.tcpagent.wrapper中
    """
    is_server = (ptype == "server")
    if ptype not in protos:
        return
    ps = protos[ptype]
    for p in ps:
        # get class by proto short name...
        _c = proto_func(p)
        if is_server:
            if p.endswith("-udp"):
                pinst = _c()
                reactor.listenUDP(ps[p], pinst)
            if p.endswith("-tcp"):
                factory = Factory()
                factory.protocol = _c
                reactor.listenTCP(ps[p], factory)
            if p.endswith("-http"):
                def _dummy(*args, **argd):
                    pass

                factory = HTTPFactory()
                factory.log = _dummy
                factory.protocol = _c
                reactor.listenTCP(ps[p], factory)
        else:
            if p == "query-udp":
                for target in ps[p]:
                    target_server, target_pro_name = target.split(":")
                    if target_server.endswith("*"):
                        tss = server_type_map[target_server[:-1]]
                        for target_svr_id in tss:
                            _init_query_udp(target_svr_id, target_pro_name)
                    else:
                        _init_query_udp(target_server, target_pro_name)
