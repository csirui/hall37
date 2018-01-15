# -*- coding=utf-8
'''
Created on 2015年10月15日

@author: zhaojiangang
'''
import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from hall.entity import hallitem
from hall.servers.util import old_remote_call_new_handler
from poker.entity.biz.item.exceptions import TYItemException


def consumeUserItem(userId, gameId, kindId, count, eventId, userBag):
    timestamp = pktimestamp.getCurrentTimestamp()
    itemKind = hallitem.itemSystem.findItemKind(kindId)
    if not itemKind:
        ftlog.warn('TYOldItemTransfer.consumeUserItem gameId=', gameId, 'userId=', userId, 'itemKindId=', kindId,
                   'err=', 'UnknownItemKindId')
        raise TYItemException(-1, '未知的道具类型')
    count = userBag.consumeUnitsCountByKind(gameId, itemKind, count, timestamp, eventId, 0)
    item = userBag.getItemByKindId(kindId)
    balance = userBag.calcTotalUnitsCount(itemKind)
    val = {
        "cCount": count,
        "itemId": kindId,
        "count": balance,
        "startTime": item.createTime if item else 0
    }

    return val


old_remote_call_new_handler.consumeUserItem1 = old_remote_call_new_handler.consumeUserItem
old_remote_call_new_handler.consumeUserItem = consumeUserItem
