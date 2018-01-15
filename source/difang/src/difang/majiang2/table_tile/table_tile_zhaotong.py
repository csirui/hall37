# -*- coding=utf-8
'''
Created on 2016年12月3日
昭通麻将牌堆规则
只有万筒条,无字牌
发完牌后摸一张牌,根据这张牌计算赖子,规则是牌面+1,同花色内循环,例如摸到9万,那么1万是赖子
@author: zhangwei
'''
from difang.majiang2.table_state.state import MTableState
from difang.majiang2.table_tile.table_tile import MTableTile
from freetime.util import log as ftlog


class MTableTileZhaotong(MTableTile):
    def __init__(self, playerCount, playMode, runMode):
        super(MTableTileZhaotong, self).__init__(playerCount, playMode, runMode)
        # 宝牌
        self.__magic_tiles = []
        # 漏胡牌数组
        self.__pass_hu = [[] for _ in range(0, playerCount)]
        # 杠牌最多可以用的赖子数
        self.setMagicGangMaxCount(2)
        # 碰牌最多可以用的赖子数
        self.setMagicPengMaxCount(1)
        # 抢杠胡的规则
        self.setQiangGangRule(0b010)

    def reset(self):
        """重置"""
        super(MTableTileZhaotong, self).reset()
        for temp in self.__pass_hu:
            temp = []

    def shuffle(self, goodPointCount, handTileCount, piguTrick=[]):
        """
        洗牌器 
        添加特殊逻辑，宝牌
        """
        super(MTableTileZhaotong, self).shuffle(goodPointCount, handTileCount)
        #         tile = self.tiles.pop(-1)
        tile = 5
        self.tiles.remove(5)
        self.__magic_tiles = []
        if tile % 10 == 9:
            self.__magic_tiles.append(tile - 8)
            self.__magic_tiles.append(tile - 1)
        elif tile % 10 == 1:
            self.__magic_tiles.append(tile + 1)
            self.__magic_tiles.append(tile + 8)
        else:
            self.__magic_tiles.append(tile + 1)
            self.__magic_tiles.append(tile - 1)
        ftlog.debug('MTableTileYunnan.shuffle len:', len(self.tiles))
        ftlog.debug('MTableTileYunnan.self.__magic_tile:', self.__magic_tiles)

    def canUseMagicTile(self, state):
        """牌桌状态state，是否可使用癞子牌"""
        if state & MTableState.TABLE_STATE_HU:
            return True

        if state & MTableState.TABLE_STATE_GANG:
            return True

        if state & MTableState.TABLE_STATE_PENG:
            return True

        if state & MTableState.TABLE_STATE_CHI:
            return False

        return False

    def getMagicTiles(self, isTing=False):
        """获取宝牌，采用数组，有的游戏有多个宝牌"""
        return self.__magic_tiles

    def addPassHuBySeatId(self, seatId, huInfo):
        ftlog.debug("addPassHuBySeatId1 passHuArr = ", self.__pass_hu, "seatId=", seatId)
        if huInfo in self.__pass_hu[seatId]:
            ftlog.debug("addPassHuBySeatId2 already have tile = ", huInfo['tile'])
            return
        else:
            self.__pass_hu[seatId].append(huInfo)
        ftlog.debug("addPassHuBySeatId2 passHuArr = ", self.__pass_hu[seatId])

    def clearPassHuBySeatId(self, seatId):
        ftlog.debug("clearPassHuBySeatId passHuArr = ", self.__pass_hu, "seatId=", seatId)
        self.__pass_hu[seatId] = []

    def isPassHuTileBySeatId(self, seatId, huInfo):
        ftlog.debug("isPassHuTileBySeatId passHuArr = ", self.__pass_hu, "seatId=", seatId)
        if len(self.__pass_hu[seatId]) > 0:
            huInfoFan = huInfo.get('fan', 0)
            for info in self.__pass_hu[seatId]:
                infoFan = info.get('fan', 0)
                if infoFan > huInfoFan:
                    ftlog.debug("isPassHuTileBySeatId  True passHuArr = ", self.__pass_hu, "seatId=", seatId)
                    return True
                    break
        ftlog.debug("isPassHuTileBySeatId  False passHuArr = ", self.__pass_hu, "seatId=", seatId)
        return False

    def needChangeMagic(self):
        """摸牌时是否需要换赖子"""
        return True
