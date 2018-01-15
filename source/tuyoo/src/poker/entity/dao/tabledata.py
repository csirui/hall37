# -*- coding=utf-8 -*-

from poker.entity.dao import daoconst, daobase
from poker.servers.util.rpc._private import user_scripts


def getTableAttrs(roomId, tableId, attrlist, filterKeywords=True):
    '''
    获取用户游戏属性列表
    '''
    values = daobase.executeTableCmd(roomId, tableId, 'HMGET', daoconst.HKEY_TABLEDATA % (roomId, tableId), *attrlist)
    if values and filterKeywords:
        return daobase.filterValues(attrlist, values)
    return values


def setTableAttrs(roomId, tableId, attrlist, valuelist):
    '''
    设置用户游戏属性列表
    '''
    gdkv = []
    for k, v in zip(attrlist, valuelist):
        gdkv.append(k)
        gdkv.append(v)
        assert (k not in daoconst.FILTER_MUST_FUNC_FIELDS)
    daobase.executeTableCmd(roomId, tableId, 'HMSET', daoconst.HKEY_TABLEDATA % (roomId, tableId), *gdkv)


def delTableAttrs(roomId, tableId, attrlist):
    '''
    删除用户游戏属性列表
    '''
    values = daobase.executeTableCmd(roomId, tableId, 'HDEL', daoconst.HKEY_TABLEDATA % (roomId, tableId), *attrlist)
    return values


def getTableAttr(roomId, tableId, attrname, filterKeywords=True):
    '''
    获取用户游戏属性
    '''
    value = daobase.executeTableCmd(roomId, tableId, 'HGET', daoconst.HKEY_TABLEDATA % (roomId, tableId), attrname)
    if value and filterKeywords:
        return daobase.filterValue(attrname, value)
    return value


def setTableAttr(roomId, tableId, attrname, value):
    '''
    设置用户游戏属性
    '''
    assert (attrname not in daoconst.FILTER_MUST_FUNC_FIELDS)
    daobase.executeTableCmd(roomId, tableId, 'HSET', daoconst.HKEY_TABLEDATA % (roomId, tableId), attrname, value)


def incrTableAttr(roomId, tableId, attrname, value):
    '''
    INCR用户游戏属性
    '''
    assert (attrname not in daoconst.FILTER_MUST_FUNC_FIELDS)
    return daobase.executeTableCmd(roomId, tableId, 'HINCRBY', daoconst.HKEY_TABLEDATA % (roomId, tableId), attrname,
                                   value)


def incrTableAttrLimit(roomId, tableId, attrname, deltaCount, lowLimit, highLimit, chipNotEnoughOpMode):
    '''
    INCR用户游戏属性
    参考: incr_chip_limit
    '''
    assert (attrname not in daoconst.FILTER_MUST_FUNC_FIELDS)
    trueDetal, finalCount, fixCount = daobase.executeTableLua(roomId, tableId, user_scripts.MAIN_INCR_CHIP_LUA_SCRIPT,
                                                              6, deltaCount, lowLimit, highLimit,
                                                              chipNotEnoughOpMode,
                                                              daoconst.HKEY_TABLEDATA % (roomId, tableId), attrname)
    return trueDetal, finalCount, fixCount
