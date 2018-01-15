# -*- coding=utf-8 -*-
'''
Created on 2015年9月30日
牌桌观察者,继承自majiang2模块,用于管理需要向大厅发送的事件
@author: 赵良
'''
from difang.majiang2.table.majiang_table_observer import MajiangTableObserver

from qujiangmj.servers.util.rpc import table_events_remote


class QuJingTableObserver(MajiangTableObserver):
    def __init__(self, gameId, roomId, tableId):
        super(QuJingTableObserver, self).__init__(gameId, roomId, tableId)

    def onBeginGame(self, players, banker):
        """游戏开始"""
        for userId in players:
            table_events_remote.gamePlay(userId, self.gameId, self.roomId, self.tableId, banker)

    def onWinLoose(self):
        """结果"""
        pass
