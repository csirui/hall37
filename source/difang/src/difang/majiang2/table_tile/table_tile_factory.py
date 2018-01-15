# -*- coding=utf-8
'''
Created on 2016年9月23日
庄家规则
@author: zhaol
'''
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.table.run_mode import MRunMode
from difang.majiang2.table_tile.table_tile import MTableTile
from difang.majiang2.table_tile.table_tile_haerbin import MTableTileHaerbin
from difang.majiang2.table_tile.table_tile_jixi import MTableTileJixi
from difang.majiang2.table_tile.table_tile_kawuxing import MTableTileKawuxing
from difang.majiang2.table_tile.table_tile_yunnan import MTableTileYunnan
from difang.majiang2.table_tile.table_tile_zhaotong import MTableTileZhaotong
from difang.majiang2.tile.tile import MTile


class MTableTileFactory(object):
    def __init__(self):
        super(MTableTileFactory, self).__init__()

    @classmethod
    def getTableTileMgr(cls, playerCount, playMode, runMode):
        """牌桌手牌管理器获取工厂
        输入参数：
            playMode - 玩法      
        返回值：
            对应玩法手牌管理器
        """
        if playMode == MPlayMode.HAERBIN:
            return MTableTileHaerbin(playerCount, playMode, runMode)
        elif playMode == MPlayMode.YUNNAN:
            return MTableTileYunnan(playerCount, playMode, runMode)
        elif playMode == MPlayMode.ZHAOTONG:
            return MTableTileZhaotong(playerCount, playMode, runMode)
        elif playMode == MPlayMode.JIXI:
            return MTableTileJixi(playerCount, playMode, runMode)
        elif MPlayMode().isSubPlayMode(playMode, MPlayMode.KAWUXING):
            return MTableTileKawuxing(playerCount, playMode, runMode)
        return MTableTile(playerCount, playMode, runMode)


if __name__ == "__main__":
    tableTileMgr = MTableTileFactory.getTableTileMgr(4, MPlayMode.HAERBIN, MRunMode.CONSOLE)
    tableTileMgr.tileTestMgr.setHandTiles([[5, 5, 5, 5], [6, 6, 6, 6], [7, 7, 7, 7], [8, 8, 8, 8]])
    tableTileMgr.tileTestMgr.setTiles([9, 9, 9, 9])
    tableTileMgr.shuffle(0, 13)
    tiles = tableTileMgr.tiles
    print tiles

    tileArr = MTile.changeTilesToValueArr(tiles)
    print tileArr
