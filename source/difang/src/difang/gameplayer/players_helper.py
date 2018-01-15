# coding=UTF-8
'''
    玩家辅助模块
'''

__author__ = ['Zhou Hao']

import freetime.util.log as ftlog


class DiFangPlayersHelper(object):
    @classmethod
    def getSitPlayerIds(cls, table):
        return [table.seats[seatIndex].userId
                for seatIndex in range(table.cMaxSeatNum) if not table.seats[seatIndex].isEmptySeat()]

    @classmethod
    def getSitPlayers(cls, table):
        return [table.players[seatIndex]
                for seatIndex in range(table.cMaxSeatNum) if not table.seats[seatIndex].isEmptySeat()]

    @classmethod
    def getPlayingPlayers(cls, table):
        return [table.players[seatIndex]
                for seatIndex in range(table.cMaxSeatNum) if table.seats[seatIndex].isPlayingSeat()]

    @classmethod
    def getPlayingPlayersIds(cls, table):
        return [table.players[seatIndex].userId
                for seatIndex in range(table.cMaxSeatNum) if table.seats[seatIndex].isPlayingSeat()]

    @classmethod
    def getWaitingPlayersIds(cls, table):
        return [table.players[seatIndex].userId
                for seatIndex in range(table.cMaxSeatNum) if table.seats[seatIndex].isWaitingSeat()]

    @classmethod
    def getRobotUserIds(cls, table):
        return [player.userId for player in table.players if player.isRobot(player.userId)]

    @classmethod
    def getPlayerInfos(cls, table, **argd):
        """获取当前牌桌上所有玩家的信息，这些信息在 tableInfo/game_start/ 消息里要传给客户端
        """
        playerInfos = []
        for seatIndex in xrange(table.cMaxSeatNum):
            if not table.seats[seatIndex].isEmptySeat():
                item = table.players[seatIndex].getInfo()
                playerInfos.append(item)
            else:
                item = {"userId": 0}
                if not argd.get("ignoreEmpySeat", False):
                    playerInfos.append(item)

        return playerInfos

    @classmethod
    def playersWait(cls, table):
        for player in cls.getSitPlayers(table):
            player.wait()
            table.seats[player.seatIndex].setWaitingState()

    @classmethod
    def playersStart(cls, table):
        for player in cls.getSitPlayers(table):
            player.start()
            table.seats[player.seatIndex].setPlayingState()

    @classmethod
    def isAllReady(cls, table):
        for player in cls.getSitPlayers(table):
            if not player.isReady():
                if ftlog.is_debug():
                    ftlog.debug("|userId, state:", player.userId, player.state, caller=cls)
                return False
        return True
