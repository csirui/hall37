# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import random

from freetime.entity.msg import MsgPack
from freetime.util import log as ftlog
from poker.entity.configure import gdata, configure
from poker.entity.dao import userchip, daoconst
from poker.entity.robot.robotprotocol import RobotClientProtocol

try:
    from poker.entity.robot.robotprotocol_ws import WebSocketRobotClientProtocol
except:
    pass
from poker.util import strutil, webpage

CMD_LOGIN = 0
CMD_TCP_CONNECTED = 1
CMD_BIND_USER = 2
CMD_GANEDATA_9999 = 3
CMD_GANEDATA_CUR_GAMEID = 4
CMD_QUICK_START = 5
CMD_READY = 6
CMD_GAME_READY = 7
CMD_GAME_START = 9
CMD_GAME_WINLOSE = 10
CMD_TCP_CLOSED = 11

from autobahn.twisted.websocket import WebSocketClientFactory


class H5WebSocketClientFactory(WebSocketClientFactory):
    def startedConnecting(self, connector):
        pass


class RobotUser(object):
    TCPSRV = None

    def __init__(self, clientId, snsId, name):
        self.clientId = clientId if clientId != None else configure.CLIENTID_ROBOT
        self.snsId = snsId
        self.name = name
        self.protocol = None
        self.responseDelaySecond = -1
        self.stop()

    def getResponseDelaySecond(self):
        roomConf = gdata.roomIdDefineMap()[self.roomId].configure
        robotUserOpTime = roomConf.get('robotUserOpTime', None)
        if robotUserOpTime:
            return random.randint(int(min(robotUserOpTime)), int(max(robotUserOpTime)))
        if self.responseDelaySecond < 0:
            delay = 0
        else:
            delay = random.randint(0, self.responseDelaySecond)  # 随机延迟进入
        return delay

    @property
    def msgQueue(self):
        return self._msgQueue

    def doShutDown(self):
        self.stop()
        pass

    def stop(self):
        ftlog.info('!! close robot of->', self.snsId)
        if self.protocol:
            self.protocol.closeConnection(1)
            self.protocol.robotUser = None
            self.protocol = None
        self.isbusy = 0
        self.gameId = 0
        self.roomId = 0
        self.tableId = 0
        self.seatId = 0
        self.userId = 0
        self.userInfo = {}
        self.gameData = {}
        self.gameData9999 = {}
        self._msgQueue = []
        self._delayWrite = []
        self._state = {}
        self._isMatch = False

    def start(self, roomId, tableId, isMatch=False):
        gameId = 0
        bigRoomId = gdata.getBigRoomId(roomId)
        if bigRoomId == roomId:
            gameId = strutil.getGameIdFromBigRoomId(bigRoomId)
        else:
            gameId, _, _, _ = strutil.parseInstanceRoomId(roomId)
        self.gameId = gameId
        self.roomId = roomId
        self.tableId = tableId
        ftlog.info('robot start', self.snsId, self.roomId, self.tableId, caller=self)
        self._isMatch = isMatch
        self._start()
        try:
            self._doLogin()
            if self.isbusy == 0:  # 已经关闭
                return
            self._doConnTcp()
            if self.isbusy == 0:  # 已经关闭
                return
        except:
            ftlog.error('robot start error %s %s %s' % (self.snsId, roomId, tableId))
            self.stop()

    def _start(self):
        pass

    def _doLogin(self):
        loginur = gdata.httpSdkInner() + '/open/v3/user/processSnsId'
        params = {'svninfo': '$robot$',
                  'appId': str(self.gameId),
                  'ty_bindmobile': '',
                  'phoneType': '',
                  'imei': ['Xb6tiNAVcw5eLrd1F4JTW2dnDrGNr3P0EXl2x99NUeVYGHCQB6ECeQ=='],
                  'iccid': ['RcjQJPkcLGfazgYaKJGWd8hTMfWp8OVr86NEoHuo1C0fIaCKUsTAhuB7huInoqWf'],
                  'androidId': ['BwyJv/PH1UCPjZDob4BSPgiwpuTq4dYgt1OFMrAoLJTED4oxlxdnEtuXKiOJxpkV'],
                  'snsToken': '',
                  'mac': ['wn+rGmlh6/AG6S6O+7kew0ZaMHsfR0LstUtr/WOvXtX681nrM5c+406L0PvY3P7W'],
                  'ty_uid': '0',
                  'clientId': self.clientId,
                  'deviceName': self.name,
                  'snsId': strutil.tyDesEncode(self.snsId),
                  'deviceId': ''
                  }
        sigstr = ''
        pkeys = params.keys()
        pkeys.sort()
        for k in pkeys:
            sigstr = sigstr + str(k) + '=' + str(params[k]) + '&'
        sigstr = sigstr[:-1]
        code = strutil.md5digest(strutil.tyDesEncode(sigstr))
        params['code'] = code

        userInfo, _ = webpage.webget(loginur, params)
        userInfo = strutil.loads(userInfo, ignoreException=True, execptionValue=userInfo)
        if not isinstance(userInfo, dict):
            ftlog.warn('snsId=', self.snsId, 'login-> return error !', userInfo)
            self.stop()
            return
        if self.isbusy == 0:  # 已经关闭
            return

        ftlog.debug('snsId=', self.snsId, 'login->', userInfo)

        result = userInfo.get('result', {})
        self.userId = result.get('userId', 0)
        if not isinstance(self.userId, int) or self.userId < 0:
            raise Exception('robot user login false !' + self.snsId)
        ftlog.debug('Robot login ok snsId=', self.snsId, 'userId=', self.userId)
        self.userInfo = result
        self.checkState(CMD_LOGIN)

    def _makeRoboProtocloWs(self):
        p = WebSocketRobotClientProtocol(self)
        self.protocol = p
        return p

    def _makeRoboProtoclo(self):
        p = RobotClientProtocol(self)
        self.protocol = p
        return p

    def _createClientFactory(self, tcpip=None, tcpport=None):
        import freetime.entity.config as ftconfig
        if ftconfig.global_config.get('is_h5', 0):
            #             from autobahn.twisted.websocket import WebSocketClientFactory
            #             factory = WebSocketClientFactory("ws://" + tcpip + ":" + str(tcpport), debug=True)
            factory = H5WebSocketClientFactory("ws://" + tcpip + ":" + str(tcpport), debug=True)
            factory.protocol = self._makeRoboProtocloWs
            return factory
        else:
            from twisted.internet.protocol import ClientFactory
            factory = ClientFactory()
            factory.protocol = self._makeRoboProtoclo
            return factory

    def _doConnTcp(self):
        tcpsrv = self.userInfo['tcpsrv']
        ftlog.debug('_doConnTcp->', tcpsrv)
        from twisted.internet import reactor
        factory = self._createClientFactory(tcpsrv['ip'], tcpsrv['port'])
        reactor.connectTCP(tcpsrv['ip'], tcpsrv['port'], factory)

    def _onTimer(self, event):
        pass

    def onTimer(self, event):
        if self.isbusy == 0:  # 已经关闭
            return
        dws = []
        dwq = []
        for x in xrange(len(self._delayWrite)):
            dw = self._delayWrite[x]
            dw[0] = dw[0] - 1
            if dw[0] <= 0:
                dws.append(dw[1])
            else:
                dwq.append(dw)
        self._delayWrite = dwq
        self._onTimer(event)
        # 执行延迟时间到时的发送消息
        for msg in dws:
            try:
                self.writeMsg(msg)
            except:
                ftlog.error()
                self.stop()
                return

        # 执行延迟时间到时的事件
        mqueue = self._msgQueue
        ftlog.debug('timer hc=', event.count, 'len(mqueue)=', len(mqueue))
        if len(mqueue) > 0:
            self._msgQueue = []
            for msg in mqueue:
                self.onMsg(msg)
                if not self.isbusy:
                    return

    def writeDelayMsg(self, delay, msg):
        self._delayWrite.append([delay, msg])

    def writeMsg(self, msg):
        if ftlog.is_debug():
            ftlog.debug('msg:', msg, caller=self)
        if self.protocol:
            self.protocol.writeMsg(msg)

    def checkState(self, state):
        if self._state.get(state, 0) != 1:
            self._state[state] = 1
            return 1
        return 0

    def getState(self, state):
        return self._state.get(state, 0)

    def cleanState(self, *stateList):
        for s in stateList:
            if s in self._state:
                del self._state[s]

    def onMsgLogin(self, msg):
        ftlog.debug('RobotUser.onMsgLogin snsId=', self.snsId, 'msg->', msg)
        cmd = msg.getCmd()

        if cmd == '_tcp_closed_':
            self.stop()
            return 1

        if cmd == '_tcp_conneted_':
            if self.checkState(CMD_TCP_CONNECTED):
                mo = MsgPack()
                mo.setCmd('bind_user')
                mo.setParam('userId', self.userId)
                mo.setParam('gameId', 9999)
                mo.setParam('clientId', self.clientId)
                self.writeMsg(mo)
            return 1

        if cmd == 'user_info':  # bind_user 命令返回结果
            if self.checkState(CMD_BIND_USER):
                mo = MsgPack()
                mo.setCmdAction('game', 'enter')
                mo.setParam('userId', self.userId)
                mo.setParam('gameId', 9999)
                mo.setParam('clientId', self.clientId)
                self.writeMsg(mo)
            return 1

        # game#enter 9999 命令返回结果
        if cmd == 'game_data' and msg.getResult('gameId') == 9999:
            self.gameData9999 = msg.getKey('result')
            if self.checkState(CMD_GANEDATA_9999):
                mo = MsgPack()
                mo.setCmdAction('game', 'enter')
                mo.setParam('userId', self.userId)
                mo.setParam('gameId', self.gameId)
                mo.setParam('clientId', self.clientId)
                self.writeMsg(mo)
            return 1

        # game#enter DIZHU_GAMEID 命令返回结果
        if cmd == 'game_data' and msg.getResult('gameId') == self.gameId:
            self.gameData = msg.getKey('result')
            if self.checkState(CMD_GANEDATA_CUR_GAMEID):
                return 2
            return 1
        return 0

    def onMsg(self, msg):
        if self.isbusy == 0:  # 已经关闭
            return
        # 登录, TCP接入和链接处理, 直到成功接收 gamedata为止
        ret = self.onMsgLogin(msg)
        ftlog.debug('RobotUser.onMsgLoginRet snsId=', self.snsId, 'ret=', ret, 'msg->', msg)
        if ret == 2:
            self.onMsgTableBegin()
            return
        elif ret == 1:
            return
        else:
            self.onMsgTablePlay(msg)

    def onMsgTableBegin(self):
        ftlog.debug('RobotUser.doBeginQuickStart begin')

    def onMsgTablePlay(self, msg):
        ftlog.debug('RobotUser.onMsgTablePlay snsId=', self.snsId, 'msg->', msg)

    def adjustChip(self, minCoin=None, maxCoin=None):
        if not isinstance(minCoin, int) or not isinstance(maxCoin, int) \
                or minCoin < 0 or maxCoin < 0 or minCoin >= maxCoin:
            roomDef = gdata.roomIdDefineMap()[self.roomId]
            roomConf = roomDef.configure
            maxCoin = roomConf['maxCoin']
            minCoin = roomConf['minCoin']
            maxCoin = maxCoin if maxCoin > 0 else minCoin + 100000

        uchip = userchip.getChip(self.userId)
        ftlog.debug('adjustChip->userId, uchip, minCoin, maxCoin =', self.snsId, self.userId, uchip, minCoin, maxCoin)
        if uchip < minCoin or uchip > maxCoin:
            nchip = random.randint(minCoin + 1, minCoin + 1000)
            dchip = nchip - uchip
            trueDelta, finalCount = userchip.incrChip(self.userId, self.gameId, dchip,
                                                      daoconst.CHIP_NOT_ENOUGH_OP_MODE_NONE,
                                                      'SYSTEM_ADJUST_ROBOT_CHIP',
                                                      self.roomId, self.clientId)
            ftlog.debug('adjustChip->userId, trueDelta, finalCount=', self.snsId, self.userId, trueDelta, finalCount)
