# -*- coding=utf-8
"""
Created on 2016年9月23日
庄家规则
@author: zhaol
"""
from abc import abstractmethod


class MWinRule(object):
    """
    胡牌规则
    """
    WIN_BY_MYSELF = 0
    WIN_BY_OTHERS = 1
    WIN_BY_QIANGGANGHU = 2
    LOOSE = -1

    def __init__(self):
        super(MWinRule, self).__init__()
        self.__table_tile_mgr = None
        # 倍数,由玩家建房参数带入
        self.__multiple = 1
        # 当前杠牌人座位信息,内容为当前杠牌人的座位号
        self.__last_gang_seat = -1
        # 当前操作者的位置
        self.__curSeatId = -1
        # 自摸奖励
        self.__zimo_bonus = 1
        # 静态配置不需要第一时间加载到游戏的
        self.__item_params = {}

    @property
    def itemParams(self):
        return self.__item_params

    def setItemParams(self, itemParams):
        self.__item_params = itemParams

    @property
    def zimoBonus(self):
        return self.__zimo_bonus

    def setZimoBonus(self, zimoBonus):
        self.__zimo_bonus = zimoBonus

    @property
    def curSeatId(self):
        return self.__curSeatId

    def setCurSeatId(self, seatId):
        self.__curSeatId = seatId

    @property
    def lastGangSeat(self):
        return self.__last_gang_seat

    def setLastGangSeat(self, seat):
        self.__last_gang_seat = seat

    @property
    def tableTileMgr(self):
        return self.__table_tile_mgr

    def setTableTileMgr(self, mgr):
        self.__table_tile_mgr = mgr

    @abstractmethod
    def isHu(self, tiles, last_tile, isTing, getTileType, magicTiles=list(), tingNodes=list()):
        """
        :param tiles 该玩家的手牌
        :param last_tile: 最后的上牌
        :param isTing 是否听牌
        :param getTileType 获取tile的方式,0为摸牌,1为要别人打出的牌
        :param tingNodes 为听牌之后胡牌把听牌条件附带过来，按照听牌的胡牌规则来
        :param magicTiles:
        :type tiles HandTiles
        """
        return False, []

    def isPassHu(self):
        """是否有漏胡规则"""
        return False

    def isDropHu(self, player):
        """出牌立即胡牌的类型判断"""

        return False, []

    def isAddHu(self, player, tile):
        """上牌后立即判胡的类型"""
        return False

    def isBaoZhongBaoHu(self, isTing, handTiles, magicTiles):
        return False

    # 鸡西麻将用 听牌之后如果和的是宝牌 那么直接算和
    def isMagicAfertTingHu(self, isTing, winNodes, magicTiles):
        return False

    # 鸡西麻将用 三人麻将无对胡
    def isWuDuiHu(self, allTiles, winTile):
        return False, -1

    def canWinAfterChiPengGang(self, tiles):
        return True

    @property
    def multiple(self):
        return self.__multiple

    def setMultiple(self, playerMultiple):
        self.__multiple = playerMultiple
