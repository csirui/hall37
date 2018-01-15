# coding=UTF-8
'''百人房间类
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>'
]

from freetime.core.lock import locked
from freetime.util import log as ftlog
from freetime.util.log import catchedmethod, getMethodName
from poker.entity.configure import gdata
from poker.entity.game.rooms.normal_room import TYNormalRoom
from poker.entity.game.rooms.room import TYRoom


class TYHundredsRoom(TYNormalRoom):
    '''百人房间类'''

    def __init__(self, roomdefine):
        super(TYHundredsRoom, self).__init__(roomdefine)

        serverType = gdata.serverType()
        if serverType == gdata.SRV_TYPE_ROOM:
            self.initData()

    def initData(self):
        self.isActive = set([self.roomDefine.shadowRoomIds[0]])  # 记录各GT房间是否激活
        self.userCountTotal = 0  # 各GT房间总人数
        self.roomUsers = {}  # 记录各GT房间名单
        for rid in self.roomDefine.shadowRoomIds:
            self.roomUsers[rid] = set()
        if ftlog.is_debug():
            ftlog.debug("|roomId, self.roomUsers:", self.roomId, self.roomUsers, caller=self)

    @catchedmethod
    @locked
    def doQuickStart(self, msg):
        '''
        Note:
            1> 每个房间一张桌子
            2> 房间分为激活和非激活状态
            3> 选择激活房间中人数最少的
        '''
        assert self.roomId == msg.getParam("roomId")

        userId = msg.getParam("userId")
        shadowRoomId = msg.getParam("shadowRoomId")
        tableId = msg.getParam("tableId")
        clientId = msg.getParam("clientId")
        ftlog.hinfo("doQuickStart <<", "|userId, clientId, roomId, shadowRoomId, tableId:", userId, clientId,
                    self.roomId, shadowRoomId, tableId, caller=self)

        if tableId == 0:  # 选择激活房间中人数最少的
            shadowRoomId = self.roomDefine.shadowRoomIds[0]
            for rid in self.roomDefine.shadowRoomIds[1:]:
                if rid in self.isActive and \
                                len(self.roomUsers[rid]) < len(self.roomUsers[shadowRoomId]):
                    shadowRoomId = rid
                    break
            tableId = shadowRoomId * 10000 + 1

        if not tableId:
            ftlog.error(getMethodName(), "getFreeTableId timeout", "|userId, roomId, tableId:", userId, self.roomId,
                        tableId)
            return

        if ftlog.is_debug():
            ftlog.info("after choose table", "|userId, shadowRoomId, tableId:", userId, shadowRoomId, tableId,
                       caller=self)

        self.doEnter(userId)
        self.roomUsers[shadowRoomId].add(userId)
        self.userCountTotal += 1
        if ftlog.is_debug():
            ftlog.debug("|shadowRoomId, userId, self.roomUsers[shadowRoomId]",
                        shadowRoomId, userId, self.roomUsers[shadowRoomId],
                        "|self.userCountTotal:", self.userCountTotal, caller=self)

        # 增加active room
        if self.roomConf["openTableRatio"] * self.tableConf["maxSeatN"] * len(self.isActive) <= self.userCountTotal:
            if ftlog.is_debug():
                ftlog.debug("|userId, self.roomDefine.shadowRoomIds[1:]:", userId, self.roomDefine.shadowRoomIds[1:],
                            caller=self)
            for rid in self.roomDefine.shadowRoomIds[1:]:
                if rid not in self.isActive:
                    self.isActive.add(rid)
                    if ftlog.is_debug():
                        ftlog.debug("add active room |shadowRoomId, userId, self.roomUsers[shadowRoomId]",
                                    shadowRoomId, userId, self.roomUsers[shadowRoomId],
                                    "|self.userCountTotal, self.isActive:", self.userCountTotal, self.isActive,
                                    caller=self)
                    break

        extParams = msg.getKey('params')
        self.sendSitReq(userId, shadowRoomId, tableId, clientId, extParams)

    def _enter(self, userId):
        if ftlog.is_debug():
            ftlog.debug("<< |roomId, userId:", self.roomId, userId, caller=self)

        # PlayerRoomDao.clear(userId, self.bigRoomId)

        return True, TYRoom.ENTER_ROOM_REASON_OK

    def _leave(self, userId, reason, needSendRes):
        ftlog.hinfo("_leave << |roomId, userId, reason:", self.roomId, userId, reason, caller=self)

        if reason == TYRoom.LEAVE_ROOM_REASON_LOST_CONNECTION:
            return False

        if not self._remoteTableLeave(userId, reason):
            return False

        for shadowRoomId in self.roomUsers:
            if userId in self.roomUsers[shadowRoomId]:
                break

        if userId in self.roomUsers[shadowRoomId]:
            self.roomUsers[shadowRoomId].remove(userId)
            self.userCountTotal -= 1

            if ftlog.is_debug():
                ftlog.debug("|shadowRoomId, userId, self.roomUsers[shadowRoomId]",
                            shadowRoomId, userId, self.roomUsers[shadowRoomId],
                            "|self.userCountTotal, self.isActive:",
                            self.userCountTotal, self.isActive, caller=self)

            # 关闭active room
            if len(self.isActive) > 1 and \
                                            self.roomConf["closeTableRatio"] * self.tableConf["maxSeatN"] * (
                                        len(self.isActive) - 1) > self.userCountTotal:
                minUserRoomId = 0
                for rid in self.roomDefine.shadowRoomIds[1:]:
                    if rid in self.isActive:
                        if not minUserRoomId or len(self.roomUsers[rid]) < len(self.roomUsers[minUserRoomId]):
                            minUserRoomId = rid

                self.isActive.remove(minUserRoomId)

                if ftlog.is_debug():
                    ftlog.debug("remove active room |minUserRoomId, userId, self.roomUsers[minUserRoomId]",
                                minUserRoomId, userId, self.roomUsers[minUserRoomId],
                                "|self.userCountTotal, self.isActive:", self.userCountTotal, self.isActive,
                                caller=self)

        # PlayerRoomDao.clear(userId, self.bigRoomId)

        return True
