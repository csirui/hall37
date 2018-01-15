# -*- coding: utf-8 -*-
'''
Created on 2014年2月20日

@author: zjgzzz@126.com
'''

import freetime.util.log as ftlog
from poker.entity.configure import pokerconf
from poker.entity.dao import userdata
from poker.entity.dao.daoconst import UserSessionSchema
from poker.util import strutil


def getClientId(userId):
    '''
    取得用户的当前的客户端ID
    '''
    datas = userdata.getSessionData(userId)
    return datas[UserSessionSchema.CLIENTID]


def getCityZip(userId):
    datas = userdata.getSessionData(userId)
    return datas[UserSessionSchema.CITYCODE][0]


def getCityName(userId):
    datas = userdata.getSessionData(userId)
    name = datas[UserSessionSchema.CITYCODE][1]
    if name:
        return name
    else:
        return '全国'


def getClientIp(userId):
    datas = userdata.getSessionData(userId)
    return datas[UserSessionSchema.IPADDRESS]


def getGameId(userId):
    datas = userdata.getSessionData(userId)
    return datas[UserSessionSchema.APPID]


def getDeviceId(userId):
    datas = userdata.getSessionData(userId)
    return datas[UserSessionSchema.DEVICEID]


def getConnId(userId):
    datas = userdata.getSessionData(userId)
    return datas[UserSessionSchema.CONN]


def getClientIdInfo(userId):
    '''
    取得用户的当前的客户端ID的分解信息
    返回: 客户端的OS, 客户端的版本, 客户端的渠道, 客户端ID
    '''
    clientId = getClientId(userId)
    clientOs, clientVer, clientChannel = strutil.parseClientId(clientId)
    return clientOs, clientVer, clientChannel, clientId


def _parseClientIdNum(clientId):
    if isinstance(clientId, (str, unicode)):
        return pokerconf.clientIdToNumber(clientId)
    elif isinstance(clientId, (int, float)):
        return int(clientId)
    return 0


def getClientIdNum(userId, clientId=None):
    '''
    取得用户的当前的客户端ID的数字ID
    '''
    if clientId:
        clientNum = _parseClientIdNum(clientId)
        if clientNum:
            return clientId, clientNum
    ci = None
    if userId:
        ci = getClientId(userId)
        if ci:
            clientNum = _parseClientIdNum(ci)
            if clientNum:
                return ci, clientNum
    ftlog.error('getClientIdNum clientId=', clientId, 'ci=', ci, 'userId=', userId, 'UnknownClientId Final')
    return '', 0


def getClientIdSys(userId):
    clientOs, _, _, _ = getClientIdInfo(userId)
    return clientOs


def getClientIdVer(userId):
    _, clientVer, _, _ = getClientIdInfo(userId)
    return clientVer


def getClientIdChanel(userId):
    _, _, clientChannel, _ = getClientIdInfo(userId)
    return clientChannel
