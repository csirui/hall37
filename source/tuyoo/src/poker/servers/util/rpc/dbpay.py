# -*- coding=utf-8 -*-

'''
Created on 2013-3-18

@author: Administrator
'''

import poker.servers.util.direct.dbpay as _dbpay
from poker.protocol.rpccore import markRpcCall


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getExchangeRecords(gameId, userId):
    return _dbpay._getExchangeRecords(gameId, userId)


@markRpcCall(groupName="", lockName="", syncCall=1)
def _makeExchangeId():
    return _dbpay._makeExchangeId()


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _makeGameOrderId(gameId, userId, productId):
    return _dbpay._makeGameOrderId(gameId, userId, productId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setGameOrderInfo(userId, orderId, datas):
    return _dbpay._setGameOrderInfo(userId, orderId, datas)


@markRpcCall(groupName="", lockName="", syncCall=1)
def _getGameOrderInfo(orderId):
    return _dbpay._getGameOrderInfo(orderId)
