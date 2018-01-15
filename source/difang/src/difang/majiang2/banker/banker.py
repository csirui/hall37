# -*- coding=utf-8
'''
Created on 2016年9月23日
庄家规则
@author: zhaol
'''


class MBanker(object):
    def __init__(self):
        """类成员变量可继承
        """
        super(MBanker, self).__init__()
        self.banker = 0
        self.remain_count = 0
        self.no_result_count = 0

    def reset(self):
        """重置"""
        self.banker = 0
        self.remain_count = 0
        self.no_result_count = 0

    def getBanker(self, playerCount, isFirst, winLoose, winSeatId):
        """子类必须实现
        参数：
        1）isFirst 是否第一句
        2）winLoose 上局的结果 1分出了胜负 0流局
        3）winSeatId 赢家的座位号，如果第二个参数为0，则本参数为上一局的庄家
        """
        return 0, 0, 0

    def queryBanker(self):
        """查询当前的庄家
        """
        return self.banker
