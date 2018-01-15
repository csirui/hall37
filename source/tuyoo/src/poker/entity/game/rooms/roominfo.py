# -*- coding:utf-8 -*-
'''
Created on 2016年4月22日

@author: zhaojiangang
'''
import freetime.util.log as ftlog
from poker.entity.biz.content import TYContentItem
from poker.entity.dao import daobase
from poker.util import strutil


class RoomInfo(object):
    clzMap = {}

    def __init__(self, roomType):
        self._roomType = roomType
        self.roomId = None
        self.playerCount = 0

    @classmethod
    def registerRoomType(cls, typeName, clz):
        cls.clzMap[typeName] = clz

    @classmethod
    def fromDict(cls, roomId, d):
        roomType = d['roomType']
        clz = cls.clzMap.get(roomType)
        if clz:
            ret = clz()
            ret.roomId = roomId
            ret.playerCount = d.get('playerCount', 0)
            return ret.fromDict(d)
        return None

    def toDict(self):
        d = {}
        self._toDictImpl(d)
        d['roomType'] = self._roomType
        d['playerCount'] = self.playerCount
        return d

    def _toDictImpl(self, d):
        pass


class MatchRoomInfo(RoomInfo):
    def __init__(self):
        super(MatchRoomInfo, self).__init__('match')
        self.signinCount = 0
        self.startType = None
        self.instId = None
        self.fees = None
        self.startTime = None
        self.signinTime = None

    def fromDict(self, d):
        self.signinCount = d.get('signinCount', 0)
        self.startType = d.get('startType')
        self.instId = d.get('instId')
        self.startTime = d.get('startTime')
        self.signinTime = d.get('signinTime')
        fees = d.get('fees')
        if fees:
            self.fees = TYContentItem.decodeList(fees)
        return self

    def _toDictImpl(self, d):
        d['signinCount'] = self.signinCount
        d['startType'] = self.startType
        d['instId'] = self.instId
        d['startTime'] = self.startTime
        d['signinTime'] = self.signinTime
        if self.fees:
            d['fees'] = TYContentItem.encodeList(self.fees)


RoomInfo.registerRoomType('match', MatchRoomInfo)


def buildKey(gameId):
    return 'roomInfo:%s' % (gameId)


def decodeRoomInfo(roomId, jstr):
    d = strutil.loads(jstr)
    return RoomInfo.fromDict(roomId, d)


def loadAllRoomInfo(gameId):
    ret = {}
    datas = daobase.executeMixCmd('hgetall', buildKey(gameId))
    if datas:
        i = 0
        while i + 1 < len(datas):
            try:
                roomId = datas[i]
                ret[roomId] = decodeRoomInfo(roomId, datas[i + 1])
            except:
                ftlog.error('roominfo.loadAllRoomInfo gameId=', gameId,
                            'roomId=', datas[i],
                            'roomInfo=', datas[i + 1])
            i += 2
    return ret


def loadRoomInfo(gameId, roomId):
    jstr = daobase.executeMixCmd('hget', buildKey(gameId), roomId)
    if jstr:
        return decodeRoomInfo(roomId, jstr)
    return None


def saveRoomInfo(gameId, roomInfo):
    d = roomInfo.toDict()
    jstr = strutil.dumps(d)
    daobase.executeMixCmd('hset', buildKey(gameId), roomInfo.roomId, jstr)


def removeRoomInfo(gameId, roomId):
    daobase.executeMixCmd('hdel', buildKey(gameId), roomId)
