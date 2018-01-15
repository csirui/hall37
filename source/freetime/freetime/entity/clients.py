# -*- coding=utf-8
'''
Created on 2015年6月3日

@author: zhaoqh
'''
import json
import urllib

from twisted.internet import protocol, reactor

import freetime.util.log as ftlog
from freetime.aio import http
from freetime.core.timer import FTLoopTimer
from freetime.entity.msg import MsgPack
from freetime.support.tcpagent.factory import FTReconnectFactory

_DEBUG = 0
debug = ftlog.info


class _HttpAdapter():
    def __init__(self, httppath, timeout, retryCount):
        self.httppath = httppath
        self.timeout = timeout
        self.retryCount = retryCount

    def start(self):
        pass

    def isOK(self):
        return self.httppath != None

    def send(self, dataDict, headerDict=None):
        if self.httppath:
            if isinstance(dataDict, (str, unicode)):
                postdata_ = dataDict
            elif isinstance(dataDict, MsgPack):
                postdata_ = urllib.urlencode(dataDict._ht)
            elif isinstance(dataDict, dict):
                postdata_ = urllib.urlencode(dataDict)
            else:
                postdata_ = json.dumps(dataDict)

            if headerDict == None:
                headers_ = {'Content-type': ['application/x-www-form-urlencoded']}
            else:
                headers_ = {}
                for k, v in headerDict.items():
                    headers_[k] = [v]
            http.runHttpNoResponse('POST', self.httppath, headers_, postdata_, self.timeout,
                                   retrydata={'try': 0, 'max': self.retryCount})

    def close(self):
        self.httppath = None


class _UdpAdapter():
    _UDPSENDER = None

    def __init__(self, udppath, timeout, retryCount):
        self.timeout = timeout  # HOW TODO ? UDP发送超时和重试机制,需要制定QUERY模式
        self.retryCount = retryCount
        datas = udppath[7:].split(':')
        self.toAddress = (datas[0], int(datas[1]))

    def start(self):
        if _UdpAdapter._UDPSENDER == None:
            from freetime.core.protocol import FTUDPSenderProtocol
            _UdpAdapter._UDPSENDER = FTUDPSenderProtocol()
            reactor.listenUDP(0, _UdpAdapter._UDPSENDER)

    def isOK(self):
        return _UdpAdapter._UDPSENDER != None

    @staticmethod
    def packDatas(data, headerDict=None):
        try:
            if isinstance(data, MsgPack):
                data = data.pack()
            elif not isinstance(data, (str, unicode)):
                data = json.dumps(data)
            if headerDict != None:
                lines = []
                for k, v in headerDict.items():
                    lines.append(str(k))
                    lines.append(str(v))
                lines.append(data)
                data = '|'.join(lines)
            return data
        except:
            if _DEBUG:
                debug('ERROR !! can not pack data of ->', data, headerDict)

    def send(self, data, headerDict=None):
        if _UdpAdapter._UDPSENDER and self.toAddress:
            data = _UdpAdapter.packDatas(data, headerDict)
            if data:
                _UdpAdapter._UDPSENDER.sendTo(data, self.toAddress)

    def close(self):
        self.toAddress = None


class _TcpAdapter():
    class TcpHea4Protocol(protocol.Protocol):

        _buffer = b""

        def connectionMade(self):
            pass

        def connectionLost(self, reason):
            pass

        def clearLineBuffer(self):
            b = self._buffer
            self._buffer = ""
            return b

        def dataReceived(self, data):
            self._buffer = self._buffer + data
            dlen = len(self._buffer)
            while dlen > 4:
                mlen = self._buffer[0:4]
                try:
                    mlen = int(mlen, 16)
                except:
                    self.transport.loseConnection()
                    return
                if dlen < mlen + 4:
                    return
                line = self._buffer[:mlen + 4]
                self._buffer = self._buffer[mlen + 4:]
                self.lineReceived(line)
                dlen = len(self._buffer)

        def lineReceived(self, data):
            pass

        def writeData(self, data):
            if not data:
                msg = '0000'
            else:
                msg = '%04X' % len(data) + data
            self.transport.write(msg)

    @staticmethod
    def connect(ip, port, owner):
        class MyProtocol(_TcpAdapter.TcpHea4Protocol):
            def connectionMade(self):
                if _DEBUG:
                    debug('clinets TcpHea4Protocol connectionMade !', self)
                owner.protocol = self

            def connectionLost(self, reason):
                if _DEBUG:
                    debug('clinets TcpHea4Protocol connectionLost !', self)
                owner.protocol = None

        factory = FTReconnectFactory()
        factory.protocol = MyProtocol
        owner.factory = factory
        reactor.connectTCP(ip, port, factory)

    def __init__(self, tcppath, timeout, retryCount):
        self.timeout = timeout  # HOW TODO ? TCP发送超时和重试机制,需要制定QUERY模式
        self.retryCount = retryCount
        datas = tcppath[7:].split(':')
        self.ip = datas[0]
        self.port = int(datas[1])
        self.protocol = None
        self.factory = None

    def start(self):
        _TcpAdapter.connect(self.ip, self.port, self)

    def isOK(self):
        return self.factory != None and self.protocol != None

    def send(self, data, headerDict=None):
        if self.protocol:
            data = _UdpAdapter.packDatas(data, headerDict)
            if data:
                self.protocol.writeData(data)

    def close(self):
        if self.factory:
            try:
                self.factory.stopTrying()
            except:
                ftlog.error()
            self.factory = None

        if self.protocol:
            try:
                self.protocol.transport.abortConnection()
            except:
                ftlog.error()
            self.protocol = None


_clietnsmap = {}


def resetAdapters(adapterKey, newConfig):
    if _DEBUG:
        debug('resetAdapters->', adapterKey, newConfig)
    if adapterKey in _clietnsmap:
        clientinfos = _clietnsmap[adapterKey]
    else:
        clientinfos = {'config': None,
                       'adapters': None,
                       'sendcount': 0}
        _clietnsmap[adapterKey] = clientinfos

    oldConfig = clientinfos['config']
    oldAdapters = clientinfos['adapters']

    if newConfig == oldConfig:
        return

    timeout = newConfig.get('timeout', 5)
    retryCount = newConfig.get('retryCount', 0)
    newAdapters = []
    for addres in newConfig.get('address', []):
        if addres.find('http://') == 0:
            newAdapters.append(_HttpAdapter(addres, timeout, retryCount))
        elif addres.find('tcp4://') == 0:
            newAdapters.append(_TcpAdapter(addres, timeout, retryCount))
        elif addres.find('udpj://') == 0:
            newAdapters.append(_UdpAdapter(addres, timeout, retryCount))
        else:
            raise Exception('not know Adapter address !' + str(addres))
    FTLoopTimer(1, 0, _startAdapter, adapterKey, newAdapters, newConfig, oldAdapters, oldConfig).start()


def _closeAllAdapter(adapters):
    if adapters:
        for ad in adapters:
            ad.close()


def _startAdapter(adapterKey, newAdapters, newConfig, oldAdapters, oldConfig):
    if _DEBUG:
        debug('_startAdapter !', adapterKey)
    if newAdapters:
        for ad in newAdapters:
            ad.start()
        FTLoopTimer(1, 0, _checkAdapter, adapterKey, newAdapters, newConfig, oldAdapters, oldConfig, 1).start()
        if _DEBUG:
            debug('_startAdapter wait connect', adapterKey)
    else:
        if _DEBUG:
            debug('_startAdapter close all', adapterKey)
        _closeAllAdapter(oldAdapters)
        if adapterKey in _clietnsmap:
            del _clietnsmap[adapterKey]


def _checkAdapter(adapterKey, newAdapters, newConfig, oldAdapters, oldConfig, checkcount):
    if _DEBUG:
        debug('_checkAdapter', adapterKey, checkcount)
    isOK = 1
    for ad in newAdapters:
        if not ad.isOK():
            isOK = 0
    if _DEBUG:
        debug('_checkAdapter isOK=', isOK, adapterKey)
    if isOK:
        if _DEBUG:
            debug('all Adapter isOK !!, checkcount=', checkcount, adapterKey)
        _clietnsmap[adapterKey] = {'config': newConfig,
                                   'adapters': newAdapters,
                                   'sendcount': 0}
        _closeAllAdapter(oldAdapters)
    else:
        if checkcount > 5:
            _closeAllAdapter(newAdapters)
            ftlog.error('new Adapters timeout !!!', adapterKey)
            # FTLoopTimer(1, 0, _startAdapter, adapterKey, newAdapters, newConfig, oldAdapters, oldConfig).start()
        else:
            if _DEBUG:
                debug('not all Adapter isOK, checkcount=', checkcount, adapterKey)
            FTLoopTimer(1, 0, _checkAdapter, adapterKey, newAdapters, newConfig, oldAdapters, oldConfig,
                        checkcount + 1).start()


def sendToAdapter(adapterKey, dictData, headerDict=None):
    if adapterKey in _clietnsmap:
        clientinfos = _clietnsmap[adapterKey]
        adapters = clientinfos.get('adapters', None)
        sendcount = clientinfos.get('sendcount', 0)
        if adapters:
            ad = adapters[sendcount % len(adapters)]
            ad.send(dictData, headerDict)
            clientinfos['sendcount'] += 1


def isEnabled(adapterKey):
    if adapterKey in _clietnsmap:
        clientinfos = _clietnsmap[adapterKey]
        adapters = clientinfos.get('adapters', None)
        if adapters:
            return 1
    return 0
