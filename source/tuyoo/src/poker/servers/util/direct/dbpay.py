# -*- coding=utf-8 -*-

'''
Created on 2013-3-18

@author: Administrator
'''

import json

from datetime import datetime

import freetime.util.log as ftlog
from poker.entity.dao import daobase, daoconst
from poker.entity.dao.daoconst import GameOrderSchema


def _getExchangeRecords(gameId, userId):
    records = []
    datas = daobase._executePayDataCmd('HGETALL', daoconst.PAY_KEY_CTY % (gameId, userId))
    if datas:
        for i in xrange(len(datas) / 2):
            try:
                jstr = datas[i * 2 + 1]
                record = json.loads(jstr)
                dt = datetime.strptime(record['rtime'], '%Y%m%d%H%M%S')
                record['rtime'] = dt.strftime('%Y-%m-%d %H:%M')
                records.append(record)
            except:
                ftlog.error()
    return records


def _makeExchangeId():
    exchangeId = daobase._executePayDataCmd('INCR', daoconst.PAY_KEY_EXCHANGE_ID)
    ct = datetime.now()
    exchangeId = 'EO%s%s' % (ct.strftime('%Y%m%d%H%M%S'), exchangeId)
    return exchangeId


def _makeGameOrderId(gameId, userId, productId):
    orderId = daobase._executePayDataCmd('INCR', daoconst.PAY_KEY_GAME_ORDER_ID)
    ct = datetime.now()
    orderId = 'GO%s%s' % (ct.strftime('%Y%m%d%H%M%S'), orderId)
    return orderId


def _setGameOrderInfo(userId, orderId, datas):
    params = GameOrderSchema.paramsDict2List(datas)
    return daobase._executePayDataCmd('HMSET', GameOrderSchema.mkey(orderId), *params)


def _getGameOrderInfo(orderId):
    values = daobase._executePayDataCmd('HMGET', GameOrderSchema.mkey(orderId), *GameOrderSchema.FIELDS_ALL)
    return GameOrderSchema.checkDataDict(GameOrderSchema.FIELDS_ALL, values)
