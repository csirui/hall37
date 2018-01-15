# coding=UTF-8
'''房间基类Mixin
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack
from freetime.util.log import getMethodName
from poker.entity.biz import bireport
from poker.entity.configure import gdata
from poker.entity.dao import userchip, sessiondata
from poker.protocol import router
from poker.util import strutil


class TYRoomMixin(object):
    '''房间Mixin基类
    
    '''

    @classmethod
    def sendRoomQuickStartReq(cls, msg, roomId, tableId, **kwargs):
        msg.setCmd("room")
        msg.setParam("action", "quick_start")
        msg.setParam("roomId", roomId)
        msg.setParam("tableId", tableId)
        for key in kwargs:
            msg.setParam(key, kwargs[key])
        if ftlog.is_debug():
            ftlog.debug(msg, caller=cls)
        router.sendRoomServer(msg, roomId)

    @classmethod
    def queryRoomQuickStartReq(cls, msg, roomId, tableId, **kwargs):
        msg.setCmd("room")
        msg.setParam("action", "quick_start")
        msg.setParam("roomId", roomId)
        msg.setParam("tableId", tableId)
        for key in kwargs:
            msg.setParam(key, kwargs[key])
        if ftlog.is_debug():
            ftlog.debug(msg, caller=cls)
        router.queryRoomServer(msg, roomId)

    @classmethod
    def queryRoomGetPlayingTableListReq(cls, shadowRoomId, **kwargs):
        msg = MsgPack()
        msg.setCmd("room")
        msg.setParam("action", "playingTableList")
        msg.setParam("roomId", shadowRoomId)
        for key in kwargs:
            msg.setParam(key, kwargs[key])
        if ftlog.is_debug():
            ftlog.debug(msg, caller=cls)
        return router.queryTableServer(msg, shadowRoomId)

    @classmethod
    def makeSitReq(cls, userId, shadowRoomId, tableId, clientId):
        mpSitReq = MsgPack()
        mpSitReq.setCmd("table")
        mpSitReq.setParam("action", "sit")
        mpSitReq.setParam("userId", userId)
        mpSitReq.setParam("roomId", shadowRoomId)
        mpSitReq.setParam("tableId", tableId)
        mpSitReq.setParam("clientId", clientId)
        mpSitReq.setParam("gameId", strutil.getGameIdFromInstanceRoomId(shadowRoomId))
        if ftlog.is_debug():
            ftlog.debug(str(mpSitReq), caller=cls)
        return mpSitReq

    @classmethod
    def sendSitReq(cls, userId, shadowRoomId, tableId, clientId, extParams=None):
        mpSitReq = cls.makeSitReq(userId, shadowRoomId, tableId, clientId)
        if extParams:
            moParams = mpSitReq.getKey('params')
            for k, v in extParams.items():
                if not k in moParams:
                    moParams[k] = v
        if ftlog.is_debug():
            ftlog.debug(str(mpSitReq), caller=cls)
        router.sendTableServer(mpSitReq, shadowRoomId)

    @classmethod
    def querySitReq(cls, userId, shadowRoomId, tableId, clientId, extParams=None):
        mpSitReq = cls.makeSitReq(userId, shadowRoomId, tableId, clientId)
        if extParams:
            moParams = mpSitReq.getKey('params')
            for k, v in extParams.items():
                if not k in moParams:
                    moParams[k] = v
        if ftlog.is_debug():
            ftlog.debug(str(mpSitReq), caller=cls)
        router.queryTableServer(mpSitReq, shadowRoomId)

    @classmethod
    def sendTableCallObserveReq(cls, userId, shadowRoomId, tableId, clientId):
        mpReq = MsgPack()
        mpReq.setCmd("table_call")
        mpReq.setParam("action", "observe")
        mpReq.setParam("userId", userId)
        mpReq.setParam("roomId", shadowRoomId)
        mpReq.setParam("tableId", tableId)
        mpReq.setParam("clientId", clientId)
        if ftlog.is_debug():
            ftlog.debug(str(mpReq), caller=cls)
        router.sendTableServer(mpReq, shadowRoomId)

    @classmethod
    def makeTableManageReq(cls, userId, shadowRoomId, tableId, clientId, action, params=None):
        mpReq = MsgPack()
        mpReq.setCmd("table_manage")
        mpReq.setParam("action", action)
        mpReq.setParam("userId", userId)
        mpReq.setParam("gameId", strutil.getGameIdFromInstanceRoomId(shadowRoomId))
        mpReq.setParam("roomId", shadowRoomId)
        mpReq.setParam("tableId", tableId)
        mpReq.setParam("clientId", clientId)
        if params:
            mpReq.updateParam(params)
        if ftlog.is_debug():
            ftlog.debug(str(mpReq), caller=cls)
        return mpReq

    @classmethod
    def queryTableManageSitReq(cls, userId, shadowRoomId, tableId, clientId):
        mpReq = cls.makeTableManageReq(userId, shadowRoomId, tableId, clientId, 'sit')
        if ftlog.is_debug():
            ftlog.debug(str(mpReq), caller=cls)
        return router.queryTableServer(mpReq, shadowRoomId)

    @classmethod
    def queryTableManageTableStandupReq(cls, userId, shadowRoomId, tableId, seatId, clientId, reason):
        mpReq = cls.makeTableManageReq(userId, shadowRoomId, tableId, clientId, 'standup', {
            'seatId': seatId, 'reason': reason})
        if ftlog.is_debug():
            ftlog.debug(str(mpReq), caller=cls)
        return router.queryTableServer(mpReq, shadowRoomId)

    @classmethod
    def queryTableManageTableLeaveReq(cls, userId, shadowRoomId, tableId, clientId, params=None):
        mpReq = cls.makeTableManageReq(userId, shadowRoomId, tableId, clientId, 'leave', params)
        if ftlog.is_debug():
            ftlog.debug(str(mpReq), caller=cls)
        return router.queryTableServer(mpReq, shadowRoomId)

    def sendTableManageGameStartReq(self, shadowRoomId, tableId, userIds, recyclePlayersN=0, params=None):
        '''recyclePlayersN表示需要从牌桌回收到队列的人数
        '''
        mpReq = self.makeTableManageReq(0, shadowRoomId, tableId, None, 'game_start',
                                        {'recyclePlayersN': recyclePlayersN})
        mpReq.setParam("userIds", userIds)
        from poker.entity.game.rooms import tyRoomConst
        if self.roomConf['typeName'] == tyRoomConst.ROOM_TYPE_NAME_MTT and self.state == self.MTT_STATE_FINALS:
            mpReq.setParam("isFinalTable", True)
        if params:
            mpReq.updateParam(params)
        ftlog.hinfo(str(mpReq), caller=self)
        router.sendTableServer(mpReq, shadowRoomId)

    #     @classmethod
    #     def queryTableManageGameStartReq(cls, shadowRoomId, tableId, userIds):
    #         mpReq = cls.makeTableManageReq(0, shadowRoomId, tableId, None, 'game_start')
    #         mpReq.setParam("userIds", userIds)
    #         ftlog.debug(str(mpReq), caller=cls)
    #         return router.queryTableServer(mpReq, shadowRoomId)


    @classmethod
    def queryTableManageClearPlayersReq(cls, shadowRoomId, tableId):
        mpReq = cls.makeTableManageReq(0, shadowRoomId, tableId, None, 'clear_players')
        if ftlog.is_debug():
            ftlog.debug(str(mpReq), caller=cls)
        return router.queryTableServer(mpReq, shadowRoomId)

    @classmethod
    def sendChangeBetsConfReq(cls, shadowRoomId, betsConf):
        mpReq = MsgPack()
        mpReq.setCmd("room")
        mpReq.setParam("action", "change_betsConf")
        mpReq.setParam("roomId", shadowRoomId)
        mpReq.setParam("betsConf", betsConf)
        if ftlog.is_debug():
            ftlog.debug(str(mpReq), caller=cls)
        router.sendTableServer(mpReq, shadowRoomId)

    @classmethod
    def sendChangeBetsConfReqToAllShadowRoom(cls, ctrlRoomId, betsConf):
        for shadowRoomId in gdata.roomIdDefineMap()[ctrlRoomId].shadowRoomIds:
            cls.sendChangeBetsConfReq(shadowRoomId, betsConf)

    @classmethod
    def sendTableClothRes(cls, gameId, userId, tableType, tableTheme=None):
        mpTableClothRes = MsgPack()
        mpTableClothRes.setCmd('table_cloth')
        mpTableClothRes.setResult('userId', userId)
        mpTableClothRes.setResult('gameId', gameId)
        mpTableClothRes.setResult('tableType', tableType)
        mpTableClothRes.setResult('tableTheme', tableTheme)
        router.sendToUser(mpTableClothRes, userId)
        if ftlog.is_debug():
            ftlog.debug("|mpTableClothRes:", mpTableClothRes, caller=cls)

    @classmethod
    def sendQuickStartRes(cls, gameId, userId, reason, roomId=0, tableId=0, info=""):
        mpQuickRes = MsgPack()
        mpQuickRes.setCmd('quick_start')
        mpQuickRes.setResult('info', info)
        mpQuickRes.setResult('userId', userId)
        mpQuickRes.setResult('gameId', gameId)
        mpQuickRes.setResult('roomId', roomId)
        mpQuickRes.setResult('tableId', tableId)
        mpQuickRes.setResult('seatId', 0)  # 兼容检查seatId参数的地主客户端
        mpQuickRes.setResult('reason', reason)
        router.sendToUser(mpQuickRes, userId)
        ftlog.hinfo("|mpQuickRes:", mpQuickRes, caller=cls)

    def reportBiGameEvent(self, eventId, userId, roomId, tableId, roundId, detalChip, state1, state2, cardlist, tag=''):
        try:
            finalUserChip = userchip.getChip(userId)
            finalTableChip = 0
            clientId = sessiondata.getClientId(userId)
            bireport.reportGameEvent(eventId, userId, self.gameId, roomId, tableId, roundId, detalChip,
                                     state1, state2, cardlist, clientId, finalTableChip, finalUserChip)
            if ftlog.is_debug():
                ftlog.debug('tag=', tag, 'eventId=', eventId, 'userId=', userId, 'gameId=', self.gameId,
                            'roomId=', roomId, 'tableId=', tableId, 'roundId=', roundId, 'detalChip=', detalChip,
                            caller=self)
        except:
            ftlog.error(getMethodName(), 'tag=', tag, 'eventId=', eventId, 'userId=', userId, 'gameId=', self.gameId)
