# -*- coding=utf-8 -*-

'''
Created on 2013-3-18

@author: Administrator
'''
from poker.entity.dao import weakdata


def getDay1stDatas(userId, gameId):
    return weakdata.getWeakData(userId, gameId, weakdata.CYCLE_TYPE_DAY, '1st')


def setDay1stDatas(userId, gameId, datas):
    return weakdata.setWeakData(userId, gameId, weakdata.CYCLE_TYPE_DAY, '1st', datas)


def isDayFirstLogin(userId, gameId):
    day1stData = getDay1stDatas(userId, gameId)
    return day1stData.get("daylogin", 0) == 1
