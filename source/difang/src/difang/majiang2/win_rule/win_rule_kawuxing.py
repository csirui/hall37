# -*- coding=utf-8
'''
Created on 2016年12月11日
庄家规则
@author: dongwei
'''
import copy

from difang.majiang2.ai.win import MWin
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.tile.tile import MTile
from difang.majiang2.win_rule.win_rule import MWinRule
from freetime.util import log as ftlog


class MWinRuleKawuxing(MWinRule):
    """卡五星胡牌
    多支持七对胡
    """

    def __init__(self):
        super(MWinRuleKawuxing, self).__init__()

    def isHu(self, tiles, tile, isTing, getTileType, magicTiles=[], tingNodes=[]):
        # 此处有坑，winPattern只有一种牌型，这样有问题，比如：[14,14,14,15,15,16,16,16,19,19,19,20,20]，最后抓15
        # 如果卡五星比碰碰胡番数高，此处应该算卡五星，所以isHu应该返回所有可能的胡的牌型，结算时计算最优的番型
        # 未来有时间需要调整一下

        # 先判断定制的逻辑，防止通用逻辑修改造成业务出错
        result, pattern = self.isQidui(tiles)
        if result:
            return result, pattern
        result, pattern = MWin.isHu(tiles[MHand.TYPE_HAND], magicTiles)
        if result:
            return result, pattern
        return False, []

    def isAddHu(self, player, tile):
        """卡五星麻将，抓到要胡的牌直接胡，不再要求确认"""
        if player.isTing():
            # [{'winTile': 11, 'winTileCount': 3, 'pattern': [[16, 16], [15, 16, 17], [14, 15, 16], [11, 12, 13]]}
            for winNode in player.winNodes:
                if winNode['winTile'] == tile:
                    ftlog.debug('isDirectHuAfterTing success winTile is', tile)
                    return True
        return False

    def isQidui(self, tiles):
        handTiles = copy.deepcopy(tiles[MHand.TYPE_HAND])
        handTilesArr = MTile.changeTilesToValueArr(handTiles)

        if len(handTiles) != 14:
            return False, []

        pattern = []
        for tile in range(MTile.TILE_MAX_VALUE):
            if handTilesArr[tile] == 1 or handTilesArr[tile] == 3:
                # 只要出现单数，必然不是七对
                return False, []
            if handTilesArr[tile] == 2:
                pattern.append([tile, tile])
            if handTilesArr[tile] == 4:
                # 和KawuxingOneResult配合
                pattern.extend([[tile, tile], [tile, tile]])
        return True, pattern


if __name__ == "__main__":
    tiles = [[11, 11, 13, 13, 15, 15, 18, 18, 19, 19, 24, 24, 24, 24], [], [], [], [], []]
    rule = MWinRuleKawuxing()
    result, pattern = rule.isHu(tiles, 24, True, MWinRule.WIN_BY_MYSELF)
    ftlog.debug(result, pattern)
    assert [[11, 11], [13, 13], [15, 15], [18, 18], [19, 19], [24, 24], [24, 24]] == pattern
