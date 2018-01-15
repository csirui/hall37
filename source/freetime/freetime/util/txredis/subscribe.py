# -*- coding=utf-8 -*-

import freetime.util.log as ftlog


def startSubScriber(ip, port, channels, funOnMessage):
    assert (isinstance(ip, (str, unicode))), 'the ip must be string'
    assert (isinstance(port, int)), 'the port must be integer'
    assert (isinstance(channels, (list, tuple))), 'the channels must be a list or tuple with string content'
    assert (callable(funOnMessage)), 'the funOnMessage must be callable, with 2 args'

    from twisted.internet import reactor
    from freetime.util.txredis.client import RedisSubscriber, RedisSubscriberFactory

    class myProtocol(RedisSubscriber):

        def connectionMade(self):
            super(myProtocol, self).connectionMade()
            self.subscribe(*channels)
            ftlog.debug("waiting for messages...", ip, port, channels)

        def messageReceived(self, channel, message):
            ftlog.debug('messageReceived->', channel, message)
            try:
                funOnMessage(channel, message)
            except:
                ftlog.error()

    class myFactory(RedisSubscriberFactory):
        maxDelay = 2
        continueTrying = True
        protocol = myProtocol

    reactor.connectTCP(ip, port, myFactory())
