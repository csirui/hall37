# -*- coding:utf-8 -*-
'''
Created on 2016年1月22日

@author: zhaojiangang
'''

import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from hall.entity import hallitem, datachangenotify
from poker.entity.biz.content import TYContentItem
from poker.entity.biz.item.exceptions import TYAssetNotEnoughException
from poker.entity.biz.item.item import TYAssetUtils
from poker.entity.dao import daobase, onlinedata
from poker.protocol.rpccore import markRpcCall
from poker.util import strutil


class UserMatchInfo(object):
    ST_SIGNIN = 1
    ST_PLAYING = 2

    def __init__(self, gameId, userId, bigRoomId):
        self.gameId = gameId
        self.userId = userId
        self.bigRoomId = bigRoomId
        self.ctrlRoomId = None
        self.instId = None
        self.state = UserMatchInfo.ST_SIGNIN
        self.feeItem = None


def buildKey(gameId, userId):
    return 'minfo:%s:%s' % (gameId, userId)


def decodeUserMatchInfo(gameId, userId, bigRoomId, jstr):
    d = strutil.loads(jstr)
    if d:
        ret = UserMatchInfo(gameId, userId, bigRoomId)
        ret.state = d['st']
        ret.instId = d['instId']
        ret.ctrlRoomId = d['crid']
        fee = d.get('fee')
        if fee:
            ret.feeItem = TYContentItem.decodeFromDict(fee)
        return ret
    return None


def loadUserMatchInfo(gameId, userId, bigRoomId):
    try:
        key = buildKey(gameId, userId)
        jstr = daobase.executeUserCmd(userId, 'hget', key, bigRoomId)
        if jstr:
            return decodeUserMatchInfo(gameId, userId, bigRoomId, jstr)
        return None
    except:
        ftlog.error('match_remote.loadUserMatchInfo gameId=', gameId,
                    'userId=', userId,
                    'bigRoomId=', bigRoomId)
        return None


def saveUserMatchInfo(info):
    d = {
        'st': info.state,
        'instId': info.instId,
        'crid': info.ctrlRoomId
    }
    if info.feeItem:
        d['fee'] = info.feeItem.toDict()
    jstr = strutil.dumps(d)
    key = buildKey(info.gameId, info.userId)
    daobase.executeUserCmd(info.userId, 'hset', key, info.bigRoomId, jstr)


def removeUserMatchInfo(info):
    key = buildKey(info.gameId, info.userId)
    daobase.executeUserCmd(info.userId, 'hdel', key, info.bigRoomId)


def loadAllUserMatchInfo(gameId, userId):
    ret = {}
    key = buildKey(gameId, userId)
    datas = daobase.executeUserCmd(userId, 'hgetall', key)
    if ftlog.is_debug():
        ftlog.debug('match_remote.loadAllUserMatchInfo gameId=', gameId,
                    'userId=', userId,
                    'key=', key,
                    'datas=', datas)
    if datas:
        i = 0
        while i + 1 < len(datas):
            try:
                bigRoomId = datas[i]
                userMatchInfo = decodeUserMatchInfo(gameId, userId, bigRoomId, datas[i + 1])
                if userMatchInfo:
                    ret[bigRoomId] = userMatchInfo
            except:
                ftlog.error('match_remote.loadAllUserMatchInfo gameId=', gameId,
                            'bigRoomId=', datas[i],
                            'userMatchInfo=', datas[i + 1])
            i += 2
    return ret


ERR_ALREADY_SIGNIN = -1
ERR_ALREADY_IN_MATCH = -2
ERR_FEE_NOT_ENOUGH = -3


@markRpcCall(groupName='userId', lockName='userId', syncCall=1)
def createMatchUser(gameId, userId, contentItem, bigRoomId, instId, ctrlRoomId):
    if ftlog.is_debug():
        ftlog.debug('match_remote.createUserMatchInfo gameId=', gameId,
                    'userId=', userId,
                    'contentItem=', contentItem,
                    'bigRoomId=', bigRoomId,
                    'instId=', instId,
                    'ctrlRoomId=', ctrlRoomId)
    userMatchInfo = loadUserMatchInfo(gameId, userId, bigRoomId)
    if userMatchInfo:
        if userMatchInfo.instId == instId:
            if userMatchInfo.state == UserMatchInfo.ST_SIGNIN:
                return ERR_ALREADY_SIGNIN
            return ERR_ALREADY_IN_MATCH
        else:
            ftlog.warn('match_remote.createUserMatchInfo gameId=', gameId,
                       'userId=', userId,
                       'contentItem=', contentItem,
                       'bigRoomId=', bigRoomId,
                       'instId=', instId,
                       'ctrlRoomId=', ctrlRoomId,
                       'recordInstId=', userMatchInfo.instId)

    userMatchInfo = UserMatchInfo(gameId, userId, bigRoomId)
    userMatchInfo.ctrlRoomId = ctrlRoomId
    userMatchInfo.instId = instId
    if contentItem:
        userMatchInfo.feeItem = TYContentItem.decodeFromDict(contentItem)
    saveUserMatchInfo(userMatchInfo)
    return 0


def removeMatchUser(gameId, userId, bigRoomId, instId, ctrlRoomId):
    return _removeMatchUser(gameId, userId, bigRoomId, instId, ctrlRoomId)


def _removeMatchUser(gameId, userId, bigRoomId, instId, ctrlRoomId):
    userMatchInfo = loadUserMatchInfo(gameId, userId, bigRoomId)
    if userMatchInfo:
        removeUserMatchInfo(userMatchInfo)
        return True
    return False


def lockMatchUser(gameId, userId, bigRoomId, instId, ctrlRoomId, tableId, seatId, clientId):
    if ftlog.is_debug():
        ftlog.debug('match_remote.lockMatchUser gameId=', gameId,
                    'userId=', userId,
                    'bigRoomId=', bigRoomId,
                    'instId=', instId,
                    'ctrlRoomId=', ctrlRoomId,
                    'tableId=', tableId,
                    'seatId=', seatId,
                    'clientId=', clientId)

    userMatchInfo = loadUserMatchInfo(gameId, userId, bigRoomId)
    if not userMatchInfo:
        # 此处有异常，正常要有userMatchInfo
        userMatchInfo = UserMatchInfo(gameId, userId, bigRoomId)
        userMatchInfo.ctrlRoomId = ctrlRoomId
        userMatchInfo.instId = instId
        userMatchInfo.state = UserMatchInfo.ST_SIGNIN

    userMatchInfo.ctrlRoomId = ctrlRoomId
    userMatchInfo.state = UserMatchInfo.ST_PLAYING

    saveUserMatchInfo(userMatchInfo)

    onlinedata.setBigRoomOnlineLoc(userId, ctrlRoomId, tableId, seatId)

    ftlog.info('match_remote.lockMatchUser ok gameId=', gameId,
               'userId=', userId,
               'bigRoomId=', bigRoomId,
               'instId=', instId,
               'ctrlRoomId=', ctrlRoomId,
               'tableId=', tableId,
               'seatId=', seatId,
               'clientId=', clientId)
    return True


def unlockMatchUser(gameId, userId, bigRoomId, instId, ctrlRoomId, tableId, seatId):
    if ftlog.is_debug():
        ftlog.debug('match_remote.unlockMatchUser gameId=', gameId,
                    'userId=', userId,
                    'bigRoomId=', bigRoomId,
                    'instId=', instId,
                    'ctrlRoomId=', ctrlRoomId,
                    'tableId=', tableId,
                    'seatId=', seatId)

    if _removeMatchUser(gameId, userId, bigRoomId, instId, ctrlRoomId):
        try:
            onlinedata.removeOnlineLoc(userId, ctrlRoomId, tableId)
        except:
            ftlog.error('match_remote.unlockMatchUser gameId=', gameId,
                        'userId=', userId,
                        'bigRoomId=', bigRoomId,
                        'instId=', instId,
                        'ctrlRoomId=', ctrlRoomId,
                        'tableId=', tableId,
                        'seatId=', seatId)

    ftlog.info('match_remote.unlockMatchUser ok gameId=', gameId,
               'userId=', userId,
               'bigRoomId=', bigRoomId,
               'instId=', instId,
               'ctrlRoomId=', ctrlRoomId,
               'tableId=', tableId,
               'seatId=', seatId)


@markRpcCall(groupName='userId', lockName='userId', syncCall=1)
def moveTo(gameId, userId, bigRoomId, instId, ctrlRoomId, toInstId):
    if ftlog.is_debug():
        ftlog.debug('match_remote.moveTo gameId=', gameId,
                    'userId=', userId,
                    'bigRoomId=', bigRoomId,
                    'instId=', instId,
                    'ctrlRoomId=', ctrlRoomId,
                    'toInstId=', toInstId)
    try:
        userMatchInfo = loadUserMatchInfo(gameId, userId, bigRoomId)
        if userMatchInfo:
            if userMatchInfo.instId == instId:
                userMatchInfo.instId = toInstId
                userMatchInfo.state = UserMatchInfo.ST_SIGNIN
                saveUserMatchInfo(userMatchInfo)
                ftlog.debug('match_remote.moveTo ok gameId=', gameId,
                            'userId=', userId,
                            'bigRoomId=', bigRoomId,
                            'instId=', instId,
                            'ctrlRoomId=', ctrlRoomId,
                            'toInstId=', toInstId)
                return True
            else:
                ftlog.warn('match_remote.moveTo fail gameId=', gameId,
                           'userId=', userId,
                           'bigRoomId=', bigRoomId,
                           'instId=', instId,
                           'ctrlRoomId=', ctrlRoomId,
                           'toInstId=', toInstId,
                           'recordInstId=', userMatchInfo.instId)
                return False
    except:
        ftlog.error('match_remote.moveTo exception gameId=', gameId,
                    'userId=', userId,
                    'bigRoomId=', bigRoomId,
                    'instId=', instId,
                    'ctrlRoomId=', ctrlRoomId,
                    'toInstId=', toInstId)
        return False


@markRpcCall(groupName='userId', lockName='userId', syncCall=1)
def signinMatch(gameId, userId, contentItem, bigRoomId, instId, ctrlRoomId):
    if ftlog.is_debug():
        ftlog.debug('match_remote.signinMatch gameId=', gameId,
                    'userId=', userId,
                    'contentItem=', contentItem,
                    'bigRoomId=', bigRoomId,
                    'instId=', instId,
                    'ctrlRoomId=', ctrlRoomId)
    try:
        userMatchInfo = loadUserMatchInfo(gameId, userId, bigRoomId)
        if userMatchInfo:
            if userMatchInfo.instId == instId:
                if userMatchInfo.state == UserMatchInfo.ST_SIGNIN:
                    return ERR_ALREADY_SIGNIN, None
                return ERR_ALREADY_IN_MATCH, None
            else:
                ftlog.warn('match_remote.signinMatch gameId=', gameId,
                           'userId=', userId,
                           'contentItem=', contentItem,
                           'bigRoomId=', bigRoomId,
                           'instId=', instId,
                           'ctrlRoomId=', ctrlRoomId,
                           'recordInstId=', userMatchInfo.instId)

        userMatchInfo = UserMatchInfo(gameId, userId, bigRoomId)
        userMatchInfo.ctrlRoomId = ctrlRoomId
        userMatchInfo.instId = instId
        if contentItem:
            userMatchInfo.feeItem = TYContentItem.decodeFromDict(contentItem)
        if userId > 10000 and contentItem:
            userAssets = hallitem.itemSystem.loadUserAssets(userId)
            assetTuple = userAssets.consumeAsset(gameId,
                                                 contentItem['itemId'],
                                                 contentItem['count'],
                                                 pktimestamp.getCurrentTimestamp(),
                                                 'MATCH_SIGNIN_FEE', bigRoomId)
            if assetTuple[1] < contentItem['count']:
                raise TYAssetNotEnoughException(assetTuple[0], contentItem['count'], assetTuple[2])
            # 记录用户
            datachangenotify.sendDataChangeNotify(gameId, userId, TYAssetUtils.getChangeDataNames([assetTuple]))
        saveUserMatchInfo(userMatchInfo)
        daobase.executeTableCmd(ctrlRoomId, 0, 'sadd', 'signs:' + str(ctrlRoomId), userId)
        return 0, None
    except TYAssetNotEnoughException, e:
        return ERR_FEE_NOT_ENOUGH, (e.assetKind.kindId, e.required - e.actually)


@markRpcCall(groupName='userId', lockName='userId', syncCall=1)
def signoutMatch(gameId, userId, contentItem, bigRoomId, instId, ctrlRoomId):
    if ftlog.is_debug():
        ftlog.debug('match_remote.signoutMatch gameId=', gameId,
                    'userId=', userId,
                    'contentItem=', contentItem,
                    'bigRoomId=', bigRoomId,
                    'instId=', instId,
                    'ctrlRoomId=', ctrlRoomId)
    userMatchInfo = loadUserMatchInfo(gameId, userId, bigRoomId)
    if not userMatchInfo:
        return 0, None

    if userMatchInfo.instId != instId:
        ftlog.debug('match_remote.signoutMatch diffInstId gameId=', gameId,
                    'userId=', userId,
                    'contentItem=', contentItem,
                    'bigRoomId=', bigRoomId,
                    'instId=', instId,
                    'ctrlRoomId=', ctrlRoomId,
                    'recordInstId=', userMatchInfo.instId)
        return 0, None

    if userMatchInfo.state != UserMatchInfo.ST_SIGNIN:
        return ERR_ALREADY_IN_MATCH, None

    removeUserMatchInfo(userMatchInfo)
    daobase.executeTableCmd(ctrlRoomId, 0, 'srem', 'signs:' + str(ctrlRoomId), userId)
    ftlog.debug('match_remote.signoutMatch gameId=', gameId,
                'userId=', userId,
                'contentItem=', contentItem,
                'bigRoomId=', bigRoomId,
                'instId=', instId,
                'ctrlRoomId=', ctrlRoomId)
    if userId > 10000 and contentItem:
        userAssets = hallitem.itemSystem.loadUserAssets(userId)
        item = TYContentItem.decodeFromDict(contentItem)
        assetList = userAssets.sendContentItemList(gameId, [item], 1, True,
                                                   pktimestamp.getCurrentTimestamp(),
                                                   'MATCH_RETURN_FEE', bigRoomId)
        datachangenotify.sendDataChangeNotify(gameId, userId, TYAssetUtils.getChangeDataNames(assetList))
    return 0, None


# @markRpcCall(groupName='userId', lockName='userId', syncCall=1)
def lockUserForMatch(gameId, userId, bigRoomId, instId, ctrlRoomId, tableId, seatId):
    if ftlog.is_debug():
        ftlog.debug('match_remote.lockUserForMatch gameId=', gameId,
                    'userId=', userId,
                    'bigRoomId=', bigRoomId,
                    'instId=', instId,
                    'ctrlRoomId=', ctrlRoomId,
                    'tableId=', tableId,
                    'seatId=', seatId)

    userMatchInfo = loadUserMatchInfo(gameId, userId, bigRoomId)
    if not userMatchInfo:
        # 此处有异常，正常要有userMatchInfo
        userMatchInfo = UserMatchInfo(gameId, userId, bigRoomId)
        userMatchInfo.ctrlRoomId = ctrlRoomId
        userMatchInfo.instId = instId
        userMatchInfo.state = UserMatchInfo.ST_SIGNIN

    userMatchInfo.ctrlRoomId = ctrlRoomId
    userMatchInfo.state = UserMatchInfo.ST_PLAYING

    saveUserMatchInfo(userMatchInfo)

    onlinedata.setBigRoomOnlineLoc(userId, ctrlRoomId, tableId, seatId)

    ftlog.info('match_remote.lockUserForMatch ok gameId=', gameId,
               'userId=', userId,
               'bigRoomId=', bigRoomId,
               'instId=', instId,
               'ctrlRoomId=', ctrlRoomId,
               'tableId=', tableId,
               'seatId=', seatId)
    return True


# @markRpcCall(groupName='userId', lockName='userId', syncCall=1)
def unlockUserForMatch(gameId, userId, bigRoomId, instId, ctrlRoomId, tableId, seatId, contentItem):
    if ftlog.is_debug():
        ftlog.debug('match_remote.unlockUserForMatch gameId=', gameId,
                    'userId=', userId,
                    'bigRoomId=', bigRoomId,
                    'instId=', instId,
                    'ctrlRoomId=', ctrlRoomId,
                    'tableId=', tableId,
                    'seatId=', seatId,
                    'contentItem=', contentItem)

    userMatchInfo = loadUserMatchInfo(gameId, userId, bigRoomId)
    if userMatchInfo:
        # 此处有异常，正常要有userMatchInfo
        removeUserMatchInfo(userMatchInfo)

        if contentItem:
            try:
                contentItemObj = TYContentItem.decodeFromDict(contentItem)
                userAssets = hallitem.itemSystem.loadUserAssets(userId)
                assetList = userAssets.sendContentItemList(gameId, [contentItemObj],
                                                           1, True,
                                                           pktimestamp.getCurrentTimestamp(),
                                                           'MATCH_RETURN_FEE', bigRoomId)
                datachangenotify.sendDataChangeNotify(gameId, userId, TYAssetUtils.getChangeDataNames(assetList))
                ftlog.info('match_remote.unlockUserForMatch returnFees ok gameId=', gameId,
                           'userId=', userId,
                           'bigRoomId=', bigRoomId,
                           'instId=', instId,
                           'ctrlRoomId=', ctrlRoomId,
                           'tableId=', tableId,
                           'seatId=', seatId,
                           'contentItem=', contentItem)
            except:
                ftlog.error('match_remote.unlockUserForMatch gameId=', gameId,
                            'userId=', userId,
                            'bigRoomId=', bigRoomId,
                            'instId=', instId,
                            'ctrlRoomId=', ctrlRoomId,
                            'tableId=', tableId,
                            'seatId=', seatId,
                            'contentItem=', contentItem)
        try:
            onlinedata.removeOnlineLoc(userId, ctrlRoomId, tableId)
        except:
            ftlog.error('match_remote.unlockUserForMatch gameId=', gameId,
                        'userId=', userId,
                        'bigRoomId=', bigRoomId,
                        'instId=', instId,
                        'ctrlRoomId=', ctrlRoomId,
                        'tableId=', tableId,
                        'seatId=', seatId,
                        'contentItem=', contentItem)

        ftlog.info('match_remote.unlockUserForMatch ok gameId=', gameId,
                   'userId=', userId,
                   'bigRoomId=', bigRoomId,
                   'instId=', instId,
                   'ctrlRoomId=', ctrlRoomId,
                   'tableId=', tableId,
                   'seatId=', seatId,
                   'contentItem=', contentItem)
