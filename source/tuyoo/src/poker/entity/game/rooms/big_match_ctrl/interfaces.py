# -*- coding:utf-8 -*-
'''
Created on 2014年9月17日

@author: zjgzzz@126.com
'''


class PlayerLocation(object):
    pass


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
    def notifyMatchCancelled(self, player, inst, reason, message=None):
        '''
        通知用户比赛由于reason取消了
        '''
        raise NotImplemented()

    def notifyMatchOver(self, player, group, reason, rankRewards):
        '''
        通知用户比赛结束了
        '''
        raise NotImplemented()

    def notifyMatchGiveupFailed(self, player, group, message):
        '''
        通知用户不能放弃比赛
        '''
        raise NotImplemented()

    def notifyMatchUpdate(self, player, group):
        '''
        通知比赛更新
        '''
        raise NotImplemented()

    def notifyMatchRank(self, player, group):
        '''
        通知比赛排行榜
        '''
        raise NotImplemented()

    def notifyMatchWait(self, player, group, step=None):
        '''
        通知用户等待
        '''
        raise NotImplemented()

    def notifyMatchStart(self, players, group):
        '''
        通知用户比赛开始
        '''
        raise NotImplemented()

    def notifyStageStart(self, player, group):
        '''
        通知用户正在配桌
        '''
        raise NotImplemented()


class SigninRecordDao(object):
    def load(self, matchId, instId):
        '''
        加载所有报名记录
        @return: list((userId, signinTime))
        '''
        raise NotImplemented()

    def recordSignin(self, matchId, instId, userId, timestamp, signinParams):
        '''
        记录报名信息
        '''
        raise NotImplemented()

    def removeSignin(self, matchId, instId, userId):
        '''
        删除报名信息
        '''
        raise NotImplemented()

    def removeAll(self, matchId, instId):
        '''
        删除instId相关的所有报名信息
        '''
        raise NotImplemented()


class MatchRewards(object):
    def sendRewards(self, player, group, rankRewards):
        '''给用户发送奖励'''
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


class SigninFee(object):
    def collectFees(self, inst, userId, fees):
        '''
        收取用户报名费, 如果报名费不足则抛异常SigninFeeNotEnoughException
        '''
        raise NotImplemented()

    def returnFees(self, inst, userId, fees):
        '''
        退还报名费
        '''
        raise NotImplemented()


class UserInfoLoader(object):
    def loadUserName(self, userId):
        '''
        获取用户名称
        '''
        raise NotImplemented()

    def loadUserAttrs(self, userId, attrs):
        '''
        '''
        raise NotImplemented()
