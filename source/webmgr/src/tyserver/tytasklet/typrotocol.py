# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from datetime import  datetime
import hashlib, struct, base64
from struct import pack, unpack

from twisted.internet.protocol import Factory, Protocol
import twisted.web.http

from tyserver.tycmds.runhttp import handlerHttpRequest
from tyserver.tycmds.runws import handlerWsRequest
from tyserver.tytasklet.tytasklet import TyTasklet
from tyserver.tyutils import tylog
from tyserver.tyutils.msg import MsgPack


class TyProtocolBase(object):
    PACK_COUNT = 0
    PACK_TIME = datetime.now()

    def lostHandler(self, reason):
        raise NotImplementedError('TCP protocol should create lostHandler')


    def madeHandler(self):
        raise NotImplementedError('Should create the method function')


    def getTaskletFunc(self, pack):
        raise NotImplementedError('Should create the method function')


    def parseData(self, data):
        return data

    
    def _runTasklet(self, *argl, **argd):
        try:
            # Call user defined parseData method...
            data = argd["data"]
            pack = self.parseData(data)
            if pack == None:
                tylog.error("_runTasklet: can't parseData received(%s....)" % data[0:64])
                return
            argd["pack"] = pack

            # Call user defined getTaskletFunc...
            taskf = self.getTaskletFunc(argd)
            if taskf == None:
                tylog.error("_runTasklet: can't find tasklet func by pack:(%r....)" % pack[0:64])
                return
            argd["handler"] = taskf

            # Create and run tasklet...
            TyTasklet.create(argl, argd)
        except:
            tylog.error()


    def _countPack(self):
        self.PACK_COUNT += 1
        if self.PACK_COUNT % 50000 == 0:
            ct = datetime.now()
            dt = ct - self.PACK_TIME
            pps = 50000 / (dt.seconds + dt.microseconds / 1000000.0)
            self.PACK_TIME = ct
            tylog.debug("PPS", pps, TyTasklet.concurrent_task_count)


class TyHttpRequest(twisted.web.http.Request, TyProtocolBase):
    def process(self):
        try:
            self._runTasklet(data=self.path, httprequest=self)
        except:
            tylog.error()


    def getTaskletFunc(self, pack):
        return self.handleRequest


    def handleRequest(self):
        handlerHttpRequest(self)


class TyHttpChannel(twisted.web.http.HTTPChannel):
    requestFactory = TyHttpRequest


class WebSocketProtocol(Protocol, TyProtocolBase):
    def __init__(self, sockets):
        self.sockets = sockets
        self.__buffer = ''
        self.__handsake = 0
        self.__is_new_ver = 0

    def connectionMade(self):
        if not self.sockets.has_key(self):
            self.sockets[self] = {}


    def dataReceived(self, msg):
        if self.__handsake == 0 :
            try:
                self.handShake(msg)
            except:
                tylog.error()
                self.wsClose()
        else:
            try:
                self.__buffer = self.__buffer + msg
                if self.__is_new_ver:
                    self.parseRecvDataNew()
                else:
                    self.parseRecvDataOld()
            except:
                tylog.error()


    def lineReceived(self, raw_str):
        self._runTasklet(data=raw_str, wsprotocol=self)


    def wsClose(self):
        try:
            self.transport.abortConnection()
        except:
            pass


    def parseData(self, data):
        mpack = MsgPack()
        mpack.unpack(data)
        return mpack


    def getTaskletFunc(self, pack):
        return self.handleRequest


    def handleRequest(self):
        handlerWsRequest(self)


    def connectionLost(self, reason):
        if self.sockets.has_key(self):
            del self.sockets[self]


    def generateToken(self, key1, key2, key3):
        num1 = int("".join([digit for digit in list(key1) if digit.isdigit()]))
        spaces1 = len([char for char in list(key1) if char == " "])
        num2 = int("".join([digit for digit in list(key2) if digit.isdigit()]))
        spaces2 = len([char for char in list(key2) if char == " "])

        combined = struct.pack(">II", num1 / spaces1, num2 / spaces2) + key3
        return hashlib.md5(combined).digest()


    def generateToken2(self, key):
        key = key + '765a5a89-e019-4ebf-8918-d4b898137fb3'
        ser_key = hashlib.sha1(key).digest()
        return base64.b64encode(ser_key)


    def sendData(self, raw_str):
        if self.__is_new_ver:
            back_str = []
            back_str.append('\x81')
            data_length = len(raw_str)

            if data_length < 126:
                back_str.append(chr(data_length))
            elif data_length < 65000 :
                back_str.append('~') # chr(126)
                back_str.append(chr(data_length >> 8))
                back_str.append(chr(data_length & 0xFF))
            else:
                raise Exception('can not send websocket package of big than 65000 bytes !')
            back_str = ''.join(back_str) + raw_str
            self.transport.write(back_str)
        else:
            if len(raw_str) < 65000 :
                back_str = '\x00%s\xFF' % (raw_str)
                self.transport.write(back_str)
            else:
                raise Exception('can not send websocket package of big than 65000 bytes !')


    def parseRecvDataNew(self):
        while 1 :
            buf = self.__buffer
            blen = len(buf)
            if blen < 1 :
                return

            code_length = ord(buf[1]) & 127
            if code_length < 126:
                pastLen = code_length + 6
                if blen < pastLen :
                    return
                masks = buf[2:6]
                data = buf[6:pastLen]
            elif code_length == 126:
                if blen < 8 :
                    return
                pastLen = unpack('H', buf[2:4]) + 8
                if blen < pastLen :
                    return
                masks = buf[4:8]
                data = buf[8:pastLen]
            else:
                self.wsClose()
                raise Exception('forbidden access of websocket package of big than 65535 bytes !! ')

            self.__buffer = buf[pastLen:]

            ordmasks = []
            for m in masks :
                ordmasks.append(ord(m))

            i = 0
            raw_strs = []
            for d in data:
                raw_strs.append(chr(ord(d) ^ ordmasks[i % 4]))
                i += 1
            
            if raw_strs:
                raw_str = ''.join(raw_strs)
                self.lineReceived(raw_str)


    def parseRecvDataOld(self):
        while len(self.__buffer) > 0 :
            sbyte = self.__buffer[0]
            if sbyte == '\x00' :
                i = self.__buffer.find('\xFF')
                if i > 1 :
                    raw_str = self.__buffer[1:i]
                    self.__buffer = self.__buffer[i + 1:]
                    if raw_str:
                        self.lineReceived(raw_str)
                else:
                    return
            else:
                return


    def handShake(self, msg):
        self.__handsake = 1
        headers = {}
        header, data = msg.split('\r\n\r\n', 1)
        for line in header.split('\r\n')[1:]:
            key, value = line.split(": ", 1)
            headers[key] = value

        headers["Location"] = "ws://%s/" % headers["Host"]

        if headers.has_key('Sec-WebSocket-Key1'):
            key1 = headers["Sec-WebSocket-Key1"]
            key2 = headers["Sec-WebSocket-Key2"]
            key3 = data[:8]

            token = self.generate_token(key1, key2, key3)

            handshake = '\
HTTP/1.1 101 Web Socket Protocol Handshake\r\n\
Upgrade: WebSocket\r\n\
Connection: Upgrade\r\n\
Sec-WebSocket-Origin: %s\r\n\
Sec-WebSocket-Location: %s\r\n\r\n\
' % (headers['Origin'], headers['Location'])

            self.transport.write(handshake + token)
            self.__is_new_ver = 0
        else:
            key = headers['Sec-WebSocket-Key']
            token = self.generate_token_2(key)
            handshake = '\
HTTP/1.1 101 Switching Protocols\r\n\
Upgrade: WebSocket\r\n\
Connection: Upgrade\r\n\
Sec-WebSocket-Accept: %s\r\n\r\n\
' % (token)
            self.transport.write(handshake)
            self.__is_new_ver = 1


class WebSocketFactory(Factory):
    def __init__(self):
        self.sockets = {}


    def buildProtocol(self, addr):
        return WebSocketProtocol(self.sockets)

