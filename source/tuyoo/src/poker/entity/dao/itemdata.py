# -*- coding=utf-8 -*-

'''
Created on 2013-3-18

@author: Administrator
'''
from poker.servers.util.direct import dbitem


def getItemDataAll(userId, gameId):
    '''
    取得用户所有的道具数据
    @return: list<(itemId, bytes)>
    '''
    return dbitem._getItemDataAll(userId, gameId)


def setItemData(userId, gameId, itemId, itemData):
    '''
    设置用户的一个道具的数据
    '''
    return dbitem._setItemData(userId, gameId, itemId, itemData)


def delItemData(userId, gameId, itemId):
    '''
    删除用户的一个道具的数据
    '''
    return dbitem._delItemData(userId, gameId, itemId)
