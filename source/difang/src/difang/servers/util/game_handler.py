# -*- coding: utf-8 -*-
'''
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import freetime.util.log as ftlog
from hall.servers.common.base_checker import BaseMsgPackChecker
from poker.entity.game.game import TYGame
from poker.entity.game.plugin import TYPluginCenter
from poker.protocol import runcmd
from poker.protocol.decorator import markCmdActionHandler, markCmdActionMethod


@markCmdActionHandler
class DiFangGameTcpHandler(BaseMsgPackChecker):
    @markCmdActionMethod(cmd='game', action="quick_start", clientIdVer=0, scope='game')
    def doGameQuickStart(self, userId, gameId, clientId, roomId0, tableId0, playMode):
        msg = runcmd.getMsgPack()
        if ftlog.is_debug():
            ftlog.debug("<< |userId, gameId, clientId, msg:", userId, gameId, clientId, msg, caller=self)
        TYGame(gameId).QuickStartDispatcherClass.dispatchQuickStart(msg, userId, gameId, roomId0, tableId0, playMode,
                                                                    clientId)

    @markCmdActionMethod(cmd='game', action="*", scope='game')
    def doHandleCommonGameCmdAction(self, userId, gameId, clientId):
        '''把某个消息转发到 pluginCenter，以便 plugins 能处理 '''
        msg = runcmd.getMsgPack()
        if ftlog.is_debug():
            ftlog.debug("<< |userId, gameId, clientId, msg:", userId, gameId, clientId, msg, caller=self)
        TYPluginCenter.event(msg, gameId)
