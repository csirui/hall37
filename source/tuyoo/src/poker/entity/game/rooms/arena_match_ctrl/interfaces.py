# -*- coding:utf-8 -*-
'''
Created on 2015年11月12日

@author: zhaojiangang
'''


class UserLocker(object):
    def lockUser(self, userId, roomId, tableId, seatId):
        raise NotImplementedError

    def unlockUser(self, roomId, tableId):
        raise NotImplementedError


class SigninFee(object):
    def collectFee(self, inst, userId, fee):
        '''
        收取用户报名费, 如果报名费不足则抛异常SigninFeeNotEnoughException
        '''
        raise NotImplemented()

    def returnFee(self, inst, userId, fee):
        '''
        退还报名费
        '''
        raise NotImplemented()


class SigninRecordDao(object):
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

    def removeAll(self, matchId):
        '''
        删除instId相关的所有报名信息
        '''
        raise NotImplemented()


class MatchTableController(object):
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


class MatchPlayerNotifier(object):
    def notifyMatchStart(self, player):
        '''
        通知用户比赛开始了
        '''
        raise NotImplemented()

    def notifyMatchWait(self, player):
        '''
        通知用户等待晋级
        '''
        raise NotImplemented()

    def notifyMatchRank(self, player):
        '''
        通知比赛排行榜
        '''
        raise NotImplemented()

    def notifyMatchGiveupFailed(self, player, info):
        '''
        通知用户放弃比赛失败
        '''
        raise NotImplemented()

    def notifyMatchWillCancelled(self, player, reason):
        '''
        通知用户比赛即将取消
        '''
        raise NotImplemented()

    def notifyMatchCancelled(self, player, reason):
        '''
        通知用户比赛取消
        '''
        raise NotImplemented()

    def notifyMatchOver(self, player, reason, rankRewards):
        '''
        通知用户比赛结束了
        '''
        raise NotImplemented()


class UserInfoLoader(object):
    def loadUserAttrs(self, userId, attrs):
        '''
        获取用户属性
        '''
        raise NotImplemented()

    def getSessionClientId(self, userId):
        '''
        获取用户sessionClientId
        '''
        raise NotImplemented()


class MatchRankRewardsSender(object):
    def sendRankRewards(self, player, rankRewards):
        '''
        给用户发奖
        '''
        raise NotImplemented()


if __name__ == '__main__':
    pass
