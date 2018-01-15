# -*- coding=utf-8
'''
Created on 2016年9月23日

本桌的输赢结果
1）陌生人桌，打完后直接散桌，有一个round_results
2）自建桌，SNG，打几把，有几个round_results
@author: nick.kai.lee
'''


class HYFinalBudget(object):
    def __init__(self):
        super(HYFinalBudget, self).__init__()
        self.__final_results = []
        self.__score = None

    def reset(self):
        self.__final_results = []
        self.__score = None

    @property
    def score(self):
        return self.__score

    @property
    def results(self):
        return self.__final_results

    def get_score(self):
        """
        获得玩家结算的积分数组
        """
        return self.__score or []

    def add_round_budget(self, budget):
        self.__final_results.append(budget)

        if not self.__score:
            self.__score = [0 for _ in range(budget.get_player_count())]

        # 单次结算的积分 汇入 单局结算中
        for i in range(budget.get_player_count()):
            self.__score[i] += budget.get_score_by_seat_id(i)
