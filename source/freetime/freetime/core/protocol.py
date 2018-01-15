# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.3.28

import array
import base64
import hashlib
import os
import random
import socket
import struct
import zlib

import twisted.web.http
from datetime import datetime
from twisted.internet import defer
from twisted.internet import protocol, reactor
from twisted.internet.protocol import DatagramProtocol
from twisted.protocols.basic import LineReceiver
from twisted.python import failure

import freetime.util.encry as ftenc
import freetime.util.log as ftlog
from tasklet import FTTasklet


class FTTimeoutException(Exception):
    pass


_COUNT_PPS = 0
_COUNT_COUNT = 0
_COUNT_TIME = datetime.now()
_COUNT_PACKS = {}


def _countProtocolPack(ptype, proto, count_block=10000):
    try:
        global _COUNT_COUNT, _COUNT_TIME, _COUNT_PACKS, _COUNT_PPS
        if not _COUNT_PPS:
            return
        ckey = getattr(proto, '_count_key_', None)
        if ckey == None:
            if ptype == 1:  # tcp
                host = proto.transport.getHost()
                ckey = str(host.host) + ':' + str(host.port)
            elif ptype == 2:  # udp
                host = proto.transport.getHost()
                ckey = str(host.host) + ':' + str(host.port)
            elif ptype == 3:  # http
                host = proto.transport.getHost()
                ckey = str(host.host) + ':' + str(host.port)
            else:
                ckey = 'other'
            # ckey = ckey + ':' + str(proto)
            setattr(proto, '_count_key_', ckey)

        if not ckey in _COUNT_PACKS:
            _COUNT_PACKS[ckey] = 0
        _COUNT_PACKS[ckey] += 1

        _COUNT_COUNT += 1
    # if _COUNT_COUNT % count_block == 0:
    #             ct = datetime.now()
    #             dt = ct - _COUNT_TIME
    #             dt = dt.seconds + dt.microseconds / 1000000.0
    #             pps = '%0.2f' % (count_block / dt)
    #             _COUNT_TIME = ct
    #             plist = []
    #             for k, v in _COUNT_PACKS.items():
    #                 plist.append('%s=%0.2f|%d' % (k, v / dt, v))
    #             _COUNT_PACKS = {}
    #             ftlog.info("PPS", pps, 'TASKCOUNT', FTTasklet.concurrent_task_count, 'DT %0.2f' % (dt),
    #                        'TASKPEAK', FTTasklet.PEAKVALUE, 'PEAKTIME', FTTasklet.PEAKTIME.strftime('%m-%d %H:%M:%S'),
    #                        'ALLCOUNT', _COUNT_COUNT, 'PROTS', plist)
    except:
        ftlog.error()


def ppsCountProtocolPack():
    global _COUNT_COUNT, _COUNT_TIME, _COUNT_PACKS
    ct = datetime.now()
    dt = ct - _COUNT_TIME
    dt = dt.seconds + dt.microseconds / 1000000.0
    pps = '%0.2f' % (_COUNT_COUNT / dt)
    plist = []
    for k, v in _COUNT_PACKS.items():
        plist.append('%s=%0.2f|%d' % (k, v / dt, v))
    plist = ','.join(plist)

    ftlog.hinfo("NET_PPS", pps, 'TASKCOUNT', FTTasklet.concurrent_task_count, 'DT %0.2f' % (dt),
                'TASKPEAK', FTTasklet.PEAKVALUE, 'PEAKTIME', FTTasklet.PEAKTIME.strftime('%m-%d %H:%M:%S'),
                'ALLCOUNT', _COUNT_COUNT, 'PROTS', plist)
    _COUNT_TIME = ct
    _COUNT_PACKS = {}
    _COUNT_COUNT = 0


class FTProtocolBase(object):
    """
    FreeTime协议的公共抽象，封装了“为每个请求派生一个tasklet”的机制

    定义了lostHandler和madeHandler接口,用于实现建立连接和连接丢失的处理逻辑
    (对于udp协议，startProtocol和stopProtocol时触发)

    定义了getTaskletFunc接口，业务逻辑层通过这个接口管理消息和消息处理函数
    的映射,框架会传入启动tasklet时的参数字典，业务逻辑层通过这些参数分配合
    适的tasklet方法，可以实现诸如消息注册等方式

    定义了parseData接口，用于实现解析网络原始包，解析后的pack后续
    可以通过ftsvr.getTaskPack()得到
    对于格式非法的数据，parseData需要返回None

    另外，还实现了请求包个数和每秒处理包速度PPS等基本统计功能
    """

    def lostHandler(self, reason):
        raise NotImplementedError('TCP protocol should create lostHandler')

    def madeHandler(self):
        raise NotImplementedError('Should create the method function')

    def getTaskletFunc(self, pack):
        raise NotImplementedError('Should create the method function')

    def parseData(self, data):
        return data

    def closeConnection(self, isabort=0):
        try:
            if isabort:
                self.transport.abortConnection()
            else:
                self.transport.loseConnection()
        except:
            pass

    def _runTasklet(self, *argl, **argd):
        try:
            # Call user defined parseData method...
            data = argd["data"]
            pack = self.parseData(data)
            if pack == None:
                ftlog.error("_runTasklet: can't parseData received(%s....)" % data[0:64])
                return
            argd["pack"] = pack

            # Call user defined getTaskletFunc...
            taskf = self.getTaskletFunc(argd)
            if taskf == None:
                ftlog.error("_runTasklet: can't find tasklet func by pack:(%r....)" % pack[0:64])
                return
            argd["handler"] = taskf

            # Create and run tasklet...
            FTTasklet.create(argl, argd)
        except:
            ftlog.error()


class _SocketOpt():
    """
    常用socket设置
    """
    UDP_BUFFER_SIZE = 2 * 1024 * 1024
    TCP_LINE_MAX_LENGTH = 1024 * 63

    @classmethod
    def udp(cls, p):
        sock = p.transport.getHandle()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, cls.UDP_BUFFER_SIZE)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, cls.UDP_BUFFER_SIZE)

    @classmethod
    def tcp(cls, p):
        try:
            p.MAX_LENGTH = _SocketOpt.TCP_LINE_MAX_LENGTH
        except:
            ftlog.error()
        try:
            p.transport.setTcpNoDelay(1)
        except:
            ftlog.error()
        try:
            p.transport.setTcpKeepAlive(1)
        except:
            ftlog.error()
        try:
            p.transport.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 180)
        except:
            ftlog.error()
        try:
            p.transport.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 30)
        except:
            ftlog.error()
        try:
            p.transport.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 10)
            # p.transport.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 128*1024)
        except:
            ftlog.error()


class FTUDPSenderProtocol(DatagramProtocol, FTProtocolBase):
    def startProtocol(self):
        _SocketOpt.udp(self)

    def datagramReceived(self, data, address):
        pass

    def sendTo(self, data, toAddress):
        self.transport.write(data, toAddress)


class FTUDPServerProtocol(DatagramProtocol, FTProtocolBase):
    def startProtocol(self):
        _SocketOpt.udp(self)
        self.madeHandler()

    def stopProtocol(self):
        self.lostHandler(None)

    def datagramReceived(self, data, address):
        _countProtocolPack(2, self)
        self._runTasklet(data=data, udpsrc=address)


class FTUDPQueryProtocol(DatagramProtocol, FTProtocolBase):
    QUERYID = 0

    def __init__(self, dsthost, dstport):
        self.dsthost = dsthost
        self.dstport = dstport

    def startProtocol(self):
        _SocketOpt.udp(self)
        self.live_msg_map = {}

    def stopProtocol(self):
        self.live_msg_map = {}

    def datagramReceived(self, data, address):
        try:
            i = data.find('|', 0, 16)
            qid = int(data[0:i])
            ftlog.debug("udp query receive:", qid, data)
            if qid in self.live_msg_map:
                d, c = self.live_msg_map[qid]
                del self.live_msg_map[qid]
                c.cancel()
                d.callback(data)
            else:
                ftlog.error('udp response msg id not in live table:', data[0:64], '....')
        except:
            ftlog.error()

    def query(self, data, timeout=1):
        try:
            FTUDPQueryProtocol.QUERYID += 1
            self.transport.write(str(FTUDPQueryProtocol.QUERYID) + '|' + data, (self.dsthost, self.dstport))
            resultDeferred = defer.Deferred()
            cancelCall = reactor.callLater(timeout, self._clearFailed, resultDeferred, FTUDPQueryProtocol.QUERYID)
            self.live_msg_map[FTUDPQueryProtocol.QUERYID] = (resultDeferred, cancelCall)
            return resultDeferred
        except:
            ftlog.error()
        return None

    def _clearFailed(self, deferred, mid):
        try:
            del self.live_msg_map[mid]
        except KeyError:
            pass
        deferred.errback(failure.Failure(FTTimeoutException(str(mid))))


class FTTCPServerProtocol(LineReceiver, FTProtocolBase):
    def connectionMade(self):
        _SocketOpt.tcp(self)
        self.madeHandler()

    def connectionLost(self, reason):
        self.lostHandler(reason)

    def lineReceived(self, data):
        _countProtocolPack(1, self)
        self._runTasklet(data=data)

    def lineLengthExceeded(self, line):
        super(FTTCPServerProtocol, self).lineLengthExceeded(line)
        ftlog.error('the FTTCPServerProtocol lineLengthExceeded ERROR !!')


class FTZipEncryServerProtocol(protocol.Protocol, FTProtocolBase):
    """
    一个压缩加密的tcp协议基类
    客户端建立连接后，首先回应一个%04X的随机数作为种子
    然后双方会使用（种子+长度）对数据加密压缩，然后用"%04X%s"%(len, data)的格式交换数据
    加密算法用cffi实现
    """

    _buffer = b""

    def connectionMade(self):
        ftlog.debug('zipsocket: connectionMade')
        _SocketOpt.tcp(self)
        self.encry_seed = random.randint(100, 0xfffE)
        self.transport.write("%04x" % self.encry_seed)
        self.madeHandler()

    def connectionLost(self, reason):
        self.lostHandler(reason)

    def _encode(self, src):
        if not src:
            return '0000'
        zsrc = zlib.compress(src)
        dlen = len(zsrc)
        return '%04X' % dlen + ftenc.code(self.encry_seed + dlen, zsrc)

    def _decode(self, dst):
        #         return zlib.decompress(ftenc.code(self.encry_seed + int(dst[:4], 16), dst[4:]))
        return ftenc.code(self.encry_seed + int(dst[:4], 16), dst[4:])

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
            why = self.lineReceived(line)
            if why or self.transport and self.transport.disconnecting:
                return why
            dlen = len(self._buffer)

    def lineReceived(self, data):
        _countProtocolPack(2, self)
        data = self._decode(data)
        self._runTasklet(data=data)


class FTHead4ServerProtocol(protocol.Protocol, FTProtocolBase):
    """
    一个tcp协议基类, 4字节的数据长度+数据体
    """

    _buffer = b""

    def connectionMade(self):
        _SocketOpt.tcp(self)
        self.madeHandler()

    def connectionLost(self, reason):
        self.lostHandler(reason)

    def _encode(self, src):
        if not src:
            return '0000'
        zsrc = zlib.compress(src)
        dlen = len(zsrc)
        return '%04X' % dlen + ftenc.code(self.encry_seed + dlen, zsrc)

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
        _countProtocolPack(2, self)
        self._runTasklet(data=data)


class FTWebSocketServerProtocol(protocol.Protocol, FTProtocolBase):
    """
    WebSocket加密的tcp协议基类
    客户端建立连接后，首先回应一个%04X的随机数作为种子
    """

    _buffer = b""
    isNewVersion = True
    handshaken = False

    def connectionMade(self):
        # if self.handshaken:
        #     return
        ftlog.debug('websocket: connectionMade')
        _SocketOpt.tcp(self)
        # self.encry_seed = random.randint(100, 0xfffE)
        # self.transport.write("%04x" % self.encry_seed)
        self.madeHandler()

    def connectionLost(self, reason):
        ftlog.debug('websocket: connectionLost', reason)
        self.lostHandler(reason)
        self.handshaken = False

    def _encode(self, src):
        # zsrc = zlib.compress(src)
        # dlen = len(zsrc)
        # return '%04X' % dlen + ftenc.code(self.encry_seed + dlen, zsrc)
        if not src:
            src = '0000'

        src = self.encode_message(src)
        if self.isNewVersion:
            back_str = []
            back_str.append('\x81')
            data_length = len(src)

            if data_length <= 125:
                back_str.append(chr(data_length))
            else:
                back_str.append(chr(126))
                back_str.append(chr(data_length >> 8))
                back_str.append(chr(data_length & 0xFF))

            send_data = ''.join(back_str) + src
            ftlog.debug('websocket: -------send isWebsocketNewVersion=True data:----------', send_data)
            return send_data
        else:
            back_str = '\x00%s\xFF' % (src)
            ftlog.debug('websocket: --------send isWebsocketNewVersion=False data:-----------')
        return back_str

    def encode_message(self, src):
        if self.userId and self.userId < 10000:
            return src
        mask_key = os.urandom(4)
        src = mask_key + self.mask_message(mask_key, src)
        src = base64.b64encode(src)
        return src

    def mask_message(self, mask_key, data):
        """
        mask or unmask data. Just do xor for each byte
        mask_key: 4 byte string(byte).
        data: data to mask/unmask.
        """
        if data is None:
            data = ""
        _m = array.array("B", mask_key)
        _d = array.array("B", data)
        for i in range(len(_d)):
            _d[i] ^= _m[i % 4]
        return _d.tostring()

    def _decode(self, dst):
        # return ftenc.code(self.encry_seed + int(dst[:4], 16), dst[4:])
        return dst

    def clearLineBuffer(self):
        b = self._buffer
        self._buffer = ""
        return b

    def dataReceived(self, data):
        ftlog.debug('websocket: handshaken', self.handshaken)
        if not self.handshaken:
            self.handshaken = True
            if data.lower().find('upgrade: websocket') != -1:
                ftlog.debug('websocket:: -------------start run handshake------')
                # self.isWebsocketTcp = True
                self.on_handshake(data)
                return
        self._buffer = self._buffer + data
        dlen = len(self._buffer)
        if dlen <= 4:
            return
        rawStr = ''
        ftlog.debug('websocket:: -------------received buffer:------', self._buffer)
        if self.isNewVersion:
            indexN = 0
            msgLen = len(self._buffer)
            while indexN < msgLen:
                rawStr = ''
                packMsg = self._buffer[indexN:]
                dataLen = 0
                pastLen = 0
                data = ''
                codeLength = ord(packMsg[1]) & 127
                if codeLength == 126:
                    # ftlog.debug('websocket:: packMsg[2:4]---', packMsg[2:4])
                    dataLen, = struct.unpack('!H', packMsg[2:4])
                    pastLen = dataLen + 8
                    masks = packMsg[4:8]
                    data = packMsg[8:]
                elif codeLength == 127:
                    # ftlog.debug('websocket:: packMsg[2:10]---', packMsg[2:10])
                    dataLen, = struct.unpack('!Q', packMsg[2:10])
                    pastLen = dataLen + 14
                    masks = packMsg[10:14]
                    data = packMsg[14:]
                else:
                    dataLen = codeLength
                    pastLen = dataLen + 6
                    masks = packMsg[2:6]
                    data = packMsg[6:]
                i = 0
                for d in data:
                    if i >= dataLen:
                        break
                    rawStr += chr(ord(d) ^ ord(masks[i % 4]))
                    i += 1
                try:
                    ftlog.debug('websocket:: -------------received data:------', dataLen, rawStr)
                except:
                    pass
                if rawStr:
                    self.lineReceived(rawStr)
                indexN += pastLen
        else:
            rawStrArray = self._buffer.split("\xFF")
            for tempData in rawStrArray:
                rawStr = tempData[1:]
                ftlog.debug('websocket old: -------------received data:------', rawStr)
                if rawStr:
                    self.lineReceived(rawStr)
        self._buffer = ''

    def lineReceived(self, data):
        _countProtocolPack(2, self)
        ftlog.debug('websocket: lineReceived', data)
        data = self._decode(data)
        ftlog.debug('websocket: lineReceived decode', data)
        self._runTasklet(data=data)

    def on_handshake(self, msg):
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

            token = self.h5_generate_token(key1, key2, key3)

            handshake = '\
HTTP/1.1 101 Web Socket Protocol Handshake\r\n\
Upgrade: WebSocket\r\n\
Connection: Upgrade\r\n\
Sec-WebSocket-Origin: %s\r\n\
Sec-WebSocket-Location: %s\r\n\r\n\
' % (headers['Origin'], headers['Location'])

            self.transport.write(handshake + token)

            self.isNewVersion = False
            ftlog.debug('websocket: -------------send hand data:------isWebsocketNewVersion:False')
        else:
            key = headers['Sec-WebSocket-Key']
            token = self.h5_generate_token2(key)

            handshake = '\
HTTP/1.1 101 Switching Protocols\r\n\
Upgrade: WebSocket\r\n\
Connection: Upgrade\r\n\
Sec-WebSocket-Accept: %s\r\n\r\n\
' % (token)
            self.transport.write(handshake)
            self.isNewVersion = True
            ftlog.debug('websocket: -------------send hand data:------isWebsocketNewVersion:True')

    def h5_generate_token(self, key1, key2, key3):
        num1 = int("".join([digit for digit in list(key1) if digit.isdigit()]))
        spaces1 = len([char for char in list(key1) if char == " "])
        num2 = int("".join([digit for digit in list(key2) if digit.isdigit()]))
        spaces2 = len([char for char in list(key2) if char == " "])

        combined = struct.pack(">II", num1 / spaces1, num2 / spaces2) + key3
        return hashlib.md5(combined).digest()

    def h5_generate_token2(self, key):
        key = key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        serKey = hashlib.sha1(key).digest()
        return base64.b64encode(serKey)


class FTHttpRequest(twisted.web.http.Request, FTProtocolBase):
    def process(self):
        try:
            _countProtocolPack(2, self, 1000)
            self._runTasklet(data=self)
        except:
            ftlog.error()

    def getTaskletFunc(self, pack):
        return self.handleRequest

    def handleRequest(self):
        raise NotImplementedError('Should override handleRequest')


class FTHttpChannel(twisted.web.http.HTTPChannel):
    requestFactory = FTHttpRequest
