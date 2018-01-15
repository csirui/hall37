# -*- coding=utf-8
'''
Created on 2016年9月23日
听牌规则
@author: zhaol
'''
from difang.majiang2.ai.ting import MTing
from difang.majiang2.tile.tile import MTile
from difang.majiang2.ting_rule.ting_rule import MTingRule
from difang.majiang2.win_rule.win_rule_kawuxing import MWinRuleKawuxing
from freetime.util import log as ftlog


class MTingKawuxingRule(MTingRule):
    """胡牌规则，此处听牌和亮牌一个含义
    """

    def __init__(self):
        super(MTingKawuxingRule, self).__init__()

    def canTing(self, tiles, leftTiles, tile, magicTiles=[]):
        if len(leftTiles) < 12:
            # 小于12张不能亮牌/听牌
            return False, []
        isTing, tingResults = MTing.canTing(MTile.cloneTiles(tiles), leftTiles, self.winRuleMgr, tile, magicTiles)
        ftlog.debug('MTingKawuxingRule.canTing using MTing isTing:', isTing, ' tingResults:', tingResults)
        return isTing, tingResults


if __name__ == "__main__":
    tiles = [[11, 11, 13, 13, 15, 15, 18, 18, 19, 19, 22, 22, 24, 29], [], [], [], [], []]
    rule = MTingKawuxingRule()
    rule.setWinRuleMgr(MWinRuleKawuxing())
    isTing, tingResults = rule.canTing(tiles, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 22, [])
    ftlog.debug(isTing, tingResults)
    assert True == isTing
    isTing, tingResults = rule.canTing(tiles, [0, 0, 0, 0], 22, [])
    ftlog.debug(isTing, tingResults)
    assert False == isTing
