# -*- coding:utf-8 -*-
'''
Created on 2016年7月13日

@author: zhaojiangang
'''
from poker.entity.game.rooms.erdayi_match_ctrl.utils import Logger


class SigninFee(object):
    def collectFee(self, matchId, roomId, instId, userId, fee):
        '''
        收取用户报名费, 如果报名费不足则抛异常SigninFeeNotEnoughException
        '''
        raise NotImplemented()

    def returnFee(self, matchId, roomId, instId, userId, fee):
        '''
        退还报名费
        '''
        raise NotImplemented()


class SigninRecord(object):
    def __init__(self, userId, signinTime=None, fee=None):
        self.userId = userId
        self.signinTime = signinTime
        self.fee = fee


class SigninRecordDao(object):
    def loadAll(self, matchId, instId, ctrlRoomId):
        '''
        获取所有在本ctrlRoomId下的所有报名记录
        @return: list<SigninRecord>
        '''
        raise NotImplementedError

    def add(self, matchId, instId, ctrlRoomId, record):
        '''
        记录用户报名
        @return: 成功返回True，如果已经存返回False
        '''
        raise NotImplementedError

    def remove(self, matchId, instId, ctrlRoomId, userId):
        '''
        删除用户报名记录
        '''
        raise NotImplementedError

    def removeAll(self, matchId, instId, ctrlRoomId):
        '''
        删除所有报名记录
        '''
        raise NotImplementedError


class MatchUserIF(object):
    def createUser(self, matchId, ctrlRoomId, instId, userId, fee):
        '''
        '''
        raise NotImplementedError

    def removeUser(self, matchId, ctrlRoomId, instId, userId):
        '''
        '''
        raise NotImplementedError

    def lockUser(self, matchId, ctrlRoomId, instId, userId, clientId):
        '''
        锁定用户
        '''
        raise NotImplementedError

    def unlockUser(self, matchId, ctrlRoomId, instId, userId):
        '''
        解锁用户并返还报名费
        '''
        raise NotImplementedError


class SignerInfoLoader(object):
    def fillSigner(self, signer):
        '''
        '''
        raise NotImplementedError


class MatchRewards(object):
    def sendRewards(self, player, rankRewards):
        '''给用户发送奖励'''
        raise NotImplemented()


class TableController(object):
    def startTable(self, table):
        '''
        让桌子开始
        '''
        raise NotImplemented()

    def clearTable(self, table):
        '''
        清理桌子
        '''
        raise NotImplemented()

    def userReconnect(self, table, seat):
        '''
        用户坐下
        '''
        raise NotImplemented()


class PlayerNotifier(object):
    def notifyMatchCancelled(self, signer, reason, message=None):
        '''
        通知用户比赛由于reason取消了
        '''
        raise NotImplemented()

    def notifyMatchOver(self, player, reason, rankRewards):
        '''
        通知用户比赛结束了
        '''
        raise NotImplemented()

    def notifyMatchGiveupFailed(self, player, message):
        '''
        通知用户不能放弃比赛
        '''
        raise NotImplemented()

    def notifyMatchUpdate(self, player):
        '''
        通知比赛更新
        '''
        raise NotImplemented()

    def notifyMatchRank(self, player):
        '''
        通知比赛排行榜
        '''
        raise NotImplemented()

    def notifyMatchWait(self, player, step=None):
        '''
        通知用户等待
        '''
        raise NotImplemented()

    def notifyMatchStart(self, instId, signers):
        '''
        通知用户比赛开始
        '''
        raise NotImplemented()

    def notifyStageStart(self, player):
        '''
        通知用户正在配桌
        '''
        raise NotImplemented()


class MatchStage(object):
    def __init__(self, stageConf, group):
        self._group = group
        self._stageConf = stageConf
        self._stageId3 = None
        self._logger = Logger()
        self._logger.add('matchingId', self.matchingId)
        if self.matchingId3:
            self._stageId3 = '%s%02d%s' % (self.matchingId3[0:12], self.stageIndex + 1, self.matchingId3[12:])
            self._logger.add('matchingId3', self.matchingId3)
        self._logger.add('stageIndex', self.stageIndex)

    @property
    def matchConf(self):
        return self._group.matchConf

    @property
    def matchingId(self):
        return self._group.matchingId

    @property
    def matchingId3(self):
        return self._group.matchingId3

    @property
    def stageId3(self):
        return self._stageId3

    @property
    def stageConf(self):
        return self._stageConf

    @property
    def stageIndex(self):
        return self._stageConf.index

    @property
    def group(self):
        return self._group

    @property
    def area(self):
        return self.group.area

    def calcUncompleteTableCount(self, player):
        return 0

    def hasNextStage(self):
        return self.stageIndex + 1 < len(self.matchConf.stages)

    def start(self):
        raise NotImplementedError

    def kill(self, reason):
        raise NotImplementedError

    def finish(self, reason):
        raise NotImplementedError

    def isStageFinished(self):
        raise NotImplementedError

    def processStage(self):
        raise NotImplementedError


class MatchFactory(object):
    def newStage(self, stageConf, group):
        '''
        创建阶段
        '''
        raise NotImplementedError

    def newSigner(self, userId, instId):
        '''
        创建一个Signer
        '''
        raise NotImplementedError

    def newPlayer(self, signer):
        '''
        创建一个Player
        '''
        raise NotImplementedError


class MatchStatus(object):
    def __init__(self, matchId=None, sequence=None, startTime=None):
        self.matchId = matchId
        self.sequence = sequence
        self.startTime = startTime

    @property
    def instId(self):
        return '%s%06d' % (self.matchId, self.sequence)


class MatchStatusDao(object):
    def load(self, matchId):
        '''
        加载比赛信息
        @return: MatchStatus
        '''
        raise NotImplementedError

    def save(self, status):
        '''
        保存比赛信息
        '''
        raise NotImplementedError

    def getNextMatchingSequence(self, matchId):
        '''
        '''
        raise NotImplementedError
