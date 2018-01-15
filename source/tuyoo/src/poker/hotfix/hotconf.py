# -*- coding: utf-8 -*-

from poker.entity.dao import sessiondata
from poker.entity.game.rooms.relaxation_match_ctrl.models import TableManager


def getTableSitdown(self, player):
    self._logger.info('TableManager.getTableSitdown player.userId=', player.userId,
                      'idleTableCount=', self.idleTableCount,
                      'allTableCount=', self.allTableCount)
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
        if (not isMeet) and (not isSameIp):
            table.sitdown(player)
            sitTable = table
            if table.getPlayerCount() == table.seatCount:
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


TableManager.getTableSitdown = getTableSitdown
