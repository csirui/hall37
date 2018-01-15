# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''
from difang.majiang2.table.table_config_define import MTDefine
from difang.majiang2.table_state.state import MTableState
from freetime.util import log as ftlog

"""
操作的基类
"""


class MProcessor(object):
    def __init__(self):
        super(MProcessor, self).__init__()
        self.__action_id = 0
        self.__playsers = []
        self.__time_out = 0
        self.__table_tile_mgr = None

    def setTableTileMgr(self, tableTileMgr):
        """设置牌局手牌管理器"""
        self.__table_tile_mgr = tableTileMgr

    @property
    def tableTileMgr(self):
        return self.__table_tile_mgr

    @property
    def actionID(self):
        """操作ID，作为当前操作有效性的标记"""
        return self.__action_id

    def setActionID(self, actionID):
        """设置操作ID"""
        self.__action_id = actionID

    @property
    def timeOut(self):
        """获取超时时间"""
        return self.__time_out

    def setTimeOut(self, timeOut):
        """设置超时"""
        self.__time_out = timeOut

    def updateTimeOut(self, deta):
        """更新超时"""
        self.__time_out += deta
        if self.__time_out < 0:
            self.__time_out = 0

    @property
    def players(self):
        """玩家，由牌桌同步"""
        return self.__playsers

    def setPlayers(self, players):
        """设置玩家"""
        self.__playsers = players

    def hasAutoDecideAction(self, curSeat, trustTeeSet):
        """是否有托管的行为"""
        return MTDefine.INVALID_SEAT

    def isUserAutoDecided(self, seatId, trustTeeSet, state=MTableState.TABLE_STATE_NEXT, response=False):
        """
        判断用户是否由系统托管
        1）用户自己为托管状态则托管
        2）用户未托管，超时，则判断超时托管配置
        2.1）超时托管，则过关
        2.2）超时不托管，则不托管
        3）好友桌不会设置用户托管状态
        """
        if response:
            ftlog.debug('User responsed, isUserAutoDecided ok....')
            return True

        if self.players[seatId].autoDecide or self.players[seatId].isTing():
            ftlog.debug('MProcessor.isUserAutoDecided user autoDecide, decide:', self.players[seatId].autoDecide
                        , ' isTing:', self.players[seatId].isTing())
            if self.players[seatId].userId > 10000 and state & MTableState.TABLE_STATE_HU:
                return False

            return True

        if self.timeOut:
            # 未超时
            return False

        if self.players[seatId].userId < 10000:
            ftlog.debug('MProcessor.isUserAutoDecided robot:', self.players[seatId].userId)
            return True

        if trustTeeSet == MTDefine.NEVER_TIMEOUT:
            # 超时不托管
            return False

        ftlog.debug('MProcessor.isUserAutoDecided last return True')
        return True
