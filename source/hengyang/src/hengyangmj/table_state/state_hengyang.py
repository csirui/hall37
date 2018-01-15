# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: nick.kai.lee
'''
from difang.majiang2.table_state.state import MTableState


class MTableStateHengYang(MTableState):
    def __init__(self):
        super(MTableStateHengYang, self).__init__()
        # 云南曲靖麻将
        self.setState(MTableState.TABLE_STATE_DROP)
        # 吃
        self.setState(MTableState.TABLE_STATE_CHI)
        # 碰
        self.setState(MTableState.TABLE_STATE_PENG)
        # 杠
        self.setState(MTableState.TABLE_STATE_GANG)
        # 翻屁股
        self.setState(MTableState.TABLE_STATE_FANPIGU)
        # 抢杠和
        self.setState(MTableState.TABLE_STATE_QIANGGANG)
        # 和
        self.setState(MTableState.TABLE_STATE_HU)
        # 和牌后游戏结束
        self.setState(MTableState.TABLE_STATE_GAME_OVER)
