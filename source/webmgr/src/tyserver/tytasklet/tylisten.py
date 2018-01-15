# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from twisted.internet import reactor
from twisted.web.http import HTTPFactory

from tyserver.tytasklet.typrotocol import TyHttpChannel, WebSocketFactory


def listenHttp(httpoprt):
    factory = HTTPFactory()
    def _dummy(*args, **argd):
        pass 
    factory.log = _dummy
    factory.protocol = TyHttpChannel
    reactor.listenTCP(httpoprt, factory)


def listenWs(wsport):
    reactor.listenTCP(wsport, WebSocketFactory())

