# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''
from difang.majiang2.table_state.state import MTableState


class MTableStateXueliu(MTableState):
    def __init__(self):
        super(MTableStateXueliu, self).__init__()
        # 血战玩法
        self.setState(MTableState.TABLE_STATE_DROP)
        # 碰
        self.setState(MTableState.TABLE_STATE_PENG)
        # 杠
        self.setState(MTableState.TABLE_STATE_GANG)
        # 定缺
        self.setState(MTableState.TABLE_STATE_ABSENCE)
        # 和
        self.setState(MTableState.TABLE_STATE_HU)
        # 和牌后血流成河
        self.setState(MTableState.TABLE_STATE_XUELIU)
