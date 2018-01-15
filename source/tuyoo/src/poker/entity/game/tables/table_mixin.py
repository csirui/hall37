# coding=UTF-8
'''
'''

__author__ = [
    'Zhaoqh'
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import freetime.util.log as ftlog

from poker.entity.dao import onlinedata, sessiondata
from poker.entity.game.rooms.room import TYRoom
from poker.entity.game.tables.table_timer import TYTableTimer


class TYTableMixin(object):
    def _baseLogStr(self, des="", userId=None):
        if ftlog.is_debug():
            baseTableInfo = '%s |tableId, playersNum: %d, %d' % (des, self.tableId, self.playersNum)
        else:
            baseTableInfo = '%s |tableId: %d' % (des, self.tableId)
        baseUserInfo = '' if not userId else ' |userId: %d' % (userId)

        return self.__class__.__name__ + " " + baseTableInfo + baseUserInfo

    def getValidIdleSeatId(self, userId, seatIndex, result):
        '''通用坐下合法性检查函数
        
        Returns
            idleSeatId：
                >0   ：  为新玩家找到合适座位，需要继续处理
                <0   :   断线重连
                0    ：  坐下失败
         '''

        clientId = sessiondata.getClientId(userId)
        onlineSeatId = onlinedata.getOnlineLocSeatId(userId, self.table.roomId, self.table.tableId)
        if onlineSeatId and onlineSeatId <= self.maxSeatN:  # 断线重连， Note：旁观的人坐下此处不能返回负数，否则无法入座
            ftlog.hinfo('re-sit ok. |userId, tableId, seatId:', userId, self.tableId, onlineSeatId, caller=self)
            result["seatId"] = onlineSeatId
            result["reason"] = TYRoom.ENTER_ROOM_REASON_OK
            self.sendQuickStartRes(userId, clientId, result)
            return -onlineSeatId

        isOk, reason = self._checkSitCondition(userId)
        if not isOk:
            result["isOK"] = False
            result["reason"] = reason
            #             if reason == TYRoom.ENTER_ROOM_REASON_TABLE_FULL and userId in self.observers: #玩家从旁观状态点坐下排队，不下发quick_start
            if reason == TYRoom.ENTER_ROOM_REASON_TABLE_FULL:
                pass
            else:
                self.sendQuickStartRes(userId, clientId, result)
            return 0

        # 按指定座位坐下，如果座位上有人则随机分配座位。
        if seatIndex >= 0 and seatIndex < self.maxSeatN:
            if self.seats[seatIndex].isEmptySeat():
                return seatIndex + 1
            else:
                ftlog.warn("seatIndex >=0 but not self.seats[seatIndex].isEmptySeat()",
                           "|userId, roomId, tableId, seatIndex:", userId, self.table.roomId, self.table.tableId,
                           seatIndex,
                           caller=self)

        idleSeatId = self.findIdleSeat(userId)

        if idleSeatId < 0:
            # 断线重连机制出错了??
            # 已经在座位上坐下, 返回成功消息和桌子信息
            ftlog.warn("idleSeatId < 0",
                       "|userId, roomId, tableId, idleSeatId:", userId, self.table.roomId, self.table.tableId,
                       idleSeatId,
                       caller=self)
            result["seatId"] = abs(idleSeatId)
            result["reason"] = TYRoom.ENTER_ROOM_REASON_OK
            self.sendQuickStartRes(userId, clientId, result)
            return idleSeatId

        if idleSeatId == 0:  # 座位已经满了, 返回失败消息
            ftlog.warn("idleSeatId == 0",
                       "|userId, roomId, tableId, idleSeatId:", userId, self.table.roomId, self.table.tableId,
                       idleSeatId,
                       caller=self)
            result["isOK"] = False
            result["reason"] = TYRoom.ENTER_ROOM_REASON_TABLE_FULL
            if userId not in self.observers:  # 玩家从旁观状态点坐下排队，不下发quick_start
                self.sendQuickStartRes(userId, clientId, result)
            return 0

            # 为了支持并发坐下，findIdleSeat后不应该有异步操作
            # 座位冲突检查
        #         lastUserId = self.table.getLastSeatUserId(idleSeatId)
        #         if lastUserId and lastUserId != userId :
        #             ftlog.error(getMethodName(), 'seat Userid is not clean up !! tid=', self.table.tableId,
        #                         'seatId=', idleSeatId, 'olduid=', lastUserId, 'newuid=', userId)
        #             result["isOK"] = False
        #             result["reason"] = TYRoom.ENTER_ROOM_REASON_INNER_ERROR
        #             self.sendQuickStartRes(userId, clientId, result)
        #             return 0

        return idleSeatId

    def _checkSitCondition(self, userId):
        '''游戏可扩展'''
        return self.room.checkSitCondition(userId)

    def onSitOk(self, userId, idleSeatId, result):
        '''坐下条件成功后的处理
        Return：
            player：新空座位上的player
        '''
        ftlog.hinfo('onSitOk << |userId, tableId, seatId:', userId, self.tableId, idleSeatId,
                    "|observers:", self.observers, caller=self)

        # 设置玩家坐在座位上, 为了支持并发坐下，此设置需要在异步操作前完成！！！
        seat = self.table.seats[idleSeatId - 1]
        seat.userId = userId
        seat.setWaitingState()
        if ftlog.is_debug():
            ftlog.debug("|seats:", self.table.seats, caller=self)

        if userId in self.table.observers:
            del self.table.observers[userId]
            onlinedata.removeOnlineLoc(userId, self.roomId, self.tableId)

        # 设置玩家的在线状态
        if ftlog.is_debug():
            ftlog.debug("before addOnlineLoc. |tableId, onlineSeatId:", self.tableId,
                        onlinedata.getOnlineLocSeatId(userId, self.roomId, self.tableId), caller=self)
        onlinedata.addOnlineLoc(userId, self.roomId, self.tableId, idleSeatId)
        if ftlog.is_debug():
            ftlog.debug("after addOnlineLoc. |tableId, onlineSeatId:", self.tableId,
                        onlinedata.getOnlineLocSeatId(userId, self.roomId, self.tableId), caller=self)

        # 记录当前座位的userId, 以便对玩家的金币做恢复处理
        self.table.recordSeatUserId(idleSeatId, userId)

        result["seatId"] = idleSeatId
        result["reason"] = TYRoom.ENTER_ROOM_REASON_OK

        ftlog.hinfo('onSitOk >> |userId, tableId, seatId:', userId, self.tableId, idleSeatId,
                    "|observers:", self.observers, caller=self)

    def onStandUpOk(self, userId, seatId):
        '''坐下条件成功后的处理
        note: 站起后没有自动进入旁观列表
        '''
        if ftlog.is_debug():
            ftlog.debug('<< |userId, tableId, seatId:', userId, self.tableId, seatId, caller=self)
        # 清理在线信息
        onlinedata.removeOnlineLoc(userId, self.roomId, self.tableId)
        # 清理当前座位的userId
        self.recordSeatUserId(seatId, 0)

        seat = self.table.seats[seatId - 1]
        seat.userId = 0

        # 更新当前桌子的快速开始积分, 如果此时桌子正在分配玩家，刷新将失败
        #         self.room.updateTableScore(self.getTableScore(), self.tableId)

        ftlog.hinfo('onStandUpOk >> |userId, tableId, seatId:', userId, self.tableId, seatId,
                    "|observers:", self.observers, caller=self)

    def getAllUserIds(self):
        return [seat.userId for seat in self.seats if seat and not seat.isEmptySeat()] + self.observers.keys()

    def clearInvalidObservers(self):
        '''一段防御性代码，防止本桌上一局的旁观者未被及时清理，下一局开局时换到了别的桌子，但收到本桌的协议
        '''
        invalidObservers = []
        for userId in self.observers:
            onlineSeatId = onlinedata.getOnlineLocSeatId(userId, self.roomId, self.tableId)
            if onlineSeatId == 0:  # Note: 断线的旁观玩家不做清理，table._doClearPlayers会处理
                ftlog.warn(self._baseLogStr('invalid observer found', userId),
                           '|locList:', onlinedata.getOnlineLocList(userId), caller=self)
                invalidObservers.append(userId)
        for userId in invalidObservers:
            del self.observers[userId]

    def callLaterFunc(self, interval, func, userId=0, timer=None, msgPackParams=None):
        '''延时调用table对象的一个函数
           原理：延时调用table.doTableCall命令，通过此命令调用table对象的一个函数
           意义：table.doTableCall函数会锁定table对象，保证数据操作的同步性
        '''

        if msgPackParams == None:
            msgPackParams = {}
        msgPackParams["userId"] = userId
        clientId = sessiondata.getClientId(userId) if userId > 0 else None
        msgPackParams["clientId"] = clientId
        msgPackParams["func"] = func
        action = "CL_FUNC"

        if timer == None:
            timer = TYTableTimer(self)
        timer.setup(interval, action, msgPackParams, cancelLastTimer=False)

        funcName = func.func.func_name
        if ftlog.is_debug():
            ftlog.debug(">> |clientId, userId, tableId:", clientId, userId, self.tableId,
                        "|action, func, interval:", action, funcName, interval, caller=self)
