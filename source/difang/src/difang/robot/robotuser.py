# -*- coding=utf-8 -*-
'''
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

from freetime.entity.msg import MsgPack
from freetime.util import log as ftlog
from poker.entity.configure import gdata
from poker.entity.dao import onlinedata
from poker.entity.game import rooms
from poker.entity.game.rooms.room import TYRoom
from poker.entity.robot.robotuser import RobotUser


class DiFangRobotUser(RobotUser):
    TCPSRV = {}  # 测试时指定的Tcp server，而不是使用sdk server返回的tcp server地址；

    def __init__(self, clientId, snsId, name):
        super(DiFangRobotUser, self).__init__(clientId, snsId, name)

    def _start(self):
        ftlog.debug("<< |snsId:", self.snsId, caller=self)
        super(DiFangRobotUser, self)._start()
        self.bigRoomId = gdata.getBigRoomId(self.roomId)
        self.responseDelaySecond = 3

    def _doConnTcp(self):
        if not self.TCPSRV:
            tcpsrv = self.userInfo['tcpsrv']
        else:
            tcpsrv = self.TCPSRV
        ftlog.debug('_doConnTcp->', tcpsrv)
        from twisted.internet import reactor
        factory = self._createClientFactory(tcpsrv['ip'], tcpsrv['port'])
        reactor.connectTCP(tcpsrv['ip'], tcpsrv['port'], factory)

    def _enterRoom(self):
        ftlog.debug('<<', caller=self)
        self.adjustChip()
        onlinedata.cleanOnlineLoc(self.userId)
        mo = MsgPack()
        mo.setCmdAction('game', 'quick_start')
        mo.setParam('userId', self.userId)
        mo.setParam('gameId', self.gameId)
        mo.setParam('clientId', self.clientId)
        mo.setParam('roomId', self.bigRoomId)
        self.writeMsg(mo)

    def _enterTable(self):
        ftlog.debug('<<', caller=self)
        # self.adjustChip()
        onlinedata.cleanOnlineLoc(self.userId)
        mo = MsgPack()
        mo.setCmdAction('game', 'quick_start')
        mo.setParam('userId', self.userId)
        mo.setParam('gameId', self.gameId)
        mo.setParam('clientId', self.clientId)
        mo.setParam('roomId', self.tableId / 10000)
        mo.setParam('tableId', self.tableId)
        self.writeMsg(mo)

    def _signinMtt(self):
        ftlog.debug('<<', caller=self)
        mo = MsgPack()
        mo.setCmdAction('room', 'signin')
        mo.setParam('userId', self.userId)
        mo.setParam('gameId', self.gameId)
        mo.setParam('clientId', self.clientId)
        mo.setParam('roomId', self.bigRoomId)
        self.writeMsg(mo)

    def onMsgTableBegin(self):
        ftlog.debug('|self.roomId:', self.roomId, caller=self)
        roomTypeName = gdata.roomIdDefineMap()[self.roomId].configure['typeName']
        # if roomTypeName in (rooms.tyRoomConst.ROOM_TYPE_NAME_NORMAL,
        #                     rooms.tyRoomConst.ROOM_TYPE_NAME_QUEUE,
        #                     rooms.tyRoomConst.ROOM_TYPE_NAME_SNG,
        #                     rooms.tyRoomConst.ROOM_TYPE_NAME_HUNDREDS,
        #                     rooms.tyRoomConst.ROOM_TYPE_NAME_DTG):
        #     self._enterRoom()
        if roomTypeName in (rooms.tyRoomConst.ROOM_TYPE_NAME_CUSTOM):
            self._enterTable()
        # if roomTypeName == rooms.tyRoomConst.ROOM_TYPE_NAME_MTT:
        #     self._signinMtt()
        return

    def onMsgTablePlay(self, msg):
        ftlog.debug('|snsId, userId, seatId:', self.snsId, self.userId, self.seatId, 'msg->', msg, caller=self)
        cmd = msg.getCmd()
        if cmd == 'quick_start':
            roomId = msg.getResult('roomId')
            tableId = msg.getResult('tableId')
            roomTypeName = gdata.getRoomConfigure(roomId)['typeName']
            # if roomTypeName in (rooms.tyRoomConst.ROOM_TYPE_NAME_NORMAL,
            #                     rooms.tyRoomConst.ROOM_TYPE_NAME_QUEUE,
            #                     rooms.tyRoomConst.ROOM_TYPE_NAME_SNG,
            #                     rooms.tyRoomConst.ROOM_TYPE_NAME_MTT,
            #                     rooms.tyRoomConst.ROOM_TYPE_NAME_HUNDREDS,
            #                     rooms.tyRoomConst.ROOM_TYPE_NAME_DTG) :
            #     if tableId == 0: # 进入队列的返回，忽略
            #         return
            #     else:
            #         self.tableId = tableId

            seatId = msg.getResult('seatId', 0)
            self.seatId = seatId - 1
            if tableId == self.tableId and seatId > 0:
                ftlog.debug('QuickStart', self.snsId, 'OK !', roomId, tableId, seatId)
            else:
                # 快速开始失败
                ftlog.error('QuickStart', self.snsId, self.roomId, self.tableId, msg)
                self.stop()

        action = msg.getResult('action')
        if (cmd == 'table' and action == 'info') or cmd == 'tableInfo':
            self.tableInfoResult = msg.getKey('result')

        if cmd == 'standup':
            userId = msg.getResult('userId')
            reason = msg.getResult('reason')
            if userId == self.userId and reason != TYRoom.LEAVE_ROOM_REASON_CHANGE_TABLE:
                mo = MsgPack()
                mo.setCmdAction('room', 'leave')
                mo.setParam('userId', self.userId)
                mo.setParam('gameId', self.gameId)
                mo.setParam('clientId', self.clientId)
                mo.setParam('roomId', self.bigRoomId)
                self.writeMsg(mo)

        if (cmd == 'room' and action == 'leave') or cmd == 'room_leave':
            self.stop()

        if cmd == 'table_call':
            if action == 'game_start':
                ftlog.debug("table_call game_start |msg:", msg, caller=self)
                self.gameStartResult = msg.getKey('result')
                return

            elif action == 'game_win':
                ftlog.debug("table_call game_win |msg:", msg, caller=self)
                self.sendReadyReq(msg)
                return

    def sendReadyReq(self, msg):
        mo = MsgPack()
        mo.setCmdAction('table_call', "ready")
        mo.setParam('userId', self.userId)
        mo.setParam('gameId', self.gameId)
        mo.setParam('clientId', self.clientId)
        mo.setParam('roomId', msg.getResult("roomId"))
        mo.setParam('tableId', self.tableId)
        mo.setParam('seatId', self.seatId)
        self.writeDelayMsg(2, mo)
