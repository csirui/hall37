# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.table_state.state_haerbin import MTableStateHaerbin
from difang.majiang2.table_state.state_jixi import MTableStateJixi
from difang.majiang2.table_state.state_kawuxing import MTableStateKawuxing
from difang.majiang2.table_state.state_xuezhan import MTableStateXuezhan
from difang.majiang2.table_state.state_yunnan import MTableStateYunnan
from difang.majiang2.table_state.state_zhaotong import MTableStateZhaotong


class TableStateFactory(object):
    def __init__(self):
        super(TableStateFactory, self).__init__()

    @classmethod
    def getTableStates(cls, playMode):
        """发牌器获取工厂
        输入参数：
            playMode - 玩法
        
        返回值：
            对应玩法的牌桌状态
        """
        if playMode == MPlayMode.HAERBIN:
            return MTableStateHaerbin()
        elif playMode == MPlayMode.SICHUAN:
            return MTableStateXuezhan()
        elif playMode == MPlayMode.YUNNAN:
            return MTableStateYunnan()
        elif playMode == MPlayMode.ZHAOTONG:
            return MTableStateZhaotong()
        elif playMode == MPlayMode.JIXI:
            return MTableStateJixi()
        elif MPlayMode().isSubPlayMode(playMode, MPlayMode.KAWUXING):
            return MTableStateKawuxing()
