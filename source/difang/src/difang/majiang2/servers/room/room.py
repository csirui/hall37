# -*- coding=utf-8 -*-
'''
Created on 2015年10月25日

@author: liaoxx
'''
import time
from random import choice

from difang.majiang2.entity.util import sendPopTipMsg
from difang.servers.util.rpc import user_remote
from freetime.entity.msg import MsgPack
from freetime.util import log as ftlog
from hall.entity import hall_friend_table
from hall.servers.common.base_checker import BaseMsgPackChecker
from poker.entity.configure import gdata
from poker.entity.dao import gamedata
from poker.protocol import router, runcmd


class RoomTcpHandler(BaseMsgPackChecker):
    def __init__(self):
        pass

    def _check_param_match_id(self, msg, key, params):
        match_id = msg.getParam("match_id")
        if match_id and isinstance(match_id, (str, unicode)):
            return None, match_id
        return 'ERROR of match_id !' + str(match_id), None

    def doMatchState(self, userId, gameId, roomId):
        msg = runcmd.getMsgPack()
        match_id = msg.getParam("match_id")
        if match_id:  # 老比赛，由于前端新比赛也会发此消息，但没有match_id导致的问题，这里处理下
            state = gdata.rooms()[roomId].getMatchState(userId, gameId, match_id)
            current_ts = int(time.time())
            msg = MsgPack()
            msg.setCmd('match_state')
            msg.setResult('gameId', gameId)
            msg.setResult('userId', userId)
            msg.setResult('state', state)
            msg.setResult('match_id', match_id)
            msg.setResult('current_ts', current_ts)
            router.sendToUser(msg, userId)

    def doMatchAwardCertificate(self, userId, gameId, roomId, match_id):
        room = gdata.rooms()[roomId]
        if hasattr(room, 'get_award_certificate'):
            room.get_award_certificate(userId, gameId, match_id)

    def signinNextMatch(self, gameId, userId):
        """报名下一场比赛
        """
        msg = runcmd.getMsgPack()
        roomId = msg.getParam('room_id', 0)
        ctlRoomIds = [bigRoomId * 10000 + 1000 for bigRoomId in gdata.gameIdBigRoomidsMap()[gameId]]
        if roomId in ctlRoomIds:
            room = gdata.rooms()[roomId]
            if room:
                signinParams = gamedata.getGameAttrJson(userId, room.gameId, 'test.signinParams')
                room.doSignin(userId, signinParams)
            else:
                ftlog.info('=======signinNextMatch==Trace==', roomId, userId)

    def doCreateTable(self, userId, gameId, roomId):
        """自建桌创建
            1.通过roomId得到房间对象
            2.得到合适的tableId,然后sit
        """
        ftlog.info("<< doCreateTable | userId, clientId, roomId, msg:", userId, gameId, roomId)

        msg = runcmd.getMsgPack()
        room = gdata.rooms()[roomId]
        self._doCreateTable(room, msg, gameId)
        if router.isQuery():
            mo = runcmd.newOkMsgPack(1)
            router.responseQurery(mo, '', str(userId))

    def _doCreateTable(self, room, msg, gameId):
        """选择合适的table,然后sit
        """
        assert room.roomId == msg.getParam("roomId")

        userId = msg.getParam("userId")
        clientId = msg.getParam("clientId")
        ftlog.info("<< _doCreateTable |userId, clientId, roomId, msg:", userId, clientId, room.roomId, msg)

        fangka_count = msg.getParam("needFangka")
        itemId = room.roomConf.get('create_item', None)

        if not itemId:
            sendPopTipMsg(userId, "未知房卡")

        consumeResult = user_remote.consumeItem(userId, gameId, itemId, fangka_count, room.roomId)
        if not consumeResult:
            sendPopTipMsg(userId, "房卡不足，请购买")
            return

        # 扣卡成功，产生自建桌号，分配table
        shadowRoomId = choice(room.roomDefine.shadowRoomIds)
        tableId = room.getBestTableId(userId, shadowRoomId)
        if not tableId:  # 拿不到桌子
            sendPopTipMsg(userId, "哎呀呀，没有空桌子了……我们稍候会优先为您安排新桌，请稍等片刻~")
            ftlog.error("getFreeTableId timeout", "|userId, roomId, tableId:", userId, room.roomId, tableId)
            user_remote.resumeItemFromRoom(userId, gameId, itemId, fangka_count, room.roomId)
            return

        # 扣卡成功，产生自建桌号
        for _ in range(10):
            ftId = hall_friend_table.createFriendTable(gameId)
            if ftId:
                ftlog.info("room._doCreateTable create_table ok, userId:", userId
                           , " shadowRoomId:", shadowRoomId
                           , " roomId:", room.roomId
                           , " tableId:", tableId
                           , " ftId:", ftId
                           , " fangka_count:", fangka_count
                           , room.roomConf)
                extParams = msg.getKey('params')
                extParams['ftId'] = ftId
                room.querySitReq(userId, shadowRoomId, tableId, clientId, extParams)
                return

        ftlog.error('room._doCreateTable request ftId error, return fangka item...')
        user_remote.resumeItemFromRoom(userId, gameId, itemId, fangka_count, room.roomId)

    def doJoinCreateTable(self, userId, gameId, roomId):
        """加入自建桌
        """
        msg = runcmd.getMsgPack()
        ftlog.debug('RoomTcpHandler.doJoinCreateTable msg=', userId,
                    gameId, roomId, msg, caller=self)
        room = gdata.rooms()[roomId]
        self._doJoinCreateTable(room, msg)
        if router.isQuery():
            mo = runcmd.newOkMsgPack(1)
            router.responseQurery(mo, '', str(userId))

    def _doJoinCreateTable(self, room, msg):
        assert room.roomId == msg.getParam("roomId")
        userId = msg.getParam("userId")
        shadowRoomId = msg.getParam("shadowRoomId")
        tableId = msg.getParam("tableId")
        clientId = msg.getParam("clientId")
        ftlog.info("<<|userId, clientId, roomId, shadowRoomId, tableId:", userId, clientId, room.roomId, shadowRoomId,
                   tableId)

        assert isinstance(shadowRoomId, int) and gdata.roomIdDefineMap()[
                                                     shadowRoomId].bigRoomId == room.roomDefine.bigRoomId
        extParams = msg.getKey('params')
        room.querySitReq(userId, shadowRoomId, tableId, clientId, extParams)

    def doRoomQuickStart(self, roomId, userId):
        msg = runcmd.getMsgPack()
        ftlog.debug('msg=', msg, caller=self)
        gdata.rooms()[roomId].doQuickStart(msg)
        if router.isQuery():
            mo = runcmd.newOkMsgPack(1)
            router.responseQurery(mo, '', str(userId))
