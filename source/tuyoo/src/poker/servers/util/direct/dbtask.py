# -*- coding=utf-8

from poker.entity.dao import daobase
from poker.entity.dao.daoconst import GameTaskSchema


def _getTaskDataAll(userId, gameId):
    tasks = []
    dataKey = GameTaskSchema.mkey(gameId, userId)
    datas = daobase.executeUserCmd(userId, 'HGETALL', dataKey)
    if datas:
        x = 0
        for i in xrange(len(datas) / 2):
            x = i * 2
            tasks.append([int(datas[x]), datas[x + 1]])
    return tasks


def _setTaskData(userId, gameId, taskId, taskData):
    '''
    设置用户的一个道具的数据
    '''
    dataKey = GameTaskSchema.mkey(gameId, userId)
    data = daobase.sendUserCmd(userId, 'HSET', dataKey, taskId, taskData)
    return data


def _delTaskData(userId, gameId, taskId):
    '''
    删除用户的一个道具的数据
    '''
    dataKey = GameTaskSchema.mkey(gameId, userId)
    data = daobase.sendUserCmd(userId, 'HDEL', dataKey, taskId)
    return data
