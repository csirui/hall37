# -*- coding=utf-8 -*-

'''
Created on 2013-3-18

@author: Administrator
'''
import freetime.util.log as ftlog
from freetime.core.timer import FTLoopTimer
from freetime.entity import config
from freetime.util.txredis import subscribe
from poker.entity.configure import gdata
from poker.entity.dao import userdata


def _initialize():
    return  # 当前没有做数据缓存，无需数据变化通知

    if gdata.serverType() != gdata.SRV_TYPE_UTIL:
        return

    channelcount = 16
    channels = []
    usids = gdata.serverTypeMap()[gdata.SRV_TYPE_UTIL]
    usids.sort()
    if len(usids) < channelcount:
        if usids[0] == gdata.serverId():
            for x in xrange(channelcount):
                channels.append('userdatachange_%d' % (x))
    else:
        if gdata.serverId() in usids:
            i = usids.index(gdata.serverId())
            if i < channelcount:
                channels.append('userdatachange_%d' % (i))

    if channels:
        conf = config.redis_config_map.get('mix')
        ip, port = conf[0], conf[1]
        subscribe.startSubScriber(ip, port, channels, _onSubMessage)


def _userdatachange(userId):
    ftlog.debug('_userdatachange->', userId)
    userdata.clearUserCache(int(userId))


def _onSubMessage(channel, message):
    FTLoopTimer(0.01, 0, _userdatachange, message).start()
