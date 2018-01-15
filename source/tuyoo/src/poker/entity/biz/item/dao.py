# -*- coding=utf-8
'''
Created on 2015年6月2日

@author: zhaojiangang
'''


class TYItemDataDao(object):
    def loadAll(self, userId):
        '''
        加载用户所有道具
        @param userId: 哪个用户
        @return: list<(itemId, bytes)>
        '''
        raise NotImplemented()

    def saveItem(self, userId, itemId, itemData):
        '''
        保存道具
        @param userId: 哪个用户
        @param itemId: 道具ID
        @param itemData: bytes 
        '''
        raise NotImplemented()

    def removeItem(self, userId, itemId):
        '''
        删除一个道具
        @param userId: 哪个用户
        @param itemId: 道具ID
        '''
        raise NotImplemented()

    def nextItemId(self):
        '''
        获取下一个道具ID
        @return: itemId
        '''
        raise NotImplemented()
