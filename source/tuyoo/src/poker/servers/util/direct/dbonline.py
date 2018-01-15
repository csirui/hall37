# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from poker.entity.dao import daobase, daoconst

_ONLINE_LIST_ALLKEYS = None


def _checkOnlineKeys(newKey=None):
    global _ONLINE_LIST_ALLKEYS
    if not _ONLINE_LIST_ALLKEYS:
        _ONLINE_LIST_ALLKEYS = set([daoconst.ONLINE_KEY_USERS])
        keys = daobase._executeOnlineCmd('SMEMBERS', daoconst.ONLINE_KEY_ALLKEYS)
        if keys:
            _ONLINE_LIST_ALLKEYS.update(keys)
    if newKey and newKey not in _ONLINE_LIST_ALLKEYS:
        _ONLINE_LIST_ALLKEYS.add(newKey)
        daobase._executeOnlineCmd('SADD', daoconst.ONLINE_KEY_ALLKEYS, newKey)
    return _ONLINE_LIST_ALLKEYS


def _setOnlineState(userId, state):
    if state == daoconst.OFFLINE:
        for key in _checkOnlineKeys():
            daobase._executeOnlineCmd('SREM', key, userId)
    else:
        daobase._executeOnlineCmd('SADD', daoconst.ONLINE_KEY_USERS, userId)


def _setGameOnline(userId, gameId, groupname):
    '''
    设置用户再当前游戏的在线状态为"在线"
    通常再bind_game时调用此方法
    groupname为一个分组名称的列表, 例如:'chip_gt_100w', 'vipuser'
    数据库中, 存储的键值为: onlinelist:<gameId>:<groupname>
    数据onlinelist_allkeys包含了所有出现过的数据集合键值, 再删除online状态时使用, 
    因此,需要系统每个一段时间检查这个集合中的值是否是有效的键值
    '''
    key = daoconst.ONLINE_KEY_LIST % (gameId, groupname)
    daobase._executeOnlineCmd('SADD', key, userId)
    _checkOnlineKeys(key)


def _setGameOffline(userId, gameId, groupname):
    '''
    设置用户再当前游戏的在线状态为"离线"
    groupname为一个分组名称的列表, 例如:'chip_gt_100w', 'vipuser'
    数据库中, 存储的键值为: onlinelist:<gameId>:<groupname>
    通常再unbind_game时或用户TCP断线时调用此方法,
    '''
    key = daoconst.ONLINE_KEY_LIST % (gameId, groupname)
    return daobase._executeOnlineCmd('SREM', key, userId)


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
