# -*- coding=utf-8
'''
Created on 2016年9月23日
庄家规则
@author: zhaol
'''
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.win_rule.win_rule_haerbin import MWinRuleHaerbin
from difang.majiang2.win_rule.win_rule_jixi import MWinRuleJixi
from difang.majiang2.win_rule.win_rule_kawuxing import MWinRuleKawuxing
from difang.majiang2.win_rule.win_rule_sichuan import MWinRuleSichuan
from difang.majiang2.win_rule.win_rule_simple import MWinRuleSimple
from difang.majiang2.win_rule.win_rule_yunnan import MWinRuleYunnan
from difang.majiang2.win_rule.win_rule_zhaotong import MWinRuleZhaotong


class MWinRuleFactory(object):
    def __init__(self):
        super(MWinRuleFactory, self).__init__()

    @classmethod
    def getWinRule(cls, playMode):
        """判和规则获取工厂
        输入参数：
            playMode - 玩法
        
        返回值：
            对应玩法的判和规则
        """
        if playMode == MPlayMode.HAERBIN:
            return MWinRuleHaerbin()
        elif playMode == MPlayMode.SICHUAN:
            return MWinRuleSichuan()
        elif playMode == MPlayMode.YUNNAN:
            return MWinRuleYunnan()
        elif playMode == MPlayMode.ZHAOTONG:
            return MWinRuleZhaotong()
        elif playMode == MPlayMode.JIXI:
            return MWinRuleJixi()
        elif MPlayMode().isSubPlayMode(playMode, MPlayMode.KAWUXING):
            return MWinRuleKawuxing()
        else:
            return MWinRuleSimple()
        return None
