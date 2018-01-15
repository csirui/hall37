# -*- coding=utf-8
'''
Created on 2015年10月15日

@author: zhaojiangang
'''

import struct

from datetime import datetime

import freetime.util.log as ftlog
import poker.entity.dao.gamedata as pkgamedata
import poker.util.timestamp as pktimestamp
from hall.entity import hallitem
from hall.entity.hallconf import HALL_GAMEID
from hall.entity.hallitem import __timingItems, itemSystem
from poker.util import strutil


def transItemIfNeed(userId):
    userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
    transFlag = pkgamedata.getGameAttr(userId, HALL_GAMEID, 'flag.item.trans')

    # 如果还没转换过的不需要处理
    if not transFlag:
        ftlog.info('hotfix_item_add.transItemIfNeed NotTrans1 userId=', userId, 'transFlag=', transFlag)
        return

    try:
        datas = pkgamedata.getAllAttrs(userId, HALL_GAMEID, 'item')

        ftlog.info('hotfixitem.transItemIfNeed userId=', userId,
                   'datas=', None if datas is None else [v for i, v in enumerate(datas) if i % 2 == 0])

        # 读取用户所有老的道具，和新背包中的道具比较，如果新背包中没有则把老的加到新背包中
        if datas:
            for i in xrange(len(datas) / 2):
                try:
                    x = i * 2
                    # fid,  utime 更新时间 count道具个数 state 状态
                    dataBytes = strutil.unicode2Ascii(datas[x + 1])
                    _fid, utime, count, _state = struct.unpack("3iB", dataBytes)

                    timestamp = pktimestamp.getCurrentTimestamp()
                    kindId = int(datas[x])
                    if kindId == 0:
                        continue

                    if kindId in __timingItems:
                        now_day = datetime.now().date()
                        uday = datetime.fromtimestamp(utime).date()
                        count -= (now_day - uday).days
                        if count <= 0:
                            ftlog.info('hotfix_item_add.transItemIfNeed expires userId=', userId,
                                       'kindId=', kindId,
                                       'count=', count,
                                       'utime=', datetime.fromtimestamp(utime).strftime('%Y-%m-%d %H:%M:%S'))
                            continue

                    itemKind = itemSystem.findItemKind(kindId)
                    if not itemKind:
                        ftlog.warn('hotfix_item_add.transItemIfNeed unknownKind userId=', userId,
                                   'kindId=', kindId,
                                   'count=', count,
                                   'utime=', datetime.fromtimestamp(utime).strftime('%Y-%m-%d %H:%M:%S'))
                        continue

                    # 在背包中查找是否有老的道具，如果没有则加到背包中、
                    item = userBag.getItemByKind(itemKind)
                    alreadyCount = item.balance(timestamp) if item else 0
                    ftlog.info('hotfix_item_add.transItemIfNeed transOk userId=', userId,
                               'kindId=', kindId,
                               'count=', count,
                               'alreadyCount=', alreadyCount,
                               'utime=', datetime.fromtimestamp(utime).strftime('%Y-%m-%d %H:%M:%S'))

                    userBag.addItemUnitsByKind(HALL_GAMEID, itemKind, count, timestamp,
                                               0, "DATA_TRANSFER", 0)
                except:
                    ftlog.error('hotfix_item_add.transItemIfNeed exception0 userId=', userId)
    except:
        ftlog.error('hotfix_item_add.transItemIfNeed exception1 userId=', userId)


uids = [126059804]
for uid in uids:
    ftlog.info('hot fix items add, ', uid)
    if uid:
        transItemIfNeed(uid)
