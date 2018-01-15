# coding=UTF-8
'''普通房间类
'''
from poker.util import strutil

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import json

import freetime.util.log as ftlog

from poker.entity.game.rooms.room import TYRoom
from poker.entity.dao import onlinedata


class TYCustomRoom(TYRoom):
    '''自建房间类'''

    def __init__(self, roomDefine):
        super(TYCustomRoom, self).__init__(roomDefine)
        self._initIdleTableIds()

    def _initIdleTableIds(self):
        self.idleTableIds = []
        shadowRoomIds = self.roomDefine.shadowRoomIds
        if ftlog.is_debug():
            ftlog.debug("<<", '|shadowRoomIds=', list(shadowRoomIds), caller=self)
        for shadowRoomId in shadowRoomIds:
            for i in xrange(self.roomDefine.configure['gameTableCount']):
                self.idleTableIds.append(shadowRoomId * 10000 + i + 1)
        # shuffle(self.idleTableIds)
        if ftlog.is_debug():
            ftlog.debug(">>", '|len(shadowRoomIds), len(idleTableIds):',
                        len(shadowRoomIds), len(self.idleTableIds), caller=self)

    def getIdleTableId(self):
        try:
            idleTableId = self.idleTableIds.pop()
            if ftlog.is_debug():
                ftlog.debug(">>", '|idleTableId, len(idleTableIds):', idleTableId, len(self.idleTableIds), caller=self)

            return idleTableId
        except:
            return 0

    def _recycleTable(self, idleTableId):
        try:
            shadowRoomId = idleTableId / 10000
            resultStr = self.queryTableManageClearPlayersReq(shadowRoomId, idleTableId)
            if resultStr:
                result = json.loads(resultStr)
                if ftlog.is_debug():
                    ftlog.debug("|result:", result, caller=self)
            self.idleTableIds.append(idleTableId)
            if ftlog.is_debug():
                ftlog.debug(">>", '|idleTableId, len(idleTableIds):', idleTableId, len(self.idleTableIds), caller=self)
        except Exception, e:
            ftlog.error(e)

    def doAdjustTablePlayers(self, msg):
        tableId = msg.getParam("tableId")
        self._recycleTable(tableId)

    def _leave(self, userId, reason, needSendRes):
        ftlog.hinfo("_leave << |roomId, userId, reason: ", self.roomId, userId, reason,
                    caller=self)

        self._remoteTableLeave(userId, reason)

        locList = onlinedata.getOnlineLocList(userId)
        if ftlog.is_debug():
            ftlog.debug("<< |roomId, userId: ", self.roomId, userId,
                        "|locList:", locList, caller=self)

        for loc in locList:
            onlineRoomId, onlineTableId = loc[0], loc[1]
            if strutil.getBigRoomIdFromInstanceRoomId(onlineRoomId) == self.bigRoomId:
                return False

        return True
