# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import freetime.util.log as ftlog


class TcpUser(object):
    '''
    CONN服务使用的用户的对象定义
    '''

    def __init__(self, uid):
        self.userId = uid
        self.hbcounter = 0
        self.hbcounts = 0
        self.firstUserInfo = 0
        self.tcpProtocol = None
        self.clientId = ''
        self.cid = ''
        self.gameId = 0
        self.delaySendMsg = []
        self.carryMsg = []

    def sendTcpMessage(self, strmsg):
        '''
        发送消息至用户的客户端
        '''
        if self.tcpProtocol:
            self.tcpProtocol.writeEncodeMsg(strmsg)
        else:
            ftlog.debug('the user has no connected ! userId=', self.userId)

    def sendCarryMsg(self):
        if self.tcpProtocol and self.firstUserInfo and self.carryMsg:
            mlist = self.carryMsg
            self.carryMsg = []
            for m in mlist:
                ftlog.debug('send carry msg->', m)
                self.tcpProtocol.writeEncodeMsg(m)
