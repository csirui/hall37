# -*- coding=utf-8

import base64

from freetime.util.cache import lfu_time_cache
from poker.entity.dao import daobase
from poker.entity.dao.daoconst import GameTaskSchema
from poker.protocol.rpccore import markRpcCall
from poker.servers.util.rpc.dbuser import _CACHE_SIZE, _CACHE_GROUP

_CACHE_TASK_ENABLE = 0


@lfu_time_cache(maxsize=_CACHE_SIZE, mainindex=0, subindex=1, group=_CACHE_GROUP)
def _cacheTask(userId, dataKey):
    return _getTaskDataRedis(userId, dataKey)


def _getTaskDataRedis(userId, dataKey):
    taskDict = {}
    datas = daobase.executeUserCmd(userId, 'HGETALL', dataKey)
    if datas:
        x = 0
        for i in xrange(len(datas) / 2):
            x = i * 2
            taskDict[int(datas[x])] = base64.b64encode(datas[x + 1])
    return taskDict


def _getTaskDataAll(userId, gameId):
    taskDict = _getTaskDataAll_(userId, gameId)
    tasks = []
    if taskDict:
        for k, v in taskDict.items():
            tasks.append([int(k), base64.b64decode(v)])
    return tasks


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _getTaskDataAll_(userId, gameId):
    '''
    取得用户所有的道具数据
    '''
    dataKey = GameTaskSchema.mkey(gameId, userId)
    if _CACHE_TASK_ENABLE:
        return _cacheTask(userId, dataKey)
    else:
        return _getTaskDataRedis(userId, dataKey)


def _setTaskData(userId, gameId, taskId, taskData):
    taskDataB64 = base64.b64encode(taskData)
    return _setTaskData_(userId, gameId, taskId, taskDataB64)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setTaskData_(userId, gameId, taskId, taskDataB64):
    '''
    设置用户的一个道具的数据
    '''
    taskData = base64.b64decode(taskDataB64)
    dataKey = GameTaskSchema.mkey(gameId, userId)
    data = daobase.executeUserCmd(userId, 'HSET', dataKey, taskId, taskData)
    if _CACHE_TASK_ENABLE:
        _cacheTask.update_group_dict_data(userId, dataKey, {int(taskId): taskDataB64})
    return data


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _delTaskData(userId, gameId, taskId):
    '''
    删除用户的一个道具的数据
    '''
    dataKey = GameTaskSchema.mkey(gameId, userId)
    data = daobase.executeUserCmd(userId, 'HDEL', dataKey, taskId)
    if _CACHE_TASK_ENABLE:
        _cacheTask.remove_group_dict_data(userId, dataKey, {int(taskId): 0})
    return data
