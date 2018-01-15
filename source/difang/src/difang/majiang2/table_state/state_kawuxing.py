# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''
from difang.majiang2.table_state.state import MTableState


class MTableStateKawuxing(MTableState):
    def __init__(self):
        super(MTableStateKawuxing, self).__init__()
        # 卡五星玩法
        self.setState(MTableState.TABLE_STATE_DROP)
        # 碰
        self.setState(MTableState.TABLE_STATE_PENG)
        # 杠
        self.setState(MTableState.TABLE_STATE_GANG)
        # 听
        self.setState(MTableState.TABLE_STATE_TING)
        # 和
        self.setState(MTableState.TABLE_STATE_HU)
        # 和牌后游戏结束
        self.setState(MTableState.TABLE_STATE_GAME_OVER)
