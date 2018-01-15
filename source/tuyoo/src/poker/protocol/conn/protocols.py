# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import json

import freetime.entity.service as ftsvr
import freetime.util.log as ftlog
from freetime.core.protocol import FTZipEncryServerProtocol, \
    FTWebSocketServerProtocol, _countProtocolPack
from freetime.core.tasklet import FTTasklet
from freetime.entity.msg import MsgPack
from freetime.style import ide_debug, ide_print_pack
from freetime.support.tcpagent.protocol import S2AProtocol
from poker.entity.biz import bireport
from poker.entity.configure import gdata, pokerconf
from poker.entity.dao import userdata
from poker.protocol import router, runcmd
from poker.protocol.conn import structProtocolHelper, conn_bridge
from poker.protocol.conn.tcpuser import TcpUser
from poker.util import strutil

ERROR_SYS_LOGOUT_USERID_ERROR = 1  # bind_user命令的userid值错误
ERROR_SYS_LOGOUT_DATASWAP_ERROR = 2  # bind_user命令的userid值错误
ERROR_SYS_LOGOUT_FIRST_CMD_ERROR = 3  # 第一个命令非bind_user
ERROR_SYS_LOGOUT_OTHER_LOGIN = 4  # 同一个账号在不同的地点登录，造成以前的登录退出
ERROR_SYS_LOGOUT_TIME_OUT = 5  # 系统强迫没有客户端心跳的用户退出
ERROR_SYS_LOGOUT_FORCE_LOGOUT = 6  # 管理员强制退出
ERROR_SYS_LOGOUT_CLIENTID_ERROR = 7  # bind_user命令的userid值错误

_ONLINE_USERS = {}  # 所有在线用户的集合, key为int(userId), value为TcpUser
_NEW_PROTOCOLS = {}  # 所有的新建TCP连接, 即刚建立, 但是没有发送bind_user的连接
_MSG_QUEUES = {}
_MSG_QUEUES_MAX_LEN = 60

_HEART_BEAT_MOD = 5  # 客户端发送n个消息, 处理一个
_EMPTY_TCP_CHECK_TIMES = 10  # 每隔n秒检查一次TCP的链接超时
_EMPTY_TCP_TIMEOUT_COUNT = 6  # 未绑定userId的TCP长连接, 若n次检查后, 还没有消息, 那么主动切断链接
_EMPTY_USER_TIMEOUT_COUNT = 6  # 已经绑定userId的TCP长连接, 若n次检查后, 若还未有heart_beat消息上传, 那么主动切断链接

_DISABLE_GAMEIDS = set([])


class COS2AProto(S2AProtocol):
    def getTaskletFunc(self, argd):
        return self.doServerTcpMsg

    def doServerTcpMsg(self):
        '''
        其他服务发送至CONN服务的消息处理 
        绝大部分需要转发至用户客户端
        '''
        args = ftsvr.getTaskRunArg()
        src = args.get('src')
        dst = args.get('dst')
        userheader1 = args.get('userheader1')
        userheader2 = args.get('userheader2')
        msgstr = ftsvr.getTaskPack()
        cmd = strutil.getJsonStr(msgstr, 'cmd', '')

        ftlog.debug('COS2AProto-doServerTcpMsg src=', src, 'dst=', dst, 'h1=', userheader1, 'h2=', userheader2, 'cmd=',
                    cmd, 'pack=', msgstr)
        if not gdata.initializeOk():
            ftlog.info('COS2AProto-doServerTcpMsg not initialize ok, ignore this message :', ftsvr.getTaskPack())
            return

        if userheader1 == 'S0':  # 发送给用户客户端的消息标记
            toUserId = int(userheader2)
            if toUserId in _ONLINE_USERS:
                user = _ONLINE_USERS[toUserId]
                if cmd == 'user_info':
                    # 链接建立后, 第一个返回给客户端的命令必须是user_info
                    isFirst = 0
                    if user.firstUserInfo == 0:
                        isFirst = 1

                    user.sendTcpMessage(msgstr)
                    user.firstUserInfo = 1

                    # 强制进行第一次心跳处理, 发送led,返回比赛报名情况等
                    if isFirst:
                        msg = '{"cmd":"heart_beat","params":{"userId":%d,"gameId":%d,"clientId":"%s","must":1}}' % (
                            toUserId, user.gameId, user.clientId)
                        router.sendUtilServer(msg, toUserId)

                    if len(user.delaySendMsg) > 0:
                        mlist = user.delaySendMsg
                        user.delaySendMsg = []
                        for m in mlist:
                            user.sendTcpMessage(m)
                else:
                    # 只有第一个命令user_info完成后, 后续的消息才会发送给客户端
                    if user.firstUserInfo == 1:
                        user.sendTcpMessage(msgstr)
                    else:
                        if user.delaySendMsg != None and len(user.delaySendMsg) < 20:
                            user.delaySendMsg.append(msgstr)
                        else:
                            ftlog.info('ERROR, the user tcp bind not ok !', toUserId, cmd)
            else:
                ftlog.info('ERROR, the user is already offline !', toUserId, cmd)
        else:
            # 当前进程需要处理的消息, 例如更新配置,热更新,强制用户退出等
            msg = MsgPack()
            try:
                msg.unpack(msgstr)
            except:
                raise Exception('the json data error 6 !! [' + repr(msgstr) + ']')
            task = FTTasklet.getCurrentFTTasklet()
            task.pack = msg
            task.run_args['pack'] = msg
            runcmd.handlerCommand(msg)


class COTCPProto(object):
    '''
    TCP的协议类, 其基类可以是FTWebSocketServerProtocol也可以是FTZipEncryServerProtocol
    再startup时,判定是否用COTCPProtoZIP还是COTCPProtoWS
    '''

    def lostHandler(self, reason):
        '''
        TCP链接断开处理
        '''
        try:
            if self in _NEW_PROTOCOLS:
                del _NEW_PROTOCOLS[self]
            if self.userId > 0:
                ftlog.info('TCP lostHandler clientAddress=', self.clientAddress, 'userId=', self.userId, 'reason=',
                           reason)
                # 异步进行用户断开连接的后续处理, 避免阻挡主tasklet
                data = '{"cmd":"conn_lost","params":{"userId":%d}}' % (self.userId)
                _countProtocolPack(1, self)
                self._runTasklet(data=data)
        except:
            ftlog.error('lostHandler:')

    def madeHandler(self):
        '''
        TCP链接建立处理
        '''
        self.userId = 0  # 当前连接的UserId
        if not gdata.initializeOk():
            ftlog.info('COTCPProto-madeHandler not initialize ok, close this TCP')
            self.closeConnection(1)
            return
        self.timeOutCount = 0  # 新连接的超时次数
        self.heart_beat_count = 0  # 新连接的心跳次数
        peer = self.transport.getPeer()
        self.clientAddress = str(peer.host) + ':' + str(peer.port)  # 当前连接的地址
        if not self in _NEW_PROTOCOLS:
            _NEW_PROTOCOLS[self] = self
        ftlog.info('TCP madeHandler', self.clientAddress)

    def getTaskletFunc(self, pack):
        return self.doClientTcpMsg

    def parseData(self, data):
        '''
        CONN服务接到客户端的消息, 不进行JSON解析, 避免过高的CPU
        '''
        return data

    def writeEncodeMsg(self, msg):
        """
        向用户客户端发送一个加密消息
        """
        ftlog.debug('======== SEND TCP->', self.clientAddress, self.userId, msg)
        msg = structProtocolHelper.encode(msg)
        if len(msg) and ide_debug():
            ide_print_pack("SEND TCP_", json.loads(msg))
        msg = self._encode(msg)
        self.transport.write(msg)

    def doClientTcpMsg(self):
        """
        接收到一个的用户客户端的TCP消息
        """
        msgstr = ftsvr.getTaskPack()
        if not msgstr:
            return

        ftlog.debug('======== RECEIVE TCP->', self.clientAddress, 'pack=|', repr(msgstr), '|')
        msgstr = structProtocolHelper.decode(msgstr)
        if not gdata.initializeOk():
            ftlog.warn('COTCPProto-doClientTcpMsg not initialize ok, ignore this message :', msgstr)
            return

        if len(msgstr) < 11:  # {"cmd":"a"}
            ftlog.warn('simple json format check too short ! [' + repr(msgstr) + ']')
            return
        if msgstr[0] == '[':  # 代理机器校验
            _proxyCheck(msgstr, self)
            return
        if msgstr[0] != '{':
            ftlog.warn('simple json format check not start with { ! [' + repr(msgstr[0:10]) + '...]')
            return

        # 后3位可能是  }\n\0 或 }\n 或 }\0 或 } 或 }\r\n
        if msgstr[-1] == '}':
            pass
        elif msgstr[-2] == '}':
            pass  # msgstr = msgstr[0:-1]
        elif msgstr[-3] == '}':
            pass  # msgstr = msgstr[0:-2]
        elif msgstr[-4] == '}':
            pass  # msgstr = msgstr[0:-3]
        elif msgstr[-5] == '}':
            pass  # msgstr = msgstr[0:-4]
        else:
            ftlog.warn('simple json format check not end with } ! [...' + repr(msgstr[-10:]) + ']')
            return

        if ide_debug():
            ide_print_pack("RECV TCP_", json.loads(msgstr))
        userId = strutil.getJsonInt(msgstr, 'userId', 0)
        if userId <= 0:
            ftlog.warn('COTCPProto-doClientTcpMsg the userId error, ignore this message :', userId, msgstr)
            return

        msgqueue = _MSG_QUEUES.get(userId, None)
        if msgqueue == None:
            msgqueue = []
            _MSG_QUEUES[userId] = msgqueue
            ftlog.debug('creat user msgqueue !', userId)

        if len(msgqueue) > _MSG_QUEUES_MAX_LEN and msgstr.find('"conn_lost"') < 0:  # TODO 这个经验值如何确定?
            ftlog.warn('the user msgqueue queue too large !!, ignore this message :', userId)
            return

        msgqueue.append(msgstr)
        if len(msgqueue) > 1:
            ftlog.debug('the user msgqueue is process, wait ...', userId)
            return

        ftlog.debug('process user msgqueue !', userId)

        while 1:
            msgstr1 = msgqueue[0]
            try:
                self._processUserMessage(userId, msgstr1)
            except:
                ftlog.error('ERROR _processUserMessage', userId, msgstr1)
            del msgqueue[0]
            if len(msgqueue) == 0:
                break
        del _MSG_QUEUES[userId]
        ftlog.debug('remove user msgqueue !', userId)

    def _processUserMessage(self, userId, msgstr):
        gameId = strutil.getJsonInt(msgstr, 'gameId', 0)
        if gameId in _DISABLE_GAMEIDS:
            return
        cmd = strutil.getJsonStr(msgstr, 'cmd', '')
        roomId = strutil.getJsonInt(msgstr, 'roomId', 0)

        ftlog.debug('do user msgqueue', self.clientAddress, 'cmd=', cmd, 'userId=', userId, 'gameId=', gameId,
                    'roomId=', roomId)

        # 第一个消息固定为bind_user，绑定userId和TCP链接
        if self.userId == 0:
            if cmd == 'bind_user' or cmd == 'user_info':
                clientId = strutil.getJsonStr(msgstr, 'clientId', '')
                if not self._doUserConnect(userId, gameId, clientId):
                    return
                else:
                    msgstr = '{"firstUserInfo":1,' + msgstr[1:]
            else:
                ftlog.debug('do user msgqueue the new tcp first cmd is not bind_user !', msgstr)
                _sendLogOutMsg(self, ERROR_SYS_LOGOUT_FIRST_CMD_ERROR, 1)
                return

        # 心跳处理, 正常消息也认为是心跳的
        if self._doUserAlive(cmd):
            return

        # 如果是当前的服务消息，那么直接处理
        if cmd == 'conn_lost':
            self._doUserClosed()
            return

            # 路由消息到其他服务进程
        #         router.routeConnTcpMsg(cmd, userId, roomId, msgstr)
        # clientId补偿处理，避免命令执行时到redis或rpc中取得clientId

        roomId, msgstr = conn_bridge.convertOldRoomId(roomId, msgstr)
        if userId in _ONLINE_USERS:
            user = _ONLINE_USERS[userId]
            msgstr = user.cid + msgstr[1:]
            router.routeConnTcpMsgQuery(cmd, userId, roomId, msgstr)
        else:
            ftlog.warn('the user is offline !!', userId)

    def _doUserConnect(self, userId, gameId, clientId):
        """
        更新用户的TCP链接
        """
        ftlog.info('doUpdateUserTcpConnection userId=', userId, 'address=', self.clientAddress)
        ipaddress = self.transport.getPeer().host
        if ftlog.is_debug():
            ftlog.debug("|userId, ip:", userId, ipaddress, caller=self)
        if userId <= 0:
            _sendLogOutMsg(self, ERROR_SYS_LOGOUT_USERID_ERROR, 1)
            return
        # try:
        #             conns = gdata.getUserConnIpPortList()
        #             idx = userId % len(conns)
        #             if idx != gdata.serverNumIdx() :
        #                 raise Exception('the user ip port error, this is ' + str(gdata.serverNumIdx()) \
        #                                 + ' idx=' + str(idx) + ' sid=' + str(gdata.serverId()) + ' ' \
        #                                 + str(userId) + ' ' + str(gameId) + ' ' + str(clientId) + ' ' + str(ipaddress))
        #         except:
        #             ftlog.error()
        #             _sendLogOutMsg(self, ERROR_SYS_LOGOUT_TIME_OUT, 1)
        #             return

        intClientId = pokerconf.clientIdToNumber(clientId)
        if intClientId <= 0:
            ftlog.warn('the user clientid error ! ' + str(userId) + ' ' + \
                       str(gameId) + ' ' + str(clientId) + ' ' + str(ipaddress))
            _sendLogOutMsg(self, ERROR_SYS_LOGOUT_CLIENTID_ERROR, 1)
            return

        _checkLastedConnId(userId)
        session = {'ip': ipaddress, 'ci': clientId, 'conn': gdata.serverId()}
        try:
            if not userdata.checkUserData(userId, clientId, session=session):
                # 冷数据导入失败, 关闭连接TCP连接
                _sendLogOutMsg(self, ERROR_SYS_LOGOUT_DATASWAP_ERROR, 0)
                return
        except:
            # 冷数据导入失败, 关闭连接TCP连接
            ftlog.error()
            _sendLogOutMsg(self, ERROR_SYS_LOGOUT_DATASWAP_ERROR, 0)
            return

        if ftlog.is_debug():
            from poker.entity.dao import sessiondata
            ftlog.debug("|userId, ip:", userId, sessiondata.getClientIp(userId), caller=self)

        # 建立当前进程内的userid和tcp链接的对应关系 1:1的对应关系
        user = None
        if _ONLINE_USERS.has_key(userId):
            user = _ONLINE_USERS[userId]
            user.hbcounter = 0
        else:
            user = TcpUser(userId)
            _ONLINE_USERS[userId] = user
        oldProtocol = user.tcpProtocol
        user.tcpProtocol = self
        user.clientId = str(clientId)
        user.cid = '{"clientId":"' + user.clientId + '",'
        user.gameId = gameId
        self.userId = userId

        if self in _NEW_PROTOCOLS:
            del _NEW_PROTOCOLS[self]

        ftlog.info('User Protocol update : userId=', userId, ' newProtocol=', self.clientAddress)

        _notifyUserOnlineStatus(user, 1)

        if oldProtocol and oldProtocol.userId > 0 and self != oldProtocol:
            ftlog.info('User Protocol close old : userId=', userId, ' oldProtocol=', oldProtocol.clientAddress)
            user.firstUserInfo = 0
            oldProtocol.userId = 0
            _sendLogOutMsg(oldProtocol, ERROR_SYS_LOGOUT_OTHER_LOGIN, 0)
            # TODO 还需要发出room_leave的消息么?
        return 1

    def _doUserAlive(self, cmd):
        '''
        用户客户端发送的心跳处理
        '''
        userId = self.userId
        if userId in _ONLINE_USERS:
            user = _ONLINE_USERS[userId]
            user.hbcounter = 0  # 将超时的计时器清零
            user.sendCarryMsg()
            if cmd == 'heart_beat':
                self.writeEncodeMsg('')  # 响应一个空消息, 以表明连接是活动的
                user.hbcounts = user.hbcounts + 1
                if user.hbcounts % 600 == 0:  # 心跳约6秒一次, 600次约1个小时, 更新该用户的数据时间
                    userdata.updateUserDataAliveTime(userId)
                if user.hbcounts % _HEART_BEAT_MOD != 0:
                    return True  # 每n个heart_beat,处理一次, 客户端的这个请求过于频繁, 会压垮服务器
        else:
            self.timeOutCount = 0
        return False

    def _doUserClosed(self):
        '''
        用户掉线处理
        '''
        userId = self.userId
        ftlog.info('_doUserClosed userId=', userId)
        self.userId = -2
        if userId in _ONLINE_USERS:
            user = _ONLINE_USERS[userId]
            del _ONLINE_USERS[userId]
            _notifyUserOnlineStatus(user, 0)
        else:
            ftlog.info('TCP lostHandler not found userId in ONLINE_USERS')


class COTCPProtoZIP(COTCPProto, FTZipEncryServerProtocol):
    pass


class COTCPProtoWS(COTCPProto, FTWebSocketServerProtocol):
    pass


def _sendLogOutMsg(protocol, errorCode, isabort):
    '''
    发送一个强制logout的消息后, 关闭用户的TCP的链接
    '''
    if errorCode != ERROR_SYS_LOGOUT_TIME_OUT:
        ml = MsgPack()
        ml.setCmd('logout')
        ml.setError(errorCode, pokerconf.getConnLogoutMsg(errorCode, 'Please try to login again'))
        protocol.writeEncodeMsg(ml.pack())
    protocol.closeConnection(0)
    ftlog.info('_sendLogOutMsg address=', protocol.clientAddress, 'errorCode=', errorCode)


def forceUserLogOut(userId, logoutmsg):
    '''
    管理员发送强制关闭TCP链接的消息, 
    发送logout消息后,关闭用户的TCP的链接
    '''
    ftlog.info('forceUserLogOut userId=', userId)
    if not logoutmsg:
        logoutmsg = pokerconf.getConnLogoutMsg(ERROR_SYS_LOGOUT_FORCE_LOGOUT, 'Please try to login again')
    ml = MsgPack()
    ml.setCmd('logout')
    ml.setError(ERROR_SYS_LOGOUT_FORCE_LOGOUT, logoutmsg)
    ml = ml.pack()
    if userId in _ONLINE_USERS:
        user = _ONLINE_USERS[userId]
        ftlog.debug('forceUserLogOut user=', user)
        protocol = user.tcpProtocol
        if protocol:
            protocol.writeEncodeMsg(ml)
            protocol.closeConnection(0)
            return 1
    ftlog.debug('forceUserLogOut user not in map !!')
    return 0


def _notifyUserOnlineStatus(user, isOnline):
    '''
    发送用户的上下线通知到UTIL服务
    '''
    mo = MsgPack()
    mo.setCmd('user')
    mo.setParam('userId', user.userId)
    mo.setParam('clientId', user.clientId)
    mo.setKey('clientId', user.clientId)
    if isOnline:
        mo.setParam('action', 'online')
    else:
        mo.setParam('action', 'offline')
    router.sendUtilServer(mo, user.userId)
    userdata.updateUserDataAliveTime(user.userId)  # 用户上下线的同时, 更新用户的数据时间


def doCleanUpEmptyTcp(event):
    '''
    检查当前进程内的空闲的TCP链接, 
    关闭空闲的TCP, 释放资源
    '''
    if event.count % _EMPTY_TCP_CHECK_TIMES != 0:
        return
    ftlog.debug('doCleanUpEmptyTcp->', event.count)
    # 空连接检测
    emptyCount = 0
    for protocol in _NEW_PROTOCOLS:
        cnt = protocol.timeOutCount + 1
        if cnt > _EMPTY_TCP_TIMEOUT_COUNT:
            _sendLogOutMsg(protocol, ERROR_SYS_LOGOUT_TIME_OUT, 1)
            emptyCount = emptyCount + 1
        else:
            protocol.timeOutCount = cnt

    # 客户端心跳检测，视为断开链接
    count = 0
    rcount = 0
    closeUser = []
    for uid in _ONLINE_USERS:
        user = _ONLINE_USERS[uid]
        if user.userId > 10000:  # 机器人永远不掉线
            tcpProtocol = user.tcpProtocol
            if tcpProtocol and tcpProtocol.userId > 0:
                cnt = user.hbcounter + 1
                if cnt > _EMPTY_USER_TIMEOUT_COUNT:
                    closeUser.append(uid)
                    ftlog.debug('doCleanUpEmptyTcp heart beat time out ! user.userId=', user.userId)
                    user.hbcounter = 0
                else:
                    user.hbcounter = cnt
                    count = count + 1
        else:
            tcpProtocol = user.tcpProtocol
            if tcpProtocol and tcpProtocol.userId > 0:
                rcount = rcount + 1

    for uid in closeUser:
        if uid in _ONLINE_USERS:
            user = _ONLINE_USERS[uid]
            _sendLogOutMsg(user.tcpProtocol, ERROR_SYS_LOGOUT_TIME_OUT, 1)

    bireport.tcpUserOnline(count)

    ftlog.warn('online user count=', count, 'robots=', rcount, \
               'ONLINE_USERS=', len(_ONLINE_USERS), 'NEW_PROTOCOLS=', len(_NEW_PROTOCOLS), \
               'close empty tcp=', emptyCount, 'close user =', closeUser, 'SERVERID=', gdata.serverId())


def sendCarryMessage(msg, userids=[]):
    '''
    发送延迟的携带消息
    '''
    if not msg:
        return
    if isinstance(msg, MsgPack):
        msg = msg.pack()
    assert (isinstance(msg, (str, unicode)))

    if not userids:
        userids = _ONLINE_USERS.keys()
    count = 0
    for userId in userids:
        if userId in _ONLINE_USERS:
            user = _ONLINE_USERS[userId]
            user.carryMsg.append(msg)
            count += 1
            if count % 500 == 0:
                FTTasklet.getCurrentFTTasklet().sleepNb(0.01)
    return count


def _proxyCheck(msgstr, protocol):
    try:
        dlist = strutil.loads(msgstr)
        host, port, userId, logtag, checktag = dlist[0], dlist[1], dlist[2], dlist[3], dlist[4]
        peer = protocol.transport.getPeer()
        phost = peer.host
        pport = peer.port
        idx = userId % len(gdata.getUserConnIpPortList())
        ret = 'ok'
        numIdx = gdata.serverNumIdx()
        if idx != numIdx:
            ret = 'user idx error ' + msgstr + ' idx=' + str(idx) + ' serverNumIdx=' + str(gdata.serverNumIdx())
        ftlog.warn('PROXY_CHECK', (idx == numIdx), host, port, userId, logtag, checktag, 'PEER', phost, pport, 'IDX',
                   idx, numIdx)
        ret = strutil.dumps({'result': ret})
        protocol.writeEncodeMsg(ret)
    except:
        ftlog.error()


def _checkLastedConnId(userId):
    if gdata.ENABLIE_DEFENCE_2:
        try:
            from poker.entity.dao import sessiondata
            from poker.servers.conn.rpc import onlines
            lastConnId = sessiondata.getConnId(userId)
            if lastConnId and lastConnId != gdata.serverId():
                onlines.forceLogOut2(userId, lastConnId, '')
        except:
            ftlog.error()
