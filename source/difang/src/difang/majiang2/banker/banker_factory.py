# -*- coding=utf-8
'''
Created on 2016年9月23日
庄家规则
@author: zhaol
'''
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.banker.bank_host_next import MBankerHostNext
from difang.majiang2.banker.bank_host_win import MBankerHostWin
from difang.majiang2.banker.banker_random_remain import MBankerRandomRemain


class BankerFactory(object):
    # 初始随机 坐庄玩法
    RANDOM_REMAIN = 'random_remain'
    # 首局房主坐庄 赢家接庄
    HOST_WIN = 'host_win'
    # 首局房主坐庄 输了庄下家接庄
    HOST_NEXT = 'host_next'

    def __init__(self):
        super(BankerFactory, self).__init__()

    @classmethod
    def getBankerAI(cls, playMode):
        """庄家规则获取工厂
        输入参数：
            playMode - 玩法
        
        返回值：
            对应玩法的庄家管理规则
        """
        bankerType = cls.getBankerTypeByPlayMode(playMode)
        if bankerType == cls.RANDOM_REMAIN:
            return MBankerRandomRemain()
        if bankerType == cls.HOST_WIN:
            return MBankerHostWin()
        if bankerType == cls.HOST_NEXT:
            return MBankerHostNext()
        return MBankerRandomRemain()

    @classmethod
    def getBankerTypeByPlayMode(cls, playMode):
        if playMode == MPlayMode.HAERBIN \
                or playMode == MPlayMode.GUOBIAO \
                or playMode == MPlayMode.SICHUAN \
                or MPlayMode().isSubPlayMode(playMode, MPlayMode.KAWUXING):
            return cls.RANDOM_REMAIN
        elif playMode == MPlayMode.YUNNAN:
            return cls.HOST_WIN
        elif playMode == MPlayMode.ZHAOTONG:
            return cls.HOST_WIN
        elif playMode == MPlayMode.JIXI:
            return cls.HOST_NEXT
        return None
