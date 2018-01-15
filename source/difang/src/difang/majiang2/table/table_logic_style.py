#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
补充一个table_logic的接口类出来
"""
from abc import abstractmethod

from difang.majiang2.table_state.state import MTableState


class AbstractMajiangTableLogic(object):
    def __init__(self):
        pass

    @property
    def addCardProcessor(self):
        pass

    @property
    def dropCardProcessor(self):
        pass

    @property
    def qiangGangHuProcessor(self):
        pass

    @abstractmethod
    def chiTile(self, seatId, chiTile, chiPattern, state=MTableState.TABLE_STATE_CHI):
        """
        以下四种情况为别人打出的牌，其他人可以有的行为
        分别是
            吃
            碰
            杠
            胡
        同一人或者多个人有不同的选择，状态机的大小代表优先级。
        响应的规则是：
        优先响应最高优先级的操作，最高优先级的操作取消，响应次高优先级的操作。
        一人放弃响应，此人的状态机重置

        特殊说明：
            此时当前座位还是出牌的人
            获取出牌之外的人的状态进行比较
        """
        pass

    @abstractmethod
    def gameWin(self, seatId, tile):
        """
        胡牌
        1）出牌时 可以有多个人和牌
        2）摸牌时，只有摸牌的人和牌
        """
        pass

    @abstractmethod
    def gangTile(self, seatId, tile, gangPattern, style, state, special_tile=None):
        """杠别人的牌
        只有一个人
        """
        pass

    @abstractmethod
    def grabHuGang(self, seatId, tile):
        pass

    @abstractmethod
    def playerCancel(self, seatId):
        """
        用户选择放弃
        """
        pass

    @abstractmethod
    def pengTile(self, seatId, tile, pengPattern, state):
        """
        碰别人的牌
        """
        pass

    @abstractmethod
    def sendNetStateToUser(self, userId, seatId, timeStamp, delta):
        """
        处理玩家网络状态并发送
        """
        pass

    @abstractmethod
    def ting(self, seatId, dropTile, exInfo):
        """
        听牌状态
        """

    @abstractmethod
    def zhanTile(self, seatId, tile, zhanPattern, state, special_tile):
        """
        粘别人的牌
        """
