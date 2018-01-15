# coding=UTF-8
'''
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

from freetime.util import log as ftlog
from poker.entity.dao import onlinedata
from poker.entity.game.quick_start import BaseQuickStart
from poker.entity.game.rooms.room import TYRoom
from poker.entity.game.rooms.room_mixin import TYRoomMixin
from poker.util import strutil


class DiFangQuickStartDispatcher(object):
    '''按clientId分发快速开始请求
    '''

    @classmethod
    def dispatchQuickStart(cls, msg, userId, gameId, roomId, tableId, playMode, clientId):
        return DiFangQuickStart.onCmdQuickStart(msg, userId, gameId, roomId, tableId, playMode, clientId)


class DiFangQuickStart(BaseQuickStart):
    @classmethod
    def checkReConnect(cls, userId, clientId, gameId):
        loc = onlinedata.checkUserLoc(userId, clientId, gameId)
        if ftlog.is_debug():
            ftlog.debug('checkUserLoc |userId, gameId, loc:', userId, gameId, loc, caller=cls)
        if isinstance(loc, basestring):
            lgameId, lroomId, ltableId, lseatId = strutil.parseInts(*loc.split('.'))
            if lgameId == gameId and lroomId > 0:
                if ftlog.is_debug():
                    ftlog.debug('re-connected |userId, gameId, loc:', userId, gameId, loc, caller=cls)
                TYRoomMixin.querySitReq(userId, lroomId, ltableId, clientId)
                return True

        return False

    @classmethod
    def onCmdQuickStart(cls, msg, userId, gameId, roomId, tableId, playMode, clientId):
        ''''''
        assert isinstance(userId, int) and userId > 0
        assert isinstance(roomId, int) and roomId >= 0
        assert isinstance(tableId, int) and tableId >= 0

        if ftlog.is_debug():
            ftlog.debug("<< |clientId:", clientId,
                        "|userId, roomId, tableId:", userId, roomId, tableId,
                        "|gameId, playMode:", gameId, playMode, caller=cls)

        if cls.checkReConnect(userId, clientId, gameId):
            return

        if not roomId or not tableId:
            ftlog.warn("onCmdQuickStart not roomId or not tableId |userId=",
                       userId, "roomId=", roomId, "tableId=", tableId, caller=cls)
            TYRoomMixin.sendQuickStartRes(gameId, userId, TYRoom.ENTER_ROOM_REASON_NOT_QUALIFIED, roomId, tableId)
            return

        # 进入指定牌桌
        TYRoomMixin.querySitReq(userId, roomId, tableId, clientId)
