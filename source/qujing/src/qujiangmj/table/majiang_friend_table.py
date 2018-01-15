# -*- coding=utf-8 -*-
'''
Created on 2015年9月30日
麻将好友桌的牌桌，负责好友桌号的管理和好友桌赛制的调度。
@author: 赵良
'''
from difang.majiang2.table.majiang_friend_table import MajiangFriendTable
from difang.majiang2.table.run_mode import MRunMode

from qujiangmj.table.majiang_table_observer import QuJingTableObserver
from qujiangmj.table.table_logic import QJMajiangTableLogic


class QJMajiangFriendTable(MajiangFriendTable):
    def __init__(self, tableId, room):
        super(QJMajiangFriendTable, self).__init__(tableId, room)
        self.logic_table = QJMajiangTableLogic(self.maxSeatN, self.playMode, MRunMode.LONGNET)
        self.logic_table.setTableConfig(self._tableConf)
        self.logic_table.msgProcessor.setInfo(self.gameId, self.roomId, self.tableId, self.playMode, self.tableType,
                                              self.maxSeatN)
        self.logic_table.msgProcessor.setRoomInfo(self._roomConf, self._tableConf)
        self.actionHander.setTable(self.logic_table)
        observer = QuJingTableObserver(self.gameId, self.roomId, self.tableId)
        self.setTableObserver(observer)
