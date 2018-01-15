# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''


class MTableState(object):
    """开始打牌后的牌桌状态
    状态的位数代表了优先级，位数越高，优先级越高
    """
    # 牌桌无状态，未开始
    TABLE_STATE_NONE = -1
    # 给下家发牌，next
    TABLE_STATE_NEXT = 0
    # 二进制第一位 等待出牌，出牌的座位号是当前座位号
    TABLE_STATE_DROP = 0b1
    # 二进制第二位 等待吃牌，吃牌的座位号是当前座位号的下一个
    TABLE_STATE_CHI = 0b10
    # 二进制第三位 等待碰牌，碰牌的座位号可以是其他的任何人
    TABLE_STATE_PENG = 0b100
    # 二进制第四位 等待杠牌，杠牌的座位号可以使任何一个人，当杠牌座位号与当前座位号相同时，为暗杠；当碰牌座位号与当前座位号不同时，为明杠
    TABLE_STATE_GANG = 0b1000
    # 二进制第五位，听牌，表示只和听牌后的这几张牌
    TABLE_STATE_TING = 0b10000
    # 二进制第六位，抢听，抢先停牌
    TABLE_STATE_GRABTING = 0b100000
    # 二进制第七位，翻屁股，云南幺鸡麻将的特殊玩法
    TABLE_STATE_FANPIGU = 0b1000000
    # 二进制第八位，定缺，特殊玩法，四川玩法具有定缺规则
    TABLE_STATE_ABSENCE = 0b10000000
    # 二进制第九位，换宝牌，交换原先杠牌/吃牌中的宝牌
    TABLE_STATE_CHANGE_MAGIC = 0b100000000
    # 二进制第十位，抢杠和，抢回头杠，碰杠的和牌
    TABLE_STATE_QIANGGANG = 0b1000000000
    # 二进制第十一位，鸡西粘牌
    TABLE_STATE_ZHAN = 0b10000000000

    # 二进制第十七位 等待和牌，和牌的座位号可以使任何一个人，当和牌座位号与当前座位号相同时，为自摸；当和牌座位号与当前座位号不同时，为吃和
    TABLE_STATE_HU = 0b10000000000000000
    # 二进制第十八位，血战到底，三个人和牌或者牌都发完后结束
    TABLE_STATE_XUEZHAN = 0b100000000000000000
    # 二进制第十九位，血流成河，所有牌发完后结束
    TABLE_STATE_XUELIU = 0b1000000000000000000
    # 二进制第三十二位 和牌之后牌局结束
    TABLE_STATE_GAME_OVER = 0b10000000000000000000000000000000

    def __init__(self):
        super(MTableState, self).__init__()
        self.__states = 0
        # 超时可以按照状态定制
        self.__time_out_setting = [9 for _ in range(32)]
        self.__time_out_setting[5] = 0

    def setState(self, state):
        """设置状态"""
        self.__states = self.__states | state

    def clearState(self, state):
        """清除状态"""
        if self.__states & state:
            self.__states = self.__states ^ state

    @property
    def states(self):
        """获取牌桌状态设置"""
        return self.__states

    def getTimeOutByState(self, state):
        """超时设置"""
        bigger = self.__time_out_setting[0]
        if state & self.TABLE_STATE_ABSENCE:
            if self.__time_out_setting[6] > bigger:
                bigger = self.__time_out_setting[6]

        return bigger
