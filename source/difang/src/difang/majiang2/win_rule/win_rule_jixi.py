# -*- coding=utf-8
"""
Created on 2016年9月23日
庄家规则
@author: zhaol
"""
from difang.majiang2.ai.win import MWin
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.tile.tile import MTile, human_tiles, new_hand_tails
from difang.majiang2.win_rule.win_rule import MWinRule
from freetime.util import log as ftlog


class MWinRuleJixi(MWinRule):
    """
    鸡西玩法的和牌规则
    1）没听牌 不和
    2）和牌不可以过
    3）和牌完全从听中去和牌番型
    """

    def __init__(self):
        super(MWinRuleJixi, self).__init__()

    def isHu(self, tiles, tile, isTing, getTileType, magicTiles=[], tingNodes=[]):
        if not isTing:
            # 没听牌 不和
            return False, []

        # 鸡西打宝炮(先不支持 之后通过配置项目支持) 玩家上听后没有听牌的玩家打出宝牌 则听牌玩家和牌
        # 听牌之后自摸到宝牌 自动和牌
        if isTing and getTileType == MWinRule.WIN_BY_MYSELF:
            if tile in magicTiles:
                # 听牌并且是宝牌，和牌
                return True, []

        # 从tingNode中判断，如果是听规则中的才算胡
        if len(tingNodes) > 0:
            hasTile = False
            pattern = []
            # [{'winTile': 16, 'winTileCount': 0, 'pattern': [[16, 17, 18], [12, 12]]}, {'winTile': 19, 'winTileCount': 0, 'pattern': [[17, 18, 19], [12, 12]]}]
            for tingNode in tingNodes:
                if tingNode['winTile'] == tile:
                    hasTile = True
                    pattern = tingNode['pattern']
                    break
            if hasTile:
                return True, pattern

        result, pattern = MWin.isHu(tiles[MHand.TYPE_HAND])
        if not result:
            return False, []

        return True, pattern

    def isMagicAfertTingHu(self, isTing, winNodes, magicTiles):
        if len(magicTiles) == 0:
            # ftlog.debug('isMagicAfertTingHu magcicTile is zero')
            return False
        magicTile = magicTiles[0]
        if isTing:
            # [{'winTile': 1, 'winTileCount': 3, 'pattern': [[6, 6], [5, 6, 7], [4, 5, 6], [1, 2, 3]]}
            for winNode in winNodes:
                if winNode['winTile'] == magicTile:
                    ftlog.debug('isMagicAfertTingHu success magcicTile is', magicTile)
                    return True
        return False

    # 三人麻将无对胡
    def isWuDuiHu(self, allTiles, winTile):
        huSeatId = -1
        for seatId, playerTiles in enumerate(allTiles):
            handTiles = playerTiles[MHand.TYPE_HAND]
            handTilesArr = MTile.changeTilesToValueArr(handTiles)
            huSeatId = seatId
            for handTile in handTiles:
                if handTilesArr[handTile] >= 2:
                    huSeatId = -1
                    break

        if huSeatId >= 0:
            return True, huSeatId

        return False, -1

    def canWinAfterChiPengGang(self, tiles):
        """吃完之后是否能和牌"""

        handTiles = tiles[MHand.TYPE_HAND]
        count = len(handTiles) - 2

        # 飘可以手把一
        if count == 1:
            chiTiles = tiles[MHand.TYPE_CHI]
            if len(chiTiles) == 0:
                return True
            else:
                return False

        if count < 4:
            return False

        return True


if __name__ == "__main__":
    def test():
        tiles = new_hand_tails(human_tiles("幺鸡二条三条二万二万五万六万七万7筒八筒9筒5条6条"))
        rule = MWinRuleJixi()
        ftlog.debug(rule.isHu(tiles, 2, True, human_tiles("4条")))


    test()
