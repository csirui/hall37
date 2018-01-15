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
class DiFangTableTcpHandler(BaseMsgPackChecker):
    @markCmdActionMethod(cmd='table', action="*", scope='game')
    def doHandleCommonRoomCmdAction(self, gameId, roomId, userId, clientId):
        msg = runcmd.getMsgPack()
        room = gdata.rooms()[roomId]
        tableId = msg.getParam("tableId")
        if tableId:
            table = room.maptable[tableId]
        else:
            table = None

        params = msg.getKey('params')
        params.update({'room': room, 'table': table})

        if ftlog.is_debug():
            ftlog.debug("<< |userId, gameId, roomId, tableId, clientId, msg:", userId, gameId, roomId, clientId, msg,
                        caller=self)

        TYPluginCenter.event(msg, gameId)

    @markCmdActionMethod(cmd='table', action="gm", scope='game', lockParamName='')
    def doTableGM(self, gameId, roomId, tableId):
        msg = runcmd.getMsgPack()
        if ftlog.is_debug():
            ftlog.info('doTableGM msg=', msg, caller=self)

        room = gdata.rooms()[roomId]
        table = room.maptable[tableId]

        result = {}
        params = msg.getKey('params')
        params.update({'room': room, 'table': table})

        evmsg = TYPluginUtils.updateMsg(cmd="EV_TABLE_GM", params=params,
                                        result=result)
        TYPluginCenter.event(msg, room.gameId)

        if router.isQuery():
            mo = TYPluginUtils.updateMsg(cmd='table', result=result)
            router.responseQurery(mo)
