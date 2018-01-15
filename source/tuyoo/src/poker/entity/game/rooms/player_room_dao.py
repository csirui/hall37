# coding=UTF-8
'''
'''

import json

import freetime.util.log as ftlog
from poker.entity.dao import tabledata

__author__ = ['Zhou Hao']


class PlayerRoomDao(object):
    '''存取玩家在同一房间连续玩的局数；
       key: playerRoomRound:[bigRoomId]
       value: int值
       存取玩家在同一房间换桌时需要保留的信息，例如：
       key: playerRoomRecord:[bigRoomId]
       value: {tableChips: 离开上一桌时，玩家的筹码;
               timeoutCount: 连续超时弃牌的次数
               isManaged: 是否托管
                "buyinDelta": 0,  # 在开局时要补充这么多筹码(暂时只有 mtt addon/rebuy 使用)
                "buyinTo": 0,  # 在开局时要补充到这么多筹码
                "rebuyType": "",  # 补充筹码类型。详细见定义
                "isRoomNewUser": True,  # 是否刚进入房间未参与游戏
              }
    '''

    @classmethod
    def clear(cls, userId, bigRoomId):
        '''删除redis里的数据，节省redis空间'''
        attrlist = [cls._getPlayerRoomRecordKey(userId), cls._getPlayerRoomRoundKey(userId)]

        values = tabledata.getTableAttrs(bigRoomId, 0, attrlist)
        if ftlog.is_debug():
            ftlog.debug("|values:", values, caller=cls)

        ret = tabledata.delTableAttrs(bigRoomId, 0, attrlist)
        if ftlog.is_debug():
            ftlog.debug("|ret:", ret, caller=cls)

        values = tabledata.getTableAttrs(bigRoomId, 0, attrlist)
        if ftlog.is_debug():
            ftlog.debug("|values:", values, caller=cls)

    @classmethod
    def _getPlayerRoomRecordKey(cls, userId):
        return "playerRoomRecord:%s" % (userId)

    @classmethod
    def _getPlayerRoomRoundKey(cls, userId):
        return "playerRoomRound:%s" % (userId)

    @classmethod
    def getPlayerRoomRecord(cls, userId, bigRoomId):
        recordDict = tabledata.getTableAttr(bigRoomId, 0, cls._getPlayerRoomRecordKey(userId))
        if ftlog.is_debug():
            ftlog.debug("userId, roomId, db_recordDict:", userId, bigRoomId, recordDict)
        if recordDict == None:
            recordDict = {
                "tableChips": 0,
                "timeoutCount": 0,
                "isManaged": False,
                "buyinDelta": 0,  # 在开局时要补充这么多筹码(暂时只有 mtt addon/rebuy 使用)
                "buyinTo": 0,  # 在开局时要补充到这么多筹码
                "rebuyType": "",  # 补充筹码类型。详细见定义
                "isRoomNewUser": True,  # 是否刚进入房间未参与游戏
            }
        else:
            recordDict = json.loads(recordDict)
        if ftlog.is_debug():
            ftlog.debug("userId, roomId, ret_recordDict:", userId, bigRoomId, recordDict)
        return recordDict

    @classmethod
    def setPlayerRoomRecord(cls, userId, bigRoomId, recordDict):
        if ftlog.is_debug():
            ftlog.debug("userId, roomId, recordDict:", userId, bigRoomId, recordDict)
        tabledata.setTableAttr(bigRoomId, 0, cls._getPlayerRoomRecordKey(userId), json.dumps(recordDict))

    @classmethod
    def getPlayerRound(cls, userId, bigRoomId):
        return tabledata.getTableAttr(bigRoomId, 0, cls._getPlayerRoomRoundKey(userId))

    @classmethod
    def incrPlayerRound(cls, userId, bigRoomId):
        tabledata.incrTableAttr(bigRoomId, 0, cls._getPlayerRoomRoundKey(userId), 1)
