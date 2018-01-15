# -*- coding=utf-8 -*-
'''
Created on 2015年10月25日

@author: liaoxx
'''
from difang.majiang2.servers.room.room import RoomTcpHandler
from poker.protocol.decorator import markCmdActionHandler, markCmdActionMethod


@markCmdActionHandler
class hengyangmjRoomTcpHandler(RoomTcpHandler):
    CONST_TAG = "[hengyangmjRoomTcpHandler]: "  # 对象标记

    def __init__(self):
        super(hengyangmjRoomTcpHandler, self).__init__()

    @markCmdActionMethod(cmd='room', action="create_table", clientIdVer=0, scope='game', lockParamName="")
    def doCreateTable(self, userId, gameId, roomId):
        '''
        创建牌桌
        PS：
        1.创建失败，要退还房卡

        '''
        super(hengyangmjRoomTcpHandler, self).doCreateTable(userId, gameId, roomId)

    @markCmdActionMethod(cmd='room', action="join_create_table", clientIdVer=0, scope='game', lockParamName="")
    def doJoinCreateTable(self, userId, gameId, roomId):
        super(hengyangmjRoomTcpHandler, self).doJoinCreateTable(userId, gameId, roomId)

    @markCmdActionMethod(cmd='room', action="quick_start", clientIdVer=0, scope='game')
    def doRoomQuickStart(self, roomId, userId):
        super(hengyangmjRoomTcpHandler, self).doRoomQuickStart(roomId, userId)
