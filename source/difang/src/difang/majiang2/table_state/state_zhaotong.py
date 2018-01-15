# -*- coding=utf-8
'''
Created on 2016年12月3日

@author: zhangwei
'''
from difang.majiang2.table_state.state import MTableState


class MTableStateZhaotong(MTableState):
    def __init__(self):
        super(MTableStateZhaotong, self).__init__()
        # 云南昭通麻将
        self.setState(MTableState.TABLE_STATE_DROP)
        # 碰
        self.setState(MTableState.TABLE_STATE_PENG)
        # 杠
        self.setState(MTableState.TABLE_STATE_GANG)
        # 抢杠和
        self.setState(MTableState.TABLE_STATE_QIANGGANG)
        # 和
        self.setState(MTableState.TABLE_STATE_HU)
        # 血战
        self.setState(MTableState.TABLE_STATE_XUEZHAN)
        # 换碰杠牌中的癞子
        self.setState(MTableState.TABLE_STATE_CHANGE_MAGIC)
