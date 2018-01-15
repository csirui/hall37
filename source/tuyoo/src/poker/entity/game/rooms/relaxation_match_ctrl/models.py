# -*- coding:utf-8 -*-
'''
Created on 2016年6月7日

@author: luoguanggui
'''

from freetime.core.tasklet import FTTasklet
from poker.entity.dao import daobase
from poker.entity.dao import sessiondata
from poker.entity.game.rooms.relaxation_match_ctrl.utils import Logger

RELAXATION_MATCH_LOCK_KEY = 'relaxation_match_lock'


class Player(object):
    '''
    玩家
    '''

    def __init__(self, userId):
        self.userId = userId
        # 当前休闲赛参加的累计局数
        self.playCount = 0
        self.score = 0
        self.averageScore = 0.0
        self.winN = 0
        self.loseN = 0
        self.drawN = 0
        # topN中的临时排名
        self.topRank = 0
        # 最终的排名
        self.rank = 0
        # 当前休闲赛遇到的玩家字典库key 为 userId
        self.meetPlayersMap = {}
        self.isEnter = False
        self.isLocked = False
        self.clientId = ''
        self.userName = ''
        # 玩家坐的座位
        self._seat = None

    @property
    def seat(self):
        return self._seat

    @seat.setter
    def seat(self, seat):
        self._seat = seat

    def fillUserInfo(self, userName, clientId):
        self.userName = userName
        self.clientId = clientId


class Seat(object):
    def __init__(self, table, seatId):
        self._table = table
        self._seatId = seatId
        self._location = '%s.%s.%s.%s' % (table.gameId, table.roomId, table.tableId, seatId)
        self._player = None

    @property
    def gameId(self):
        return self.table.gameId

    @property
    def table(self):
        return self._table

    @property
    def seatId(self):
        return self._seatId

    @property
    def roomId(self):
        return self.table.roomId

    @property
    def tableId(self):
        return self.table.tableId

    @property
    def location(self):
        return self._location

    @property
    def player(self):
        return self._player


class Table(object):
    def __init__(self, gameId, roomId, tableId, seatCount, matchId):
        # 游戏ID
        self._gameId = gameId
        # 房间ID
        self._roomId = roomId
        # 座位ID
        self._tableId = tableId
        # 比赛Id
        self.matchId = matchId
        # 所有座位
        self._seats = self._makeSeats(seatCount)
        # 空闲座位
        self._idleSeats = self._seats[:]
        # 当前比赛信息
        self.matchInfo = {}
        # 桌子Location
        self._location = '%s.%s.%s' % (self.gameId, self.roomId, self.tableId)
        self._logger = Logger()

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
    def seats(self):
        return self._seats

    @property
    def group(self):
        return self._group

    @property
    def location(self):
        return self._location

    @property
    def seatCount(self):
        return len(self._seats)

    @property
    def idleSeatCount(self):
        '''
        空闲座位的数量
        '''
        return len(self._idleSeats)

    def getPlayerCount(self):
        '''
        获取该桌子上玩家数量
        '''
        count = 0
        for seat in self._seats:
            if seat.player:
                count += 1
        return count

    def getPlayerList(self):
        '''
        获取本桌的所有player
        '''
        return [seat.player for seat in self.seats if seat.player]

    def getAnotherPlayer(self, player):
        anotherPlayer = None
        for seat in self._seats:
            if seat.player != player and seat.player:
                anotherPlayer = seat.player
        return anotherPlayer

    def getUserIdList(self):
        '''
        获取本桌所有userId
        '''
        ret = []
        for seat in self.seats:
            ret.append(seat.player.userId if seat.player else 0)
        return ret

    def sitdown(self, player):
        '''
        玩家坐下
        '''
        assert (player._seat is None)
        assert (len(self._idleSeats) > 0)
        seat = self._idleSeats[-1]
        del self._idleSeats[-1]
        seat._player = player
        player._seat = seat
        self._logger.info('Table.sitdown userId=', player.userId,
                          'seatId=', seat.seatId,
                          'tableId=', self.tableId)

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
            seats.append(Seat(self, i + 1))
        return seats


class TableManager(object):
    def __init__(self, room, tableSeatCount):
        self._room = room
        # 重启的时候将锁清零初始化
        daobase.executeMixCmd('HSET', RELAXATION_MATCH_LOCK_KEY, str(self._room.roomId), 0)
        self._tableSeatCount = tableSeatCount
        # 打牌的桌子
        self._busyTableList = []
        # 处于等待的桌子,已经有人但没有坐满
        self._waitTableList = []
        # 空闲的桌子        
        self._idleTables = []
        # 所有的桌子
        self._allTableMap = {}
        self._roomIds = set()
        self._logger = Logger()
        self._logger.add('roomId', self._room.roomId)

    @property
    def tableSeatCount(self):
        return self._tableSeatCount

    @property
    def roomCount(self):
        return len(self._roomIds)

    @property
    def gameId(self):
        return self._room.gameId

    @property
    def allTableCount(self):
        return len(self._allTableMap)

    @property
    def idleTableCount(self):
        return len(self._idleTables)

    @property
    def busyTableCount(self):
        return len(self._busyTableList)

    @property
    def waitTableCount(self):
        return len(self._waitTableList)

    @property
    def waitTableList(self):
        return self._waitTableList

    @property
    def busyTableList(self):
        return self._busyTableList

    def getTableCountPerRoom(self):
        return len(self._allTableMap) / max(1, self.roomCount)

    def updateMatchTime(self, todayStartTime, todayEndTime, matchConf):
        allTableList = list(self._allTableMap.values())
        tableN = len(allTableList)
        for x in xrange(tableN):
            allTableList[x].matchInfo['startTime'] = todayStartTime
            allTableList[x].matchInfo['endTime'] = todayEndTime
            allTableList[x].matchInfo['matchConf'] = matchConf

    def updateMatchRank(self, topRankPlayerList):
        allTableList = list(self._allTableMap.values())
        tableN = len(allTableList)
        # top10
        topRankList = []
        lenTop = len(topRankPlayerList)
        topN = 10 if lenTop > 10 else lenTop
        for t in xrange(topN):
            meetPlayerList = list(topRankPlayerList[t].meetPlayersMap.values())
            meetPlayerAs = 0.0
            meetPlayerCount = len(meetPlayerList)
            if meetPlayerCount > 0:
                allPlayerAs = 0
                for x in xrange(meetPlayerCount):
                    allPlayerAs += meetPlayerList[x].averageScore
                meetPlayerAs = allPlayerAs / meetPlayerCount
            topRankList.append(
                {'userId': topRankPlayerList[t].userId, 'rank': t + 1, 'name': topRankPlayerList[t].userName,
                 'score': topRankPlayerList[t].averageScore, 'rivalScore': meetPlayerAs,
                 'winN': topRankPlayerList[t].winN, 'loseN': topRankPlayerList[t].loseN,
                 'drawN': topRankPlayerList[t].drawN, 'playCount': topRankPlayerList[t].playCount
                 })
        for i in xrange(tableN):
            allTableList[i].matchInfo['topRank'] = topRankList
            seats = allTableList[i].seats
            seatInfo = []
            for seat in seats:
                if seat.player:
                    meetPlayerList = list(seat.player.meetPlayersMap.values())
                    meetPlayerAs = 0.0
                    meetPlayerCount = len(meetPlayerList)
                    if meetPlayerCount > 0:
                        allPlayerAs = 0
                        for x in xrange(meetPlayerCount):
                            allPlayerAs += meetPlayerList[x].averageScore
                        meetPlayerAs = allPlayerAs / meetPlayerCount
                    seatInfo.append({'userId': seat.player.userId,
                                     'name': seat.player.userName,
                                     'rank': seat.player.topRank if seat.player in topRankPlayerList else 0,
                                     'score': seat.player.averageScore,
                                     'rivalScore': meetPlayerAs,
                                     'winN': seat.player.winN,
                                     'loseN': seat.player.loseN,
                                     'drawN': seat.player.drawN,
                                     'playCount': seat.player.playCount
                                     })
                else:
                    seatInfo.append({})
            allTableList[i].matchInfo['seats'] = seatInfo

    def addTables(self, roomId, baseId, count, matchId):
        if count > 0:
            self._roomIds.add(roomId)
        for i in xrange(count):
            tableId = baseId + i + 1  # 新框架里tableId 从 1开始计数， 0表示队列。
            table = Table(self.gameId, roomId, tableId, self._tableSeatCount, matchId)
            self._idleTables.append(table)
            self._allTableMap[tableId] = table

    def _borrowOneTable(self):
        table = None
        if self.idleTableCount > 0:
            table = self._idleTables.pop()
        self._logger.info('TableManager._borrowOneTable table=', table,
                          'idleTableCount=', self.idleTableCount,
                          'allTableCount=', self.allTableCount)
        return table

    def getTableSitdown(self, player):
        self._logger.info('TableManager.getTableSitdown player.userId=', player.userId,
                          'idleTableCount=', self.idleTableCount,
                          'allTableCount=', self.allTableCount)
        for countN in xrange(5):
            isLock = daobase.executeMixCmd('HGET', RELAXATION_MATCH_LOCK_KEY, str(self._room.roomId))
            if isLock:
                FTTasklet.getCurrentFTTasklet().sleepNb(0.2)
                if countN >= 4:
                    return None
            else:
                break
        try:
            # 加锁
            daobase.executeMixCmd('HSET', RELAXATION_MATCH_LOCK_KEY, str(self._room.roomId), 1)
            sitTable = None
            for t in xrange(self.waitTableCount):
                table = self.waitTableList[t]
                playerList = table.getPlayerList()
                isMeet = False
                isSameIp = False
                # 休闲赛中，桌子内不能匹配当场比赛已经在一起打过的人,同时相同ip的不会坐在一起
                for onePlayer in playerList:
                    if sessiondata.getClientIp(onePlayer.userId) == sessiondata.getClientIp(player.userId):
                        isSameIp = True
                    if onePlayer.meetPlayersMap.get(player.userId, None) == player:
                        isMeet = True
                if (not isMeet) and (not isSameIp) and table.idleSeatCount > 0:
                    table.sitdown(player)
                    sitTable = table
                    if table.idleSeatCount <= 0:
                        self._busyTableList.append(table)
                        del self.waitTableList[t]
                    break
                    # 如果在self.waitTableList 找到位置，那么就取self._idleTables里的
            if not sitTable:
                sitTable = self._borrowOneTable()
                if sitTable:
                    sitTable.sitdown(player)
                    self.waitTableList.append(sitTable)
            return sitTable
        finally:
            # 解锁
            daobase.executeMixCmd('HSET', RELAXATION_MATCH_LOCK_KEY, str(self._room.roomId), 0)

    def returnOneTable(self, table):
        if table:
            if table == self._allTableMap.get(table.tableId, None):
                table.clear()
                for x in xrange(self.busyTableCount):
                    if self._busyTableList[x] == table:
                        del self._busyTableList[x]
                        self._idleTables.append(table)
                        break
                for x in xrange(self.waitTableCount):
                    if self.waitTableList[x] == table:
                        del self.waitTableList[x]
                        self._idleTables.append(table)
                        break
                self._logger.info('TableManager.returnOneTable tableId = ', table.tableId,
                                  'idleTableCount=', self.idleTableCount,
                                  'allTableCount=', self.allTableCount)

    def findTable(self, tableId):
        return self._allTableMap.get(tableId, None)

    def standupFromTable(self, table, player):
        if (not table) or (not player):
            return
        if self._logger.isDebug():
            self._logger.debug('TableManager.standupFromTable player=', player, 'table.tableId=', table.tableId)
        if table in self._busyTableList:
            # 正在比赛的桌子会通过winlose消息退回桌子资源，这里过滤掉
            if self._logger.isDebug():
                self._logger.debug('TableManager.standupFromTable in self._busyTableList')
            return
        table.standup(player)
        if table.getPlayerCount() == 0:
            # 没有玩家在了，那么就归还吧
            self.returnOneTable(table)
