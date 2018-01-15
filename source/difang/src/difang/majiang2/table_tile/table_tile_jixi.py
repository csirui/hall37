# -*- coding=utf-8
'''
Created on 2016年9月23日
牌桌麻将牌的管理器
包括：
1）发牌
2）牌桌上的出牌
3）宝牌

发牌说明：
发牌涉及到好牌点
@author: zhaol
'''
import copy

from difang.majiang2.table_state.state import MTableState
from difang.majiang2.table_tile.table_tile import MTableTile
from freetime.util import log as ftlog


class MTableTileJixi(MTableTile):
    def __init__(self, playerCount, playMode, runMode):
        super(MTableTileJixi, self).__init__(playerCount, playMode, runMode)
        # 宝牌
        self.__magic_tile = None

    def reset(self):
        """重置"""
        super(MTableTileJixi, self).reset()
        self.__magic_tile = None

    def shuffle(self, goodPointCount, handTileCount, piguTrick=[]):
        """
        洗牌器 
        添加特殊逻辑，宝牌
        """
        super(MTableTileJixi, self).shuffle(goodPointCount, handTileCount)
        ftlog.debug('MTableTileJixi.shuffle changed tile:', self.__magic_tile)

    def canUseMagicTile(self, state):
        """牌桌状态state，是否可使用癞子牌"""
        if state & MTableState.TABLE_STATE_HU:
            return True

        return False

    def getMagicTiles(self, isTing=False):
        """获取宝牌，采用数组，有的游戏有多个宝牌"""
        if not isTing:
            return []
        if self.__magic_tile:
            return [self.__magic_tile]

        return []

    def getAbandonedMagics(self):
        """获取废弃宝牌"""
        abandons = copy.deepcopy(self.specialTiles)
        if self.__magic_tile in abandons:
            abandons.remove(self.__magic_tile)
        return abandons

    def updateMagicTile(self):
        """更新宝牌"""
        self.__magic_tile = self.tiles.pop(-1)
        self.addSpecialTile(self.__magic_tile)
        ftlog.debug('MTableTileJixi.updateMagicTile changed tile:', self.__magic_tile)
        return self.__magic_tile

    def getCheckFlowCount(self):
        """覆盖父类方法,荒庄牌的数量"""
        magicTiles = self.getMagicTiles()
        fakeRemainCount = len(self.tiles) + len(magicTiles)
        if fakeRemainCount <= 9:
            return 0
        return fakeRemainCount
