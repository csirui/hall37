# -*- coding:utf-8 -*-
'''
Created on 2014年9月23日

@author: zjgzzz@126.com
'''
import functools
import time

from datetime import datetime

import freetime.util.log as ftlog
import poker.entity.events.tyeventbus as pkeventbus
from freetime.core.timer import FTTimer, FTLoopTimer
from poker.entity.biz.content import TYContentItem
from poker.entity.configure import gdata
from poker.entity.dao import sessiondata, onlinedata
from poker.entity.events.tyevent import MatchPlayerSigninEvent, \
    MatchPlayerSignoutEvent, MatchPlayerOverEvent
from poker.entity.game.rooms import roominfo
from poker.entity.game.rooms.big_match_ctrl.const import MatchFinishReason, \
    FeesType, StageType, GroupingType, WaitReason
from poker.entity.game.rooms.big_match_ctrl.exceptions import \
    MatchExpiredException, AlreadySigninException, MatchAlreadyStartedException, \
    SigninStoppedException, SigninNotStartException, AlreadyInMatchException, \
    SigninFullException
from poker.entity.game.rooms.big_match_ctrl.interfaces import MatchStatus
from poker.entity.game.rooms.big_match_ctrl.models import Table, Player
from poker.entity.game.rooms.big_match_ctrl.utils import PlayerSort, \
    PlayerGrouping, PlayerChipCalc, PlayerQueuing, Utils
from poker.entity.game.rooms.roominfo import MatchRoomInfo
from poker.util import strutil


class TableManager(object):
    def __init__(self, gameId, tableSeatCount):
        self._gameId = gameId
        self._tableSeatCount = tableSeatCount
        self._idleTables = []
        self._allTableMap = {}
        self._roomIds = set()

    @property
    def tableSeatCount(self):
        return self._tableSeatCount

    def getRoomCount(self):
        return len(self._roomIds)

    def getAllTableCount(self):
        return len(self._allTableMap)

    def getTableCountPerRoom(self):
        return len(self._allTableMap) / max(1, self.getRoomCount())

    def addTables(self, roomId, baseId, count):
        if count > 0:
            self._roomIds.add(roomId)
        for i in xrange(count):
            tableId = baseId + i + 1  # 新框架里tableId 从 1开始计数， 0表示队列。
            table = Table(self._gameId, roomId, tableId, self._tableSeatCount)
            self._idleTables.append(table)
            self._allTableMap[tableId] = table

    def borrowTables(self, count):
        assert (self.idleTableCount() >= count)
        ret = self._idleTables[0:count]
        self._idleTables = self._idleTables[count:]
        return ret

    def returnTables(self, tables):
        for table in tables:
            assert (table.group is None)
            assert (self._allTableMap.get(table.tableId, None) == table)
            assert (table.getPlayingPlayerCount() <= 0)
            self._idleTables.append(table)

    def idleTableCount(self):
        return len(self._idleTables)

    def usedTableCount(self):
        return max(0, self.getAllTableCount() - self.idleTableCount())

    def findTable(self, roomId, tableId):
        return self._allTableMap.get(tableId, None)


class MatchStageFactory(object):
    def newMatchStage(self, matching, conf, index):
        return MatchStage(matching, conf, index)


class MatchGroupFactory(object):
    def newMatchGroup(self, groupId, groupName, playerList):
        return MatchGroup(groupId, groupName, playerList)


class Match(object):
    '''
    赛事
    '''
    STATE_IDLE = 0
    STATE_LOADING = 1
    STATE_LOADED = 2

    def __init__(self, conf):
        self._conf = conf
        self._state = Match.STATE_IDLE
        self._currentInstance = None
        self._matchingInstanceSet = set()
        self._nextInstId = 1
        self._tick = 0
        self._matchStatus = None

        self.tableManager = None
        self.userInfoLoader = None
        self.signinFee = None
        self.playerLocker = None
        self.playerNotifier = None
        self.tableController = None
        self.matchStatusDao = None
        self.signinRecordDao = None
        self.matchRewards = None
        self.playerLocation = None
        self.matchStageFactory = MatchStageFactory()
        self.matchGroupFactory = MatchGroupFactory()

        self._heartBesatInterval = 1
        self._roomInfoTimer = None

    @property
    def gameId(self):
        return self._conf.gameId

    @property
    def matchId(self):
        return self._conf.matchId

    @property
    def conf(self):
        return self._conf

    @property
    def roomId(self):
        return self._conf.roomId

    @property
    def tableId(self):
        return self._conf.tableId

    @property
    def seatId(self):
        return self._conf.seatId

    @property
    def currentInstance(self):
        return self._currentInstance

    @property
    def tableSeatCount(self):
        return self.tableManager.tableSeatCount

    @property
    def tick(self):
        return Utils.timestamp()

    def getMatchingPlayerCount(self):
        count = 0
        for inst in self._matchingInstanceSet:
            count += inst.getMatchingPlayerCount()
        return count

    def signin(self, userId, signinParams, feeIndex=0):
        '''
        比赛报名
        '''
        if self._currentInstance:
            return self._currentInstance.signin(userId, feeIndex, signinParams)
        else:
            ftlog.warn('Match.signin matchId=', self.matchId,
                       'userId=', userId,
                       'feeIndex=', feeIndex,
                       'signinParams=', signinParams,
                       'match expired')
            raise MatchExpiredException(self.matchId)

    def signout(self, userId):
        '''
        退赛
        '''
        if self._currentInstance:
            self._currentInstance.signout(userId)
        else:
            ftlog.error('Match.signout matchId=', self.matchId,
                        'userId=', userId, 'match expired')
            raise MatchExpiredException(self.matchId)

    def giveup(self, userId):
        player = self.findMatchingPlayer(userId)
        if not player:
            ftlog.warn('Match.giveup matchId=', self.matchId,
                       'err=', 'NotFoundPlayer')
            return False

        if ftlog.is_debug():
            ftlog.debug('Match.giveup matchId=', self.matchId,
                        'userId=', userId,
                        'player=', player)

        if not player.group:
            ftlog.debug('Match.giveup matchId=', self.matchId,
                        'userId=', userId,
                        'player=', player)
            return False

        group = player.group
        group.stage.giveup(group, player)
        return True

    def winlose(self, tableId, ccrc, seatId, userId, deltaChip, isWin):
        player = self.findMatchingPlayer(userId)

        if ftlog.is_debug():
            ftlog.debug('Match.winlose matchId=', self.matchId,
                        'tableId=', tableId, 'ccrc=', ccrc, 'seatId=', seatId,
                        'userId=', userId, 'deltaChip=', deltaChip,
                        'isWin=', isWin)
        if not player:
            ftlog.error('Match.winlose matchId=', self.matchId,
                        'tableId=', tableId, 'ccrc=', ccrc, 'seatId=', seatId,
                        'userId=', userId, 'deltaChip=', deltaChip,
                        'isWin=', isWin, 'error=', 'NotFoundPlayer')
            return None
        if not player.group:
            ftlog.error('Match.winlose matchId=', self.matchId,
                        'tableId=', tableId, 'ccrc=', ccrc, 'seatId=', seatId,
                        'userId=', userId, 'deltaChip=', deltaChip,
                        'isWin=', isWin, 'error=', 'NoGroup')
            return None
        if player.state != Player.STATE_PLAYING:
            ftlog.error('Match.winlose matchId=', self.matchId,
                        'userId=', userId, 'deltaChip=', deltaChip,
                        'isWin=', isWin, 'error=', 'BadState',
                        'state=', player.state, 'expect=', Player.STATE_PLAYING)
            return None
        if not player.seat:
            ftlog.error('Match.winlose matchId=', self.matchId,
                        'tableId=', tableId, 'ccrc=', ccrc, 'seatId=', seatId,
                        'userId=', userId, 'deltaChip=', deltaChip,
                        'isWin=', isWin, 'error=', 'NotInSeat')
            return None
        if player.seat.seatId != seatId:
            ftlog.error('Match.winlose matchId=', self.matchId,
                        'tableId=', tableId, 'ccrc=', ccrc, 'seatId=', seatId,
                        'userId=', userId, 'deltaChip=', deltaChip,
                        'isWin=', isWin, 'error=', 'DiffSeat',
                        'diffSeat=', player.seat.seatId)
            return None
        if player.seat.table.tableId != tableId:
            ftlog.error('Match.winlose matchId=', self.matchId,
                        'tableId=', tableId, 'ccrc=', ccrc, 'seatId=', seatId,
                        'userId=', userId, 'deltaChip=', deltaChip,
                        'isWin=', isWin, 'error=', 'DiffTable'
                                                   'diffTable=', player.seat.table.tableId)
            return None

        if player.seat.table.ccrc != ccrc:
            ftlog.error('Match.winlose matchId=', self.matchId,
                        'tableId=', tableId, 'ccrc=', ccrc, 'seatId=', seatId,
                        'userId=', userId, 'deltaChip=', deltaChip,
                        'isWin=', isWin, 'error=', 'DiffCCRC',
                        'diffCCRC=', player.seat.table.ccrc)
            return None
        group = player.group
        group.stage.winlose(group, player, deltaChip, isWin)
        return player

    def enter(self, userId):
        if not self._currentInstance:
            return False
        player = self.findMatchingPlayer(userId)
        if player:
            return False
        return self._currentInstance.enter(userId)

    def leave(self, userId):
        if not self._currentInstance:
            # TODO log
            return False
        player = self.findMatchingPlayer(userId)
        if player:
            return False
        if self._currentInstance.conf.start.isUserCountType():
            return self._currentInstance.signout(userId)
        else:
            return self._currentInstance.leave(userId)

    def findPlayer(self, userId):
        if self._currentInstance:
            found = self._currentInstance.playerMap.get(userId, None)
            if found:
                return found
        return self.findMatchingPlayer(userId)

    def findMatchingPlayer(self, userId):
        '''
        查找正在比赛的玩家
        '''
        for inst in self._matchingInstanceSet:
            found = inst.findMatchingPlayer(userId)
            if found:
                return found
        return None

    def setHeartBeatInterval(self, interval):
        self._heartBesatInterval = interval

    def doHeartBeat(self):
        assert (self._state >= Match.STATE_LOADED)
        if self._currentInstance:
            try:
                self._currentInstance.doHeartBeat()
            except:
                ftlog.error()

        # 所有比赛实例心跳
        if self._matchingInstanceSet:
            matchingInstanceList = list(self._matchingInstanceSet)
            for inst in matchingInstanceList:
                try:
                    inst.doHeartBeat()
                except:
                    ftlog.error()

        FTTimer(self._heartBesatInterval, self.doHeartBeat)

    def load(self):
        assert (Match.STATE_IDLE == self._state)
        self._state = Match.STATE_LOADING
        ftlog.info('Match.load loading matchId=', self.matchId)

        timestamp = Utils.timestamp()
        matchStatus = self.matchStatusDao.load(self.matchId)
        if matchStatus and matchStatus.matchId != self.matchId:
            matchStatus = None

        if matchStatus:
            self._currentInstance = self._load(matchStatus, timestamp)
        else:
            matchStatus = MatchStatus(self.matchId, 0, None)

        self._matchStatus = matchStatus

        roominfo.removeRoomInfo(self.gameId, gdata.getBigRoomId(self.roomId))

        if not self._currentInstance:
            self._matchStatus.sequence += 1
            self._currentInstance = self._createInstance(matchStatus, timestamp)
            if self._currentInstance:
                self.matchStatusDao.save(matchStatus)
        if self._currentInstance:
            ftlog.info('Match.load loaded matchId=', self.matchId, 'instId=', self._currentInstance.instId)
        else:
            ftlog.info('Match.load loaded matchId=', self.matchId, 'None inst')

        self._state = Match.STATE_LOADED

        self._roomInfoTimer = FTLoopTimer(5, -1, self._doRoomInfoUpdate)
        FTTimer(self._heartBesatInterval, self.doHeartBeat)
        self._roomInfoTimer.start()

    def fillPlayer(self, player):
        userName, sessionClientId, snsId = self.userInfoLoader.loadUserAttrs(player.userId,
                                                                             ['name', 'sessionClientId', 'snsId'])

        snsId = strutil.ensureString(snsId)
        player.userName = strutil.ensureString(userName)
        player.clientId = strutil.ensureString(sessionClientId)
        player.snsId = snsId
        return player

    def _calcMatchingPlayerCount(self):
        ret = 0
        if self._matchingInstanceSet:
            for inst in self._matchingInstanceSet:
                ret += len(inst.playerMap)
        return ret

    def _calcTotalSignerCount(self):
        return len(self._currentInstance.playerMap) if self._currentInstance else 0

    def _buildRoomInfo(self):
        roomInfo = MatchRoomInfo()
        roomInfo.roomId = gdata.getBigRoomId(self.roomId)
        roomInfo.playerCount = self._calcMatchingPlayerCount()
        roomInfo.signinCount = self._calcTotalSignerCount()
        roomInfo.startType = self.conf.start.type
        roomInfo.instId = self._currentInstance.instId if self._currentInstance else None
        roomInfo.fees = []
        if self.conf.fees:
            for fee in self.conf.fees:
                roomInfo.fees.append(TYContentItem(fee.assetKindId, fee.count))
        if self._currentInstance and self._currentInstance.conf.start.isTimingType():
            roomInfo.startTime = self._currentInstance.startTime
        return roomInfo

    def _doRoomInfoUpdate(self):
        roomInfo = self._buildRoomInfo()
        if ftlog.is_debug():
            ftlog.debug('Match._doRoomInfoUpdate matchId=', self.matchId,
                        'roomId=', self.roomId,
                        'roomInf=', roomInfo.__dict__)
        roominfo.saveRoomInfo(self.gameId, roomInfo)

    def _load(self, matchStatus, timestamp):
        if matchStatus is not None:
            # 检查是否超时
            if (not self._conf.start.isTimingType()):
                self._cancelMatch(matchStatus)
                return None

            startTime = self._conf.start.calcNextStartTime(timestamp)
            if startTime != matchStatus.startTime:
                # 比赛已经超时或开赛时间有变化
                self._cancelMatch(matchStatus)
                return None
            # 加载
            inst = self._createInstance(matchStatus, timestamp)
            records = self.signinRecordDao.load(matchStatus.matchId, matchStatus.instId)
            for record in records:
                player = Player(inst, record[0], '', record[1], 0, '')
                self.fillPlayer(player)
                player.signinParams = record[2]
                inst._addPlayers([player])
            return inst
        return None

    def _createInstance(self, matchStatus, timestamp):
        inst = None
        if not self._conf.start.isTimingType():
            inst = MatchInstance(self, matchStatus.instId, self._conf)
            inst._state = MatchInstance.STATE_SIGNIN
        else:
            if matchStatus.startTime is None:
                matchStatus.startTime = self._conf.start.calcNextStartTime(timestamp)
            if matchStatus.startTime is not None:
                inst = MatchInstance(self, matchStatus.instId, self._conf)
                inst._startTime = matchStatus.startTime
                inst._signinTime = self._conf.start.calcSigninTime(matchStatus.startTime)
                inst._signinTimeStr = self._conf.start.buildSigninTimeStr()
                inst._startTimeStr = datetime.fromtimestamp(matchStatus.startTime).strftime('%Y-%m-%d %H:%M')
                inst._prepareTime = self._conf.start.calcPrepareTime(inst._startTime)
                if not inst._signinTime or timestamp >= inst._signinTime:
                    inst._state = MatchInstance.STATE_SIGNIN
        ftlog.info('Match._createInstance matchId=', self.matchId,
                   'instId=', matchStatus.instId,
                   'startTime=', matchStatus.startTime,
                   'inst=', inst)
        return inst

    def _cancelMatch(self, matchStatus):
        ftlog.info('Match._cancelMatch matchId=', matchStatus.matchId,
                   'instId=', matchStatus.instId,
                   'startTime=', matchStatus.startTime)
        matchStatus.startTime = None
        if self._conf.fees:
            records = self.signinRecordDao.load(matchStatus.matchId, matchStatus.instId)
            for record in records:  # TODO: 延迟60秒退费，为了等待进程启动完毕在执行，否则会导致启动失败
                func = functools.partial(self.signinFee.returnFees, matchStatus.instId, record[0], self._conf.fees)
                FTTimer(60, func)
        self.signinRecordDao.removeAll(matchStatus.matchId, matchStatus.instId)

    def setupNextInstance(self, timestamp=None):
        tmp = self._currentInstance
        self._matchStatus.sequence += 1
        self._matchStatus.startTime = None
        timestamp = timestamp or Utils.timestamp()
        self._currentInstance = self._createInstance(self._matchStatus, timestamp + 1)
        if tmp:
            self._matchingInstanceSet.add(tmp)
            self.signinRecordDao.removeAll(tmp.matchId, tmp.instId)

        if self._currentInstance is None:
            self._hasNextInstance = False
        else:
            self.matchStatusDao.save(self._matchStatus)
            ftlog.info('Match.setupNextInstance matchId=', self.matchId,
                       'instId=', self._currentInstance.instId)

    def _finishInstance(self, inst):
        self._matchingInstanceSet.remove(inst)
        ftlog.info('Match._finishInstance matchId=', self.matchId,
                   'instId=', inst.instId)


class SigninState(object):
    STATE_IDLE = 0
    STATE_SIGNIN = 1
    STATE_STOP = 2


class MatchInstance(object):
    '''
    一个赛事实例
    '''
    STATE_IDLE = 0
    STATE_SIGNIN = 1
    STATE_PREPARE = 2
    STATE_STARTING = 4
    STATE_STARTED = 5
    STATE_FINISH = 6
    STATE_FINAL = 7

    def __init__(self, match, instId, conf):
        self._match = match
        self._instId = instId
        self._conf = conf
        self._playerMap = {}

        self._matchingSet = set()

        self._state = MatchInstance.STATE_IDLE

        # 开始时间(定时赛时有效)
        self._startTime = None
        self._startTimeStr = ''
        # 报名时间(定时赛时有效)
        self._signinTime = None
        self._signinTimeStr = ''
        # 准备时间
        self._prepareTime = None

        self._finishedReason = None

    @property
    def instId(self):
        return self._instId

    @property
    def matchId(self):
        return self._match.matchId

    @property
    def match(self):
        return self._match

    @property
    def conf(self):
        return self._conf

    @property
    def state(self):
        return self._state

    @property
    def startTime(self):
        return self._startTime

    @property
    def startTimeStr(self):
        return self._startTimeStr

    @property
    def playerMap(self):
        return self._playerMap

    def getMatchingPlayerCount(self):
        count = 0
        for matching in self._matchingSet:
            count += matching.getMatchingPlayerCount()
        return count

    def signin(self, userId, feeIndex, signinParams):
        # 确认能报名
        self._ensureCanSignin(userId)

        # 收取报名费
        self._collectFees(userId)

        # 收费过程中可能其它tasklet已经报名了，所以此处需要检查
        if userId in self._playerMap:
            self._returnFees(userId)
            raise AlreadySigninException(self.matchId)

        # 收费过程中比赛可能已经开始了, 所以此处需要退费
        if self._state >= MatchInstance.STATE_STARTING:
            self._returnFees(userId)
            raise MatchAlreadyStartedException(self.matchId)

        # 记录报名用户
        ts = Utils.timestamp()
        player = Player(self, userId, '', ts, ts, '')
        player.isenter = True
        player.signinParams = signinParams
        self._playerMap[userId] = player

        ftlog.info('MatchInstance.signin successed matchId=', self.matchId,
                   'instId=', self._instId,
                   'userId=', userId,
                   'signinParams=', signinParams,
                   'signinUserCount=', len(self._playerMap))

        self._match.signinRecordDao.recordSignin(self.match.matchId, self.instId, userId, ts, signinParams)
        self.match.fillPlayer(player)
        pkeventbus.globalEventBus.publishEvent(MatchPlayerSigninEvent(userId, self.match.gameId, self.matchId, player))
        return player

    def signout(self, userId):
        player = self._playerMap.get(userId)
        if player:
            if self._state != MatchInstance.STATE_SIGNIN:
                raise SigninStoppedException(self.matchId)

            # 删除报名记录
            del self._playerMap[userId]

            ftlog.info('MatchInstance.singout successed matchId=', self.matchId,
                       'instId=', self._instId,
                       'userId=', userId,
                       'signinUserCount=', len(self._playerMap))

            # 退费
            self._match.signinFee.returnFees(self, userId, self._conf.fees)
            self._match.signinRecordDao.removeSignin(self.match.matchId, self.instId, userId)
            pkeventbus.globalEventBus.publishEvent(
                MatchPlayerSignoutEvent(userId, self.match.gameId, self.matchId, player))
            return True
        return False

    def enter(self, userId):
        assert (self._state < MatchInstance.STATE_STARTING)
        player = self._playerMap.get(userId)
        if player and not player.isenter:
            player.isenter = True
            player.activeTime = time.time()
            sessionClientId = sessiondata.getClientId(userId)
            player.clientId = sessionClientId or ''
            ftlog.info('MatchInstance.enter matchId=', self.matchId,
                       'instId=', self._instId,
                       'userId=', userId,
                       'signinUserCount=', len(self._playerMap))
        return True

    def leave(self, userId):
        assert (self._state < MatchInstance.STATE_STARTING)
        player = self._playerMap.get(userId, None)
        if player:
            player.locked = False
            player.isenter = False
            player.activeTime = time.time()
            ftlog.info('MatchInstance.leave matchId=', self.matchId,
                       'instId=', self._instId,
                       'userId=', userId,
                       'signinUserCount=', len(self._playerMap))

    def findMatchingPlayer(self, userId):
        '''
        查找所有的
        '''
        return self._playerMap.get(userId)

    def doHeartBeat(self):
        timestamp = Utils.timestamp()
        #         if ftlog.is_debug():
        #             ftlog.debug('MatchInstance.doHeartBeat matchId=', self.matchId,
        #                                   'instId=', self._instId,
        #                                   'state=', self._state,
        #                                   'userCount=', len(self._playerMap),
        #                                   'startTime=', self._startTime,
        #                                   'nowTime=', timestamp,
        #                                   'idleTableCount=', self.match.tableManager.idleTableCount())

        if MatchInstance.STATE_IDLE == self._state:
            assert (self._signinTime)
            if timestamp >= self._signinTime:
                self._doStartSignin()
            return

        if MatchInstance.STATE_SIGNIN == self._state:
            if self._startTime is not None:
                if timestamp >= self._prepareTime:
                    self._doPrepare()
                if timestamp >= self._startTime:
                    self._doStart()
            elif len(self._playerMap) >= self._conf.start.userCount:
                self._doStart()
            return

        if MatchInstance.STATE_PREPARE == self._state:
            assert (self._startTime)
            if timestamp >= self._startTime:
                self._doStart()
            return

        if MatchInstance.STATE_STARTED == self._state:
            matchings = list(self._matchingSet)
            for matching in matchings:
                matching.doHeartBeat()

    def _moveTo(self, players, toInst):
        if players:
            ts = Utils.timestamp()
            for player in players:
                if player.locked:
                    self._unlockPlayer(player)
                del self._playerMap[player.userId]
                self._match.signinRecordDao.removeSignin(self.match.matchId, self.instId, player.userId)
                newPlayer = Player(toInst, player.userId, player.userName, player.signinTime, ts, player.clientId)
                newPlayer.isenter = True
                newPlayer.signinParams = player.signinParams
                newPlayer.snsId = player.snsId
                toInst._playerMap[player.userId] = newPlayer
                self._match.signinRecordDao.recordSignin(self.match.matchId, self.instId, player.userId, ts,
                                                         player.signinParams)
                ftlog.info('MatchInstance._moveTo userId=', newPlayer.userId,
                           'fromInst=', self._instId, 'toInst=', toInst._instId)

    def _doStart(self):
        assert (self._state <= MatchInstance.STATE_STARTING)

        # 状态变为启动中
        self._state = MatchInstance.STATE_STARTING
        self._startTime = Utils.timestamp()

        ftlog.hinfo('MatchInstance._doStart starting matchId=', self.matchId,
                    'instId=', self.instId,
                    'signinUserCount=', len(self._playerMap))

        # 准备下一场比赛
        self._match.setupNextInstance()

        # 比赛人数不足
        if (not self._isPlayersEnough(len(self._playerMap))):
            ftlog.info('MatchInstance._doStart aborted matchId=', self.matchId,
                       'instId=', self._instId,
                       'signinUserCount=', len(self._playerMap),
                       'reason=', MatchFinishReason.USER_NOT_ENOUGH)
            if self._conf.start.isUserCountType() and self._match.currentInstance:
                # 报名下一场
                self._moveTo(self._playerMap.values()[:], self._match.currentInstance)
            self._doStartAbort(self._playerMap.values()[:], MatchFinishReason.USER_NOT_ENOUGH)
            return

        # 锁定玩家
        self._lockPlayers(self._playerMap.values())

        if not self._isPlayersEnough(len(self._playerMap)):
            ftlog.info('MatchInstance._doStart aborted matchId=', self.matchId,
                       'instId=', self._instId,
                       'lockedUserCount=', len(self._playerMap),
                       'reason=', MatchFinishReason.USER_NOT_ENOUGH)
            if self._conf.start.isUserCountType() and self._match.currentInstance:
                # 报名下一场
                self._moveTo(self._playerMap.values()[:], self._match.currentInstance)
            self._doStartAbort(self._playerMap.values()[:], MatchFinishReason.USER_NOT_ENOUGH)
            return

        onlinePlayers = sorted(self._playerMap.values(), PlayerSort.cmpBySigninTime)

        grouppedPlayerList = self._groupingPlayers(onlinePlayers)

        if self._conf.start.isUserCountType():
            if len(grouppedPlayerList[-1]) < self._conf.start.userCount:
                if self._match.currentInstance:
                    # 报名下一场
                    self._moveTo(grouppedPlayerList[-1], self._match.currentInstance)
                else:
                    abortUserIds = [p.userId for p in grouppedPlayerList[-1]]
                    ftlog.info('MatchInstance._doStart abortGroup matchId=', self.matchId,
                               'instId=', self._instId,
                               'userCount=', len(grouppedPlayerList[-1]),
                               'minUserCount=', self._conf.start.userCount,
                               'abortUserIds=', abortUserIds)
                    self._doStartAbortPlayers(grouppedPlayerList[-1], MatchFinishReason.USER_NOT_ENOUGH)
                del grouppedPlayerList[-1]

        if len(grouppedPlayerList) <= 0:
            ftlog.info('MatchInstance._doStart aborted matchId=', self.matchId,
                       'instId=', self._instId,
                       'userCount=', 0,
                       'reason=', MatchFinishReason.USER_NOT_ENOUGH)
            self._doStartAbort(None, MatchFinishReason.USER_NOT_ENOUGH)
            return

        for playerList in grouppedPlayerList:
            matching = self._newMatching()
            matching.start(playerList)

        # 启动完成
        ftlog.info('MatchInstance._doStart started matchId=', self.matchId,
                   'instId=', self.instId,
                   'matchingCount=', len(self._matchingSet),
                   'userCount=', len(self._playerMap),
                   'usedTime=', Utils.timestamp() - self._startTime)

        self._state = MatchInstance.STATE_STARTED

    def _newMatching(self):
        matchingId = '%s.%d' % (self._instId, len(self._matchingSet) + 1)
        matching = Matching(self, matchingId, self._conf.stages)
        self._matchingSet.add(matching)
        return matching

    def _finishMatching(self, matching):
        ftlog.info('MatchInstance._finishMatching matchId=', self.matchId,
                   'instId=', self._instId,
                   'matchingId=', matching.matchingId)
        self._matchingSet.remove(matching)
        if len(self._matchingSet) <= 0:
            self._match._finishInstance(self)

    def _doStartAbort(self, playerList, reason):
        self._state = MatchInstance.STATE_FINISH
        if playerList:
            self._doStartAbortPlayers(playerList, reason)
        self._match._finishInstance(self)

    def _doStartSignin(self):
        self._state = MatchInstance.STATE_SIGNIN
        ftlog.info('MatchInstance._doStartSignin matchId=', self.matchId,
                   'instId=', self._instId)

    def _doPrepare(self):
        self._state = MatchInstance.STATE_PREPARE

        # 准备阶段预锁定用户，此处只锁定在报名界面的用户
        if self._isPlayersEnough(len(self._playerMap)):
            self._prelockPlayers(self._playerMap.values())

        ftlog.info('MatchInstance._doPrepare matchId=', self.matchId,
                   'instId=', self._instId)

    def _doStartAbortPlayers(self, playerList, reason):
        for player in playerList:
            # 退费，用户离开比赛后没进入比赛不退报名费
            if (self._conf.fees
                and (self._conf.start.feeType == FeesType.TYPE_RETURN
                     or player.isenter)):
                self._match.signinFee.returnFees(self, player.userId, self._conf.fees)

            if player.isenter:
                # 通知用户
                self._match.playerNotifier.notifyMatchCancelled(player, self, reason)

            if player.locked:
                self._unlockPlayer(player)

            del self._playerMap[player.userId]

    def _setEnterLoc(self, userId):
        gid, rid, tid, sid = self.match.playerLocation.getLocation(userId)
        if ftlog.is_debug():
            ftlog.debug('MatchInstance._setEnterLoc matchId=', self.matchId,
                        'instId=', self.instId,
                        'userId=', userId,
                        'loc=', '%s.%s.%s.%s' % (gid, rid, tid, sid),
                        'target=%s.%s.%s.%s' % (self.match.gameId, self.match.roomId, 0, 0))
        if (gid == self.match.gameId
            and rid == self.match.roomId):
            return True
        if tid != 0 or sid != 0:
            return False
        self.match.playerLocation.setLocationForce(userId, self.match.gameId,
                                                   self.match.roomId,
                                                   0, 0)
        return True

    def _setLeaveLoc(self, userId):
        gid, rid, tid, sid = self.match.playerLocation.getLocation(userId)
        if ftlog.is_debug():
            ftlog.debug('MatchInstance._setEnterLoc matchId=', self.matchId,
                        'instId=', self.instId,
                        'userId=', userId,
                        'loc=', '%s.%s.%s.%s' % (gid, rid, tid, sid),
                        'target=%s.%s.%s.%s' % (self.match.gameId, 0, 0, 0))
        if gid == self.match.gameId and rid == self.match.roomId:
            self.match.playerLocation.setLocationForce(userId,
                                                       self.match.gameId,
                                                       0, 0, 0)

    def _prelockPlayers(self, playerList):
        ftlog.info('MatchInstance._prelockPlayers prelocking matchId=', self.matchId,
                   'instId=', self.instId,
                   'playerLen=', len(playerList))

        lockedCount = 0
        unlockedCount = 0
        noenterCount = 0

        for player in playerList:
            # 只锁定在比赛界面的玩家
            if not player.isenter:
                noenterCount += 1
                continue
            if self._lockPlayer(player):
                lockedCount += 1
            else:
                unlockedCount += 1

        ftlog.info('MatchInstance._prelockPlayers prelocked matchId=', self.matchId,
                   'instId=', self.instId,
                   'playerLen=', len(playerList),
                   'lockedCount=', lockedCount,
                   'noenterCount=', noenterCount,
                   'unlockedCount=', unlockedCount,
                   'prelockCount=', lockedCount)

    def _lockPlayers(self, playerList):
        '''锁定报名用户'''
        nolockPlayerList = []
        for player in playerList:
            if not self._lockPlayer(player):
                nolockPlayerList.append(player)

        self._doStartAbortPlayers(nolockPlayerList, MatchFinishReason.USER_LEAVE)

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

            if onlinedata.getOnlineLocSeatId(player.userId, self.match.roomId, self.match.tableId) == self.match.seatId:
                player.locked = True
                ftlog.info('MatchInstance._lockPlayer successed matchId=', self.matchId,
                           'instId=', self.instId,
                           'userId=', player.userId,
                           'loc=', '%s.%s.%s.%s' % (
                               self.match.gameId, self.match.roomId, self.match.tableId, self.match.seatId))
                if ftlog.is_debug():
                    ftlog.debug("|userId, locList:", player.userId, onlinedata.getOnlineLocList(player.userId),
                                caller=self)
                return True

            onlinedata.addOnlineLoc(player.userId, self.match.roomId, self.match.tableId, self.match.seatId)
            player.locked = True
            if ftlog.is_debug():
                ftlog.debug('MatchInstance._lockPlayer successed matchId=', self.matchId,
                            'instId=', self.instId,
                            'userId=', player.userId,
                            'loc=', '%s.%s.%s.%s' % (
                                self.match.gameId, self.match.roomId, self.match.tableId, self.match.seatId))
            if ftlog.is_debug():
                ftlog.debug("|userId, locList:", player.userId, onlinedata.getOnlineLocList(player.userId), caller=self)
            return True
        except:
            ftlog.error()
            return False

    def _unlockPlayer(self, player):
        try:
            onlinedata.removeOnlineLoc(player.userId, self.match.roomId, self.match.tableId)
            if ftlog.is_debug():
                ftlog.debug('MatchInstance._unlockPlayer successed matchId=', self.matchId,
                            'instId=', self.instId,
                            'userId=', player.userId,
                            'loc=', '%s.0.0.0' % (self.match.gameId))
            if ftlog.is_debug():
                ftlog.debug("|userId, locList:", player.userId, onlinedata.getOnlineLocList(player.userId), caller=self)
        except:
            ftlog.error()
        player.locked = False

    def _unlockPlayers(self, playerList):
        for player in playerList:
            self._unlockPlayer(player)

    def _collectFees(self, userId):
        if self._conf.fees:
            self._match.signinFee.collectFees(self, userId, self._conf.fees)

    def _returnFees(self, userId):
        if self._conf.fees:
            self._match.signinFee.returnFees(self, userId, self._conf.fees)

    def _isPlayersEnough(self, playerCount):
        if (self._conf.start.isTimingType()):
            return playerCount >= self._conf.start.userMinCount
        return playerCount >= self._conf.start.userCount

    def _addPlayers(self, playerList):
        for player in playerList:
            if player.inst != self:
                player.inst = self
            self._playerMap[player.userId] = player

    def _ensureCanSignin(self, userId):
        # 报名还未开始
        if self._state == self.STATE_IDLE:
            msg = u'请在比赛开始前%s，报名参加此比赛' % (self._signinTimeStr)
            raise SigninNotStartException(self.matchId, msg)

        # 报名已经截止
        if self._state == self.STATE_PREPARE:
            raise SigninStoppedException(self.matchId)

        # 比赛已经开始
        if self._state >= self.STATE_STARTING:
            raise MatchAlreadyStartedException(self.matchId)

        # 已经报名
        if userId in self._playerMap:
            raise AlreadySigninException(self.matchId)

        # 已经在该比赛中打比赛
        if self._match.findMatchingPlayer(userId):
            raise AlreadyInMatchException(self.matchId)

        # 检查报名人数是否已满
        if (self._conf.start.isTimingType()
            and len(self._playerMap) >= self._conf.start.userMaxCount):
            raise SigninFullException(self.matchId)

    def _groupingPlayers(self, playerList):
        if self._conf.start.isTimingType():
            groupCount = 1
            if len(playerList) > self._conf.start.userCountPerGroup:
                gfloat = float(len(playerList)) / float(self._conf.start.userCountPerGroup)
                groupCount = int(gfloat)
                gfloat = gfloat - groupCount
                if gfloat > self._conf.start.userNextGroup:
                    groupCount += 1
            return PlayerGrouping.groupingByGroupCount(playerList, groupCount)
        else:
            # 按固定人数分组
            return PlayerGrouping.groupingByFixedUserCountPerGroup(playerList, self._conf.start.userCount)


class MatchStage(object):
    STATE_IDLE = 0
    STATE_SETUP = 1
    STATE_STARTING = 2
    STATE_STARTED = 3
    STATE_FINISHED = 4

    def __init__(self, matching, conf, index):
        self._conf = conf
        # 比赛
        self._matching = matching
        self._stageId = '%s.%s' % (matching.matchingId, index + 1)
        self._index = index
        # 所有组
        self._groupList = None
        # 下一个阶段， 为None表示最后一个阶段
        self._next = None
        # 比赛中的组
        self._matchingGroupSet = None
        # 已经结束的组
        self._finishedGroupSet = None
        self._state = MatchStage.STATE_IDLE

        # 底分
        self._loseBetChip = self._conf.chipBase
        self._growCount = 0
        self._assLoseChip = self._calcASSLoseChip()
        self._lastGrowTime = None

        # 平均每组开赛人数
        self._playerCountPerGroup = 0
        # 晋级人数
        self._totalRisePlayerCount = None

    @property
    def index(self):
        return self._index

    @property
    def name(self):
        return self._conf.name

    @property
    def matching(self):
        return self._matching

    @property
    def matchingId(self):
        return self._matching.matchingId

    @property
    def match(self):
        return self._matching.match

    @property
    def matchId(self):
        return self.match.matchId

    @property
    def matchInst(self):
        return self._matching.matchInst

    @property
    def instId(self):
        return self.matchInst.instId

    @property
    def conf(self):
        return self._conf

    @property
    def next(self):
        return self._next

    @property
    def stageId(self):
        return self._stageId

    @property
    def playerCountPerGroup(self):
        return self._playerCountPerGroup

    @property
    def totalRisePlayerCount(self):
        if self._totalRisePlayerCount is None:
            return self._conf.riseUserCount
        return self._totalRisePlayerCount

    def getLoseBetChip(self):
        return self._loseBetChip

    def getAssLoseChip(self):
        return self._assLoseChip

    def getGroupCount(self):
        return len(self._groupList)

    def getMatchingPlayerCount(self):
        count = 0
        for group in self._groupList:
            count += len(group.rankList)
        return count

    def hasNextStage(self):
        return self._next is not None

    def calcNeedTableCount(self):
        if self._state != MatchStage.STATE_STARTED:
            return -1

        count = 0
        for group in self._groupList:
            count += int((len(group._rankList) + self.match.tableSeatCount - 1) / self.match.tableSeatCount)
        return count

    def findMatchingPlayer(self, userId):
        '''
        查找所有的
        '''
        for group in self._groupList:
            found = group.findMatchingPlayer(userId)
            if found:
                return found
        return None

    def setupStage(self, groups):
        assert (MatchStage.STATE_IDLE == self._state)
        self._state = MatchStage.STATE_SETUP

        ftlog.info('MatchStage.setupStage setuping matchId=', self.matchId,
                   'instId=', self.instId,
                   'matchingId=', self.matchingId,
                   'stageId=', self.stageId,
                   'groupCount=', len(groups))

        self._groupList = groups
        self._matchingGroupSet = set(self._groupList)
        self._finishedGroupSet = set()
        self._lastGrowTime = Utils.timestamp()

        playerCount = 0
        totalRisePlayerCount = 0

        # 初始化用户chip
        for group in self._groupList:
            # 当前阶段
            playerCount += len(group.rankList)
            totalRisePlayerCount += min(len(group.rankList), self._conf.riseUserCount)

            group._stage = self
            group._lastTablePlayTime = Utils.timestamp() + max(10, self.matchInst.conf.start.tableAvgTimes - 20)

            if self.index == 0:
                self.match.playerNotifier.notifyMatchStart(group.rankList, group)
                userIds = [p.userId for p in group.rankList]
                ftlog.hinfo('MatchStage.setupStage setupGroup matchId=', self.match.matchId,
                            'instId=', self.instId,
                            'matchingId=', self.matching.matchingId,
                            'stageId=', self.stageId,
                            'stageIndex=', self.index,
                            'groupId=', group.groupId,
                            'userIds=', userIds)

                # 初始化用户数据
                self._initPlayerDatas(group)

                # 重新排序
                self._sortMatchRanks(group)
            else:
                # 重新排序
                self._sortMatchRanks(group)

                # 初始化用户数据
                self._initPlayerDatas(group)

                # 重新排序
                self._sortMatchRanks(group)

        self._playerCountPerGroup = int(playerCount / len(self._groupList))
        self._totalRisePlayerCount = totalRisePlayerCount
        ftlog.info('MatchStage.setupStage setupped matchId=', self.matchId,
                   'instId=', self.instId,
                   'matchingId=', self.matchingId,
                   'stageId=', self.stageId,
                   'stageIndex=', self.index,
                   'groupCount=', len(groups))

    def _startStage(self):
        assert (MatchStage.STATE_SETUP == self._state)
        self._state = MatchStage.STATE_STARTING
        ftlog.info('MatchStage._startStage starting matchId=', self.matchId,
                   'instId=', self.instId,
                   'matchingId=', self.matchingId,
                   'stageId=', self.stageId,
                   'stageIndex=', self.index,
                   'groupCount=', len(self._groupList))

        for group in self._groupList:
            # 初始化等待列表
            self._initWaitPlayerList(group)

        self._state = MatchStage.STATE_STARTED

        for group in self._groupList:
            for player in group._waitPlayerList:
                self.match.playerNotifier.notifyStageStart(player, group)
                if self._index != 0:
                    self.match.playerNotifier.notifyMatchRank(player, group)

        ftlog.hinfo('MatchStage._startStage started matchId=', self.matchId,
                    'instId=', self.instId,
                    'matchingId=', self.matchingId,
                    'stageId=', self.stageId,
                    'stageIndex=', self.index,
                    'groupCount=', len(self._groupList))

    def winlose(self, group, player, deltaChip, isWin, isKill=False):
        if self._state != MatchStage.STATE_STARTED:
            ftlog.error('MatchStage.winlose matchId=', self.matchId,
                        'instId=', self.instId, 'matchingId=', self.matchingId,
                        'stageId=', self.stageId, 'stageIndex=', self.index,
                        'groupId=', group.groupId, 'userId=', player.userId,
                        'deltaChip=', deltaChip, 'isWin=', isWin,
                        'userState=', player.state,
                        'isKill=', isKill, 'state=', self._state, 'not started')
            return

        player.state = Player.STATE_WINLOSE
        player.chip += int(deltaChip)

        table = player.table

        ftlog.info('MatchStage.winlose matchId=', self.matchId,
                   'instId=', self.instId, 'matchingId=', self.matchingId,
                   'stageId=', self.stageId, 'stageIndex=', self.index,
                   'groupId=', group.groupId, 'userId=', player.userId,
                   'tableId=', table.tableId if table else None,
                   'deltaChip=', deltaChip, 'isWin=', isWin,
                   'userState=', player.state,
                   'isKill=', isKill, 'state=', self._state)
        if not table:
            playerList = [player]

            # 本桌子用户排名
            self._sortTableRank(playerList)

            # 重新排名
            self._sortMatchRanks(group)

            # 添加到完成列表
            group.addWinlosePlayerList(playerList)
        elif table.getPlayingPlayerCount() <= 0:
            playerList = table.getPlayerList()

            # 本桌子用户排名
            self._sortTableRank(playerList)

            # 重新排名
            self._sortMatchRanks(group)

            # 让该桌子上的用户站起
            self._clearTable(table, False)

            # 释放桌子
            self._releaseTable(group, table)

            # 计算group剩余时间
            self._calcLastTablePlayTime(group, table)

            # 添加到完成列表
            group.addWinlosePlayerList(playerList)

            # 改变玩家loc
            for player in playerList:
                try:
                    onlinedata.addOnlineLoc(player.userId, self.match.roomId, self.match.tableId, self.match.seatId)
                    if ftlog.is_debug():
                        ftlog.debug("|userId, locList:", player.userId, onlinedata.getOnlineLocList(player.userId),
                                    caller=self)
                except:
                    ftlog.error()

    def giveup(self, group, player):
        if self._state != MatchStage.STATE_STARTED:
            ftlog.warn('MatchStage.giveup matchId=', self.matchId,
                       'instId=', self.instId, 'matchingId=', self.matchingId,
                       'stageId=', self.stageId, 'stageIndex=', self.index,
                       'groupId=', group.groupId, 'userId=', player.userId,
                       'state=', self._state, 'err=', 'NotStarted')
            return False

        if player.state != Player.STATE_WAIT:
            ftlog.warn('MatchStage.giveup matchId=', self.matchId,
                       'instId=', self.instId, 'matchingId=', self.matchingId,
                       'stageId=', self.stageId, 'stageIndex=', self.index,
                       'groupId=', group.groupId, 'userId=', player.userId,
                       'state=', self._state, 'err=', 'NotWaitState')
            return False

        player.group.addGiveupPlayer(player)
        ftlog.info('MatchStage.giveup giveuped matchId=', self.matchId,
                   'instId=', self.instId, 'matchingId=', self.matchingId,
                   'stageId=', self.stageId, 'stageIndex=', self.index,
                   'groupId=', group.groupId, 'userId=', player.userId)
        return True

    def doHeartBeat(self):
        if ftlog.is_debug():
            ftlog.debug('MatchStage.doHeartBeat matchId=', self.matchId,
                        'instId=', self.instId,
                        'matchingId=', self.matchingId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupCount=', len(self._groupList),
                        'finishedGroupCount=', len(self._finishedGroupSet),
                        'idleTableCount=', self.match.tableManager.idleTableCount())

        if self._state == MatchStage.STATE_SETUP:
            self._startStage()
            return

        if self._state != MatchStage.STATE_STARTED:
            return

        ftlog.info('MatchStage.doHeartBeat matchId=', self.matchId,
                   'instId=', self.instId,
                   'matchingId=', self.matchingId,
                   'stageId=', self.stageId,
                   'stageIndex=', self.index,
                   'groupCount=', len(self._groupList),
                   'finishedGroupCount=', len(self._finishedGroupSet),
                   'idleTableCount=', self.match.tableManager.idleTableCount())

        self._checkGrowLoseBetChip()

        matchingGroups = list(self._matchingGroupSet)
        for group in matchingGroups:
            count = 200
            try:
                maxPlayerPerRoom = self.match.tableManager.getTableCountPerRoom() * self.match.tableSeatCount
                countPerRoom = int((maxPlayerPerRoom / self.matchInst.conf.start.startMatchSpeed + 10) / 10)
                count = self.match.tableManager.getRoomCount() * countPerRoom
            except:
                ftlog.exception()
            self._processGroup(group, max(200, count))
            try:
                if len(group._waitPlayerList) >= self.match.tableSeatCount:
                    self.match.setHeartBeatInterval(0.1)
                # TyContext.getTasklet().reset_heartbeat_interval(0.1)
                else:
                    self.match.setHeartBeatInterval(1)
            except:
                ftlog.exception()
                pass
        if (len(self._finishedGroupSet) >= len(self._groupList)):
            self._finishStage()

    def _calcLastTablePlayTime(self, group, table=None):
        if table and table.playTime < group._lastTablePlayTime:
            return
        playTime = 0
        for table in group._busyTableSet:
            if table.playTime and table.playTime > playTime:
                playTime = table.playTime
        group._lastTablePlayTime = playTime

    def calcRemTimes(self, group):
        timestamp = Utils.timestamp()
        if group not in self._finishedGroupSet:
            return self._calcRemTimesForGroup(group, timestamp)
        else:
            remTimes = 0
            for group in self._matchingGroupSet:
                t = self._calcRemTimesForGroup(group, timestamp)
                remTimes = max(t, remTimes)
            return remTimes

    def calcUncompleteTableCount(self, group):
        if group not in self._finishedGroupSet:
            return self._calcUncompleteTableCount(group)
        else:
            count = 0
            for group in self._finishedGroupSet:
                c = self._calcUncompleteTableCount(group)
                count = max(count, c)
            return count

    def _calcUncompleteTableCount(self, group):
        busyTableCount = len(group._busyTableSet)
        waitUserCount = len(group._waitPlayerList)
        winloseUserCount = len(group._winlosePlayerSet)
        return int(busyTableCount + (waitUserCount + winloseUserCount) / self.matchInst.conf.tableSeatCount)

    def _calcRemTimesForGroup(self, group, timestamp):
        playTime = group._lastTablePlayTime
        waitUserCount = len(group._waitPlayerList)
        winloseUserCount = len(group._winlosePlayerSet)
        waitTableCount = (waitUserCount + winloseUserCount) / self.matchInst.conf.tableSeatCount
        if waitTableCount > 0:
            playTime = timestamp

        if playTime + self.matchInst.conf.start.tableAvgTimes < timestamp:
            playTime = playTime + self.matchInst.conf.start.tableTimes
        else:
            playTime = playTime + self.matchInst.conf.start.tableAvgTimes
        return max(0, playTime - timestamp)

    def _releaseTable(self, group, table):
        # 释放桌子
        assert (table.getIdleSeatCount() == table.seatCount)
        table.group = None
        table.playTime = None
        self._matching.returnTable(table)
        group._busyTableSet.remove(table)

    def _finishGroup(self, group):
        assert (len(group._busyTableSet) == 0)
        if len(group._winlosePlayerSet) != 0:
            ftlog.error('MatchStage._finishGroup matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'winlosePlayerSet not empty')
        ftlog.info('MatchStage._finishGroup matchId=', self.matchId,
                   'instId=', self.instId,
                   'stageId=', self.stageId,
                   'stageIndex=', self.index,
                   'groupId=', group.groupId)
        group._finishCardCountPlayerSet.clear()
        group._winlosePlayerListQueue = []
        group._winlosePlayerSet = set()
        riseUserCount = min(self._conf.riseUserCount, len(group._rankList))
        while len(group._rankList) > riseUserCount:
            self._outPlayer(group, group._rankList[-1])
        self._matchingGroupSet.remove(group)
        self._finishedGroupSet.add(group)

    def _finishStage(self):
        self._state = MatchStage.STATE_FINISHED
        ftlog.hinfo('MatchStage._finishStage matchId=', self.matchId,
                    'instId=', self.instId,
                    'stageId=', self.stageId,
                    'stageIndex=', self.index)
        self._matching.startNextStage()

    def _killStage(self, reason):
        self._state = MatchStage.STATE_FINISHED
        ftlog.info('MatchStage._killStage matchId=', self.matchId,
                   'instId=', self.instId,
                   'stageId=', self.stageId,
                   'stageIndex=', self.index,
                   'reason=', reason)
        for group in self._groupList:
            # 释放所有桌子
            for table in group._busyTableSet:
                self._clearTable(table)

            group._busyTableSet.clear()

            # 解锁并over所有用户
            for player in group._rankList:
                self._doPlayerMatchOver(group, player, reason)

    def _isGroupFinished(self, group):
        return len(group._finishCardCountPlayerSet) >= len(group._rankList)

    def _processGroup(self, group, maxCount=2000):
        if ftlog.is_debug():
            winlosePlayerListQueue = []
            for l in group._winlosePlayerListQueue:
                winlosePlayerListQueue.append([l[0], [p.userId for p in l[1]]])

            ftlog.debug('MatchStage._processGroup matchId=', self.matchId,
                        'instId=', self.instId, 'stageId=', self.stageId,
                        'stageIndex=', self.index, 'groupId=', group.groupId,
                        'userCount=', len(group.rankList), 'tick=', self.match.tick,
                        'waitUserIds=', [p.userId for p in group._waitPlayerList],
                        'winloseUserIds=', winlosePlayerListQueue,
                        'finishCardUserIds=', [p.userId for p in group._finishCardCountPlayerSet],
                        'busyTableIds=', [t.tableId for t in group._busyTableSet])

        ftlog.info('MatchStage._processGroup matchId=', self.matchId,
                   'instId=', self.instId, 'stageId=', self.stageId,
                   'stageIndex=', self.index, 'groupId=', group.groupId,
                   'userCount=', len(group.rankList), 'tick=', self.match.tick,
                   'waitUserCount=', len(group._waitPlayerList),
                   'winlosePlayerListQueueLen=', len(group._winlosePlayerListQueue),
                   'finishCardUserCount=', len(group._finishCardCountPlayerSet),
                   'busyTableCount=', len(group._busyTableSet))

        self._processTimeoutTables(group)
        self._processWinloseUserList(group)
        self._processGiveupUsers(group)
        self._processWaitUserList(group, maxCount)

        # 检查group是否已经结束
        if self._isGroupFinished(group):
            self._finishGroup(group)

    def _processTimeoutTables(self, group):
        overtimeTables = []
        timestamp = Utils.timestamp()
        for table in group._busyTableSet:
            if timestamp - table.playTime >= self.matchInst.conf.start.tableTimes:
                overtimeTables.append(table)
        for table in overtimeTables:
            ftlog.info('MatchStage._processTimeoutTables matchId=', self.matchId,
                       'instId=', self.instId,
                       'stageId=', self.stageId,
                       'stageIndex=', self.index,
                       'groupId=', group.groupId,
                       'tableId=', table.tableId,
                       'playTimes=', (timestamp - table.playTime))
            playerList = table.getPlayingPlayerList()
            for player in playerList:
                self.winlose(group, player, 0, True, True)

    def _sortMatchRanks(self, group):
        # 排序当前的比赛结果
        if self._conf.type == StageType.DIEOUT:
            group._rankList.sort(PlayerSort.cmpByTableRanking)
        else:
            group._rankList.sort(PlayerSort.cmpByChip)

        for index in xrange(len(group._rankList)):
            group._rankList[index].rank = index + 1

        ranktops = []
        ranktops.extend(group._rankList)
        ranktops.sort(PlayerSort.cmpByChip)
        newranktops = []
        for index, player in enumerate(ranktops):
            player.chiprank = index + 1
            newranktops.append([player.userId, player.userName, player.chip, player.signinTime])
        group._ranktops = newranktops[0:10]

    def _initPlayerDatas(self, group):
        chipCalc = PlayerChipCalc.makeCalc(self._conf, group._rankList)
        for player in group._rankList:
            player.chip = chipCalc.calc(player.chip)
            player.waitTimes = 0
            player.cardCount = 0
            player.tableRank = 0
            if ftlog.is_debug():
                ftlog.debug('MatchStage._initPlayerDatas matchId=', self.matchId,
                            'instId=', self.instId,
                            'stageId=', self.stageId,
                            'stageIndex=', self.index,
                            'groupId=', group.groupId,
                            'userId=', player.userId,
                            'chip=', player.chip)

    def _initWaitPlayerList(self, group):
        # 排序
        if ftlog.is_debug():
            ftlog.debug('MatchStage._initWaitPlayerList matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'userIds=', [p.userId for p in group._rankList])
        group._waitPlayerList = []

        waitPlayers = PlayerQueuing.sort(self._conf.seatQueuing, group._rankList)
        byeCount = len(waitPlayers) % self.match.tableSeatCount

        for player in waitPlayers:
            self._appendWaitPlayerList(group, player)

        for i in xrange(byeCount):
            group._waitPlayerList[-1 - i].waitReason = WaitReason.BYE

    def _processWaitUserList(self, group, maxCount=2000):
        if ftlog.is_debug():
            ftlog.debug('MatchStage._processWaitUserList matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'waitUserIds=', [p.userId for p in group._waitPlayerList],
                        'maxCount=', maxCount)

        # 检查剩余的玩家能不能凑够一桌
        waitCount = len(group._waitPlayerList)
        finishCount = len(group._finishCardCountPlayerSet)
        if (waitCount > 0
            and waitCount < self.match.tableSeatCount
            and (finishCount + waitCount) >= len(group.rankList)):
            diff = self.match.tableSeatCount - waitCount
            if finishCount < diff:
                # 凑不够一桌，直接结算轮空的用户完成
                ftlog.hinfo('MatchStage._processWaitUserList matchId=', self.matchId,
                            'instId=', self.instId,
                            'stageId=', self.stageId,
                            'stageIndex=', self.index,
                            'groupId=', group.groupId,
                            'userCount=', len(group.rankList),
                            'waitUserIds=', [p.userId for p in group._waitPlayerList],
                            'error=', 'userNotEnough')
            waitPlayerList = group._waitPlayerList
            group._waitPlayerList = []
            for player in waitPlayerList:
                player.cardCount += 1
                self.winlose(group, player, 0, True, True)
            # else:
            #                 waitPlayerList = group._waitPlayerList
            #                 group._waitPlayerList = []
            #                 for player in waitPlayerList:
            #                     player.cardCount += 1
            #                     self.winlose(group, player, 0, True, True)
            #                 for _ in xrange(diff):
            #                     player = group._finishCardCountPlayerSet.pop()
            #                     self._appendWaitPlayerList(group, player)
            return waitCount

        index = 0
        while (index < maxCount and
                           index + self.match.tableSeatCount <= len(group._waitPlayerList)):
            # 分配桌子
            table = self._matching.borrowTable()
            assert (table is not None)
            table.group = group
            table.playTime = Utils.timestamp()
            table.ccrc += 1
            table.stageType = self._conf.type
            for i in xrange(self.match.tableSeatCount):
                player = group._waitPlayerList[index + i]
                if player.state != Player.STATE_WAIT:
                    ftlog.error('MatchStage._processWaitUserList matchId=', self.matchId,
                                'instId=', self.instId,
                                'stageId=', self.stageId,
                                'stageIndex=', self.index,
                                'groupId=', group.groupId,
                                'userId=', player.userId,
                                'state=', player.state,
                                'error=', 'badState')
                    assert (player.state == Player.STATE_WAIT)

                player.state = Player.STATE_PLAYING
                player.cardCount += 1
                player.waitReason = WaitReason.UNKNOWN
                if player.seat:
                    ftlog.error('MatchStage._processWaitUserList matchId=', self.matchId,
                                'instId=', self.instId,
                                'stageId=', self.stageId,
                                'stageIndex=', self.index,
                                'groupId=', group.groupId, 'userId=', player.userId,
                                'seatLoc=', player.seat.location,
                                'error=', 'seatNotEmpty')
                    assert (player.seat is None)
                table.sitdown(player)
                assert (player.seat)
                if ftlog.is_debug():
                    ftlog.debug('MatchStage._processWaitUserList matchId=', self.matchId,
                                'instId=', self.instId,
                                'stageId=', self.stageId,
                                'stageIndex=', self.index,
                                'groupId=', group.groupId,
                                'userId=', player.userId,
                                'sitdown=', player.seat.location)
                group._busyTableSet.add(table)
                # 设置用户loc
            #             userSeatList = []
            #             for seat in table.seats:
            #                 userSeatList.append((seat.player.userId, seat.seatId))
            #             self.match.playerLocation.setLocationListForce(self.match.gameId,
            #                                                        table.roomId,
            #                                                        table.tableId,
            #                                                        userSeatList)

            ftlog.hinfo('MatchStage._processWaitUserList matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'tableId=', table.tableId,
                        'userIds=', table.getUserIdList())
            self.match.tableController.startTable(table)
            index += self.match.tableSeatCount

        if index > 0:
            del group._waitPlayerList[0:index]

        return index

    def _processGiveupUsers(self, group):
        if ftlog.is_debug():
            ftlog.debug('MatchStage._processGiveupUsers matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'giveupUserIds=', [p.userId for p in group._giveupPlayers])

        requestGiveupPlayers = group._giveupPlayers
        group._giveupPlayers = set()

        for player in requestGiveupPlayers:
            if (self._conf.type != StageType.ASS
                or len(group._rankList) <= self._conf.riseUserCount
                or self.index + 1 >= self.matching.stageCount):
                if ftlog.is_debug():
                    ftlog.debug('MatchStage._processGiveupUsers matchId=', self.matchId,
                                'instId=', self.instId,
                                'stageId=', self.stageId,
                                'stageIndex=', self.index,
                                'groupId=', group.groupId,
                                'rankListLen=', len(group._rankList),
                                'riseUserCount=', self._conf.riseUserCount)
                self.match.playerNotifier.notifyMatchGiveupFailed(player, group, '您的当前阶段不能退出比赛，请稍候')
            else:
                player.rank = len(self.matchInst.playerMap)
                try:
                    group._waitPlayerList.remove(player)
                except:
                    pass
                self._outPlayer(group, player)

    def _processWinloseUserList(self, group):
        winLosePlayerList = group.nextTickWinlosePlayerList()

        if ftlog.is_debug():
            ftlog.debug('MatchStage._processWinloseUserList matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'winloseUserIds=', [p.userId for p in winLosePlayerList] if winLosePlayerList else [])

        ftlog.info('MatchStage._processWinloseUserList matchId=', self.matchId,
                   'instId=', self.instId,
                   'stageId=', self.stageId,
                   'stageIndex=', self.index,
                   'groupId=', group.groupId,
                   'winloseUserCount=', len(winLosePlayerList) if winLosePlayerList else 0)

        if not winLosePlayerList:
            return

        # 重新排序
        self._sortMatchRanks(group)

        if self._conf.type == StageType.ASS:
            self._processWinlosePlayerListASS(group, winLosePlayerList)
        else:
            self._processWinlosePlayerListDieout(group, winLosePlayerList)

    def _checkWaitFinishOrFinishStageASS(self, group):
        # 排行榜的人数到达预订人数，当前阶段结束
        return len(group._rankList) <= self._conf.riseUserRefer

    def _playerFinishCardCount(self, group, player):
        player.state = Player.STATE_WAIT
        player.waitReason = WaitReason.RISE
        group._finishCardCountPlayerSet.add(player)

    def _processWinlosePlayerListASS(self, group, winLosePlayerList):
        if ftlog.is_debug():
            ftlog.debug('MatchStage._processWinlosePlayerListASS matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'winloseUserIds=', [p.userId for p in winLosePlayerList])

        losers = []
        for player in winLosePlayerList:
            if self._checkWaitFinishOrFinishStageASS(group):
                # 当前阶段要结束了, 把这些player算作完成CardCount的玩家
                self._playerFinishCardCount(group, player)
                self.match.playerNotifier.notifyMatchWait(player, group, 1)
                continue

            if player.chip < self._assLoseChip:
                losers.append(player)
            else:
                if player.cardCount >= self._conf.cardCount:
                    self._playerFinishCardCount(group, player)
                    self.match.playerNotifier.notifyMatchWait(player, group, 1)
                else:
                    self._appendWaitPlayerList(group, player)
                    self.match.playerNotifier.notifyMatchWait(player, group, 0)

        for player in losers:
            player.whenOut = Player.WHEN_OUT_ASS
            self._outPlayer(group, player)

    def _processWinlosePlayerListDieout(self, group, winLosePlayerList):
        if ftlog.is_debug():
            ftlog.debug('MatchStage._processWinlosePlayerListDieout matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'winloseUserIds=', [p.userId for p in winLosePlayerList])

        for player in winLosePlayerList:
            # 如果打的牌数达到最大定义的牌数，等待阶段结束排名
            if player.cardCount < self._conf.cardCount:
                # 否则放入等待队列，等待再次开始
                self._appendWaitPlayerList(group, player)
                self.match.playerNotifier.notifyMatchWait(player, group, 0)
            else:
                self._playerFinishCardCount(group, player)
                self.match.playerNotifier.notifyMatchWait(player, group, 1)

    def _outPlayer(self, group, player):
        if ftlog.is_debug():
            ftlog.debug('MatchStage._outPlayer matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'userId=', player.userId)
        player.state = Player.STATE_OUT
        assert (player.seat is None)

        del group._playerMap[player.userId]

        # 删除MatchInstance中的用户
        del self.matchInst.playerMap[player.userId]

        # 删除已完成cardCount的用户
        group._finishCardCountPlayerSet.discard(player)

        # 删除排行榜中的用户
        group._rankList.remove(player)
        self._doPlayerMatchOver(group, player, MatchFinishReason.USER_LOSER)

    def _appendWaitPlayerList(self, group, player):
        if ftlog.is_debug():
            ftlog.debug('MatchStage._appendWaitPlayerList matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'userId=', player.userId)
        player.state = Player.STATE_WAIT
        group._waitPlayerList.append(player)

    def _sortTableRank(self, tablePlayers):
        tablePlayers.sort(PlayerSort.cmpByChip)
        for i in xrange(len(tablePlayers)):
            tablePlayers[i].tableRank = i + 1

    def _clearTable(self, table, changeLoc=True):
        if ftlog.is_debug():
            ftlog.info('MatchStage._clearTable matchId=', self.matchId,
                       'instId=', self.instId,
                       'stageId=', self.stageId,
                       'stageIndex=', self.index,
                       'tableId=', table.tableId)
        if changeLoc:
            for seat in table.seats:
                if seat.player:
                    try:
                        onlinedata.addOnlineLoc(seat.player.userId, self.match.roomId, self.match.tableId,
                                                self.match.seatId)
                        if ftlog.is_debug():
                            ftlog.debug("|userId, locList:", seat.player.userId,
                                        onlinedata.getOnlineLocList(seat.player.userId), caller=self)
                    except:
                        ftlog.error()

        self.match.tableController.clearTable(table)
        for seat in table.seats:
            if seat.player:
                if ftlog.is_debug():
                    ftlog.debug('MatchStage._clearTable matchId=', self.matchId,
                                'instId=', self.instId,
                                'stageId=', self.stageId,
                                'stageIndex=', self.index,
                                'tableId=', table.tableId,
                                'userId=', seat.player.userId,
                                'standup=', seat.location)
                table.standup(seat.player)

    def _checkGrowLoseBetChip(self):
        timestamp = Utils.timestamp()
        if (timestamp - self._lastGrowTime) >= self._conf.chipTimes:
            self._lastGrowTime = timestamp
            if self._conf.chipGrow > 99:
                self._growLoseBetChip(self._conf.chipGrow)
            else:
                deltaChip = 0
                if self._conf.chipGrowBase == 0:
                    deltaChip = self._loseBetChip * self._conf.chipGrow
                else:
                    if self._growCount == 0:
                        deltaChip = self._conf.chipGrowBase
                    else:
                        deltaChip = self._conf.chipGrowBase + self._growCount * self._conf.chipGrowIncr

                    self._growCount += 1
                self._growLoseBetChip(deltaChip)

            ftlog.info('MatchStage._checkGrowLoseBetChip matchId=', self.matchId,
                       'instId=', self.instId,
                       'stageId=', self.stageId,
                       'stageIndex=', self.index,
                       'lostBetChip=', self._loseBetChip,
                       'assLoseChip=', self._assLoseChip,
                       '_growCount=', self._growCount)

            # for group in self._matchingGroupSet:
            #    for table in group._busyTableSet:
            #        self.match.tableController.updateTableInfo(table)

    def _growLoseBetChip(self, chipGrow):
        self._loseBetChip += int(chipGrow)
        if self._conf.type == StageType.ASS:
            self._assLoseChip = self._calcASSLoseChip()

    def _calcASSLoseChip(self):
        if self._conf.type == StageType.ASS:
            loseChip = self._conf.loseUserChip
            if loseChip > 1:
                return int(loseChip)
            else:
                return int(loseChip * self._loseBetChip)
        return None

    def _doPlayerMatchOver(self, group, player, reason):
        # 解锁玩家
        if ftlog.is_debug():
            ftlog.debug('MatchStage._doPlayerMatchOver matchId=', self.matchId,
                        'instId=', self.instId,
                        'stageId=', self.stageId,
                        'stageIndex=', self.index,
                        'groupId=', group.groupId,
                        'userId=', player.userId,
                        'cardCount=', player.cardCount,
                        'stageCardCount=', self._conf.cardCount,
                        'reason=', reason,
                        'whenOut=', player.whenOut)

        rankRewards = None
        self.matchInst._unlockPlayer(player)

        if (reason == MatchFinishReason.USER_WIN
            or reason == MatchFinishReason.USER_LOSER):
            rankRewards = self._getRewards(player)
            if rankRewards:
                self.match.matchRewards.sendRewards(player, group, rankRewards)
                if reason == MatchFinishReason.USER_LOSER:
                    reason = MatchFinishReason.USER_WIN

                    #             event_remote.publishMatchWinloseEvent(self.matchInst.conf.gameId,
                    #                                                         player.userId, self.match.matchId,
                    #                                                         reason == MatchFinishReason.USER_WIN,
                    #                                                         player.rank)

                    # 为了避免在typoker里调用hall里的Rpc，publishMatchWinloseEvent转移到self.match.playerNotifier.notifyMatchOver实现

        ftlog.hinfo('MatchStage._doPlayerMatchOver matchId=', self.matchId,
                    'instId=', self.instId,
                    'stageId=', self.stageId,
                    'stageIndex=', self.index,
                    'groupId=', group.groupId,
                    'userCount=', len(group.rankList),
                    'userId=', player.userId,
                    'rank=', player.rank,
                    'reason=', reason,
                    'whenOut=', player.whenOut,
                    'cardCount=', player.cardCount,
                    'stageCardCount=', self._conf.cardCount,
                    'rankRewards=', rankRewards.conf if rankRewards else None)

        self.match.playerNotifier.notifyMatchOver(player, group, reason, rankRewards)
        pkeventbus.globalEventBus.publishEvent(MatchPlayerOverEvent(player.userId,
                                                                    self.match.gameId,
                                                                    self.matchId, player,
                                                                    reason,
                                                                    rankRewards))

    def _getRewards(self, player):
        # 看当前阶段是否有配置奖励
        rankRewardsList = self._conf.rankRewardsList
        if not rankRewardsList:
            # 当前阶段没有配置奖励
            if len(self._groupList) == 1 or not self.hasNextStage():
                rankRewardsList = self.matchInst.conf.rankRewardsList
        if rankRewardsList:
            for rankRewards in rankRewardsList:
                if rankRewards.startRank == -1:
                    return rankRewards
                if (player.rank >= rankRewards.startRank
                    and (rankRewards.endRank == -1 or player.rank <= rankRewards.endRank)):
                    return rankRewards
        return None


class Matching(object):
    '''
    一个赛事的一场比赛
    '''
    STATE_IDLE = 0
    STATE_STARTING = 1
    STATE_STARTED = 2
    STATE_FINISHED = 3
    STATE_FINAL = 4

    def __init__(self, matchInst, matchingId, stageConfs):
        # 比赛中的阶段
        self._matchInst = matchInst
        self._matchingId = matchingId
        self._stages = self._createStages(stageConfs)
        self._idleTableList = None
        self._allTableSet = None
        self._stage = self._stages[0]
        self._state = Matching.STATE_IDLE
        self._startTime = None
        self._startPlayerCount = 1

    @property
    def matchingId(self):
        return self._matchingId

    @property
    def match(self):
        return self._matchInst.match

    @property
    def matchInst(self):
        return self._matchInst

    @property
    def stageCount(self):
        return len(self._stages)

    @property
    def startPlayerCount(self):
        return self._startPlayerCount

    def getStage(self, index):
        assert (index >= 0 and index < self.stageCount)
        return self._stages[index]

    def getMatchingPlayerCount(self):
        return self._stage.getMatchingPlayerCount()

    def findMatchingPlayer(self, userId):
        '''
        查找所有的
        '''
        return self._stage.findMatchingPlayer(userId)

    def findFirstStage(self, playerCount):
        if self.matchInst.conf.start.selectFirstStage:
            for stage in self._stages:
                if playerCount > stage.conf.riseUserCount:
                    return stage
        return self._stages[0]

    def start(self, playerList):
        assert (self._state == Matching.STATE_IDLE)
        self._state = Matching.STATE_STARTING

        # 记录开始时间
        self._startTime = Utils.timestamp()
        self._startPlayerCount = len(playerList)

        self._stage = self.findFirstStage(len(playerList))

        ftlog.info('Matching.start matchingId=', self._matchingId,
                   'userCount=', self._startPlayerCount,
                   'startTime=', self._startTime,
                   'firstStageIndex=', self._stage.index,
                   'starting...')

        # 锁定桌子
        if not self._lockTables(playerList):
            for player in playerList:
                self.matchInst._unlockPlayer(player)
                self.match.playerNotifier.notifyMatchCancelled(player, self.matchInst,
                                                               MatchFinishReason.RESOURCE_NOT_ENOUGH)
                del self.matchInst._playerMap[player.userId]
            self._state = Matching.STATE_FINISHED
            return

        # 分组启动
        groups = self._groupingPlayers(playerList, self._stage)

        # 启动当前阶段
        self._stage.setupStage(groups)

        ftlog.info('Matching.start matchingId=', self._matchingId,
                   'userCount=', len(playerList),
                   'startTime=', self._startTime,
                   'started')

        self._state = Matching.STATE_STARTED

    def borrowTable(self):
        assert (len(self._idleTableList) > 0)
        table = self._idleTableList.pop()
        if ftlog.is_debug():
            ftlog.debug('Matching.borrowTable matchingId=', self._matchingId,
                        'tableId=', table.tableId)
        return table

    def returnTable(self, table):
        assert (table in self._allTableSet)
        self._idleTableList.append(table)
        if ftlog.is_debug():
            ftlog.debug('Matching.returnTable matchingId=', self._matchingId,
                        'tableId=', table.tableId)

    def doHeartBeat(self):
        if self._state == Matching.STATE_FINISHED:
            self._doFinal()
            return

        if self._state == Matching.STATE_STARTED:
            if Utils.timestamp() - self._startTime >= self._matchInst.conf.start.maxPlayTime:
                ftlog.info('Matching.doHeartBeat matchingId=', self._matchingId, 'timeover')
                self._killMatching()
                return
            self._stage.doHeartBeat()
            self._reclaimTables()

    def startNextStage(self):
        if not self._stage.hasNextStage():
            self._finishMatching()
            return

        stage = self._stage
        groups = stage._groupList
        self._stage = stage._next

        playerList = []

        for group in groups:
            playerList.extend(group._rankList)

        # 分组启动
        groups = self._groupingPlayers(playerList, self._stage)

        # 启动当前阶段
        self._stage.setupStage(groups)

    def _reclaimTables(self):
        if (self._state != Matching.STATE_STARTED
            or not self._stage):
            return

        needCount = self._stage.calcNeedTableCount()
        if needCount <= 0:
            return

        reclaimCount = len(self._allTableSet) - needCount
        if reclaimCount <= 0:
            return

        n = 0
        while (n < reclaimCount and len(self._idleTableList) > 0):
            n += 1
            table = self._idleTableList.pop()
            self.match.tableManager.returnTables([table])
            self._allTableSet.remove(table)

        ftlog.info('Matching._reclaimTables matching matchingId=', self._matchingId,
                   'needCount=', needCount, 'reclaimCount=', reclaimCount,
                   'allCount=', len(self._allTableSet))

    def _killMatching(self):
        assert (self._state == Matching.STATE_STARTED)
        self._state = Matching.STATE_FINISHED

        ftlog.info('Killing matching matchingId=', self._matchingId)

        # kill 当前阶段
        self._stage._killStage(MatchFinishReason.OVERTIME)

        ftlog.info('Killed matching matchingId=', self._matchingId)

    def _finishMatching(self):
        assert (self._state == Matching.STATE_STARTED)
        self._state = Matching.STATE_FINISHED

        ftlog.info('Finishing matchingId=', self._matchingId)

        # 处理当前阶段晋级的用户，发奖
        for group in self._stage._groupList:
            for player in group._rankList:
                self._stage._doPlayerMatchOver(group, player, MatchFinishReason.USER_WIN)

        ftlog.info('Finished matchingId=', self._matchingId)

    def _doFinal(self):
        assert (self._state == Matching.STATE_FINISHED)
        self._state = Matching.STATE_FINAL
        ftlog.info('Finaling matchingId=', self._matchingId)
        self._releaseTables()
        self._matchInst._finishMatching(self)
        ftlog.info('Finaled matchingId=', self._matchingId,
                   'idleTableCount=', self.match.tableManager.idleTableCount())

    def _lockTables(self, playerList):
        count = (len(playerList) + self.match.tableManager.tableSeatCount - 1) / self.match.tableManager.tableSeatCount
        if self.match.tableManager.idleTableCount() < count:
            return False
        self._idleTableList = self.match.tableManager.borrowTables(count)
        self._allTableSet = set(self._idleTableList)
        return True

    def _releaseTables(self):
        if self._allTableSet:
            assert (len(self._allTableSet) == len(self._idleTableList))
            tables = self._allTableSet
            self._allTableSet = None
            self._idleTableList = None
            if tables:
                self.match.tableManager.returnTables(tables)

    def _groupingPlayers(self, playerList, stage):
        groupPlayersList = None
        if stage.conf.groupingType == GroupingType.TYPE_GROUP_COUNT:
            groupPlayersList = PlayerGrouping.groupingByGroupCount(playerList, stage.conf.groupingGroupCount)
        elif stage.conf.groupingType == GroupingType.TYPE_USER_COUNT:
            groupPlayersList = PlayerGrouping.groupingByMaxUserCountPerGroup(playerList, stage.conf.groupingUserCount)
        else:
            groupPlayersList = [playerList]
        groups = []
        for i in xrange(len(groupPlayersList)):
            groupId = '%s.%s' % (self._matchingId, i + 1)
            groupName = stage.name
            if len(groupPlayersList) > 1:
                groupName = '%s%s组' % (groupName, i + 1)
            # groups.append(MatchGroup(groupId, groupName, groupPlayersList[i]))
            groups.append(self.match.matchGroupFactory.newMatchGroup(groupId, groupName, groupPlayersList[i]))
        return groups

    def _createStages(self, stageConfs):
        ret = []
        for i in xrange(len(stageConfs)):
            stage = self.match.matchStageFactory.newMatchStage(self, stageConfs[i], i)
            # stage = MatchStage(self, stageConfs[i], i)
            ret.append(stage)
        for i in range(1, len(ret)):
            ret[i - 1]._next = ret[i]
        return ret


class MatchGroup(object):
    '''
    分组, 每个组会打N个阶段的比赛
    '''

    def __init__(self, groupId, groupName, playerList):
        # 组ID
        self._groupId = groupId
        self._groupName = groupName
        # 本组内的剩余玩家
        self._playerMap = self._initPlayerMap(playerList)
        self._allPlayerCount = len(playerList)
        # 当前阶段
        self._stage = None
        # 排序的所有玩家
        self._rankList = playerList
        # 空闲的桌子
        self._busyTableSet = set()
        # 等待开始的玩家列表
        self._waitPlayerList = []
        # 玩完一局的玩家列表
        self._winlosePlayerListQueue = []
        self._winlosePlayerSet = set()
        self._processIndex = 0
        # 完成局数的玩家列表
        self._finishCardCountPlayerSet = set()

        # 榜单
        self._ranktops = []
        self._lastTablePlayTime = 0

        # 放弃比赛的玩家
        self._giveupPlayers = set()

    @property
    def groupId(self):
        return self._groupId

    @property
    def groupName(self):
        return self._groupName

    @property
    def stage(self):
        return self._stage

    @property
    def match(self):
        return self._stage.match

    @property
    def matchInst(self):
        return self._stage.matchInst

    @property
    def startTime(self):
        return self.matchInst.startTime

    @property
    def rankList(self):
        return self._rankList

    @property
    def ranktops(self):
        return self._ranktops

    @property
    def allPlayerCount(self):
        return self._allPlayerCount

    @property
    def busyTableCount(self):
        return len(self._busyTableSet)

    def getStartPlayerCount(self):
        if self._stage.getGroupCount() > 1:
            return self._allPlayerCount
        return self._stage.matching.startPlayerCount

    def findMatchingPlayer(self, userId):
        '''
        查找所有的
        '''
        return self._playerMap.get(userId, None)

    def addGiveupPlayer(self, player):
        assert (player.group == self)
        assert (player.state == Player.STATE_WAIT)
        self._giveupPlayers.add(player)

    def addWinlosePlayerList(self, playerList):
        processTick = self.match.tick + 2
        playerSet = set(playerList)
        assert (len(playerSet) == len(playerList))
        for player in playerList:
            if player in self._winlosePlayerSet:
                ftlog.error('MatchGroup.addWinlosePlayerList groupId=', self.groupId,
                            'tick=', self.match.tick, 'processTick=', processTick,
                            'userIds=', [p.userId for p in playerList],
                            'userId=', player.userId, 'already in winlose')
            assert (player not in self._winlosePlayerSet)
        self._winlosePlayerSet.update(playerList)
        if (len(self._winlosePlayerListQueue) > 0
            and self._winlosePlayerListQueue[-1][0] >= processTick):
            self._winlosePlayerListQueue[-1][1].extend(playerList)
        else:
            self._winlosePlayerListQueue.append((processTick, playerList))
        if ftlog.is_debug():
            ftlog.debug('MatchGroup.addWinlosePlayerList groupId=', self.groupId,
                        'tick=', self.match.tick, 'processTick=', processTick,
                        'winlosePlayerListQueue.len=', len(self._winlosePlayerListQueue),
                        'userIds=', [p.userId for p in playerList])

    def nextTickWinlosePlayerList(self):
        ret = []
        while (len(self._winlosePlayerListQueue) > 0
               and self.match.tick >= self._winlosePlayerListQueue[0][0]):
            subRet = self._winlosePlayerListQueue.pop(0)[1]
            for player in subRet:
                self._winlosePlayerSet.remove(player)
            ret.extend(subRet)
        return ret

    def _initPlayerMap(self, playerList):
        ret = {}
        for player in playerList:
            ret[player.userId] = player
            player.group = self
        return ret
