# -*- coding:utf-8 -*-
'''
Created on 2016年1月15日

@author: zhaojiangang
'''
from poker.entity.game.rooms.group_match_ctrl.const import WaitReason
from poker.entity.game.rooms.group_match_ctrl.utils import Logger


class Signer(object):
    '''
    报名用户
    '''

    def __init__(self, userId, instId, signinTime):
        self.userId = userId
        self.instId = instId
        self.signinTime = signinTime
        self.isEnter = False
        self.isLocked = False
        self.clientId = ''
        self.userName = ''
        self.inst = None
        self.feeItem = None


class Riser(object):
    '''
    晋级用户
    '''

    def __init__(self, userId, score, rank, tableRank):
        self.userId = userId
        self.score = score
        self.rank = rank
        self.tableRank = tableRank

    @classmethod
    def fromPlayer(cls, player):
        return Riser(player.userId, player.score, player.rank, player.tableRank)


class Player(Signer):
    '''
    比赛中的用户
    '''
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_WINLOSE = 2
    STATE_WAIT = 3
    STATE_OUT = 4

    WHEN_OUT_NORMAL = 0
    WHEN_OUT_ASS = 1

    def __init__(self, userId, instId, signinTime):
        super(Player, self).__init__(userId, instId, signinTime)
        # 玩家用户名
        self.userName = ''
        # 玩家积分
        self.score = 0
        # 玩家排名
        self.rank = 0
        # 积分排名
        self.scoreRank = 0
        # 在桌子中的排名
        self.tableRank = 0
        # 当前阶段打的牌的计数器
        self.cardCount = 0
        # 用户等待时间
        self.waitTimes = 0
        self.isenter = False
        self.locked = False
        # 用户当前clientId
        self.clientId = ''
        # 报名参数
        self.signinParams = None
        # snsId
        self.snsId = None
        # 等待原因
        self.waitReason = WaitReason.UNKNOWN
        # 为什么淘汰
        self.whenOut = Player.WHEN_OUT_NORMAL

        # 状态
        self._state = Player.STATE_IDLE
        # 玩家坐的座位
        self._seat = None
        # 当前分组
        self._group = None

        self.beatDownUserName = ''

    @property
    def state(self):
        return self._state

    @property
    def table(self):
        return self._seat.table if self._seat else None

    @property
    def seat(self):
        return self._seat

    @property
    def group(self):
        return self._group

    def updateByRiser(self, riser):
        assert (isinstance(riser, Riser))
        self.score = riser.score
        self.rank = riser.rank
        self.tableRank = riser.tableRank


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
    def __init__(self, gameId, roomId, tableId, seatCount):
        # 游戏ID
        self._gameId = gameId
        # 房间ID
        self._roomId = roomId
        # 座位ID
        self._tableId = tableId
        # 所有座位
        self._seats = self._makeSeats(seatCount)
        # 空闲座位
        self._idleSeats = self._seats[:]
        # 使用该桌子的比赛
        self._group = None
        # 当前牌局开始时间
        self.playTime = None
        # 当前牌局ccrc
        self.ccrc = 0
        # 桌子Location
        self._location = '%s.%s.%s' % (self.gameId, self.roomId, self.tableId)

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

    def getPlayingPlayerCount(self):
        '''
        获取PLAYING状态的玩家数量
        '''
        count = 0
        for seat in self._seats:
            if seat.player and seat.player.state == Player.STATE_PLAYING:
                count += 1
        return count

    def getPlayingPlayerList(self):
        playerList = []
        for seat in self._seats:
            if seat.player and seat.player.state == Player.STATE_PLAYING:
                playerList.append(seat.player)
        return playerList

    def getPlayerList(self):
        '''
        获取本桌的所有player
        '''
        return [seat.player for seat in self.seats if seat.player]

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
            seats.append(Seat(self, i + 1))
        return seats


class TableManager(object):
    def __init__(self, room, tableSeatCount):
        self._room = room
        self._tableSeatCount = tableSeatCount
        self._idleTables = []
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
        return max(0, self.allTableCount - self.idleTableCount())

    def getTableCountPerRoom(self):
        return len(self._allTableMap) / max(1, self.roomCount)

    def addTables(self, roomId, baseId, count):
        if count > 0:
            self._roomIds.add(roomId)
        for i in xrange(count):
            tableId = baseId + i + 1  # 新框架里tableId 从 1开始计数， 0表示队列。
            table = Table(self.gameId, roomId, tableId, self._tableSeatCount)
            self._idleTables.append(table)
            self._allTableMap[tableId] = table

    def borrowTables(self, count):
        assert (self.idleTableCount >= count)
        ret = self._idleTables[0:count]
        self._idleTables = self._idleTables[count:]
        self._logger.info('TableManager.borrowTables',
                          'count=', count,
                          'idleTableCount=', self.idleTableCount,
                          'allTableCount=', self.allTableCount)
        return ret

    def returnTables(self, tables):
        for table in tables:
            assert (self._allTableMap.get(table.tableId, None) == table)
            assert (not table.getPlayerList())
            self._idleTables.append(table)
        self._logger.info('TableManager.returnTables',
                          'count=', len(tables),
                          'idleTableCount=', self.idleTableCount,
                          'allTableCount=', self.allTableCount)

    def findTable(self, roomId, tableId):
        return self._allTableMap.get(tableId, None)
