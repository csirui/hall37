# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''
from difang.majiang2.action_handler.action_handler import ActionHandler
from difang.majiang2.msg_handler.msg import MMsg
from difang.majiang2.table_state.state import MTableState
from freetime.util import log as ftlog


class MMsgConsole(MMsg):
    def __init__(self):
        super(MMsgConsole, self).__init__()

    def table_call_add_card(self, player, tile, state, seatId, timeOut, actionId, extendInfo, changeInfo=None):
        """通知庄家游戏开始
        参数
        player - 庄家
        tile - 摸牌
        """
        ftlog.debug('seat:', player.curSeatId)
        ftlog.debug(player.printTiles())
        ftlog.debug('Add tile:', tile, ' U can:')
        if state & MTableState.TABLE_STATE_CHI:
            ftlog.debug('CHI, enter ', ActionHandler.ACTION_CHI)

        if state & MTableState.TABLE_STATE_PENG:
            ftlog.debug('PENG, enter ', ActionHandler.ACTION_PENG)

        if state & MTableState.TABLE_STATE_GANG:
            ftlog.debug('GANG, enter ', ActionHandler.ACTION_GANG)

        if state & MTableState.TABLE_STATE_HU:
            ftlog.debug('HU, enter ', ActionHandler.ACTION_HU)

        if state & MTableState.TABLE_STATE_DROP:
            ftlog.debug('DROP, enter ', ActionHandler.ACTION_DROP)

    def table_call_add_card_broadcast(self, seatId, timeOut, actionId, userId, tile, changeInfo=None):
        """通知其他人游戏开始
        参数
        pBanker - 庄家
        player - 待通知玩家
        tile - 庄家摸牌
        """
        pass

    def table_call_drop(self, seatId, player, tile, state, extendInfo, actionId, timeOut):
        """通知玩家出牌
        参数：
            player - 做出牌操作的玩家
        """
        if state == MTableState.TABLE_STATE_NEXT:
            return

        ftlog.debug('seat:', player.curSeatId)
        ftlog.debug(player.printTiles())
        ftlog.debug('Drop by other player:', tile, ' U can:')

        if state & MTableState.TABLE_STATE_CHI:
            ftlog.debug('CHI, enter ', ActionHandler.ACTION_CHI)

        if state & MTableState.TABLE_STATE_PENG:
            ftlog.debug('PENG, enter ', ActionHandler.ACTION_PENG)

        if state & MTableState.TABLE_STATE_GANG:
            ftlog.debug('GANG, enter ', ActionHandler.ACTION_GANG)

        if state & MTableState.TABLE_STATE_HU:
            ftlog.debug('HU, enter ', ActionHandler.ACTION_HU)

        if state & MTableState.TABLE_STATE_DROP:
            ftlog.debug('DROP, enter ', ActionHandler.ACTION_DROP)

        ftlog.debug('CANCEL, enter ', 0)
