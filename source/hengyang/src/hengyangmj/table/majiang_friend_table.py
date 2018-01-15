# -*- coding=utf-8 -*-
'''
Created on 2015年9月30日
麻将好友桌的牌桌，负责好友桌号的管理和好友桌赛制的调度。
@author: 赵良
'''

from difang.majiang2.table.majiang_friend_table import MajiangFriendTable
from difang.majiang2.table.run_mode import MRunMode
from hengyangmj.action_handler.action_handler_longnet import HYActionHandlerLongNet
from hengyangmj.hengyang_log import HYLog
from hengyangmj.table.majiang_table_observer import QuJingTableObserver  #
from hengyangmj.table.table_logic import HYMajiangTableLogic


class HYMajiangFriendTable(MajiangFriendTable):
    def __init__(self, tableId, room):
        super(HYMajiangFriendTable, self).__init__(tableId, room)

        # 逻辑处理者
        self.logic_table = HYMajiangTableLogic(self.maxSeatN, self.playMode, MRunMode.LONGNET)
        self.logic_table.setTableConfig(self._tableConf)
        self.logic_table.msgProcessor.setInfo(self.gameId, self.roomId, self.tableId, self.playMode, self.tableType,
                                              self.maxSeatN)
        self.logic_table.msgProcessor.setRoomInfo(self._roomConf, self._tableConf)

        # 指向本地的操作处理
        self.setActionHandler(HYActionHandlerLongNet()).setTable(self.logic_table)

        HYLog.debug("HYMajiangFriendTable's actionHandler has table:", self.actionHander.table)

        observer = QuJingTableObserver(self.gameId, self.roomId, self.tableId)
        self.setTableObserver(observer)
