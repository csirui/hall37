# -*- coding:utf-8 -*-
'''
Created on 2016年1月15日

@author: zhaojiangang
'''


class SignIF(object):
    def signin(self, userId, matchId, ctrlRoomId, instId, fee):
        '''
        报名接口，如果不成功抛异常
        '''
        pass

    def moveTo(self, userId, matchId, ctrlRoomId, instId, toInstId):
        '''
        移动玩家到下一场比赛
        '''
        pass

    def signout(self, userId, matchId, ctrlRoomId, instId, feeContentItem):
        '''
        '''
        pass

    def loadAllUsers(self, matchId, ctrlRoomId, instId):
        '''
        '''
        pass

    def removeAllUsers(self, matchId, ctrlRoomId, instId):
        '''
        '''
        pass

    def lockUser(self, matchId, ctrlRoomId, instId, userId):
        '''
        '''
        pass

    def unlockUser(self, matchId, ctrlRoomId, instId, userId, feeContentItem):
        '''
        '''
        pass


class UserInfoLoader(object):
    def loadUserAttrs(self, userId, attrs):
        '''
        '''
        raise NotImplemented()


class MatchStatus(object):
    def __init__(self, matchId=None, sequence=None, startTime=None):
        self.matchId = matchId
        self.sequence = sequence
        self.startTime = startTime

    @property
    def instId(self):
        return '%s.%s' % (self.matchId, self.sequence)


class MatchStatusDao(object):
    def load(self, matchId):
        '''
        加载比赛信息
        @return: MatchStatus
        '''
        raise NotImplemented()

    def save(self, status):
        '''
        保存比赛信息
        '''
        raise NotImplemented()


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

    def notifyMatchStart(self, group, signers):
        '''
        通知用户比赛开始
        '''
        raise NotImplemented()

    def notifyStageStart(self, player):
        '''
        通知用户正在配桌
        '''
        raise NotImplemented()
