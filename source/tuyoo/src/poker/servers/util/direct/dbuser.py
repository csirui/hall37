# -*- coding=utf-8

import json

import freetime.util.log as ftlog
from poker.entity.configure import pokerconf
from poker.entity.dao import daobase, daoconst
from poker.entity.dao.daoconst import UserDataSchema, UserSessionSchema, \
    UserLocationSchema, UserWeakSchema, UserOnlineGameSchema
from poker.servers.rpc import roommgr
from poker.servers.util.direct import dbonline, dbplaytime
from poker.servers.util.rpc._private import dataswap, user_scripts
from poker.util import strutil, timestamp


def _checkUserData(userId, clientId=None, appId=0, session={}):
    ret = dataswap.checkUserData(userId, clientId, appId)
    if ret and session:
        _setSessionDatas(userId, session)
    return ret


def _updateUserDataAuthorTime(userId):
    ctfull = timestamp.formatTimeMs()
    daobase.sendUserCmd(userId, 'HSET', daoconst.HKEY_USERDATA + str(userId), 'authorTime', ctfull)
    return ctfull


def _updateUserDataAliveTime(userId):
    ctfull = timestamp.formatTimeMs()
    daobase.sendUserCmd(userId, 'HSET', daoconst.HKEY_USERDATA + str(userId), 'aliveTime', ctfull)
    return ctfull


def _updateUserGameDataAuthorTime(userId, gameId):
    ctfull = timestamp.formatTimeMs()
    daobase.sendUserCmd(userId, 'HSET', daoconst.HKEY_GAMEDATA + str(gameId) + ':' + str(userId), 'authorTime', ctfull)
    return ctfull


def _cacheSession(userId, dataKey):
    values = daobase.executeUserCmd(userId, 'HMGET', dataKey, *UserSessionSchema.FIELD_GROUP_SESSION)
    if values[0] == None:  # 补丁, 数据上线期间, 有些用户还没有建立session数据, 重主数据中获取
        values = daobase.executeUserCmd(userId, 'HMGET', UserDataSchema.mkey(userId),
                                        *UserDataSchema.FIELD_GROUP_SESSION)
    datas = UserSessionSchema.checkDataDict(UserSessionSchema.FIELD_GROUP_SESSION, values, None)
    return datas


def _getSessionDatas(userId):
    dataKey = UserSessionSchema.mkey(userId)
    return _cacheSession(userId, dataKey)


def _setSessionDatas(userId, datas):
    # TODO 补充user表中的几个数据至用户的session中sessionAppId, sessionDevId,city_code
    atts = [UserDataSchema.SESSION_APPID, UserDataSchema.SESSION_DEVID, UserDataSchema.SESSION_CITY_CODE,
            UserDataSchema.SESSION_IP]
    values = daobase.executeUserCmd(userId, 'HMGET', UserDataSchema.mkey(userId), *atts)
    values = UserDataSchema.checkDataList(atts, values, None)
    if not UserSessionSchema.APPID in datas:
        datas[UserSessionSchema.APPID] = values[0]
    if not UserSessionSchema.DEVICEID in datas:
        datas[UserSessionSchema.DEVICEID] = values[1]
    if not UserSessionSchema.CITYCODE in datas:
        datas[UserSessionSchema.CITYCODE] = values[2]
    datas[UserSessionSchema.IPADDRESS] = values[3]  # TODO 加了阿里云代理后，CO服务的带的IP都是阿里的IP地址，只能在重SDK的数据中再取一次
    dataKey = UserSessionSchema.mkey(userId)
    params = UserSessionSchema.paramsDict2List(datas)
    ret = daobase.sendUserCmd(userId, 'HMSET', dataKey, *params)
    return ret


def _getUserDatas(userId, fieldList):
    dataKey = UserDataSchema.mkey(userId)
    values = daobase.executeUserCmd(userId, 'HMGET', dataKey, *fieldList)
    values = UserDataSchema.checkDataList(fieldList, values, None)
    ftlog.debug('_getUserDatas->', userId, fieldList, values)
    return values


def _setUserDatas(userId, datas):
    dataKey = UserDataSchema.mkey(userId)
    params = UserDataSchema.paramsDict2List(datas)
    ret = daobase.executeUserCmd(userId, 'HMSET', dataKey, *params)
    return ret


def _setUserDatasNx(userId, datas):
    dataKey = UserDataSchema.mkey(userId)
    params = UserDataSchema.paramsDict2List(datas)
    ret = daobase.executeUserCmd(userId, 'HSETNX', dataKey, *params)
    return ret


def _setUserDatasForce(userId, datas):
    dataKey = UserDataSchema.mkey(userId)
    params = UserDataSchema.paramsDict2List(datas, 0)
    ret = daobase.executeUserLua(userId, user_scripts.MAIN_SET_HASH_DATA_FORCE, 2, dataKey, json.dumps(params))
    return ret


def _delUserDatas(userId, datas):
    dataKey = UserDataSchema.mkey(userId)
    ret = daobase.executeUserCmd(userId, 'HDEL', dataKey, *datas.keys())
    return ret


def _incrUserDatas(userId, field, value):
    dataKey = UserDataSchema.mkey(userId)
    ret = daobase.executeUserCmd(userId, 'HINCRBY', dataKey, field, value)
    return ret


def _incrUserDatasLimit(userId, field, value, lowLimit, highLimit, chipNotEnoughOpMode, dataKey=None):
    from poker.entity.dao import sessiondata
    _, numberClientId = sessiondata.getClientIdNum(userId, None)
    appId = sessiondata.getGameId(userId)

    if dataKey == None:
        dataKey = UserDataSchema.mkey(userId)
    trueDetal, finalCount, fixCount = daobase.executeUserLua(userId, user_scripts.MAIN_INCR_CHIP_LUA_SCRIPT,
                                                             6, value, lowLimit, highLimit, chipNotEnoughOpMode,
                                                             dataKey, field)

    return trueDetal, finalCount, fixCount, appId, numberClientId


def _setTableChipToRange(userId, gameid, _min, _max, eventId, intEventParam, clientId, tableId, rhashkey, rfield):
    from poker.entity.dao import sessiondata
    _, numberClientId = sessiondata.getClientIdNum(userId, None)
    appId = sessiondata.getGameId(userId)

    tdelta, tfinal, tfixed, delta, final, fixed = daobase.executeUserLua(userId,
                                                                         user_scripts.MAIN_MOVE_CHIP_TO_TABLE_LUA_SCRIPT,
                                                                         6, userId, gameid, _min, _max, rhashkey,
                                                                         rfield)
    # TODO 替换GAME DATA中的金币数据值

    ftlog.debug('dbuser->_setTableChipToRange', userId, gameid, _min, _max,
                eventId, intEventParam, clientId, tableId, rhashkey,
                'result->', tdelta, tfinal, tfixed, delta, final, fixed)
    return tdelta, tfinal, tfixed, delta, final, fixed, appId, numberClientId


def _getWeakData(userId, gameId, weakname, cycleName, curCycle):
    dataKey = UserWeakSchema.mkey(cycleName, weakname, gameId, userId)
    jsonstr = daobase.executeUserCmd(userId, 'GET', dataKey)
    data = strutil.loads(jsonstr, ignoreException=True, execptionValue={})
    if not isinstance(data, dict):
        data = {}
    oldCycle = data.get('_cycle_', 0)
    if oldCycle != curCycle:
        data = {'_cycle_': curCycle}
    return data


def _setWeakData(userId, gameId, weakname, datas, cycleName, curCycle, expire):
    dataKey = UserWeakSchema.mkey(cycleName, weakname, gameId, userId)
    if datas:
        datas['_cycle_'] = curCycle
    if datas:
        ret = daobase.sendUserCmd(userId, 'SETEX', dataKey, expire, strutil.dumps(datas))
    else:
        ret = daobase.sendUserCmd(userId, 'DEL', dataKey)
    return ret


def _setOnlineState(userId, state):
    '''
    设置用户的在线状态,即TCP的链接状态
    用户ID将添加再online数据库的online:users集合
    注意: 此方法通常由CONN服务进行调用,其他人禁止调用
    '''
    if state == daoconst.OFFLINE:
        dbplaytime._cleanalltime(userId)
        daobase.sendUserCmd(userId, 'DEL', UserOnlineGameSchema.mkey(userId))
        daobase.sendUserCmd(userId, 'HDEL', UserSessionSchema.mkey(userId), UserSessionSchema.ONLINE_STATE)
        daobase.sendUserCmd(userId, 'HDEL', UserSessionSchema.mkey(userId), UserSessionSchema.LAST_GAME)
    else:
        daobase.sendUserCmd(userId, 'HSET', UserSessionSchema.mkey(userId), UserSessionSchema.ONLINE_STATE,
                            daoconst.ONLINE)
    dbonline._setOnlineState(userId, state)


def _getOnlineState(userId):
    '''
    取得用户的在线状态,即TCP的链接状态
    '''
    val = daobase.executeUserCmd(userId, 'HGET', UserSessionSchema.mkey(userId), UserSessionSchema.ONLINE_STATE)
    return UserSessionSchema.checkData(UserSessionSchema.ONLINE_STATE, val)


def _setGameEnter(userId, gameId):
    '''
    设置用户进入一个游戏
    通常再bind_game时调用此方法
    数据库中, 存储的键值为: og:<userId>
    '''
    daobase.sendUserCmd(userId, 'SADD', UserOnlineGameSchema.mkey(userId), gameId)
    daobase.sendUserCmd(userId, 'HSET', UserSessionSchema.mkey(userId), UserSessionSchema.LAST_GAME, gameId)


def _getLastGameId(userId):
    '''
    取得用户最后进入的gameId
    '''
    value = daobase.executeUserCmd(userId, 'HGET', UserSessionSchema.mkey(userId), UserSessionSchema.LAST_GAME)
    return UserSessionSchema.checkData(UserSessionSchema.LAST_GAME, value)


def _setGameLeave(userId, gameId):
    '''
    设置用户离开一个游戏
    通常再leave_game时调用此方法
    数据库中, 存储的键值为: og:<userId>
    '''
    daobase.sendUserCmd(userId, 'HSET', UserSessionSchema.mkey(userId), UserSessionSchema.LAST_GAME, 9999)
    daobase.sendUserCmd(userId, 'SREM', UserOnlineGameSchema.mkey(userId), gameId)


def _getGameEnterIds(userId):
    '''
    取得用户进入的游戏列表
    '''
    return daobase.executeUserCmd(userId, 'SMEMBERS', UserOnlineGameSchema.mkey(userId))


def _addOnlineLoc(userId, roomId, tableId, seatId, checkConfict):
    '''
    添加一个用户的在线位置, 
    注意: 子键值为roomId+'.'+tableId, 因此不允许用户再同一个桌子的不同桌位坐下
    通常此方法在用户真实坐在某一个桌位后调用
    '''
    if checkConfict:
        onlineSeatId = _getOnlineLocSeatId(userId, roomId, tableId)
        assert not onlineSeatId or onlineSeatId == seatId
    # 设置游戏时长记录, 1天后自动过期
    dbplaytime._setPlayTimeStart(userId, roomId, tableId)
    if ftlog.is_debug():
        ftlog.debug('dbuser._addOnlineLoc userId=', userId,
                    'roomId=', roomId,
                    'tableId=', tableId,
                    'seatId=', seatId,
                    'checkConfict=', checkConfict)
    return daobase.sendUserCmd(userId, 'HSET', UserLocationSchema.mkey(userId), 'R.' + str(roomId) + '.' + str(tableId),
                               seatId)


def _setBigRoomOnlineLoc(userId, roomId, tableId, seatId):
    bigRoomId = strutil.getBigRoomIdFromInstanceRoomId(roomId)
    loclist = _getOnlineLocList(userId)
    for locs in loclist:
        rid, tid, _ = locs[0], locs[1], locs[2]
        brid = strutil.getBigRoomIdFromInstanceRoomId(rid)
        if ftlog.is_debug():
            ftlog.debug('dbuser._setBigRoomOnlineLoc userId=', userId,
                        'brid=', brid,
                        'bigRoomId=', bigRoomId,
                        'tableId=', tableId,
                        'seatId=', seatId)
        if brid == bigRoomId:
            _removeOnlineLoc(userId, rid, tid)
    _addOnlineLoc(userId, roomId, tableId, seatId, False)


def _getOnlineLocSeatId(userId, roomId, tableId):
    '''
    取得用户再桌子上的ID
    若不在桌子上返回0
    同_addOnlineLoc为配对方法
    '''
    value = daobase.executeUserCmd(userId, 'HGET', UserLocationSchema.mkey(userId),
                                   'R.' + str(roomId) + '.' + str(tableId))
    return UserLocationSchema.checkData(UserLocationSchema.SEATID, value)


def _removeOnlineLoc(userId, roomId, tableId):
    '''
    移除一个用户的在线位置
    通常此方法在用户真实离开某一个桌位后调用
    '''
    # 游戏时长计算, 1天后自动过期
    subkey = 'R.' + str(roomId) + '.' + str(tableId)
    if ftlog.is_debug():
        ftlog.debug('dbuser._removeOnlineLoc userId=', userId,
                    'roomId=', roomId,
                    'tableId=', tableId)
    daobase.sendUserCmd(userId, 'HDEL', UserLocationSchema.mkey(userId), subkey)
    dbplaytime._setPlayTimeStop(userId, roomId, tableId)


def _cleanOnlineLoc(userId):
    '''
    移除一个用户的所有在线位置
    '''
    dbplaytime._cleanalltime(userId)
    daobase.sendUserCmd(userId, 'DEL', UserLocationSchema.mkey(userId))


def _getOnlineLocList(userId):
    '''
    取得当前用户的所有在线位置信息list
    返回loc的数组列表, 每一项为一个3项值, 分别为: roomId, tableId, seatId
    示例 :
        return [
                [roomId1, tableId1, seatId1],
                [roomId2, tableId2, seatId2],
                ]
    '''
    loclist = []
    val = daobase.executeUserCmd(userId, 'HGETALL', UserLocationSchema.mkey(userId))
    if val:
        vlen = len(val)
        i = 0
        while i < vlen:
            k = val[i]
            v = val[i + 1]
            i += 2
            datas = k.split('.', 2)
            rid = int(datas[1])
            tid = int(datas[2])
            loclist.append([rid, tid, int(v)])
    return loclist


def _checkUserLoc(userId, clientId, matchGameId=0):
    '''Why：
           玩家断线重连时，loc的信息可能与table不一致，conn server需要与table server通讯检查一致性；
           导致不一致的原因：服务端重启（特别是roomId、tableId变更）
           如果玩家在队列房间或者比赛房间的等待队列中, 此处不做一致性检查，等玩家发起quick_start时由room server检查
       What：
           与table server通讯检查桌子对象里是否有这个玩家的数据
           如果不一致，则回收牌桌金币并清空loc；
       Return：
           如果玩家在房间队列里，返回gameId.roomId.roomId*10000.1
           如果玩家在座位上，返回gameId.roomId.tableId.seatId
           如果玩家在旁观，返回gameId.roomId.tableId.0
           玩家不在table对象里，返回0.0.0.0
    '''
    truelocs = []
    loclist = _getOnlineLocList(userId)
    for locs in loclist:
        rid, tid, sid = locs[0], locs[1], locs[2]
        gid = strutil.getGameIdFromInstanceRoomId(rid)
        if gid > 0 and rid > 0 and tid > 0:
            # 到具体的房间或桌子的服务上去查询, 是否是真的在桌子上
            if tid == rid * 10000:  # 玩家在队列房间或者比赛房间的等待队列中, 此处不做一致性检查，玩家发起quick_start时检查。 
                truelocs.append('%d.%d.%d.%d' % (gid, rid, tid, sid))
            else:
                seatId, isObserving = 0, 0
                try:
                    seatId, isObserving = roommgr.doCheckUserLoc(userId, gid, rid, tid, clientId)
                except:
                    ftlog.error()
                    continue
                ftlog.debug('_checkUserLoc->userId=', userId, 'seatId=', seatId, 'isObserving=', isObserving)
                if seatId > 0 or isObserving == 1:
                    # 还在桌子上游戏, 返回断线重连的信息
                    if matchGameId > 0:
                        if matchGameId == gid:
                            truelocs.append('%d.%d.%d.%d' % (gid, rid, tid, seatId))
                    else:
                        truelocs.append('%d.%d.%d.%d' % (gid, rid, tid, seatId))
                else:
                    # 已经不再桌子上了, 清理所有的桌子带入金币
                    if sid > 0:
                        from poker.entity.dao import userchip
                        userchip.moveAllTableChipToChip(
                            userId, gid,
                            'TABLE_TCHIP_TO_CHIP',
                            0, clientId, tid)
                    # 清理当前的在线数据
                    _removeOnlineLoc(userId, rid, tid)
        else:
            # 到这儿, 数据是错误的, 删除处理
            _removeOnlineLoc(userId, rid, tid)
    ftlog.debug('_checkUserLoc->', userId, clientId, truelocs)
    if pokerconf.isOpenMoreTable(clientId):
        # 新的客户端协议, 对于断线重连支持的时列表格式, 即客户端可以进行多开
        return strutil.dumps(truelocs)
    else:
        # 老的客户端, 只支持一个桌子
        if truelocs:
            return truelocs[0]
        return '0.0.0.0'


def _clearUserCache(userId):
    return 0
