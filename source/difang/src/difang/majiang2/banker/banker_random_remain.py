# -*- coding=utf-8
'''
Created on 2016年9月23日
庄家规则
@author: zhaol
'''
import random

from difang.majiang2.banker.banker import MBanker


class MBankerRandomRemain(MBanker):
    """
    开局随机庄家，之后连庄的规则
    庄家赢，连庄
    闲家赢，闲家坐庄
    
    哈尔滨麻将中有一个包庄的玩法，连续流局3次后，庄家就属于包牌了，不管谁胡，庄都要付3家的钱，而且庄要移到下一家。
    """

    def __init__(self):
        super(MBankerRandomRemain, self).__init__()

    def getBanker(self, playerCount, isFirst, winLoose, winSeatId):
        """子类必须实现
        参数：
        1）isFirst 是否第一句
        2）winLoose 上局的结果 1分出了胜负 0流局
        3）winSeatId 赢家的座位号，如果第二个参数为0，则本参数为上一局的庄家
        """
        if isFirst:
            # 初始化，随机选庄
            self.banker = random.randint(0, playerCount - 1)
            self.no_result_count = 0
            self.remain_count = 0
        else:
            if winLoose > 0:
                # 有输赢结果
                if winSeatId == self.banker:
                    # 赢得是庄家
                    self.remain_count += 1
                    self.no_result_count = 0
                else:
                    # 赢得是闲家
                    self.banker = winSeatId
                    self.remain_count = 0
                    self.no_result_count = 0
            else:
                # 荒牌，流局，庄家继续，荒牌次数加一，坐庄次数加一
                self.no_result_count += 1
                self.remain_count += 1

        return self.banker, self.remain_count, self.no_result_count
