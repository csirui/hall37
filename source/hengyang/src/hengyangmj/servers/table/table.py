# -*- coding=utf-8 -*-
'''
Created on 2015年9月29日

@author: liaoxx
'''

from difang.majiang2.servers.table.table import TableTcpHandler
from poker.protocol.decorator import markCmdActionHandler, markCmdActionMethod


@markCmdActionHandler
class hengyangmjTableTcpHandler(TableTcpHandler):
    def __init__(self):
        super(hengyangmjTableTcpHandler, self).__init__()

    @markCmdActionMethod(cmd='table', action="chat", clientIdVer=0, scope='game')
    def doTableChat(self, userId, roomId, tableId, seatId, isFace, voiceIdx, chatMsg):
        super(hengyangmjTableTcpHandler, self).doTableChat(userId, roomId, tableId, seatId, isFace, voiceIdx, chatMsg)

    @markCmdActionMethod(cmd='table', action="smilies", clientIdVer=0, scope='game')
    def doTableSmilies(self, userId, roomId, tableId, seatId, smilies, toseat):
        super(hengyangmjTableTcpHandler, self).doTableSmilies(userId, roomId, tableId, seatId, smilies, toseat)

    @markCmdActionMethod(cmd='table_call', action="leave_table_scene", clientIdVer=0, scope='game')
    def doTableSceneLeave(self, userId, roomId, tableId, seatId):
        super(hengyangmjTableTcpHandler, self).doTableSceneLeave(userId, roomId, tableId, seatId)
