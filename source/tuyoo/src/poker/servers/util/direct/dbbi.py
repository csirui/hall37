# -*- coding=utf-8

from poker.entity.configure import gdata
from poker.entity.dao import daobase, daoconst
from poker.util import strutil


def _incrGcoin(rkey, coinKey, detalCount):
    '''
    增加全局金流的数值，此方法由bireport方法调用
    rkey的格式为：<gameId> + ":" + <YYYYMMDD>
    coinKey为业务逻辑的全局金流键值
    detalCount 为数据的变化量，整形数值
    '''
    leftCount = daobase._executeBiCmd('HINCRBY', daoconst.BI_KEY_GCOIN % (rkey), coinKey, int(detalCount))
    return leftCount


def _setConnOnLineInfo(serverId, userCount):
    '''
    向BI数据库汇报当前CONN进程的在线人数
    '''
    return daobase._sendBiCmd('HSET', daoconst.BI_KEY_USER_ONLINES, serverId, userCount)


def _getConnOnlineUserCount():
    datas = daobase._executeBiCmd('HGETALL', daoconst.BI_KEY_USER_ONLINES)
    allcount = 0
    if datas:
        for x in xrange(len(datas) / 2):
            i = x * 2
            connId = str(datas[i])
            if connId in gdata.allServersMap():
                allcount += int(datas[i + 1])
            else:
                daobase._sendBiCmd('HDEL', daoconst.BI_KEY_USER_ONLINES, connId)
    return allcount


_ROOMS = {}


def _setRoomOnLineInfo(gameId, roomId, userCount, playTableCount, observerCount):
    userCount, playTableCount, observerCount = strutil.parseInts(userCount, playTableCount, observerCount)
    val = str(userCount) + '|' + str(playTableCount) + '|' + str(observerCount)
    info = _ROOMS.get(roomId, None)
    if info != val:  # 减少非必要的redis数据更新
        _ROOMS[roomId] = val
        return daobase._sendBiCmd('HSET', daoconst.BI_KEY_ROOM_ONLINES % (gameId), roomId, val)
    return 1


def _getRoomOnLineUserCount(gameId, withShadowRoomInfo):
    '''
    重BI数据库中取得当前的游戏的所有的在线人数信息
    return allcount, counts, details, allobcount, obcounts, obdetails
    allcount int，游戏内所有房间的人数的总和
    counts 字典dict，key为大房间ID（bigRoomId)，value为该大房间内的人数总和
    details 字典dict，key为房间实例ID（roomId），value为该房间内的人数
    allobcount, obcounts, obdetails 观察者数量，需要table类实现observersNum属性
    此数据由每个GR，GT进程每10秒钟向BI数据库进行汇报一次
    '''
    rkey = daoconst.BI_KEY_ROOM_ONLINES % (gameId)
    datas = daobase._executeBiCmd('HGETALL', rkey)
    counts = {}
    details = {}
    allcount = 0
    allobcount = 0
    obdetails = {}
    obcounts = {}
    if datas:
        allrooms = gdata.roomIdDefineMap()
        for x in xrange(len(datas) / 2):
            i = x * 2
            roomId = int(datas[i])
            roomConf = allrooms.get(roomId, None)
            if roomConf:
                bigRoomId = str(roomConf.bigRoomId)
                tks = datas[i + 1].split('|')
                ucount, ocount = strutil.parseInts(tks[0], tks[-1])
                ucount += roomConf.configure.get('dummyUserCount', 0)
                if withShadowRoomInfo:
                    details[str(roomId)] = ucount
                if bigRoomId in counts:
                    counts[bigRoomId] += ucount
                else:
                    counts[bigRoomId] = ucount
                allcount += ucount

                if withShadowRoomInfo:
                    obdetails[str(roomId)] = ocount
                if bigRoomId in obcounts:
                    obcounts[bigRoomId] += ocount
                else:
                    obcounts[bigRoomId] = ocount
                allobcount += ocount

            else:
                daobase._sendBiCmd('HDEL', rkey, roomId)
    return allcount, counts, details, allobcount, obcounts, obdetails
