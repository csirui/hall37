# -*- coding=utf-8
'''
Created on 2017年3月7日

胡牌结算算分(非结束)

@author: nick.kai.lee
'''


class HYWinBudget(object):
    """
    设置胡牌结算的基本类型 (readable class)
    """

    class BudgetType(object):
        IDLE = -1
        ZIMO = 0  # 自摸
        HUPAI = 1  # 胡牌
        LIUJU = 2  # 流局

    class BudgetData(object):
        """
        设置杠牌结算的基本数据结构,外部数据传入 (private class)
        """

        def __init__(self):
            super(HYWinBudget.BudgetData, self).__init__()
            self.targets = []
            self.active_seat_id = 0  # 第一手接牌或自摸玩家座位号
            self.passive_seat_id = 0  # 第一手点炮或者自摸玩家座位号list
            self.loser_seat_ids = []  # 输家座位号list
            self.style = HYWinBudget.BudgetType.IDLE
            self.tile = 0  # 胡牌花色

        pass

    class BudgetResult(object):
        """
        设置杠牌结算的"结果"基本数据结构 (private class)
        """

        def __init__(self):
            super(HYWinBudget.BudgetResult, self).__init__()
            self.delta = []  # 保存结算中玩家的积分 数组下标是座位号

        pass

    def __init__(self):
        super(HYWinBudget, self).__init__()
        self.__data = HYWinBudget.BudgetData()
        self.__results = HYWinBudget.BudgetResult()

    def __update_score(self, score):
        """
        更新杠牌分数 (private api)
        @param score: 每一个输家提供的分数(正数)
        """
        self.__results.delta[self.__data.active_seat_id] = score * len(self.__data.loser_seat_ids)
        for seat_id in self.__data.loser_seat_ids:
            self.__results.delta[seat_id] = -1 * score

    def set_budget_base(self, targets, active_seat_id, passive_seat_id, loser_seat_ids, tile=0, game_flow=False):
        """
        设置杠牌结算的基本数据 (public api)
        @param targets: players object list
        @param active_seat_id: 赢家座位号
        @param passive_seat_id: 点炮或者自摸者输家座位号
        @param loser_seat_ids: 输家座位号列表 []
        @param tile: 胡牌花色
        @param game_flow: boolean 是否流局
        @:return self
        """
        self.__data.targets = targets

        self.__data.tile = tile
        self.__data.active_seat_id = active_seat_id
        self.__data.passive_seat_id = passive_seat_id
        self.__data.loser_seat_ids = loser_seat_ids

        if game_flow:
            self.__data.style = HYWinBudget.BudgetType.LIUJU
        else:
            if active_seat_id == passive_seat_id:
                self.__data.style = HYWinBudget.BudgetType.ZIMO
            else:
                self.__data.style = HYWinBudget.BudgetType.HUPAI

        self.__results.delta = [0 for _ in range(len(targets))]

        return self

    def get_player_count(self):
        """
        获得记录涉及的人数 (public api)
        @:return 返回玩家数量

        PS: round_budget会调用
        """
        return len(self.__data.targets)

    def get_score_by_seat_id(self, seat_id):
        """
        根据座位号获得玩家结算的积分 (public api)
        @param seat_id 玩家座位号

        PS: round_budget会调用
        """
        return self.__results.delta[seat_id] or 0

    def calculate_budget(self):
        """
        计算结果 (public api)
        补杠:当前没结束的每家赔1分(3)
        暗杠:当前没结束的每家赔2分(6)
        明杠:放杠者赔3分(3)

        @:return self
        """
        if self.__data.style == HYWinBudget.BudgetType.ZIMO:
            self.__update_score(3)
        elif self.__data.style == HYWinBudget.BudgetType.HUPAI:
            self.__update_score(2)
        elif self.__data.style == HYWinBudget.BudgetType.LIUJU:
            self.__update_score(0)
        return self
