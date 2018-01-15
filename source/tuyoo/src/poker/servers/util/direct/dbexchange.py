# -*- coding=utf-8

from poker.entity.dao import daobase
from poker.entity.dao.daoconst import GameExchangeSchema


def _getExchangeDataAll(userId, gameId):
    '''
    取得用户所有的兑换数据
    '''
    datas = daobase.executeUserCmd(userId, 'HGETALL', GameExchangeSchema.mkey(gameId, userId))
    return datas


def _setExchangeData(userId, gameId, exchangeId, exchangeData):
    '''
    设置用户的一个兑换的数据
    '''
    data = daobase.executeUserCmd(userId, 'HSET', GameExchangeSchema.mkey(gameId, userId), exchangeId, exchangeData)
    return data


def _getExchangeData(userId, gameId, exchangeId):
    '''
    设置用户的一个兑换的数据
    '''
    data = daobase.executeUserCmd(userId, 'HGET', GameExchangeSchema.mkey(gameId, userId), exchangeId)
    return data
