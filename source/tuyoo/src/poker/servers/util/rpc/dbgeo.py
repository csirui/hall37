# -*- coding=utf-8

import poker.servers.util.direct.dbgeo as _dbgeo
from poker.protocol.rpccore import markRpcCall


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setUserGeoOffline(userId, gameId):
    return _dbgeo._setUserGeoOffline(userId, gameId)
