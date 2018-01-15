# -*- coding=utf-8
'''
Created on 2017年3月2日
衡阳麻将庄家规则
@author: nick.kai.lee
'''
from difang.majiang2.banker.banker import MBanker


class HYBanker(MBanker):
    """
    第一轮房主坐庄 YES
    谁胡谁坐庄 YES
    荒牌，流局，庄家继续 YES
    # 一炮多响，点炮者坐庄
    # 如果所有人都不要海底牌（最后一张牌），那么谁抓牌谁坐庄
    # 如果有人要了海底牌，但是也没有人胡牌，那么这一局庄继续做庄
    """

    def __init__(self):
        super(HYBanker, self).__init__()

        self.banker = 0  # 庄家座位号
        self.no_result_count = 0  # 流局次数
        self.remain_count = 0  # 庄家还能连庄的次数

    def getBanker(self, playerCount, isFirst, winLoose, winSeatId):
        """子类必须实现
        参数：
        1）isFirst 是否第一局
        2）winLoose 上局的结果 1分出了胜负 0流局
        3）winSeatId 赢家的座位号，如果第二个参数为0，则本参数为上一局的庄家
        """
        if isFirst:
            self.banker = 0  # 第一轮房主坐庄
            self.no_result_count = 0
            self.remain_count = 0
        else:
            if winLoose > 0:
                # 有输赢结果
                if winSeatId == self.banker:
                    # 赢得是庄家 连庄
                    self.remain_count += 1
                    self.no_result_count = 0
                else:
                    # 赢得是闲家 闲家坐庄
                    self.banker = winSeatId
                    self.remain_count = 0
                    self.no_result_count = 0
            else:
                # 荒牌，流局，庄家继续，荒牌次数加一，坐庄次数加一
                self.no_result_count += 1
                self.remain_count += 1

        return self.banker, self.remain_count, self.no_result_count
