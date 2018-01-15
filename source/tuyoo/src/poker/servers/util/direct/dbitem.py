# -*- coding=utf-8

from poker.entity.dao import daobase
from poker.entity.dao.daoconst import GameItemSchema


def _getItemDataAll(userId, gameId):
    items = []
    dataKey = GameItemSchema.mkey(gameId, userId)
    datas = daobase.executeUserCmd(userId, 'HGETALL', dataKey)
    if datas:
        x = 0
        for i in xrange(len(datas) / 2):
            x = i * 2
            items.append([int(datas[x]), datas[x + 1]])
    return items


def _setItemData(userId, gameId, itemId, itemData):
    '''
    设置用户的一个道具的数据
    '''
    dataKey = GameItemSchema.mkey(gameId, userId)
    data = daobase.sendUserCmd(userId, 'HSET', dataKey, itemId, itemData)
    return data


def _delItemData(userId, gameId, itemId):
    '''
    删除用户的一个道具的数据
    '''
    dataKey = GameItemSchema.mkey(gameId, userId)
    data = daobase.sendUserCmd(userId, 'HDEL', dataKey, itemId)
    return data
