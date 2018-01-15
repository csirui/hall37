# -*- coding=utf-8
'''
Created on 2016年9月23日
牌桌统计
@author: zhaol
'''
from difang.majiang2.table_statistic.statistic import MTableStatistic
from freetime.util import log as ftlog
from poker.entity.biz import bireport


class MTableStatisticLongNet(MTableStatistic):
    def __init__(self):
        super(MTableStatisticLongNet, self).__init__()

    def reportEvent(self, event, players, gameId, roomId, tableId):
        ftlog.debug('MTableStatisticLongNet.reportEvent event:', event
                    , ' players:', players
                    , ' gameId:', gameId
                    , ' roomId:', roomId
                    , ' tableId:', tableId
                    )

        uids = []
        for player in players:
            uids.append(player.userId)
            bireport.reportGameEvent(event
                                     , player.userId
                                     , gameId
                                     , roomId
                                     , tableId
                                     , 0, 0, 0, 0, []
                                     , player.clientId)

        if event == MTableStatistic.TABLE_START:
            bireport.tableStart(gameId, roomId, tableId, 0, uids)
        elif event == MTableStatistic.TABLE_WIN:
            bireport.tableWinLose(gameId, roomId, tableId, 0, uids)
