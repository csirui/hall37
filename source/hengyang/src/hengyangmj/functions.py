# -*- coding=utf-8
'''
Created on 2017年3月2日

@author: nick.kai.lee
'''
from difang.majiang2.utils.timeUtils import timeUtils as TIMEUTILS

from difang.majiang2.entity.util import sendPopTipMsg as SENDPOPTIPMSG
from freetime.util import log as FTLOG


class Functions(object):
    CONST_TAG = "[Functions]: "  # 对象标记

    @classmethod
    def checkRoomFangKaFree(cls, userId, room):
        itemId = room.roomConf.get('create_item', None)
        freePlayConfig = room.roomConf.get('freePlay', None)
        FTLOG.info(cls.CONST_TAG, "checkRoomFangKaRequire freePlayConfig: ", freePlayConfig)

        if not itemId:
            SENDPOPTIPMSG(userId, "未知房卡")

        # 读免费时段配置,确定是否要收房卡
        isFree = False
        if freePlayConfig and isinstance(freePlayConfig, list):
            for config in freePlayConfig:
                if isinstance(config, list) and len(config) == 2:
                    if TIMEUTILS.isInTimeIntervalEveryDay(config[0], config[1]):
                        isFree = True
                        break
        return isFree
