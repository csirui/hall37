# -*- coding=utf-8 -*-

'''
Created on 2013-3-18

@author: Administrator
'''
from poker.servers.util.direct import dbexchange


def getExchangeDataAll(userId, gameId):
    '''
    取得用户所有的任务数据
    @return: list<(exchangeId, bytes)>
    '''
    return dbexchange._getExchangeDataAll(userId, gameId)


def getExchangeData(userId, gameId, exchangeId):
    '''
    取得用户对应的任务数据
    @return: bytes
    '''
    return dbexchange._getExchangeData(userId, gameId, exchangeId)


def setExchangeData(userId, gameId, exchangeId, exchangeData):
    '''
    设置用户的一个任务的数据
    '''
    return dbexchange._setExchangeData(userId, gameId, exchangeId, exchangeData)
