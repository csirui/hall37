# -*- coding=utf-8 -*-

'''
Created on 2013-3-18

@author: Administrator
'''

from poker.servers.util.direct import dbuser
from poker.util import timestamp

CYCLE_TYPE_DAY = 1  # 每天循环(自然天)
CYCLE_TYPE_WEEK = 2  # 每星期循环(自然周)
CYCLE_TYPE_MONTH = 3  # 每月循环(自然月)


def _getCycleInfo(cycleType):
    assert (cycleType in (CYCLE_TYPE_DAY, CYCLE_TYPE_WEEK, CYCLE_TYPE_MONTH))
    if cycleType == CYCLE_TYPE_DAY:
        curCycle = timestamp.formatTimeDayInt()
        expire = 86400  # 1天后自动过期
        cycleName = 'day'
    elif cycleType == CYCLE_TYPE_WEEK:
        curCycle = timestamp.formatTimeWeekInt()
        expire = 604800  # 86400 * 7 7天后自动过期
        cycleName = 'week'
    elif cycleType == CYCLE_TYPE_MONTH:
        curCycle = timestamp.formatTimeMonthInt()
        expire = 2678400  # 86400 * 31 31天后自动过期
        cycleName = 'month'
    return cycleName, curCycle, expire


def getWeakData(userId, gameId, cycleType, datakey):
    '''
    取得一个用户的弱存储数据, 例如: 每日登陆的数据,凌晨过后即被清空重新建立
    cycleType 参考: CYCLE_TYPE_DAY, CYCLE_TYPE_WEEK, CYCLE_TYPE_MONTH
    返回必定是一个dict数据集合
    可参考day1st.py的使用方法
    '''
    cycleName, curCycle, _ = _getCycleInfo(cycleType)
    return dbuser._getWeakData(userId, gameId, datakey, cycleName, curCycle)


def setWeakData(userId, gameId, cycleType, datakey, datas):
    '''
    设置一个用户的弱存储数据, 例如: 每日登陆的数据,凌晨过后即被清空重新建立
    cycleType 参考: CYCLE_TYPE_DAY, CYCLE_TYPE_WEEK, CYCLE_TYPE_MONTH
    datas必须是一个dict数据集合
    可参考day1st.py的使用方法
    '''
    cycleName, curCycle, expire = _getCycleInfo(cycleType)
    if datas != None:
        assert (isinstance(datas, dict))
    return dbuser._setWeakData(userId, gameId, datakey, datas, cycleName, curCycle, expire)
