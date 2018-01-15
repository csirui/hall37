# coding=UTF-8

__author__ = [
    'Zhaoqh'
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]


class TYObserver(object):
    '''
    玩家基类
    玩家table.players和座位table.seats是一一对应的
    此类主要是为了保持玩家再当前桌子的上的一些基本用户数据, 避免反复查询数据库
    注: 再游戏逻辑中, 不区分机器人和真实玩家
    '''

    def __init__(self, table, seatIndex):
        self.table = table
        self.__seatIndex = seatIndex
        self.__seatId = seatIndex + 1

    @property
    def seatId(self):
        return self.__seatId

    @property
    def seatIndex(self):
        return self.__seatIndex

    @property
    def userId(self):
        return self.table.seats[self.__seatIndex].userId
