# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import stackless
from autobahn.twisted.websocket import WebSocketClientProtocol

import freetime.util.log as ftlog
from freetime.core.protocol import _SocketOpt, FTProtocolBase, \
    _countProtocolPack
from freetime.entity.msg import MsgPack


class WebSocketRobotClientProtocol(WebSocketClientProtocol, FTProtocolBase):
    def __init__(self, robotUser):
        self.encry_seed = 0
        self.robotUser = robotUser

    def onConnect(self, response):
        ftlog.debug("---Server connected: {0}".format(response.peer))

    def onOpen(self):
        ftlog.debug("---WebSocket connection open.")
        self.encry_seed = 1
        mi = MsgPack()
        mi.setCmd('_tcp_conneted_')
        self.robotUser.msgQueue.append(mi)

    def onMessage(self, payload, isBinary):
        # if isBinary:
        #     print("Binary message received: {0} bytes".format(len(payload)))
        # else:
        #     print("Text message received: {0}".format(payload.decode('utf8')))
        msg = payload.decode('utf8')
        ftlog.debug('ws onMessage', msg)
        _countProtocolPack(1, self)
        self._runTasklet(data=msg)

    def connectionMade(self):
        if self.robotUser:
            _SocketOpt.tcp(self)
            ftlog.debug('RobotClientProtocol.connectionMade', self.robotUser.snsId)
            super(WebSocketClientProtocol, self).connectionMade()
        else:
            ftlog.debug('RobotClientProtocol.connectionMade robot user is none !!')
            self.closeConnection(1)

    def dataReceived(self, data):
        try:
            if not self.state:
                return
            super(WebSocketRobotClientProtocol, self).dataReceived(data)
        except:
            pass

    def lostHandler(self, reason):
        if self.robotUser:
            mi = MsgPack()
            mi.setCmd('_tcp_closed_')
            self.robotUser.msgQueue.append(mi)
        else:
            pass

    def getTaskletFunc(self, pack):
        return self.onMsg

    def parseData(self, data):
        return data

    def onMsg(self):
        if self.robotUser:
            pack = stackless.getcurrent()._fttask.pack
            #             ftlog.debug('RobotClientProtocol.onMsg', self.robotUser.snsId, '[' + pack + ']')
            msg = MsgPack()
            msg.unpack(pack)
            self.robotUser.msgQueue.append(msg)
        else:
            #             ftlog.debug('RobotClientProtocol.onMsg robot user is none !!')
            self.closeConnection(1)

    def writeMsg(self, msg):
        if not isinstance(msg, (str, unicode)):
            msg = msg.pack()
        # ftlog.debug('===>', self.robotUser.snsId, msg)
        #         dlen = len(msg)
        #         msg = '%04X' % dlen + ftenc.code(self.encry_seed + dlen, msg)
        #         self.transport.write(msg)
        self.sendMessage(msg)

    def startedConnecting(self, connector):
        pass
