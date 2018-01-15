# coding=UTF-8

__author__ = [
    'Zhaoqh'
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

ROBOT_USER_ID_MAX = 10000


class TYPlayer(object):
    '''
    玩家基类
    玩家table.players和座位table.seats是一一对应的
    此类主要是为了保持玩家再当前桌子的上的一些基本用户数据, 避免反复查询数据库
    注: 在游戏逻辑中, 不区分机器人和真实玩家
    '''

    def __init__(self, table, seatIndex):
        self.table = table
        self.__seatIndex = seatIndex
        self.__seatId = seatIndex + 1
        self.clientId = ''

    @property
    def seatId(self):
        return self.__seatId

    @property
    def seatIndex(self):
        return self.__seatIndex

    @property
    def userId(self):
        return self.table.seats[self.__seatIndex].userId

    @property
    def isRobotUser(self):
        return self.isRobot(self.userId, self.clientId)

    @classmethod
    def isRobot(cls, userId, clientId=''):
        if userId > 0 and userId <= ROBOT_USER_ID_MAX:
            return True
        if userId > ROBOT_USER_ID_MAX:
            if isinstance(clientId, (str, unicode)) and clientId.find('robot') >= 0:
                return True
        return False

    @classmethod
    def isHuman(cls, userId, clientId=''):
        return not cls.isRobot(userId, clientId)
