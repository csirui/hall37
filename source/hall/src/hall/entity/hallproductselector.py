# -*- coding=utf-8
'''
Created on 2015年8月14日

@author: zhaojiangang
'''

import freetime.util.log as ftlog
from hall.entity import hallconf, hallstore
from poker.entity.configure import gdata


# 选择转运礼包商品
def selectZhuanyunProduct(gameId, userId, clientId, roomId):
    return selectProcutByRoomId(gameId, userId, clientId, roomId, 'zhuanyun')


# 选择充值引导商品
def selectWinleadProduct(gameId, userId, clientId, roomId):
    return selectProcutByRoomId(gameId, userId, clientId, roomId, 'winlead')


# 选择金币不足引导商品
def selectLessbuyProduct(gameId, userId, clientId, roomId):
    return selectProcutByRoomId(gameId, userId, clientId, roomId, 'lessbuychip')


# 选择桌面快充商品
def selectTableBuyProduct(gameId, userId, clientId, roomId):
    return selectProcutByRoomId(gameId, userId, clientId, roomId, 'tablebuy')


def selectProcutByRoomId(gameId, userId, clientId, roomId, action):
    levelName = hallconf.getRoomLevelName(gameId, gdata.getBigRoomId(roomId))
    return selectProduct(gameId, userId, clientId, levelName, action)


def selectProduct(gameId, userId, clientId, templateName, action):
    template = hallconf.getChargeLeadTemplate(templateName)
    if not template:
        return None, None

    payOrder = template.get(action)
    if not payOrder:
        if ftlog.is_debug():
            ftlog.debug('hallproductselector.selectProduct gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'templateName=', templateName,
                        'template=', template,
                        'action=', action,
                        'err=', 'EmptyPayOrder')
        return None, None

    if ftlog.is_debug():
        ftlog.debug('hallproductselector.selectProduct gameId=', gameId,
                    'userId=', userId,
                    'clientId=', clientId,
                    'templateName=', templateName,
                    'template=', template,
                    'action=', action,
                    'payOrder=', payOrder)

    return hallstore.findProductByPayOrder(gameId, userId, clientId, payOrder)
