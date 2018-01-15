# -*- coding=utf-8
"""
Created on 2016年9月23日
庄家规则
@author: zhaol
"""
from difang.majiang2.ai.win import MWin
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.win_rule.win_rule import MWinRule


class MWinRuleSimple(MWinRule):
    """开局随机庄家，之后连庄的规则
    庄家赢，连庄
    闲家赢，闲家坐庄
    """

    def __init__(self):
        super(MWinRuleSimple, self).__init__()

    def isHu(self, tiles, tile, isTing, getTileType, magicTiles=list(), tingNodes=list()):
        result, pattern = MWin.isHu(tiles[MHand.TYPE_HAND], magicTiles)
        return result, pattern
