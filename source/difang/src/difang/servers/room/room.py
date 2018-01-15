# -*- coding: utf-8 -*-

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import freetime.util.log as ftlog
from hall.servers.common.base_checker import BaseMsgPackChecker
from poker.entity.configure import gdata
from poker.entity.game.plugin import TYPluginCenter, TYPluginUtils
from poker.protocol import runcmd, router
from poker.protocol.decorator import markCmdActionHandler, markCmdActionMethod


@markCmdActionHandler
class DiFangRoomTcpHandler(BaseMsgPackChecker):
    @markCmdActionMethod(cmd='room', action="*", scope='game')
    def doHandleCommonRoomCmdAction(self, userId, gameId, roomId, clientId):
        room = gdata.rooms()[roomId]
        msg = runcmd.getMsgPack()
        params = msg.getKey('params')
        params.update({'room': room})

        if ftlog.is_debug():
            ftlog.debug("<< |userId, gameId, roomId, clientId, msg:", userId, gameId, roomId, clientId, msg,
                        caller=self)

        TYPluginCenter.event(msg, gameId)

        if router.isQuery():
            mo = runcmd.newOkMsgPack(1)
            router.responseQurery(mo)

    @markCmdActionMethod(cmd='room', action="gm", clientIdVer=0, lockParamName='', scope='game')
    def doRoomGM(self, roomId):
        msg = runcmd.getMsgPack()
        if ftlog.is_debug():
            ftlog.info('doRoomGM msg=', msg, caller=self)
        room = gdata.rooms()[roomId]

        result = {}
        params = msg.getKey('params')
        params.update({'room': room})

        evmsg = TYPluginUtils.updateMsg(cmd='EV_ROOM_GM', params=params,
                                        result=result)
        TYPluginCenter.event(evmsg, room.gameId)

        if router.isQuery():
            mo = TYPluginUtils.updateMsg(cmd='room', result=result)
            router.responseQurery(mo)
