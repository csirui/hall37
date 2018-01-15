# -*- coding: utf-8 -*-
"""
Created on 2015-5-12
@author: zqh
"""

import json

from datetime import datetime

import freetime.aio.redis as ftred
import freetime.entity.config as ftcon
import freetime.util.log as ftlog
from poker.entity.dao import daoconst
from poker.entity.dao.lua_scripts import room_scripts
from poker.util import keywords
from poker.util import reflection

__luascripts = {}
__user_redis_conns = []  # 用户数据的REDIS链接, 按userid取模进行数据的存储
__user_redis_conns_len = 0
__table_redis_conns = []  # 桌子数据的REDIS链接, 按userid取模进行数据的存储
__table_redis_conns_len = 0
__mix_redis_conn = None
__forbidden_redis_conn = None
__keymap_redis_conn = None
__paydata_redis_conn = None
__geo_redis_conn = None
__config_redis_conn = None
__online_redis_conn = None
__replay_redis_conn = None
__rank_redis_conn = None
__dizhu_redis_conn = None
__bi_redis_conn = None

_REDIS_CMD_PPS_ = 0
_REDIS_CMDS_ = {}
_REDIS_COUNT_ = 0
_REDIS_COUNT_TIME_ = datetime.now()


def _redisCmdPps(group, cmds):
    global _REDIS_CMDS_, _REDIS_COUNT_, _REDIS_COUNT_TIME_
    try:
        if not group in _REDIS_CMDS_:
            _REDIS_CMDS_[group] = {}
        rgroup = _REDIS_CMDS_[group]

        rcmd = str(cmds[0]).upper()
        if len(cmds) > 1:
            rkey = str(cmds[1]).split(':', 1)[0]
            if rkey not in rgroup:
                rgroup[rkey] = {}
            rcmds = rgroup[rkey]
            if rcmd in rcmds:
                rcmds[rcmd] += 1
            else:
                rcmds[rcmd] = 1

        _REDIS_COUNT_ += 1
    # if _REDIS_COUNT_ % _REDIS_COUNT_BLOCK_ == 0:
    #             ct = datetime.now()
    #             dt = ct - _REDIS_COUNT_TIME_
    #             dt = dt.seconds + dt.microseconds / 1000000.0
    #             pps = '%0.2f' % (_REDIS_COUNT_BLOCK_ / dt)
    #             _REDIS_COUNT_TIME_ = ct
    #             ftlog.info("REDIS_PPS", pps, 'CMDCOUNT', _REDIS_COUNT_, 'DT %0.2f' % (dt), 'CMDS', json.dumps(_REDIS_CMDS_))
    #             _REDIS_CMDS_ = {}
    except:
        ftlog.error()


def ppsCountRedisCmd():
    global _REDIS_CMDS_, _REDIS_COUNT_, _REDIS_COUNT_TIME_
    ct = datetime.now()
    dt = ct - _REDIS_COUNT_TIME_
    dt = dt.seconds + dt.microseconds / 1000000.0
    pps = '%0.2f' % (_REDIS_COUNT_ / dt)
    ftlog.hinfo("REDIS_PPS", pps, 'CMDCOUNT', _REDIS_COUNT_, 'DT %0.2f' % (dt), 'CMDS', json.dumps(_REDIS_CMDS_))
    _REDIS_COUNT_TIME_ = ct
    _REDIS_CMDS_ = {}
    _REDIS_COUNT_ = 0


def _initialize():
    global __user_redis_conns, __user_redis_conns_len, __table_redis_conns, __table_redis_conns_len
    global __mix_redis_conn, __keymap_redis_conn, __paydata_redis_conn, __geo_redis_conn
    global __config_redis_conn, __online_redis_conn, __replay_redis_conn
    global __rank_redis_conn, __dizhu_redis_conn, __bi_redis_conn
    if __user_redis_conns_len == 0:
        ftlog.debug('_initialize begin->', __name__)
        mlist = reflection.findMethodUnderModule('poker.servers.util.rpc._private', '_initialize')
        for method in mlist:
            method()
        ftlog.debug('_initialize finis->', __name__)

        loadLuaScripts(room_scripts.ALIAS_GET_BEST_TABLE_ID_LUA, room_scripts.GET_BEST_TABLE_ID_LUA)
        loadLuaScripts(room_scripts.ALIAS_UPDATE_TABLE_SCORE_LUA, room_scripts.UPDATE_TABLE_SCORE_LUA)
        __user_redis_conns = _getRedisCluster('user')
        __user_redis_conns_len = len(__user_redis_conns)
        __table_redis_conns = _getRedisCluster('table')
        __table_redis_conns_len = len(__table_redis_conns)
        __mix_redis_conn = ftcon.redis_pool_map.get('mix')
        __forbidden_redis_conn = ftcon.redis_pool_map.get('forbidden')
        __replay_redis_conn = ftcon.redis_pool_map.get('replay')
        __online_redis_conn = ftcon.redis_pool_map.get('online')
        __keymap_redis_conn = ftcon.redis_pool_map.get('keymap')
        __paydata_redis_conn = ftcon.redis_pool_map.get('paydata')
        __geo_redis_conn = ftcon.redis_pool_map.get('geo')
        __config_redis_conn = ftcon.redis_pool_map.get('config')
        __rank_redis_conn = ftcon.redis_pool_map.get('rank')
        __dizhu_redis_conn = ftcon.redis_pool_map.get('dizhu')
        __bi_redis_conn = ftcon.redis_pool_map.get('bi')
        if __bi_redis_conn == None:
            __bi_redis_conn = ftcon.redis_pool_map.get('mix')


def _getRedisCluster(dbnamehead):
    rconns = []
    for k, conn in ftcon.redis_pool_map.items():
        if k.startswith(dbnamehead):
            modid = int(k[len(dbnamehead):])
            rconns.append([modid, conn])
    rconns.sort(key=lambda x: x[0])
    if rconns:
        assert (rconns[0][0] == 0)
        assert (rconns[-1][0] == len(rconns) - 1)
        connlist = []
        for x in rconns:
            connlist.append(x[1])
        return connlist
    return []


def preLoadLuaScript(scriptModule, luaScript):
    assert (isinstance(luaScript, (str, unicode)))
    scriptName = None
    for x in dir(scriptModule):
        if luaScript == getattr(scriptModule, x):
            scriptName = x
    assert (isinstance(scriptName, (str, unicode)))
    oldsha = None
    for k in ftcon.redis_pool_map:
        conn = ftcon.redis_pool_map[k]
        shaval = ftred.runCmd(conn, 'script', 'load', luaScript)
        if oldsha == None:
            __luascripts[scriptName] = shaval
            oldsha = shaval
        else:
            assert (oldsha == shaval)
    ftlog.info('LOADSCRIPT->', oldsha, scriptName, luaScript)
    setattr(scriptModule, scriptName, scriptName)
    return oldsha


def loadLuaScripts(luaName, luaScript):
    oldsha = None
    for k in ftcon.redis_pool_map:
        conn = ftcon.redis_pool_map[k]
        shaval = ftred.runCmd(conn, 'script', 'load', luaScript)
        if oldsha == None:
            __luascripts[luaName] = shaval
            oldsha = shaval
        else:
            assert (oldsha == shaval)
    ftlog.info('LOADSCRIPT->', oldsha, luaName, luaScript)
    return oldsha


def getLuaScriptsShaVal(luaName):
    return __luascripts[luaName]


def filterValue(attr, value):
    if attr in daoconst.FILTER_KEYWORD_FIELDS:
        value = unicode(value)
        return keywords.replace(value)
    return value


def filterValues(attrlist, values):
    if (not isinstance(attrlist, list)
        or not isinstance(values, list)
        or len(attrlist) != len(values)):
        return values
    for i in xrange(len(values)):
        values[i] = filterValue(attrlist[i], values[i])
    return values


def executeUserCmd(uid, *cmds):
    assert (isinstance(uid, int) and uid > 0)
    cindex = int(uid) % __user_redis_conns_len
    if _REDIS_CMD_PPS_:
        _redisCmdPps('user', cmds)
    return ftred.runCmd(__user_redis_conns[cindex], *cmds)


def sendUserCmd(uid, *cmds):
    assert (isinstance(uid, int) and uid > 0)
    cindex = int(uid) % __user_redis_conns_len
    ftred.sendCmd(__user_redis_conns[cindex], *cmds)


def executeUserLua(uid, luaName, *cmds):
    assert (isinstance(uid, int) and uid > 0)
    cindex = int(uid) % __user_redis_conns_len
    shaval = getLuaScriptsShaVal(luaName)
    if _REDIS_CMD_PPS_:
        _redisCmdPps('user', ['EVALSHA', luaName])
    return ftred.runCmd(__user_redis_conns[cindex], 'EVALSHA', shaval, *cmds)


def _getUserDbClusterSize():
    return __user_redis_conns_len


def executeTableCmd(roomId, tableId, *cmds):
    assert (isinstance(roomId, int) and roomId > 0)
    assert (isinstance(tableId, int) and tableId >= 0)
    cindex = int(roomId) % __table_redis_conns_len
    if _REDIS_CMD_PPS_:
        _redisCmdPps('table', cmds)
    return ftred.runCmd(__table_redis_conns[cindex], *cmds)


def executeTableLua(roomId, tableId, luaName, *cmds):
    assert (isinstance(roomId, int) and roomId > 0)
    assert (isinstance(tableId, int) and tableId >= 0)
    cindex = int(roomId) % __table_redis_conns_len
    shaval = getLuaScriptsShaVal(luaName)
    if _REDIS_CMD_PPS_:
        _redisCmdPps('table', ['EVALSHA', luaName])
    return ftred.runCmd(__table_redis_conns[cindex], 'EVALSHA', shaval, *cmds)


def executeForbiddenCmd(*cmds):
    if __forbidden_redis_conn:
        if _REDIS_CMD_PPS_:
            _redisCmdPps('forbidden', cmds)
        return ftred.runCmd(__forbidden_redis_conn, *cmds)


def executeMixCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('mix', cmds)
    return ftred.runCmd(__mix_redis_conn, *cmds)


def executeMixLua(luaName, *cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('mix', ['EVALSHA', luaName])
    shaval = getLuaScriptsShaVal(luaName)
    return ftred.runCmd(__mix_redis_conn, 'EVALSHA', shaval, *cmds)


def executeRePlayCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('replay', cmds)
    return ftred.runCmd(__replay_redis_conn, *cmds)


def executeRePlayLua(luaName, *cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('replay', ['EVALSHA', luaName])
    shaval = getLuaScriptsShaVal(luaName)
    return ftred.runCmd(__replay_redis_conn, 'EVALSHA', shaval, *cmds)


def _executeOnlineCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('online', cmds)
    return ftred.runCmd(__online_redis_conn, *cmds)


def _executeOnlineLua(luaName, *cmds):
    shaval = getLuaScriptsShaVal(luaName)
    if _REDIS_CMD_PPS_:
        _redisCmdPps('online', ['EVALSHA', luaName])
    return ftred.runCmd(__online_redis_conn, 'EVALSHA', shaval, *cmds)


def _executeBiCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('bi', cmds)
    return ftred.runCmd(__bi_redis_conn, *cmds)


def _sendBiCmd(*cmds):
    ftred.sendCmd(__bi_redis_conn, *cmds)


def _executeBiLua(luaName, *cmds):
    shaval = getLuaScriptsShaVal(luaName)
    if _REDIS_CMD_PPS_:
        _redisCmdPps('bi', ['EVALSHA', luaName])
    return ftred.runCmd(__bi_redis_conn, 'EVALSHA', shaval, *cmds)


def _executeKeyMapCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('keymap', cmds)
    return ftred.runCmd(__keymap_redis_conn, *cmds)


def _executeKeyMapLua(luaName, *cmds):
    shaval = getLuaScriptsShaVal(luaName)
    if _REDIS_CMD_PPS_:
        _redisCmdPps('keymap', ['EVALSHA', luaName])
    return ftred.runCmd(__keymap_redis_conn, 'EVALSHA', shaval, *cmds)


def _executePayDataCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('paydata', cmds)
    return ftred.runCmd(__paydata_redis_conn, *cmds)


def _executePayDataLua(luaName, *cmds):
    shaval = getLuaScriptsShaVal(luaName)
    if _REDIS_CMD_PPS_:
        _redisCmdPps('paydata', ['EVALSHA', luaName])
    return ftred.runCmd(__paydata_redis_conn, 'EVALSHA', shaval, *cmds)


def _executeGeoCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('geo', cmds)
    return ftred.runCmd(__geo_redis_conn, *cmds)


def _sendGeoCmd(*cmds):
    ftred.sendCmd(__geo_redis_conn, *cmds)


def _executeGeoLua(luaName, *cmds):
    shaval = getLuaScriptsShaVal(luaName)
    if _REDIS_CMD_PPS_:
        _redisCmdPps('geo', ['EVALSHA', luaName])
    return ftred.runCmd(__geo_redis_conn, 'EVALSHA', shaval, *cmds)


def sendRankCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('rank', cmds)
    ftred.sendCmd(__rank_redis_conn, *cmds)


def executeRankCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('rank', cmds)
    return ftred.runCmd(__rank_redis_conn, *cmds)


def executeRankLua(luaName, *cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('rank', ['EVALSHA', luaName])
    shaval = getLuaScriptsShaVal(luaName)
    return ftred.runCmd(__rank_redis_conn, 'EVALSHA', shaval, *cmds)


def sendDizhuCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('dizhu', cmds)
    ftred.sendCmd(__dizhu_redis_conn, *cmds)


def executeDizhuCmd(*cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('dizhu', cmds)
    return ftred.runCmd(__dizhu_redis_conn, *cmds)


def executeDizhuLua(luaName, *cmds):
    if _REDIS_CMD_PPS_:
        _redisCmdPps('dizhu', ['EVALSHA', luaName])
    shaval = getLuaScriptsShaVal(luaName)
    return ftred.runCmd(__dizhu_redis_conn, 'EVALSHA', shaval, *cmds)
