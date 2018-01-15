# -*- coding=utf-8 -*-

'''
Created on 2013-3-18

@author: Administrator
'''
from poker.servers.util.direct import dbtask


def getTaskDataAll(userId, gameId):
    '''
    取得用户所有的任务数据
    @return: list<(taskId, bytes)>
    '''
    return dbtask._getTaskDataAll(userId, gameId)


def setTaskData(userId, gameId, taskId, taskData):
    '''
    设置用户的一个任务的数据
    '''
    return dbtask._setTaskData(userId, gameId, taskId, taskData)


def delTaskData(userId, gameId, taskId):
    '''
    删除用户的一个任务的数据
    '''
    return dbtask._delTaskData(userId, gameId, taskId)
