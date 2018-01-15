# -*- coding=utf-8
"""
Created on 2016年9月23日
庄家规则
@author: zhaol
"""
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.ting_rule.ting_rule_haerbin import MTingHaerbinRule
from difang.majiang2.ting_rule.ting_rule_jixi import MTingJixiRule
from difang.majiang2.ting_rule.ting_rule_kawuxing import MTingKawuxingRule
from difang.majiang2.ting_rule.ting_rule_sichuan import MTingSichuanRule
from difang.majiang2.ting_rule.ting_rule_simple import MTingSimpleRule
from difang.majiang2.win_rule.win_rule_factory import MWinRuleFactory
from freetime.util import log as ftlog


class MTingRuleFactory(object):
    def __init__(self):
        super(MTingRuleFactory, self).__init__()

    @classmethod
    def getTingRule(cls, playMode):
        """判和规则获取工厂
        输入参数：
            playMode - 玩法
        
        返回值：
            对应玩法的判和规则
        """
        if playMode == MPlayMode.HAERBIN:
            return MTingHaerbinRule()
        elif playMode == MPlayMode.JIXI:
            return MTingJixiRule()
        elif playMode == MPlayMode.SICHUAN:
            return MTingSichuanRule()
        elif MPlayMode().isSubPlayMode(playMode, MPlayMode.KAWUXING):
            return MTingKawuxingRule()
        else:
            return MTingSimpleRule()
        return None


def tingHaerbin():
    tingRule = MTingRuleFactory.getTingRule(MPlayMode.HAERBIN)
    winRule = MWinRuleFactory.getWinRule(MPlayMode.HAERBIN)
    tingRule.setWinRuleMgr(winRule)
    tiles = [[4, 4, 4, 5, 13, 14, 15, 29], [[23, 24, 25]], [[27, 27, 27]], [], [], []]
    leftTiles = [3, 4, 4, 4, 7, 8, 8, 9, 14, 14, 16, 17, 18, 19, 21, 21, 22, 23, 24, 24, 25, 27, 28, 29]
    result, resultDetail = tingRule.canTing(tiles, leftTiles, 7, [])
    ftlog.debug(result)
    if result:
        ftlog.debug(resultDetail)


if __name__ == "__main__":
    tingHaerbin()
