# -*- coding=utf-8
'''
Created on 2016年12月02日
牌桌麻将牌的管理器
包括：
1）发牌
2）牌桌上的出牌
3）宝牌

发牌说明：
发牌涉及到好牌点
@author: dongwei
'''
from difang.majiang2.table.table_config_define import MTDefine
from difang.majiang2.table_tile.table_tile import MTableTile
from freetime.util import log as ftlog


class MTableTileKawuxing(MTableTile):
    def __init__(self, playerCount, playMode, runMode):
        super(MTableTileKawuxing, self).__init__(playerCount, playMode, runMode)
        # 宝牌
        self.__last_special_tiles = None

    def reset(self):
        """重置"""
        super(MTableTileKawuxing, self).reset()
        self.__last_special_tiles = None

    def getLastSpecialTiles(self):
        """随州买马，获取最后的马牌；其他玩法，最后需要多组牌，所以设计成这样的返回值"""
        if self.__last_special_tiles:
            return {"ma_tile": self.__last_special_tiles}

        return None

    def drawLastSpecialTiles(self, curSeatId, winSeatId):
        """随州买马，抓取最后的马牌"""
        maType = self.tableConfig.get(MTDefine.MAI_MA, 0)
        if maType == 0:
            # 未开启买马
            return False
        if maType == 1:
            # 必须自摸，才能买马
            if curSeatId != winSeatId:
                return False
        if maType == 2:
            # 必须自摸，才能买马
            if curSeatId != winSeatId:
                return False
            # 必须听牌亮倒才能买马
            if not self.players[winSeatId].isTing():
                return False

        self.__last_special_tiles = self.tiles.pop(-1)
        ftlog.debug('MTableTileKawuxing.drawLastSpecialTiles draw last specail tile:', self.__last_special_tiles)
        return True

    def getTingLiangMode(self):
        """卡五星在听牌时，即亮牌"""
        # 卡五星默认亮全部手牌
        mode = self.tableConfig.get(MTDefine.LIANG_PAI, self.MODE_LIANG_HAND)
        ftlog.debug('MTableTileKawuxing.getTingLiangMode liang mode:', mode)
        if mode in [self.MODE_LIANG_HAND, self.MODE_LIANG_TING]:
            return mode
        else:
            ftlog.debug('MTableTileKawuxing.getTingLiangMode liang mode to default:', self.MODE_LIANG_HAND)
            return self.MODE_LIANG_HAND
