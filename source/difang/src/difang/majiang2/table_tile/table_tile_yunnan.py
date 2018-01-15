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

云南幺鸡麻将手牌管理的特点：
1）宝牌，幺鸡；
1.1 癞子牌可吃可碰可杠
1.2 自己摸到了吃牌/碰牌中的牌后，可换回癞子牌
2）翻屁股，剩余手牌中，最后两张牌要明牌，杠牌时，玩家从这两张牌中任选一张；
@author: zhaol
'''
from difang.majiang2.table_state.state import MTableState
from difang.majiang2.table_tile.table_tile import MTableTile
from difang.majiang2.tile.tile import MTile
from freetime.util import log as ftlog


class MTableTileYunnan(MTableTile):
    def __init__(self, playerCount, playMode, runMode):
        super(MTableTileYunnan, self).__init__(playerCount, playMode, runMode)
        # 宝牌
        self.__magic_tile = [MTile.TILE_ONE_TIAO]
        # 翻屁股
        self.__tail_tiles_for_gang = []
        # 漏胡牌数组
        self.__pass_hu = [[] for _ in range(0, playerCount)]
        # 杠牌最多可以用的赖子数
        self.setMagicGangMaxCount(1)
        # 碰牌最多可以用的赖子数
        self.setMagicPengMaxCount(0)
        # 抢杠胡的规则
        self.setQiangGangRule(0b010)

    def reset(self):
        """重置"""
        super(MTableTileYunnan, self).reset()
        self.__tail_tiles_for_gang = []
        for temp in self.__pass_hu:
            temp = []

    def shuffle(self, goodPointCount, handTileCount, piguTrick=[]):
        """
        洗牌器 
        添加特殊逻辑，宝牌
        """
        super(MTableTileYunnan, self).shuffle(goodPointCount, handTileCount)
        if len(piguTrick) == 2:
            ftlog.debug('MTableTileYunnan.shuffle handlepiguTrick')
            trickCount = 2
            for pigu in piguTrick:
                if pigu in self.tiles:
                    self.tiles.remove(pigu)
                    self.__tail_tiles_for_gang.append(pigu)
                    self.addSpecialTile(pigu)
                    trickCount -= 1
            ftlog.debug('MTableTileYunnan.shuffle handlepiguTrick trickCount:', trickCount)
            while trickCount > 0:
                tile = self.tiles.pop(-1)
                self.__tail_tiles_for_gang.append(tile)
                self.addSpecialTile(tile)
                trickCount -= 1
        else:
            tile = self.tiles.pop(-1)
            self.__tail_tiles_for_gang.append(tile)
            self.addSpecialTile(tile)
            tile = self.tiles.pop(-1)
            self.__tail_tiles_for_gang.append(tile)
            self.addSpecialTile(tile)
        ftlog.debug('MTableTileYunnan.shuffle tailTilesForGang:', self.__tail_tiles_for_gang)
        ftlog.debug('MTableTileYunnan.shuffle len:', len(self.tiles))

    def canUseMagicTile(self, state):
        """牌桌状态state，是否可使用癞子牌"""
        if state & MTableState.TABLE_STATE_HU:
            return True

        if state & MTableState.TABLE_STATE_GANG:
            return True

        if state & MTableState.TABLE_STATE_PENG:
            return False

        if state & MTableState.TABLE_STATE_CHI:
            return False

        return False

    def getMagicTiles(self, isTing=False):
        """获取宝牌，采用数组，有的游戏有多个宝牌"""
        return self.__magic_tile

    def getPigus(self):
        """获取用于补杠的翻屁股牌"""
        return self.__tail_tiles_for_gang

    def updatePigu(self, tile):
        """更新屁股"""
        self.__tail_tiles_for_gang.remove(tile)
        newTile = self.tiles.pop(-1)
        self.__tail_tiles_for_gang.append(newTile)
        self.addSpecialTile(newTile)

    def getTilesLeftCount(self):
        """覆盖父类方法,获取剩余手牌数量需要加上屁股牌数"""
        return len(self.tiles) + len(self.__tail_tiles_for_gang)

    def getCheckFlowCount(self):
        """覆盖父类方法,非常规流局"""
        fakeRemainCount = len(self.tiles) + len(self.__tail_tiles_for_gang) - 20
        if fakeRemainCount < 0:
            return 0
        return fakeRemainCount

    def addPassHuBySeatId(self, seatId, tile):
        ftlog.debug("addPassHuBySeatId1 passHuArr = ", self.__pass_hu, "seatId=", seatId)
        if tile in self.__pass_hu[seatId]:
            ftlog.debug("addPassHuBySeatId2 already have tile = ", tile)
            return
        else:
            self.__pass_hu[seatId].append(tile)
        ftlog.debug("addPassHuBySeatId2 passHuArr = ", self.__pass_hu[seatId])

    def clearPassHuBySeatId(self, seatId):
        ftlog.debug("clearPassHuBySeatId passHuArr = ", self.__pass_hu, "seatId=", seatId)
        self.__pass_hu[seatId] = []

    def isPassHuTileBySeatId(self, seatId, tile):
        ftlog.debug("isPassHuTileBySeatId passHuArr = ", self.__pass_hu, "seatId=", seatId)
        if len(self.__pass_hu[seatId]) > 0:
            #         if tile in self.__pass_hu[seatId]:
            ftlog.debug("isPassHuTileBySeatId  True passHuArr = ", self.__pass_hu, "seatId=", seatId)
            return True
        ftlog.debug("isPassHuTileBySeatId  False passHuArr = ", self.__pass_hu, "seatId=", seatId)
        return False
