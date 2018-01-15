# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
每个配置项必须是JSON格式
'''

from poker.entity.configure import configure


def getIntegrate():
    return configure.getJson('poker:global', {}).get('integrate', {})


getConfigGameIds = configure.getConfigGameIds


def getCmds():
    return configure.getJson('poker:cmd', {})


def getOldCmds():
    return configure.getJson('poker:oldcmd', {})


clientIdToNumber = configure.clientIdToNumber
numberToClientId = configure.numberToClientId


def productIdToNumber(productId):
    '''
    转换商品ID字符串定义至INTEGER_ID的定义
    '''
    return configure.stringIdToNumber('poker:map.productid', productId)


def giftIdToNumber(giftId):
    '''
    转换礼物ID字符串定义至INTEGER_ID的定义
    '''
    return configure.stringIdToNumber('poker:map.giftid', giftId)


def biEventIdToNumber(eventName):
    '''
    取得事件ID字符串对应的INTEGER_ID的定义
    '''
    return configure.stringIdToNumber('poker:map.bieventid', eventName)


def activityIdToNumber(activityName):
    '''
    取得活动ID字符串对应的NTEGER_ID的定义
    '''
    return configure.stringIdToNumber('poker:activityid', activityName)


def getConnLogoutMsg(errorCode, defaultVal):
    '''
    关闭TCP连接时, 通知客户端的error消息内容
    '''
    pgdict = configure.getJson('poker:global')
    return pgdict.get('conn_logout_error_msg_' + str(errorCode), defaultVal)


def isOpenMoreTable(clientId):
    '''
    判定一个clientId是否支持多开
    目前都不支持
    '''
    return False
