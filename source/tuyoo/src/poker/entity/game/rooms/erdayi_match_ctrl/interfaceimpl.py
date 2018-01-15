# -*- coding:utf-8 -*-
'''
Created on 2016年7月14日

@author: zhaojiangang
'''
from poker.entity.biz.content import TYContentItem
from poker.entity.dao import daobase
from poker.entity.game.rooms.erdayi_match_ctrl.interface import SigninRecordDao, \
    SigninRecord, MatchStatusDao, MatchStatus
from poker.entity.game.rooms.erdayi_match_ctrl.utils import Logger
from poker.util import strutil


class SigninRecordDaoRedis(SigninRecordDao):
    def __init__(self, gameId):
        self._gameId = gameId
        self._logger = Logger()

    def buildKey(self, matchId, instId, ctrlRoomId):
        return 'msignin4:%s:%s:%s' % (self._gameId, instId, ctrlRoomId)

    @classmethod
    def decodeRecord(cls, userId, jstr):
        d = strutil.loads(jstr)
        record = SigninRecord(userId)
        record.signinTime = d['st']
        fee = d.get('fee')
        if fee:
            record.fee = TYContentItem.decodeFromDict(fee)
        return record

    @classmethod
    def encodeRecord(cls, record):
        d = {'st': record.signinTime}
        if record.fee:
            d['fee'] = record.fee.toDict()
        return strutil.dumps(d)

    def loadAll(self, matchId, instId, ctrlRoomId):
        ret = []
        key = self.buildKey(matchId, instId, ctrlRoomId)
        datas = daobase.executeMixCmd('hgetall', key)
        if datas:
            i = 0
            while (i + 1 < len(datas)):
                try:
                    userId = int(datas[i])
                    record = self.decodeRecord(userId, datas[i + 1])
                    ret.append(record)
                except:
                    self._logger.error('SigninRecordDaoRedis.loadAll',
                                       'matchId=', matchId,
                                       'instId=', instId,
                                       'ctrlRoomId=', ctrlRoomId,
                                       'Bad SigninRecord data: [%s, %s]' % (datas[i], datas[i + 1]))
                i += 2
        return ret

    def add(self, matchId, instId, ctrlRoomId, record):
        key = self.buildKey(matchId, instId, ctrlRoomId)
        if self._logger.isDebug():
            self._logger.debug('SigninRecordDaoRedis.add',
                               'matchId=', matchId,
                               'instId=', instId,
                               'ctrlRoomId=', ctrlRoomId,
                               'key=', key,
                               'record=', self.encodeRecord(record))
        return daobase.executeMixCmd('hsetnx', key, record.userId, self.encodeRecord(record)) == 1

    def remove(self, matchId, instId, ctrlRoomId, userId):
        key = self.buildKey(matchId, instId, ctrlRoomId)
        if self._logger.isDebug():
            self._logger.debug('SigninRecordDaoRedis.remove',
                               'matchId=', matchId,
                               'instId=', instId,
                               'ctrlRoomId=', ctrlRoomId,
                               'userId=', userId,
                               'key=', key)
        daobase.executeMixCmd('hdel', key, userId)

    def removeAll(self, matchId, instId, ctrlRoomId):
        key = self.buildKey(matchId, instId, ctrlRoomId)
        if self._logger.isDebug():
            self._logger.debug('SigninRecordDaoRedis.removeAll',
                               'matchId=', matchId,
                               'instId=', instId,
                               'ctrlRoomId=', ctrlRoomId,
                               'key=', key)
        daobase.executeMixCmd('del', key)


class MatchStatusDaoRedis(MatchStatusDao):
    def __init__(self, room):
        self._room = room
        self._logger = Logger()
        self._logger.add('roomId', self._room.roomId)

    def load(self, matchId):
        '''
        加载比赛信息
        @return: MatchStatus
        '''
        key = 'mstatus:%s' % (self._room.gameId)
        jstr = daobase.executeMixCmd('hget', key, matchId)
        if jstr:
            d = strutil.loads(jstr)
            return MatchStatus(matchId, d['seq'], d['startTime'])
        return None

    def save(self, status):
        '''
        保存比赛信息
        '''
        try:
            key = 'mstatus:%s' % (self._room.gameId)
            d = {'seq': status.sequence, 'startTime': status.startTime}
            jstr = strutil.dumps(d)
            daobase.executeMixCmd('hset', key, status.matchId, jstr)
        except:
            self._logger.error('MatchStatusDaoDizhu.save',
                               'matchId=', status.matchId,
                               'instId=', status.instId,
                               'startTime=', status.startTime)

    def getNextMatchingSequence(self, matchId):
        key = 'matchingId:%s' % (self._room.gameId)
        self._logger.hinfo('MatchStatusDaoDizhu.getNextMatchingSequence',
                           'matchId=', matchId,
                           'key=', key)
        return daobase.executeMixCmd('hincrby', key, matchId, 1)
