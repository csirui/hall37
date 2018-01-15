# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import zlib

import stackless

import freetime.util.encry as ftenc
from freetime.core.protocol import FTZipEncryServerProtocol, _SocketOpt, \
    _countProtocolPack
from freetime.entity.msg import MsgPack


class RobotClientProtocol(FTZipEncryServerProtocol):
    def __init__(self, robotUser):
        self.encry_seed = 0
        self.robotUser = robotUser

    def connectionMade(self):
        if self.robotUser:
            _SocketOpt.tcp(self)
        # ftlog.debug('RobotClientProtocol.connectionMade', self.robotUser.snsId)
        else:
            #             ftlog.debug('RobotClientProtocol.connectionMade robot user is none !!')
            self.closeConnection(1)

    def dataReceived(self, data):
        if self.encry_seed == 0:
            if len(data) >= 4:
                self.encry_seed = int(data, 16)
                #                 ftlog.debug('RobotClientProtocol.lineReceived encry_seed=', self.encry_seed)
                mi = MsgPack()
                mi.setCmd('_tcp_conneted_')
                self.robotUser.msgQueue.append(mi)
            data = data[4:]
        super(RobotClientProtocol, self).dataReceived(data)

    def lineReceived(self, data):
        data = ftenc.code(self.encry_seed + int(data[:4], 16), data[4:])
        data = zlib.decompress(data)
        _countProtocolPack(1, self)
        self._runTasklet(data=data)

    def lostHandler(self, reason):
        if self.robotUser:
            #             ftlog.debug('RobotClientProtocol.lostHandler', reason, self.robotUser.snsId)
            mi = MsgPack()
            mi.setCmd('_tcp_closed_')
            self.robotUser.msgQueue.append(mi)
        else:
            #             ftlog.debug('RobotClientProtocol.lostHandler robot user is none !!')
            pass

    def getTaskletFunc(self, pack):
        return self.onMsg

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
        dlen = len(msg)
        msg = '%04X' % dlen + ftenc.code(self.encry_seed + dlen, msg)
        self.transport.write(msg)
