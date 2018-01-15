# -*- coding:utf-8 -*-
'''
Created on 2016年6月7日

@author: luoguanggui
'''

from sre_compile import isstring

import datetime

from poker.entity.game.rooms.relaxation_match_ctrl.exceptions import ConfigException


class StartConfig(object):
    def __init__(self):
        self.conf = None
        self.startTime = None
        self.endTime = None
        self.maxPlayCount = 0
        self.minPlayCount = 0

    def _checkTimeFormat(self):
        '''
        检测timeStr是否属于12:22这样正常的时间格式
        '''
        t1 = self.startTime.split(':')
        h1 = int(t1[0])
        m1 = int(t1[1])
        t2 = self.endTime.split(':')
        h2 = int(t2[0])
        m2 = int(t2[1])
        time1 = datetime.time(h1, m1, 0)
        time2 = datetime.time(h2, m2, 0)
        if time2 > time1:
            return True
        return False

    def checkValid(self):
        try:
            if not self._checkTimeFormat():
                raise ConfigException('error: must be start.endTime > start.endTime, else start.startTime='
                                      + str(self.startTime) + 'start.endTime=' + str(self.endTime))
        except:
            raise ConfigException('start.startTime or start.endTime format error: start.startTime='
                                  + str(self.startTime) + 'start.endTime=' + str(self.endTime))
        if not isinstance(self.maxPlayCount, int) or self.maxPlayCount <= 0:
            raise ConfigException('start.maxPlayCount error: start.maxPlayCount='
                                  + str(self.maxPlayCount))
        if not isinstance(self.minPlayCount, int) or self.minPlayCount <= 0:
            raise ConfigException('start.minPlayCount error: start.minPlayCount='
                                  + str(self.minPlayCount))
        return self

    @classmethod
    def parse(cls, conf):
        ret = StartConfig()
        ret.conf = conf
        ret.startTime = conf.get('startTime', None)
        ret.endTime = conf.get('endTime', None)
        ret.maxPlayCount = conf.get('maxPlayCount', 0)
        ret.minPlayCount = conf.get('minPlayCount', 0)
        return ret.checkValid()


class RankRewards(object):
    def __init__(self):
        self.conf = None
        self.startRank = None
        self.endRank = None
        self.rewards = None
        self.rewardsDesc = None
        # 此奖励需要跳转的todotask
        self.todotask = None

    def checkValid(self):
        if not isinstance(self.startRank, int) or self.startRank < -1:
            raise ConfigException('rank.start must be int >= -1')
        if not isinstance(self.endRank, int) or self.endRank < -1:
            raise ConfigException('rank.end must be int >= -1')
        if self.endRank != -1 and self.endRank < self.startRank:
            raise ConfigException('rank.end must greater than rewards.rank.start')
        return self

    @classmethod
    def parse(cls, conf):
        ret = cls()
        ret.conf = conf
        ret.startRank = conf['ranking']['start']
        ret.endRank = conf['ranking']['end']

        rewards = conf.get('rewards', [])
        ret.rewards = []
        for reward in rewards:
            if not isinstance(reward, dict):
                raise ConfigException('reward item must dict')
            itemId = reward.get('itemId', None)
            if not isstring(itemId) or not itemId:
                raise ConfigException('reward item.name must be not empty string')
            count = reward.get('count', None)
            if not isinstance(count, int) or count < 0:
                raise ConfigException('reward item.count must be int >= 0')
            if count > 0:
                ret.rewards.append(reward)

        ret.desc = conf['desc']
        ret.message = conf.get('message', None)
        ret.todotask = conf.get('todotask', None)
        return ret.checkValid()

    @classmethod
    def buildRewardDescList(cls, rankRewardsList):
        rewardDescList = []
        if rankRewardsList:
            for rankRewards in rankRewardsList:
                rankIndex = ''
                if rankRewards.startRank == rankRewards.endRank:
                    rankIndex = str(rankRewards.startRank)
                else:
                    rankIndex = str(rankRewards.startRank) + '-' + str(rankRewards.endRank)
                rewardDescList.append(u'第%s名:' % (rankIndex) + rankRewards.desc)
        return '\n'.join(rewardDescList)


class MatchConfig(object):
    def __init__(self):
        self.conf = None
        self.gameId = None
        self.matchId = None
        self.name = None
        self.desc = None
        self.tableSeatCount = None
        self.start = None
        self.rankRewardsList = None
        self.rankRewardsDesc = None
        self.recordId = None
        self.baseChip = None

    def checkValid(self):
        if not isinstance(self.matchId, int):
            raise ConfigException('matchId must be int')
        if not isinstance(self.tableSeatCount, int) or self.tableSeatCount <= 0:
            raise ConfigException('table.seat.count must be int > 0')
        if not isinstance(self.recordId, int):
            raise ConfigException('recordId must be int')
        if not isinstance(self.baseChip, int) or self.baseChip <= 0:
            raise ConfigException('chip.base must be int > 0')
        return self

    @classmethod
    def getRankRewardsClass(cls):
        return RankRewards

    @classmethod
    def parse(cls, gameId, roomId, matchId, name, conf):
        ret = MatchConfig()
        ret.conf = conf
        ret.gameId = gameId
        ret.roomId = roomId
        ret.matchId = matchId
        ret.name = name
        ret.desc = conf.get('desc', '')
        ret.tableSeatCount = conf.get('table.seat.count', None)
        ret.recordId = conf.get('recordId', matchId)
        ret.baseChip = conf.get('chip.base', 1)

        start = conf.get('start', None)
        if not isinstance(start, dict):
            raise ConfigException('start must be dict')
        ret.start = StartConfig.parse(start)

        ret.rankRewardsList = []
        rankRewardsList = conf.get('rank.rewards')
        if rankRewardsList is not None:
            if not isinstance(rankRewardsList, list):
                raise ConfigException('rank.rewards must be list')
            for rankRewards in rankRewardsList:
                ret.rankRewardsList.append(cls.getRankRewardsClass().parse(rankRewards))
        ret.rankRewardsDesc = cls.getRankRewardsClass().buildRewardDescList(ret.rankRewardsList)
        return ret.checkValid()
