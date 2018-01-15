# -*- coding: utf-8 -*-
'''
Created on 2015年5月20日

@author: zqh
'''

from poker.entity.configure import gdata
from poker.protocol import rpccore


def doCheckUserLoc(userId, gameId, roomId, tableId, clientId):
    assert (isinstance(userId, int))
    assert (isinstance(roomId, int))
    assert (isinstance(tableId, int))
    serverId = rpccore.getRpcDstRoomServerId(roomId, 0)
    if not serverId:
        return -1, 0
    assert (serverId in gdata.allServersMap())
    ret = _doCheckUserLoc(serverId, userId, gameId, roomId, tableId, clientId)
    return ret


@rpccore.markRpcCall(groupName=rpccore.RPC_FIRST_SERVERID, lockName="", syncCall=1)
def _doCheckUserLoc(serverId, userId, gameId, roomId, tableId, clientId):
    seatId, isObserving = gdata.rooms()[roomId].doCheckUserLoc(userId, gameId, roomId, tableId, clientId)
    return seatId, isObserving
