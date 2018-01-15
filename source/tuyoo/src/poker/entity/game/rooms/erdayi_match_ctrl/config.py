# -*- coding:utf-8 -*-
'''
Created on 2014年9月23日

@author: zjgzzz@126.com
'''

import time
from sre_compile import isstring

from datetime import datetime

import poker.util.timestamp as pktimestamp
from freetime.util.cron import FTCron
from poker.entity.biz.exceptions import TYBizConfException
from poker.entity.game.rooms.erdayi_match_ctrl.const import MatchType, FeeType, \
    GroupingType, AnimationType, SeatQueuingType, MAX_CARD_COUNT
from poker.entity.game.rooms.erdayi_match_ctrl.exceptions import \
    MatchConfException


class StartConfig(object):
    def __init__(self):
        self.conf = None

        # 通用配置
        self.type = None
        self.feeType = None
        self.maxPlayTime = None
        self.tableTimes = None
        self.tableAvgTimes = None

        # 人满开赛的配置
        self.userCount = None

        # 定时赛配置
        self.userMinCount = None
        self.userMaxCount = None
        self.signinMaxCount = None
        self.userMaxCountPerMatch = None
        self.userNextGroup = None
        self.signinTimes = None
        self.prepareTimes = None
        self.signinTimesStr = None
        self.times = None
        self._cron = None

        # 开赛速度
        self.startMatchSpeed = None
        self.selectFirstStage = None

    def isTimingType(self):
        return self.type == MatchType.TIMING

    def isUserCountType(self):
        return self.type == MatchType.USER_COUNT

    def calcNextStartTime(self, timestamp=None):
        timestamp = timestamp or pktimestamp.getCurrentTimestamp()
        ntime = datetime.fromtimestamp(int(timestamp))
        nexttime = None
        if self._cron:
            nexttime = self._cron.getNextTime(ntime)
        if nexttime is not None:
            return int(time.mktime(nexttime.timetuple()))
        return None

    def getTodayNextLater(self):
        if self._cron:
            return self._cron.getTodayNextLater()
        return -1

    def calcSigninTime(self, startTime):
        assert (self.isTimingType())
        if self.signinTimes:
            return startTime - self.signinTimes
        return None

    def calcPrepareTime(self, startTime):
        assert (self.isTimingType())
        if self.prepareTimes:
            return startTime - self.prepareTimes
        return startTime - 5

    def buildSigninTimeStr(self):
        if not self.isTimingType():
            return u''
        if self.signinTimesStr:
            return self.signinTimesStr
        ts = int(self.signinTimes)
        thours = int(ts / 3600)
        ts = ts - thours * 3600
        tminutes = int(ts / 60)
        ts = ts - tminutes * 60
        tseconds = int(ts % 60)
        tstr = u''
        if thours > 0:
            tstr = tstr + unicode(thours) + u'小时'
        if tminutes > 0:
            tstr = tstr + unicode(tminutes) + u'分钟'
        if tseconds > 0:
            tstr = tstr + unicode(tseconds) + u'秒'
        return '请在比赛开始前%s，报名参加此比赛' % (tstr)

    def checkValid(self):
        if not MatchType.isValid(self.type):
            raise MatchConfException('start.type must in:' + str(MatchType.VALID_TYPES))
        if not FeeType.isValid(self.feeType):
            raise MatchConfException('start.fee.type must in:' + str(FeeType.VALID_TYPES))
        if not isinstance(self.maxPlayTime, int) or self.maxPlayTime <= 0:
            raise MatchConfException('start.maxplaytime must be int > 0')
        if not isinstance(self.tableTimes, int) or self.tableTimes <= 0:
            raise MatchConfException('start.tableTimes must be int > 0')
        if not isinstance(self.tableAvgTimes, int) or self.tableAvgTimes <= 0:
            raise MatchConfException('start.tableAvgTimes must be int > 0')
        if not isinstance(self.startMatchSpeed, int) or self.startMatchSpeed <= 0:
            raise MatchConfException('start.speed must be int > 0')
        if self.isUserCountType():
            if not isinstance(self.userCount, int) or self.userCount <= 0:
                raise MatchConfException('start.user.size must be int > 0')
        else:
            if not isinstance(self.userMaxCount, int) or self.userMaxCount <= 0:
                raise MatchConfException('start.user.maxsize must be int > 0')
            if not isinstance(self.userMinCount, int) or self.userMinCount <= 0:
                raise MatchConfException('start.user.minsize must be int > 0')
            if not isinstance(self.signinMaxCount, int) or self.signinMaxCount <= 0:
                raise MatchConfException('start.signin.minsize must be int > 0')
            if self.signinMaxCount < self.userMinCount:
                raise MatchConfException('start.signin.minsize must > start.user.maxsize')
            if self.userMaxCount < self.userMinCount:
                raise MatchConfException('start.user.maxsize must greater than start.user.minsize')
            if not isinstance(self.signinTimes, int) or self.signinTimes < 0:
                raise MatchConfException('start.signin.times must be int >= 0')
            if not isstring(self.signinTimesStr):
                raise MatchConfException('start.signin.times.str must be string')
            if not isinstance(self.prepareTimes, int) or self.signinTimes < 0:
                raise MatchConfException('start.prepare.times must be int >= 0')
            if not isinstance(self.times, dict):
                raise MatchConfException('start.times must be dict')
            if not self._cron:
                raise MatchConfException('start.times is invalid')
            if not isinstance(self.userNextGroup, (int, float)):
                raise MatchConfException('start.user.next.group must be float')
            if self.selectFirstStage not in (0, 1):
                raise MatchConfException('start.selectFirstStage must in (0, 1)')
        return self

    @classmethod
    def parse(cls, conf):
        ret = StartConfig()
        ret.conf = conf
        ret.type = conf.get('type', None)
        ret.feeType = conf.get('fee.type', None)
        ret.maxPlayTime = conf.get('maxplaytime', None)
        ret.tableTimes = conf.get('table.times', 480)
        ret.tableAvgTimes = conf.get('table.avg.times', 150)
        ret.startMatchSpeed = conf.get('start.speed', 5)

        # 人满开赛的配置
        ret.userCount = conf.get('user.size', None)

        # 定时赛配置
        ret.userMinCount = conf.get('user.minsize', None)
        ret.userMaxCount = conf.get('user.maxsize', None)
        ret.signinMaxCount = conf.get('signin.maxsize', ret.userMaxCount)
        ret.userMaxCountPerMatch = ret.userMaxCount
        ret.signinMaxCountPerMatch = ret.signinMaxCount
        ret.signinTimes = conf.get('signin.times', None)
        ret.signinTimesStr = conf.get('signin.times.str', '')
        ret.prepareTimes = conf.get('prepare.times', 5)
        ret.userNextGroup = conf.get('user.next.group', None)
        ret.selectFirstStage = conf.get('selectFirstStage', 0)
        ret.times = conf.get('times', None)
        if ret.isTimingType():
            ret._cron = FTCron(ret.times)
        return ret.checkValid()


class GroupingConfig(object):
    def __init__(self):
        self.conf = None
        self.type = None
        # 固定分组
        self.groupCount = None
        # 按照人数分组
        self.userCount = None

    def checkValid(self):
        if not GroupingType.isValid(self.type):
            raise MatchConfException('matchs.grouping.type must in:' + str(GroupingType.VALID_TYPES))
        if GroupingType.TYPE_GROUP_COUNT:
            if not isinstance(self.groupCount, int) or self.groupCount <= 0:
                raise MatchConfException('matchs.grouping.group.count must in:' + str(GroupingType.VALID_TYPES))
        else:
            if not isinstance(self.userCount, int) or self.userCount <= 0:
                raise MatchConfException('matchs.grouping.user.count must be int > 0')
        return self

    @classmethod
    def parse(cls, conf):
        ret = GroupingConfig()
        ret.conf = conf
        ret.type = conf.get('type', None)
        ret.groupCount = conf.get('group.count', None)
        ret.userCount = conf.get('user.count', None)
        return ret.checkValid()


class StageConfig(object):
    def __init__(self):
        self.conf = None

        self.name = None
        self.animationType = None
        self.seatQueuing = None
        self.cardCount = None
        self.riseUserCount = None
        self.chipBase = None

        self.groupingType = None
        self.groupingUserCount = None
        self.groupingGroupCount = None
        self.rankRewardsList = None
        self.rankRewardsDesc = None
        self.index = 0
        self.tableTimeoutCheckInterval = 5

    def checkValid(self):
        if not isstring(self.name):
            raise MatchConfException('Stage.name must be string')

        if not AnimationType.isValid(self.animationType):
            raise MatchConfException('Stage.animationType must in:' + str(AnimationType.VALID_TYPES))

        if not SeatQueuingType.isValid(self.seatQueuing):
            raise MatchConfException('Stage.seat.principles must in:' + str(SeatQueuingType.VALID_TYPES))

        if (not isinstance(self.cardCount, int)
            or self.cardCount <= 0
            or self.cardCount > MAX_CARD_COUNT):
            raise MatchConfException('Stage.card.count must in:' + str((1, MAX_CARD_COUNT)))

        if (not isinstance(self.riseUserCount, int)
            or self.riseUserCount <= 0):
            raise MatchConfException('Stage.raise.user.count must be integer >= 0')

        if not isinstance(self.chipBase, int):
            raise MatchConfException('Stage.chip.base must be integer')

        if not GroupingType.isValid(self.groupingType):
            raise MatchConfException('Stage.grouping.type must in:' + str(GroupingType.VALID_TYPES))

        if self.groupingType == GroupingType.TYPE_GROUP_COUNT:
            if not isinstance(self.groupingGroupCount, int) or self.groupingGroupCount <= 0:
                raise MatchConfException('Stage.grouping.group.count must be integer > 0')
        elif self.groupingType == GroupingType.TYPE_USER_COUNT:
            if not isinstance(self.groupingUserCount, int) or self.groupingUserCount <= 0:
                raise MatchConfException('Stage.grouping.user.count must be integer > 0')
        return self

    @classmethod
    def parse(cls, conf):
        ret = StageConfig()
        ret.conf = conf

        # 通用配置
        ret.name = conf.get('name', None)
        ret.animationType = conf.get('animation.type', -1)
        ret.seatQueuing = conf.get('seat.principles', None)
        ret.cardCount = conf.get('card.count', None)
        ret.riseUserCount = conf.get('rise.user.count', None)
        ret.chipBase = conf.get('chip.base', None)
        ret.groupingType = conf.get('grouping.type', GroupingType.TYPE_NO_GROUP)
        ret.groupingUserCount = conf.get('grouping.user.count', None)
        ret.groupingGroupCount = conf.get('grouping.group.count', None)

        ret.rankRewardsList = []
        rankRewardsList = conf.get('rank.rewards')
        if rankRewardsList is not None:
            if not isinstance(rankRewardsList, list):
                raise MatchConfException('rank.rewards must be list')
            for rankRewards in rankRewardsList:
                ret.rankRewardsList.append(RankRewards.parse(rankRewards))
        ret.rankRewardsDesc = RankRewards.buildRewardDescList(ret.rankRewardsList)
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
            raise MatchConfException('rank.start must be int >= -1')
        if not isinstance(self.endRank, int) or self.endRank < -1:
            raise MatchConfException('rank.end must be int >= -1')
        if self.endRank != -1 and self.endRank < self.startRank:
            raise MatchConfException('rank.end must greater than rewards.rank.start')
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
                raise MatchConfException('reward item must dict')
            itemId = reward.get('itemId', None)
            if not isstring(itemId) or not itemId:
                raise MatchConfException('reward item.name must be not empty string')
            count = reward.get('count', None)
            if not isinstance(count, (int, float)) or count < 0:
                raise MatchConfException('reward item.count must be int or float >= 0')
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


class TipsConfig(object):
    def __init__(self):
        self.conf = None
        self.infos = None
        self.interval = None

    def checkValid(self):
        if not isinstance(self.infos, list):
            raise MatchConfException('tips.infos must be array')
        for info in self.infos:
            if not isstring(info):
                raise MatchConfException('tips.infos.item must be string')

        if not isinstance(self.interval, int) or self.interval <= 0:
            raise MatchConfException('tips.interval must be int > 0')
        return self

    @classmethod
    def parse(cls, conf):
        ret = cls()
        ret.conf = conf
        ret.infos = conf.get('infos', [])
        ret.interval = conf.get('interval', 5)
        return ret


class MatchFee(object):
    def __init__(self, assetKindId, count, params):
        self.assetKindId = assetKindId
        self.count = count
        self.params = params

    def getParam(self, paramName, defVal=None):
        return self.params.get(paramName, defVal)

    @property
    def failure(self):
        return self.getParam('failure', '')

    @classmethod
    def decodeFromDict(cls, d):
        assetKindId = d.get('itemId')
        if not isstring(assetKindId):
            raise TYBizConfException(d, 'MatchFee.itemId must be string')
        count = d.get('count')
        if not isinstance(count, int):
            raise TYBizConfException(d, 'MatchFee.count must be string')
        params = d.get('params', {})
        if not isinstance(params, dict):
            raise TYBizConfException(d, 'MatchFee.params must be dict')
        return MatchFee(assetKindId, count, params)

    def toDict(self):
        return {'itemId': self.assetKindId, 'count': self.count}


class MatchConfig(object):
    VALID_GAMEIDS = [3, 6, 7, 15, 17, 21]

    def __init__(self):
        self.conf = None
        self.gameId = None
        self.matchId = None
        self.matchId3 = None
        self.name = None
        self.tableSeatCount = None
        self.start = None
        self.fees = None
        self.tips = None
        self.stages = None
        self.rankRewardsList = None
        self.rankRewardsDesc = None
        self.tableId = None
        self.seatId = None
        self.recordId = None

    def checkValid(self):
        if not self.gameId in MatchConfig.VALID_GAMEIDS:
            raise MatchConfException('gameId must in:' + str(MatchConfig.VALID_GAMEIDS))
        if not isinstance(self.matchId, int):
            raise MatchConfException('matchId must be int')
        if self.matchId3 and not isstring(self.matchId3):
            raise MatchConfException('matchId3 must be string')
        if not isinstance(self.tableSeatCount, int) or self.tableSeatCount <= 0:
            raise MatchConfException('table.seat.count must be int > 0')
        return self

    @classmethod
    def getTipsConfigClass(cls):
        return TipsConfig

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
        ret.recordId = matchId
        ret.name = name
        ret.desc = conf.get('desc', '')
        ret.descMultiLang = conf.get('descMultiLang', {})
        ret.tableSeatCount = conf.get('table.seat.count', None)
        ret.matchId3 = conf.get('matchId3')
        start = conf.get('start', None)
        if not isinstance(start, dict):
            raise MatchConfException('start must be dict')
        ret.start = StartConfig.parse(start)

        fees = conf.get('fees', [])
        ret.fees = []
        for fee in fees:
            matchFee = MatchFee.decodeFromDict(fee)
            if matchFee.count > 0:
                ret.fees.append(matchFee)
        ret.tips = cls.getTipsConfigClass().parse(conf.get('tips', {}))
        ret.stages = []
        stages = conf.get('stages', None)
        if not isinstance(stages, list):
            raise MatchConfException('stages must be list')
        for i, stage in enumerate(stages):
            stage = StageConfig.parse(stage)
            stage.index = i
            ret.stages.append(stage)

        ret.rankRewardsList = []
        rankRewardsList = conf.get('rank.rewards')
        if rankRewardsList is not None:
            if not isinstance(rankRewardsList, list):
                raise MatchConfException('rank.rewards must be list')
            for rankRewards in rankRewardsList:
                ret.rankRewardsList.append(cls.getRankRewardsClass().parse(rankRewards))
        ret.rankRewardsDesc = cls.getRankRewardsClass().buildRewardDescList(ret.rankRewardsList)
        return ret.checkValid()
