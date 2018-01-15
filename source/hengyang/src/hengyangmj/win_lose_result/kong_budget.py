# -*- coding=utf-8
'''
Created on 2017年3月7日

杠牌结算算分(非结束)

@author: nick.kai.lee
'''


class HYKongBudget(object):
    """
    设置杠牌结算的基本类型 (readable class)
    """

    class BudgetType(object):
        EXPOSED_KONG = 0
        CONCEALED_KONG = 1
        SUPPLY_KONG = 2

    class BudgetData(object):
        """
        设置杠牌结算的基本数据结构,外部数据传入 (private class)
        """

        def __init__(self):
            super(HYKongBudget.BudgetData, self).__init__()
            self.targets = []
            self.active_seat_id = 0  # 杠牌者座位号
            self.passive_seat_ids = []  # 输家者座位号list
            self.style = HYKongBudget.BudgetType.EXPOSED_KONG  # (0,1,2)明杠,暗杠或补杠
            self.pattern = []  # 杠牌牌型
            self.tile = 0  # 杠牌花色

        pass

    class BudgetResult(object):
        """
        设置杠牌结算的"结果"基本数据结构 (private class)
        """

        def __init__(self):
            super(HYKongBudget.BudgetResult, self).__init__()
            self.delta = []  # 保存结算中玩家的积分 数组下标是座位号

        pass

    def __init__(self):
        super(HYKongBudget, self).__init__()
        self.__data = HYKongBudget.BudgetData()
        self.__results = HYKongBudget.BudgetData()

    def __update_score(self, score):
        """
        更新杠牌分数 (private api)
        @param score: 每一个输家提供的分数(正数)
        """
        self.__results.delta[self.__data.active_seat_id] = score * len(self.__data.passive_seat_ids)
        for seat_id in self.__data.passive_seat_ids:
            self.__results.delta[seat_id] = -1 * score

    def set_budget_base(self, targets, active_seat_id, passive_seat_id, tile, pattern, style):
        """
        设置杠牌结算的基本数据 (public api)
        @param targets: players object list
        @param active_seat_id: 赢家座位号
        @param passive_seat_id: 输家座位号列表 []
        @param tile: 杠牌花色
        @param pattern: 杠牌牌型
        @param style: 明杠1,暗杠0

        @:return self
        """
        self.__data.targets = targets
        self.__data.active_seat_id = active_seat_id
        self.__data.tile = tile
        self.__data.pattern = pattern

        loser_seat_ids = []
        style = HYKongBudget.BudgetType.EXPOSED_KONG
        if style == 0:  # 暗杠
            for seat_id in range(0, len(targets)):
                if targets[seat_id] and seat_id != active_seat_id:
                    loser_seat_ids.append(seat_id)
            style = HYKongBudget.BudgetType.CONCEALED_KONG
        elif style == 1:  # 明杠
            if active_seat_id == passive_seat_id:  # 补杠
                for seat_id in range(0, len(targets)):
                    if targets[seat_id] and seat_id != active_seat_id:
                        loser_seat_ids.append(seat_id)
                style = HYKongBudget.BudgetType.SUPPLY_KONG
            else:
                loser_seat_ids.append(passive_seat_id)
                style = HYKongBudget.BudgetType.EXPOSED_KONG

        self.__data.passive_seat_ids = loser_seat_ids
        self.__data.style = style

        self.__results.delta = [0 for _ in range(len(targets))]
        return self

    def get_player_count(self):
        """
        获得记录涉及的人数 (public api)

        @:return 返回玩家数量
        """
        return len(self.__data.targets)

    def get_score_by_seat_id(self, seat_id):
        """
        根据座位号获得玩家结算的积分 (public api)
        @param seat_id 玩家座位号
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
        if self.__data.style == HYKongBudget.BudgetType.EXPOSED_KONG:
            self.__update_score(3)
        elif self.__data.style == HYKongBudget.BudgetType.CONCEALED_KONG:
            self.__update_score(2)
        elif self.__data.style == HYKongBudget.BudgetType.SUPPLY_KONG:
            self.__update_score(1)
        return self
