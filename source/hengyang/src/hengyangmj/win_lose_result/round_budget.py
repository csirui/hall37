# -*- coding=utf-8
'''
Created on 2017年3月7日

本副牌局的和牌结果，可能有多个
1）普通麻将一个结果
2）血战到底N-1个结果，N为牌桌人数
3）血流成河有多个结果，直到本局牌全部发完
@author: nick.kai.lee
'''


class HYRoundBudget(object):
    def __init__(self):
        super(HYRoundBudget, self).__init__()
        self.__round_index = 0
        self.__player_count = 0
        self.__round_budgets = []  # 每局牌局的所有结果
        self.__score = None
        self.__delta = None

    def set_round_index(self, index):
        self.__round_index = index

    def get_player_count(self):
        return self.__player_count

    def get_delta_by_seat_id(self, seat_id):
        """
        根据座位号获得玩家"当前"结算的积分变化(加多少,减多少)
        @param seat_id 玩家座位号
        """
        return self.__delta[seat_id] if self.__delta and seat_id < len(self.__delta) else 0

    def get_score_by_seat_id(self, seat_id):
        """
        根据座位号获得玩家结算的积分
        @param seat_id 玩家座位号
        """
        return self.__score[seat_id] if self.__score and seat_id < len(self.__score) else 0

    def add_one_budget(self, budget):
        """
        添加单次结果
        @param budget 单次结算对象
        """
        self.__round_budgets.append(budget)
        self.__player_count = budget.get_player_count()

        if not self.__delta:
            self.__delta = [0 for _ in range(self.__player_count)]
        if not self.__score:
            self.__score = [0 for _ in range(self.__player_count)]

        # 单次结算的积分 汇入 单局结算中
        for i in range(self.__player_count):
            self.__delta[i] = budget.get_score_by_seat_id(i)
            self.__score[i] += self.__delta[i]
