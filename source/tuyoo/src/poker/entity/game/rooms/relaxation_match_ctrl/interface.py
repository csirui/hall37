# -*- coding:utf-8 -*-
'''
Created on 2016年6月7日

@author: luoguanggui
'''


class MatchRewards(object):
    def sendRewards(self, player, rankRewards):
        '''给用户发送奖励'''
        raise NotImplemented()


class TableController(object):
    def notifyTableSendQuickStart(self, table, player):
        '''
        发送快速开始，并将该用户置为在该桌子上
        '''
        raise NotImplemented()

    def notifyTableClearTable(self, table):
        '''
        清理桌子
        '''
        raise NotImplemented()

    def notifyUpdateMatchInfo(self, table):
        '''
        通知桌子，比赛信息改变
        '''
        raise NotImplemented()

    def notifyMatchOver(self, table):
        '''
        通知桌位上还有玩家的桌子，比赛已经结束
        '''
        raise NotImplemented()


class PlayerNotifier(object):
    def notifyMatchOver(self, player, rankRewards):
        '''
        通知用户比赛结束了
        '''
        raise NotImplemented()

    def notifyMatchRank(self, player):
        '''
        通知比赛排行榜
        '''
        raise NotImplemented()

    def notifyMatchRankGuest(self, userId):
        '''
        通知比赛排行榜,非参赛玩家
        '''
        raise NotImplemented()


class PlayerSortApi(object):
    def cmpByScore(self, p1, p2):
        '''
        比赛过程临时排名api
        '''
        raise NotImplemented()

    def overCmpByScore(self, p1, p2):
        '''
        比赛结束后最终排名api
        '''
        raise NotImplemented()
