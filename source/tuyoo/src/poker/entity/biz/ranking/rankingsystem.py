# -*- coding=utf-8
'''
Created on 2015年4月13日

@author: zhaojiangang
'''
import json
import time
from sre_compile import isstring

from datetime import date, datetime

import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from poker.entity.biz.confobj import TYConfable, TYConfableRegister
from poker.entity.biz.content import TYContentRegister
from poker.entity.biz.ranking.dao import TYRankingUserScoreInfo
from poker.entity.biz.ranking.exceptions import TYRankingConfException, \
    TYRankingUnknownException

_DEBUG = 0
debug = ftlog.info


class TYTimeCycle(object):
    def __init__(self, startTime, endTime):
        self.startTime = startTime
        self.endTime = endTime

    def inCycle(self, nt):
        if self.startTime > 0 and nt < self.startTime:
            return False
        if self.endTime > 0 and nt >= self.endTime:
            return False
        return True

    def buildIssueNumber(self):
        return date.fromtimestamp(self.startTime).strftime('%Y%m%d')


class TYRankingInputTypes:
    CHIP = 'chip'  # 用户金币
    DASHIFEN = 'dashifen'  # 大师分，金花分，雀神分, 牛掰分等
    DASHIFEN_INCR = 'dashifen_incr'  # 大师分增量榜等
    WINCHIP = 'winChip'  # 赢取的金币
    PK = 'pk'  # 德州PK值
    CHARM = 'charm'  # 魅力值
    DZFCWINCHIP = 'dzfcWinChip'  # 德州翻牌赢金
    FANTASY = 'fantasy'  # 大菠萝范特西数
    TOPHANDSSCORE = 'topHandsScore'  # 大菠萝最大手牌
    OPI = 'opi'  # 大菠萝赛季积分榜
    JIFEN = 'jifen'  # 中国象棋积分
    MTT = 'mtt'  # mtt比赛积分
    SNG = 'sng'  # sng 比赛积分
    MTTSNG = 'mttsng'  # mtt与sng比赛积分
    WINCHIP_DRAGON = 'winchip_dragon'  # 中发白赢金榜
    CHIP_DRAGON = 'chip_dragon'  # 中发白财富榜
    CHARM_DRAGON = 'charm_dragon'  # 中发白魅力值
    COUPON_BAOHUANG = 'coupon_baohuang'  # 保皇话费榜
    CHAMPION_BAOHUANG = 'champion_baohuang'  # 保皇冠军榜
    INVITE_BAOHUANG = 'invite_baohuang'  # 保皇邀请榜
    MAJIANG_LUKY_RAFFLE = 'majiang_luky_raffle'  # 麻将幸运大抽奖排行榜
    MAJIANG_TABLE_RAFFLE = 'majiang_table_raffle'  # 麻将拜雀神赢话费排行榜

    VIP_CLOWN = 'vip_clown'  # 小丑vip榜
    CHIP_CLOWN = 'chip_clown'  # 小丑财富榜
    WINCHIP_CLOWN = 'winchip_clown'  # 小丑赢金榜

    TRACTOR_TG = 'tractor_tg'  # 双升的通关次数


class TYRankingOpTypes:
    NORMAL = 'normal'  # 普通榜，设置的值直接在榜单中排序，不记录历史值
    INCR = 'incr'  # 增量榜，会累加每次写入的值
    MAX = 'max'  # 取最大值

    TYPES = set([NORMAL, INCR, MAX])
    NEED_RECORD_SCORE_TYPES = set([INCR, MAX])


class TYRankingCycle(TYConfable):
    def __init__(self, startTime=0, endTime=0):
        self.startTime = startTime
        self.endTime = endTime

    def getCurrentCycle(self, timestamp=None):
        '''
        @param nt: 当前时间戳
        @return: TYTimeCycle
        '''
        timestamp = timestamp if timestamp is not None else pktimestamp.getCurrentTimestamp()

        if self.endTime > 0 and timestamp >= self.endTime:
            return None

        cycle = self._getCurrentCycle(timestamp)

        if self.startTime > 0 and self.startTime > cycle.startTime:
            cycle.startTime = self.startTime

        if self.endTime > 0 and cycle and self.endTime > cycle.endTime:
            cycle.endTime = self.endTime

        return cycle

    def inCollectCycle(self, timeCycle, timestamp):
        return timeCycle.inCycle(timestamp)

    def decodeFromDict(self, d):
        startTime = d.get('startTime')
        endTime = d.get('endTime')
        if startTime is not None:
            try:
                self.startTime = time.mktime(datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S').timetuple())
            except:
                raise TYRankingConfException(d, 'Bad startTime: %s' % (startTime))
        else:
            self.startTime = 0

        if endTime:
            try:
                self.endTime = time.mktime(datetime.strptime(endTime, '%Y-%m-%d %H:%M:%S').timetuple())
            except:
                raise TYRankingConfException(d, 'Bad endTime: %s' % (endTime))
        else:
            self.endTime = 0

        self._decodeFromDictImpl(d)
        return self

    def _getCurrentCycle(self, timestamp):
        raise NotImplemented()

    def _decodeFromDictImpl(self, d):
        pass


class TYRankingCycleDay(TYRankingCycle):
    TYPE_ID = 'day'

    def __init__(self, startTime=0, endTime=0):
        super(TYRankingCycleDay, self).__init__(startTime, endTime)

    def _getCurrentCycle(self, timestamp):
        startTime = pktimestamp.getDayStartTimestamp(timestamp)
        return TYTimeCycle(startTime, startTime + 86400)


class TYRankingCycleWeek(TYRankingCycle):
    TYPE_ID = 'week'

    def __init__(self, startTime=0, endTime=0):
        super(TYRankingCycleWeek, self).__init__(startTime, endTime)

    def _getCurrentCycle(self, timestamp):
        startTime = pktimestamp.getWeekStartTimestamp(timestamp)
        return TYTimeCycle(startTime, startTime + 7 * 86400)


class TYRankingCycleMonth(TYRankingCycle):
    TYPE_ID = 'month'

    def __init__(self, startTime=0, endTime=0):
        super(TYRankingCycleMonth, self).__init__(startTime, endTime)

    def _getCurrentCycle(self, timestamp):
        return TYTimeCycle(pktimestamp.getDeltaMonthStartTimestamp(timestamp, 0),
                           pktimestamp.getDeltaMonthStartTimestamp(timestamp, 1))


class TYRankingCycleLife(TYRankingCycle):
    TYPE_ID = 'life'

    def __init__(self, startTime=0, endTime=0):
        super(TYRankingCycleLife, self).__init__(startTime, endTime)

    def _getCurrentCycle(self, timestamp):
        return TYTimeCycle(self.startTime, self.endTime)


class TYRankingCycleRegister(TYConfableRegister):
    _typeid_clz_map = {
        TYRankingCycleDay.TYPE_ID: TYRankingCycleDay,
        TYRankingCycleWeek.TYPE_ID: TYRankingCycleWeek,
        TYRankingCycleMonth.TYPE_ID: TYRankingCycleMonth,
        TYRankingCycleLife.TYPE_ID: TYRankingCycleLife
    }


class TYRankingRankReward(object):
    def __init__(self):
        self.startRank = None
        self.endRank = None
        self.rewardContent = None

    @classmethod
    def decodeFromDict(self, d):
        startRank = d.get('start', -1)
        endRank = d.get('end', -1)
        if startRank <= 0 and startRank != -1:
            raise TYRankingConfException(d, 'rankReward.start must > 0 or == -1')
        if endRank <= 0 and endRank != -1:
            raise TYRankingConfException(d, 'rankReward.endRank must > 0 or == -1')
        if endRank != -1 and endRank < startRank:
            raise TYRankingConfException(d, 'rankReward.endRank must >= startRank')
        rewardContent = d.get('rewardContent')
        if rewardContent is not None:
            rewardContent = TYContentRegister.decodeFromDict(rewardContent)
        ret = TYRankingRankReward()
        ret.startRank = startRank
        ret.endRank = endRank
        ret.rewardContent = rewardContent
        return ret


class TYRankingStatus(object):
    STATE_NORMAL = 0
    STATE_FINISH = 1
    STATE_REWARDS = 2

    class Item(object):
        def __init__(self, issueNumber, timeCycle, state):
            self.issueNumber = issueNumber
            self.timeCycle = timeCycle
            self.state = state

    def __init__(self, rankingDefine, totalNumber, historyList):
        self.rankingDefine = rankingDefine
        self.historyList = sorted(historyList, key=lambda h: h.issueNumber)
        self.totalNumber = totalNumber

    def getLastItem(self):
        return self.historyList[-1] if self.historyList else None

    def addItem(self, issueNumber, timeCycle):
        lastItem = self.getLastItem()
        if not lastItem or issueNumber > lastItem.issueNumber:
            self.historyList.append(TYRankingStatus.Item(issueNumber, timeCycle, TYRankingStatus.STATE_NORMAL))
            self.totalNumber += 1
            return True
        return False

    def count(self):
        return len(self.historyList)

    def removeFront(self):
        assert (len(self.historyList) > 0)
        historyItem = self.historyList[0]
        del self.historyList[0]
        return historyItem


class TYRankingScoreCalc(TYConfable):
    def calcScore(self, oldScore, opScore):
        '''
        根据老的socre和当前操作的score
        '''
        raise NotImplemented()

    def decodeFromDict(self, d):
        self._decodeFromDictImpl(d)
        return self

    def _decodeFromDictImpl(self, d):
        pass


class TYRankingScoreCalcRegister(TYConfableRegister):
    _typeid_clz_map = {}


class TYRankingDefine(TYConfable):
    def __init__(self):
        self.rankingId = None
        self.rankingIdInt = None
        self.name = None
        self.desc = None
        self.maxIssueNumber = None
        self.keepNumbers = None
        self.gameIds = None
        self.inputType = None
        self.scoreCalc = None
        self.rankingType = None
        self.rankPics = None
        self.topN = None
        self.totalN = None
        self.cycle = None
        self.cacheTimes = None
        self.rankRewardsList = None
        self.outRankDesc = None
        self.inRankDesc = None
        self.rewardMail = None

    # 获取排行图标
    def getPicByRank(self, rank):
        pic = self.rankPics.get(rank)
        if not pic:
            pic = self.rankPics.get(-1)
        return pic if pic is not None else ''

    # 检查是否支持给定的gameId
    def isSupportGameId(self, gameId):
        return gameId in self.gameIds or 0 in self.gameIds

    # 检查是否支持给定的gameId
    def isSupportInputType(self, inputType):
        return inputType == self.inputType

    # 检查是否支持给定的gameId
    def isSupport(self, gameId, inputType):
        return self.isSupportInputType(inputType) and self.isSupportGameId(gameId)

    def getCurrentIssueNumber(self, timestamp=None):
        timeCycle = self.getCurrentCycle(timestamp)
        if timeCycle:
            return timeCycle.buildIssueNumber()
        return None

    def inCollectCycle(self, timeCycle, nt):
        return self.cycle.inCollectCycle(timeCycle, nt)

    # 获取当前时间周期
    def getCurrentCycle(self, timestamp=None):
        return self.cycle.getCurrentCycle(timestamp)

    def getRewardsByRank(self, rank):
        if self.rankRewardsList:
            for rankRewards in self.rankRewardsList:
                if rankRewards.startRank > 0 and rank < rankRewards.startRank:
                    continue
                if rankRewards.endRank > 0 and rank > rankRewards.endRank:
                    continue
                return rankRewards
        return None

    def getHasRewardMaxRank(self):
        if not self.rankRewardsList:
            return -1
        maxRank = -1
        for rankRewards in self.rankRewardsList:
            endRank = self.topN if rankRewards.endRank < 0 else rankRewards.endRank
            maxRank = max(endRank, maxRank)
        return maxRank

    def decodeFromDict(self, d):
        self.rankingId = d.get('rankingId')
        if not isstring(self.rankingId):
            raise TYRankingConfException(d, 'ranking.rankingId must be string')
        try:
            int(self.rankingId)
        except:
            raise TYRankingConfException(d, 'ranking.rankingId must be convert int')

        self.name = d.get('name')
        if not isstring(self.name):
            raise TYRankingConfException(d, 'ranking.name must be string')
        self.desc = d.get('desc', '')
        if not isstring(self.desc):
            raise TYRankingConfException(d, 'ranking.desc must be string')
        self.maxIssueNumber = d.get('maxIssueNumber', 0)
        if not isinstance(self.maxIssueNumber, int):
            raise TYRankingConfException(d, 'ranking.maxIssueNumber must be int')
        self.keepNumbers = d.get('keepNumbers', 10)
        if not isinstance(self.keepNumbers, int) or self.keepNumbers <= 0:
            raise TYRankingConfException(d, 'ranking.keepNumbers must be int > 0')
        self.gameIds = d.get('gameIds', [])
        if not isinstance(self.gameIds, list):
            raise TYRankingConfException(d, 'ranking.gameIds must be list')
        for gameId in self.gameIds:
            if not isinstance(gameId, int):
                raise TYRankingConfException(d, 'ranking.gameIds.item must be int')
        self.inputType = d.get('inputType')
        if not isstring(self.inputType):
            raise TYRankingConfException(d, 'ranking.inputType must be string')
        self.scoreCalc = TYRankingScoreCalcRegister.decodeFromDict(d.get('scoreType'))

        # 透传给客户端
        self.rankingType = d.get('type')
        if not self.rankingType:
            raise TYRankingConfException(d, 'ranking.type must be dict')

        rankPics = d.get('rankPics')
        if not isinstance(rankPics, list):
            raise TYRankingConfException(d, 'ranking.rankPics must be list')

        self.rewardMail = d.get('rewardMail', '')
        if not isstring(self.rewardMail):
            raise TYRankingConfException(d, 'ranking.rewardMail must be string')

        self.rankPics = {}
        for rankPic in rankPics:
            rank = rankPic.get('rank')
            if not isinstance(rank, int):
                raise TYRankingConfException(d, 'ranking.rankPics.item.rank must be int')
            pic = rankPic.get('pic')
            if not isstring(pic):
                raise TYRankingConfException(d, 'ranking.rankPics.item.rank must be string')
            self.rankPics[rank] = pic

        self.topN = d.get('topN')
        if not isinstance(self.topN, int) or self.topN <= 0:
            raise TYRankingConfException(d, 'ranking.topN must be int > 0')

        self.totalN = d.get('totalN')
        if not isinstance(self.totalN, int) or self.totalN <= 0:
            raise TYRankingConfException(d, 'ranking.totalN must be int > 0')

        self.cacheTimes = d.get('cacheTimes', 0)
        if not isinstance(self.cacheTimes, int):
            raise TYRankingConfException(d, 'ranking.cacheTimes must be int')

        self.cycle = TYRankingCycleRegister.decodeFromDict(d.get('cycle'))

        rankDesc = d.get('rankDesc', {})
        if not isinstance(rankDesc, dict):
            raise TYRankingConfException(d, 'ranking.rankDesc must be dict')

        self.inRankDesc = rankDesc.get('in', u'您在${rankName}的排名是：${rank}').replace('${rankName}', self.name)
        self.outRankDesc = rankDesc.get('out', u'暂未进入${rankName}，加油哦！').replace('${rankName}', self.name)

        rankRewardsListConf = d.get('rankRewardList', [])
        if not isinstance(rankRewardsListConf, list):
            raise TYRankingConfException(d, 'ranking.rankRewardList must be list')

        rankRewardsList = []
        for rankRewardsConf in rankRewardsListConf:
            rankRewardsList.append(TYRankingRankReward.decodeFromDict(rankRewardsConf))

        self.rankRewardsList = rankRewardsList

        return self


class TYRankingUser(object):
    def __init__(self, userId, score, rank):
        self.userId = userId
        self.score = score
        self.rank = rank


class TYRankingList(object):
    def __init__(self, rankingDefine, issueNumber, timeCycle, rankingUserList):
        self.rankingDefine = rankingDefine
        self.issueNumber = issueNumber
        self.timeCycle = timeCycle
        self.rankingUserList = rankingUserList
        self.rankingUserMap = {}
        if self.rankingUserList:
            for rankingUser in self.rankingUserList:
                self.rankingUserMap[rankingUser.userId] = rankingUser


class TYRankingSystem(object):
    def getRankingDefines(self):
        '''
        获取所有排行榜配置
        @return list<TYRankingDefine>
        '''
        raise NotImplemented()

    def getRankingDefinesForRankingKey(self, rankingKey, templateName):
        '''
        获取rankingKey下的tempateName包含的排行榜配置
        @return: list<TYRankingDefine>
        '''
        raise NotImplemented()

    def processRankings(self, timestamp=None):
        '''
        处理所有的排行榜，改创建的创建，改发奖的发奖
        '''
        raise NotImplemented()

    def findRankingDefine(self, rankingId):
        '''
        查找rankingId的排行榜配置
        '''
        raise NotImplemented()

    def setUserByInputType(self, gameId, inputType, userId, score, timestamp=None):
        '''
        更新所有能处理inputType和gameId的排行榜中指定用户的信息
        @return: map<rankingId, rankingUser>
        '''
        raise NotImplemented()

    def removeUserByInputType(self, gameId, inputType, userId, timestamp=None):
        '''
        删除所有能处理inputType的排行榜中指定用户的信息
        '''
        raise NotImplemented()

    def setUserScore(self, rankingId, userId, score, timestamp=None):
        '''
        更新排行榜中指定用户的信息
        @param rankingId: 排行榜ID
        @param rankingUser: 排行榜用户
        @param nt: 用户记录的时间戳，如果为None则用当前时间戳
        @return: TYRankingUser
        '''
        raise NotImplemented()

    def removeUser(self, rankingId, userId, timestamp=None):
        '''
        删除排行榜中userId的用户
        @param rankingId: 排行榜ID
        @param userId: 要删除的用户ID
        @param nt: 时间戳
        '''
        raise NotImplemented()

    def removeRanking(self, rankingId):
        '''
        删除排行榜
        @param rankingId: 要删除的排行榜ID 
        '''
        raise NotImplemented()

    def getTopN(self, rankingId, topN=None, timestamp=None):
        '''
        获取nt所在期排行榜topN用户ID列表
        @param rankingId: 排行榜ID
        @param topN: topN的数量，如果是None表示按照配置的topN返回
        @param nt: 当前时间戳
        @return: TYRankingList or None
        '''
        raise NotImplemented()

    def getRankingUser(self, rankingId, userId, timestamp=None):
        '''
        获取nt所在期排行榜中userId的信息
        @param rankingId: 排行榜ID
        @param topN: topN的数量，如果是None表示按照配置的topN返回
        @param nt: 当前时间戳
        @return: TYRankingUser or None
        '''
        raise NotImplemented()


class TYRankingSystemImpl(TYRankingSystem):
    def __init__(self, scoreInfoDao, rankingDao, rewardSender):
        self._scoreInfoDao = scoreInfoDao
        self._rankingDao = rankingDao
        self._rewardSender = rewardSender
        self._rankingDefineMap = {}
        # key=rankingKey, value=map<templateName, list<rankingDefine>>
        self._rankingKeyMap = {}

    def reloadConf(self, conf):
        rankingDefineConfList = conf.get('list', [])
        rankingDefineMap = {}
        rankingKeyMap = {}
        for rankingDefineConf in rankingDefineConfList:
            rankingDefine = TYRankingDefine().decodeFromDict(rankingDefineConf)
            if rankingDefine.rankingId in rankingDefineMap:
                raise TYRankingConfException(rankingDefineConf, 'Duplicate rankingId %s' % (rankingDefine.rankingId))
            rankingDefineMap[rankingDefine.rankingId] = rankingDefine
        for rankingKey, templateMap in conf.get('rankingKeys', {}).iteritems():
            for templateName, rankingIdList in templateMap.iteritems():
                rankingDefineList = []
                for rankingId in rankingIdList:
                    rankingDefine = rankingDefineMap.get(rankingId)
                    if not rankingDefine:
                        raise TYRankingConfException(templateMap, 'Unknown rankingId %s' % (rankingId))
                    rankingDefineList.append(rankingDefine)
                rankingKeyMap[rankingKey] = {templateName: rankingDefineList}
                if _DEBUG:
                    debug('TYRankingSystemImpl.reloadConf rankingKey=', rankingKey,
                          'rankingIdList=', rankingIdList)

        self._rankingDefineMap = rankingDefineMap
        self._rankingKeyMap = rankingKeyMap
        if _DEBUG:
            debug('TYRankingSystemImpl.reloadConf successed rankingDefines=', self._rankingDefineMap.keys(),
                  'rankingKeys=', self._rankingKeyMap.keys())

    def getRankingDefinesForRankingKey(self, rankingKey, templateName):
        '''
        获取rankingKey下的tempateName包含的排行榜配置
        @return: list<TYRankingDefine>
        '''
        rankingTemplateMap = self._rankingKeyMap.get(rankingKey)
        if ftlog.is_debug():
            ftlog.debug('TYRankingSystemImpl.getRankingDefinesForRankingKey rankingKey=', rankingKey,
                        'templateName=', templateName,
                        'templateNames=', rankingTemplateMap.keys() if rankingTemplateMap else None)
        if not rankingTemplateMap:
            return []
        return rankingTemplateMap.get(templateName, [])

    def getRankingDefines(self):
        '''
        获取所有排行榜配置
        return list<TYRankingDefine>
        '''
        return self._rankingDefineMap.values()

    def processRankings(self, timestamp=None):
        '''
        处理所有的排行榜，改创建的创建，改发奖的发奖
        '''
        timestamp = timestamp or pktimestamp.getCurrentTimestamp()
        if _DEBUG:
            debug('TYRankingSystemImpl.processRankings timestamp=', timestamp)
        rankingDefineList = list(self._rankingDefineMap.values())
        for rankingDefine in rankingDefineList:
            self._processRanking(rankingDefine, timestamp)

    def findRankingDefine(self, rankingId):
        '''
        查找rankingId的排行榜配置
        '''
        return self._rankingDefineMap.get(rankingId)

    def setUserByInputType(self, gameId, inputType, userId, score, timestamp=None):
        '''
        更新所有能处理inputType和gameId的排行榜中指定用户的信息
        @return: map<rankingId, rankingUser>
        '''
        timestamp = timestamp or pktimestamp.getCurrentTimestamp()
        retMap = {}
        ftlog.debug('TYRankingSystemImpl.setUserByInputType gameId=', gameId,
                    'inputType=', inputType,
                    'userId=', userId,
                    'score=', score,
                    'timestamp=', timestamp)

        rankingDefineList = list(self._rankingDefineMap.values())
        for rankingDefine in rankingDefineList:
            if rankingDefine.isSupport(gameId, inputType):
                rank = self._setUserByRankingDefine(rankingDefine, userId, score, timestamp)
                if rank >= 0:
                    retMap[rankingDefine.rankingId] = TYRankingUser(userId, score, rank)
                ftlog.debug('TYRankingSystemImpl.setUserByInputType gameId=', gameId,
                            'inputType=', inputType,
                            'userId=', userId,
                            'score=', score,
                            'rankingDefine.gameIds=', rankingDefine.gameIds,
                            'rankingDefine.inputType=', rankingDefine.inputType,
                            'rank=', rank)
            else:
                ftlog.debug('TYRankingSystemImpl.setUserByInputType NotSupport gameId=', gameId,
                            'inputType=', inputType,
                            'userId=', userId,
                            'score=', score,
                            'rankingDefine.gameIds=', rankingDefine.gameIds,
                            'rankingDefine.inputType=', rankingDefine.inputType)
        return retMap

    def removeUserByInputType(self, gameId, inputType, userId, timestamp=None):
        '''
        删除所有能处理inputType的排行榜中指定用户的信息
        '''
        timestamp = timestamp or pktimestamp.getCurrentTimestamp()
        rankingDefineList = list(self._rankingDefineMap.values())
        for rankingDefine in rankingDefineList:
            if rankingDefine.isSupport(gameId, inputType):
                self._removeUserByRankingDefine(rankingDefine, userId, timestamp)

    def setUserScore(self, rankingId, userId, score, timestamp=None):
        '''
        更新排行榜中指定用户的信息
        @param rankingId: 排行榜ID
        @param rankingUser: 排行榜用户
        @param nt: 用户记录的时间戳，如果为None则用当前时间戳
        @return: TYRankingUser
        '''
        rankingDefine = self.findRankingDefine(rankingId)
        if not rankingDefine:
            raise TYRankingUnknownException(rankingId)
        timestamp = timestamp or pktimestamp.getCurrentTimestamp()
        rank = self._setUserByRankingDefine(rankingDefine, userId, score, timestamp)
        return TYRankingUser(userId, score, rank)

    def removeUser(self, rankingId, userId, timestamp=None):
        '''
        删除排行榜中userId的用户
        @param rankingId: 排行榜ID
        @param userId: 要删除的用户ID
        @param nt: 时间戳
        '''
        rankingDefine = self.findRankingDefine(rankingId)
        if not rankingDefine:
            raise TYRankingUnknownException(rankingId)
        timestamp = timestamp or pktimestamp.getCurrentTimestamp()
        if _DEBUG:
            debug('TYRankingSystemImpl.removeUser rankingId=', rankingId, 'userId=', userId)
        return self._removeUserByRankingDefine(rankingDefine, userId, timestamp)

    def removeRanking(self, rankingId):
        '''
        删除排行榜
        @param rankingId: 要删除的排行榜ID 
        '''
        rankingDefine = self._rankingDefineMap.get(rankingId)
        if not rankingDefine:
            raise TYRankingUnknownException(rankingId)
        if _DEBUG:
            debug('TYRankingSystemImpl.removeRanking rankingId=', rankingId)
        status = self._loadRankingStatus(rankingDefine)
        if status:
            for item in status.historyList:
                self._rankingDao.removeRankingList(rankingId, item.issueNumber)
            self._rankingDao.removeRankingStatus(rankingId)

    def getTopN(self, rankingId, topN=None, timestamp=None):
        '''
        获取nt所在期排行榜topN用户ID列表
        @param rankingId: 排行榜ID
        @param topN: topN的数量，如果是None表示按照配置的topN返回
        @param nt: 当前时间戳
        @return: TYRankingList or None
        '''
        rankingDefine = self.findRankingDefine(rankingId)
        if not rankingDefine:
            raise TYRankingUnknownException(rankingId)
        topN = topN or rankingDefine.topN
        timestamp = timestamp or pktimestamp.getCurrentTimestamp()
        timeCycle = rankingDefine.getCurrentCycle(timestamp)
        if timeCycle:
            issueNumber = timeCycle.buildIssueNumber()
            rankingUserList = self._getTopNByRankingDefine(rankingDefine, issueNumber, topN)
            return TYRankingList(rankingDefine, issueNumber, timeCycle, rankingUserList)
        return None

    def getRankingUser(self, rankingId, userId, timestamp=None):
        '''
        获取nt所在期排行榜中userId的信息
        @param rankingId: 排行榜ID
        @param topN: topN的数量，如果是None表示按照配置的topN返回
        @param nt: 当前时间戳
        @return: TYRankingUser or None
        '''
        rankingDefine = self._rankingDefineMap.get(rankingId)
        if not rankingDefine:
            raise TYRankingUnknownException(rankingId)
        timestamp = timestamp or pktimestamp.getCurrentTimestamp()
        issueNumber = rankingDefine.getCurrentIssueNumber(timestamp)
        if issueNumber:
            return self._getRankingUserByRankingDefine(rankingDefine, issueNumber, userId)
        return None

    def _processRanking(self, rankingDefine, timestamp):
        if _DEBUG:
            debug('TYRankingSystemImpl._processRanking rankingId=', rankingDefine.rankingId,
                  'timestamp=', timestamp)

        try:
            status, changed = self._loadOrCreateRankingStatus(rankingDefine, timestamp)
            if not status:
                return

            lastItem = status.getLastItem()

            # 检查是否没有下一期了
            timeCycle = rankingDefine.getCurrentCycle(timestamp)
            if not timeCycle:
                if lastItem and lastItem.state == TYRankingStatus.STATE_NORMAL:
                    if _DEBUG:
                        debug('TYRankingSystemImpl._processRanking Finished rankingId=', rankingDefine.rankingId,
                              'issueNumber=', lastItem.issueNumber,
                              'timestamp=', timestamp)
                    lastItem.state = TYRankingStatus.STATE_FINISH
                    changed = True
            else:
                issueNumber = timeCycle.buildIssueNumber()
                if lastItem and issueNumber > lastItem.issueNumber:
                    if lastItem.state == TYRankingStatus.STATE_NORMAL:
                        lastItem.state = TYRankingStatus.STATE_FINISH
                        changed = True
                        if _DEBUG:
                            debug('TYRankingSystemImpl._processRanking Finished rankingId=', rankingDefine.rankingId,
                                  'issueNumber=', lastItem.issueNumber,
                                  'timestamp=', timestamp)
                if not lastItem or issueNumber > lastItem.issueNumber:
                    if (status.rankingDefine.maxIssueNumber <= 0
                        or status.totalNumber < status.rankingDefine.maxIssueNumber):
                        status.addItem(issueNumber, timeCycle)
                        status.totalNumber += 1
                        if _DEBUG:
                            debug('TYRankingSystemImpl._processRanking Create rankingId=', rankingDefine.rankingId,
                                  'issueNumber=', issueNumber,
                                  'totalNumber=', status.totalNumber,
                                  'timestamp=', timestamp)
                        changed = True

            # 检查需要发奖的所有榜单
            for item in status.historyList:
                if item.state == TYRankingStatus.STATE_FINISH:
                    changed = True
                    self._doReward(status, item)

            while status.count() > status.rankingDefine.keepNumbers:
                item = status.removeFront()
                self._rankingDao.removeRankingList(status.rankingDefine.rankingId, item.issueNumber)
                changed = True

            if changed:
                self._saveRankingStatus(status)
        except:
            ftlog.error()

    def _setUserByRankingDefine(self, rankingDefine, userId, score, timestamp):
        timeCycle = rankingDefine.cycle.getCurrentCycle(timestamp)

        # 当前没有改榜了
        if timeCycle is None:
            ftlog.debug('TYRankingSystemImpl._setUserByRankingDefine NoneCycle rankingId=', rankingDefine.rankingId,
                        'userId=', userId,
                        'score=', score,
                        'timestamp=', timestamp)
            return -1

        # 当前时间不在本周期内
        if not rankingDefine.inCollectCycle(timeCycle, timestamp):
            ftlog.debug('TYRankingSystemImpl._setUserByRankingDefine NotInCycle rankingId=', rankingDefine.rankingId,
                        'timeCycle=', '[%s,%s)' % (timeCycle.startTime, timeCycle.endTime),
                        'userId=', userId,
                        'score=', score,
                        'timestamp=', timestamp)
            return -1

        newScore = score
        issueNumber = timeCycle.buildIssueNumber()
        scoreInfo = self._scoreInfoDao.loadScoreInfo(rankingDefine.rankingId, userId)
        if scoreInfo and scoreInfo.issueNumber == issueNumber:
            newScore = rankingDefine.scoreCalc.calcScore(scoreInfo.score, score)
            if newScore != scoreInfo.score:
                scoreInfo.score = newScore
                self._scoreInfoDao.saveScoreInfo(rankingDefine.rankingId, userId, scoreInfo)
        else:
            scoreInfo = TYRankingUserScoreInfo(score, issueNumber)
            self._scoreInfoDao.saveScoreInfo(rankingDefine.rankingId, userId, scoreInfo)

        ftlog.debug('TYRankingSystemImpl._setUserByRankingDefine rankingId=', rankingDefine.rankingId,
                    'timeCycle=', '[%s,%s)' % (timeCycle.startTime, timeCycle.endTime),
                    'userId=', userId,
                    'score=', score,
                    'newScore=', newScore,
                    'timestamp=', timestamp)
        return self._rankingDao.setUserScore(rankingDefine.rankingId, issueNumber,
                                             userId, newScore, rankingDefine.totalN)

    def _getRankingUserByRankingDefine(self, rankingDefine, issueNumber, userId):
        rank, score = self._rankingDao.getUserRankWithScore(rankingDefine.rankingId, issueNumber, userId)
        return TYRankingUser(userId, score, rank)

    def _removeUserByRankingDefine(self, rankingDefine, userId, nt=None):
        issueNumber = rankingDefine.getCurrentIssueNumber()
        if issueNumber:
            return self._rankingDao.removeUser(rankingDefine.rankingId, issueNumber, userId)
        return False

    def _getTopNByRankingDefine(self, rankingDefine, issueNumber, topN):
        rankingUserList = []
        userIdWithScores = self._rankingDao.getTopN(rankingDefine.rankingId, issueNumber, topN)
        if userIdWithScores:
            for i in xrange(len(userIdWithScores) / 2):
                userId = int(userIdWithScores[i * 2])
                score = int(userIdWithScores[i * 2 + 1])
                rankingUserList.append(TYRankingUser(userId, score, i))
        return rankingUserList

    def _loadOrCreateRankingStatus(self, rankingDefine, nt):
        status = self._loadRankingStatus(rankingDefine)
        if not status:
            timeCycle = rankingDefine.getCurrentCycle(nt)
            if not timeCycle:
                if _DEBUG:
                    debug('TYRankingSystemImpl._loadOrCreateRankingStatus End rankingId=', rankingDefine.rankingId,
                          'nt=', nt)
                return None, False
            issueNumber = timeCycle.buildIssueNumber()
            status = TYRankingStatus(rankingDefine, 0, [])
            status.addItem(issueNumber, timeCycle)
            if _DEBUG:
                debug('TYRankingSystemImpl._loadOrCreateRankingStatus Create rankingId=', rankingDefine.rankingId,
                      'issueNumber=', issueNumber,
                      'nt=', nt)
            return status, True
        return status, False

    def _loadRankingStatus(self, rankingDefine):
        jstr = self._rankingDao.loadRankingStatusData(rankingDefine.rankingId)
        if not jstr:
            return None
        d = json.loads(jstr)
        historyList = d.get('histories', [])
        totalNumber = d.get('totalNumber', 0)
        itemList = []
        for history in historyList:
            timeCycle = TYTimeCycle(history['startTime'], history['endTime'])
            itemList.append(TYRankingStatus.Item(history['issueNumber'], timeCycle, history['state']))
        return TYRankingStatus(rankingDefine, totalNumber, itemList)

    def _saveRankingStatus(self, status):
        historyList = []
        for item in status.historyList:
            historyList.append({'issueNumber': item.issueNumber,
                                'state': item.state,
                                'startTime': item.timeCycle.startTime,
                                'endTime': item.timeCycle.endTime
                                })
        d = {'histories': historyList, 'totalNumber': status.totalNumber}
        jstr = json.dumps(d)
        self._rankingDao.saveRankingStatusData(status.rankingDefine.rankingId, jstr)

    def _doReward(self, status, item):
        item.state = TYRankingStatus.STATE_REWARDS
        maxRank = status.rankingDefine.getHasRewardMaxRank()
        if _DEBUG:
            debug('TYRankingSystemImpl._doReward rankingId=', status.rankingDefine.rankingId,
                  'issueNumber=', item.issueNumber,
                  'maxRank=', maxRank)
        if maxRank >= 0:
            rankingUserList = self._getTopNByRankingDefine(status.rankingDefine, item.issueNumber, maxRank + 1)
            for rankingUser in rankingUserList:
                self._sendReward(status, item, rankingUser)

    def _sendReward(self, status, item, rankingUser):
        rankReward = status.rankingDefine.getRewardsByRank(rankingUser.rank + 1)
        if rankReward and rankReward.rewardContent:
            self._rewardSender.sendReward(status.rankingDefine, item.issueNumber, rankingUser, rankReward.rewardContent)
