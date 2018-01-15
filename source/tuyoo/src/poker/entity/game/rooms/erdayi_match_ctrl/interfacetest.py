# -*- coding:utf-8 -*-
'''
Created on 2016年1月16日

@author: zhaojiangang
'''
import random

import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from poker.entity.game.rooms.erdayi_match_ctrl.interface import SigninRecordDao, \
    MatchRewards, TableController, PlayerNotifier, SignerInfoLoader, MatchStatusDao, \
    MatchUserIF
from poker.entity.game.rooms.erdayi_match_ctrl.utils import HeartbeatAble
from poker.util import strutil


class SigninRecordDaoTest(SigninRecordDao):
    def __init__(self):
        self._records = {}

    @classmethod
    def buildKey(cls, instId, ctrlRoomId):
        return '%s:%s' % (instId, ctrlRoomId)

    def loadAll(self, matchId, instId, ctrlRoomId):
        '''
        获取所有在本ctrlRoomId下的所有报名记录
        @return: list<SigninRecord>
        '''
        userRecordMap = self._records.get(self.buildKey())
        if not userRecordMap:
            return []
        return userRecordMap.values()

    def add(self, matchId, instId, ctrlRoomId, record):
        '''
        记录用户报名
        @return: 成功返回True，如果已经存返回False
        '''
        key = self.buildKey(instId, ctrlRoomId)
        userRecordMap = self._records.get(key)
        if not userRecordMap:
            userRecordMap = {}
            self._records[key] = userRecordMap
        if record.userId in userRecordMap:
            return False
        userRecordMap[record.userId] = record
        return True

    def remove(self, matchId, instId, ctrlRoomId, userId):
        '''
        删除用户报名记录
        '''
        key = self.buildKey(instId, ctrlRoomId)
        userRecordMap = self._records.get(key)
        if userRecordMap and userId in userRecordMap:
            del userRecordMap[userId]

    def removeAll(self, matchId, instId, ctrlRoomId):
        '''
        删除所有报名记录
        '''
        key = self.buildKey(instId, ctrlRoomId)
        if key in self._records:
            del self._records[key]


class MatchRewardsTest(MatchRewards):
    def sendRewards(self, player, rankRewards):
        '''给用户发送奖励'''
        ftlog.info('MatchRewardsTest.sendRewards userId=', player.userId,
                   'matchId=', player.group.matchId,
                   'matchingId=', player.group.matchingId,
                   'stageIndex=', player.group.stageIndex,
                   'rankRewards=', rankRewards.conf)


class TableControllerTest(HeartbeatAble, TableController):
    def __init__(self, match):
        super(TableControllerTest, self).__init__(1)
        self.match = match
        self._tableMap = {}

    def startTable(self, table):
        '''
        让桌子开始
        '''
        self._tableMap[table] = pktimestamp.getCurrentTimestamp()

    def clearTable(self, table):
        '''
        清理桌子
        '''
        del self._tableMap[table]

    def updateTableInfo(self, table):
        '''
        桌子信息变化
        '''
        raise NotImplemented()

    def userReconnect(self, table, seat):
        '''
        用户坐下
        '''
        raise NotImplemented()

    def _doHeartbeat(self):
        ftlog.info('TableController._doHeartbeat')
        timestamp = pktimestamp.getCurrentTimestamp()
        winloseTables = set()
        for table, t in self._tableMap.iteritems():
            if timestamp - t > 1:
                winloseTables.add(table)
        for table in winloseTables:
            winloseList = self._randomUserWinlose(table)
            for winlose in winloseList:
                # tableId, ccrc, seatId, userId, deltaScore, isWin
                self.match.winlose(table.tableId, table.ccrc, winlose[1], winlose[0], winlose[2], winlose[3])

    def _randomUserWinlose(self, table):
        seats = table.seats
        dizhuSeatIndex = random.randint(0, len(seats) - 1)
        dizhuSeatId = seats[dizhuSeatIndex]
        dizhuWin = random.randint(0, 1)
        baseScore = random.randint(1, 20) * 100
        dizhuDeltaScore = baseScore * 2 if dizhuWin else -baseScore * 2
        nongminDeltaScore = -baseScore if dizhuWin else baseScore
        ret = []
        for seat in seats:
            isDizhu = dizhuSeatId == seat.seatId
            deltaScore = dizhuDeltaScore if isDizhu else nongminDeltaScore
            isWin = dizhuWin == 1 if isDizhu else dizhuWin == 0
            ret.append((seat.player.userId, seat.seatId, deltaScore, isWin))
        return ret


class PlayerNotifierTest(PlayerNotifier):
    def notifyMatchCancelled(self, signinUser, reason, message=None):
        '''
        通知用户比赛由于reason取消了
        '''
        ftlog.info('PlayerNotifierTest.notifyMatchCancelled userId=', signinUser.userId,
                   'reason=', reason,
                   'message=', message)

    def notifyMatchOver(self, player, reason, rankRewards):
        '''
        通知用户比赛结束了
        '''
        ftlog.info('PlayerNotifierTest.notifyMatchOver userId=', player.userId,
                   'rank=', player.rank,
                   'score=', player.score,
                   'reason=', reason,
                   'rankRewards=', rankRewards.conf if rankRewards else None)

    def notifyMatchGiveupFailed(self, player, message):
        '''
        通知用户不能放弃比赛
        '''
        ftlog.info('PlayerNotifierTest.notifyMatchGiveupFailed userId=', player.userId,
                   'message=', message)

    def notifyMatchUpdate(self, player):
        '''
        通知比赛更新
        '''
        ftlog.info('PlayerNotifierTest.notifyMatchUpdate userId=', player.userId)

    def notifyMatchRank(self, player):
        '''
        通知比赛排行榜
        '''
        ftlog.info('PlayerNotifierTest.notifyMatchRank userId=', player.userId)

    def notifyMatchWait(self, player, step=None):
        '''
        通知用户等待
        '''
        ftlog.info('PlayerNotifierTest.notifyMatchWait userId=', player.userId,
                   'step=', step)

    def notifyMatchStart(self, instId, signers):
        '''
        通知用户比赛开始
        '''
        ftlog.info('PlayerNotifierTest.notifyMatchStart instId=', instId,
                   'userIds=', [p.userId for p in signers])

    def notifyStageStart(self, player):
        '''
        通知用户正在配桌
        '''
        ftlog.info('PlayerNotifierTest.notifyStageStart userId=', player.userId)


class SignerInfoLoaderTest(SignerInfoLoader):
    def __init__(self):
        # key=userId, value={}
        self._userAttrs = {}

    def setUserAttrs(self, userId, userAttrMap):
        userAttrs = self._userAttrs.get(userId, {})
        userAttrs.update(userAttrMap)

    def fillSigner(self, signer):
        userAttrs = self._userAttrs.get(signer.userId, {})
        signer.userName = strutil.ensureString(userAttrs.get('name', None))
        signer.clientId = strutil.ensureString(userAttrs.get('sessionClientId', None))
        signer.gameClientVersion = userAttrs.get('gameClientVersion', 0)
        return signer


class MatchStatusDaoMem(MatchStatusDao):
    def __init__(self):
        self._statusMap = {}

    def load(self, matchId):
        '''
        加载比赛信息
        @return: MatchStatus
        '''
        return self._statusMap.get(matchId)

    def save(self, status):
        '''
        保存比赛信息
        '''
        self._statusMap[status.matchId] = status


class MatchUserIFTest(MatchUserIF):
    def createUser(self, matchId, ctrlRoomId, instId, userId, fee):
        '''
        '''
        return 0

    def removeUser(self, matchId, ctrlRoomId, instId, userId):
        '''
        '''
        pass

    def lockUser(self, matchId, ctrlRoomId, instId, userId, clientId):
        '''
        锁定用户
        '''
        return True

    def unlockUser(self, matchId, ctrlRoomId, instId, userId):
        '''
        解锁用户并返还报名费
        '''
        pass
