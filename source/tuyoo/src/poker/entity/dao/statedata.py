# -*- coding: utf-8 -*-
'''
Created on 2016-7-7
@author: wuyongsheng
说明：因为，活动需要添加小红点，标记用户是否查看了该活动
    所以，创建一个key，用来存储用户的活动列表，标明用户的活动状态
'''

from poker.entity.dao import daoconst, daobase
from poker.util import strutil


def getStateAttrs(uid, gameid, attrlist, filterKeywords=False):
    '''
    获取用户状态属性列表
    '''
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    values = daobase.executeUserCmd(uid, 'HMGET', daoconst.HKEY_STATEDATA + str(gameid) + ':' + str(uid), *attrlist)
    if values and filterKeywords:
        return daobase.filterValues(attrlist, values)
    return values


def setStateAttrs(uid, gameid, attrlist, valuelist):
    '''
    设置用户状态属性列表
    '''
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    gdkv = []
    for k, v in zip(attrlist, valuelist):
        gdkv.append(k)
        gdkv.append(v)
        assert (k not in daoconst.FILTER_MUST_FUNC_FIELDS)
    return daobase.executeUserCmd(uid, 'HMSET', daoconst.HKEY_STATEDATA + str(gameid) + ':' + str(uid), *gdkv)


def delStateAttr(uid, gameid, attrname):
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    return daobase.executeUserCmd(uid, 'HDEL', daoconst.HKEY_STATEDATA + str(gameid) + ':' + str(uid), attrname)


def delStateAttrs(uid, gameid, attrlist):
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    return daobase.executeUserCmd(uid, 'HDEL', daoconst.HKEY_STATEDATA + str(gameid) + ':' + str(uid), *attrlist)


def getStateAttr(uid, gameid, attrname, filterKeywords=False):
    '''
    获取用户状态属性
    '''
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    value = daobase.executeUserCmd(uid, 'HGET', daoconst.HKEY_STATEDATA + str(gameid) + ':' + str(uid), attrname)
    if value and filterKeywords:
        return daobase.filterValue(attrname, value)
    return value


def getAllAttrs(uid, gameid, key):
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    return daobase.executeUserCmd(uid, 'HGETALL', '%s:%s:%s' % (key, gameid, uid))


def getStateAttrJson(uid, gameid, attrname, defaultVal=None):
    '''
    获取用户状态属性
    '''
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    value = getStateAttr(uid, gameid, attrname)
    value = strutil.loads(value, False, True, defaultVal)
    return value


def setStateAttr(uid, gameid, attrname, value):
    '''
    设置用户状态属性
    '''
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    assert (attrname not in daoconst.FILTER_MUST_FUNC_FIELDS)
    return daobase.executeUserCmd(uid, 'HSET', daoconst.HKEY_STATEDATA + str(gameid) + ':' + str(uid), attrname, value)


def getStateAttrInt(uid, gameid, attrname):
    '''
    获取用户状态属int
    '''
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    value = getStateAttr(uid, gameid, attrname)
    if not isinstance(value, (int, float)):
        return 0
    return int(value)


def setnxStateAttr(uid, gameid, attrname, value):
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    return daobase.executeUserCmd(uid, 'HSETNX', daoconst.HKEY_STATEDATA + str(gameid) + ':' + str(uid), attrname,
                                  value)


def isStateExists(uid, gameid):
    '''
    判定当前的状态数据是否存在
    '''
    assert (isinstance(gameid, int) and gameid > 0), 'gameid must be int'
    return daobase.executeUserCmd(uid, 'EXISTS', daoconst.HKEY_STATEDATA + str(gameid) + ':' + str(uid))
