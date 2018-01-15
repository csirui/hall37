# -*- coding=utf-8 -*-
'''
Created on 2016年12月06日

@author: zhaol
'''
from difang.majiang2.entity.item import MajiangItem
from freetime.util import log as ftlog
from poker.entity.dao import onlinedata, sessiondata
from poker.protocol.rpccore import markRpcCall
from poker.util import strutil


@markRpcCall(groupName="userId", lockName="userId", syncCall=1)
def consumeItem(userId, gameId, itemId, count, roomId):
    """消费房卡，加锁操作"""
    user_fangka_count = MajiangItem.getUserItemCountByKindId(userId, itemId)
    if user_fangka_count >= count:
        consumeResult = MajiangItem.consumeItemByKindId(userId
                                                        , gameId
                                                        , itemId
                                                        , count
                                                        , 'MAJIANG_FANGKA_CONSUME'
                                                        , roomId)
        return consumeResult
    return False


@markRpcCall(groupName="userId", lockName="userId", syncCall=1)
def resumeItemFromRoom(userId, gameId, itemId, count, roomId):
    """退还房卡，加锁操作"""
    MajiangItem.addUserItemByKindId(userId
                                    , gameId
                                    , itemId
                                    , count
                                    , 'MAJIANG_FANGKA_RETURN_BACK'
                                    , roomId)


@markRpcCall(groupName="userId", lockName="userId", syncCall=1)
def resumeItemFromTable(userId, gameId, itemId, count, roomId, tableId):
    """退还房卡，加锁操作"""
    ftlog.debug('user_remote resumeItemFromTable userId:', userId
                , ' gameId:', gameId
                , ' itemId:', itemId
                , ' count:', count
                , ' roomId:', roomId
                , ' tableId:', tableId
                )

    clientId = sessiondata.getClientId(userId)
    loc = onlinedata.checkUserLoc(userId, clientId, gameId)
    ftlog.debug('user_remote resumeItemFromTable loc:', loc)

    lgameId, lroomId, ltableId, lseatId = loc.split('.')
    lgameId, lroomId, ltableId, lseatId = strutil.parseInts(lgameId, lroomId, ltableId, lseatId)
    if (lroomId != roomId) or (ltableId != tableId):
        ftlog.info('user_remote resumeItemFromTable loc not match, do not resume item. userId:', userId
                   , ' gameId:', gameId
                   , ' itemId:', itemId
                   , ' count:', count
                   , ' roomId:', roomId
                   , ' tableId:', tableId
                   , ' loc:', loc)
        return

    MajiangItem.addUserItemByKindId(userId
                                    , gameId
                                    , itemId
                                    , count
                                    , 'MAJIANG_FANGKA_RETURN_BACK'
                                    , roomId)
