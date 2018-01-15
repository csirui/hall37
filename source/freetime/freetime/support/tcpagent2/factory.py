# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.4.15

from twisted.internet.protocol import ReconnectingClientFactory


class FTReconnectFactory(ReconnectingClientFactory):
    def __init__(self):
        # 强制2s内重连...
        self.maxDelay = 2

    def startedConnecting(self, connector):
        pass

    def buildProtocol(self, addr):
        p = self.protocol()
        p.factory = self
        return p
