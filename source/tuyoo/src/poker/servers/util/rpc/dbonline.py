# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import poker.servers.util.direct.dbonline as _dbonline
from poker.entity.dao import daobase, daoconst
from poker.protocol.rpccore import markRpcCall


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setOnlineState(userId, state):
    return _dbonline._setOnlineState(userId, state)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setGameOnline(userId, gameId, groupname):
    return _dbonline._setGameOnline(userId, gameId, groupname)


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def _setGameOffline(userId, gameId, groupname):
    return _dbonline._setGameOffline(userId, gameId, groupname)


@markRpcCall(groupName="", lockName="", syncCall=1)
def _executeOnlineSet(*cmds):
    return daobase._executeOnlineCmd(*cmds)


def _getOnlineRandUserIds(count):
    '''
    随机取得count个在线用户的ID列表, 如果集合的数量不足count个, 那么返回集合所有内容
    '''
    assert (isinstance(count, int) and count > 1)
    return _executeOnlineSet('SRANDMEMBER', daoconst.ONLINE_KEY_USERS, count)


def _getGameOnlineUserIds(gameId, groupname, callback):
    '''
    取得当前游戏的在线分组的所有userid列表
    数据库中, 存储的键值为: onlinelist:<gameId>:<groupname>
    每次返回最多1000个userid, 调用callback函数
    例如: callback([10001, 10003, 10023])
    '''
    assert (callable(callback))
    key = daoconst.ONLINE_KEY_LIST % (gameId, groupname)
    cur = -1
    count = 0
    while cur != 0:
        if cur < 0: cur = 0
        datas = _executeOnlineSet('SSCAN', key, cur, 'COUNT', 999)
        cur = datas[0]
        userIds = datas[1]
        count += len(userIds)
        if userIds:
            callback(userIds)
    return count


def _getGameOnlineRandUserIds(gameId, groupname, count):
    '''
    取得当前游戏的在线分组的所有userid列表
    数据库中, 存储的键值为: onlinelist:<gameId>:<groupname>
    随机返回count个集合中的userId列表
    '''
    assert (isinstance(count, int) and count > 1)
    key = daoconst.ONLINE_KEY_LIST % (gameId, groupname)
    datas = _executeOnlineSet('SRANDMEMBER', key, count)
    return datas


def _getGameOnlineCount(gameId, groupname):
    '''
    取得当前游戏的在线分组的userId的数量
    数据库中, 存储的键值为: onlinelist:<gameId>:<groupname>
    返回集合的元素个数
    '''
    key = daoconst.ONLINE_KEY_LIST % (gameId, groupname)
    datas = _executeOnlineSet('SCARD', key)
    return datas
