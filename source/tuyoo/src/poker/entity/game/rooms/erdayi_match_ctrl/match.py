# -*- coding:utf-8 -*-
'''
Created on 2016年7月13日

@author: zhaojiangang
'''
import time

from datetime import datetime

import poker.util.timestamp as pktimestamp
from poker.entity.biz.content import TYContentItem
from poker.entity.game.rooms import roominfo
from poker.entity.game.rooms.erdayi_match_ctrl.const import FeeType, \
    MatchFinishReason, GroupingType
from poker.entity.game.rooms.erdayi_match_ctrl.exceptions import \
    SigninStoppedException, AlreadySigninException, SigninNotStartException, \
    SigninFullException, BadStateException, MatchStoppedException, \
    AleadyInMatchException, SigninException
from poker.entity.game.rooms.erdayi_match_ctrl.interface import SigninRecord, \
    MatchStatus
from poker.entity.game.rooms.erdayi_match_ctrl.models import Signer, \
    GroupNameGenerator, PlayerGrouping
from poker.entity.game.rooms.erdayi_match_ctrl.utils import HeartbeatAble, \
    Logger
from poker.entity.game.rooms.roominfo import MatchRoomInfo
from poker.util import strutil


class MatchInst(HeartbeatAble):
    ST_IDLE = 0
    ST_SIGNIN = 1
    ST_PREPARE = 2
    ST_STARTING = 3
    ST_STARTED = 4
    ST_FINAL = 5

    def __init__(self, area, instId, startTime, needLoad):
        super(MatchInst, self).__init__(1)
        # 赛区
        self.area = area
        # 实例ID
        self.instId = instId
        # 开赛时间
        self.startTime = startTime
        # 状态
        self._state = MatchInst.ST_IDLE
        # key=userId, value=Signer
        self._signerMap = {}
        # 是否需要加载
        self._needLoad = needLoad

        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('roomId', self.roomId)
        self._logger.add('instId', self.instId)

    @property
    def matchId(self):
        return self.area.matchId

    @property
    def matchConf(self):
        return self.area.matchConf

    @property
    def roomId(self):
        return self.area.roomId

    @property
    def state(self):
        return self._state

    @property
    def needLoad(self):
        return self._needLoad

    @property
    def signerCount(self):
        return len(self._signerMap)

    @property
    def signerMap(self):
        return self._signerMap

    @property
    def master(self):
        return self.area.master

    def findSigner(self, userId):
        return self._signerMap.get(userId)

    def getTotalSignerCount(self):
        return self.signerCount

    def startSignin(self):
        '''
        开始报名
        '''
        self._heart.postCall(self._doStartSignin)

    def prepare(self):
        '''
        准备阶段开始
        '''
        self._heart.postCall(self._doPrepare)

    def cancel(self, reason):
        '''
        比赛取消
        '''
        self._heart.postCall(self._doCancel, reason)

    def start(self):
        '''
        比赛开始
        '''
        self._heart.postCall(self._doStart)

    def final(self):
        '''
        结束
        '''
        self._heart.postCall(self._doFinal)

    def _doStartSignin(self):
        if self._state < MatchInst.ST_SIGNIN:
            self._state = MatchInst.ST_SIGNIN
            self._doStartSigninImpl()
        else:
            self._logger.warn('MatchInst._doStartSignin fail',
                              'state=', self._state,
                              'err=', 'BadState')

    def _doPrepare(self):
        if self._state < MatchInst.ST_PREPARE:
            self._state = MatchInst.ST_PREPARE
            self._doPrepareImpl()
        else:
            self._logger.warn('MatchInst._doPrepare fail',
                              'state=', self._state,
                              'err=', 'BadState')

    def _doCancel(self, reason):
        if self._state < MatchInst.ST_FINAL:
            self._state = MatchInst.ST_FINAL
            self._doCancelImpl(reason)
        else:
            self._logger.warn('MatchInst._doCancel fail',
                              'state=', self._state,
                              'reason=', reason,
                              'err=', 'BadState')

    def _doStart(self):
        if self._state < MatchInst.ST_STARTING:
            self._state = MatchInst.ST_STARTING
            self._doStartImpl()
        else:
            self._logger.warn('MatchInst._doStart fail',
                              'state=', self._state,
                              'err=', 'BadState')

    def _doFinal(self):
        if self._state < MatchInst.ST_FINAL:
            self._state = MatchInst.ST_FINAL
            self._doFinalImpl()
        else:
            self._logger.warn('MatchInst._doFinal fail',
                              'state=', self._state,
                              'err=', 'BadState')

    def _doStartSigninImpl(self):
        pass

    def _doPrepareImpl(self):
        pass

    def _doCancelImpl(self, reason):
        pass

    def _doStartImpl(self):
        pass

    def _doFinalImpl(self):
        pass


class MatchInstLocal(MatchInst):
    def __init__(self, area, instId, startTime, needLoad):
        super(MatchInstLocal, self).__init__(area, instId, startTime, needLoad)

    def addInitSigners(self, signers):
        for signer in signers:
            # 记录
            self.area.signinRecordDao.add(self.matchId, self.roomId, self.instId,
                                          SigninRecord(signer.userId, signer.signinTime, signer.fee))

            # 创建MatchUser
            self.area.matchUserIF.createUser(self.matchId, self.roomId, self.instId, signer.userId, signer.fee)

    def signin(self, userId, feeIndex):
        # 检查参数
        if (self.matchConf.fees
            and (feeIndex < 0
                 or feeIndex >= len(self.matchConf.fees))):
            raise SigninException('请选择报名费')

        # 检查是否可以报名
        self._ensureCanSignin(userId)

        # 报名费
        timestamp = pktimestamp.getCurrentTimestamp()
        fee = self.matchConf.fees[feeIndex] if self.matchConf.fees else None

        # 报名逻辑
        signer = self._doSignin(userId, fee, timestamp)

        self._logger.hinfo('MatchInstLocal.signin ok',
                           'state=', self._state,
                           'userId=', userId,
                           'signerCount=', self.signerCount,
                           'fee=', signer.fee.toDict() if signer.fee else None)
        return signer

    def signout(self, signer):
        assert (signer.inst == self)

        if self._state != MatchInst.ST_SIGNIN:
            raise SigninStoppedException()

        del self._signerMap[signer.userId]

        # 删除SigninRecord
        self.area.signinRecordDao.remove(self.matchId, self.roomId, self.instId, signer.userId)
        # 退费
        if signer.fee:
            self.area.signinFee.returnFee(self.matchId, self.roomId, self.instId, signer.userId, signer.fee)
        # 删除MatchPlayer
        self.area.matchUserIF.removeUser(self.matchId, self.roomId, self.instId, signer.userId)

        self._logger.hinfo('MatchInstLocal.signout ok',
                           'state=', self._state,
                           'userId=', signer.userId,
                           'fee=', signer.fee.toDict() if signer.fee else None,
                           'signerCount=', self.signerCount)

    def enter(self, signer):
        assert (signer.inst == self)
        if self._state == MatchInst.ST_SIGNIN or self._state == MatchInst.ST_PREPARE:
            signer.isEnter = True
            self._fillSigner(signer)
            self._logger.info('MatchInstLocal.enter ok',
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
            self._logger.info('MatchInstLocal.leave ok',
                              'state=', self._state,
                              'userId=', signer.userId,
                              'signerCount=', self.signerCount)

    def buildStatus(self):
        # return MatchInstStatus(self.instId, self._state, self.signerCount)
        pass

    def _doInit(self):
        self._logger.info('MatchInstLocal._doInit ...',
                          'state=', self._state)
        if self._needLoad:
            records = self.area.signinRecordDao.loadAll(self.matchId, self.roomId, self.instId)
            if records:
                for record in records:
                    signer = Signer(record.userId, self.instId)
                    signer.inst = self
                    self._signerMap[signer.userId] = signer
        self._logger.info('MatchInstLocal._doInit ok',
                          'state=', self._state)
        return 1

    def _doStartSigninImpl(self):
        self._logger.info('MatchInstLocal._doStartSigninImpl ...',
                          'state=', self._state)
        self._logger.info('MatchInstLocal._doStartSigninImpl ok',
                          'state=', self._state)

    def _doPrepareImpl(self):
        self._logger.info('MatchInstLocal._doPrepareImpl ...',
                          'state=', self._state)
        startTime = time.time()
        self._prelockSigners(self._signerMap.values()[:])
        self._logger.info('MatchInstLocal._doPrepareImpl ok',
                          'state=', self._state,
                          'signerCount=', self.signerCount,
                          'usedTime=', time.time() - startTime)
        self._logger.info('MatchInstLocal._doPrepareImpl ok',
                          'state=', self._state)

    def _doStartImpl(self):
        self._logger.hinfo('MatchInstLocal._doStartImpl ...',
                           'state=', self._state)

        startTime = time.time()
        self._totalSignerCount = self.signerCount
        self._lockSigners()
        self._logger.hinfo('MatchInstLocal._doStart lockOk',
                           'state=', self._state,
                           'signerCount=', self.signerCount,
                           'usedTime=', time.time() - startTime)

        if not self.matchConf.start.isUserCountType():
            self.area.playerNotifier.notifyMatchStart(self.instId, self._signerMap.values())

        self._state = MatchInst.ST_STARTED

        self.area.onInstStarted(self)

        self._logger.hinfo('MatchInstLocal._doStartImpl ok',
                           'state=', self._state)

    def _doCancelImpl(self, reason):
        self._logger.info('MatchInstLocal._doCancelImpl ...',
                          'state=', self._state,
                          'reason=', reason)
        for signer in self._signerMap.values():
            self._cancelSigner(signer, reason)
        self._signerMap = {}
        self._logger.info('MatchInstLocal._doCancelImpl ok',
                          'state=', self._state,
                          'rerason=', reason)

    def _doFinalImpl(self):
        self._logger.info('MatchInstLocal._doFinalImpl ...',
                          'state=', self._state)
        self._logger.info('MatchInstLocal._doFinalImpl ok',
                          'state=', self._state)

    def _doSignin(self, userId, fee, timestamp):
        signer = None
        try:
            signer = self.area.matchFactory.newSigner(userId, self.instId)
            signer.signinTime = timestamp
            signer.isEnter = True
            signer.inst = self
            # 收费
            if fee:
                self.area.signinFee.collectFee(self.matchId, self.roomId, self.instId, userId, fee)
                signer.fee = fee

            # 记录
            add = self.area.signinRecordDao.add(self.matchId, self.roomId, self.instId,
                                                SigninRecord(userId, signer.signinTime, fee))

            # 创建MatchUser
            ec = self.area.matchUserIF.createUser(self.matchId, self.roomId, self.instId, userId, fee)

            # 检查是否其它tasklet也报名了
            exists = self.findSigner(userId)
            if exists:
                exists.isEnter = True
                raise AlreadySigninException()

            # 增加signer
            self._signerMap[userId] = signer
            self._fillSigner(signer)

            if ec != 0:
                raise AlreadySigninException()

            if not add:
                # 之前已经报过名
                raise AlreadySigninException()
            return signer
        except:
            if signer and signer.fee:
                # 退还报名费
                self.area.signinFee.returnFee(self.matchId, self.roomId, self.instId, userId, signer.fee)
            raise

    def _fillSigner(self, signer):
        self.area.signerInfoLoader.fillSigner(signer)
        if self._logger.isDebug():
            self._logger.debug('MatchInstLocal._fillSigner',
                               'userId=', signer.userId,
                               'userName=', signer.userName,
                               'clientId=', signer.clientId)

    def _prelockSigners(self, signers):
        for signer in signers:
            self._lockSigner(signer)

    def _lockSigner(self, signer):
        if (not signer.isLocked
            and signer.isEnter
            and self.area.matchUserIF.lockUser(self.matchId, self.roomId, self.instId, signer.userId, signer.clientId)):
            if self._logger.isDebug():
                self._logger.debug('MatchInstLocal._lockSigner Ok',
                                   'userId=', signer.userId,
                                   'userName=', signer.userName,
                                   'clientId=', signer.clientId)
            signer.isLocked = True
        return signer.isLocked

    def _unlockSigner(self, signer, returnFee=False):
        if signer.isLocked:
            signer.isLocked = False
        # 退费
        if returnFee and signer.fee:
            self.area.signinFee.returnFee(self.matchId, self.roomId, self.instId, signer.userId, signer.fee)
        # 解锁
        self.area.matchUserIF.unlockUser(self.matchId, self.roomId, self.instId, signer.userId)

    def _lockSigners(self):
        nolocks = []
        for signer in self._signerMap.values():
            if not self._lockSigner(signer):
                nolocks.append(signer)
        for signer in nolocks:
            self._kickoutSigner(signer)
        return nolocks

    def _kickoutSigner(self, signer):
        try:
            returnFees = (self.matchConf.start.feeType == FeeType.TYPE_RETURN or signer.isEnter)
            self._unlockSigner(signer, returnFees)
            del self._signerMap[signer.userId]
            kickoutReason = 'nolock' if signer.isEnter else 'noenter'
            self._logger.info('MatchInstLocal._kickoutSigner ok',
                              'userId=', signer.userId,
                              'kickoutReason=', kickoutReason)
        except:
            self._logger.error('MatchInstLocal._kickoutSigner ERROR', signer.userId)

    def _cancelSigner(self, signer, reason):
        returnFees = (self.matchConf.start.feeType == FeeType.TYPE_RETURN or signer.isEnter) \
                     and reason in (MatchFinishReason.USER_NOT_ENOUGH, MatchFinishReason.RESOURCE_NOT_ENOUGH)
        self._unlockSigner(signer, returnFees)
        self.area.playerNotifier.notifyMatchCancelled(signer, reason)
        self._logger.info('MatchInstLocal._cancelSigner ok',
                          'userId=', signer.userId,
                          'reason=', reason,
                          'returnFees=', returnFees)

    def _ensureCanSignin(self, userId):
        # 报名还未开始
        if self._state < MatchInst.ST_SIGNIN:
            raise SigninNotStartException()

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

    def _doHeartbeat(self):
        return 1


class MatchGroup(HeartbeatAble):
    ST_IDLE = 0
    ST_START = 1
    ST_FINISHING = 2
    ST_FINISH = 3
    ST_FINALING = 4
    ST_FINAL = 5

    def __init__(self, area, instId, matchingId, matchingId3, groupId, groupIndex,
                 groupName, stageIndex, isGrouping, totalPlayerCount):
        super(MatchGroup, self).__init__(1)
        self.area = area
        self.instId = instId
        self.matchingId = matchingId
        self.matchingId3 = matchingId3
        self.groupId = groupId
        self.groupIndex = groupIndex
        self.groupName = groupName
        self.stageIndex = stageIndex
        self.isGrouping = isGrouping
        self.totalPlayerCount = totalPlayerCount

        # key=userId, value=Player
        self._playerMap = {}
        self._state = MatchGroup.ST_IDLE

        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('instId', self.instId)
        self._logger.add('groupId', self.groupId)
        self._logger.add('matchingId', self.matchingId)
        if self.matchingId3:
            self._logger.add('matchingId3', self.matchingId3)
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
    def playerMap(self):
        return self._playerMap

    @property
    def playerCount(self):
        return len(self._playerMap)

    def getRisePlayers(self):
        return self._playerMap.values()

    def findPlayer(self, userId):
        '''
        查找Player
        '''
        return self._playerMap.get(userId)

    def removePlayer(self, player):
        assert (player.group == self)
        del self._playerMap[player.userId]

    def addPlayers(self, players):
        '''
        给该分组增加一个player，必须在开始之前调用
        '''
        if self._state == MatchGroup.ST_IDLE:
            for player in players:
                if self.findPlayer(player.userId):
                    self._logger.warn('MatchGroup._doAddPlayers state=', self._state,
                                      'userId=', player.userId,
                                      'err=', 'AlreadyInGroup')
                else:
                    player._group = self
                    self._playerMap[player.userId] = player
            self._logger.info('MatchGroup._doAddPlayers state=', self._state,
                              'playerCount=', len(players))
        else:
            self._logger.error('MatchGroup.addPlayers state=', self._state,
                               'playerCount=', len(players))

    def finishGroup(self, reason):
        '''
        杀掉该分组
        '''
        self._heart.postCall(self._doFinish, reason)

    def finalGroup(self):
        self._heart.postCall(self._doFinal)

    def _doInit(self):
        return 1

    def _doFinish(self, reason):
        if self._state < MatchGroup.ST_FINISHING:
            self._state = MatchGroup.ST_FINISH

            self._doFinishImpl(reason)

            self._logger.hinfo('MatchGroup._doFinish ok',
                               'state=', self._state,
                               'reason=', reason)
        else:
            self._logger.error('MatchGroup._doFinish fail',
                               'state=', self._state,
                               'reason=', reason,
                               'err=', 'BadState')

    def _doFinal(self):
        self._logger.info('MatchGroup._doFinal ...',
                          'state=', self._state)
        if self._state == MatchGroup.ST_FINISH:
            self._state = MatchGroup.ST_FINALING
            self.stopHeart()
            try:
                self._doFinalImpl()
                self._logger.info('MatchGroup._doFinal ok',
                                  'state=', self._state)
            except:
                self._logger.error('MatchGroup._doFinal fail',
                                   'state=', self._state)
            self._state = MatchGroup.ST_FINAL
        else:
            self._logger.error('MatchGroup._doFinal fail',
                               'state=', self._state,
                               'err=', 'BadState')

    def _doFinishImpl(self, reason):
        raise NotImplementedError

    def _doFinalImpl(self):
        raise NotImplementedError

    def _doHeartbeat(self):
        return 1


class MatchGroupLocal(MatchGroup):
    '''
    一个比赛分组
    '''

    def __init__(self, area, instId, matchingId, matchingId3, groupId, groupIndex,
                 groupName, stageIndex, isGrouping, totalPlayerCount):
        super(MatchGroupLocal, self).__init__(area, instId, matchingId, matchingId3, groupId, groupIndex,
                                              groupName, stageIndex, isGrouping,
                                              totalPlayerCount)
        # 本组开始时的
        self._startPlayerCount = 0
        # 阶段
        self._stage = None
        # 该分组启动时间
        self._startTime = 0
        # 随后活跃时间
        self._lastActiveTime = 0

    @property
    def match(self):
        return self._match

    @property
    def stage(self):
        return self._stage

    @property
    def startPlayerCount(self):
        return self._startPlayerCount

    def setStage(self, stage):
        self._stage = stage

    def calcTotalUncompleteTableCount(self, player):
        return self._stage.calcUncompleteTableCount(player)

    def _doInit(self):
        self._logger.info('MatchGroupLocal._doInit ...',
                          'state=', self._state)
        self._state = MatchGroup.ST_START
        self._startTime = pktimestamp.getCurrentTimestamp()
        self._lastActiveTime = self._startTime
        self._startPlayerCount = len(self._playerMap)

        ok, reason = self._stage.start()

        if not ok:
            self._doFinish(reason)

        self._logger.info('MatchGroupLocal._doInit ok',
                          'state=', self._state)
        return 1

    def _doFinishImpl(self, reason):
        self._stage.finish(reason)

    def _doFinalImpl(self):
        self._logger.info('MatchGroupLocal._doFinalImpl ...',
                          'state=', self._state)
        self._logger.info('MatchGroupLocal._doFinalImpl ok',
                          'state=', self._state)

    def _doHeartbeat(self):
        if self._logger.isDebug():
            self._logger.debug('MatchGroupLocal._doHeartbeat',
                               'state=', self._state)
        ret = 1
        if self._state == MatchGroup.ST_START:
            ret = self._stage.processStage()
        if self._state == MatchGroup.ST_START:
            if self._stage.isStageFinished():
                self._doFinish(MatchFinishReason.FINISH)
        if self._state < MatchGroup.ST_FINISH:
            timestamp = pktimestamp.getCurrentTimestamp()
            if timestamp - self._startTime > self.matchConf.start.maxPlayTime:
                self._doFinish(MatchFinishReason.OVERTIME)
        return ret


class MatchArea(HeartbeatAble):
    def __init__(self, matchConf, interval):
        super(MatchArea, self).__init__(interval)
        # 比赛配置
        self.matchConf = matchConf
        # 当前赛区运行的分组
        self._groupMap = {}

    @property
    def matchId(self):
        return self.matchConf.matchId

    @property
    def tableId(self):
        return self.matchConf.tableId

    @property
    def groupMap(self):
        return self._groupMap

    def findPlayer(self, userId):
        for group in self._groupMap.values():
            player = group.findPlayer(userId)
            if player:
                return player
        return None

    def isOnline(self):
        '''
        赛区是否在线
        '''
        return False

    def newInst(self, instId, startTime, needLoad):
        '''
        新建一个新的比赛实例
        '''
        raise NotImplementedError

    def newGroup(self, instId, matchingId, groupId,
                 groupName, stageIndex, isGrouping,
                 totalPlayerCount):
        '''
        创建一个新的分组
        '''
        raise NotImplementedError

    def findGroup(self, groupId):
        '''
        根据groupId查找Group
        '''
        raise NotImplementedError


class MatchAreaLocal(MatchArea):
    def __init__(self, master, room, matchConf):
        super(MatchAreaLocal, self).__init__(matchConf, 1)
        # 房间
        self.room = room
        # 主控
        self.master = master
        # 当前分区所有比赛实例 key=instId, value=MatchInst
        self._instMap = {}
        # 当前比赛实例
        self._curInst = None

        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('roomId', self.room.roomId)

    @property
    def roomId(self):
        return self.room.roomId

    @property
    def gameId(self):
        return self.room.gameId

    @property
    def curInst(self):
        return self._curInst

    @property
    def findInst(self, instId):
        return self._instMap.get(instId)

    def isOnline(self):
        '''
        本地的赛区始终在线
        '''
        return True

    def newInst(self, instId, startTime, needLoad):
        self._logger.info('MatchAreaLocal.createInst ...',
                          'instId=', instId,
                          'startTime=', startTime,
                          'needLoad=', needLoad,
                          'curInstId=', self._curInst.instId if self._curInst else None)

        self._curInst = MatchInstLocal(self, instId, startTime, needLoad)
        self._instMap[instId] = self._curInst

        self._logger.info('MatchAreaLocal.createInst ok',
                          'startTime=', startTime,
                          'needLoad=', needLoad,
                          'instId=', instId)
        return self._curInst

    def newGroup(self, instId, matchingId, matchingId3, groupId, groupIndex,
                 groupName, stageIndex, isGrouping,
                 totalPlayerCount):
        group = self.findGroup(groupId)
        if group:
            self._logger.error('MatchAreaLocal.createGroup fail',
                               'instId=', instId,
                               'matchingId=', matchingId,
                               'matchingId3=', matchingId3,
                               'groupId=', groupId,
                               'groupIndex=', groupIndex,
                               'groupName=', groupName,
                               'stageIndex=', stageIndex,
                               'isGrouping=', isGrouping,
                               'totalPlayerCount=', totalPlayerCount,
                               'err=', 'GroupExists')
            raise BadStateException()

        group = MatchGroupLocal(self, instId, matchingId, matchingId3, groupId, groupIndex,
                                groupName, stageIndex, isGrouping, totalPlayerCount)
        stage = self.matchFactory.newStage(self.matchConf.stages[stageIndex], group)
        group.setStage(stage)
        self._groupMap[groupId] = group

        self._logger.info('MatchAreaLocal.createGroup ok',
                          'instId=', instId,
                          'matchingId=', matchingId,
                          'matchingId3=', matchingId3,
                          'groupId=', groupId,
                          'groupName=', groupName,
                          'stageIndex=', stageIndex,
                          'isGrouping=', isGrouping,
                          'totalPlayerCount=', totalPlayerCount)
        return group

    def findGroup(self, groupId):
        '''
        根据groupId查找Group
        '''
        return self._groupMap.get(groupId)

    def findSigner(self, userId):
        '''
        根据userId查找Signer
        '''
        return self._curInst.findSigner(userId) if self._curInst else None

    def findPlayer(self, userId):
        '''
        根据userId查找Player
        '''
        for group in self._groupMap.values():
            player = group.findPlayer(userId)
            if player:
                return player
        return None

    def signin(self, userId, feeIndex):
        '''
        玩家报名
        '''
        if not self._curInst:
            raise MatchStoppedException()

        if self.findPlayer(userId):
            raise AleadyInMatchException()

        return self._curInst.signin(userId, feeIndex)

    def signout(self, userId):
        '''
        玩家退赛
        '''
        if not self._curInst:
            raise MatchStoppedException()

        signer = self._curInst.findSigner(userId)
        if not signer:
            self._logger.warn('MatchAreaLocal.signout fail',
                              'userId=', userId,
                              'err=', 'NotFoundPlayer')
            return
        self._curInst.signout(signer)

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

    def onInstStarted(self, inst):
        '''
        暂时不做处理，因为只处理本地
        '''
        self._logger.info('MatchAreaLocal.onInstStarted instId=', inst.instId)

    def _doInit(self):
        self._logger.info('MatchAreaLocal._doInit ...')
        self._logger.info('MatchAreaLocal._doInit ok')
        return 1

    def _doHeartbeat(self):
        for inst in self._instMap.values()[:]:
            if inst.state == MatchInst.ST_FINAL:
                del self._instMap[inst.instId]
                self._logger.info('MatchAreaLocal._doHeartbeat removeInst',
                                  'instId=', inst.instId)
        for group in self._groupMap.values()[:]:
            if group.state == MatchGroup.ST_FINAL:
                del self._groupMap[group.groupId]
                self._logger.info('MatchAreaLocal._doHeartbeat removeGroup',
                                  'groupId=', group.instId)
        return 1


class MatchInstCtrl(HeartbeatAble):
    STARTING_TIMEOUT = 180

    def __init__(self, master, status, needLoad, signers=None):
        super(MatchInstCtrl, self).__init__(1)
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
        self._initSigners = signers

        # key=roomId, value=MatchInst
        self._instMap = {}
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

    def cancel(self, reason):
        self._heart.postCall(self._doCancel, reason)

    def calcTotalSignerCount(self):
        count = 0
        for inst in self._instMap.values():
            count += inst.signerCount
        return count

    def _doInit(self):
        assert (self._state == MatchInst.ST_IDLE)
        self._logger.info('MatchInstCtrl._doInit ...',
                          'state=', self._state)
        if self._initSigners:
            assert (len(self.master.areas) == 1)

        for area in self.master.areas:
            inst = area.newInst(self.instId, self.startTime, self.needLoad)
            self._instMap[area.roomId] = inst
            if self._initSigners:
                assert (isinstance(inst, MatchInstLocal))
                inst.addInitSigners(self._initSigners)
            inst.startHeart()

        self._logger.info('MatchInstCtrl._doInit ok',
                          'state=', self._state)
        return 1

    def _doStartSignin(self):
        self._logger.info('MatchInstCtrl._doStartSignin ...',
                          'state=', self._state)
        assert (self._state == MatchInst.ST_IDLE)
        self._state = MatchInst.ST_SIGNIN
        for inst in self._instMap.values():
            inst.startSignin()
        self._logger.info('MatchInstCtrl._doStartSignin ok',
                          'state=', self._state)

    def _doPrepare(self):
        self._logger.info('MatchInstCtrl._doPrepare ...',
                          'state=', self._state)
        assert (self._state < MatchInst.ST_PREPARE)
        self._state = MatchInst.ST_PREPARE
        for inst in self._instMap.values():
            inst.prepare()
        self._logger.info('MatchInstCtrl._doPrepare ok',
                          'state=', self._state)

    def _doStart(self):
        self._logger.info('MatchInstCtrl._doStart ...',
                          'state=', self._state)
        assert (self._state in (MatchInst.ST_SIGNIN, MatchInst.ST_PREPARE))
        self._state = MatchInst.ST_STARTING
        self._startingTime = pktimestamp.getCurrentTimestamp()
        for inst in self._instMap.values():
            inst.start()
        self._logger.info('MatchInstCtrl._doStart ok',
                          'state=', self._state)

    def _doCancel(self, reason):
        self._logger.info('MatchInstCtrl._doCancel',
                          'state=', self._state,
                          'reason=', reason)
        if self._state < MatchInst.ST_FINAL:
            self._state = MatchInst.ST_FINAL
            for inst in self._instMap.values():
                inst.cancel(reason)

    def _doFinal(self):
        self._logger.info('MatchInstCtrl._doFinal',
                          'state=', self._state)
        if self._state < MatchInst.ST_FINAL:
            self._state = MatchInst.ST_FINAL
            for inst in self._instMap.values():
                inst.final()

    def _isAllStarted(self):
        for inst in self._instMap.values():
            if inst.state != MatchInst.ST_STARTED:
                return False
        return True

    def _isStartingTimeout(self):
        if self._state == MatchInst.ST_STARTING:
            ts = pktimestamp.getCurrentTimestamp()
            return (ts - self._startingTime) >= MatchInstCtrl.STARTING_TIMEOUT
        return False

    def _cancelTimeoutInst(self):
        for inst in self._instMap.values():
            if inst.state != MatchInst.ST_STARTED:
                inst.cancel(MatchFinishReason.OVERTIME)

    def _collectSignerMap(self):
        signerMap = {}
        for inst in self._instMap.values():
            if inst.state == MatchInst.ST_STARTED:
                signerMap.update(inst.signerMap)
        return signerMap

    def _doHeartbeat(self):
        if self._logger.isDebug():
            self._logger.debug('MatchInstCtrl._doHeartbeat',
                               'state=', self._state)

        if self._state == MatchInst.ST_IDLE:
            if (not self.signinTime
                or pktimestamp.getCurrentTimestamp() >= self.signinTime):
                self._doStartSignin()

        if self._state == MatchInst.ST_SIGNIN:
            if (self.prepareTime
                and pktimestamp.getCurrentTimestamp() >= self.prepareTime):
                self._doPrepare()

        if self._state in (MatchInst.ST_SIGNIN, MatchInst.ST_PREPARE):
            if self.startTime:
                if pktimestamp.getCurrentTimestamp() >= self.startTime:
                    self._doStart()
            else:
                inst = self._instMap.values()[0]
                if self._logger.isDebug():
                    self._logger.debug('MatchInstCtrl._doHeartbeat',
                                       'timestamp=', pktimestamp.getCurrentTimestamp(),
                                       'state=', self._state,
                                       'totalSignerCount=', inst.signerCount,
                                       'startUserCount=', self.matchConf.start.userCount)
                if inst.signerCount >= self.matchConf.start.userCount:
                    self._doStart()

        if self._state == MatchInst.ST_STARTING:
            if self._isAllStarted() or self._isStartingTimeout():
                self._state = MatchInst.ST_STARTED
                self._cancelTimeoutInst()
                signerMap = self._collectSignerMap()

                if self._logger.isDebug():
                    self._logger.debug('MatchInstCtrl._doHeartbeat',
                                       'state=', self._state,
                                       'signerCount=', len(signerMap),
                                       'userIds=', signerMap.keys())

                if self.startTime:
                    if len(signerMap) < self.matchConf.start.userMinCount:
                        # 人数不足
                        self._doCancel(MatchFinishReason.USER_NOT_ENOUGH)
                        signerMap = None
                    self._doFinal()
                    self.master._setupNextInst(self, None, 1)
                    if signerMap:
                        self.master._startMatching(self, 1, signerMap.values())
                else:
                    signers = sorted(signerMap.values(), key=lambda s: s.signinTime)
                    num = 1
                    signersList = []
                    while len(signers) >= self.matchConf.start.userCount:
                        signersList.append(signers[0:self.matchConf.start.userCount])
                        signers = signers[self.matchConf.start.userCount:]
                        num += 1
                    self._doFinal()
                    self.master._setupNextInst(self, signers, num)
                    for signers in signersList:
                        self.master._startMatching(self, num, signers)

        if self._state == MatchInst.ST_FINAL:
            self.stopHeart()
        return 1


class MatchStageCtrl(object):
    ST_IDLE = 0
    ST_START = 1
    ST_FINISH = 2
    ST_FINAL = 3

    def __init__(self, matching, stageConf):
        # 比赛
        self.matching = matching
        # 阶段配置
        self.stageConf = stageConf
        # 该阶段所有分组key=groupId, value=MatchGroup
        self._groupMap = {}
        # 状态
        self._state = MatchStageCtrl.ST_IDLE
        self._logger = Logger()
        self._logger.add('instId', self.instId)
        self._logger.add('matchingId', self.matchingId)
        if self.matchingId3:
            self._logger.add('matchingId3', self.matchingId3)
        self._logger.add('stageIndex', self.stageIndex)

    @property
    def instId(self):
        return self.matching.instId

    @property
    def matchingId(self):
        return self.matching.matchingId

    @property
    def matchingId3(self):
        return self.matching.matchingId3

    @property
    def master(self):
        return self.matching.master

    @property
    def stageIndex(self):
        return self.stageConf.index

    @property
    def matchConf(self):
        return self.matching.matchConf

    @property
    def state(self):
        return self._state

    def getAllRisePlayerList(self):
        playerMap = {}
        for group in self._groupMap.values():
            players = group.getRisePlayers()
            for player in players:
                playerMap[player.userId] = player
        return playerMap.values()

    def startStage(self, playerList):
        '''
        启动该阶段
        '''
        self._logger.info('MatchStageCtrl.startStage',
                          'userIds=', [p.userId for p in playerList])
        # 对players进行分组
        isGrouping, groupPlayerLists = self.groupingPlayerList(playerList, self.stageConf,
                                                               self.matchConf.tableSeatCount)
        for i, groupPlayerList in enumerate(groupPlayerLists):
            groupId = '%s.%s.%s' % (self.matchingId, self.stageIndex, i + 1)
            groupName = GroupNameGenerator.generateGroupName(len(groupPlayerLists), i)
            area = self.master.areas[i % len(self.master.areas)]
            group = area.newGroup(self.instId, self.matchingId, self.matchingId3, groupId, i,
                                  groupName, self.stageIndex, isGrouping,
                                  self.matching.startPlayerCount)
            group.addPlayers(groupPlayerList)
            self._groupMap[groupId] = group

        # 启动所有分组
        for group in self._groupMap.values():
            # 启动分组
            group.startHeart()

        self._state = MatchStageCtrl.ST_START

    def finalStage(self):
        '''
        完成该阶段
        '''
        for group in self._groupMap.values():
            # 终止分组
            group.finalGroup()

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

    def _isAllGroupFinish(self):
        if self._logger.isDebug():
            self._logger.debug('MatchStageCtrl._isAllGroupFinish',
                               'state=', self._state,
                               'groups=', self._groupMap.keys())
        for group in self._groupMap.values():
            if group.state < MatchGroup.ST_FINISH:
                return False
        return True

    def _processStage(self):
        if self._logger.isDebug():
            self._logger.debug('MatchStageCtrl._processStage',
                               'state=', self._state)

        if self._state == MatchStageCtrl.ST_START:
            if self._isAllGroupFinish():
                self._state = MatchStageCtrl.ST_FINISH


class Matching(HeartbeatAble):
    '''
    一个发奖单元
    '''
    ST_IDLE = 0
    ST_START = 1
    ST_FINISH = 2

    HEARTBEAT_INTERVAL = 2

    def __init__(self, master, instId, matchingId, matchingId3, signers):
        super(Matching, self).__init__(1)
        # 主控对象
        self.master = master
        # 比赛实例ID
        self.instId = instId
        self.matchingId = matchingId
        self.matchingId3 = matchingId3

        self._signers = signers
        # 状态
        self._state = Matching.ST_IDLE
        # 所有阶段
        self._stages = None
        # 当前阶段
        self._stage = None
        # 开赛时的人数
        self._startPlayerCount = 0

        # 日志
        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('instId', self.instId)
        self._logger.add('matchingId', self.matchingId)
        if self.matchingId3:
            self._logger.add('matchingId3', self.matchingId3)

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

    @property
    def signers(self):
        return self._signers

    def findFirstStage(self, signerCount):
        if self.matchConf.start.selectFirstStage:
            for stage in self._stages:
                if signerCount > stage.stageConf.riseUserCount:
                    return stage
        return self._stages[0]

    def signersToPlayers(self, signers):
        ret = []
        for i, signer in enumerate(signers):
            player = self.master.matchFactory.newPlayer(signer)
            player.playerNo = i + 1
            ret.append(player)
        return ret

    def _createStages(self, stageConfs):
        ret = []
        for stageConf in stageConfs:
            stage = MatchStageCtrl(self, stageConf)
            ret.append(stage)
        return ret

    def _doInit(self):
        self._state = Matching.ST_START

        # 根据人数找到最合适的第一阶段
        self._stages = self._createStages(self.matchConf.stages)
        self._startPlayerCount = len(self._signers)
        self._stage = self.findFirstStage(self._startPlayerCount)

        self._logger.info('Matching._doInit ...',
                          'state=', self._state,
                          'userCount=', self._startPlayerCount,
                          'firstStageIndex=', self._stage.stageIndex)

        playerList = self.signersToPlayers(self._signers)
        self._stage.startStage(playerList)

        self._logger.info('Matching._doInit ok',
                          'state=', self._state,
                          'userCount=', self._startPlayerCount,
                          'firstStageIndex=', self._stage.stageIndex)
        return 1

    def _doHeartbeat(self):
        if self._logger.isDebug():
            self._logger.debug('Matching._doHeartbeat',
                               'state=', self._state,
                               'stageIndex=', self._stage.stageIndex if self._stage else None)
        if self._stage and self._state == Matching.ST_START:
            self._stage._processStage()

        if self._stage and self._stage.state == MatchStageCtrl.ST_FINISH:
            self._startNextStage()

        return Matching.HEARTBEAT_INTERVAL

    def _startNextStage(self):
        playerList = self._stage.getAllRisePlayerList()
        nextStage = self._getNextStage(self._stage)
        self._logger.hinfo('Matching._startNextStage',
                           'state=', self._state,
                           'stageIndex=', self._stage.stageIndex,
                           'nextStageIndex=', nextStage.stageIndex if nextStage else None,
                           'nextStageState=', nextStage.state if nextStage else None,
                           'playerCount=', len(playerList))
        self._stage.finalStage()
        if nextStage:
            self._stage = nextStage
            self._stage.startStage(playerList)
        else:
            self._doFinish()

    def _getNextStage(self, stage):
        nextStageIndex = stage.stageIndex + 1
        if nextStageIndex < len(self._stages):
            return self._stages[nextStageIndex]
        return None

    def _doFinish(self):
        self._state = Matching.ST_FINISH
        self._logger.info('Matching._doFinish ...',
                          'state=', self._state)
        self.stopHeart()
        self._logger.info('Matching._doFinish ok',
                          'state=', self._state)


class MatchMaster(HeartbeatAble):
    ST_IDLE = 0
    ST_ALL_AREA_ONLINE = 1
    ST_LOAD = 2

    HEARTBEAT_TO_AREA_INTERVAL = 5

    def __init__(self, room, matchConf):
        super(MatchMaster, self).__init__(1)
        self.matchId = matchConf.matchId
        # 所在房间
        self.room = room
        # 比赛配置
        self.matchConf = matchConf
        # value=MatchArea
        self._areas = []
        # key=roomId, value=MatchArea
        self._areaMap = {}
        # inst
        self._instCtrl = None
        # 状态
        self._state = MatchMaster.ST_IDLE
        # 所有进行的比赛
        self._matchingMap = {}
        # 最后心跳到分赛区的时间
        self._lastHeartbeatToAreaTime = 0

        self._logger = Logger()
        self._logger.add('matchId', self.matchId)
        self._logger.add('roomId', self.roomId)

    @property
    def areas(self):
        return self._areas

    @property
    def areaCount(self):
        return len(self._areas)

    @property
    def roomId(self):
        return self.room.roomId

    @property
    def gameId(self):
        return self.room.gameId

    def findArea(self, roomId):
        return self._areaMap.get(roomId)

    def addArea(self, area):
        if not self.matchConf.start.isUserCountType():
            # 人满开赛不支持分组，只能有一个Local赛区
            assert (len(self._areaMap) == 0)
            assert (isinstance(area, MatchAreaLocal))
        else:
            assert (not self.findArea(area.roomId))
        self._areaMap[area.roomId] = area
        self._areas.append(area)

    def _doInit(self):
        assert (self._areas)
        for area in self._areas:
            area.startHeart()
        return 1

    def _startMatching(self, instCtrl, num, signers):
        matchingId = '%s.%s' % (instCtrl.instId, num)
        matchingId3 = None
        if self.matchConf.matchId3:
            sequence = self.matchStatusDao.getNextMatchingSequence(self.matchConf.matchId3)
            matchingId3 = '%s%06d' % (self.matchConf.matchId3, sequence)
        matching = Matching(self, instCtrl.instId, matchingId, matchingId3, signers)
        self._matchingMap[matchingId] = matching
        self._logger.info('MatchMaster._startMatching ...',
                          'matchingId=', matchingId,
                          'matchingId3=', matchingId3,
                          'signerCount=', len(signers))

        matching.startHeart()

        if self._logger.isDebug():
            self._logger.debug('MatchMaster._startMatching',
                               'matchingId=', matchingId,
                               'matchingId3=', matchingId3,
                               'signers=', [signer.userId for signer in signers])

        self._logger.info('MatchMaster._startMatching ok',
                          'matchingId=', matchingId,
                          'matchingId3=', matchingId3,
                          'signerCount=', len(signers))

    def _setupNextInst(self, instCtrl, signers, matchingCount):
        timestamp = pktimestamp.getCurrentTimestamp()
        startTime = self.matchConf.start.calcNextStartTime(timestamp + 1)
        if startTime or self.matchConf.start.isUserCountType():
            status = MatchStatus(self.matchId, instCtrl.status.sequence + matchingCount, startTime)
            self.matchStatusDao.save(status)
            self._instCtrl = MatchInstCtrl(self, status, False, signers)
            self._instCtrl.startHeart()
            roomInfo = self._buildRoomInfo()
            if self._logger.isDebug():
                self._logger.debug('MatchMaster._setupNextInst saveRoomInfo',
                                   'roomInfo=', roomInfo.toDict())
            roominfo.saveRoomInfo(self.gameId, roomInfo)
        else:
            assert (not signers)
            self._instCtrl = None
            roominfo.removeRoomInfo(self.gameId, self.roomId)
        self._logger.info('MatchMaster._setupNextInst ok',
                          'instId=', instCtrl.instId,
                          'timestamp=', timestamp,
                          'matchingCount=', matchingCount,
                          'nextInstId=', self._instCtrl.instId if self._instCtrl else None,
                          'startTime=', self._instCtrl.startTime if self._instCtrl else None,
                          'signinTime=', self._instCtrl.signinTime if self._instCtrl else None,
                          'signers=', [s.userId for s in signers] if signers else None)
        return self._instCtrl

    def _isAllAreaOnline(self):
        for area in self._areas:
            if not area.isOnline():
                return False
        return True

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
                instCtrl = MatchInstCtrl(self, status, needLoad, None)
                instCtrl.startHeart()
                instCtrl.cancel(MatchFinishReason.OVERTIME)
                status = MatchStatus(self.matchId, status.sequence + 1, startTime)
            else:
                needLoad = True
            status.startTime = startTime
        else:
            status = MatchStatus(self.matchId, 1, startTime)

        self.matchStatusDao.save(status)

        roominfo.removeRoomInfo(self.gameId, self.roomId)

        if status.startTime or self.matchConf.start.isUserCountType():
            self._instCtrl = MatchInstCtrl(self, status, needLoad, None)
            self._instCtrl.startHeart()
            roomInfo = self._buildRoomInfo()
            roominfo.saveRoomInfo(self.gameId, roomInfo)

        self._logger.info('MatchMaster._doLoad ok',
                          'state=', self._state,
                          'instId=', self._instCtrl.instId if self._instCtrl else None,
                          'startTime=', datetime.fromtimestamp(self._instCtrl.startTime).strftime(
                '%Y-%m-%d %H:%M:%S') if self._instCtrl.startTime else None)

    def _processMatching(self):
        if self._matchingMap:
            matchingList = list(self._matchingMap.values())
            for matching in matchingList:
                if matching.state == Matching.ST_FINISH:
                    del self._matchingMap[matching.matchingId]
                    self._logger.info('MatchMaster._processMatching matchingFinished',
                                      'matchingId=', matching.matchingId)

    def _calcMatchingPlayerCount(self):
        ret = 0
        for area in self._areaMap.values():
            for group in area.groupMap.values():
                ret += group.playerCount
        return ret

    def _buildRoomInfo(self):
        roomInfo = MatchRoomInfo()
        roomInfo.roomId = strutil.getBigRoomIdFromInstanceRoomId(self.roomId)
        roomInfo.playerCount = self._calcMatchingPlayerCount()
        roomInfo.signinCount = self._instCtrl.calcTotalSignerCount() if self._instCtrl else 0
        roomInfo.startType = self.matchConf.start.type
        roomInfo.instId = self._instCtrl.instId if self._instCtrl else None
        roomInfo.fees = []
        if self.matchConf.fees:
            for fee in self.matchConf.fees:
                roomInfo.fees.append(TYContentItem(fee.assetKindId, fee.count))
        if self._instCtrl and self.matchConf.start.isTimingType():
            roomInfo.startTime = self._instCtrl.startTime
        return roomInfo

    def _heartbeatToAllArea(self):
        if self._logger.isDebug():
            self._logger.debug('MatchMaster._heartbeatToAllArea')

    def _doHeartbeat(self):
        timestamp = pktimestamp.getCurrentTimestamp()
        if self._logger.isDebug():
            self._logger.debug('MatchMaster._doHeartbeat',
                               'timestamp=', timestamp,
                               'areaCount=', self.areaCount,
                               'matchingCount=', len(self._matchingMap))
        if self._state == MatchMaster.ST_IDLE:
            if self._isAllAreaOnline():
                self._state = MatchMaster.ST_ALL_AREA_ONLINE
                self._logger.info('MatchMaster._doHeartbeat allAreaOnline',
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
                                       'roomInfo=', roomInfo.toDict())
                roominfo.saveRoomInfo(self.gameId, roomInfo)
        return 1
