# -*- coding=utf-8

import base64

from freetime.util.cache import lfu_time_cache
from poker.entity.dao import daobase
from poker.entity.dao.daoconst import GameItemSchema
from poker.protocol.rpccore import markRpcCall
from poker.servers.util.rpc.dbuser import _CACHE_SIZE, _CACHE_GROUP

_CACHE_ITEM_ENABLE = 0


@lfu_time_cache(maxsize=_CACHE_SIZE, mainindex=0, subindex=1, group=_CACHE_GROUP)
def _cacheItem(userId, dataKey):
    return _getItemDataRedis(userId, dataKey)


def _getItemDataRedis(userId, dataKey):
    itemDict = {}
    datas = daobase.executeUserCmd(userId, 'HGETALL', dataKey)
    if datas:
        x = 0
        for i in xrange(len(datas) / 2):
            x = i * 2
            itemDict[int(datas[x])] = base64.b64encode(datas[x + 1])
    return itemDict


def _getItemDataAll(userId, gameId):
    itemDict = _getItemDataAll_(userId, gameId)
    items = []
    if itemDict:
        for k, v in itemDict.items():
            items.append([int(k), base64.b64decode(v)])
    return items


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getItemDataAll_(userId, gameId):
    '''
    取得用户所有的道具数据
    '''
    dataKey = GameItemSchema.mkey(gameId, userId)
    if _CACHE_ITEM_ENABLE:
        return _cacheItem(userId, dataKey)
    else:
        return _getItemDataRedis(userId, dataKey)


def _setItemData(userId, gameId, itemId, itemData):
    itemDataB64 = base64.b64encode(itemData)
    return _setItemData_(userId, gameId, itemId, itemDataB64)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setItemData_(userId, gameId, itemId, itemDataB64):
    '''
    设置用户的一个道具的数据
    '''
    itemData = base64.b64decode(itemDataB64)
    dataKey = GameItemSchema.mkey(gameId, userId)
    data = daobase.executeUserCmd(userId, 'HSET', dataKey, itemId, itemData)
    if _CACHE_ITEM_ENABLE:
        _cacheItem.update_group_dict_data(userId, dataKey, {int(itemId): itemDataB64})
    return data


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _delItemData(userId, gameId, itemId):
    '''
    删除用户的一个道具的数据
    '''
    dataKey = GameItemSchema.mkey(gameId, userId)
    data = daobase.executeUserCmd(userId, 'HDEL', dataKey, itemId)
    if _CACHE_ITEM_ENABLE:
        _cacheItem.remove_group_dict_data(userId, dataKey, {int(itemId): 0})
    return data
