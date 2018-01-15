# -*- coding=utf-8
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.tile.tile import MTile, human_tiles, HuTiles
from difang.majiang2.tile.tiles import M14
from difang.majiang2.win_rule.win_rule import MWinRule


class MWinRuleJiNan(MWinRule):
    """
    济南麻将
    2,5,8将胡牌
    """
    JIANG = set(human_tiles("2万5万8万2筒5筒8筒2条5条8条"))  # [2, 5, 8, 12, 15, 18, 22, 25, 28]

    def __init__(self, jiang258=True, dui7=True, dui7_258=True):
        """
        :param jiang258: 必须258为将牌
        :param dui7: 支持7对胡牌
        :param dui7_258: 7对胡牌必须也有258
        """
        super(MWinRuleJiNan, self).__init__()
        self.jiang258 = jiang258
        self.dui7 = dui7
        self.dui7_258 = dui7_258

    def isHu(self, tiles, last_tile, isTing, getTileType, magicTiles=list(), tingNodes=list()):
        hu_tiles = HuTiles()
        handTileArr = MTile.changeTilesToValueArr(tiles[MHand.TYPE_HAND])
        if not M14.find_first(handTileArr, hu_tiles,
                              M14.is7Dui if self.dui7 else M14.justPass,
                              M14.isPHu,
                              ):
            # 基本的胡牌类型都挂了
            return False, None
        dui_list = handTileArr.tiles_dui()
        if len(dui_list) == 0:
            # 没有将牌
            return False, []
        if len(hu_tiles) != 7 and not set(zip(*dui_list)[0]) & MWinRuleJiNan.JIANG:
            # 没有2,5,8将牌
            return False, []

        return True, hu_tiles
