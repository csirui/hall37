# -*- coding=utf-8
"""
Created on 2016年9月23日
听牌规则
@author: zhaol
"""
from difang.majiang2.ai.ting import MTing
from difang.majiang2.ting_rule.ting_rule import MTingRule


class MTingSichuanRule(MTingRule):
    """胡牌规则
    """

    def __init__(self):
        super(MTingSichuanRule, self).__init__()

    def canTing(self, tiles, leftTiles, tile, magicTiles=list()):
        """子类必须实现
        参数：
        1）tiles 该玩家的手牌
        
        返回值：
        是否可以听牌，听牌详情
        """
        return MTing.canTing(tiles, leftTiles, self.winRuleMgr, tile, magicTiles)
