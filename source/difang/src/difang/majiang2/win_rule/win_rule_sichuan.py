# -*- coding=utf-8
"""
Created on 2016年9月23日
庄家规则
@author: zhaol
"""
from difang.majiang2.ai.win import MWin
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.tile.tile import MTile
from difang.majiang2.win_rule.win_rule import MWinRule
from freetime.util import log as ftlog


class MWinRuleSichuan(MWinRule):
    """
    开局随机庄家，之后连庄的规则
    庄家赢，连庄
    闲家赢，闲家坐庄
    """

    def __init__(self):
        super(MWinRuleSichuan, self).__init__()

    def isHu(self, tiles, tile, isTing, getTileType, magicTiles=list(), tingNodes=list()):
        result, rePattern = MWin.isHu(tiles[MHand.TYPE_HAND])
        if not result:
            return False, []

        # 分析花色
        tileArr = MTile.changeTilesToValueArr(MHand.copyAllTilesToList(tiles))
        colors = MTile.getColorCount(tileArr)
        ftlog.debug('MWinRuleSichuan.isHu colors:', colors)

        if colors <= 2:
            # 花色缺门，可以和
            return True, rePattern
        return False, []
