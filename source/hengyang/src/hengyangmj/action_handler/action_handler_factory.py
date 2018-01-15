# -*- coding=utf-8
'''
Created on 2017年3月1日

@author: nick.kai.lee
'''
from difang.majiang2.action_handler.action_handler_factory import ActionHandlerFactory


class HYActionHandlerFactory(ActionHandlerFactory):
    def __init__(self):
        super(HYActionHandlerFactory, self).__init__()

    @classmethod
    def getActionHandler(cls, runMode):
        """发牌器获取工厂
        输入参数：
            playMode - 玩法
        
        返回值：
            对应玩法的发牌算法
        """
