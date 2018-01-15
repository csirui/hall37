# -*- coding=utf-8

import json

import freetime.util.log as ftlog
import poker.servers.util.direct.dbuser as _dbuser
from freetime.util.cache import lfu_time_cache
from poker.entity.dao import daobase, daoconst
from poker.entity.dao.daoconst import UserDataSchema, UserSessionSchema, \
    UserWeakSchema
from poker.protocol.rpccore import markRpcCall
from poker.servers.util.rpc._private import dataswap, user_scripts
from poker.util import strutil

_CACHE_GROUP = 'userdata'
_CACHE_SIZE = daoconst.DATA_CACHE_SIZE
_CACHE_USER_ENABLE = 0


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _checkUserData(userId, clientId=None, appId=0, session={}):
    ret = dataswap.checkUserData(userId, clientId, appId)
    if ret and session:
        _setSessionDatas(userId, session)
    return ret


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _updateUserDataAuthorTime(userId):
    return _dbuser._updateUserDataAuthorTime(userId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _updateUserDataAliveTime(userId):
    return _dbuser._updateUserDataAliveTime(userId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _updateUserGameDataAuthorTime(userId, gameId):
    return _dbuser._updateUserGameDataAuthorTime(userId, gameId)


@lfu_time_cache(maxsize=_CACHE_SIZE, mainindex=0, subindex=1, group=_CACHE_GROUP)
def _cacheSession(userId, dataKey):
    return _getSessionDataRedis(userId, dataKey)


def _getSessionDataRedis(userId, dataKey):
    values = daobase.executeUserCmd(userId, 'HMGET', dataKey, *UserSessionSchema.FIELD_GROUP_SESSION)
    if values[0] == None:  # 补丁, 数据上线期间, 有些用户还没有建立session数据, 重主数据中获取
        values = daobase.executeUserCmd(userId, 'HMGET', UserDataSchema.mkey(userId),
                                        *UserDataSchema.FIELD_GROUP_SESSION)
    datas = UserSessionSchema.checkDataDict(UserSessionSchema.FIELD_GROUP_SESSION, values, None)
    return datas


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getSessionDatas(userId):
    dataKey = UserSessionSchema.mkey(userId)
    if _CACHE_USER_ENABLE:
        return _cacheSession(userId, dataKey)
    else:
        return _getSessionDataRedis(userId, dataKey)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setSessionDatas(userId, datas):
    ret = _dbuser._setSessionDatas(userId, datas)
    if _CACHE_USER_ENABLE:
        dataKey = UserSessionSchema.mkey(userId)
        _cacheSession.update_group_dict_data(userId, dataKey, datas)
    return ret


@lfu_time_cache(maxsize=_CACHE_SIZE, mainindex=0, subindex=1, group=_CACHE_GROUP)
def _cacheUser(userId, dataKey):
    return _getUserDataRedis(userId, dataKey)


def _getUserDataRedis(userId, dataKey):
    values = daobase.executeUserCmd(userId, 'HMGET', dataKey, *UserDataSchema.FIELDS_ALL)
    datas = UserDataSchema.checkDataDict(UserDataSchema.FIELDS_ALL, values, None)
    return datas


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getUserDatas(userId, fieldList):
    dataKey = UserDataSchema.mkey(userId)
    if _CACHE_USER_ENABLE:
        alldata = _cacheUser(userId, dataKey)
    else:
        alldata = _getUserDataRedis(userId, dataKey)
    vals = []
    for f in fieldList:
        vals.append(alldata.get(f))
    return vals


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setUserDatas(userId, datas):
    dataKey = UserDataSchema.mkey(userId)
    params = UserDataSchema.paramsDict2List(datas)
    ret = daobase.executeUserCmd(userId, 'HMSET', dataKey, *params)
    if _CACHE_USER_ENABLE:
        _cacheUser.update_group_dict_data(userId, dataKey, datas)
    return ret


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setUserDatasNx(userId, datas):
    dataKey = UserDataSchema.mkey(userId)
    params = UserDataSchema.paramsDict2List(datas)
    ret = daobase.executeUserCmd(userId, 'HSETNX', dataKey, *params)
    if _CACHE_USER_ENABLE:
        _cacheUser.replace_group_dict_data_nx(userId, dataKey, datas)
    return ret


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setUserDatasForce(userId, datas):
    dataKey = UserDataSchema.mkey(userId)
    params = UserDataSchema.paramsDict2List(datas, 0)
    ret = daobase.executeUserLua(userId, user_scripts.MAIN_SET_HASH_DATA_FORCE, 2, dataKey, json.dumps(params))
    if _CACHE_USER_ENABLE:
        _cacheUser.update_group_dict_data(userId, dataKey, datas)
    return ret


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _delUserDatas(userId, datas):
    dataKey = UserDataSchema.mkey(userId)
    ret = daobase.executeUserCmd(userId, 'HDEL', dataKey, *datas.keys())
    if _CACHE_USER_ENABLE:
        _cacheUser.remove_group_dict_data(userId, dataKey, datas)
    return ret


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _incrUserDatas(userId, field, value):
    dataKey = UserDataSchema.mkey(userId)
    ret = daobase.executeUserCmd(userId, 'HINCRBY', dataKey, field, value)
    if _CACHE_USER_ENABLE:
        _cacheUser.incrby_group_dict_data(userId, dataKey, field, value)
    return ret


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _incrUserDatasLimit(userId, field, value, lowLimit, highLimit, chipNotEnoughOpMode, dataKey=None):
    from poker.entity.dao import sessiondata
    _, numberClientId = sessiondata.getClientIdNum(userId, None)
    appId = sessiondata.getGameId(userId)

    if dataKey == None:
        dataKey = UserDataSchema.mkey(userId)
    trueDetal, finalCount, fixCount = daobase.executeUserLua(userId, user_scripts.MAIN_INCR_CHIP_LUA_SCRIPT,
                                                             6, value, lowLimit, highLimit, chipNotEnoughOpMode,
                                                             dataKey, field)

    if dataKey == UserDataSchema.mkey(userId):
        if _CACHE_USER_ENABLE:
            _cacheUser.replace_group_dict_data(userId, dataKey, field, finalCount)
    return trueDetal, finalCount, fixCount, appId, numberClientId


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setTableChipToRange(userId, gameid, _min, _max, eventId, intEventParam, clientId, tableId, rhashkey, rfield):
    from poker.entity.dao import sessiondata
    _, numberClientId = sessiondata.getClientIdNum(userId, None)
    appId = sessiondata.getGameId(userId)

    tdelta, tfinal, tfixed, delta, final, fixed = daobase.executeUserLua(userId,
                                                                         user_scripts.MAIN_MOVE_CHIP_TO_TABLE_LUA_SCRIPT,
                                                                         6, userId, gameid, _min, _max, rhashkey,
                                                                         rfield)
    if _CACHE_USER_ENABLE:
        _cacheUser.replace_group_dict_data(userId, UserDataSchema.mkey(userId), UserDataSchema.CHIP, final)
    # TODO 替换GAME DATA中的金币数据值

    ftlog.debug('dbuser->_setTableChipToRange', userId, gameid, _min, _max,
                eventId, intEventParam, clientId, tableId, rhashkey,
                'result->', tdelta, tfinal, tfixed, delta, final, fixed)
    return tdelta, tfinal, tfixed, delta, final, fixed, appId, numberClientId


@lfu_time_cache(maxsize=_CACHE_SIZE, mainindex=0, subindex=1, group=_CACHE_GROUP)
def _cacheWeak(userId, dataKey):
    return _getWeakDataRedis(userId, dataKey)


def _getWeakDataRedis(userId, dataKey):
    jsonstr = daobase.executeUserCmd(userId, 'GET', dataKey)
    data = strutil.loads(jsonstr, ignoreException=True, execptionValue={})
    if not isinstance(data, dict):
        data = {}
    return data


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getWeakData(userId, gameId, weakname, cycleName, curCycle):
    dataKey = UserWeakSchema.mkey(cycleName, weakname, gameId, userId)
    if _CACHE_USER_ENABLE:
        data = _cacheWeak(userId, dataKey)
    else:
        data = _getWeakDataRedis(userId, dataKey)
    oldCycle = data.get('_cycle_', 0)
    if oldCycle != curCycle:
        data = {'_cycle_': curCycle}
    return data


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setWeakData(userId, gameId, weakname, datas, cycleName, curCycle, expire):
    ret = _dbuser._setWeakData(userId, gameId, weakname, datas, cycleName, curCycle, expire)
    if _CACHE_USER_ENABLE:
        dataKey = UserWeakSchema.mkey(cycleName, weakname, gameId, userId)
        _cacheWeak.replace_group_data(userId, dataKey, datas)
    return ret


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setOnlineState(userId, state):
    return _dbuser._setOnlineState(userId, state)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getOnlineState(userId):
    return _dbuser._getOnlineState(userId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setGameEnter(userId, gameId):
    return _dbuser._setGameEnter(userId, gameId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getLastGameId(userId):
    return _dbuser._getLastGameId(userId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setGameLeave(userId, gameId):
    return _dbuser._setGameLeave(userId, gameId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getGameEnterIds(userId):
    return _dbuser._getGameEnterIds(userId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _addOnlineLoc(userId, roomId, tableId, seatId, checkConfict):
    return _dbuser._addOnlineLoc(userId, roomId, tableId, seatId, checkConfict)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setBigRoomOnlineLoc(userId, roomId, tableId, seatId):
    return _dbuser._setBigRoomOnlineLoc(userId, roomId, tableId, seatId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getOnlineLocSeatId(userId, roomId, tableId):
    return _dbuser._getOnlineLocSeatId(userId, roomId, tableId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _removeOnlineLoc(userId, roomId, tableId):
    return _dbuser._removeOnlineLoc(userId, roomId, tableId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _cleanOnlineLoc(userId):
    return _dbuser._cleanOnlineLoc(userId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getOnlineLocList(userId):
    return _dbuser._getOnlineLocList(userId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _checkUserLoc(userId, clientId, matchGameId=0):
    return _dbuser._checkUserLoc(userId, clientId, matchGameId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _clearUserCache(userId):
    if _CACHE_USER_ENABLE:
        c = _cacheUser.clear_key(userId)
        return c
    return 0
