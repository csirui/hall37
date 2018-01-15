# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.3.28

import stackless

import freetime.aio.http as fthttp
import freetime.aio.mysql as ftmysql
import freetime.aio.redis as ftred
import freetime.aio.udp as ftudp
import freetime.entity.config as ftcon
import freetime.support.tcpagent.wrapper as ftagent
import freetime.util.log as ftlog
from freetime.core.exception import FTException
from freetime.core.reactor import mainloop, exitmainloop, REACTOR_RUN_NORMAL
from freetime.core.tasklet import FTTasklet, _tasklet_schedule_cb

_init_fun = None


# _lock_pipe = ftlock.FTLock("lock_redis_pipe")


def doMySql(poolname, sqlstr, sql_arg_list=[]):
    conn = ftcon.mysql_pool_map.get(poolname, None)
    if conn == None:
        raise FTException("doMySql:poolname " + str(poolname) + "undefined.")
    return ftmysql.query(conn, sqlstr, sql_arg_list)


def doRedis(poolname, *argl, **argd):
    conn = ftcon.redis_pool_map.get(poolname, None)
    if conn == None:
        raise FTException("doRedis:poolname [" + str(poolname) + "] undefined.")
    return ftred.runCmd(conn, *argl, **argd)


# pipeline()及对pipeline执行redis操作，需要锁起来保证tasklet不重入
# 真正pipeline执行网络请求前解锁，这样不影响效率
# def getRedisPipe(poolname):
#     conn = ftcon.redis_pool_map.get(poolname, None)
#     if conn == None :
#         raise FTException("getRedisPipe:poolname " + str(poolname) + "undefined.")
#     _lock_pipe.lock()
#     return ftred.getPipeLine(conn)
# 
# 
# def doRedisPipe(pipeline):
#     _lock_pipe.unlock()
#     return ftred.pipeCmd(pipeline)


def doHttp(method, url, header={}, body="", conntimeout=2, timeout=2):
    return fthttp.runHttp(method, url, header, body, conntimeout, timeout)


def doUdpQuery(target_server_id, data, timeout=1):
    client = ftcon.client_query_udp_map.get(target_server_id, None)
    if client == None:
        raise FTException("doUdpQuery:target_server_id " + str(target_server_id) + " undefined.")
    return ftudp.sendQuery(client, data, timeout)


def getId():
    return ftcon.global_config["server_id"]


def getTaskUdpSrc():
    _fttask = stackless.getcurrent()._fttask
    return _fttask.udpsrc


def getTaskPack():
    _fttask = stackless.getcurrent()._fttask
    return _fttask.pack


def getTaskRunArg():
    _fttask = stackless.getcurrent()._fttask
    return _fttask.run_args


def getConcurrentTaskCount():
    _fttask = stackless.getcurrent()._fttask
    return _fttask.concurrent_task_count


def _initProtocol(sid, proto_func):
    svrconf = ftcon.getServerConf(sid)
    if not svrconf:
        ftlog.error("server(%s) config not found,bye" % sid)
        import sys
        sys.exit(0)

    protos = svrconf.get("protocols", None)

    if sid.startswith("AG"):
        # listen and connect other agent
        ftagent.connect_agent_eachother(sid)
    else:
        if protos:
            ftcon.protoParser(protos, proto_func, "server")
            ftcon.protoParser(protos, proto_func, "client")
        # connect agent
        if "agent" in svrconf:
            ftagent.connect_agent(sid, proto_func)


def _runServiceById(sid, proto_func):
    ftlog.info("run service:", sid)
    _initProtocol(sid, proto_func)
    stackless.set_schedule_callback(_tasklet_schedule_cb)
    if REACTOR_RUN_NORMAL:
        mainloop()
        return
    stackless.tasklet(mainloop)()
    stackless.run()


def _runInitFun():
    global _init_fun
    if callable(_init_fun):
        FTTasklet.create([], {"handler": _init_fun})
    _init_fun = None


# 要求自定义的protocol模块，实现getProtoClassByName方法
def run(*argl, **argd):
    global _init_fun
    ftlog.trace("FreeTime run with:", argl, argd)
    ftcon.global_config["server_id"] = argd["server_id"]
    ftcon.initFromRedis(argd["server_id"], argd["config_redis"])
    _pfunc = argd["protocols"]
    _init_fun = argd.get("init_fun", None)
    _runServiceById(argd["server_id"], _pfunc.getProtoClassByName)


def terminate():
    exitmainloop()
