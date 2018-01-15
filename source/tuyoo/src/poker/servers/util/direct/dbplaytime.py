# -*- coding=utf-8
from time import time

from datetime import datetime, timedelta

import freetime.util.log as ftlog
from poker.entity.dao import daobase
from poker.entity.dao.daoconst import UserPlayTimeSchema
from poker.util import strutil


def _cleanalltime(userId):
    daobase.sendUserCmd(userId, 'DEL', UserPlayTimeSchema.mkey(userId))


def _setPlayTimeStart(userId, roomId, tableId):
    daobase.sendUserCmd(userId, 'HSET', UserPlayTimeSchema.mkey(userId), 'R.' + str(roomId) + '.' + str(tableId),
                        int(time()))
    daobase.sendUserCmd(userId, 'EXPIRE', UserPlayTimeSchema.mkey(userId), 86400)


def _setPlayTimeStop(userId, roomId, tableId):
    ptkey = UserPlayTimeSchema.mkey(userId)
    subkey = 'R.' + str(roomId) + '.' + str(tableId)
    st = daobase.executeUserCmd(userId, 'HGET', ptkey, subkey)
    if isinstance(st, int):
        dt = int(time()) - st
        if dt > 10 and dt < 86400:  # 如何判定loc的时间变化是一个有效值? 桌子上最少待10秒, 最大不可能超过1天
            # 增加游戏时间
            _writePlayTime_(userId, dt)
        daobase.sendUserCmd(userId, 'HDEL', ptkey, subkey)
        daobase.sendUserCmd(userId, 'EXPIRE', ptkey, 86400)


def _incrPlayTime(userId, detalTime, gameId, roomId=-1, tableId=-1):
    if roomId < 0 or tableId < 0:
        _writePlayTime_(userId, detalTime)
    else:
        ptkey = UserPlayTimeSchema.mkey(userId)
        subkey = 'R.' + str(roomId) + '.' + str(tableId)
        st = daobase.executeUserCmd(userId, 'HGET', ptkey, subkey)
        if isinstance(st, int):
            dt = int(time()) - st
            if dt > 2 and dt < 86400:  # 如何判定loc的时间变化是一个有效值? 桌子上最少待2秒, 最大不可能超过1天
                # 增加游戏时间
                _writePlayTime_(userId, detalTime)


def _writePlayTime_(userId, detalTime):
    try:
        mkey = 'gamedata:9999:%d' % (userId)
        daobase.sendUserCmd(userId, 'HINCRBY', mkey, 'totaltime', detalTime)

        datas = daobase.executeUserCmd(userId, 'HGET', mkey, 'todaytime')
        datas = strutil.loads(datas, ignoreException=True, execptionValue={})
        today = datetime.now().strftime('%Y%m%d')[-6:]
        if today in datas:
            datas[today] += detalTime
        else:
            datas[today] = detalTime

        oldday = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')[-6:]
        for k in datas.keys()[:]:
            if k < oldday:
                del datas[k]
        daobase.sendUserCmd(userId, 'HSET', mkey, 'todaytime', strutil.dumps(datas))
    except:
        ftlog.error()
