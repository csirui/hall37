# -*- coding=utf-8
'''
Created on 2016年11月18日
庄家规则
@author: zhangwei
'''
import copy

from difang.majiang2.ai.win import MWin
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.table_tile.table_tile import MTableTile
from difang.majiang2.tile.tile import MTile
from difang.majiang2.win_rule.win_rule import MWinRule
from freetime.util import log as ftlog


class MWinRuleZhaotong(MWinRule):
    """开局随机庄家，之后连庄的规则
    庄家赢，连庄
    闲家赢，闲家坐庄
    """

    def __init__(self):
        super(MWinRuleZhaotong, self).__init__()
        # 昭通血站胡牌的人
        self.__hasHu_Data = {}

    def isHu(self, tiles, tile, isTing, getTileType, magicTiles=[], tingNodes=[]):
        """
        tiles:玩家所有的牌,但是手牌是加入了要胡的那张牌的
        """
        # 昭通无听牌
        ftlog.debug('MWinRuleZhaotong.isHu tiles:', tiles
                    , ' tile:', tile
                    , ' magicTils:', magicTiles
                    , ' getTileType:', getTileType)

        if getTileType != MWinRule.WIN_BY_MYSELF and MTableTile.isMagicTile(tile, magicTiles):
            # 如果是听用,不能胡
            return False, []

            # 先查花色
        playerAllTiles = []
        playerAllTiles.extend(tiles[MHand.TYPE_HAND])
        for chi in tiles[MHand.TYPE_CHI]:
            playerAllTiles.extend(chi)
        for peng in tiles[MHand.TYPE_PENG]:
            playerAllTiles.extend(peng)
        for gang in tiles[MHand.TYPE_GANG]:
            playerAllTiles.extend(gang['pattern'])
        colorStateWithMagic = MTile.getColorCount(MTile.changeTilesToValueArr(playerAllTiles))
        magicCount, tempTiles = MTableTile.getMagicTileCountInTiles(playerAllTiles, magicTiles)
        colorState = MTile.getColorCount(MTile.changeTilesToValueArr(tempTiles))
        ftlog.debug("MWinRuleZhaotong.isHu colorState = ", colorState
                    , "playerAllTiles = ", playerAllTiles
                    , "tempTiles = ", tempTiles
                    , "colorStateWithMagic = ", colorStateWithMagic
                    , "magicCount = ", magicCount)
        # 必须缺一门才能胡牌
        if colorState >= 3:
            ftlog.debug("MWinRuleZhaotong.isHu men >= 3 can not hu")
            return False, []

        result1, pattern1 = MWinRuleZhaotong.checkHuByMagicTiles(tiles, magicTiles)
        #         result2, pattern2 = MWinRuleZhaotong.checkHuByMagicTiles(tiles, [])
        #         if colorStateWithMagic >= 3:
        #             if result1 and not result2:
        #                 return result1, pattern1
        #             else:
        #                 return False, []
        #         else:
        #             if result1:
        #                 return result1, pattern1
        #             else:
        #                 return False, []
        if result1:
            return result1, pattern1
        #             if getTileType != MWinRule.WIN_BY_MYSELF:
        #                 hasMagic = False
        #                 for magicTile in magicTiles:
        #                     if magicTile in tiles[MHand.TYPE_HAND]:
        #                         hasMagic = True
        #                 if hasMagic:
        #                     # 点炮和抢杠胡要检查是不是叫听用,如果叫听用,可以胡任意牌,采用抽3张牌测试的方式,如果通过就认为是叫听用
        #                     testTiles = []
        #                     if tile/10 == 0:
        #                         testTiles.append(2)
        #                         testTiles.append(6)
        #                         testTiles.append(9)
        #                     elif tile/10 == 1:
        #                         testTiles.append(12)
        #                         testTiles.append(14)
        #                         testTiles.append(17)
        #                     elif tile/10 == 2:
        #                         testTiles.append(22)
        #                         testTiles.append(24)
        #                         testTiles.append(28)
        #                     else:
        #                         return False, []
        #                     dandiao = True
        #                     for testTile in testTiles:
        #                         tempDandiao = copy.deepcopy(tiles)
        #                         if tile in tempDandiao[MHand.TYPE_HAND]:
        #                             tempDandiao[MHand.TYPE_HAND].remove(tile)
        #                         tempDandiao[MHand.TYPE_HAND].append(testTile)
        #                         resultDandiao, _ = MWinRuleZhaotong.checkHuByMagicTiles(tempDandiao, magicTiles)
        #                         if not resultDandiao:
        #                             dandiao = False
        #                     if not dandiao:
        #                         return result1, pattern1
        #                 else:
        #                     return result1, pattern1
        #             else:
        #                 return result1, pattern1
        return False, []

    @classmethod
    def isPairs(cls, tiles, magicTiles):
        if len(tiles[MHand.TYPE_CHI]) != 0:
            return False
        if len(tiles[MHand.TYPE_PENG]) != 0:
            return False
        if len(tiles[MHand.TYPE_GANG]) != 0:
            return False
        pairTiles = copy.deepcopy(tiles[MHand.TYPE_HAND])

        haveMagicCount = 0
        for magicTile in magicTiles:
            while magicTile in pairTiles:
                pairTiles.remove(magicTile)
                haveMagicCount += 1
        ftlog.debug("win_rule_zhaotong::isPairs pairTiles = ", pairTiles, "haveMagicCount =", haveMagicCount)
        tileArr = MTile.changeTilesToValueArr(pairTiles)
        for count in tileArr:
            if count % 2 == 0:
                continue
            else:
                if haveMagicCount <= 0:
                    return False
                else:
                    haveMagicCount -= 1
                    continue
        return True

    @classmethod
    def checkHuByMagicTiles(cls, tiles, magicTiles):
        # 判断七对系列
        if cls.isPairs(tiles, magicTiles):
            return True, tiles[MHand.TYPE_HAND]

        # 判定其它胡牌
        result, rePattern = MWin.isHu(tiles[MHand.TYPE_HAND], magicTiles)
        if result:
            ftlog.debug('MWinRuleYunnan.isHu rePattern:', rePattern)
            return True, rePattern

        return False, []

    def isPassHu(self):
        """是否有漏胡规则"""
        return True

    def saveHasHuData(self, result, seatId):
        if self.__hasHu_Data.has_key(seatId):
            return
        else:
            self.__hasHu_Data[seatId] = result

    def getHasHuData(self):
        return self.__hasHu_Data

    def getHasHuDataBySeatId(self, seatId):
        if self.__hasHu_Data.has_key(seatId):
            return self.__hasHu_Data[seatId]
        else:
            return {}

    def clearHasHuData(self):
        self.__hasHu_Data = {}
