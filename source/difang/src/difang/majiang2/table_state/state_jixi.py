# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''
from difang.majiang2.table_state.state import MTableState


class MTableStateJixi(MTableState):
    def __init__(self):
        super(MTableStateJixi, self).__init__()
        # 鸡西玩法
        self.setState(MTableState.TABLE_STATE_DROP)
        # 吃
        self.setState(MTableState.TABLE_STATE_CHI)
        # 碰
        self.setState(MTableState.TABLE_STATE_PENG)
        # 杠
        self.setState(MTableState.TABLE_STATE_GANG)
        # 听
        self.setState(MTableState.TABLE_STATE_TING)
        # 抢听
        self.setState(MTableState.TABLE_STATE_GRABTING)
        # 抢杠和(只有特大夹可以抢杠和)
        self.setState(MTableState.TABLE_STATE_QIANGGANG)
        # 粘
        self.setState(MTableState.TABLE_STATE_ZHAN)
        # 和
        self.setState(MTableState.TABLE_STATE_HU)
        # 和牌后游戏结束
        self.setState(MTableState.TABLE_STATE_GAME_OVER)
