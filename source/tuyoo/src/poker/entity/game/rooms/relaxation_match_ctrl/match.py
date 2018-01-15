# -*- coding:utf-8 -*-
'''
Created on 2016年6月7日

@author: luoguanggui
'''
from datetime import datetime

from poker.entity.biz import bireport
from poker.entity.game.game import TYGame
from poker.entity.game.rooms.relaxation_match_ctrl.const import TOP_N
from poker.entity.game.rooms.relaxation_match_ctrl.events import MatchStartEvent, MatchOverEvent
from poker.entity.game.rooms.relaxation_match_ctrl.models import TableManager
from poker.entity.game.rooms.relaxation_match_ctrl.utils import HeartbeatAble
from poker.entity.game.rooms.relaxation_match_ctrl.utils import Logger


class MatchRelaxation(HeartbeatAble):
    ST_IDLE = 0
    ST_START = 2

    def __init__(self, conf, room):
        super(MatchRelaxation, self).__init__()
        # 桌子操作控制器
        self.tableController = None
        # 玩家事件通知
        self.playerNotifier = None
        # 发送奖励通知消息
        self.matchRewards = None
        # 排名规则
        self.playerSortApi = None

        # 比赛配置
        self._matchConf = conf
        self.room = room
        # 当前比赛状态，初始化为
        self._state = MatchRelaxation.ST_IDLE
        # 玩家map，key=userId, value=Player
        self._playerMap = {}
        # 最终总榜
        self._rankList = []
        # 积分排行榜 TopN
        self._ranktops = []
        # 完成最大限制牌局局数的玩家
        self._finishPlayerMap = {}
        # 等待的玩家列表
        self._waitPlayerList = []
        # 比赛开始时间
        self._startTime = None
        # 结束时间
        self._endTime = None
        # 桌子管理对象
        self.tableManager = None
        self._logger = Logger()

    @property
    def state(self):
        return self._state

    @property
    def matchConf(self):
        return self._matchConf

    @property
    def playerCount(self):
        return len(self._playerMap)

    @property
    def playerMap(self):
        return self._playerMap

    @property
    def ranktops(self):
        return self._ranktops

    @property
    def startTime(self):
        return self._startTime

    @property
    def endTime(self):
        return self._endTime

    def findTable(self, tableId):
        return self.tableManager.findTable(tableId)

    def clear(self):
        # 玩家map，key=userId, value=Player
        self._playerMap = {}
        # 最终总榜
        self._rankList = []
        # 积分排行榜
        self._ranktops = []
        # 完成最大限制牌局局数的玩家
        self._finishPlayerMap = {}
        # 等待的玩家列表
        self._waitPlayerList = []
        # 比赛开始时间
        self._startTime = None
        # 结束时间
        self._endTime = None

    def initTableManager(self, room, tableSeatCount, matchId):
        self.tableManager = TableManager(room, tableSeatCount)
        shadowRoomIds = room.roomDefine.shadowRoomIds

        self._logger.info('MatchRelaxation.initTableManager',
                          'shadowRoomIds=', list(shadowRoomIds))

        for roomId in shadowRoomIds:
            count = room.roomDefine.configure['gameTableCount']
            baseid = roomId * 10000
            self._logger.info('MatchRelaxation.initTableManager addTables',
                              'shadowRoomId=', roomId,
                              'tableCount=', count,
                              'baseid=', baseid)
            self.tableManager.addTables(roomId, baseid, count, matchId)

    def findPlayer(self, userId):
        return self._playerMap.get(userId)

    def addPlayer(self, player):
        self._playerMap[player.userId] = player
        if self._logger.isDebug():
            self._logger.debug('MatchRelaxation.addPlayer ok',
                               'userId=', player.userId)

    def enter(self, userId):
        pass

    def leave(self, userId):
        player = self.findPlayer(userId)
        if player:
            if player.seat:
                table = player.seat.table
                if table:
                    self.tableManager.standupFromTable(table, player)

    def start(self):
        self._logger.info('MatchRelaxation.start ...')
        self._startHeartbeat()

    def winlose(self, player, deltaScore, isWin):
        if self._logger.isDebug():
            self._logger.debug('MatchRelaxation.winlose player=', player, 'deltaScore=', deltaScore, 'isWin=', isWin,
                               'self._state=', self._state)
        if not player:
            self._logger.warn('MatchRelaxation.winlose player=None')
            return
        if self._state == MatchRelaxation.ST_START:
            table = player.seat.table
            player.score += int(deltaScore)
            player.playCount += 1
            if isWin == 1:
                player.winN += 1
            elif isWin == 0:
                player.drawN += 1
            elif isWin == -1:
                player.loseN += 1
            player.averageScore = (player.score * 1.0) / player.playCount
            anotherPlayer = table.getAnotherPlayer(player)
            player.meetPlayersMap[anotherPlayer.userId] = anotherPlayer
            self._sortMatchTopRanks(player)
            self._logger.info('MatchRelaxation.winlose ok',
                              'state=', self._state,
                              'userId=', player.userId,
                              'tableId=', table.tableId if table else None,
                              'seatId=', player.seat.seatId if player.seat else None,
                              'deltaScore=', deltaScore,
                              'isWin=', isWin)

    def returnTable(self, table):
        self.tableManager.returnOneTable(table)

    def _doHeartbeatImpl(self):
        if self._logger.isDebug():
            self._logger.debug('MatchRelaxation._doHeartbeatImpl',
                               'state=', self._state)

        day_now = datetime.now()
        todayStartTime = datetime.strptime(day_now.strftime('%Y-%m-%d') + self.matchConf.start.startTime + ':00',
                                           '%Y-%m-%d%H:%M:%S')
        todayEndTime = datetime.strptime(day_now.strftime('%Y-%m-%d') + self.matchConf.start.endTime + ':00',
                                         '%Y-%m-%d%H:%M:%S')
        if day_now >= todayEndTime and self._state == MatchRelaxation.ST_START:
            self._doFinish()
        elif day_now >= todayStartTime and day_now < todayEndTime and self._state == MatchRelaxation.ST_IDLE:
            self._doStart(todayStartTime, todayEndTime)
        return 1

    def _doStart(self, todayStartTime, todayEndTime):
        self._startTime = todayStartTime
        self._endTime = todayEndTime
        self._state = MatchRelaxation.ST_START
        self.clear()
        self.tableManager.updateMatchTime(todayStartTime, todayEndTime, self.matchConf)
        TYGame(self.room.gameId).getEventBus().publishEvent(MatchStartEvent(self.room.gameId, self.room.bigRoomId))
        self._logger.info('MatchRelaxation._doStart idleTableCount=', self.tableManager.idleTableCount)

    def _doFinish(self):
        assert (self.state == MatchRelaxation.ST_START)
        self._state = MatchRelaxation.ST_IDLE
        TYGame(self.room.gameId).getEventBus().publishEvent(MatchOverEvent(self.room.gameId, self.room.bigRoomId))
        needNotifyTableList = []
        needNotifyTableList.extend(self.tableManager.waitTableList)
        needNotifyTableList.extend(self.tableManager.busyTableList)
        lenTables = len(needNotifyTableList)
        for x in xrange(lenTables):
            self.tableController.notifyMatchOver(needNotifyTableList[x])
            self.returnTable(needNotifyTableList[x])
        # 排序最终排名
        self._sortMatchRanks()
        # 发送奖励
        for _, player in self._playerMap.items():
            self._doPlayerMatchOver(player)

        self._logger.info('MatchRelaxation._doFinish ...')

    def _sortMatchTopRanks(self, player):
        # 排序topN
        isNeedSort = False
        if player in self._ranktops:
            isNeedSort = True
        elif len(self._ranktops) < TOP_N:
            self._ranktops.append(player)
            isNeedSort = True
        elif self.playerSortApi.cmpByScore(self._ranktops[TOP_N - 1], player):
            self._ranktops[TOP_N - 1] = player
            isNeedSort = True
        if isNeedSort:
            self._ranktops.sort(self.playerSortApi.cmpByScore)
            topRankLen = len(self._ranktops)
            for index in xrange(topRankLen):
                self._ranktops[index].topRank = index + 1
            self.tableManager.updateMatchRank(self._ranktops)
            needNotifyTableList = []
            needNotifyTableList.extend(self.tableManager.waitTableList)
            needNotifyTableList.extend(self.tableManager.busyTableList)
            lenTables = len(needNotifyTableList)
            for x in xrange(lenTables):
                self.tableController.notifyUpdateMatchInfo(needNotifyTableList[x])

    def _sortMatchRanks(self):
        # 排序比赛最终结果
        tempPlayerList = list(self._playerMap.values())
        minPlayCount = self.matchConf.start.minPlayCount
        # 过滤掉没有打完最低局数的
        for player in tempPlayerList:
            if player.playCount >= minPlayCount:
                self._rankList.append(player)
        self._rankList.sort(self.playerSortApi.overCmpByScore)
        rankLen = len(self._rankList)
        for index in xrange(rankLen):
            self._rankList[index].rank = self._rankList[index].topRank = index + 1
        self._ranktops = self._rankList[:TOP_N]
        bireport.matchFinish(self.room.gameId, self.room.bigRoomId,
                             self.room.bigmatchId, self.room.roomConf['name'],
                             userCount=rankLen)

    def _doPlayerMatchOver(self, player):
        # 发奖并通知玩家比赛结束
        rankRewards = self._getRewards(player)
        if rankRewards:
            self.matchRewards.sendRewards(player, rankRewards)
        self._logger.info('MatchRelaxation._doPlayerMatchOver',
                          'userId=', player.userId,
                          'remUserCount=', len(self._rankList),
                          'rank=', player.rank,
                          'rankRewards=', rankRewards.conf if rankRewards else None)

        self.playerNotifier.notifyMatchOver(player, rankRewards)

    def _getRewards(self, player):
        # 看当前阶段是否有配置奖励
        rankRewardsList = self.matchConf.rankRewardsList
        if self._logger.isDebug():
            self._logger.debug('MatchRelaxation._getRewards',
                               'userId=', player.userId,
                               'rank=', player.rank,
                               'rankRewardsList=', rankRewardsList)
        if rankRewardsList:
            for rankRewards in rankRewardsList:
                if ((rankRewards.startRank == -1 or player.rank >= rankRewards.startRank)
                    and (rankRewards.endRank == -1 or player.rank <= rankRewards.endRank)):
                    return rankRewards
        return None

    def onPlayerSitdown(self, player, table, isNewPlayer):
        if self._logger.isDebug():
            self._logger.debug('MatchRelaxation.onPlayerSitdown',
                               'userId=', player.userId,
                               'isNewPlayer=', isNewPlayer,
                               'table.tableId=', table.tableId)
        if isNewPlayer:
            # 新玩家需要进行排序
            self._sortMatchTopRanks(player)
        else:
            self.tableManager.updateMatchRank(self._ranktops)
