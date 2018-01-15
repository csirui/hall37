# -*- coding:utf-8 -*-
'''
Created on 2016年1月16日

@author: zhaojiangang
'''
import random

import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from poker.entity.game.rooms.group_match_ctrl.interface import SignIF, \
    MatchRewards, TableController, PlayerNotifier, UserInfoLoader, MatchStatusDao
from poker.entity.game.rooms.group_match_ctrl.models import Signer
from poker.entity.game.rooms.group_match_ctrl.utils import Heartbeat


class SignIFMem(SignIF):
    def __init__(self):
        # key=instId, value=map<userId, Signer>
        self._instSignerMap = {}

    def findSigner(self, instId, userId):
        signerMap = self._instSignerMap.get(instId)
        if signerMap:
            return signerMap.get(userId)
        return None

    def signin(self, userId, matchId, ctrlRoomId, instId, fees):
        '''
        报名接口，如果不成功抛异常
        '''
        signerMap = self._instSignerMap.get(instId)
        if not signerMap:
            signerMap = {}
            self._instSignerMap[instId] = signerMap
        signer = signerMap.get(userId)
        if not signer:
            signerMap[userId] = Signer(userId, instId, pktimestamp.getCurrentTimestamp())
            ftlog.info('SignIFMem.signin userId=', userId,
                       'matchId=', matchId,
                       'ctrlRoomId=', ctrlRoomId)
        return True

    def signout(self, userId, matchId, ctrlRoomId, instId, fees):
        '''
        '''
        signerMap = self._instSignerMap.get(instId)
        if signerMap:
            if userId in signerMap:
                del signerMap[userId]
        return True

    def loadAllUsers(self, matchId, ctrlRoomId, instId):
        '''
        '''
        signerMap = self._instSignerMap.get(instId, {})
        return signerMap.values()

    def removeAllUsers(self, matchId, ctrlRoomId, instId):
        '''
        '''
        if instId in self._instSignerMap:
            del self._instSignerMap[instId]

    def lockUser(self, matchId, ctrlRoomId, instId, userId):
        '''
        '''
        return True

    def unlockUser(self, matchId, ctrlRoomId, instId, userId, fees):
        '''
        '''
        pass


class MatchRewardsTest(MatchRewards):
    def sendRewards(self, player, rankRewards):
        '''给用户发送奖励'''
        ftlog.info('MatchRewardsTest.sendRewards userId=', player.userId,
                   'matchId=', player.group.matchId,
                   'matchingId=', player.group.matchingId,
                   'stageIndex=', player.group.stageIndex,
                   'rankRewards=', rankRewards.conf)


class TableControllerTest(TableController):
    def __init__(self, match):
        self.match = match
        self._tableMap = {}
        self._heartbeat = Heartbeat(3, self._processTables)
        self._heartbeat.start()

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

    def _processTables(self):
        ftlog.info('TableController._processTables')
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


class UserInfoLoaderTest(UserInfoLoader):
    def __init__(self):
        # key=userId, value={}
        self._userAttrs = {}

    def setUserAttrs(self, userId, userAttrMap):
        userAttrs = self._userAttrs.get(userId, {})
        userAttrs.update(userAttrMap)

    def loadUserAttrs(self, userId, attrs):
        '''
        '''
        userAttrs = self._userAttrs.get(userId, {})
        ret = []
        for attr in attrs:
            ret.append(userAttrs.get(attr, None))
        return ret


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
