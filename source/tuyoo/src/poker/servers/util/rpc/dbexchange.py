# -*- coding=utf-8

import poker.servers.util.direct.dbexchange as _dbexchange
from poker.protocol.rpccore import markRpcCall


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getExchangeDataAll(userId, gameId):
    return _dbexchange._getExchangeDataAll(userId, gameId)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setExchangeData(userId, gameId, exchangeId, exchangeData):
    return _dbexchange._setExchangeData(userId, gameId, exchangeId, exchangeData)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getExchangeData(userId, gameId, exchangeId):
    return _dbexchange._getExchangeData(userId, gameId, exchangeId)
