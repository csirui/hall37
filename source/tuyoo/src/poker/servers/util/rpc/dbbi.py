# -*- coding=utf-8

import poker.servers.util.direct.dbbi as _dbbi
from poker.protocol.rpccore import markRpcCall


@markRpcCall(groupName="", lockName="", syncCall=1)
def _incrGcoin(rkey, coinKey, detalCount):
    return _dbbi._incrGcoin(rkey, coinKey, detalCount)


@markRpcCall(groupName="", lockName="", syncCall=1)
def _setConnOnLineInfo(serverId, userCount):
    return _dbbi._setConnOnLineInfo(serverId, userCount)


@markRpcCall(groupName="", lockName="", syncCall=1)
def _getConnOnlineUserCount():
    return _dbbi._getConnOnlineUserCount()


@markRpcCall(groupName="", lockName="", syncCall=1)
def _setRoomOnLineInfo(gameId, roomId, userCount, playTableCount, observerCount):
    return _dbbi._setRoomOnLineInfo(gameId, roomId, userCount, playTableCount, observerCount)


@markRpcCall(groupName="", lockName="", syncCall=1)
def _getRoomOnLineUserCount(gameId, withShadowRoomInfo):
    return _dbbi._getRoomOnLineUserCount(gameId, withShadowRoomInfo)
