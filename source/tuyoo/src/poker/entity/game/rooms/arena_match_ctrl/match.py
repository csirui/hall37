# -*- coding:utf-8 -*-
'''
Created on 2015年12月2日

@author: zhaojiangang
'''
import random
import time
from sre_compile import isstring

from datetime import datetime, timedelta

import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from freetime.core.timer import FTLoopTimer, FTTimer
from poker.entity.biz.content import TYContentItem
from poker.entity.biz.exceptions import TYBizConfException
from poker.entity.game.rooms import roominfo
from poker.entity.game.rooms.arena_match_ctrl.exceptions import \
    AlreadySigninException, AlreadyInMatchException, NotSigninException, \
    MatchException, SigninFullException, EnterMatchLocationException, \
    SigninNotStartException, MatchExpiredException, MatchSigninException
from poker.entity.game.rooms.big_match_ctrl.const import MatchFinishReason
from poker.entity.game.rooms.roominfo import MatchRoomInfo
from poker.util import strutil, sortedlist


class MatchSeat(object):
    def __init__(self, table, seatId):
        # 属于哪个桌子
        self._table = table
        # seatId
        self._seatId = seatId
        # location
        self._location = '%s.%s.%s.%s' % (table.gameId, table.roomId, table.tableId, seatId)
        # 当前座位上的玩家
        self._player = None

    @property
    def table(self):
        return self._table

    @property
    def tableId(self):
        return self._table.tableId

    @property
    def seatId(self):
        return self._seatId

    @property
    def location(self):
        return self._location

    @property
    def player(self):
        return self._player


class MatchTable(object):
    def __init__(self, gameId, roomId, tableId, seatCount):
        # 哪个游戏
        self._gameId = gameId
        # 房间ID
        self._roomId = roomId
        # 桌子ID
        self._tableId = tableId
        # 所有座位
        self._seats = self._makeSeats(seatCount)
        # 空闲座位
        self._idleSeats = self._seats[:]
        # 校验值
        self._ccrc = 0
        # 本桌开始时间
        self._startTime = 0
        # 哪个比赛
        self._matchInst = None

    @property
    def gameId(self):
        return self._gameId

    @property
    def roomId(self):
        return self._roomId

    @property
    def tableId(self):
        return self._tableId

    @property
    def startTime(self):
        return self._startTime

    @property
    def seats(self):
        '''
        座位列表
        '''
        return self._seats

    @property
    def seatCount(self):
        '''
        座位数量
        '''
        return len(self._seats)

    @property
    def idleSeatCount(self):
        '''
        空闲座位的数量
        '''
        return len(self._idleSeats)

    @property
    def ccrc(self):
        return self._ccrc

    @property
    def matchInst(self):
        return self._matchInst

    def getPlayerList(self):
        '''
        获取本桌的所有player
        '''
        return [seat.player for seat in self.seats if seat.player]

    def getUserIdList(self):
        '''
        获取本桌所有userId
        '''
        return [seat.player.userId for seat in self.seats if seat.player]

    def sitdown(self, player):
        '''
        玩家坐下
        '''
        assert (player._seat is None)
        assert (len(self._idleSeats) > 0)
        seat = self._idleSeats[-1]
        del self._idleSeats[-1]
        seat._player = player
        player._table = self
        player._seat = seat

    def standup(self, player):
        '''
        玩家离开桌子
        '''
        assert (player._seat is not None
                and player._seat.table == self)
        self._clearSeat(player._seat)

    def clear(self):
        '''
        清理桌子上的所有玩家
        '''
        for seat in self._seats:
            if seat._player:
                self.standup(seat._player)

    def _clearSeat(self, seat):
        seat._player._seat = None
        seat._player = None
        self._idleSeats.append(seat)

    def _makeSeats(self, count):
        assert (count > 0)
        seats = []
        for i in xrange(count):
            seats.append(MatchSeat(self, i + 1))
        return seats


class MatchTableManager(object):
    def __init__(self, gameId, tableSeatCount):
        self._gameId = gameId
        self._tableSeatCount = tableSeatCount
        self._idleTables = []
        self._allTableMap = {}
        self._roomIds = set()

    @property
    def tableSeatCount(self):
        return self._tableSeatCount

    @property
    def roomCount(self):
        return len(self._roomIds)

    @property
    def allTableCount(self):
        return len(self._allTableMap)

    @property
    def idleTableCount(self):
        return len(self._idleTables)

    @property
    def busyTableCount(self):
        return max(0, self.allTableCount - self.idleTableCount())

    def getTableCountPerRoom(self):
        return len(self._allTableMap) / max(1, self.getRoomCount())

    def addTables(self, roomId, baseId, count):
        if count > 0:
            self._roomIds.add(roomId)
        for i in xrange(count):
            tableId = baseId + i + 1  # 新框架里tableId 从 1开始计数， 0表示队列。
            table = MatchTable(self._gameId, roomId, tableId, self._tableSeatCount)
            self._idleTables.append(table)
            self._allTableMap[tableId] = table

    def borrowTables(self, count):
        assert (self.idleTableCount >= count)
        ret = self._idleTables[0:count]
        self._idleTables = self._idleTables[count:]
        return ret

    def returnTables(self, tables):
        for table in tables:
            assert (self._allTableMap.get(table.tableId, None) == table)
            assert (not table.getPlayerList())
            self._idleTables.append(table)

    def findTable(self, roomId, tableId):
        return self._allTableMap.get(tableId, None)


class MatchPlayer(object):
    # 报名成功
    STATE_SIGNIN = 0
    # 等待状态
    STATE_WAIT = 1
    # 正在打牌
    STATE_PLAYING = 2
    # 一局结束
    STATE_WINLOSE = 3
    # 晋级状态
    STATE_RISE = 4
    # 游戏结束
    STATE_OVER = 5

    def __init__(self, matchInst, userId, signinTime):
        # 在哪个比赛
        self._matchInst = matchInst
        # 用户ID
        self.userId = userId
        # 用户昵称
        self.userName = None
        # 客户端clientId
        self.clientId = None
        # snsId
        self.snsId = None
        # 报名时间
        self.signinTime = signinTime
        # 用户积分
        self.score = None
        # 上次排名排名
        self.prevRank = None
        # 当前名次
        self.rank = None
        # 在桌子上的名次
        self.tableRank = 0
        # 在桌子上显示的排名
        self.tableDisplayRank = 0
        # 当前阶段
        self._stage = None
        # 用户状态
        self._state = MatchPlayer.STATE_SIGNIN
        # 桌子
        self._table = None
        # 座位
        self._seat = None
        # 支付的报名费
        self._paidFee = None
        # 当前阶段打了几副牌
        self._cardCount = 0
        # 最后一局的输赢
        self.isWin = False
        # 是否进入比赛界面
        self.isenter = False
        # 是否锁定
        self.locked = False
        # 正在退赛中
        self.signouting = False
        # 打赢的对手
        self.beatDownUserName = ''
        # 晋级时间
        self.riseTime = 0

    @property
    def match(self):
        return self._matchInst.match

    @property
    def matchInst(self):
        return self._matchInst

    @property
    def stage(self):
        return self._stage

    @property
    def state(self):
        return self._state

    @property
    def table(self):
        return self._table

    @property
    def seat(self):
        return self._seat

    @property
    def paidFee(self):
        return self._paidFee

    @property
    def cardCount(self):
        return self._cardCount


class MatchRankLine(object):
    def __init__(self):
        self._scores = []
        self._ranks = []

    def addInitChip(self, initChip):
        for i in xrange(len(self._scores)):
            self._scores[i] = self._scores[i] + initChip

    def calcRankRange(self, score):
        '''
        根据score计算名次范围，名次从1开始
        @param score: 积分
        @return: [start, end)
        '''

        index = sortedlist.upperBound(self._scores, score) - 1
        ret = None
        if index <= 0:
            index = 0
            ret = self._ranks[index], self._ranks[index] + 1
        else:
            ret = (self._ranks[index], self._ranks[index - 1])
        if ftlog.is_debug():
            ftlog.debug('MatchRankLine.calcRank score=', score,
                        'scores=', self._scores,
                        'ranks=', self._ranks,
                        'index=', index,
                        'ret=', ret)
        return ret

    def decodeFromDict(self, d):
        for line in d:
            if not isinstance(line, list) or len(line) != 2:
                raise TYBizConfException(line, 'MatchRankLine.line must be list (score, rank)')

            i = sortedlist.insert(self._scores, line[0])
            self._ranks.insert(i, line[1])
        if not self._scores:
            raise TYBizConfException('MatchRankLine must be not empty list')
        return self


class TipsConfig(object):
    def __init__(self):
        self.infos = None
        self.interval = None

    def decodeFromDict(self, conf):
        self.infos = conf.get('infos', [])
        if not isinstance(self.infos, list):
            raise TYBizConfException(conf, 'tips.infos must be list')
        for info in self.infos:
            if not isstring(info):
                raise TYBizConfException(conf, 'tips.infos.item must be string')
        self.interval = conf.get('interval', 5)
        if not isinstance(self.interval, int) or self.interval <= 0:
            raise TYBizConfException(conf, 'tips.interval must be int > 0')
        return self


# 比赛阶段配置
class MatchStageConf(object):
    def __init__(self, index):
        # 当前阶段序号
        self.index = index
        # 阶段名称
        self.name = None
        # 动画类型
        self.animationType = None
        # 当前阶段要打几副牌
        self.cardCount = None
        # 阶段总人数
        self.totalUserCount = None
        # 晋级人数
        self.riseUserCount = None
        # 初始分数，0就继承上一阶段的值
        self.scoreInit = None
        # 积分带入系数
        self.scoreIntoRate = None
        # 名次分数线
        self.rankLine = None

    def decodeFromDict(self, d):
        self.name = d.get('name', '')
        if not isstring(self.name):
            raise TYBizConfException(d, 'MatchStageConf.name must string')
        self.animationType = d.get('animationType', 0)
        if not isinstance(self.animationType, int):
            raise TYBizConfException(d, 'MatchStageConf.animationType must int')
        self.cardCount = d.get('cardCount')
        if not isinstance(self.cardCount, int) or self.cardCount <= 0:
            raise TYBizConfException(d, 'MatchStageConf.cardCount must be int > 0')
        self.totalUserCount = d.get('totalUserCount')
        if not isinstance(self.totalUserCount, int) or self.totalUserCount <= 0:
            raise TYBizConfException(d, 'MatchStageConf.totalUserCount must be int > 0')
        self.riseUserCount = d.get('riseUserCount')
        if not isinstance(self.riseUserCount, int) or self.riseUserCount <= 0:
            raise TYBizConfException(d, 'MatchStageConf.riseUserCount must be int > 0')
        self.scoreInit = d.get('scoreInit')
        if not isinstance(self.scoreInit, int) or self.scoreInit < 0:
            raise TYBizConfException(d, 'MatchStageConf.scoreInit must be int >= 0')
        self.scoreIntoRate = d.get('scoreIntoRate')
        if not isinstance(self.scoreInit, (int, float)) or self.scoreIntoRate <= 0 or self.scoreIntoRate > 1:
            raise TYBizConfException(d, 'MatchStageConf.scoreInit must in (0,1]')
        rankLine = d.get('rankLine')
        self.rankLine = MatchRankLine().decodeFromDict(rankLine)
        return self


# 比赛奖励
class MatchRankRewards(object):
    def __init__(self):
        self.conf = None
        self.startRank = None
        self.endRank = None
        self.rewards = None
        self.desc = None
        self.message = None
        self.todotask = None

    def decodeFromDict(self, d):
        self.conf = d
        ranking = d.get('ranking', {})
        self.startRank = ranking.get('start')
        if not isinstance(self.startRank, int) or self.startRank < -1:
            raise TYBizConfException(d, 'MatchRankRewards.ranking.start must be int >= -1')
        self.endRank = ranking.get('end')
        if not isinstance(self.endRank, int) or self.endRank < -1:
            raise TYBizConfException(d, 'MatchRankRewards.ranking.end must be int >= -1')
        if self.endRank != -1 and self.endRank < self.startRank:
            raise TYBizConfException(d, 'MatchRankRewards.ranking.end must >= ranking.start')
        rewards = d.get('rewards')
        if not isinstance(rewards, list):
            raise TYBizConfException(d, 'MatchRankRewards.rewards must be list')
        TYContentItem.decodeList(rewards)
        self.rewards = rewards
        self.desc = d.get('desc')
        self.message = d.get('message', '')
        self.todotask = d.get('todotask', None)
        return self


# 比赛报名费
class MatchFee(object):
    def __init__(self):
        self.assetKindId = None
        self.count = None
        self.params = None

    def getParam(self, paramName, defVal=None):
        return self.params.get(paramName, defVal)

    @property
    def failure(self):
        return self.getParam('failure', '')

    def decodeFromDict(self, d):
        self.assetKindId = d.get('itemId')
        if not isstring(self.assetKindId):
            raise TYBizConfException(d, 'MatchFee.itemId must be string')
        self.count = d.get('count')
        if not isinstance(self.count, int):
            raise TYBizConfException(d, 'MatchFee.count must be string')
        self.params = d.get('params', {})
        if not isinstance(self.params, dict):
            raise TYBizConfException(d, 'MatchFee.params must be dict')
        return self

    def toDict(self):
        return {'itemId': self.assetKindId, 'count': self.count}


# 比赛配置    
class MatchConf(object):
    def __init__(self):
        self.gameId = None
        self.roomId = None
        self.tableId = None
        self.seatId = None
        self.recordId = None
        self.matchId = None
        # 基数
        self.baseScore = None
        # 报名费
        self.fees = []
        # 阶段列表
        self.stages = []
        # 每桌坐的人数
        self.tableSeatCount = None
        # 桌子最大时间
        self.tableMaxTimes = None
        # 报名开始时间
        self.startTime = None
        # 比赛结束时间
        self.stopTime = None
        # 提前多长时间通知用户比赛结束
        self.prepareStopSeconds = 60
        # 报名相关配置
        # 最少报名人数
        self.minSigninCount = None
        # 最大报名人数
        self.maxSigninCount = None
        # 多少秒处理一次报名玩家
        self.processSigninIntervalSeconds = None
        # 每次处理多少个报名玩家
        self.processSigninCountPerTime = None

        # 多少秒处理一次牌局结束的玩家
        self.processWinloseIntervalSeconds = 1
        self.riseDelayTime = 1
        # 多少秒处理一次等待开桌的玩家
        self.processWaitIntervalSeconds = 1

        # 多少秒处理一次所有阶段的班车
        self.processStagesIntervalSeconds = 1

        # 最大参赛人数, 包括报名的和打牌的
        self.maxPlayerCount = None
        # 比赛奖励配置
        self.rankRewardsList = None
        # 
        self.tips = None

        # 还未开始报名时的提示
        self.tipsForNotSignin = None
        # 比赛即将停止的提示
        self.tipsForWillStopInfo = None

    def calcNextTime(self):
        '''
        @return: (startTime, endTime)
        '''
        nt = datetime.now()
        startDT = datetime.combine(nt.date(), self.startTime)
        stopDT = datetime.combine(nt.date(), self.stopTime)
        if startDT == stopDT:
            return startDT, stopDT
        if nt >= stopDT:
            td = timedelta(days=1)
            startDT += td
            stopDT += td
        return startDT, stopDT

    def decodeFromDict(self, d):
        self.matchId = d.get('matchId')
        if not isinstance(self.matchId, int):
            raise TYBizConfException(d, 'MatchConf.matchId must be int')

        self.recordId = d.get('recordId', self.matchId)
        if not isinstance(self.recordId, int):
            raise TYBizConfException(d, 'MatchConf.recordId must be int')

        self.baseScore = d.get('baseScore')
        if not isinstance(self.baseScore, int) or self.baseScore <= 0:
            raise TYBizConfException(d, 'MatchConf.baseScore must be int > 0')

        stages = d.get('stages')
        if not isinstance(stages, list) or not stages:
            raise TYBizConfException(d, 'MatchConf.stages must not emptylist')

        for i, stageConf in enumerate(stages):
            stage = MatchStageConf(i).decodeFromDict(stageConf)
            self.stages.append(stage)

        initChip = self.stages[0].scoreInit
        for stage in self.stages:
            initChip = int(initChip * stage.scoreIntoRate)
            stage.rankLine.addInitChip(initChip)

        self.tableSeatCount = d.get('tableSeatCount')
        if not isinstance(self.tableSeatCount, int) or self.tableSeatCount <= 0:
            raise TYBizConfException(d, 'MatchConf.tableSeatCount must be int > 0')

        self.tableMaxTimes = d.get('tableMaxTimes', 480)
        if not isinstance(self.tableMaxTimes, int) or self.tableMaxTimes <= 0:
            raise TYBizConfException(d, 'MatchConf.tableMaxTimes must be int > 0')

        self.prepareStopSeconds = d.get('prepareStopSeconds', 5 * 60)
        if not isinstance(self.prepareStopSeconds, int) or self.prepareStopSeconds <= 0:
            raise TYBizConfException(d, 'MatchConf.prepareStopSeconds must be int > 0')

        self.minSigninCount = d.get('minSigninCount')
        if not isinstance(self.minSigninCount, int) or self.minSigninCount < self.tableSeatCount:
            raise TYBizConfException(d, 'MatchConf.minSigninCount must be int > %s' % (self.tableSeatCount))

        self.maxSigninCount = d.get('maxSigninCount')
        if not isinstance(self.maxSigninCount, int) or self.maxSigninCount < self.minSigninCount:
            raise TYBizConfException(d, 'MatchConf.maxSigninCount must be int > %s' % (self.minSigninCount))

        self.maxPlayerCount = d.get('maxPlayerCount')
        if not isinstance(self.maxPlayerCount, int):
            raise TYBizConfException(d, 'MatchConf.maxPlayerCount must be int > 0')

        self.processSigninIntervalSeconds = d.get('processSigninIntervalSeconds')
        if not isinstance(self.processSigninIntervalSeconds, int) or self.processSigninIntervalSeconds <= 0:
            raise TYBizConfException(d, 'MatchConf.processSigninIntervalSeconds must be int > 0')

        self.processSigninCountPerTime = d.get('processSigninCountPerTime')
        if not isinstance(self.processSigninCountPerTime, int) or self.processSigninCountPerTime <= 0:
            raise TYBizConfException(d, 'MatchConf.processSigninCountPerTime must be int > 0')

        # 每次处理座位数的倍数
        self.processSigninCountPerTime = (
                                             self.processSigninCountPerTime + self.tableSeatCount - 1) * self.tableSeatCount / self.tableSeatCount

        rankRewards = d.get('rank.rewards', [])
        if not isinstance(rankRewards, list):
            raise TYBizConfException(d, 'MatchConf.rank.rewards must be list')
        self.rankRewardsList = []
        for rankRewardsConf in rankRewards:
            self.rankRewardsList.append(MatchRankRewards().decodeFromDict(rankRewardsConf))

        self.fees = []
        fees = d.get('fees', [])
        if not isinstance(fees, list):
            raise TYBizConfException(d, 'MatchConf.fees must be list')

        # 多种报名条件，当前的多种报名条件是都扣取的，是个报名费用集合而非多种报名条件
        # 是与的关系非或的关系
        for fee in fees:
            self.fees.append(MatchFee().decodeFromDict(fee))

        tips = d.get('tips', {})
        self.tips = TipsConfig().decodeFromDict(tips)

        startTime = stopTime = None
        try:
            startTime = d.get('startTime')
            startTime = datetime.strptime(startTime, '%H:%M').time()
        except:
            raise TYBizConfException(d, 'MatchConf.startTime must be time HH:MM %s' % (startTime))

        try:
            stopTime = d.get('stopTime')
            stopTime = datetime.strptime(stopTime, '%H:%M').time()
        except:
            raise TYBizConfException(d, 'MatchConf.stopTime must be time HH:MM %s' % (stopTime))

        if stopTime < startTime:
            raise TYBizConfException(d, 'MatchConf.stopTime must be >= startTime')
        self.startTime = startTime
        self.stopTime = stopTime

        self.tipsForNotSignin = d.get('tipsForNotSignin')
        if not isstring(self.tipsForNotSignin) or not self.tipsForNotSignin:
            raise TYBizConfException(d, 'MatchConf.tipsForNotSignin must not empty string')

        self.tipsForWillStopInfo = d.get('tipsForWillStopInfo')
        if not isstring(self.tipsForWillStopInfo) or not self.tipsForWillStopInfo:
            raise TYBizConfException(d, 'MatchConf.tipsForWillStopInfo must not empty string')

        return self


# 比赛阶段
class MatchStage(object):
    def __init__(self, matchInst, index, stageConf):
        self._matchInst = matchInst
        self._index = index
        # 当前阶段配置
        self._stageConf = stageConf
        # 晋级的玩家 list<MatchPlayer>
        self._rised = []
        # 本阶段等待班车, list<MatchPlayer>
        self._bus = []
        # 在本阶段的所有玩家, map<userId, MatchPlayer>
        self._playerMap = {}
        # 临时变量，在处理班车时候用
        self._sortedBus = None

    @property
    def match(self):
        return self._matchInst.match

    @property
    def matchId(self):
        return self.match.matchId

    @property
    def matchInst(self):
        return self._matchInst

    @property
    def index(self):
        return self._index

    @property
    def stageConf(self):
        return self._stageConf

    @property
    def prevStage(self):
        return self.matchInst.stages[self.index - 1] if self.index > 0 else None

    def calcRank(self, score):
        startRank, _endRank = self.stageConf.rankLine.calcRankRange(score)
        return startRank

    def canRise(self, rank):
        return rank <= self.stageConf.riseUserCount

    def calcScore(self, player):
        if self.stageConf.scoreInit > 0:
            return self.stageConf.scoreInit
        else:
            return int(player.score * self.stageConf.scoreIntoRate)

    def rise(self, player):
        assert (player.stage is None)
        ftlog.info('MatchStage.rise matchId=', self.matchId,
                   'instd=', self.matchInst.instId,
                   'stageIndex=', self.index,
                   'userId=', player.userId)
        player._state = MatchPlayer.STATE_RISE
        self._rised.append(player)
        self._playerMap[player.userId] = player
        player._stage = self
        player._cardCount = 0
        player.riseTime = time.time()

    def intoBus(self, player):
        assert (player.stage is None)
        ftlog.info('MatchStage.intoBus matchId=', self.matchId,
                   'instd=', self.matchInst.instId,
                   'stageIndex=', self.index,
                   'userId=', player.userId)
        player._state = MatchPlayer.STATE_WAIT
        self._bus.append(player)
        self._playerMap[player.userId] = player
        player._stage = self
        player._cardCount = 0

    def moveRiseIntoBus(self, timeLimit):
        while self._rised:
            player = self._rised[0]
            if player.riseTime <= timeLimit:
                player._state = MatchPlayer.STATE_WAIT
                self._bus.append(player)
                self._rised.pop(0)
            else:
                break

    def removePlayer(self, player):
        assert (player.stage == self)
        del self._playerMap[player.userId]
        player._stage = None
        ftlog.info('MatchStage.removePlayer matchId=', self.matchId,
                   'instd=', self.matchInst.instId,
                   'stageIndex=', self.index,
                   'userId=', player.userId)


# 比赛
class Match(object):
    def __init__(self, matchConf):
        self._matchConf = matchConf

        self.tableController = None
        self.tableManager = None
        self.playerNotifier = None
        self.matchRewardsSender = None
        self.userInfoLoader = None
        self.signinFee = None
        self.signinRecordDao = None

        self._started = False
        self._currentInstance = None
        self._heartbeatTimer = None

    @property
    def gameId(self):
        return self.matchConf.gameId

    @property
    def matchId(self):
        return self.matchConf.matchId

    @property
    def matchConf(self):
        return self._matchConf

    @property
    def roomId(self):
        return self.matchConf.roomId

    @property
    def tableId(self):
        return self.matchConf.tableId

    @property
    def seatId(self):
        return self.matchConf.seatId

    @property
    def currentInstance(self):
        return self._currentInstance

    def findPlayer(self, userId):
        if self._currentInstance:
            return self._currentInstance.findPlayer(userId)
        return None

    def findMatchingPlayer(self, userId):
        if self._currentInstance:
            return self._currentInstance.findMatchingPlayer(userId)
        return None

    def start(self):
        if self._started:
            return
        self._started = True
        ftlog.info('Match.start matchId=', self.matchId,
                   'startTime=')
        self.signinRecordDao.removeAll(self.matchId)
        self._heartbeatTimer = FTLoopTimer(5, -1, self._doHeartbeat)
        self._heartbeatTimer.start()
        roominfo.removeRoomInfo(self.gameId, self.roomId)
        self._currentInstance = self._createInstance()
        if self._currentInstance:
            self._currentInstance.start()

    def enter(self, userId):
        if not self._currentInstance:
            return False
        player = self.findMatchingPlayer(userId)
        if player:
            ftlog.warn('Match.enter matchId=', self.matchId,
                       'userId=', userId,
                       'err=', 'foundPlayer')
            return False
        return self._currentInstance.enter(userId)

    def leave(self, userId):
        if not self._currentInstance:
            return False
        return self._currentInstance.leave(userId)

    def signin(self, userId, signinParams, feeIndex=0):
        if self._currentInstance:
            return self._currentInstance.signin(userId, signinParams, feeIndex)
        return None

    def signout(self, userId):
        if self._currentInstance:
            return self._currentInstance.signout(userId)
        return None

    def giveup(self, userId):
        player = self.findMatchingPlayer(userId)
        if not player:
            ftlog.warn('Match.giveup matchId=', self.matchId,
                       'userId=', userId,
                       'err=', 'NotFoundPlayer')
            return False

        if ftlog.is_debug():
            ftlog.debug('Match.giveup matchId=', self.matchId,
                        'userId=', userId,
                        'player=', player)

        if not player.stage:
            ftlog.error('Match.giveup matchId=', self.matchId,
                        'userId=', userId,
                        'player=', player,
                        'err=', 'NotStage')
            return False

        player.matchInst.giveup(player)
        return True

    def winlose(self, tableId, ccrc, seatId, userId, deltaScore, isWin):
        player = self.findMatchingPlayer(userId)

        if ftlog.is_debug():
            ftlog.debug('Match.winlose matchId=', self.matchId,
                        'tableId=', tableId,
                        'ccrc=', ccrc,
                        'seatId=', seatId,
                        'userId=', userId,
                        'deltaScore=', deltaScore,
                        'isWin=', isWin)

        if not player:
            ftlog.debug('Match.winlose matchId=', self.matchId,
                        'tableId=', tableId,
                        'ccrc=', ccrc,
                        'seatId=', seatId,
                        'userId=', userId,
                        'deltaScore=', deltaScore,
                        'isWin=', isWin,
                        'err=', 'NotFoundPlayer')
            return None

        if player.state != MatchPlayer.STATE_PLAYING:
            ftlog.debug('Match.winlose matchId=', self.matchId,
                        'instId=', player.matchInst.instId,
                        'stageIndex=', player.stage.index,
                        'tableId=', tableId,
                        'ccrc=', ccrc,
                        'seatId=', seatId,
                        'userId=', player.userId,
                        'deltaScore=', deltaScore,
                        'isWin=', isWin,
                        'state=', player.state,
                        'expectState=', MatchPlayer.STATE_PLAYING,
                        'err=', 'BadState')
            return None

        if not player.seat:
            ftlog.debug('Match.winlose matchId=', self.matchId,
                        'instId=', player.matchInst.instId,
                        'stageIndex=', player.stage.index,
                        'tableId=', tableId,
                        'ccrc=', ccrc,
                        'seatId=', seatId,
                        'userId=', player.userId,
                        'deltaScore=', deltaScore,
                        'isWin=', isWin,
                        'err=', 'NotInSeat')
            return None

        if player.seat.table.tableId != tableId:
            ftlog.debug('Match.winlose matchId=', self.matchId,
                        'instId=', player.matchInst.instId,
                        'stageIndex=', player.stage.index,
                        'tableId=', tableId,
                        'ccrc=', ccrc,
                        'seatId=', seatId,
                        'userId=', player.userId,
                        'deltaScore=', deltaScore,
                        'isWin=', isWin,
                        'playerTableId=', player.seat.tableId,
                        'err=', 'DiffTable')
            return None

        if player.seat.seatId != seatId:
            ftlog.debug('Match.winlose matchId=', self.matchId,
                        'instId=', player.matchInst.instId,
                        'stageIndex=', player.stage.index,
                        'tableId=', tableId,
                        'ccrc=', ccrc,
                        'seatId=', seatId,
                        'userId=', player.userId,
                        'deltaScore=', deltaScore,
                        'isWin=', isWin,
                        'playerSeat=', player.seat.seatId,
                        'err=', 'DiffSeat')
            return None

        if player.seat.table.ccrc != ccrc:
            ftlog.debug('Match.winlose matchId=', self.matchId,
                        'instId=', player.matchInst.instId,
                        'stageIndex=', player.stage.index,
                        'tableId=', tableId,
                        'ccrc=', ccrc,
                        'seatId=', seatId,
                        'userId=', player.userId,
                        'deltaScore=', deltaScore,
                        'isWin=', isWin,
                        'tableCCRC=', player.table.ccrc,
                        'err=', 'diffCCRC')
            return None

        player.matchInst.winlose(player, deltaScore, isWin)
        return player

    def _createInstance(self):
        startDT, stopDT = self.matchConf.calcNextTime()
        instId = '%s.%s' % (self.matchId, startDT.strftime('%y%m%d%H%M'))
        ftlog.info('Match._createInstance matchId=', self.matchId,
                   'startTime=', startDT.strftime('%Y-%m-%d %H:%M:%S'),
                   'stopDT=', stopDT.strftime('%Y-%m-%d %H:%M:%S'),
                   'instId=', instId)
        return MatchInstance(self, instId, self.matchConf, startDT, stopDT)

    def _onInstanceFinal(self, inst):
        ftlog.info('Match._onInstanceFinal matchId=', self.matchId,
                   'instId=', inst.instId)
        self._currentInstance = self._createInstance()
        if self._currentInstance:
            self._currentInstance.start()
            roomInfo = self._currentInstance.buildRoomInfo()
            roominfo.saveRoomInfo(self.gameId, roomInfo)
        else:
            roominfo.removeRoomInfo(self.gameId, self.roomId)

    def _doHeartbeat(self):
        if self._currentInstance:
            roomInfo = self._currentInstance.buildRoomInfo()
            roominfo.saveRoomInfo(self.gameId, roomInfo)
            if ftlog.is_debug():
                ftlog.debug('Match._doHeartbeat matchId=', self.matchId,
                            'roomInfo=', roomInfo.__dict__)


# 比赛报名处理
class MatchSigninProcesser(object):
    def __init__(self, matchInst):
        self._timer = FTLoopTimer(matchInst.matchConf.processSigninIntervalSeconds, -1, matchInst._processSignin)

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.cancel()
        self._timer = None


# 比赛结算处理
class MatchWinloseProcesser(object):
    def __init__(self, matchInst):
        self._timer = FTLoopTimer(matchInst.matchConf.processWinloseIntervalSeconds, -1, matchInst._processWinlose)

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.cancel()
        self._timer = None


# 比赛阶段处理
class MatchStagesProcesser(object):
    def __init__(self, matchInst):
        self._timer = FTLoopTimer(matchInst.matchConf.processWaitIntervalSeconds, -1, matchInst._processStages)

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.cancel()
        self._timer = None


# 比赛等待处理
class MatchWaitProcesser(object):
    def __init__(self, matchInst):
        self._timer = FTLoopTimer(matchInst.matchConf.processWaitIntervalSeconds, -1, matchInst._processWait)

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.cancel()
        self._timer = None


# 比赛桌子超时处理
class MatchTableTimeoutProcesser(object):
    def __init__(self, matchInst):
        self._timer = FTLoopTimer(10, -1, matchInst._processTimeoutTables)

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.cancel()
        self._timer = None


# 比赛观察者
class MatchWatcher(object):
    def __init__(self, matchInst):
        self._matchInst = matchInst
        self._timer = None

    def start(self):
        delay = max(0, (self._matchInst._startDT - datetime.now()).total_seconds())
        self._timer = FTTimer(delay, self._doStart)

    def stop(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _doStart(self):
        self._timer.cancel()
        self._matchInst._doStart()
        if self._matchInst._stopDT != self._matchInst._startDT:
            delay = max(0, (self._matchInst._stopDT - datetime.now()).total_seconds()
                        - self._matchInst.matchConf.prepareStopSeconds)
            self._timer = FTTimer(delay, self._doPrepareStop)

    def _doPrepareStop(self):
        self._timer.cancel()
        self._matchInst._doPrepareStop()
        delay = max(0, (self._matchInst._stopDT - datetime.now()).total_seconds())
        self._timer = FTTimer(delay, self._doStop)

    def _doStop(self):
        self._timer.cancel()
        self._timer = None
        self._matchInst._doStop()
        FTTimer(0, self._matchInst._doFinal)


# 比赛实例
class MatchInstance(object):
    STATE_IDLE = 0
    STATE_STARTED = 1
    STATE_PREPARE_STOP = 2
    STATE_STOP = 3
    STATE_FINAL = 4

    def __init__(self, match, instId, matchConf, startDT, stopDT):
        self._match = match
        self._instId = instId
        self._matchConf = matchConf
        self._state = MatchInstance.STATE_IDLE
        # 开始时间
        self._startDT = startDT
        # 结束时间
        self._stopDT = stopDT
        # 当前报名的玩家, map<userId, MatchPlayer>
        self._signinMap = {}
        # 所有比赛中的玩家, map<userId, MatchPlayer>
        self._playerMap = {}
        # 刚打完牌的玩家列表
        self._winlosePlayerList = []
        # 所有等待需要开桌的, list< list<MatchPlayer> >
        self._waitPlayersList = []

        self._idleTableList = None
        self._allTableSet = None
        self._busyTableSet = None

        self._createStages()

        self._signinProcesser = MatchSigninProcesser(self)
        self._winloseProcesser = MatchWinloseProcesser(self)
        self._waitProcesser = MatchWaitProcesser(self)
        self._stagesProcesser = MatchStagesProcesser(self)
        self._tableTimeoutProcesser = MatchTableTimeoutProcesser(self)
        self._matchWatcher = MatchWatcher(self)

    @property
    def match(self):
        return self._match

    @property
    def matchId(self):
        return self.match.matchId

    @property
    def instId(self):
        return self._instId

    @property
    def matchConf(self):
        return self._matchConf

    @property
    def state(self):
        return self._state

    @property
    def stages(self):
        return self._stages

    def findPlayer(self, userId):
        return self.findSigninPlayer(userId) or self.findMatchingPlayer(userId)

    def findSigninPlayer(self, userId):
        return self._signinMap.get(userId)

    def findMatchingPlayer(self, userId):
        return self._playerMap.get(userId)

    def getSigninCount(self):
        return len(self._signinMap)

    def canSignin(self):
        return self._state >= MatchInstance.STATE_STARTED and self.state < MatchInstance.STATE_STOP

    def start(self):
        assert (self._state == MatchInstance.STATE_IDLE)
        ftlog.info('MatchInstance.start matchId=', self.matchId,
                   'instId=', self.instId)

        if not self._initTables():
            ftlog.error('MatchInstance.start matchId=', self.matchId,
                        'instId=', self.instId,
                        'err=', 'NotEnoughTables')
            return False
        self._matchWatcher.start()
        return True

    def enter(self, userId):
        player = self._signinMap.get(userId)
        if player and not player.isenter:
            player.isenter = True
            sessionClientId = self.match.userInfoLoader.getSessionClientId(userId)
            player.clientId = sessionClientId or ''
            ftlog.info('MatchInstance.enter matchId=', self.matchId,
                       'instId=', self.instId,
                       'userId=', userId,
                       'signinUserCount=', len(self._signinMap))
        return True

    def leave(self, userId):
        try:
            self.signout(userId)
            ftlog.info('MatchInstance.leave matchId=', self.matchId,
                       'instId=', self.instId,
                       'userId=', userId,
                       'signinUserCount=', len(self._signinMap))
            return True
        except:
            return False

    def signin(self, userId, signinParams, feeIndex):
        player = None
        try:
            if self.matchConf.fees and (feeIndex < 0 or feeIndex >= len(self.matchConf.fees)):
                raise MatchSigninException('请选择报名费')

            # 确认可以报名
            self._ensureCanSignin(userId)

            # 生成玩家对象
            player = MatchPlayer(self, userId, pktimestamp.getCurrentTimestamp())
            player.isenter = True
            # 收取报名费
            self._collectFee(player, feeIndex)
            if not self._lockPlayer(player):
                raise EnterMatchLocationException(self.matchId)

            # 此处需要再次确认可以报名，因为collectFees可能是异步的
            self._ensureCanSignin(userId)

            # 加入报名队列
            self._signinMap[userId] = player

            self._match.signinRecordDao.recordSignin(self.matchId, self.instId, userId,
                                                     pktimestamp.getCurrentTimestamp(), signinParams)
            # TODO publish event
            ftlog.info('MatchInstance.signin ok matchId=', self.matchId,
                       'instId=', self.instId,
                       'userId=', userId,
                       'fee=', player.paidFee.toDict() if player.paidFee else None,
                       'signinCount=', len(self._signinMap))

            # 填充用户信息
            self._fillPlayer(player)
            return player
        except MatchException:
            if player:
                self._returnFee(player)
                self._unlockPlayer(player)
            raise

    def signout(self, userId):
        player = self.findSigninPlayer(userId)
        if not player:
            raise NotSigninException(self.match.matchId)

        del self._signinMap[userId]
        # 返还报名费
        self._returnFee(player)
        if userId not in self._signinMap:
            self._unlockPlayer(player)
        self._match.signinRecordDao.removeSignin(self.matchId, self.instId, userId)
        ftlog.info('MatchInstance.signout ok matchId=', self.matchId,
                   'instId=', self.instId,
                   'userId=', userId,
                   'fee=', (player.paidFee.assetKindId, player.paidFee.count) if player.paidFee else None)
        return player

    def giveup(self, player):
        if player.state == MatchPlayer.STATE_WINLOSE:
            try:
                if player in self._winlosePlayerList:
                    self._winlosePlayerList.remove(player)
                    player.rank = player.stage.stageConf.totalUserCount
                    self._playerOverMatch(player, 1)
                    return True
            except:
                ftlog.error('MatchInstance.giveup matchId=', self.matchId,
                            'instId=', player.matchInst.instId,
                            'stageIndex=', player.stage.index,
                            'userId=', player.userId,
                            'err=', 'NotInWinloseList')
        elif player.state == MatchPlayer.STATE_WAIT:
            try:
                if player in player.stage._bus:
                    player.stage._bus.remove(player)
                    player.rank = player.stage.stageConf.totalUserCount
                    self._playerOverMatch(player, 1)
                    return True
            except:
                ftlog.error('MatchInstance.giveup matchId=', self.matchId,
                            'instId=', player.matchInst.instId,
                            'stageIndex=', player.stage.index,
                            'userId=', player.userId,
                            'err=', 'NotInBus')
        elif player.state == MatchPlayer.STATE_RISE:
            try:
                if player in player.stage._rised:
                    player.stage._rised.remove(player)
                    player.rank = player.stage.stageConf.totalUserCount
                    self._playerOverMatch(player, 1)
                    return True
            except:
                ftlog.error('MatchInstance.giveup matchId=', self.matchId,
                            'instId=', player.matchInst.instId,
                            'stageIndex=', player.stage.index,
                            'userId=', player.userId,
                            'err=', 'NotInBus')

        if ftlog.is_debug():
            ftlog.debug('MatchInstance.giveup Fail matchId=', self.matchId,
                        'instId=', player.matchInst.instId,
                        'stageIndex=', player.stage.index,
                        'userId=', player.userId,
                        'playerState=', player.state)
        self.match.playerNotifier.notifyMatchGiveupFailed(player, '您的当前阶段不能退出比赛，请稍候')
        return False

    def winlose(self, player, deltaScore, isWin, isKill=False):
        # 处理分数和状态，加入到winlose列表
        ftlog.hinfo('MatchInstance.winlose matchId=', self.matchId,
                    'instId=', self.instId,
                    'stageIndex=', player.stage.index,
                    'state=', self.state,
                    'userId=', player.userId,
                    'tableId=', player.table.tableId if player.table else None,
                    'curScore=', player.score,
                    'deltaScore=', deltaScore,
                    'isWin=', isWin,
                    'isKill=', isKill)
        assert (player.state == MatchPlayer.STATE_PLAYING)
        # 比赛即将结束，此时不处理输赢事件了
        if self.state >= MatchInstance.STATE_STOP:
            return
        player.score += deltaScore
        player._state = MatchPlayer.STATE_WINLOSE
        player.isWin = isWin
        table = player.table

        if not table:
            playerList = [player]
            player.tableRank = 3
            if self._isLastStage(player.stage):
                # 最后一个阶段按照桌子分数排名
                player.rank = player.tableRank
            else:
                # 其它阶段按照分数线排名
                player.rank = player.stage.calcRank(player.score)
            self._addToWinloseList(playerList)
        elif self._isAllPlayerWinlose(table):
            playerList = table.getPlayerList()
            self._sortTableRank(playerList)

            for player in playerList:
                # 记录上次排名
                player.prevRank = player.rank
                if self._isLastStage(player.stage):
                    # 最后一个阶段按照桌子分数排名
                    player.rank = player.tableRank
                else:
                    # 其它阶段按照分数线排名
                    player.rank = player.stage.calcRank(player.score)

            # 让该桌子上的用户站起
            self._clearTable(table)

            # 释放桌子
            self._returnTable(table)

            # 添加到一局完成列表
            self._addToWinloseList(playerList)

    def buildRoomInfo(self):
        roomInfo = MatchRoomInfo()
        roomInfo.roomId = self.match.roomId
        roomInfo.playerCount = len(self._playerMap)
        roomInfo.signinCount = len(self._signinMap)
        roomInfo.startType = 1
        roomInfo.instId = self.instId
        roomInfo.fees = []
        if self.matchConf.fees:
            for fee in self.matchConf.fees:
                roomInfo.fees.append(TYContentItem(fee.assetKindId, fee.count))
        return roomInfo

    def _doStart(self):
        assert (self._state == MatchInstance.STATE_IDLE)
        ftlog.info('MatchInstance._startSignin matchId=', self.matchId,
                   'instId=', self.instId)
        self._state = MatchInstance.STATE_STARTED
        self._signinProcesser.start()
        self._winloseProcesser.start()
        self._waitProcesser.start()
        self._stagesProcesser.start()
        self._tableTimeoutProcesser.start()

    def _doPrepareStop(self):
        ftlog.info('MatchInstance._doPrepareStop matchId=', self.matchId,
                   'instId=', self.instId,
                   'state=', self._state)
        if self._state == MatchInstance.STATE_STARTED:
            self._state = MatchInstance.STATE_PREPARE_STOP
            # 通知所有用户，比赛即将结束，并且此时该比赛停止报名
            stopTimeStr = self._stopDT.strftime('%H:%M分')
            info = strutil.replaceParams(self.matchConf.tipsForWillStopInfo, {'stopTime': stopTimeStr})
            for player in list(self._signinMap.values()):
                self.match.playerNotifier.notifyMatchWillCancelled(player, info)
            for player in list(self._playerMap.values()):
                self.match.playerNotifier.notifyMatchWillCancelled(player, info)

    def _doStop(self):
        ftlog.info('MatchInstance._doStop matchId=', self.matchId,
                   'instId=', self.instId,
                   'state=', self._state)
        if (self._state == MatchInstance.STATE_STARTED
            or self._state == MatchInstance.STATE_PREPARE_STOP):
            self._state = MatchInstance.STATE_STOP
            self._matchWatcher.stop()
            self._signinProcesser.stop()
            self._winloseProcesser.stop()
            self._waitProcesser.stop()
            self._stagesProcesser.stop()
            self._tableTimeoutProcesser.stop()

            # 通知所有用户比赛要结束了
            players = self._signinMap.values()
            for player in players:
                ftlog.info('MatchInstance._doStop cancelSignin matchId=', self.matchId,
                           'instId=', self.instId,
                           'userId=', player.userId)
                del self._signinMap[player.userId]
                self.match.playerNotifier.notifyMatchCancelled(player, 1, '服务器维护')

            busyTableSet = list(self._busyTableSet)
            # 清理所有正在比赛的桌子
            for table in busyTableSet:
                # 让该桌子上的用户站起
                self._clearTable(table)
                # 释放桌子
                self._returnTable(table)

            self._releaseTables()

            players = self._playerMap.values()
            for player in players:
                ftlog.info('MatchInstance._doStop cancelMatching matchId=', self.matchId,
                           'instId=', self.instId,
                           'userId=', player.userId)
                player.rank = player.stage.stageConf.totalUserCount
                self._playerOverMatch(player)

            self._idleTableList = None
            self._allTableSet = None
            self._busyTableSet = None

            self._signinMap = None
            self._playerMap = None
            self._waitPlayersList = None
            self._winlosePlayerList = None

    def _doFinal(self):
        if self._state == MatchInstance.STATE_STOP:
            self._state = MatchInstance.STATE_FINAL
            # 通知比赛，该比赛实例停止了
            self.match._onInstanceFinal(self)

    def _ensureCanSignin(self, userId):
        if self._state < MatchInstance.STATE_STARTED:
            info = strutil.replaceParams(self.matchConf.tipsForNotSignin,
                                         {'startDateTime': self._startDT.strftime('%Y-%m-%d %H:%M')})
            raise SigninNotStartException(self.matchId, info)

        if self._state >= MatchInstance.STATE_PREPARE_STOP:
            raise MatchExpiredException(self.matchId)

        player = self.findPlayer(userId)
        if player:
            if ftlog.is_debug():
                ftlog.debug('MatchInstance._ensureCanSignin matchId=', self.matchId,
                            'instd=', self.instId,
                            'userId=', userId,
                            'state=', player.state,
                            'stageIndex=', player.stage.index if player.stage else -1)
            if player.state == MatchPlayer.STATE_SIGNIN:
                raise AlreadySigninException(self.matchId)
            raise AlreadyInMatchException(self.matchId)

        # 检查报名人数
        if len(self._signinMap) + 1 > self.matchConf.maxSigninCount:
            raise SigninFullException(self.matchId)

        # 检查总人数
        if len(self._signinMap) + len(self._playerMap) + 1 > self.matchConf.maxPlayerCount:
            raise SigninFullException(self.matchId)

    def _collectFee(self, player, feeIndex):
        if self.matchConf.fees:
            # 收取报名费用
            paidFee = self._match.signinFee.collectFee(self, player.userId, self.matchConf.fees[feeIndex])
            # 记录当前玩家的报名费用
            player._paidFee = paidFee

    def _returnFee(self, player):
        if player.paidFee:
            self._match.signinFee.returnFee(self, player.userId, player.paidFee)
            player._paidFee = None

    def _fillPlayer(self, player):
        userName, sessionClientId, snsId = self.match.userInfoLoader.loadUserAttrs(player.userId,
                                                                                   ['name', 'sessionClientId', 'snsId'])

        snsId = strutil.ensureString(snsId)
        player.userName = strutil.ensureString(userName)
        player.clientId = strutil.ensureString(sessionClientId)
        player.snsId = snsId
        return player

    def _processSignin(self):
        '''
        处理报名的玩家
        '''
        if ftlog.is_debug():
            ftlog.debug('MatchInstance._processSignin matchId=', self.matchId,
                        'instd=', self.instId,
                        'minSigninCount=', self.matchConf.minSigninCount,
                        'currentSigninCount=', len(self._signinMap))

        if len(self._signinMap) < self.matchConf.minSigninCount:
            if ftlog.is_debug():
                ftlog.debug('MatchInstance._processSignin PlayerNotEnough matchId=', self.matchId,
                            'instd=', self.instId,
                            'signinCount=', len(self._signinMap),
                            'minSigninCount=', self.matchConf.minSigninCount)
            return

        players = sorted(self._signinMap.values(), key=lambda p: p.signinTime)
        count = min(len(players), self.matchConf.processSigninCountPerTime)
        count -= count % self.matchConf.tableSeatCount
        firstStage = self._stages[0]

        ftlog.info('MatchInstance._processSignin matchId=', self.matchId,
                   'instd=', self.instId,
                   'minSigninCount=', self.matchConf.minSigninCount,
                   'currentSigninCount=', len(self._signinMap),
                   'processCount=', count)

        for i in xrange(count):
            player = players[i]
            del self._signinMap[player.userId]
            player.rank = player.prevRank = i + 1
            self._playerMap[player.userId] = player
            player.score = firstStage.calcScore(player)
            firstStage.intoBus(player)

        # 防止notifyMatchStart有异步操作
        for player in players:
            self.match.playerNotifier.notifyMatchStart(player)

        for player in players:
            self._match.signinRecordDao.removeSignin(self.matchId, self.instId, player.userId)

    def _processWinlose(self):
        '''
        处理刚玩完一局的玩家
        '''
        if ftlog.is_debug():
            ftlog.debug('MatchInstance._processWinlose matchId=', self.matchId,
                        'instd=', self.instId,
                        'winlosePlayerLen=', len(self._winlosePlayerList))

        winlosePlayerList = self._winlosePlayerList
        self._winlosePlayerList = []
        for player in winlosePlayerList:
            if player.cardCount < player.stage.stageConf.cardCount:
                player._state = MatchPlayer.STATE_WAIT
                player.stage._bus.append(player)
            else:
                if self._canRise(player):
                    if not self._isLastStage(player.stage):
                        # 根据系数调整名次
                        player.rank = player.rank + round(player.rank * random.uniform(-0.1, 0.1))
                        player.rank = min(player.stage.stageConf.riseUserCount, player.rank)
                        player.rank = int(max(1, player.rank))
                    self._risePlayer(player)
                else:
                    if not self._isLastStage(player.stage):
                        # 根据系数调整名次
                        player.rank = player.rank + round(player.rank * random.uniform(-0.1, 0.1))
                        player.rank = min(player.stage.stageConf.totalUserCount, player.rank)
                        player.rank = int(max(player.stage.stageConf.riseUserCount + 1, player.rank))
                    self._outPlayer(player)

    def _processWait(self):
        if ftlog.is_debug():
            ftlog.info('MatchInstance._processWaitList matchId=', self.matchId,
                       'instd=', self.instId)

        # TODO 平滑处理
        playersList = self._waitPlayersList[:]
        self._waitPlayersList = self._waitPlayersList[len(playersList):]
        for players in playersList:
            self._startTable(players)

    def _processTimeoutTables(self):
        if ftlog.is_debug():
            ftlog.debug('MatchInstance._processTimeoutTables matchId=', self.matchId,
                        'instd=', self.instId)

        overtimeTables = []
        curTime = pktimestamp.getCurrentTimestamp()
        for table in self._busyTableSet:
            if (curTime - table.startTime) >= self.matchConf.tableMaxTimes:
                overtimeTables.append(table)

        for table in overtimeTables:
            ftlog.info('MatchInstance._processTimeoutTables matchId=', self.matchId,
                       'instId=', self.instId,
                       'tableId=', table.tableId,
                       'playTimes=', (curTime - table.startTime))
            playerList = table.getPlayerList()
            for player in playerList:
                if player.state == MatchPlayer.STATE_PLAYING:
                    self.winlose(player, 0, False, True)

    def _processStages(self):
        '''
        处理所有阶段
        '''
        # 先处理第一阶段的班车，第一阶段班车的用户不能和其它阶段的混玩
        if ftlog.is_debug():
            ftlog.debug('MatchInstance._processStages matchId=', self.matchId,
                        'instd=', self.instId)

        timeLimit = time.time() - self.matchConf.riseDelayTime
        for stage in self._stages:
            stage.moveRiseIntoBus(timeLimit)

        # 排序除首末班车的所有阶段班车，用于下一阶段人数不足时补充人数时用
        for i in range(1, len(self._stages) - 2):
            stage = self._stages[i]
            # stage._sortedBus = sorted(stage._bus, key=lambda p:p.score)
            stage._sortedBus = list(stage._bus)

        # 处理首阶段班车
        # 首班车排名
        for rank, player in enumerate(self._stages[0]._bus):
            player.rank = min(rank + 1, self._stages[0].stageConf.totalUserCount)
        self._processStage(self._stages[0])

        curIndex = len(self._stages) - 1
        while (curIndex > 0):
            stage = self._stages[curIndex]
            # 清除该阶段排序的班车
            stage._sortedBus = None
            # 处理该阶段班车
            self._processStage(stage)
            curIndex -= 1

    def _processStage(self, stage):
        '''
        处理阶段班车
        '''
        if ftlog.is_debug():
            ftlog.debug('MatchInstance._processStage matchId=', self.matchId,
                        'instd=', self.instId,
                        'stageIndex=', stage.index,
                        'inBusLen=', len(stage._bus),
                        'totalLen=', len(self._playerMap))

        stage._bus = self._sortPlayerSnake(stage._bus)
        while len(stage._bus) >= self.matchConf.tableSeatCount:
            players = stage._bus[0:self.matchConf.tableSeatCount]
            stage._bus = stage._bus[self.matchConf.tableSeatCount:]
            self._waitPlayersList.append(players)
            ftlog.info('MatchInstance._processStage matchId=', self.matchId,
                       'instd=', self.instId,
                       'stageIndex=', stage.index,
                       'players=', [(p.userId, p.stage.index, p.score, p.cardCount) for p in players])

        # 首班车玩家不能和其它玩家混玩
        if not stage._bus or stage.index < 2:
            return

        # 还需要多少用户才能凑足一桌
        needCount = self.matchConf.tableSeatCount - len(stage._bus)
        players = self._getPlayersFromPrevStages(stage, needCount)
        if players:
            players.extend(stage._bus)
            stage._bus = []
            self._waitPlayersList.append(players)
            ftlog.info('MatchInstance._processStage matchId=', self.matchId,
                       'instd=', self.instId,
                       'stageIndex=', stage.index,
                       'players=', [(p.userId, p.stage.index, p.score, p.cardCount) for p in players])

    def _canRise(self, player):
        return player.stage.canRise(player.rank)

    def _outPlayer(self, player):
        ftlog.info('MatchInstance._outPlayer matchId=', self.matchId,
                   'instd=', self.instId,
                   'stageIndex=', player.stage.index,
                   'userId=', player.userId,
                   'score=', player.score,
                   'rank=', player.rank,
                   'riseCount=', player.stage.stageConf.riseUserCount)
        if player.rank < player.stage.stageConf.riseUserCount:
            ftlog.warn('MatchInstance._outPlayer matchId=', self.matchId,
                       'instd=', self.instId,
                       'stageIndex=', player.stage.index,
                       'userId=', player.userId,
                       'score=', player.score,
                       'rank=', player.rank,
                       'riseCount=', player.stage.stageConf.riseUserCount,
                       'err=', 'BadRank')
            player.rank = player.stage.stageConf.riseUserCount
        self._playerOverMatch(player)

    def _risePlayer(self, player):
        ftlog.info('MatchInstance._risePlayer matchId=', self.matchId,
                   'instd=', self.instId,
                   'stageIndex=', player.stage.index,
                   'userId=', player.userId,
                   'score=', player.score,
                   'rank=', player.rank,
                   'riseCount=', player.stage.stageConf.riseUserCount)
        nextStage = self._nextStage(player.stage)
        if not nextStage:
            self._playerOverMatch(player)
        else:
            player.stage.removePlayer(player)
            nextStage.rise(player)
            self.match.playerNotifier.notifyMatchRank(player)
            self.match.playerNotifier.notifyMatchWait(player)

    def _playerOverMatch(self, player, reason=0):
        player._state = MatchPlayer.STATE_OVER
        rankRewards = self._findRankRewards(player.rank)
        ftlog.hinfo('MatchInstance._playerOverMatch matchId=', self.matchId,
                    'instd=', self.instId,
                    'stageIndex=', player.stage.index,
                    'userId=', player.userId,
                    'score=', player.score,
                    'rank=', player.rank,
                    'reason=', reason,
                    'whenOut=', 0,
                    'riseCount=', player.stage.stageConf.riseUserCount,
                    'rankRewards=', rankRewards.desc if rankRewards else None)
        overReason = MatchFinishReason.USER_LOSER
        if rankRewards:
            self.match.matchRewardsSender.sendRankRewards(player, rankRewards)
            overReason = MatchFinishReason.USER_WIN
        self.match.playerNotifier.notifyMatchOver(player, overReason, rankRewards)
        self._unlockPlayer(player)
        # 从stage和matchInstance中删除
        player.stage.removePlayer(player)
        del self._playerMap[player.userId]

        # TODO 发送事件

    def _findRankRewards(self, rank):
        for rankRewards in self._matchConf.rankRewardsList:
            if ((rankRewards.startRank < 0 or rank >= rankRewards.startRank)
                and (rankRewards.endRank < 0 or rank <= rankRewards.endRank)):
                return rankRewards
        return None

    def _initTables(self):
        needCount = (self.matchConf.maxPlayerCount + self.matchConf.tableSeatCount - 1) / self.matchConf.tableSeatCount
        if self.match.tableManager.idleTableCount < needCount:
            return False
        tables = self.match.tableManager.borrowTables(needCount)
        self._idleTableList = tables
        self._allTableSet = set(tables)
        self._busyTableSet = set()
        return True

    def _borrowTable(self):
        assert (len(self._idleTableList) > 0)
        table = self._idleTableList.pop()
        self._busyTableSet.add(table)
        if ftlog.is_debug():
            ftlog.debug('MatchInstance._borrowTable matchId=', self.matchId,
                        'instId=', self.instId,
                        'tableId=', table.tableId)
        return table

    def _returnTable(self, table):
        assert (table.idleSeatCount == table.seatCount)
        assert (table in self._allTableSet)
        self._busyTableSet.remove(table)
        self._idleTableList.append(table)
        if ftlog.is_debug():
            ftlog.debug('MatchInstance._returnTable matchId=', self.matchId,
                        'instId=', self.instId,
                        'tableId=', table.tableId)

    @classmethod
    def calcRankInPlayers(cls, player, players):
        rank = 1
        for p in players:
            if p != player and p.score >= player.score:
                rank += 1
        return rank

    def _calcTableDisplayRank(self, i, players):
        selfPlayer = players[i]
        rankInPlayer = self.calcRankInPlayers(selfPlayer, players)
        maxRank = selfPlayer.stage.stageConf.totalUserCount - 3 + rankInPlayer
        rank = max(rankInPlayer, selfPlayer.rank)
        return min(maxRank, rank)

    def _startTable(self, players):
        table = self._borrowTable()
        table._ccrc += 1
        table._startTime = pktimestamp.getCurrentTimestamp()
        table._matchInst = self

        # 计算下一阶段分数
        for player in players:
            if player.cardCount < 1 and player.stage.index != 0:
                player.score = player.stage.calcScore(player)

        for i, player in enumerate(players):
            player._state = MatchPlayer.STATE_PLAYING
            player._cardCount += 1
            player.tableDisplayRank = self._calcTableDisplayRank(i, players)
            table.sitdown(player)

        ftlog.info('MatchInstance._startTable matchId=', self.matchId,
                   'instd=', self.instId,
                   'tableId=', table.tableId,
                   'players=',
                   [(p.userId, p.stage.index, p.score, p.cardCount, p.seat.seatId, p.tableDisplayRank, p.rank) for p in
                    players])

        self.match.tableController.startTable(table)

    def _clearTable(self, table):
        ftlog.info('MatchInstance._clearTable matchId=', self.matchId,
                   'instd=', self.instId,
                   'tableId=', table.tableId,
                   'players=',
                   [(p.userId, p.stage.index, p.score, p.cardCount, p.seat.seatId, p.tableDisplayRank) for p in
                    table.getPlayerList()])

        for seat in table.seats:
            if seat.player:
                try:
                    self.match.userLocker.lockUser(seat.player.userId, self.match.roomId, self.match.tableId,
                                                   self.match.seatId, seat.player.clientId)
                    # onlinedata.addOnlineLoc(seat.player.userId, self.match.roomId, self.match.tableId, self.match.seatId)
                    # if ftlog.is_debug() :
                    #    ftlog.debug("|userId, locList:", seat.player.userId, onlinedata.getOnlineLocList(seat.player.userId), caller=self)
                except:
                    ftlog.error()
        self.match.tableController.clearTable(table)
        for seat in table.seats:
            if seat.player:
                table.standup(seat.player)

    def _releaseTables(self):
        # 释放桌子
        ftlog.info('MatchInstance._releaseTables matchId=', self.matchId,
                   'instd=', self.instId)
        self.match.tableManager.returnTables(self._allTableSet)

    def _createStages(self):
        self._stages = []
        for index, stageConf in enumerate(self.matchConf.stages):
            stage = MatchStage(self, index, stageConf)
            self._stages.append(stage)

    def _nextStage(self, stage):
        nextIndex = stage.index + 1
        return self._stages[nextIndex] if nextIndex < len(self._stages) else None

    def _isLastStage(self, stage):
        return stage.index + 1 >= len(self._stages)

    def _getPlayersFromPrevStages(self, stage, count):
        # 从前面阶段的班车里补足玩家
        prevIndex = stage.index - 1
        totalCount = 0
        # list<(stage, count)
        stageCountList = []
        while (totalCount < count and prevIndex > 0):
            prevStage = self._stages[prevIndex]
            if prevStage._sortedBus:
                stageCount = min(count - totalCount, len(prevStage._sortedBus))
                totalCount += stageCount
                stageCountList.append((prevStage, stageCount))
            prevIndex -= 1

        players = []
        if totalCount >= count:
            for stageCount in stageCountList:
                for _ in xrange(stageCount[1]):
                    player = stageCount[0]._sortedBus[-1]
                    players.append(player)
                    del stageCount[0]._sortedBus[-1]
                    stageCount[0]._bus.remove(player)
        return players

    def _addToWinloseList(self, playerList):
        for player in playerList:
            if ftlog.is_debug():
                ftlog.debug('MatchInstance._addToWinloseList matchId=', self.matchId,
                            'instd=', self.instId,
                            'userId=', player.userId,
                            'stageIndex=', player.stage.index)
            self._winlosePlayerList.append(player)

    def _sortTableRank(self, playerList):
        playerList.sort(key=lambda p: p.score, reverse=True)
        for i, p in enumerate(playerList):
            p.tableRank = i + 1

    def _sortPlayerSnake(self, players):
        buckets = [[] for _ in xrange(self.matchConf.tableSeatCount)]
        for i in xrange(len(players)):
            mod = i % self.matchConf.tableSeatCount
            buckets[mod].append(players[i])
        ret = []
        for subPlayers in buckets:
            ret.extend(subPlayers)
        return ret

    def _isAllPlayerWinlose(self, table):
        for seat in table.seats:
            if seat.player and seat.player.state != MatchPlayer.STATE_WINLOSE:
                return False
        return True

    def _lockPlayer(self, player):
        try:
            if not player.isenter:
                ftlog.warn('MatchInstance._lockPlayer failed matchId=', self.matchId,
                           'instId=', self.instId,
                           'userId=', player.userId,
                           'err=', 'NotEnter')
                return False

            if player.locked:
                ftlog.info('MatchInstance._lockPlayer locked matchId=', self.matchId,
                           'instId=', self.instId,
                           'userId=', player.userId)
                return True

            if not self.match.userLocker.lockUser(player.userId, self.match.roomId, self.match.tableId,
                                                  self.match.seatId, player.clientId):
                ftlog.info('MatchInstance._lockPlayer failed matchId=', self.matchId,
                           'instId=', self.instId,
                           'userId=', player.userId,
                           'err=', 'NotLock')
                return False
            # if onlinedata.getOnlineLocSeatId(player.userId, self.match.roomId, self.match.tableId) == self.match.seatId :
            #                 player.locked = True
            #                 ftlog.info('MatchInstance._lockPlayer successed matchId=', self.matchId,
            #                            'instId=', self.instId,
            #                            'userId=', player.userId,
            #                            'loc=', '%s.%s.%s.%s' % (self.match.gameId, self.match.roomId, self.match.tableId, self.match.seatId))
            #                 if ftlog.is_debug() :
            #                     ftlog.debug("|userId, locList:", player.userId, onlinedata.getOnlineLocList(player.userId), caller=self)
            #                 return True
            #
            #             onlinedata.addOnlineLoc(player.userId, self.match.roomId, self.match.tableId, self.match.seatId)
            player.locked = True
            if ftlog.is_debug():
                ftlog.debug('MatchInstance._lockPlayer successed matchId=', self.matchId,
                            'instId=', self.instId,
                            'userId=', player.userId,
                            'loc=', '%s.%s.%s.%s' % (
                                self.match.gameId, self.match.roomId, self.match.tableId, self.match.seatId))
            # if ftlog.is_debug() :
            #    ftlog.debug("|userId, locList:", player.userId, onlinedata.getOnlineLocList(player.userId), caller=self)
            return True
        except:
            ftlog.error()
            return False

    def _unlockPlayer(self, player):
        try:
            if player.locked:
                player.locked = False
                self.match.userLocker.unlockUser(player.userId, self.match.roomId, self.match.tableId, player.clientId)
                # onlinedata.removeOnlineLoc(player.userId, self.match.roomId, self.match.tableId)
                if ftlog.is_debug():
                    ftlog.debug('MatchInstance._unlockPlayer successed matchId=', self.matchId,
                                'instId=', self.instId,
                                'userId=', player.userId,
                                'loc=', '%s.0.0.0' % (self.match.gameId))
                    # if ftlog.is_debug() :
                    #    ftlog.debug("|userId, locList:", player.userId, onlinedata.getOnlineLocList(player.userId), caller=self)
        except:
            ftlog.error('MatchInstance._unlockPlayer exception matchId=', self.matchId,
                        'instId=', self.instId,
                        'userId=', player.userId)
