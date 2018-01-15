# -*- coding=utf-8
'''
Created on 2016年9月23日
庄家规则
@author: zhaol
'''
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.win_loose_result.haerbin_one_result import MHaerbinOneResult
from difang.majiang2.win_loose_result.jixi_one_result import MJixiOneResult
from difang.majiang2.win_loose_result.kawuxing_one_result import MKawuxingOneResult
from difang.majiang2.win_loose_result.one_result import MOneResult
from difang.majiang2.win_loose_result.yunnan_one_result import MYunnanOneResult
from difang.majiang2.win_loose_result.zhaotong_one_result import MZhaotongOneResult


class MOneResultFactory(object):
    def __init__(self):
        super(MOneResultFactory, self).__init__()

    @classmethod
    def getOneResult(cls, playMode):
        """判和规则获取工厂
        输入参数：
            playMode - 玩法
        
        返回值：
            对应玩法的判和规则
        """
        if playMode == MPlayMode.HAERBIN:
            return MHaerbinOneResult()
        elif playMode == MPlayMode.YUNNAN:
            return MYunnanOneResult()
        elif playMode == MPlayMode.ZHAOTONG:
            return MZhaotongOneResult()
        elif playMode == MPlayMode.JIXI:
            return MJixiOneResult()
        if MPlayMode().isSubPlayMode(playMode, MPlayMode.KAWUXING):
            return MKawuxingOneResult()
        return MOneResult()
