# -*- coding=utf-8

import freetime.entity.config as ftcon
import freetime.util.log as ftlog
from freetime.aio import mysql
from poker.entity.configure import gdata
from poker.protocol.rpccore import markRpcCall, RPC_FIRST_SERVERID

_MYSQLPIDS = {}  # key=dbname, value = [serverId,...]


def _getServerIdOfMysql(userId, dbname):
    serverIds = _MYSQLPIDS.get(dbname, None)
    if not serverIds:
        serverIds = []
        for sid, sdef in gdata.allServersMap().items():
            ftlog.debug('sid, sdef=', sid, sdef)
            if sdef['type'] == gdata.SRV_TYPE_UTIL:
                mydbs = sdef.get('mysql', [])
                if dbname in mydbs:
                    serverIds.append(sid)
        serverIds.sort()
        _MYSQLPIDS[dbname] = serverIds
    ftlog.debug('dbname=', dbname, 'serverIds=', serverIds)
    sid = serverIds[userId % (len(serverIds))]
    return sid


def _queryMysql00(userId, dbname, sqlstr):
    '''
    在拥有mysql的进程中，取得一个进程
    MYSQL只在UT进程进行连接,因MYSQL的请求量不大,为降低MYSQL数据库的连接数,只有ID为1~99的UT进程有MYSQL链接
    '''
    serverId = _getServerIdOfMysql(userId, dbname)
    data = _queryMysql(serverId, dbname, sqlstr)
    return data


@markRpcCall(groupName=RPC_FIRST_SERVERID, lockName="", syncCall=1)
def _queryMysql(serverId, dbname, sqlstr):
    mysqlconn = ftcon.mysql_pool_map[dbname]
    tabledata = mysql.query(mysqlconn, sqlstr)
    data = _get_table_data(tabledata, 0, 0)
    return data


def _get_table_data(datas, row, col):
    try:
        if datas and len(datas) > 0:
            dstr = datas[row][col]
            if dstr[0] == '{' and dstr[-1] == '}':
                return dstr
        ftlog.warn('WARN, the mysql data error !!', datas)
    except:
        ftlog.warn('WARN, the mysql data not found !!', datas)
    return None
