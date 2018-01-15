# -*- coding=utf-8
"""
Created on 2016年9月23日
听牌规则
@author: zhaol
"""
from difang.majiang2.ai.peng import MPeng
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.table_state.state import MTableState
from difang.majiang2.table_tile.table_tile_factory import MTableTileFactory
from difang.majiang2.tile.tile import MTile
from freetime.util import log as ftlog


class MPengRule(object):
    """
    碰牌判断
    """

    def __init__(self):
        super(MPengRule, self).__init__()
        self.__table_tile_mgr = None

    @property
    def tableTileMgr(self):
        return self.__table_tile_mgr

    def setTableTileMgr(self, tableTileMgr):
        self.__table_tile_mgr = tableTileMgr

    def hasPeng(self, tiles, tile):
        """
        是否有碰牌解
        
        参数说明；
        tiles - 玩家的所有牌，包括手牌，吃牌，碰牌，杠牌，胡牌
        tile - 待碰的牌
        """
        pengSolutions = []
        normalPeng = MPeng.hasPeng(tiles[MHand.TYPE_HAND], tile)
        if normalPeng:
            pengSolutions.append([tile, tile, tile])

        magics = self.tableTileMgr.getMagicTiles(False)
        tileArr = MTile.changeTilesToValueArr(tiles[MHand.TYPE_HAND])
        tileArr, magicTiles = self.tableTileMgr.exculeMagicTiles(tileArr, magics)
        magicCount = len(magicTiles)
        if magicCount == 0:
            return pengSolutions

        if not self.tableTileMgr.canUseMagicTile(MTableState.TABLE_STATE_PENG):
            return pengSolutions

        magicPengMaxCount = self.tableTileMgr.magicPengMaxCount
        if magicPengMaxCount > 3 or magicPengMaxCount < 0:
            magicPengMaxCount = 3

        ftlog.debug('MPengRule.hasPeng tile:', tile
                    , ' tileCount:', tileArr[tile]
                    , ' magicCount:', magicCount
                    , 'magicPengMaxCount', magicPengMaxCount)

        if (magicCount == 0) or (tileArr[tile] == 0) or (magicPengMaxCount <= 0):
            return pengSolutions

        if magicCount >= 1 and tileArr[tile] >= 2 and magicPengMaxCount >= 1:
            # 使用一个癞子
            pattern1 = [tile, tile, magicTiles[0]]
            pattern1.sort()
            pengSolutions.append(pattern1)

        if magicCount >= 2 and tileArr[tile] >= 1 and magicPengMaxCount >= 2:
            # 使用两个癞子
            pattern2 = [tile, magicTiles[0], magicTiles[1]]
            pattern2.sort()
            pengSolutions.append(pattern2)

        return pengSolutions


if __name__ == "__main__":
    def test():
        tiles = [[4, 4, 7, 8, 11, 12, 21, 21], [29, 29, 29], [28, 28, 28, 28], [], []]
        tileMgr = MTableTileFactory.getTableTileMgr(4, MPlayMode.YUNNAN)
        pengRuler = MPengRule()
        pengRuler.setTableTileMgr(tileMgr)

        result = pengRuler.hasPeng(tiles, 21)
        ftlog.debug(result)


    test()
