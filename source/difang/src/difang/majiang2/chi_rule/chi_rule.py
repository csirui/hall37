# -*- coding=utf-8
'''
Created on 2016年9月23日
听牌规则
@author: zhaol
'''
from difang.majiang2.ai.chi import MChi
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.table_state.state import MTableState
from difang.majiang2.tile.tile import MTile
from freetime.util import log as ftlog


class MChiRule(object):
    """胡牌规则
    """

    def __init__(self):
        super(MChiRule, self).__init__()
        self.__table_tile_mgr = None

    @property
    def tableTileMgr(self):
        return self.__table_tile_mgr

    def setTableTileMgr(self, tableTileMgr):
        self.__table_tile_mgr = tableTileMgr

    def hasChi(self, tiles, tile):
        """是否有吃牌解
        
        参数说明；
        tiles - 玩家的所有牌，包括手牌，吃牌，碰牌，杠牌，胡牌
        tile - 待吃的牌
        """
        if tile >= MTile.TILE_DONG_FENG:
            return []

        chiSolutions = MChi.hasChi(tiles[MHand.TYPE_HAND], tile)
        magicTiles = self.tableTileMgr.getMagicTiles(False)
        if len(magicTiles) == 0:
            return chiSolutions

        if not self.tableTileMgr.canUseMagicTile(MTableState.TABLE_STATE_CHI):
            return chiSolutions

        magicTile = magicTiles[0]
        tileArr = MTile.changeTilesToValueArr(tiles[MHand.TYPE_HAND])
        magicCount = tileArr[magicTile]
        tileArr[magicTile] = 0
        ftlog.debug('MChiRule.hasChi tile:', tile, ' magicCount:', magicCount)

        if magicCount == 0 or (tileArr[tile] == 0):
            return chiSolutions

        if MTile.getValue(tile) <= 7:
            # +1[-] +2[+] ==> [tile, magic, tile+2]
            if tileArr[tile + 1] == 0 and tileArr[tile + 2] > 0:
                chiSolutions.append([tile, magicTile, tile + 2])

            # +1[+] +2[-] ==> [tile, tile + 1, magicTile]
            if tileArr[tile + 1] > 0 and tileArr[tile + 2] == 0:
                chiSolutions.append([tile, tile + 1, magicTile])

            if (tileArr[tile + 1] + tileArr[tile + 2]) == 0 and magicCount >= 2:
                chiSolutions.append([tile, magicTile, magicTile])

        if MTile.getValue(tile) >= 3:
            # -2[+] -1[-] ==> [tile - 2, magicTile, tile]
            if tileArr[tile - 2] > 0 and tileArr[tile - 1] == 0:
                chiSolutions.append([tile - 2, magicTile, tile])

            # -2[0] -1[+] ==> [magicTile, tile - 1, tile]
            if tileArr[tile - 2] == 0 and tileArr[tile - 1] > 0:
                chiSolutions.append([magicTile, tile - 1, tile])

            if (tileArr[tile - 2] + tileArr[tile - 1]) == 0 and magicCount >= 2:
                chiSolutions.append([magicTile, magicTile, tile])

        if MTile.getValue(tile) >= 2 and MTile.getValue(tile) <= 8:
            # -1[-] 1[+] ==> magicTile, tile, tile + 1
            if tileArr[tile - 1] == 0 and tileArr[tile + 1] > 0:
                chiSolutions.append([magicTile, tile, tile + 1])

            # -1[+] 1[-] ==> [tile - 1, tile, magicTile]
            if tileArr[tile - 1] > 0 and tileArr[tile + 1] == 0:
                chiSolutions.append([tile - 1, tile, magicTile])

            if (tileArr[tile + 1] + tileArr[tile - 1]) == 0 and magicCount >= 2:
                chiSolutions.append([magicTile, tile, magicTile])

        return chiSolutions
