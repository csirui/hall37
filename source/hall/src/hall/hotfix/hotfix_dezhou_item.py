# -*- coding=utf-8
'''
Created on 2015年10月15日

@author: zhaojiangang
'''
import struct

import freetime.util.log as ftlog
import poker.entity.dao.gamedata as pkgamedata
import poker.util.timestamp as pktimestamp
from hall.entity import hallitem
from poker.util import strutil

HOT_ITEM_IDS = set([1029, 1030, 1031, 1032, 1033, 1034, 1035])


def _tranformItems(userId):
    userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
    try:
        datas = pkgamedata.getAllAttrs(userId, 9999, 'item')

        ftlog.info('hallitem._tranformItems gameId=', 9999,
                   'userId=', userId,
                   'datas=', datas)

        if datas:
            for i in xrange(len(datas) / 2):
                x = i * 2
                # fid,  utime 更新时间 count道具个数 state 状态
                dataBytes = strutil.unicode2Ascii(datas[x + 1])
                _fid, _utime, count, _state = struct.unpack("3iB", dataBytes)

                timestamp = pktimestamp.getCurrentTimestamp()
                kindId = int(datas[x])
                if kindId not in HOT_ITEM_IDS:
                    continue

                itemKind = hallitem.itemSystem.findItemKind(kindId)
                if not itemKind:
                    ftlog.warn('TYOldItemTransfer.transform gameId=', 9999,
                               'userId=', userId,
                               'itemKindId=', kindId,
                               'err=', 'UnknownItemKindId')
                    continue

                item = userBag.getItemByKindId(kindId)
                ftlog.info('hot fix userId=', userId, count, kindId, item)
                if count > 0 and not item:
                    userBag.addItemUnitsByKind(9999, itemKind, count, timestamp,
                                               0, "DATA_TRANSFER", 0)
    except:
        ftlog.error('hallitem._tranformItems gameId=', 9999,
                    'userId=', userId)


for uid in open('/tmp/texas_login_uids'):
    uid = uid.strip()
    ftlog.info('hot fix texas items, ', uid)
    if uid:
        _tranformItems(int(uid))
