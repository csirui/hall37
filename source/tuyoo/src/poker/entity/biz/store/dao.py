# -*- coding=utf-8
'''
Created on 2015年6月8日

@author: zhaojiangang
'''


class TYOrderDao(object):
    def addOrder(self, order):
        '''
        增加order
        '''
        raise NotImplemented()

    def loadOrder(self, orderId):
        '''
        加载order
        '''
        raise NotImplemented()

    def updateOrder(self, order, expectState):
        '''
        更新order
        '''
        raise NotImplemented()


class TYClientStoreConf(object):
    def findTemplateNameByClientId(self, clientId):
        '''
        根据clientId查找商城模版名称
        '''
        raise NotImplemented()

    def isClosedLastBuy(self, clientId):
        '''
        判断clientId是否关闭了最后购买记录
        '''
        raise NotImplemented()
