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
        ftlog.info('hotfix_item.transItemIfNeed NotTrans1 userId=', userId, 'transFlag=', transFlag)
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
                            ftlog.info('hotfix_item.transItemIfNeed expires userId=', userId,
                                       'kindId=', kindId,
                                       'count=', count,
                                       'utime=', datetime.fromtimestamp(utime).strftime('%Y-%m-%d %H:%M:%S'))
                            continue

                    itemKind = itemSystem.findItemKind(kindId)
                    if not itemKind:
                        ftlog.warn('hotfix_item.transItemIfNeed unknownKind userId=', userId,
                                   'kindId=', kindId,
                                   'count=', count,
                                   'utime=', datetime.fromtimestamp(utime).strftime('%Y-%m-%d %H:%M:%S'))
                        continue

                    # 在背包中查找是否有老的道具，如果没有则加到背包中、
                    item = userBag.getItemByKind(itemKind)
                    if not item and count > 0:
                        ftlog.info('hotfix_item.transItemIfNeed transOk userId=', userId,
                                   'kindId=', kindId,
                                   'count=', count,
                                   'utime=', datetime.fromtimestamp(utime).strftime('%Y-%m-%d %H:%M:%S'))

                        userBag.addItemUnitsByKind(HALL_GAMEID, itemKind, count, timestamp,
                                                   0, "DATA_TRANSFER", 0)
                    else:
                        ftlog.info('hotfix_item.transItemIfNeed alreadyExists userId=', userId,
                                   'kindId=', kindId,
                                   'count=', count,
                                   'utime=', datetime.fromtimestamp(utime).strftime('%Y-%m-%d %H:%M:%S'))
                except:
                    ftlog.error('hotfix_item.transItemIfNeed exception0 userId=', userId)
    except:
        ftlog.error('hotfix_item.transItemIfNeed exception1 userId=', userId)


uids = set([128624976, 127999345, 60257453, 119488069, 127999345,
            47403141, 128624976, 120835243, 132319498, 91929925,
            38204340, 123073136, 118278654, 114516500, 120835243,
            107161879, 41072640, 123073136, 60257453, 76576577,
            37956683, 74950829, 120975231, 74141957, 119488069,
            84585847, 94460638, 97743992, 124128590, 132533044,
            67934545, 126059804, 122504891, 88021331, 122504891,
            136742413, 136155131, 136742413, 120806733, 112033416,
            111111060, 57815906, 110700101, 61413049, 128522671,
            74276187, 91705643, 25073099, 132319498, 124128590,
            122483994, 27558384, 135975575, 55039002, 134962825,
            123491992, 118072717, 123441736, 97743992, 38204340, 12691272, 13108045,
            25073099, 79166253, 84372535, 85006101, 4137169, 134649557, 122462141, 126080074,
            80363121, 82396448, 77842036])
uids = [27558384]
uids = [131043789, 126059804, 97743992, 27558384]
uids = [117013533, 64444512]
for uid in uids:
    ftlog.info('hot fix items, ', uid)
    if uid:
        transItemIfNeed(uid)
