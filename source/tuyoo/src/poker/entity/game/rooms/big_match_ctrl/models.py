# -*- coding:utf-8 -*-
'''
Created on 2014年9月17日

@author: zjgzzz@126.com
'''
from poker.entity.game.rooms.big_match_ctrl.const import WaitReason


class Player(object):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_WINLOSE = 2
    STATE_WAIT = 3
    STATE_OUT = 4

    WHEN_OUT_NORMAL = 0
    WHEN_OUT_ASS = 1

    def __init__(self, inst, userId, userName, signinTime, activeTime, clientId=''):
        self.inst = inst
        # 玩家用户ID
        self.userId = userId
        # 玩家用户名
        self.userName = userName
        # 玩家报名时间
        self.signinTime = signinTime
        # 用户最后活跃时间
        self.activeTime = signinTime
        # 玩家积分
        self.chip = 0
        # 玩家排名
        self.rank = 0
        # 积分排名
        self.chiprank = 0
        # 在桌子中的排名
        self.tableRank = 0
        # 当前阶段打的牌的计数器
        self.cardCount = 0
        # 用户等待时间
        self.waitTimes = 0
        # 状态
        self.state = Player.STATE_IDLE
        self.isenter = False
        self.locked = False
        # 玩家坐的座位
        self._seat = None
        self.group = None
        self.clientId = clientId
        self.signinParams = None
        self.snsId = None

        # 等待原因
        self.waitReason = WaitReason.UNKNOWN
        self.whenOut = Player.WHEN_OUT_NORMAL

        # 打赢的对手名
        self.beatDownUserName = ''

    @property
    def seat(self):
        return self._seat

    @property
    def table(self):
        return self._seat.table if self._seat else None

    @property
    def matchId(self):
        return self.inst.matchId

    def getSigninParam(self, name, defVal=None):
        return self.signinParams.get(name, defVal) if self.signinParams else defVal

    def __repr__(self):
        return str(self.userId)

    def __str__(self):
        return str(self.userId)

    def __unicode__(self):
        return unicode(self.userId)


class Seat(object):
    def __init__(self, table, seatId):
        self.table = table
        self.seatId = seatId
        self._location = '%s.%s.%s.%s' % (table.gameId, table.roomId, table.tableId, seatId)
        self._player = None

    @property
    def gameId(self):
        return self.table.gameId

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
        self.gameId = gameId
        # 房间ID
        self.roomId = roomId
        # 座位ID
        self.tableId = tableId
        # 所有座位
        self._seats = self._makeSeats(seatCount)
        # 空闲座位
        self._idleSeats = self._seats[:]
        # 使用该桌子的比赛
        self.group = None
        self.playTime = None
        self.ccrc = 0
        self._location = '%s.%s.%s' % (self.gameId, self.roomId, self.tableId)

    @property
    def location(self):
        return self._location

    @property
    def seats(self):
        return self._seats

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

    def standup(self, player):
        '''
        玩家离开桌子
        '''
        assert (player._seat is not None
                and player._seat.table == self)
        self._clearSeat(player._seat)

    @property
    def seatCount(self):
        '''
        座位数量
        '''
        return len(self._seats)

    def clear(self):
        for seat in self._seats:
            if seat._player:
                self._clearSeat(seat)

    def getIdleSeatCount(self):
        '''
        空闲座位数量
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
        playerList = []
        for seat in self._seats:
            if seat.player:
                playerList.append(seat.player)
        return playerList

    def getUserIdList(self):
        userIdList = []
        for seat in self._seats:
            if seat.player:
                userIdList.append(seat.player.userId)
        return userIdList

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
