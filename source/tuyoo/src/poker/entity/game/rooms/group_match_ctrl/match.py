# -*- coding:utf-8 -*-
'''
Created on 2016年1月25日

@author: zhaojiangang
'''
import time

from datetime import datetime

import poker.util.timestamp as pktimestamp
from freetime.core.lock import locked
from poker.entity.biz import bireport
from poker.entity.biz.content import TYContentItem
from poker.entity.configure import gdata
from poker.entity.game.game import TYGame
from poker.entity.game.rooms import roominfo
from poker.entity.game.rooms.group_match_ctrl.const import FeesType, \
    MatchFinishReason, StageType, WaitReason, GroupingType
from poker.entity.game.rooms.group_match_ctrl.events import \
    MatchStartSigninEvent, MatchingStageStartEvent, MatchingStartEvent, \
    MatchingFinishEvent, MatchingStageFinishEvent, MatchCancelEvent
from poker.entity.game.rooms.group_match_ctrl.exceptions import \
    BadStateException, SigninStoppedException, SigninNotStartException, \
    AlreadySigninException, SigninFullException, MatchStoppedException, \
    AlreadyInMatchException, SigninException
from poker.entity.game.rooms.group_match_ctrl.interface import MatchStatus
from poker.entity.game.rooms.group_match_ctrl.models import Signer, Player, \
    Riser
from poker.entity.game.rooms.group_match_ctrl.utils import Lockable, Logger, \
    HeartbeatAble, PlayerScoreCalc, PlayerQueuing, PlayerSort, PlayerGrouping, \
    GroupNameGenerator
from poker.entity.game.rooms.roominfo import MatchRoomInfo
from poker.util import strutil


class MatchInst(Lockable):
    '''
    比赛实例，用于接受报名，退赛，运行在赛区中
    '''
    ST_IDLE = 0
    ST_LOAD = 1
    ST_SIGNIN = 2
    ST_PREPARE = 3
    ST_STARTING = 4
    ST_START = 5
    ST_FINAL = 6

    def __init__(self, area, instId, startTime, needLoad):
        # 赛区
        self.area = area
        # 实例ID
        self.instId = instId
        # 开赛时间
        self.startTime = startTime
        self.signinTimeStr = ''
        self.startTimeStr = ''
        if self.startTime:
            self.signinTimeStr = self.matchConf.start.buildSigninTimeStr()
            self.startTimeStr = datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M')
        # 报名记录
        self._signerMap = {}
        # 是否需要加载报名记录
        self._needLoad = needLoad
        # 状态
        self._state = MatchInst.ST_IDLE

        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('instId', self.instId)

    @property
    def matchId(self):
        return self.area.matchId

    @property
    def roomId(self):
        return self.area.roomId

    @property
    def state(self):
        return self._state

    @property
    def matchConf(self):
        return self.area.matchConf

    @property
    def signerMap(self):
        return self._signerMap

    @property
    def signerCount(self):
        return len(self._signerMap)

    def findSigner(self, userId):
        return self._signerMap.get(userId)

    def getTotalSignerCount(self):
        if self.state < MatchInst.ST_START:
            return self.area.getTotalSignerCount(self)
        return 0

    def buildStatus(self):
        return MatchInstStatus(self.instId, self._state, self.signerCount)

    @locked
    def load(self):
        if self._state == MatchInst.ST_IDLE:
            self._doLoad()
        else:
            self._logger.error('MatchInst.load fail',
                               'state=', self._state,
                               'err=', 'BadState')
            raise BadStateException()

    @locked
    def cancel(self, reason):
        if self._state < MatchInst.ST_FINAL:
            self._doCancel(reason)
        else:
            self._logger.error('MatchInst.cancel fail',
                               'state=', self._state,
                               'err=', 'BadState')
            raise BadStateException()

    @locked
    def cancelSigners(self, reason, userIds):
        if self._state < MatchInst.ST_FINAL:
            for userId in userIds:
                signer = self._signerMap.get(userId)
                if signer:
                    self._cancelSigner(signer, reason)
        else:
            self._logger.error('MatchInst.cancelSigners fail',
                               'state=', self._state,
                               'err=', 'BadState')
            raise BadStateException()

    @locked
    def moveTo(self, toInstId, userIds):
        if self._state == MatchInst.ST_START:
            self._doMoveTo(toInstId, userIds)
        else:
            self._logger.error('MatchInst.moveTo fail',
                               'state=', self._state,
                               'toInstId=', toInstId,
                               'userIds=', userIds,
                               'err=', 'BadState')
            raise BadStateException()

    @locked
    def startSignin(self):
        if self._state < MatchInst.ST_SIGNIN:
            self._doStartSignin()
        else:
            self._logger.error('MatchInst.startSignin fail',
                               'state=', self._state,
                               'err=', 'BadState')
            raise BadStateException()

    @locked
    def prepare(self):
        if self._state < MatchInst.ST_PREPARE:
            self._doPrepare()
        else:
            self._logger.error('MatchInst.prepare fail',
                               'state=', self._state,
                               'err=', 'BadState')
            raise BadStateException()

    @locked
    def start(self):
        if self._state < MatchInst.ST_STARTING:
            self._doStart()
        else:
            self._logger.error('MatchInst.start fail',
                               'state=', self._state,
                               'err=', 'BadState')
            raise BadStateException()

    def _fillSigner(self, signer):
        userName, sessionClientId, _snsId = self.area.userInfoLoader.loadUserAttrs(signer.userId,
                                                                                   ['name', 'sessionClientId', 'snsId'])
        signer.userName = strutil.ensureString(userName)
        signer.clientId = strutil.ensureString(sessionClientId)
        if self._logger.isDebug():
            self._logger.debug('MatchInst._fillSigner',
                               'userId=', signer.userId,
                               'userName=', signer.userName,
                               'clientId=', signer.clientId)

    def signin(self, userId, feeIndex):
        if self.matchConf.fees and (feeIndex < 0 or feeIndex >= len(self.matchConf.fees)):
            raise SigninException('请选择报名费')
        self._ensureCanSignin(userId)
        fee = self.matchConf.fees[feeIndex] if self.matchConf.fees else None
        self.area.signIF.signin(userId, self.matchId, self.roomId, self.instId, fee)
        signer = self.findSigner(userId)
        if signer:
            self._logger.info('MatchInst.signin ok1',
                              'state=', self._state,
                              'userId=', userId,
                              'feeIndex=', feeIndex,
                              'signerCount=', self.signerCount,
                              'fee=', signer.feeItem.toDict() if signer.feeItem else None)
            return signer
        timestamp = pktimestamp.getCurrentTimestamp()
        signer = Signer(userId, self.instId, timestamp)
        signer.isEnter = True
        signer.inst = self
        signer.feeItem = TYContentItem(fee.assetKindId, fee.count) if fee else None

        self._signerMap[userId] = signer
        self._fillSigner(signer)

        bireport.matchUserSignin(self.area.gameId, self.area.roomId,
                                 self.matchId, self.area.matchName,
                                 instId=self.instId,
                                 userId=userId,
                                 clientId=signer.clientId)

        self._logger.hinfo('MatchInst.signin ok',
                           'state=', self._state,
                           'userId=', userId,
                           'signerCount=', self.signerCount,
                           'fee=', signer.feeItem.toDict() if signer.feeItem else None)
        return signer

    def signout(self, signer):
        assert (signer.inst == self)
        if self._state != MatchInst.ST_SIGNIN:
            raise SigninStoppedException()
        del self._signerMap[signer.userId]

        bireport.matchUserSignout(self.area.gameId, self.area.roomId,
                                  self.matchId, self.area.matchName,
                                  instId=self.instId,
                                  userId=signer.userId)

        self.area.signIF.signout(signer.userId, self.matchId, self.roomId, self.instId, signer.feeItem)
        self._logger.hinfo('MatchInst.signout ok',
                           'state=', self._state,
                           'userId=', signer.userId,
                           'fee=', signer.feeItem.toDict() if signer.feeItem else None,
                           'signerCount=', self.signerCount)

    def enter(self, signer):
        assert (signer.inst == self)
        if self._state == MatchInst.ST_SIGNIN or self._state == MatchInst.ST_PREPARE:
            signer.isEnter = True
            clientId, userName = self.area.userInfoLoader.loadUserAttrs(signer.userId, ['sessionClientId', 'name'])
            signer.clientId = strutil.ensureString(clientId, '')
            signer.userName = strutil.ensureString(userName, '')
            bireport.matchUserEnter(self.area.gameId, self.area.roomId,
                                    self.matchId, self.area.matchName,
                                    instId=self.instId,
                                    userId=signer.userId,
                                    clientId=signer.clientId)
            self._logger.hinfo('MatchInst.enter ok',
                               'state=', self._state,
                               'userId=', signer.userId,
                               'userName=', signer.userName,
                               'clientId=', signer.clientId,
                               'signerCount=', self.signerCount)

    def leave(self, signer):
        assert (signer.inst == self)
        if self._state == MatchInst.ST_SIGNIN or self._state == MatchInst.ST_PREPARE:
            signer.isEnter = False
            signer.isLocked = False
            bireport.matchUserLeave(self.area.gameId, self.area.roomId,
                                    self.matchId, self.area.matchName,
                                    instId=self.instId,
                                    userId=signer.userId)
            self._logger.hinfo('MatchInst.leave ok',
                               'state=', self._state,
                               'userId=', signer.userId,
                               'signerCount=', self.signerCount)

    def _doLoad(self):
        assert (self._state == MatchInst.ST_IDLE)
        self._logger.hinfo('MatchInst._doLoad ...',
                           'state=', self._state)
        self._state = MatchInst.ST_LOAD
        if self._needLoad:
            signers = self.area.signIF.loadAllUsers(self.matchId, self.roomId, self.instId)
            for signer in signers:
                signer.inst = self
                self._signerMap[signer.userId] = signer
                if self.matchConf.start.isUserCountType():
                    signer.isEnter = True
                    self._fillSigner(signer)
        self._logger.hinfo('MatchInst._doLoad ok',
                           'state=', self._state,
                           'signerCount=', self.signerCount)

    def _doMoveTo(self, toInstId, userIds):
        assert (self._state == MatchInst.ST_START)
        self._logger.info('MatchInst._doMoveTo ...',
                          'state=', self._state,
                          'toInstId=', toInstId,
                          'userIds=', userIds)

        for userId in userIds:
            self.area.signIF.moveTo(userId, self.matchId, self.roomId, self.instId, toInstId)
        self._logger.info('MatchInst._doMoveTo ok',
                          'state=', self._state,
                          'toInstId=', toInstId,
                          'userIds=', userIds)

    def _doCancel(self, reason):
        assert (self._state < MatchInst.ST_FINAL)
        self._logger.info('MatchInst._doCancel ...',
                          'state=', self._state,
                          'reason=', reason)
        self._state = MatchInst.ST_FINAL
        for signer in self._signerMap.values()[:]:
            self._cancelSigner(signer, reason)
        self._logger.info('MatchInst._doCancel ok',
                          'state=', self._state,
                          'reason=', reason)

    def _doStartSignin(self):
        assert (self._state < MatchInst.ST_SIGNIN)
        self._logger.info('MatchInst._doStartSignin ...',
                          'state=', self._state)
        self._state = MatchInst.ST_SIGNIN
        self._logger.info('MatchInst._doStartSignin ok',
                          'state=', self._state)

    def _doPrepare(self):
        assert (self._state < MatchInst.ST_PREPARE)
        self._logger.info('MatchInst._doPrepare ...',
                          'state=', self._state,
                          'signerCount=', self.signerCount)
        startTime = time.time()
        self._state = MatchInst.ST_PREPARE
        self._prelockSigners(self._signerMap.values()[:])
        self._logger.info('MatchInst._doPrepare ok',
                          'state=', self._state,
                          'signerCount=', self.signerCount,
                          'usedTime=', time.time() - startTime)

    def _doStart(self):
        assert (self._state < MatchInst.ST_STARTING)
        self._logger.hinfo('MatchInst._doStart ...',
                           'state=', self._state,
                           'signerCount=', self.signerCount)
        self._state = MatchInst.ST_STARTING
        startTime = time.time()
        totalSignerCount = self.signerCount
        self._lockSigners()
        toKickSigners = []

        if self.matchConf.start.isTimingType():
            # 删除不能处理的（达到最大人数）玩家
            signers = sorted(self._signerMap.values(), cmp=PlayerSort.cmpBySigninTime)
            toKickSigners = signers[self.matchConf.start.userMaxCountPerMatch:]
            for signer in toKickSigners:
                del self._signerMap[signer.userId]
                self._unlockSigner(signer, True)
                self.area.playerNotifier.notifyMatchCancelled(signer,
                                                              MatchFinishReason.RESOURCE_NOT_ENOUGH,
                                                              MatchFinishReason.toString(
                                                                  MatchFinishReason.RESOURCE_NOT_ENOUGH))
        bireport.matchLockUser(self.area.gameId, self.area.roomId,
                               self.matchId, self.area.matchName,
                               instId=self.instId,
                               signinUserCount=totalSignerCount,
                               lockedUserCount=self.signerCount,
                               lockedUserIds=self._signerMap.keys())
        self._logger.hinfo('MatchInst._doStart lockOk',
                           'state=', self._state,
                           'signerCount=', self.signerCount,
                           'kickCount=', len(toKickSigners),
                           'usedTime=', time.time() - startTime)
        if not self.matchConf.start.isUserCountType():
            self.area.playerNotifier.notifyMatchStart(self.instId, self._signerMap.values())
        self.area.signIF.removeAllUsers(self.matchId, self.roomId, self.instId)
        self.area.onInstStarted(self)
        self._state = MatchInst.ST_START
        self._logger.hinfo('MatchInst._doStart ok',
                           'state=', self._state,
                           'signerCount=', self.signerCount,
                           'usedTime=', time.time() - startTime)

    def _lockSigners(self):
        nolocks = []
        for signer in self._signerMap.values():
            if not self._lockSigner(signer):
                nolocks.append(signer)
        for signer in nolocks:
            self._kickoutSigner(signer)

        return nolocks

    def _lockSigner(self, signer):
        if (not signer.isLocked
            and signer.isEnter
            and self.area.signIF.lockUser(self.matchId, self.roomId, self.instId, signer.userId, signer.clientId)):
            signer.isLocked = True
        return signer.isLocked

    def _unlockSigner(self, signer, returnFees=False):
        if signer.isLocked:
            signer.isLocked = False
        fee = signer.feeItem if returnFees else None
        self.area.signIF.unlockUser(self.matchId, self.roomId, self.instId, signer.userId, fee)

    def _prelockSigners(self, signers):
        for signer in signers:
            self._lockSigner(signer)

    def _kickoutSigner(self, signer):
        try:
            returnFees = self.matchConf.fees \
                         and (self.matchConf.start.feeType == FeesType.TYPE_RETURN or signer.isEnter)
            self._unlockSigner(signer, returnFees)
            del self._signerMap[signer.userId]
            kickoutReason = 'nolock' if signer.isEnter else 'noenter'
            bireport.matchUserKickout(self.area.gameId, self.area.roomId,
                                      self.matchId, self.area.matchName,
                                      instId=self.instId,
                                      userId=signer.userId,
                                      kickoutReason=kickoutReason)
            self._logger.info('MatchInst._kickoutSigner ok',
                              'userId=', signer.userId,
                              'kickoutReason=', kickoutReason)
        except:
            self._logger.error('MatchInst._kickoutSigner ERROR', signer.userId)

    def _cancelSigner(self, signer, reason):
        try:
            returnFees = self.matchConf.fees \
                         and (self.matchConf.start.feeType == FeesType.TYPE_RETURN or signer.isEnter)
            if returnFees and reason in (MatchFinishReason.USER_NOT_ENOUGH, MatchFinishReason.RESOURCE_NOT_ENOUGH):
                returnFees = True
            self._unlockSigner(signer, returnFees)
            del self._signerMap[signer.userId]
            self.area.playerNotifier.notifyMatchCancelled(signer, reason, MatchFinishReason.toString(reason))
            self._logger.info('MatchInst._cancelSigner ok',
                              'userId=', signer.userId,
                              'reason=', reason,
                              'returnFees=', returnFees)
        except:
            self._logger.error('MatchInst._cancelSigner ERROR', signer.userId)

    def _ensureCanSignin(self, userId):
        # 报名还未开始
        if self._state < MatchInst.ST_SIGNIN:
            raise SigninNotStartException(self.signinTimeStr)

        # 报名已经截止
        if self._state >= MatchInst.ST_PREPARE:
            raise SigninStoppedException()

        # 已经报名
        if self.findSigner(userId):
            raise AlreadySigninException()

        # 检查报名人数是否已满
        if (self.matchConf.start.isTimingType()
            and self.signerCount >= self.matchConf.start.signinMaxCountPerMatch):
            raise SigninFullException()


class MatchGroup(HeartbeatAble):
    ST_IDLE = 0
    ST_SETUP = 1
    ST_START = 2
    ST_FINISHING = 3
    ST_FINISH = 4
    ST_FINALING = 5
    ST_FINAL = 6

    def __init__(self, area, instId, matchingId, groupId,
                 groupName, stageIndex, isGrouping, totalPlayerCount):
        super(MatchGroup, self).__init__()
        # 赛区
        self.area = area
        # 实例ID
        self.instId = instId
        # 比赛ID
        self.matchingId = matchingId
        # 分组ID
        self.groupId = groupId
        # 分组名称
        self.groupName = groupName
        # 阶段index
        self.stageIndex = stageIndex
        # 阶段配置
        self.stageConf = area.matchConf.stages[stageIndex]
        # 是否分组
        self.isGrouping = isGrouping
        self.totalPlayerCount = totalPlayerCount
        # 玩家map，key=userId, value=Player
        self._playerMap = {}
        # 分组状态
        self._state = MatchGroup.ST_IDLE
        # 分组完成原因
        self._finishReason = MatchFinishReason.FINISH
        # 排行榜
        self._rankList = []
        # 积分排行榜
        self._ranktops = []
        # 完成牌局局数的玩家
        self._finishCardCountPlayerSet = set()
        # 打牌的桌子
        self._busyTableSet = set()
        # 所有用于该组的桌子
        self._idleTableList = []
        # 所有用于该组的桌子
        self._allTableSet = set()
        # 刚刚结束的玩家列表
        self._winlosePlayerList = []
        # 等待的玩家列表
        self._waitPlayerList = []
        # 放弃比赛的玩家列表
        self._giveupPlayerSet = []
        # 最后开局时间
        self._lastTableTime = 0
        # 最后一次检查超时桌子的时间
        self._lastCheckTimeoutTableTime = None
        # 底分增长次数
        self._growCount = 0
        # 最后增长底分时间
        self._lastGrowTime = None
        # 底分
        self._loseBetScore = self.stageConf.chipBase
        # ASS淘汰分
        self._assLoseScore = self._calcASSLoseScore()
        # 分组开始时的总人数
        self._startPlayerCount = 0
        # 本组启动时间
        self._startTime = None
        self._lastActiveTime = None
        self._processWaitPlayerCount = 0
        self._hasTimeoutTable = False
        # 日志
        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('instId', self.instId)
        self._logger.add('matchingId', self.matchingId)
        self._logger.add('groupId', self.groupId)
        self._logger.add('stageIndex', self.stageIndex)

    @property
    def matchId(self):
        return self.area.matchId

    @property
    def matchConf(self):
        return self.area.matchConf

    @property
    def state(self):
        return self._state

    @property
    def playerCount(self):
        return len(self._playerMap)

    @property
    def finishReason(self):
        return self._finishReason

    @property
    def playerMap(self):
        return self._playerMap

    @property
    def rankList(self):
        return self._rankList

    @property
    def ranktops(self):
        return self._ranktops

    @property
    def startPlayerCount(self):
        return self._startPlayerCount

    @property
    def assLoseScore(self):
        return self._assLoseScore

    @property
    def loseBetScore(self):
        return self._loseBetScore

    @property
    def startTime(self):
        return self._startTime

    @property
    def lastActiveTime(self):
        return self._lastActiveTime

    def findPlayer(self, userId):
        return self._playerMap.get(userId)

    def addPlayer(self, player):
        player._group = self
        player.instId = self.instId
        self._playerMap[player.userId] = player
        if self._logger.isDebug():
            self._logger.debug('MatchGroup.addPlayer ok',
                               'userId=', player.userId)

    def buildStatus(self):
        return MatchGroupStatus(self.groupId, self.matchingId, self._state,
                                self.calcUncompleteTableCount(),
                                self.calcRemTimes(),
                                self._lastActiveTime,
                                self.playerCount)

    def calcNeedTableCount(self):
        return (self.playerCount + self.area.tableSeatCount - 1) / self.area.tableSeatCount

    def calcUncompleteTableCount(self):
        busyTableCount = len(self._busyTableSet)
        waitUserCount = len(self._waitPlayerList)
        winloseUserCount = len(self._winlosePlayerList)
        if self._logger.isDebug():
            self._logger.debug('MatchGroup.calcUncompleteTableCount',
                               'busyTableCount=', busyTableCount,
                               'waitUserCount=', waitUserCount,
                               'winloseUserCount=', winloseUserCount,
                               'ret=',
                               int(busyTableCount + (waitUserCount + winloseUserCount) / self.matchConf.tableSeatCount))
        return int(busyTableCount + (waitUserCount + winloseUserCount) / self.matchConf.tableSeatCount)

    def calcTotalUncompleteTableCount(self):
        return self.area.calcTotalUncompleteTableCount(self)

    def calcRemTimes(self, timestamp=None):
        timestamp = timestamp or pktimestamp.getCurrentTimestamp()
        playTime = self._lastTableTime
        waitUserCount = len(self._waitPlayerList)
        winloseUserCount = len(self._winlosePlayerList)
        waitTableCount = (waitUserCount + winloseUserCount) / self.matchConf.tableSeatCount
        if waitTableCount > 0:
            playTime = timestamp
        if playTime + self.matchConf.start.tableAvgTimes < timestamp:
            playTime = playTime + self.matchConf.start.tableTimes
        else:
            playTime = playTime + self.matchConf.start.tableAvgTimes
        return max(0, playTime - timestamp)

    def calcTotalRemTimes(self, timestamp):
        return self.area.calcTotalRemTimes(self)

    def start(self):
        if self._state != MatchGroup.ST_IDLE:
            self._logger.error('MatchGroup.start fail',
                               'state=', self._state,
                               'err=', 'BadState')
            raise BadStateException()

        self._logger.hinfo('MatchGroup.start ...',
                           'state=', self._state,
                           'userCount=', len(self._playerMap))
        self._state = MatchGroup.ST_SETUP
        self._startPlayerCount = len(self._playerMap)
        self._rankList = list(self._playerMap.values())
        self._startTime = pktimestamp.getCurrentTimestamp()
        self._lastActiveTime = self._startTime
        self._startHeartbeat()
        self._logger.hinfo('MatchGroup.start ok',
                           'state=', self._state,
                           'userCount=', len(self._playerMap))

    def kill(self, reason):
        assert (reason != MatchFinishReason.FINISH)
        self._logger.info('MatchGroup.kill ...',
                          'state=', self._state,
                          'reason=', reason)
        self.postCall(self._doKill, reason)
        self._logger.info('MatchGroup.kill ok',
                          'state=', self._state,
                          'reason=', reason)

    def final(self):
        assert (self._state == MatchGroup.ST_FINISH)
        self._logger.info('MatchGroup.final ...',
                          'state=', self._state)
        self.postCall(self._doFinal)
        self._logger.info('MatchGroup.final ok',
                          'state=', self._state)

    def giveup(self, player):
        '''
        玩家放弃比赛
        '''
        assert (player.group == self)

        if player.state != Player.STATE_WAIT:
            self._logger.warn('MatchGroup.giveup failed',
                              'userId=', player.userId,
                              'playerState=', player.state,
                              'err=', 'NotWaitState')
            return False

        self._addGiveupPlayer(player)

        self._logger.info('MatchGroup.giveup ok',
                          'userId=', player.userId,
                          'playerState=', player.state)
        return True

    def winlose(self, player, deltaScore, isWin, isKill=False):
        assert (player.group == self)
        table = player.table

        if self._state != MatchGroup.ST_START:
            self._logger.error('MatchGroup.winlose fail',
                               'state=', self._state,
                               'userId=', player.userId,
                               'tableId=', table.tableId if table else None,
                               'deltaScore=', deltaScore,
                               'isWin=', isWin,
                               'isKill=', isKill,
                               'busyTableCount=', len(self._busyTableSet))
            raise BadStateException()

        player._state = Player.STATE_WINLOSE
        player.score += int(deltaScore)

        self._logger.info('MatchGroup.winlose ok',
                          'state=', self._state,
                          'userId=', player.userId,
                          'tableId=', table.tableId if table else None,
                          'seatId=', player.seat.seatId if player.seat else None,
                          'deltaScore=', deltaScore,
                          'score=', player.score,
                          'isWin=', isWin,
                          'isKill=', isKill,
                          'busyTableCount=', len(self._busyTableSet))
        if not table:
            # 本桌排名第一
            player.tableRank = 1
            # 添加到winlose列表
            self._addWinlosePlayers(player)
        elif table.getPlayingPlayerCount() <= 0:
            playerList = table.getPlayerList()
            # 本桌子用户排名
            self._sortTableRank(playerList)
            # 让该桌子上的用户站起并释放桌子
            self._clearAndReleaseTable(table)
            # 添加到winlose列表
            self._addWinlosePlayers(playerList)

    def _doHeartbeatImpl(self):
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._doHeartbeatImpl',
                               'state=', self._state)

        self._lastActiveTime = pktimestamp.getCurrentTimestamp()

        if self._state == MatchGroup.ST_SETUP:
            self._doStart()

        if self._state == MatchGroup.ST_START:
            self._checkGrowLoseBetScore()
            self._processTimeoutTables()
            self._processWinlosePlayers()
            self._processGiveupPlayers()
            self._processWaitPlayers()
            self._reclaimTables()

        if self._state == MatchGroup.ST_START:
            if self._isGroupFinished():
                self._doFinish()

        if self._state < MatchGroup.ST_FINISH:
            timestamp = pktimestamp.getCurrentTimestamp()
            if timestamp - self._startTime > self._calcMaxPlayTime():
                self._doFinish(MatchFinishReason.OVERTIME)

        if self._state == MatchGroup.ST_START and len(self._waitPlayerList) >= self.area.tableSeatCount:
            return 0.08
        return 1

    def _calcMaxPlayTime(self):
        return self.matchConf.start.maxPlayTime

    def _doStart(self):
        assert (self._state == MatchGroup.ST_SETUP)
        self._state = MatchGroup.ST_START

        self._logger.hinfo('MatchGroup._doStart ...',
                           'state=', self._state,
                           'playerCount=', self.playerCount,
                           'idleTableCount=', self.area.tableManager.idleTableCount)

        if self.playerCount < self.area.tableSeatCount:
            # 人数不足
            self._logger.hinfo('MatchGroup._doStart fail',
                               'state=', self._state,
                               'userCount=', self.playerCount,
                               'err=', 'NotEnoughUser')
            self._doFinish(MatchFinishReason.USER_NOT_ENOUGH)
            return

        needTableCount = self.calcNeedTableCount()
        if self.area.tableManager.idleTableCount < needTableCount:
            # 桌子资源不足
            self._logger.error('MatchGroup._doStart fail',
                               'playerCount=', self.playerCount,
                               'idleTableCount=', self.area.tableManager.idleTableCount,
                               'err=', 'NotEnoughTable')
            self._doFinish(MatchFinishReason.RESOURCE_NOT_ENOUGH)
            return

        timestamp = pktimestamp.getCurrentTimestamp()
        self._lastGrowTime = timestamp
        # 借桌子
        self._idleTableList = self.area.tableManager.borrowTables(needTableCount)
        self._allTableSet = set(self._idleTableList)

        # 初始化用户数据
        self._initPlayerDatas()
        self._sortMatchRanks()
        self._initWaitPlayerList()

        self._lastCheckTimeoutTableTime = timestamp + self.matchConf.start.tableTimes

        for player in self._waitPlayerList:
            self.area.playerNotifier.notifyStageStart(player)

        nwait = len(self._playerMap) % self.area.tableSeatCount
        if nwait < self.area.tableSeatCount:
            for i in range(-1, -1 - nwait, -1):
                player = self._waitPlayerList[i]
                self._processWaitPlayerCount += 1
                self.area.signIF.lockUser(self.matchId, self.area.roomId, self.instId, player.userId, player.clientId)
                self.area.playerNotifier.notifyMatchWait(player)
                self._logger.info('MatchGroup._doStart bye',
                                  'playerCount=', self.playerCount,
                                  'userId=', player.userId,
                                  'index=', i)

        self._logger.hinfo('MatchGroup._doStart ok',
                           'playerCount=', self.playerCount,
                           'idleTableCount=', self.area.tableManager.idleTableCount)

    def _doFinish(self, reason=MatchFinishReason.FINISH):
        assert (self.state < MatchGroup.ST_FINISHING)
        self._state = MatchGroup.ST_FINISHING
        self._finishReason = reason

        self._logger.hinfo('MatchGroup._doFinish ...',
                           'state=', self._state,
                           'busyTableCount=', len(self._busyTableSet),
                           'winlosePlayerCount=', len(self._winlosePlayerList),
                           'reason=', reason)

        riseUserCount = 0
        if reason == MatchFinishReason.FINISH:
            riseUserCount = min(self.stageConf.riseUserCount, len(self._rankList))
            if len(self._busyTableSet) > 0:
                self._logger.error('MatchGroup._doFinish issue',
                                   'state=', self._state,
                                   'busyTableCount=', len(self._busyTableSet),
                                   'winlosePlayerCount=', len(self._winlosePlayerList),
                                   'reason=', reason,
                                   'err=', 'HaveBusyTable')

            if len(self._winlosePlayerList) != 0:
                self._logger.error('MatchGroup._doFinish issue',
                                   'state=', self._state,
                                   'busyTableCount=', len(self._busyTableSet),
                                   'winlosePlayerCount=', len(self._winlosePlayerList),
                                   'reason=', reason,
                                   'err=', 'HaveWinlosePlayer')

            while len(self._rankList) > riseUserCount:
                self._outPlayer(self._rankList[-1], MatchFinishReason.USER_LOSER)

            if self.stageIndex + 1 >= len(self.matchConf.stages):
                # 最后一个阶段, 给晋级的人发奖
                while self._rankList:
                    self._outPlayer(self._rankList[-1], MatchFinishReason.USER_LOSER)
        else:
            # 释放所有桌子
            for table in self._busyTableSet:
                self._clearTable(table)
            self._busyTableSet.clear()

            while self._rankList:
                self._outPlayer(self._rankList[-1], reason)

        self._releaseResource()

        self._state = MatchGroup.ST_FINISH

        self.area.onGroupFinish(self)

        self._logger.hinfo('MatchGroup._doFinish ok',
                           'state=', self._state,
                           'reason=', reason)

    def _doKill(self, reason):
        if self._state < MatchGroup.ST_FINISH:
            self._doFinish(reason)
            self._logger.info('MatchGroup._doKill ok',
                              'state=', self._state,
                              'reason=', reason)
        else:
            self._logger.warn('MatchGroup._doKill fail',
                              'state=', self._state,
                              'reason=', reason,
                              'err=', 'BadState')

    def _doFinal(self):
        if self._state == MatchGroup.ST_FINISH:
            self._state = MatchGroup.ST_FINALING
            self._stopHeartbeat()
            self._state = MatchGroup.ST_FINAL
            self._logger.info('MatchGroup._doFinal ok',
                              'state=', self._state)
        else:
            self._logger.warn('MatchGroup._doFinal fail',
                              'state=', self._state,
                              'err=', 'BadState')

    def _releaseResource(self):
        self._finishCardCountPlayerSet.clear()
        self._winlosePlayerList = []
        for table in self._busyTableSet:
            self._clearTable(table)

        self._busyTableSet.clear()
        self._idleTableList = []
        self.area.tableManager.returnTables(self._allTableSet)
        self._allTableSet.clear()

    def _isGroupFinished(self):
        return len(self._finishCardCountPlayerSet) >= len(self._rankList)

    def _processTimeoutTables(self):
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._processTimeoutTables',
                               'state=', self._state,
                               'busyTableCount=', len(self._busyTableSet),
                               'hasTimeoutTable=', self._hasTimeoutTable,
                               'lastCheckTimeoutTableTime=', self._lastCheckTimeoutTableTime)
        timestamp = pktimestamp.getCurrentTimestamp()
        # 每tableTimeoutCheckInterval秒检查一次
        if self._hasTimeoutTable or (
                        timestamp - self._lastCheckTimeoutTableTime >= self.stageConf.tableTimeoutCheckInterval):
            self._lastCheckTimeoutTableTime = timestamp
            overtimeTables = []
            for table in self._busyTableSet:
                if timestamp - table.playTime >= self.matchConf.start.tableTimes:
                    overtimeTables.append(table)
            processCount = min(len(overtimeTables), 10)
            for table in overtimeTables:
                processCount -= 1
                if not table.playTime:
                    self._logger.warn('MatchGroup._processTimeoutTables notPlayTime',
                                      'state=', self._state,
                                      'tableId=', table.tableId,
                                      'timestamp=', timestamp)
                else:
                    self._logger.info('MatchGroup._processTimeoutTables tableTimeout',
                                      'state=', self._state,
                                      'tableId=', table.tableId,
                                      'playTimes=', (timestamp - table.playTime))
                    if timestamp - table.playTime >= self.matchConf.start.tableTimes:
                        playerList = table.getPlayingPlayerList()
                        for player in playerList:
                            self.winlose(player, 0, True, True)
                if processCount <= 0:
                    break
            self._hasTimeoutTable = processCount < len(overtimeTables)

    def _processWinlosePlayers(self):
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._processWinlosePlayers',
                               'state=', self._state,
                               'winloseUserIds=', [p.userId for p in self._winlosePlayerList])

        if self._winlosePlayerList:
            self._sortMatchRanks()
            winlosePlayerList = self._winlosePlayerList
            self._winlosePlayerList = []
            if self.stageConf.type == StageType.ASS:
                self._processWinlosePlayersAss(winlosePlayerList)
            else:
                self._processWinlosePlayersDieout(winlosePlayerList)

    def _processWinlosePlayersAss(self, winlosePlayerList):
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._processWinlosePlayersAss',
                               'state=', self._state,
                               'winloseUserIds=', [p.userId for p in winlosePlayerList])

        losers = []
        waitPlayers = []
        for player in winlosePlayerList:
            if self._checkWaitFinishOrFinishStageASS():
                # 当前阶段要结束了, 把这些player算作完成CardCount的玩家
                self._playerFinishCardCount(player)
                waitPlayers.append(player)
                continue

            if player.score < self._assLoseScore:
                losers.append(player)
            else:
                waitPlayers.append(player)
                if player.cardCount >= self.stageConf.cardCount:
                    self._playerFinishCardCount(player)
                else:
                    self._addWaitPlayer(player)

        for player in losers:
            player.whenOut = Player.WHEN_OUT_ASS
            self._outPlayer(player)

        for player in waitPlayers:
            self.area.playerNotifier.notifyMatchWait(player)

        # 处理不能晋级的人
        if self.matchConf.outAssWait:
            try:
                losers = []
                keepCount = self.stageConf.riseUserRefer if self.matchConf.outAssKeepReferCount else self.stageConf.riseUserCount

                if len(self._finishCardCountPlayerSet) > keepCount:
                    finishList = list(self._finishCardCountPlayerSet)
                    finishList.sort(cmp=PlayerSort.cmpByScore)
                    losers = finishList[keepCount:]

                for i, player in enumerate(losers):
                    player.whenOut = Player.WHEN_OUT_NORMAL
                    player.rank = max(1, len(self._rankList))
                    self._logger.info('MatchGroup._processWinlosePlayersAss outFinishCardCountPlayer',
                                      'state=', self._state,
                                      'userId=', player.userId,
                                      'rankInFinishPlayers=', i + 1,
                                      'rank=', player.rank,
                                      'keepCount=', keepCount)
                    self._outPlayer(player)
            except:
                self._logger.error('MatchGroup._processWinlosePlayersAss',
                                   'state=', self._state)

    def _processWinlosePlayersDieout(self, winlosePlayerList):
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._processWinlosePlayersDieout',
                               'state=', self._state,
                               'winloseUserIds=', [p.userId for p in winlosePlayerList])

        for player in winlosePlayerList:
            # 如果打的牌数达到最大定义的牌数，等待阶段结束排名
            if player.cardCount < self.stageConf.cardCount:
                # 否则放入等待队列，等待再次开始
                self._addWaitPlayer(player)
            else:
                self._playerFinishCardCount(player)

        for player in winlosePlayerList:
            self.area.playerNotifier.notifyMatchWait(player)

    def _processGiveupPlayers(self):
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._processGiveupPlayers',
                               'state=', self._state,
                               'giveupUserIds=', [p.userId for p in self._giveupPlayerSet])

        requestGiveupPlayers = self._giveupPlayerSet
        self._giveupPlayerSet = set()

        for player in requestGiveupPlayers:
            if (self.stageConf.type != StageType.ASS
                or len(self._rankList) <= self.stageConf.riseUserCount
                or self.stageIndex + 1 >= len(self.matchConf.stages)):
                if self._logger.isDebug():
                    self._logger.debug('MatchGroup._processGiveupPlayers',
                                       'playerCount=', self.playerCount,
                                       'state=', self._state,
                                       'risePlayerCount=', self.stageConf.riseUserCount)
                self.area.playerNotifier.notifyMatchGiveupFailed(player, '您的当前阶段不能退出比赛，请稍候')
            else:
                player.rank = len(self._playerMap)
                try:
                    self._waitPlayerList.remove(player)
                except:
                    pass
                self._outPlayer(player)

    def _processWaitPlayers(self):
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._processWaitPlayers',
                               'state=', self._state,
                               'processWaitPlayerCount=', self._processWaitPlayerCount,
                               'startPlayerCount=', self._startPlayerCount,
                               'waitUserIds=', [p.userId for p in self._waitPlayerList])

        isAllProcess = self._processWaitPlayerCount >= self._startPlayerCount

        # 检查剩余的玩家能不能凑够一桌
        waitCount = len(self._waitPlayerList)
        finishCount = len(self._finishCardCountPlayerSet)
        if (waitCount > 0
            and waitCount < self.area.tableSeatCount
            and (finishCount + waitCount) >= len(self._rankList)):
            # 凑不够一桌，直接结算轮空的用户完成
            self._logger.info('MatchGroup._processWaitPlayers',
                              'state=', self._state,
                              'playerCount=', self.playerCount,
                              'waitUserIds=', [p.userId for p in self._waitPlayerList],
                              'err=', 'UserNotEnough')
            waitPlayerList = self._waitPlayerList
            self._waitPlayerList = []
            for player in waitPlayerList:
                player.cardCount += 1
                self.winlose(player, 0, True, True)
            return

        processedCount = 0
        maxCount = self._calcMaxProcessPlayerCount()
        tableSeatCount = self.area.tableSeatCount
        while (len(self._waitPlayerList) >= tableSeatCount and processedCount < maxCount):
            processedCount += tableSeatCount
            players = self._waitPlayerList[0:tableSeatCount]
            self._waitPlayerList = self._waitPlayerList[tableSeatCount:]
            # 分配桌子
            table = self._borrowTable()
            assert (table is not None)
            table._group = self
            table.playTime = pktimestamp.getCurrentTimestamp()
            table.ccrc += 1
            for i in xrange(self.area.tableSeatCount):
                player = players[i]
                if player.state != Player.STATE_WAIT:
                    self._logger.error('MatchGroup._processWaitPlayers',
                                       'state=', self._state,
                                       'userId=', player.userId,
                                       'playerState=', player.state,
                                       'err=', 'BadUserState')
                    assert (player.state == Player.STATE_WAIT)

                player._state = Player.STATE_PLAYING
                player.cardCount += 1
                player.waitReason = WaitReason.UNKNOWN
                if player.seat:
                    self._logger.error('MatchGroup._processWaitPlayers',
                                       'state=', self._state,
                                       'userId=', player.userId,
                                       'seatLoc=', player.seat.location,
                                       'err=', 'SeatNotEmpty')
                    assert (player.seat is None)
                table.sitdown(player)
                assert (player.seat)
                self._processWaitPlayerCount += 1
                if self._logger.isDebug():
                    self._logger.debug('MatchGroup._processWaitPlayers',
                                       'state=', self._state,
                                       'userId=', player.userId,
                                       'sitdown=', player.seat.location)
            self.area.tableController.startTable(table)
            bireport.matchStartTable(self.area.room.gameId, self.area.roomId,
                                     self.matchId, self.area.matchName,
                                     instId=self.instId,
                                     matchingId=self.matchingId,
                                     stageIndex=self.stageIndex,
                                     groupId=self.groupId,
                                     tableId=table.tableId,
                                     userIds=table.getUserIdList())
            self._logger.info('MatchGroup._processWaitPlayers startTable',
                              'state=', self._state,
                              'tableId=', table.tableId,
                              'userIds=', table.getUserIdList(),
                              'processWaitPlayerCount=', self._processWaitPlayerCount,
                              'startPlayerCount=', self._startPlayerCount)

        if not isAllProcess and self._processWaitPlayerCount >= self._startPlayerCount:
            self._logger.info('MatchGroup._processWaitPlayers',
                              'state=', self._state,
                              'processWaitPlayerCount=', self._processWaitPlayerCount,
                              'startPlayerCount=', self._startPlayerCount,
                              'isAllProcessFinish=', True)

    def _initPlayerDatas(self):
        scoreCalc = PlayerScoreCalc.makeCalc(self.stageConf, self._rankList)
        self._logger.info('MatchGroup._initPlayerDatas',
                          'state=', self._state,
                          'scoreCalcType=', type(scoreCalc),
                          'scoreCalc=', scoreCalc.__dict__)
        for player in self._rankList:
            oldScore = player.score
            player.score = scoreCalc.calc(player.score)
            player.waitTimes = 0
            player.cardCount = 0
            player.tableRank = 0
            self._logger.info('MatchGroup._initPlayerDatas',
                              'state=', self._state,
                              'userId=', player.userId,
                              'score=', player.score,
                              'oldScore=', oldScore)

    def _initWaitPlayerList(self):
        # 排序
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._initWaitPlayerList',
                               'state=', self._state,
                               'userIds=', [p.userId for p in self._rankList])
        self._waitPlayerList = []

        waitPlayers = PlayerQueuing.sort(self.stageConf.seatQueuing, self._rankList)
        byeCount = len(waitPlayers) % self.area.tableSeatCount

        for player in waitPlayers:
            self._addWaitPlayer(player)

        for i in xrange(byeCount):
            self._waitPlayerList[-1 - i].waitReason = WaitReason.BYE

    def _addWinlosePlayers(self, players):
        if isinstance(players, (list, set)):
            self._winlosePlayerList.extend(players)
        else:
            self._winlosePlayerList.append(players)

    def _addWaitPlayer(self, player):
        player._state = Player.STATE_WAIT
        player.waitReason = WaitReason.WAIT
        self._waitPlayerList.append(player)

    def _addGiveupPlayer(self, player):
        assert (player.state == Player.STATE_WAIT)
        self._giveupPlayerSet.add(player)

    def _playerFinishCardCount(self, player):
        player._state = Player.STATE_WAIT
        player.waitReason = WaitReason.RISE
        self._finishCardCountPlayerSet.add(player)
        self._logger.info('MatchGroup._playerFinishCardCount',
                          'userId=', player.userId,
                          'cardCount=', player.cardCount,
                          'totalFinishUserCount=', len(self._finishCardCountPlayerSet))

    def _sortTableRank(self, tablePlayerList):
        tablePlayerList.sort(PlayerSort.cmpByScore)
        for i, player in enumerate(tablePlayerList):
            player.tableRank = i + 1

    def _sortMatchRanks(self):
        # 排序当前的比赛结果
        if self.stageConf.type == StageType.DIEOUT:
            self._rankList.sort(PlayerSort.cmpByTableRanking)
        else:
            self._rankList.sort(PlayerSort.cmpByScore)

        for index in xrange(len(self._rankList)):
            self._rankList[index].rank = index + 1

        ranktops = []
        ranktops.extend(self._rankList)
        ranktops.sort(PlayerSort.cmpByScore)
        newranktops = []
        for index, player in enumerate(ranktops):
            player.scoreRank = index + 1
            newranktops.append([player.userId, player.userName, player.score, player.signinTime])
        self._ranktops = newranktops[0:10]

    def _clearAndReleaseTable(self, table):
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._clearAndReleaseTable',
                               'tableId=', table.tableId)
        players = []
        self.area.tableController.clearTable(table)
        for seat in table.seats:
            if seat.player:
                players.append(seat.player)
                if self._logger.isDebug():
                    self._logger.debug('MatchGroup._clearAndReleaseTable standup',
                                       'tableId=', table.tableId,
                                       'seatId=', seat.seatId,
                                       'userId=', seat.player.userId)
                table.standup(seat.player)

        self._logger.info('MatchGroup._clearAndReleaseTable',
                          'tableId=', table.tableId)
        table._group = None
        table.playTime = None
        self._busyTableSet.remove(table)
        self._idleTableList.append(table)

        for player in players:
            try:
                self.area.signIF.lockUser(self.matchId, self.area.roomId, self.instId, player.userId, player.clientId)
            except:
                self._logger.error('MatchGroup._clearAndReleaseTable lockUserFail',
                                   'tableId=', table.tableId,
                                   'userId=', player.userId)

    def _clearTable(self, table):
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._clearTable',
                               'tableId=', table.tableId)
        players = []
        self.area.tableController.clearTable(table)
        for seat in table.seats:
            if seat.player:
                players.append(seat.player)
                if self._logger.isDebug():
                    self._logger.debug('MatchGroup._clearTable standup',
                                       'tableId=', table.tableId,
                                       'seatId=', seat.seatId,
                                       'userId=', seat.player.userId)
                table.standup(seat.player)

        for player in players:
            try:
                self.area.signIF.lockUser(self.matchId, self.area.roomId, self.instId, player.userId, player.clientId)
            except:
                self._logger.error('MatchGroup._clearTable lockUserFail',
                                   'tableId=', table.tableId,
                                   'userId=', player.userId)

    def _borrowTable(self):
        # 借用桌子
        assert (len(self._idleTableList) > 0)
        table = self._idleTableList.pop(0)
        self._busyTableSet.add(table)
        self._logger.info('MatchGroup._borrowTable',
                          'tableId=', table.tableId)
        return table

    def _releaseTable(self, table):
        # 释放桌子
        assert (table.idleSeatCount == table.seatCount)
        self._logger.info('MatchGroup._releaseTable',
                          'tableId=', table.tableId)
        table._group = None
        table.playTime = None
        self._busyTableSet.remove(table)
        self._idleTableList.append(table)

    def _reclaimTables(self):
        needCount = self.calcNeedTableCount()
        reclaimCount = len(self._allTableSet) - needCount
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._reclaimTables',
                               'needCount=', needCount,
                               'reclaimCount=', reclaimCount,
                               'allCount=', len(self._allTableSet),
                               'tableManager.idleCount=', self.area.tableManager.idleTableCount)

        if reclaimCount > 0:
            count = min(reclaimCount, len(self._idleTableList))
            tables = self._idleTableList[0:count]
            self._idleTableList = self._idleTableList[count:]
            self.area.tableManager.returnTables(tables)
            for table in tables:
                self._allTableSet.remove(table)
            self._logger.info('MatchGroup._reclaimTables',
                              'needCount=', needCount,
                              'reclaimCount=', reclaimCount,
                              'realReclaimCount=', count,
                              'allCount=', len(self._allTableSet),
                              'tableManager.idleCount=', self.area.tableManager.idleTableCount)

    def _calcMaxProcessPlayerCount(self):
        count = 200
        try:
            maxPlayerPerRoom = self.area.tableManager.getTableCountPerRoom() * self.area.tableSeatCount
            countPerRoom = int((maxPlayerPerRoom / self.matchConf.start.startMatchSpeed + 10) / 10)
            count = min(200, self.area.tableManager.roomCount * countPerRoom)
            if self._logger.isDebug():
                self._logger.debug('MatchGroup._calcMaxProcessPlayerCount',
                                   'maxPlayerPerRoom=', maxPlayerPerRoom,
                                   'startMatchSpeed=', self.matchConf.start.startMatchSpeed,
                                   'countPerRoom=', countPerRoom,
                                   'count=', count)
        except:
            self._logger.error()
        return count

    def _checkGrowLoseBetScore(self):
        timestamp = pktimestamp.getCurrentTimestamp()
        if (timestamp - self._lastGrowTime) >= self.stageConf.chipTimes:
            self._lastGrowTime = timestamp
            if self.stageConf.chipGrow >= 100:
                self._growLoseBetChip(self.stageConf.chipGrow)
            else:
                deltaScore = 0
                if self.stageConf.chipGrowBase == 0:
                    deltaScore = self._loseBetScore * self.stageConf.chipGrow
                else:
                    if self._growCount == 0:
                        deltaScore = self.stageConf.chipGrowBase
                    else:
                        deltaScore = self.stageConf.chipGrowBase + self._growCount * self.stageConf.chipGrowIncr
                    self._growCount += 1
                self._growLoseBetScore(deltaScore)

            self._logger.info('MatchGroup._checkGrowLoseBetScore',
                              'lostBetScore=', self._loseBetScore,
                              'assLoseScore=', self._assLoseScore,
                              'growCount=', self._growCount)

    def _growLoseBetScore(self, chipGrow):
        self._loseBetScore += int(chipGrow)
        if self.stageConf.type == StageType.ASS:
            self._assLoseScore = self._calcASSLoseScore()

    def _calcASSLoseScore(self):
        if self.stageConf.type == StageType.ASS:
            loseScore = self.stageConf.loseUserChip
            if loseScore > 1:
                return int(loseScore)
            else:
                return int(loseScore * self._loseBetScore)
        return None

    def _checkWaitFinishOrFinishStageASS(self):
        # 排行榜的人数到达预订人数，当前阶段结束
        return len(self._rankList) <= self.stageConf.riseUserRefer

    def _outPlayer(self, player, reason=MatchFinishReason.USER_LOSER):
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._outPlayer',
                               'userId=', player.userId,
                               'reason=', reason)
        player._state = Player.STATE_OUT
        assert (player.seat is None)

        del self._playerMap[player.userId]
        # 删除已完成cardCount的用户
        self._finishCardCountPlayerSet.discard(player)
        # 删除排行榜中的用户
        self._rankList.remove(player)
        # 玩家完成比赛
        self._doPlayerMatchOver(player, reason)

    def _doPlayerMatchOver(self, player, reason):
        # 解锁玩家
        rankRewards = None

        if (reason == MatchFinishReason.USER_WIN
            or reason == MatchFinishReason.USER_LOSER):
            rankRewards = self._getRewards(player)
            if rankRewards:
                self.area.matchRewards.sendRewards(player, rankRewards)
                if reason == MatchFinishReason.USER_LOSER:
                    reason = MatchFinishReason.USER_WIN

        bireport.matchUserGameOver(self.area.gameId, self.area.roomId,
                                   self.matchId, self.area.matchName,
                                   instId=self.instId,
                                   matchingId=self.matchingId,
                                   stageIndex=self.stageIndex,
                                   groupId=self.groupId,
                                   userId=player.userId,
                                   rank=player.rank,
                                   scoreRank=player.scoreRank,
                                   cardCount=player.cardCount,
                                   stageCardCount=self.stageConf.cardCount,
                                   reason=reason,
                                   whenOut=player.whenOut,
                                   rankRewards=rankRewards.conf if rankRewards else None)

        self._logger.hinfo('MatchGroup._doPlayerMatchOver',
                           'userId=', player.userId,
                           'remUserCount=', len(self._rankList),
                           'rank=', player.rank,
                           'cardCount=', player.cardCount,
                           'stageCardCount=', self.stageConf.cardCount,
                           'reason=', reason,
                           'whenOut=', player.whenOut,
                           'rankRewards=', rankRewards.conf if rankRewards else None)

        self.area.playerNotifier.notifyMatchOver(player, reason, rankRewards)
        self.area.signIF.unlockUser(self.matchId, self.area.roomId, self.instId, player.userId, None)

    def _getRewards(self, player):
        # 看当前阶段是否有配置奖励
        rankRewardsList = self.stageConf.rankRewardsList if self.isGrouping else self.matchConf.rankRewardsList
        if self._logger.isDebug():
            self._logger.debug('MatchGroup._getRewards',
                               'userId=', player.userId,
                               'rank=', player.rank,
                               'rankRewardsList=', rankRewardsList,
                               'stageConf.rankRewards=', self.stageConf.rankRewardsList)
        if rankRewardsList:
            for rankRewards in rankRewardsList:
                if ((rankRewards.startRank == -1 or player.rank >= rankRewards.startRank)
                    and (rankRewards.endRank == -1 or player.rank <= rankRewards.endRank)):
                    return rankRewards
        return None


class MatchInstStatus(object):
    def __init__(self, instId, state, signerCount):
        self.instId = instId
        self.state = state
        self.signerCount = signerCount

    def toDict(self):
        d = {}
        d['iid'] = self.instId
        d['st'] = self.state
        d['sc'] = self.signerCount
        return d

    @classmethod
    def fromDict(cls, d):
        return MatchInstStatus(d['iid'], d['st'], d['sc'])


class MatchGroupStatus(object):
    def __init__(self, groupId, matchingId, state,
                 uncompleteTableCount, remTimes, lastActiveTime, playerCount):
        # 分组ID
        self.groupId = groupId
        # 比赛ID
        self.matchingId = matchingId
        # 状态
        self.state = state
        # 剩余几桌没完成
        self.uncompleteTableCount = uncompleteTableCount
        # 剩余时间
        self.remTimes = remTimes
        # 最后活跃时间
        self.lastActiveTime = lastActiveTime
        # 时间戳
        self.timestamp = None
        # 当前分组的人数
        self.playerCount = playerCount

    def toDict(self):
        d = {}
        d['gid'] = self.groupId
        d['mid'] = self.matchingId
        d['st'] = self.state
        d['utc'] = self.uncompleteTableCount
        d['rt'] = self.remTimes
        d['lat'] = self.lastActiveTime
        d['pc'] = self.playerCount
        return d

    @classmethod
    def fromDict(cls, d):
        return MatchGroupStatus(d['gid'], d['mid'], d['st'], d['utc'], d['rt'], d['lat'], d['pc'])


class MatchAreaStatus(object):
    def __init__(self):
        # 比赛实例状态
        self.instStatus = None
        # key=roomId, value=MatchAreaStatus
        self.groupStatusMap = {}
        # 分赛区时间戳
        self.timestamp = None

    def toDict(self):
        d = {}
        if self.instStatus:
            d['inst'] = self.instStatus.toDict()
        groups = []
        for groupStatus in self.groupStatusMap.values():
            groups.append(groupStatus.toDict())
        d['groups'] = groups
        d['ts'] = self.timestamp
        return d

    @classmethod
    def fromDict(cls, d):
        ret = MatchAreaStatus()
        instD = d.get('inst')
        if instD:
            ret.instStatus = MatchInstStatus.fromDict(instD)
        ret.timestamp = d['ts']
        for groupD in d.get('groups', []):
            groupStatus = MatchGroupStatus.fromDict(groupD)
            groupStatus.timestamp = ret.timestamp
            ret.groupStatusMap[groupStatus.groupId] = groupStatus
        return ret


class MatchMasterStatus(object):
    def __init__(self):
        # key=roomId, value=MatchAreaStatus
        self.areaStatusMap = {}

    def toDict(self):
        d = {}
        areaStatusMap = {}
        for roomId, areaStatus in self.areaStatusMap.iteritems():
            areaStatusMap[roomId] = areaStatus.toDict()
        d['asm'] = areaStatusMap
        return d

    @classmethod
    def fromDict(cls, d):
        ret = MatchMasterStatus()
        areaStatusMap = d['asm']
        for roomId, areaStatusD in areaStatusMap.iteritems():
            ret.areaStatusMap[roomId] = MatchAreaStatus.fromDict(areaStatusD)
        return ret


class MatchMasterStub(object):
    '''
    赛事在赛区控制对象，运行于赛区中
    '''

    def __init__(self, roomId):
        # 所有赛区的状态map，key=roomId, value=MatchAreaStatus
        self.masterStatus = MatchMasterStatus()
        self.roomId = roomId
        self._logger = Logger()
        self._logger.add('roomId', roomId)

    def areaHeartbeat(self, area):
        '''
        area心跳，运行
        '''
        raise NotImplemented()

    def areaGroupStart(self, area, group):
        '''
        向主赛区汇报
        '''
        raise NotImplemented()

    def areaGroupFinish(self, area, group):
        '''
        向主赛区汇报
        '''
        raise NotImplemented()

    def areaInstStarted(self, area, inst):
        '''
        向主赛区汇报比赛实例启动成功，汇报报名用户列表
        '''
        raise NotImplemented()

    def onMasterHeartbeat(self, masterStatus):
        '''
        主赛区心跳回调
        '''
        assert (isinstance(masterStatus, MatchMasterStatus))
        self.masterStatus = masterStatus


class MatchArea(HeartbeatAble):
    '''
    赛区是一个分组管理器
    '''
    ST_IDLE = 0
    ST_START = 1

    HEARTBEAT_TO_MASTER_INTERVAL = 5

    def __init__(self, room, matchId, matchConf, masterStub):
        super(MatchArea, self).__init__()
        # 控制房间
        self.room = room
        # 比赛ID
        self.matchId = matchId
        # 比赛配置
        self.matchConf = matchConf
        # 当前比赛实例
        self._curInst = None
        # 当前该赛区比赛中的所有分组
        self._groupMap = {}
        # 赛区状态
        self._state = MatchArea.ST_IDLE
        # 最后心跳到master的时间
        self._lastHeartbeatToMasterTime = None
        # 主控stub
        self.masterStub = masterStub

        self.tableManager = None
        self.signIF = None
        self.tableController = None
        self.playerNotifier = None
        self.matchRewards = None
        self.userInfoLoader = None

        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('roomId', self.room.roomId)

    @property
    def tableSeatCount(self):
        return self.tableManager.tableSeatCount

    @property
    def gameId(self):
        return self.room.gameId

    @property
    def roomId(self):
        return self.room.roomId

    @property
    def curInst(self):
        return self._curInst

    @property
    def state(self):
        return self._state

    @property
    def tableId(self):
        return self.matchConf.tableId

    @property
    def seatId(self):
        return self.matchConf.seatId

    @property
    def matchName(self):
        return self.room.roomConf.get('name')

    def start(self):
        assert (self._state == MatchArea.ST_IDLE)
        self._logger.info('MatchArea.start ...',
                          'state=', self._state)
        self._state = MatchArea.ST_START
        self._startHeartbeat()
        self._logger.info('MatchArea.start ok',
                          'state=', self._state)

    def findSigner(self, userId):
        if self._curInst:
            return self._curInst.findSigner(userId)
        return None

    def findPlayer(self, userId):
        for group in self._groupMap.values():
            player = group.findPlayer(userId)
            if player:
                return player
        return None

    def findGroup(self, groupId):
        return self._groupMap.get(groupId)

    @classmethod
    def parseStageId(cls, matchingId, groupId):
        try:
            return groupId[0:groupId.rfind('.')]
        except:
            return matchingId

    def calcTotalUncompleteTableCount(self, group):
        count = 0
        for areaStatus in self.masterStub.masterStatus.areaStatusMap.values():
            for groupStatus in areaStatus.groupStatusMap.values():
                if groupStatus.groupId == group.groupId:
                    count += group.calcUncompleteTableCount()
                elif groupStatus.matchingId == group.matchingId:
                    if self.parseStageId(group.matchingId, groupStatus.groupId) == self.parseStageId(group.matchingId,
                                                                                                     group.groupId):
                        count += groupStatus.uncompleteTableCount
        return count

    def calcTotalRemTimes(self, group):
        remTimes = 0
        for areaStatus in self.masterStub.masterStatus.areaStatusMap.values():
            for groupStatus in areaStatus.groupStatusMap.values():
                if groupStatus.matchingId == group.matchingId and groupStatus.remTimes > remTimes:
                    remTimes = groupStatus.remTimes
        return remTimes

    def getTotalSignerCount(self, inst):
        count = 0
        for areaStatus in self.masterStub.masterStatus.areaStatusMap.values():
            if areaStatus.instStatus and inst.instId == areaStatus.instStatus.instId:
                count += areaStatus.instStatus.signerCount
        return max(count, inst.signerCount)

    def buildStatus(self):
        ret = MatchAreaStatus()
        ret.timestamp = pktimestamp.getCurrentTimestamp()
        if self.curInst:
            ret.instStatus = self.curInst.buildStatus()
        for group in self._groupMap.values():
            status = group.buildStatus()
            status.timestamp = ret.timestamp
            ret.groupStatusMap[group.groupId] = status
        return ret

    def signin(self, userId, signinParams, feeIndex=0):
        '''
        玩家报名
        '''
        if not self._curInst:
            raise MatchStoppedException()

        if self.findPlayer(userId):
            raise AlreadyInMatchException()

        return self._curInst.signin(userId, feeIndex)

    def signout(self, userId):
        '''
        玩家退赛，转到主赛区处理
        '''
        if not self._curInst:
            raise MatchStoppedException()

        signer = self._curInst.findSigner(userId)
        if not signer:
            self._logger.warn('MatchArea.signout fail',
                              'state=', self._state,
                              'userId=', userId,
                              'err=', 'NotFoundPlayer')
            return None
        self._curInst.signout(signer)
        return signer

    def giveup(self, userId):
        '''
        玩家放弃比赛
        '''
        player = self.findPlayer(userId)
        if not player:
            self._logger.warn('MatchArea.giveup fail',
                              'state=', self._state,
                              'userId=', userId,
                              'err=', 'NotFoundPlayer')
            return False
        return player.group.giveup(player)

    def enter(self, userId):
        '''
        进入报名页
        '''
        if self._curInst:
            signer = self._curInst.findSigner(userId)
            if signer:
                self._curInst.enter(signer)

    def leave(self, userId):
        '''
        离开报名页
        '''
        if self._curInst:
            signer = self._curInst.findSigner(userId)
            if signer:
                self._curInst.leave(signer)

    def winlose(self, tableId, ccrc, seatId, userId, deltaScore, isWin):
        '''
        玩家一局结束
        '''
        player = self.findPlayer(userId)

        if self._logger.isDebug():
            self._logger.debug('MatchArea.winlose',
                               'state=', self._state,
                               'tableId=', tableId,
                               'ccrc=', ccrc,
                               'seatId=', seatId,
                               'userId=', userId,
                               'deltaScore=', deltaScore,
                               'isWin=', isWin)
        if not player:
            self._logger.error('MatchArea.winlose fail',
                               'state=', self._state,
                               'tableId=', tableId,
                               'ccrc=', ccrc,
                               'seatId=', seatId,
                               'userId=', userId,
                               'deltaScore=', deltaScore,
                               'isWin=', isWin,
                               'err=', 'NotFoundPlayer')
            return None

        if not player.group:
            self._logger.error('MatchArea.winlose fail',
                               'state=', self._state,
                               'tableId=', tableId,
                               'ccrc=', ccrc,
                               'seatId=', seatId,
                               'userId=', userId,
                               'deltaScore=', deltaScore,
                               'isWin=', isWin,
                               'err=', 'NoGroup')
            return None

        if player.state != Player.STATE_PLAYING:
            self._logger.error('MatchArea.winlose fail',
                               'state=', self._state,
                               'tableId=', tableId,
                               'ccrc=', ccrc,
                               'seatId=', seatId,
                               'userId=', userId,
                               'deltaScore=', deltaScore,
                               'isWin=', isWin,
                               'state=', player.state,
                               'expectState=', Player.STATE_PLAYING,
                               'err=', 'BadState')
            return None

        if not player.seat:
            self._logger.error('MatchArea.winlose fail',
                               'state=', self._state,
                               'tableId=', tableId,
                               'ccrc=', ccrc,
                               'seatId=', seatId,
                               'userId=', userId,
                               'deltaScore=', deltaScore,
                               'isWin=', isWin,
                               'err=', 'NotInSeat')
            return None

        if player.seat.table.tableId != tableId:
            self._logger.error('MatchArea.winlose fail',
                               'tableId=', tableId,
                               'ccrc=', ccrc,
                               'seatId=', seatId,
                               'userId=', userId,
                               'deltaScore=', deltaScore,
                               'isWin=', isWin,
                               'diffTableId=', player.table.tableId,
                               'err=', 'DiffTable')
            return None

        if player.seat.seatId != seatId:
            self._logger.error('MatchArea.winlose fail',
                               'state=', self._state,
                               'tableId=', tableId,
                               'ccrc=', ccrc,
                               'seatId=', seatId,
                               'userId=', userId,
                               'deltaScore=', deltaScore,
                               'isWin=', isWin,
                               'diffSeatId=', player.seat.seatId,
                               'err=', 'DiffSeat')
            return None

        if player.seat.table.ccrc != ccrc:
            self._logger.error('MatchArea.winlose fail',
                               'state=', self._state,
                               'tableId=', tableId,
                               'ccrc=', ccrc,
                               'seatId=', seatId,
                               'userId=', userId,
                               'deltaScore=', deltaScore,
                               'isWin=', isWin,
                               'diffCCRC=', player.seat.table.ccrc,
                               'err=', 'DiffCCRC')
            return None

        player.group.winlose(player, deltaScore, isWin, False)
        return player

    def createInst(self, instId, startTime, needLoad):
        self._logger.info('MatchArea.createInst ...',
                          'state=', self._state,
                          'instId=', instId,
                          'startTime=', startTime,
                          'needLoad=', needLoad,
                          'curInstId=', self._curInst.instId if self._curInst else None)
        if self._curInst and self._curInst.instId == instId:
            self._logger.error('MatchArea.createInst fail',
                               'state=', self._state,
                               'instId=', instId,
                               'startTime=', startTime,
                               'needLoad=', needLoad,
                               'curInstId=', self._curInst.instId if self._curInst else None,
                               'err=', 'AlreadyCreate')
            return

        self._curInst = MatchInst(self, instId, startTime, needLoad)
        self._curInst.load()
        self._logger.info('MatchArea.createInst ok',
                          'state=', self._state,
                          'startTime=', startTime,
                          'needLoad=', needLoad,
                          'instId=', instId)
        return self._curInst

    def cancelInst(self, instId, reason):
        self._logger.info('MatchArea.cancelInst ...',
                          'state=', self._state,
                          'instId=', instId,
                          'reason=', reason)
        inst = MatchInst(self, instId, None, True)
        inst.load()
        inst.cancel(reason)
        self._logger.info('MatchArea.cancelInst ok',
                          'state=', self._state,
                          'instId=', instId,
                          'reason=', reason)

    def createGroup(self, instId, matchingId, groupId,
                    groupName, stageIndex, isGrouping, totalPlayerCount):
        '''
        创建分组
        '''
        group = self.findGroup(groupId)
        if group:
            self._logger.error('MatchArea.createGroup fail',
                               'state=', self._state,
                               'instId=', instId,
                               'matchingId=', matchingId,
                               'groupId=', groupId,
                               'groupName=', groupName,
                               'stageIndex=', stageIndex,
                               'isGrouping=', isGrouping,
                               'totalPlayerCount=', totalPlayerCount,
                               'err=', 'GroupExists')
            raise BadStateException()

        group = MatchGroup(self, instId, matchingId, groupId, groupName, stageIndex, isGrouping, totalPlayerCount)
        self._groupMap[groupId] = group

        self._logger.info('MatchArea.createGroup ok',
                          'state=', self._state,
                          'instId=', instId,
                          'matchingId=', matchingId,
                          'groupId=', groupId,
                          'groupName=', groupName,
                          'stageIndex=', stageIndex,
                          'isGrouping=', isGrouping,
                          'totalPlayerCount=', totalPlayerCount)
        return group

    def onInstStarted(self, inst):
        self._logger.info('MatchArea.onInstStarted ...',
                          'state=', self._state,
                          'instId=', inst.instId,
                          'signerCount=', inst.signerCount)
        try:
            self.masterStub.areaInstStarted(self, inst)
            self._logger.info('MatchArea.onInstStarted ok',
                              'instId=', inst.instId,
                              'signerCount=', inst.signerCount)
        except:
            self._logger.error('MatchArea.onInstStarted fail',
                               'instId=', inst.instId,
                               'signerCount=', inst.signerCount)

    def onGroupFinish(self, group):
        self._logger.info('MatchArea.onGroupFinish',
                          'state=', self._state,
                          'groupId=', group.groupId,
                          'reason=', group.finishReason,
                          'riseUserIds=', [p.userId for p in group.rankList])
        try:
            self.masterStub.areaGroupFinish(self, group)
        except:
            self._logger.error('MatchArea.onGroupFinish fail',
                               'state=', self._state,
                               'groupId=', group.groupId,
                               'reason=', group.finishReason)

    def _processGroups(self):
        groups = list(self._groupMap.values())
        for group in groups:
            if group.state == MatchGroup.ST_FINAL:
                del self._groupMap[group.groupId]
                self._logger.info('MatchArea._processGroups removeGroup',
                                  'state=', self._state,
                                  'groupId=', group.groupId)

    def _doHeartbeatImpl(self):
        timestamp = pktimestamp.getCurrentTimestamp()
        if self._logger.isDebug():
            self._logger.debug('MatchArea._doHeartbeatImpl',
                               'state=', self._state,
                               'timestamp=', timestamp,
                               'lastHeartbeatToMasterTime=', self._lastHeartbeatToMasterTime)
        heartbeatInterval = 1 if self.matchConf.start.isUserCountType else MatchArea.HEARTBEAT_TO_MASTER_INTERVAL
        if not self._lastHeartbeatToMasterTime or timestamp - self._lastHeartbeatToMasterTime > heartbeatInterval:
            self._lastHeartbeatToMasterTime = timestamp
            try:
                self.masterStub.areaHeartbeat(self)
            except:
                self._logger.error('MatchArea._doHeartbeatImpl',
                                   'state=', self._state)
        self._processGroups()
        return 1


class MatchInstStub(object):
    '''
    比赛实例存根，运行于主控进程
    '''

    def __init__(self, areaStub, instId, startTime, needLoad):
        # 赛区
        self.areaStub = areaStub
        # 实例ID
        self.instId = instId
        # 启动时间
        self.startTime = startTime
        # 是否需要加载
        self.needLoad = needLoad
        # 状态
        self._state = MatchInst.ST_IDLE
        # 所有报名
        self._signerMap = {}
        # 完成原因
        self._finishReason = MatchFinishReason.FINISH
        # 日志
        self._logger = Logger()
        self._logger.add('matchId', self.areaStub.matchId)
        self._logger.add('roomId', self.areaStub.roomId)
        self._logger.add('instId', instId)

    @property
    def roomId(self):
        return self.areaStub.roomId

    @property
    def master(self):
        return self.areaStub.master

    @property
    def state(self):
        return self._state

    @property
    def signerMap(self):
        return self._signerMap

    @property
    def signerCount(self):
        return len(self._signerMap)

    @property
    def finishReason(self):
        return self._finishReason

    def startSignin(self):
        '''
        开始报名
        '''
        self._logger.info('MatchInstStub.startSignin ...',
                          'state=', self._state)
        self._state = MatchInst.ST_SIGNIN
        try:
            self._doStartSignin()
            self._logger.info('MatchInstStub.startSignin ok',
                              'state=', self._state)
        except:
            self._logger.error('MatchInstStub.startSignin fail',
                               'state=', self._state)

    def prepare(self):
        '''
        开始准备开赛
        '''
        self._logger.info('MatchInstStub.prepare ...',
                          'state=', self._state)
        self._state = MatchInst.ST_PREPARE
        try:
            self._doPrepare()
            self._logger.info('MatchInstStub.prepare ok',
                              'state=', self._state)
        except:
            self._logger.info('MatchInstStub.prepare fail',
                              'state=', self._state)

    def cancel(self, reason):
        '''
        取消比赛
        '''
        assert (reason != MatchFinishReason.FINISH)
        self._logger.info('MatchInstStub.cancel ...',
                          'state=', self._state,
                          'reason=', reason)
        self._state = MatchInst.ST_FINAL
        self._finishReason = reason
        self._signerMap = {}
        try:
            self._doCancel()
            self._logger.info('MatchInstStub.cancel ok',
                              'state=', self._state,
                              'reason=', reason)
        except:
            self._logger.error('MatchInstStub.cancel fail',
                               'state=', self._state,
                               'reason=', reason)

    def cancelSigners(self, reason, signers):
        '''
        取消比赛
        '''
        assert (reason != MatchFinishReason.FINISH)
        self._logger.info('MatchInstStub.cancelSigners ...',
                          'state=', self._state,
                          'reason=', reason,
                          'signerCount=', len(signers))
        userIds = []
        for signer in signers:
            s = self._signerMap.get(signer.userId)
            if s:
                self._signerMap[signer.userId]
                userIds.append(signer.userId)
        try:
            self._doCancelSigners(reason, userIds)
            self._logger.info('MatchInstStub.cancelSigners ok',
                              'state=', self._state,
                              'reason=', reason,
                              'signerCount=', len(signers))
        except:
            self._logger.info('MatchInstStub.cancelSigners fail',
                              'state=', self._state,
                              'reason=', reason,
                              'signerCount=', len(signers))

    def moveTo(self, toInstId, signers):
        self._logger.info('MatchInstStub.moveTo ...',
                          'state=', self._state,
                          'toInstId=', toInstId,
                          'signersCount=', len(signers))
        userIds = []
        for signer in signers:
            s = self._signerMap.get(signer.userId)
            if s:
                self._signerMap[signer.userId]
                userIds.append(signer.userId)
        self._doMoveTo(toInstId, userIds)
        self._logger.info('MatchInstStub.moveTo ok',
                          'state=', self._state,
                          'toInstId=', toInstId,
                          'signersCount=', len(signers))

    def start(self):
        '''
        开始比赛
        '''
        self._logger.info('MatchInstStub.start ...',
                          'state=', self._state)
        self._state = MatchInst.ST_STARTING
        try:
            self._doStart()
            self._logger.info('MatchInstStub.start ok',
                              'state=', self._state)
        except:
            self._logger.error('MatchInstStub.start fail',
                               'state=', self._state)

    def onSignin(self, signers):
        '''
        主对象汇报报名列表
        '''
        if (self._state >= MatchInst.ST_SIGNIN
            and self._state < MatchInst.ST_START):
            self._logger.info('MatchInstStub.onSignin ...',
                              'state=', self._state,
                              'signerCount=', len(signers))
            if self._logger.isDebug():
                self._logger.debug('MatchInstStub.onSignin ...',
                                   'state=', self._state,
                                   'signers=', [(s.userId, s.userName) for s in signers])
            for signer in signers:
                self._signerMap[signer.userId] = signer
            self._logger.info('MatchInstStub.onSignin ok',
                              'state=', self._state,
                              'signerCount=', len(signers))
        else:
            self._logger.error('MatchInstStub.onSignin fail',
                               'state=', self._state,
                               'err=', 'BadState')

    def onStart(self):
        '''
        赛区中的实例启动完成
        '''
        if self._state == MatchInst.ST_STARTING:
            self._state = MatchInst.ST_START
            self._logger.info('MatchInstStub.onStart ok',
                              'state=', self._state)
        else:
            self._logger.error('MatchInstStub.onStart fail',
                               'state=', self._state,
                               'err=', 'BadState')

    def _doCancelSigners(self, reason, userIds):
        raise NotImplementedError

    def _doMoveTo(self, toInstId, userIds):
        raise NotImplementedError

    def _doStartSignin(self):
        raise NotImplementedError

    def _doPrepare(self):
        raise NotImplementedError

    def _doCancel(self):
        raise NotImplementedError

    def _doStart(self):
        raise NotImplementedError


class MatchInstStubLocal(MatchInstStub):
    def __init__(self, areaStub, instId, startTime, needLoad, inst):
        super(MatchInstStubLocal, self).__init__(areaStub, instId, startTime, needLoad)
        self.inst = inst

    def _doCancelSigners(self, reason, userIds):
        try:
            self.inst.cancelSigners(reason, userIds)
        except:
            self._logger.error('MatchInstStubLocal._doMoveTo fail',
                               'reason=', reason,
                               'userIds=', userIds)

    def _doMoveTo(self, toInstId, userIds):
        try:
            self.inst.moveTo(toInstId, userIds)
        except:
            self._logger.error('MatchInstStubLocal._doMoveTo fail',
                               'toInstId=', toInstId,
                               'userIds=', userIds)

    def _doStartSignin(self):
        try:
            self.inst.startSignin()
        except:
            self._logger.error('MatchInstStubLocal._doStartSignin fail')

    def _doPrepare(self):
        try:
            self.inst.prepare()
        except:
            self._logger.error('MatchInstStubLocal._doPrepare fail')

    def _doCancel(self):
        try:
            self.inst.cancel(self._finishReason)
        except:
            self._logger.error('MatchInstStubLocal._doCancel fail')

    def _doStart(self):
        try:
            self.inst.start()
        except:
            self._logger.error('MatchInstStubLocal._doStart fail')


class MatchGroupStub(HeartbeatAble):
    '''
    比赛分组存根对象，运行于主控进程
    '''
    HEARTBEAT_INTERVAL = 1

    ACTIVE_TIME_COUNT = 36

    def __init__(self, areaStub, stage, groupId,
                 groupName, playerList, isGrouping, totalPlayerCount):
        super(MatchGroupStub, self).__init__()
        # 赛区控制对象
        self.areaStub = areaStub
        # 当前阶段
        self.stage = stage
        # 分组ID
        self.groupId = groupId
        # 分组名称
        self.groupName = groupName
        # 是否分组
        self.isGrouping = isGrouping
        # 开赛总人数
        self.totalPlayerCount = totalPlayerCount
        # 玩家map
        self._playerMap = {p.userId: p for p in playerList}
        # 晋级的玩家
        self._risePlayerSet = set()
        # 状态
        self._state = MatchGroup.ST_IDLE
        # 日志
        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('matchingId', self.matchingId)
        self._logger.add('roomId', self.roomId)
        self._logger.add('stageIndex', self.stageIndex)
        self._logger.add('groupId', self.groupId)
        # 完成原因
        self._finishReason = MatchFinishReason.FINISH
        # 开始时间
        self._startTime = None
        # group状态
        self._status = None
        # 最后心跳时间
        self._lastGroupHeartbeatTime = None

    @property
    def instId(self):
        return self.stage.instId

    @property
    def roomId(self):
        return self.areaStub.roomId

    @property
    def master(self):
        return self.areaStub.master

    @property
    def playerMap(self):
        return self._playerMap

    @property
    def playerCount(self):
        return len(self._playerMap)

    @property
    def matchId(self):
        return self.stage.matchId

    @property
    def matchingId(self):
        return self.stage.matchingId

    @property
    def stageIndex(self):
        return self.stage.stageIndex

    @property
    def risePlayerSet(self):
        return self._risePlayerSet

    @property
    def finishReason(self):
        return self._finishReason

    @property
    def state(self):
        return self._state

    def buildStatus(self):
        return self._status

    def start(self):
        assert (self._state == MatchGroup.ST_IDLE)
        self._state = MatchGroup.ST_SETUP
        self._startTime = pktimestamp.getCurrentTimestamp()
        self._lastGroupHeartbeatTime = self._startTime
        self._logger.info('MatchGroupStub.start ...',
                          'state=', self._state)
        self._startHeartbeat()
        self._logger.info('MatchGroupStub.start ok',
                          'state=', self._state)

    def kill(self, reason):
        assert (reason != MatchFinishReason.FINISH)
        self._logger.info('MatchGroupStub.kill ...',
                          'state=', self._state)
        self.postCall(self._doKill, reason)
        self._logger.info('MatchGroupStub.kill ok',
                          'state=', self._state)

    def final(self):
        assert (self._state < MatchGroup.ST_FINAL)
        self._logger.info('MatchGroupStub.final ...',
                          'state=', self._state)
        self.postCall(self._doFinal)
        self._logger.info('MatchGroupStub.final ok',
                          'state=', self._state)

    def onRise(self, risers):
        if self._logger.isDebug():
            self._logger.debug('MatchGroupStub.onRise',
                               'state=', self._state,
                               'riseCount=', len(risers),
                               'riseUserIds=', [(riser.userId, riser.score, riser.rank) for riser in risers])

        self._logger.info('MatchGroupStub.onRise ...',
                          'state=', self._state,
                          'riseCount=', len(risers))

        riseOkCount = 0
        for riser in risers:
            player = self._playerMap.get(riser.userId)
            if player:
                player.updateByRiser(riser)
                self._risePlayerSet.add(player)
                riseOkCount += 1
            else:
                self._logger.warn('MatchGroupStub.onRise',
                                  'state=', self._state,
                                  'userId=', riser.userId,
                                  'score=', riser.score,
                                  'rank=', riser.rank,
                                  'err=', 'NotFoundPlayer')
        self._logger.info('MatchGroupStub.onRise ok',
                          'state=', self._state,
                          'riseCount=', len(risers),
                          'riseOkCount=', riseOkCount)

    def onFinish(self, reason):
        self._logger.info('MatchGroupStub.onFinish',
                          'state=', self._state,
                          'reason=', reason,
                          'riseCount=', len(self._risePlayerSet))
        self.postCall(self._doFinish, reason)

    def onStart(self):
        self._logger.info('MatchGroupStub.onStart',
                          'state=', self._state)
        self.postCall(self._doStartOk)

    def onHeartbeat(self, status):
        self._logger.info('MatchGroupStub.onHeartbeat',
                          'state=', self._state,
                          'groupTimestamp=', status.timestamp,
                          'lastActiveTime=', status.lastActiveTime)
        self._lastGroupHeartbeatTime = pktimestamp.getCurrentTimestamp()
        self._status = status

    def _doStart(self):
        assert (self._state == MatchGroup.ST_SETUP)
        self._logger.info('MatchGroupStub._doStart ...',
                          'state=', self._state,
                          'userCount=', len(self._playerMap))
        self._state = MatchGroup.ST_START
        try:
            self._doStartGroup()
            self._logger.info('MatchGroupStub._doStart ok',
                              'state=', self._state,
                              'userCount=', len(self._playerMap))
        except:
            self._logger.error('MatchGroupStub._doStart fail',
                               'state=', self._state,
                               'userCount=', len(self._playerMap))

    def _doKill(self, reason):
        self._logger.info('MatchGroupStub._doKill ...',
                          'state=', self._state,
                          'reason=', reason)
        if self._state < MatchGroup.ST_FINISHING:
            self._state = MatchGroup.ST_FINISH
            self._finishReason = reason

            bireport.matchGroupFinish(self.master.gameId, self.master.roomId, self.matchId, self.master.matchName,
                                      areaRoomId=self.roomId,
                                      instId=self.instId,
                                      matchingId=self.matchingId,
                                      stageIndex=self.stageIndex,
                                      groupId=self.groupId,
                                      reason=reason,
                                      isKill=True)

            if self._status:
                self._status.uncompleteTableCount = 0
                self._status.remTimes = 0
                self._status.state = MatchGroup.ST_FINISH

            try:
                self._doKillGroup()
                self._logger.info('MatchGroupStub._doKill ok',
                                  'state=', self._state,
                                  'reason=', reason)
            except:
                self._logger.error('MatchGroupStub._doKill fail',
                                   'state=', self._state,
                                   'reason=', reason)
        else:
            self._logger.error('MatchGroupStub._doKill fail',
                               'state=', self._state,
                               'reason=', reason,
                               'err=', 'BadState')

    def _doFinal(self):
        self._logger.info('MatchGroupStub._doFinal ...',
                          'state=', self._state)
        if self._state == MatchGroup.ST_FINISH:
            self._state = MatchGroup.ST_FINALING
            self._stopHeartbeat()
            self._state = MatchGroup.ST_FINAL
            try:
                self._doFinalGroup()
                self._logger.info('MatchGroupStub._doFinal ok',
                                  'state=', self._state)
            except:
                self._logger.error('MatchGroupStub._doFinal fail',
                                   'state=', self._state)
        else:
            self._logger.error('MatchGroupStub._doFinal fail',
                               'state=', self._state,
                               'err=', 'BadState')

    def _doFinish(self, reason):
        self._logger.info('MatchGroupStub._doFinish ...',
                          'state=', self._state,
                          'reason=', reason)
        if self._state <= MatchGroup.ST_FINISHING:
            self._state = MatchGroup.ST_FINISH
            self._finishReason = reason
            bireport.matchGroupFinish(self.master.gameId, self.master.roomId,
                                      self.matchId, self.master.matchName,
                                      areaRoomId=self.roomId,
                                      instId=self.instId,
                                      matchingId=self.matchingId,
                                      stageIndex=self.stageIndex,
                                      groupId=self.groupId,
                                      reason=reason,
                                      isKill=False)
            self._logger.info('MatchGroupStub._doFinish ok',
                              'state=', self._state,
                              'reason=', reason)
        else:
            self._logger.error('MatchGroupStub._doFinish fail',
                               'state=', self._state,
                               'reason=', reason,
                               'err=', 'BadState')

    def _doHeartbeatImpl(self):
        if self._logger.isDebug():
            self._logger.info('MatchGroupStub._doHeartbeatImpl',
                              'state=', self._state)

        if self._state == MatchGroup.ST_SETUP:
            self._doStart()

        if self._state < MatchGroup.ST_FINISHING:
            if self._isActiveTimeout():
                self._logger.info('MatchGroupStub._doHeartbeatImpl activeTimeout',
                                  'state=', self._state)
                try:
                    self._doKill(MatchFinishReason.OVERTIME)
                except:
                    self._logger.error('MatchGroupStub._doHeartbeatImpl killFail',
                                       'state=', self._state)
        return 1

    def _isActiveTimeout(self):
        delta = max(0, pktimestamp.getCurrentTimestamp() - self._lastGroupHeartbeatTime)
        if self._status and self._status.lastActiveTime:
            delta += max(0, self._status.timestamp - self._status.lastActiveTime)
        if self._logger.isDebug():
            self._logger.debug('MatchGroupStub._isActiveTimeout',
                               'lastGroupHeartbeatTime=', self._lastGroupHeartbeatTime,
                               'lastActiveTime=', self._status.lastActiveTime if self._status else None,
                               'delta=', delta,
                               'limit=', MatchArea.HEARTBEAT_TO_MASTER_INTERVAL * MatchGroupStub.ACTIVE_TIME_COUNT)
        return delta >= MatchArea.HEARTBEAT_TO_MASTER_INTERVAL * MatchGroupStub.ACTIVE_TIME_COUNT

    def _doStartGroup(self):
        raise NotImplemented()

    def _doKillGroup(self):
        raise NotImplemented()

    def _doFinalGroup(self):
        raise NotImplemented()


class MatchGroupStubLocal(MatchGroupStub):
    '''
    比赛分组存根对象，运行于主控进程
    '''

    def __init__(self, areaStub, stage, groupId,
                 groupName, playerList, isGrouping, totalPlayerCount, area):
        super(MatchGroupStubLocal, self).__init__(areaStub, stage, groupId,
                                                  groupName, playerList, isGrouping, totalPlayerCount)
        self.area = area

    def _doStartGroup(self):
        group = self.area.createGroup(self.instId, self.matchingId, self.groupId,
                                      self.groupName, self.stageIndex, self.isGrouping,
                                      self.totalPlayerCount)
        for player in self._playerMap.values():
            group.addPlayer(player)

        group.start()

    def _doKillGroup(self):
        group = self.area.findGroup(self.groupId)
        if group:
            group.kill(self.finishReason)

    def _doFinalGroup(self):
        group = self.area.findGroup(self.groupId)
        if group:
            group.final()


class GroupCreateInfo(object):
    def __init__(self, stage, groupId, groupName, playerList):
        self.stage = stage
        self.groupId = groupId
        self.groupName = groupName
        self.playerList = playerList


class MatchStage(object):
    '''
    比赛阶段，运行于中控进程
    '''
    ST_IDLE = 0
    ST_START = 1
    ST_FINISH = 2
    ST_FINAL = 3

    GROUP_NAME_PREFIX = [chr(i) for i in range(ord('A'), ord('Z') + 1)]

    def __init__(self, matching, stageConf):
        # 哪场比赛
        self.matching = matching
        # 阶段index
        self.stageIndex = stageConf.index
        # 阶段配置
        self.stageConf = stageConf
        # 分组控制map, key=groupId, value=MatchGroupCtrl
        self._groupStubMap = {}
        # 状态
        self._state = MatchStage.ST_IDLE
        # 日志
        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('instId', self.instId)
        self._logger.add('matchingId', self.matchingId)
        self._logger.add('stageIndex', self.stageIndex)

    @property
    def matchId(self):
        return self.matching.matchId

    @property
    def instId(self):
        return self.matching.instId

    @property
    def matchingId(self):
        return self.matching.matchingId

    @property
    def master(self):
        return self.matching.master

    @property
    def matchConf(self):
        return self.matching.matchConf

    @property
    def state(self):
        return self._state

    def findGroupStub(self, groupId):
        return self._groupStubMap.get(groupId)

    def start(self, playerList):
        assert (self._state == MatchStage.ST_IDLE)
        self._state = MatchStage.ST_START
        self._logger.info('MatchStage.start ...',
                          'state=', self._state,
                          'playerCount=', len(playerList))
        TYGame(self.master.gameId).getEventBus().publishEvent(
            MatchingStageStartEvent(self.master.gameId, self.instId, self.matchingId, self.stageIndex))
        isGrouping, groupPlayerLists = self.groupingPlayerList(playerList, self.stageConf,
                                                               self.matchConf.tableSeatCount)
        groupCreateInfos = []
        for i, groupPlayerList in enumerate(groupPlayerLists):
            groupId = '%s.%s.%s' % (self.matchingId, self.stageIndex, i + 1)
            groupName = GroupNameGenerator.generateGroupName(len(groupPlayerLists), i)
            groupCreateInfos.append(GroupCreateInfo(self, groupId, groupName, groupPlayerList))
        # 创建GroupStub
        groupStubs = self.master.createGroupStubs(self, groupCreateInfos, isGrouping)
        self._groupStubMap = {g.groupId: g for g in groupStubs}

        bireport.matchStageStart(self.master.gameId, self.master.roomId,
                                 self.matchId, self.master.matchName,
                                 instId=self.instId,
                                 matchingId=self.matchingId,
                                 stageIndex=self.stageIndex,
                                 isGrouping=isGrouping,
                                 userCount=len(playerList),
                                 groupCount=len(self._groupStubMap),
                                 groupInfos=[(g.groupId, g.groupName, g.roomId, len(g.playerMap)) for g in
                                             self._groupStubMap.values()])

        for groupStub in self._groupStubMap.values():
            # 启动分组
            groupStub.start()

            bireport.matchGroupStart(self.master.gameId, self.master.roomId,
                                     self.matchId, self.master.matchName,
                                     areaRoomId=groupStub.roomId,
                                     instId=self.instId,
                                     matchingId=self.matchingId,
                                     stageIndex=self.stageIndex,
                                     isGrouping=isGrouping,
                                     groupId=groupStub.groupId,
                                     userCount=len(groupStub.playerMap),
                                     userIds=groupStub.playerMap.keys())

        self._logger.info('MatchStage.start ok',
                          'state=', self._state,
                          'isGrouping=', isGrouping,
                          'groupInfos=',
                          [(g.groupId, g.groupName, g.roomId, len(g.playerMap)) for g in self._groupStubMap.values()],
                          'groupCount=', len(self._groupStubMap),
                          'playerCount=', len(playerList))

    def final(self):
        assert (self._state == MatchStage.ST_FINISH)
        self._logger.info('MatchStage.final ...',
                          'state=', self._state)

        for groupStub in self._groupStubMap.values():
            groupStub.final()

        bireport.matchStageFinish(self.master.gameId, self.master.roomId,
                                  self.matchId, self.master.matchName,
                                  instId=self.instId,
                                  matchingId=self.matchingId,
                                  stageIndex=self.stageIndex)

        TYGame(self.master.gameId).getEventBus().publishEvent(
            MatchingStageFinishEvent(self.master.gameId, self.instId, self.matchingId, self.stageIndex))

        self._logger.info('MatchStage.final ok',
                          'state=', self._state)

    def getAllRisePlayerList(self):
        playerMap = {}
        for groupStub in self._groupStubMap.values():
            for player in groupStub.risePlayerSet:
                playerMap[player.userId] = player
        return playerMap.values()

    @classmethod
    def groupingPlayerList(self, playerList, stageConf, tableSeatCount):
        groupPlayersList = None
        isGrouping = True
        if stageConf.groupingType == GroupingType.TYPE_GROUP_COUNT:
            groupPlayersList = PlayerGrouping.groupingByGroupCount(playerList, stageConf.groupingGroupCount,
                                                                   tableSeatCount)
        elif stageConf.groupingType == GroupingType.TYPE_USER_COUNT:
            groupPlayersList = PlayerGrouping.groupingByMaxUserCountPerGroup(playerList, stageConf.groupingUserCount,
                                                                             tableSeatCount)
        else:
            groupPlayersList = [playerList[:]]
            isGrouping = False
        return isGrouping, groupPlayersList

    def _processStage(self):
        if self._logger.isDebug():
            self._logger.debug('MatchStage._processStage',
                               'state=', self._state)

        if self._state == MatchStage.ST_START:
            if self._isAllGroupStubFinish():
                self._state = MatchStage.ST_FINISH

    def _isAllGroupStubFinish(self):
        for groupStub in self._groupStubMap.values():
            if groupStub.state < MatchGroup.ST_FINISH:
                return False
        return True


class Matching(HeartbeatAble):
    '''
    一场比赛，运行于主控进程
    '''
    ST_IDLE = 0
    ST_START = 1
    ST_FINISH = 2

    HEARTBEAT_INTERVAL = 2

    def __init__(self, master, instId, matchingId):
        super(Matching, self).__init__()
        # 赛事
        self.master = master
        # 实例ID
        self.instId = instId
        # 比赛ID
        self.matchingId = matchingId
        # 所有阶段
        self._stages = self._createStages(master.matchConf.stages)
        # 当前阶段
        self._stage = self._stages[0]
        # 状态
        self._state = Matching.ST_IDLE
        # 开赛时的人数
        self._startPlayerCount = 0
        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('instId', self.instId)
        self._logger.add('matchingId', self.matchingId)

    @property
    def matchId(self):
        return self.master.matchId

    @property
    def matchConf(self):
        return self.master.matchConf

    @property
    def state(self):
        return self._state

    @property
    def startPlayerCount(self):
        return self._startPlayerCount

    def findGroupStub(self, groupId):
        if self._stage:
            return self._stage.findGroupStub(groupId)
        return None

    def findFirstStage(self, signerCount):
        if self.matchConf.start.selectFirstStage:
            for stage in self._stages:
                if signerCount > stage.stageConf.riseUserCount:
                    return stage
        return self._stages[0]

    def start(self, signers):
        assert (self._state == Matching.ST_IDLE)
        self._state = Matching.ST_START
        self._stage = self.findFirstStage(len(signers))
        self._logger.info('Matching.start ...',
                          'state=', self._state,
                          'userCount=', len(signers),
                          'firstStageIndex=', self._stage.stageIndex)
        TYGame(self.master.gameId).getEventBus().publishEvent(
            MatchingStartEvent(self.master.gameId, self.instId, self.matchingId))
        bireport.matchStart(self.master.gameId, self.master.roomId,
                            self.matchId, self.master.matchName,
                            instId=self.instId,
                            matchingId=self.matchingId,
                            userCount=len(signers))
        playerList = self._signersToPlayerList(signers)
        self._startPlayerCount = len(playerList)
        self._stage.start(playerList)
        self._startHeartbeat()
        self._logger.info('Matching.start ok',
                          'state=', self._state,
                          'userCount=', len(signers),
                          'firstStageIndex=', self._stage.stageIndex)

    def _doHeartbeatImpl(self):
        if self._logger.isDebug():
            self._logger.debug('Matching._doHeartbeatImpl',
                               'state=', self._state,
                               'stageIndex=', self._stage.stageIndex if self._stage else None)
        if self._stage and self._state == Matching.ST_START:
            self._stage._processStage()
        if self._stage and self._stage.state == MatchStage.ST_FINISH:
            self._startNextStage()
        return Matching.HEARTBEAT_INTERVAL

    def _startNextStage(self):
        playerList = self._stage.getAllRisePlayerList()
        nextStage = self._getNextStage(self._stage)
        self._logger.info('Matching._startNextStage',
                          'state=', self._state,
                          'stageIndex=', self._stage.stageIndex,
                          'nextStageIndex=', nextStage.stageIndex if nextStage else None,
                          'nextStageState=', nextStage.state if nextStage else None,
                          'playerCount=', len(playerList))
        self._stage.final()
        if nextStage:
            self._stage = nextStage
            self._stage.start(playerList)
        else:
            self._doFinish()

    def _getNextStage(self, stage):
        nextStageIndex = stage.stageIndex + 1
        if nextStageIndex < len(self._stages):
            return self._stages[nextStageIndex]
        return None

    def _createStages(self, stageConfs):
        ret = []
        for stageConf in stageConfs:
            stage = MatchStage(self, stageConf)
            ret.append(stage)
        return ret

    def _signersToPlayerList(self, signers):
        ret = []
        for signer in signers:
            player = Player(signer.userId, signer.instId, signer.signinTime)
            player.clientId = signer.clientId
            player.userName = signer.userName
            ret.append(player)
        return ret

    def _doFinish(self):
        self._state = Matching.ST_FINISH
        self._logger.info('Matching._doFinish ...',
                          'state=', self._state)
        self._stopHeartbeat()
        self._logger.info('Matching._doFinish ok',
                          'state=', self._state)

        bireport.matchFinish(self.master.gameId, self.master.roomId,
                             self.matchId, self.master.matchName,
                             instId=self.instId,
                             matchingId=self.matchingId)
        TYGame(self.master.gameId).getEventBus().publishEvent(
            MatchingFinishEvent(self.master.gameId, self.instId, self.matchingId))


class MatchAreaStub(HeartbeatAble):
    '''
    赛区存根对象，用于控制分赛区，运行于主控进程
    '''
    ST_OFFLINE = 0
    ST_ONLINE = 1
    ST_TIMEOUT = 2

    HEARTBEAT_TIMEOUT_TIMES = 3

    def __init__(self, master, roomId):
        super(MatchAreaStub, self).__init__()
        # 比赛主控对象
        self.master = master
        # 赛区roomId
        self.roomId = roomId
        # 状态
        self.areaStatus = None
        # 分赛区比赛实例控制对象
        self._curInstStub = None
        # 分赛区分组比赛控制对象map, key=groupId, value=MatchGroupCtrl
        self._groupStubMap = {}
        # 最后心跳时间
        self._lastHeartbeatTime = None
        # 启动时间
        self._startTime = None
        # 在线状态
        self._onlineState = MatchAreaStub.ST_OFFLINE
        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('roomId', self.roomId)

    @property
    def matchId(self):
        return self.master.matchId

    @property
    def matchConf(self):
        return self.master.matchConf

    @property
    def curInstStub(self):
        return self._curInstStub

    @property
    def groupStubMap(self):
        return self._groupStubMap

    def findInstStub(self, instId):
        if self._curInstStub and self._curInstStub.instId == instId:
            return self._curInstStub
        return None

    def findGroupStub(self, groupId):
        return self._groupStubMap.get(groupId)

    def isOnline(self):
        '''
        是否上线了
        '''
        return self._lastHeartbeatTime is not None

    def buildStatus(self):
        ret = MatchAreaStatus()
        if self.areaStatus:
            ret.instStatus = self.areaStatus.instStatus
            ret.timestamp = self.areaStatus.timestamp
        for groupStub in self._groupStubMap.values():
            groupStatus = groupStub.buildStatus()
            if groupStatus:
                ret.groupStatusMap[groupStub.groupId] = groupStatus
        return ret

    def start(self):
        self._startHeartbeat()

    def createInst(self, instId, startTime, needLoad):
        '''
        让分赛区创建比赛实例
        '''
        self._curInstStub = self._createInstStubImpl(instId, startTime, needLoad)

    def createGroup(self, stage, groupId, groupName, playerList, isGrouping, totalPlayerCount):
        self._logger.info('MatchAreaStub.createGroup ...',
                          'instId=', stage.instId,
                          'matchingId=', stage.matchingId,
                          'groupId=', groupId,
                          'groupName=', groupName,
                          'stageIndex=', stage.stageIndex,
                          'userCount=', len(playerList),
                          'isGrouping=', isGrouping,
                          'totalPlayerCount=', totalPlayerCount)
        groupStub = self._createGroupStubImpl(stage, groupId, groupName, playerList, isGrouping, totalPlayerCount)
        if groupStub:
            self._groupStubMap[groupId] = groupStub
            self._logger.info('MatchAreaStub.createGroup ok',
                              'instId=', stage.instId,
                              'matchingId=', stage.matchingId,
                              'groupId=', groupId,
                              'groupName=', groupName,
                              'stageIndex=', stage.stageIndex,
                              'userCount=', len(playerList),
                              'isGrouping=', isGrouping,
                              'totalPlayerCount=', totalPlayerCount)
        else:
            self._logger.error('MatchAreaStub.createGroup fail',
                               'instId=', stage.instId,
                               'matchingId=', stage.matchingId,
                               'groupId=', groupId,
                               'groupName=', groupName,
                               'stageIndex=', stage.stageIndex,
                               'userCount=', len(playerList),
                               'isGrouping=', isGrouping,
                               'totalPlayerCount=', totalPlayerCount)
        return groupStub

    def cancelInst(self, instId, reason):
        '''
        分赛区取消比赛实例
        '''
        raise NotImplemented()

    def masterHeartbeat(self, master):
        '''
        向分赛区发送，主赛区心跳
        '''
        raise NotImplemented()

    def onAreaHeartbeat(self, areaStatus):
        '''
        area心跳回调
        '''
        assert (isinstance(areaStatus, MatchAreaStatus))
        if self._logger.isDebug():
            self._logger.debug('MatchAreaStub.onAreaHeartbeat',
                               'curInstId=', self._curInstStub.instId if self._curInstStub else None,
                               'groupIds=', self._groupStubMap.keys())

        self._lastHeartbeatTime = pktimestamp.getCurrentTimestamp()
        self.areaStatus = areaStatus
        # 把心跳分发给各个groupStub
        for groupStatus in self.areaStatus.groupStatusMap.values():
            groupStub = self.findGroupStub(groupStatus.groupId)
            if groupStub:
                groupStub.onHeartbeat(groupStatus)

    def _doHeartbeatImpl(self):
        if self._logger.isDebug():
            self._logger.debug('MatchAreaStub._doHeartbeatImpl',
                               'curInstId=', self._curInstStub.instId if self._curInstStub else None,
                               'groupIds=', self._groupStubMap.keys())

        self._processGroupStubs()
        return 1

    def _processGroupStubs(self):
        groupStubs = list(self._groupStubMap.values())
        for groupStub in groupStubs:
            if groupStub.state == MatchGroup.ST_FINAL:
                del self._groupStubMap[groupStub.groupId]
                self._logger.info('MatchAreaStub._processGroupStubs removeGroupStub',
                                  'groupId=', groupStub.groupId)

    def _createInstStubImpl(self, instId, startTime, needLoad):
        raise NotImplemented()

    def _createGroupStubImpl(self, stage, groupId, groupName, playerList, isGrouping, totalPlayerCount):
        raise NotImplemented()


class MatchAreaStubLocal(MatchAreaStub):
    def __init__(self, master, area):
        super(MatchAreaStubLocal, self).__init__(master, area.roomId)
        self.area = area

    def masterHeartbeat(self, master):
        '''
        向分赛区发送，主赛区心跳
        '''
        self.area.masterStub.onMasterHeartbeat(master.buildStatus())

    def cancelInst(self, instId, reason):
        '''
        分赛区取消比赛实例
        '''
        self.area.cancelInst(instId, reason)

    def _createInstStubImpl(self, instId, startTime, needLoad):
        try:
            inst = self.area.createInst(instId, startTime, needLoad)
        except:
            self._logger.error('MatchAreaStubLocal._createInstStubImpl',
                               'instId=', instId,
                               'startTime=', startTime,
                               'needLoad=', needLoad)
        return MatchInstStubLocal(self, instId, startTime, needLoad, inst)

    def _createGroupStubImpl(self, stage, groupId, groupName, playerList, isGrouping, totalPlayerCount):
        return MatchGroupStubLocal(self, stage, groupId, groupName, playerList, isGrouping, totalPlayerCount, self.area)


class MatchMasterStubLocal(MatchMasterStub):
    '''
    赛事在赛区控制对象，运行于赛区中
    '''

    def __init__(self, master):
        super(MatchMasterStubLocal, self).__init__(master.roomId)
        self.master = master

    def areaHeartbeat(self, area):
        '''
        area心跳，运行
        '''
        self._logger.info('MatchMasterStubLocal.areaHeartbeat'
                          'area=', area.roomId)
        areaStub = self.master.findAreaStub(area.roomId)
        areaStub.onAreaHeartbeat(area.buildStatus())

    def areaGroupStart(self, area, group):
        '''
        向主赛区汇报
        '''
        self._logger.info('MatchMasterStubLocal.areaGroupStart'
                          'area=', area.roomId,
                          'groupId=', group.groupId)
        groupStub = self.master.findGroupStubWithMatchingId(group.matchingId, group.groupId)
        groupStub.onStart()

    def areaGroupFinish(self, area, group):
        '''
        向主赛区汇报
        '''
        self._logger.info('MatchMasterStubLocal.areaGroupFinish',
                          'area=', area.roomId,
                          'groupId=', group.groupId)
        groupStub = self.master.findGroupStubWithMatchingId(group.matchingId, group.groupId)
        if group.finishReason == MatchFinishReason.FINISH:
            risers = []
            for player in group.rankList:
                risers.append(Riser.fromPlayer(player))
            groupStub.onRise(risers)
        groupStub.onFinish(group.finishReason)

    def areaInstStarted(self, area, inst):
        '''
        向主赛区汇报比赛实例启动成功，汇报报名用户列表
        '''
        self._logger.info('MatchMasterStubLocal.areaInstStarted'
                          'area=', area.roomId,
                          'instId=', inst.instId)
        instStub = self.master.findInstStub(area.roomId, inst.instId)
        instStub.onSignin(inst.signerMap.values())
        instStub.onStart()


class MatchInstCtrl(HeartbeatAble):
    STARTING_TIMEOUT = 90

    def __init__(self, master, status, needLoad):
        super(MatchInstCtrl, self).__init__()
        self.master = master
        self.status = status
        self.prepareTime = None
        self.signinTime = None
        self.needLoad = needLoad
        if status.startTime:
            self.prepareTime = master.matchConf.start.calcPrepareTime(status.startTime)
            self.signinTime = master.matchConf.start.calcSigninTime(status.startTime)

        self._state = MatchInst.ST_IDLE
        self._startingTime = None

        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('instId', self.instId)
        self._logger.add('startTime', self.startTime)
        self._logger.add('signinTime', self.signinTime)

    @property
    def matchId(self):
        return self.master.matchId

    @property
    def state(self):
        return self._state

    @property
    def matchConf(self):
        return self.master.matchConf

    @property
    def instId(self):
        return self.status.instId

    @property
    def startTime(self):
        return self.status.startTime

    def start(self):
        assert (self._state == MatchInst.ST_IDLE)
        self._logger.info('MatchInstCtrl.Start ...',
                          'state=', self._state)
        self._startHeartbeat()
        self._logger.info('MatchInstCtrl.Start ok',
                          'state=', self._state)

    def final(self):
        assert (self._state == MatchInst.ST_STARTED)
        self._state = MatchInst.ST_FINAL
        self._stopHeartbeat()
        self._logger.info('MatchInstCtrl.final ok',
                          'state=', self._state)

    def _doHeartbeat(self):
        timestamp = pktimestamp.getCurrentTimestamp()
        if self._logger.isDebug():
            self._logger.debug('MatchInstCtrl._doHeartbeat',
                               'timestamp=', timestamp,
                               'state=', self._state)

        if self._state == MatchInst.ST_IDLE:
            self._doLoad()

        if self._state == MatchInst.ST_LOAD:
            if (not self.signinTime
                or pktimestamp.getCurrentTimestamp() >= self.signinTime):
                self._doStartSignin()

        if self._state == MatchInst.ST_SIGNIN:
            if (self.prepareTime
                and timestamp >= self.prepareTime):
                self._doPrepare()

        if self._state in (MatchInst.ST_SIGNIN, MatchInst.ST_PREPARE):
            if self.startTime:
                if timestamp >= self.startTime:
                    self._doStart()
            else:
                totalSignerCount = self._calcTotalSignerCount()
                if self._logger.isDebug():
                    self._logger.debug('MatchInstCtrl._doHeartbeat',
                                       'timestamp=', timestamp,
                                       'state=', self._state,
                                       'totalSignerCount=', totalSignerCount,
                                       'startUserCount=', self.matchConf.start.userCount)
                if totalSignerCount >= self.matchConf.start.userCount:
                    self._doStart()

        if self._state == MatchInst.ST_STARTING:
            if self._isAllStarted() or self._isStartingTimeout():
                self._cancelNotStartInst()
                self._state = MatchInst.ST_START
                signerMap = self._collectSignerMap()
                if self.startTime:
                    if len(signerMap) < self.matchConf.start.userMinCount:
                        self._cancel(MatchFinishReason.USER_NOT_ENOUGH)
                        signerMap = None
                    self._doFinal()
                    if signerMap:
                        self.master._startMatching(self, 1, signerMap.values())
                    self.master._setupNextInst(self, None)
                else:
                    signers = sorted(signerMap.values(), key=lambda s: s.signinTime)
                    num = 1
                    while len(signers) >= self.matchConf.start.userCount:
                        self.master._startMatching(self, num, signers[0:self.matchConf.start.userCount])
                        signers = signers[self.matchConf.start.userCount:]
                        num += 1
                    self.master._setupNextInst(self, signers)
                    self._doFinal()

        return 1

    def _collectSignerMap(self):
        signerMap = {}
        for areaStub in self.master.areaStubMap.values():
            if areaStub.curInstStub:
                signerMap.update(areaStub.curInstStub.signerMap)
        return signerMap

    def _doLoad(self):
        assert (self._state == MatchInst.ST_IDLE)
        self._state = MatchInst.ST_LOAD
        self._logger.info('MatchInstCtrl._doLoad ...',
                          'state=', self._state)
        for areaStub in self.master.areaStubMap.values():
            areaStub.createInst(self.instId, self.startTime, self.needLoad)
        self._logger.info('MatchInstCtrl._doLoad ok',
                          'state=', self._state)

    def _cancel(self, reason):
        self._logger.info('MatchInstCtrl._cancel ...',
                          'state=', self._state)
        for areaStub in self.master.areaStubMap.values():
            if areaStub.curInstStub:
                areaStub.curInstStub.cancel(reason)

        TYGame(self.master.gameId).getEventBus().publishEvent(MatchCancelEvent(self.master.gameId, self.instId, reason))
        self._logger.info('MatchInstCtrl._cancel ok',
                          'state=', self._state)

    def _moveToNext(self, nextInstId, signers):
        self._logger.info('MatchInstCtrl._moveToNext ...',
                          'state=', self._state,
                          'nextInstId=', nextInstId,
                          'signerCount=', len(signers))
        assert (len(self.master.areaStubMap) == 1)
        areaStub = self.master.areaStubMap.values()[0]
        areaStub.curInstStub.moveTo(nextInstId, signers)

        self._logger.info('MatchInstCtrl._moveToNext ok',
                          'state=', self._state,
                          'nextInstId=', nextInstId,
                          'signerCount=', len(signers))

    def _cancelSigners(self, reason, signers):
        self._logger.info('MatchInstCtrl._cancelSigners ...',
                          'state=', self._state,
                          'reason=', reason,
                          'signerCount=', len(signers))
        assert (len(self.master.areaStubMap) == 1)
        areaStub = self.master.areaStubMap.values()[0]
        areaStub.curInstStub.cancelSigners(reason, signers)
        self._logger.info('MatchInstCtrl._cancelSigners ok',
                          'state=', self._state,
                          'reason=', reason,
                          'signerCount=', len(signers))

    def _doStartSignin(self):
        assert (self._state == MatchInst.ST_LOAD)
        self._state = MatchInst.ST_SIGNIN
        self._logger.info('MatchInstCtrl._doStartSignin ...',
                          'state=', self._state)
        for areaStub in self.master.areaStubMap.values():
            if areaStub.curInstStub:
                areaStub.curInstStub.startSignin()
        TYGame(self.master.gameId).getEventBus().publishEvent(MatchStartSigninEvent(self.master.gameId, self.instId))
        self._logger.info('MatchInstCtrl._doStartSignin ok',
                          'state=', self._state)

    def _doPrepare(self):
        self._logger.info('MatchInstCtrl._doPrepare ...',
                          'state=', self._state)
        assert (self._state == MatchInst.ST_SIGNIN)
        self._state = MatchInst.ST_PREPARE
        for areaStub in self.master.areaStubMap.values():
            if areaStub.curInstStub:
                areaStub.curInstStub.prepare()
        self._logger.info('MatchInstCtrl._doPrepare ok',
                          'state=', self._state)

    def _doStart(self):
        assert (self._state in (MatchInst.ST_SIGNIN, MatchInst.ST_PREPARE))
        self._state = MatchInst.ST_STARTING
        self._startingTime = pktimestamp.getCurrentTimestamp()
        self._logger.info('MatchInstCtrl._doStart ...',
                          'state=', self._state)
        for areaStub in self.master.areaStubMap.values():
            if areaStub.curInstStub:
                areaStub.curInstStub.start()
        self._logger.info('MatchInstCtrl._doStart ok',
                          'state=', self._state)

    def _doFinal(self):
        assert (self._state == MatchInst.ST_START)
        self._state = MatchInst.ST_FINAL
        self._logger.info('MatchInstCtrl._doFinal ...',
                          'state=', self._state)
        self._stopHeartbeat()
        self._logger.info('MatchInstCtrl._doFinal ok',
                          'state=', self._state)

    def _isAllStarted(self):
        for areaStub in self.master.areaStubMap.values():
            if areaStub.curInstStub and areaStub.curInstStub.state != MatchInst.ST_START:
                return False
        return True

    def _isStartingTimeout(self):
        if self._state == MatchInst.ST_STARTING:
            ts = pktimestamp.getCurrentTimestamp()
            return (ts - self._startingTime) >= MatchInstCtrl.STARTING_TIMEOUT
        return False

    def _cancelNotStartInst(self):
        for areaStub in self.master.areaStubMap.values():
            if areaStub.curInstStub and areaStub.curInstStub.state != MatchInst.ST_START:
                areaStub.curInstStub.cancel(MatchFinishReason.OVERTIME)

    def _calcTotalSignerCount(self):
        count = 0
        for areaStub in self.master.areaStubMap.values():
            if areaStub.areaStatus and areaStub.areaStatus.instStatus:
                if areaStub.areaStatus.instStatus.instId == self.instId:
                    count += areaStub.areaStatus.instStatus.signerCount
        return count


class MatchMaster(HeartbeatAble):
    ST_IDLE = 0
    ST_START = 1
    ST_ALL_AREA_ONLINE = 2
    ST_LOAD = 3

    HEARTBEAT_TO_AREA_INTERVAL = 5

    def __init__(self, room, matchId, matchConf):
        super(MatchMaster, self).__init__()
        # 控制房间
        self.room = room
        # 比赛ID
        self.matchId = matchId
        # 比赛配置
        self.matchConf = matchConf
        # 赛区map
        self._areaStubMap = {}
        self._areaList = []
        # 状态
        self._state = MatchMaster.ST_IDLE
        # 实例控制对象
        self._instCtrl = None
        # 所有比赛
        self._matchingMap = {}
        # 最后到所有area心跳时间
        self._lastHeartbeatToAreaTime = None
        # 日志
        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('roomId', self.roomId)

        # 赛事状态dao
        self.matchStatusDao = None

    @property
    def areaCount(self):
        return len(self._areaStubMap)

    @property
    def areaStubMap(self):
        return self._areaStubMap

    @property
    def instCtrl(self):
        return self._instCtrl

    @property
    def gameId(self):
        return self.room.gameId

    @property
    def roomId(self):
        return self.room.roomId

    @property
    def matchName(self):
        return self.room.roomConf.get('name')

    def findMatching(self, matchingId):
        return self._matchingMap.get(matchingId)

    def findAreaStub(self, roomId):
        return self._areaStubMap.get(roomId)

    def findInstStub(self, roomId, instId):
        areaStub = self.findAreaStub(roomId)
        if areaStub:
            return areaStub.findInstStub(instId)
        return None

    def addAreaStub(self, areaStub):
        assert (self._state == MatchMaster.ST_IDLE)
        assert (isinstance(areaStub, MatchAreaStub))
        assert (not self.findAreaStub(areaStub.roomId))
        self._areaStubMap[areaStub.roomId] = areaStub
        self._areaList.append(areaStub)

    def findGroupStubWithMatchingId(self, matchingId, groupId):
        matching = self.findMatching(matchingId)
        if matching:
            return matching.findGroupStub(groupId)
        return None

    def findGroupStub(self, groupId):
        for matching in self._matchingMap.values():
            groupStub = matching.findGroupStub(groupId)
            if groupStub:
                return groupStub
        return None

    def buildStatus(self):
        ret = MatchMasterStatus()
        for areaStub in self._areaStubMap.values():
            ret.areaStatusMap[areaStub.roomId] = areaStub.buildStatus()
        return ret

    def start(self):
        assert (self._state == MatchMaster.ST_IDLE)
        self._state = MatchMaster.ST_START
        self._startHeartbeat()
        for areaStub in self._areaStubMap.values():
            areaStub.start()
        self._logger.info('MatchMaster.start ok',
                          'state=', self._state)

    def createGroupStubs(self, stage, groupCreateInfos, isGrouping):
        groupStubs = []
        for i, groupCreateInfo in enumerate(groupCreateInfos):
            index = i % len(self._areaList)
            groupStub = self._areaList[index].createGroup(stage, groupCreateInfo.groupId,
                                                          groupCreateInfo.groupName,
                                                          groupCreateInfo.playerList,
                                                          isGrouping, stage.matching.startPlayerCount)
            groupStubs.append(groupStub)
        return groupStubs

    def _doHeartbeatImpl(self):
        timestamp = pktimestamp.getCurrentTimestamp()
        if self._logger.isDebug():
            self._logger.debug('MatchMaster._doHeartbeatImpl',
                               'timestamp=', timestamp,
                               'areaCount=', self.areaCount,
                               'matchingCount=', len(self._matchingMap))
        if self._state == MatchMaster.ST_START:
            if self._isAllAreaOnline():
                self._state = MatchMaster.ST_ALL_AREA_ONLINE
                self._logger.info('MatchMaster._doHeartbeatImpl allAreaOnline',
                                  'areaCount=', self.areaCount)

        if self._state == MatchMaster.ST_ALL_AREA_ONLINE:
            self._doLoad()

        if self._state == MatchMaster.ST_LOAD:
            self._processMatching()

        if self._state >= MatchMaster.ST_ALL_AREA_ONLINE:
            if (not self._lastHeartbeatToAreaTime
                or timestamp - self._lastHeartbeatToAreaTime > MatchMaster.HEARTBEAT_TO_AREA_INTERVAL):
                self._lastHeartbeatToAreaTime = timestamp
                self._heartbeatToAllArea()
                roomInfo = self._buildRoomInfo()
                if self._logger.isDebug():
                    self._logger.debug('MatchMaster._doHeartbeatImpl',
                                       'roomInfo=', roomInfo.__dict__)
                roominfo.saveRoomInfo(self.gameId, roomInfo)
        return 1

    def _processMatching(self):
        if self._matchingMap:
            matchingList = list(self._matchingMap.values())
            for matching in matchingList:
                if matching.state == Matching.ST_FINISH:
                    del self._matchingMap[matching.matchingId]
                    self._logger.info('MatchMaster._processMatching matchingFinished',
                                      'matchingId=', matching.matchingId)

    def _heartbeatToAllArea(self):
        for areaStub in self._areaStubMap.values():
            try:
                areaStub.masterHeartbeat(self)
            except:
                self._logger.error('MatchMaster._heartbeatToAllArea',
                                   'roomId=', areaStub.roomId)
        self._logger.info('MatchMaster._heartbeatToAllArea areaRoomIds=', self._areaStubMap.keys(),
                          'areaCount=', self.areaCount)

    def _isAllAreaOnline(self):
        for areaStub in self._areaStubMap.values():
            if not areaStub.isOnline():
                return False
        return True

    def _calcMatchingPlayerCount(self):
        ret = 0
        for areaStub in self._areaStubMap.values():
            for groupStub in areaStub.groupStubMap.values():
                ret += groupStub.playerCount
        return ret

    def _buildRoomInfo(self):
        roomInfo = MatchRoomInfo()
        roomInfo.roomId = gdata.getBigRoomId(self.roomId)
        roomInfo.playerCount = self._calcMatchingPlayerCount()
        roomInfo.signinCount = self._instCtrl._calcTotalSignerCount() if self._instCtrl else 0
        roomInfo.startType = self.matchConf.start.type
        roomInfo.instId = self._instCtrl.instId if self._instCtrl else None
        roomInfo.fees = []
        if self.matchConf.fees:
            for fee in self.matchConf.fees:
                roomInfo.fees.append(TYContentItem(fee.assetKindId, fee.count))
        if self._instCtrl and self.matchConf.start.isTimingType():
            roomInfo.startTime = self._instCtrl.startTime
            roomInfo.signinTime = self._instCtrl.signinTime
        return roomInfo

    def _doLoad(self):
        assert (self._state == MatchMaster.ST_ALL_AREA_ONLINE)
        self._state = MatchMaster.ST_LOAD

        self._logger.info('MatchMaster._doLoad ...',
                          'state=', self._state)

        timestamp = pktimestamp.getCurrentTimestamp()
        startTime = self.matchConf.start.calcNextStartTime(timestamp)
        status = self.matchStatusDao.load(self.matchId)
        needLoad = False

        if status:
            # 如果没有下一场了，或者当前场已经过期
            if startTime is None or startTime != status.startTime:
                self._cancelInst(status.instId, MatchFinishReason.OVERTIME)
                status.sequence += 1
            else:
                needLoad = True
            status.startTime = startTime
        else:
            status = MatchStatus(self.matchId, 1, startTime)

        self.matchStatusDao.save(status)

        roominfo.removeRoomInfo(self.gameId, self.roomId)

        if status.startTime or self.matchConf.start.isUserCountType():
            self._instCtrl = MatchInstCtrl(self, status, needLoad)
            self._instCtrl.start()
            roomInfo = self._buildRoomInfo()
            roominfo.saveRoomInfo(self.gameId, roomInfo)

        self._logger.info('MatchMaster._doLoad ok',
                          'state=', self._state,
                          'instId=', self._instCtrl.instId if self._instCtrl else None)

    def _cancelInst(self, instId, reason):
        for areaStub in self._areaStubMap.values():
            try:
                areaStub.cancelInst(instId, reason)
            except:
                self._logger.error('MatchMaster._cancelInst',
                                   'roomId=', areaStub.roomId)

        self._logger.info('MatchMaster._cancelInst ok',
                          'instId=', instId,
                          'reason=', reason)

    def _startMatching(self, instCtrl, num, signers):
        matchingId = '%s.%s' % (instCtrl.instId, num)
        matching = Matching(self, instCtrl.instId, matchingId)
        self._matchingMap[matchingId] = matching
        self._logger.hinfo('MatchMaster._startMatching ...',
                           'matchingId=', matchingId,
                           'signerCount=', len(signers))

        matching.start(signers)

        if self._logger.isDebug():
            self._logger.debug('MatchMaster._startMatching',
                               'matchingId=', matchingId,
                               'signers=', [signer.userId for signer in signers])

        self._logger.hinfo('MatchMaster._startMatching ok',
                           'matchingId=', matchingId,
                           'signerCount=', len(signers))

    def _setupNextInst(self, instCtrl, signers):
        timestamp = pktimestamp.getCurrentTimestamp()
        startTime = self.matchConf.start.calcNextStartTime(timestamp + 1)
        if startTime or self.matchConf.start.isUserCountType():
            needLoad = False
            status = MatchStatus(self.matchId, instCtrl.status.sequence + 1, startTime)
            if signers:
                needLoad = True
                instCtrl._moveToNext(status.instId, signers)
            self.matchStatusDao.save(status)
            self._instCtrl = MatchInstCtrl(self, status, needLoad)
            self._instCtrl.start()

        else:
            self._instCtrl = None
            if signers:
                instCtrl._cancelSigners(MatchFinishReason.USER_NOT_ENOUGH, signers)
            roominfo.removeRoomInfo(self.gameId, self.roomId)
        self._logger.hinfo('MatchMaster._setupNextInst ok',
                           'instId=', instCtrl.instId,
                           'timestamp=', timestamp,
                           'nextInstId=', self._instCtrl.instId if self._instCtrl else None,
                           'startTime=', self._instCtrl.startTime if self._instCtrl else None,
                           'signinTime=', self._instCtrl.signinTime if self._instCtrl else None,
                           'signers=', [s.userId for s in signers] if signers else None)
        return self._instCtrl
