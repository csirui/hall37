# -*- coding=utf-8
"""
Created on 2016年9月23日
听牌规则
@author: zhaol
"""
from difang.majiang2.ai.ting import MTing
from difang.majiang2.tile.tile import HandTiles, Tiles
from difang.majiang2.ting_rule.ting_rule import MTingRule
from difang.majiang2.win_rule.win_rule_haerbin import MWinRuleHaerbin
from freetime.util import log as ftlog


class MTingJiNanRule(MTingRule):
    """
    听牌规则
    1）听牌时, 将牌为2,5,8。
    """

    def canTing(self, tiles, leftTiles, cur_tile, magicTiles=list()):
        """
        :type tiles HandTiles
        :type leftTiles Tiles
        """
        # 通用规则
        ret, result = MTing.canTing(tiles, leftTiles, self.winRuleMgr, cur_tile, magicTiles)
        if ret:
            # 确定将牌
            pass
        return ret, result

    def __init__(self):
        super(MTingJiNanRule, self).__init__()


if __name__ == "__main__":
    def test():
        tiles = [[3, 4, 15, 5, 5, 6, 9, 9], [[26, 27, 28]], [[8, 8, 8]], [], [], []]
        rule = MTingJiNanRule()
        rule.setWinRuleMgr(MWinRuleHaerbin())
        ftlog.debug(rule.canTing(tiles, [], 4, []))


    test()
