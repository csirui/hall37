# -*- coding: utf-8 -*-
"""
Created on 2015-5-12
@author: zqh
"""
import random

import stackless

import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack
from freetime.support.tcpagent import wrapper
from poker.entity.configure import gdata, pokerconf, configure
from poker.protocol import oldcmd, _runenv
from poker.util import strutil


class _RouterServer:
    def __init__(self, sids=None, srvType=None):
        if not sids:
            sids = []
        self.srvType = srvType
        self.sids = sids[:]
        self.sidlen = len(self.sids)
        if self.sidlen > 0:
            self.sididx = random.randint(0, self.sidlen - 1)
        else:
            self.sididx = 0
        self.sids.sort()
        if sids:
            ftlog.debug('ROUTER->', self.sids, self.sidlen, self.sididx, caller=self)


_connServer = _RouterServer()
_utilServer = _RouterServer()
_httpServer = _RouterServer()
_sdkHttpServer = _RouterServer()
_gatewayHttpServer = _RouterServer()
_robotServer = _RouterServer()
_centerServer = _RouterServer()
_agentServer = _RouterServer()

_cmd_route_map = {}
_cmd_notuse_map = set()
_cmd_group_match_set = set()


def _initialize():
    '''
    初始化命令路由
    '''
    ftlog.debug('router._initialize begin')
    allsrv = gdata.serverTypeMap()
    global _connServer
    _connServer = _RouterServer(allsrv.get(gdata.SRV_TYPE_CONN, None), gdata.SRV_TYPE_CONN)
    global _utilServer
    _utilServer = _RouterServer(allsrv.get(gdata.SRV_TYPE_UTIL, None), gdata.SRV_TYPE_UTIL)
    global _httpServer
    _httpServer = _RouterServer(allsrv.get(gdata.SRV_TYPE_HTTP, None), gdata.SRV_TYPE_HTTP)
    global _robotServer
    _robotServer = _RouterServer(allsrv.get(gdata.SRV_TYPE_ROBOT, None), gdata.SRV_TYPE_ROBOT)
    global _centerServer
    _centerServer = _RouterServer(allsrv.get(gdata.SRV_TYPE_CENTER, None), gdata.SRV_TYPE_CENTER)
    global _agentServer
    _agentServer = _RouterServer(allsrv.get(gdata.SRV_TYPE_AGENT, None), gdata.SRV_TYPE_AGENT)
    global _sdkHttpServer
    _sdkHttpServer = _RouterServer(allsrv.get(gdata.SRV_TYPE_SDK_HTTP, None), gdata.SRV_TYPE_SDK_HTTP)
    global _gatewayHttpServer
    _gatewayHttpServer = _RouterServer(allsrv.get(gdata.SRV_TYPE_SDK_GATEWAY, None), gdata.SRV_TYPE_SDK_GATEWAY)

    # 整理CONN接入使用的命令路由表
    for srvtype, cmds in pokerconf.getCmds().items():
        if srvtype == 'NOT_USED':
            global _cmd_notuse_map
            _cmd_notuse_map = set(cmds.keys())
            ftlog.debug('NOT_USED CMD->', _cmd_notuse_map)
        elif srvtype == 'GROUP_MATCH':
            global _cmd_group_match_set
            _cmd_group_match_set = set(cmds)
            ftlog.debug('GROUP_MATCH CMD->', _cmd_group_match_set)
        else:
            assert (srvtype in gdata.SRV_TYPE_ALL)
            for cmd in cmds:
                assert (cmd not in _cmd_route_map)
                _cmd_route_map[cmd] = cmds[cmd]
                cmds[cmd]['target'] = srvtype

    ftlog.debug('router._cmd_route_map=', _cmd_route_map)
    ftlog.debug('router._initialize end')


def _initialize_udp():
    pass


def sendToAll(msgpack, serverType='', head2=''):
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(msgpack, basestring))
    for stype, sids in gdata.serverTypeMap().items():
        if not serverType or serverType == stype:
            for dst in sids:
                wrapper.send(dst, msgpack, 'S7', head2)


def isQuery():
    return wrapper.isQuery()


def responseQurery(msgpack, userheader1=None, userheader2=None):
    """
    响应"查询请求"的进程内部消息命令, 即: query->response
    """
    taskarg = stackless.getcurrent()._fttask.run_args
    if not 'responsed' in taskarg:
        taskarg['responsed'] = 1
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(msgpack, basestring))
    wrapper.response(msgpack, userheader1, userheader2)


def _communicateServer(rsrv, groupId, userId, msgpack, head1, isQuery, timeout=None, notimeoutex=0):
    if timeout == None:
        timeout = _runenv._RPC_TIME_OUT
    if groupId <= 0:
        groupId = rsrv.sididx
        rsrv.sididx += 1
    dst = rsrv.sids[groupId % rsrv.sidlen]
    ftlog.debug('_communicateServer->dst=', dst, 'groupId=', userId, 'timeout=', timeout, 'msgpack=[' + msgpack + ']')
    if isQuery:
        return wrapper.query(dst, msgpack, head1, str(userId), timeout, notimeoutex=notimeoutex)
    else:
        return wrapper.send(dst, msgpack, head1, str(userId))


def sendToUser(msgpack, userId):
    """
    发送消息至用户的客户端
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(userId, (int, long)) and userId > 0)
    assert (isinstance(msgpack, basestring))
    if gdata.ENABLIE_DEFENCE_2:
        from poker.entity.dao import sessiondata
        srvId = sessiondata.getConnId(userId)
        ftlog.debug('sendToUser', userId, srvId)
        if srvId in _connServer.sids:
            return wrapper.send(srvId, msgpack, 'S0', str(userId))
    return _communicateServer(_connServer, userId, userId, msgpack, 'S0', 0)


def sendToUsers(msgpack, userIdList):
    '''
    发送消息至一组用户的客户端
    '''
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(msgpack, basestring))
    for userId in userIdList:
        assert (isinstance(userId, (int, long)) and userId > 0)
        if gdata.ENABLIE_DEFENCE_2:
            from poker.entity.dao import sessiondata
            srvId = sessiondata.getConnId(userId)
            ftlog.debug('sendToUser', userId, srvId)
            if srvId in _connServer.sids:
                wrapper.send(srvId, msgpack, 'S0', str(userId))
                continue
        _communicateServer(_connServer, userId, userId, msgpack, 'S0', 0)


def sendConnServer(msgpack, userId=0):
    """
    发送消息至CONN服务, 若userId大于0, 那么按照userId取模获得CONN进程, 否则随机选择一个CONN进程进行发送
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(userId, (int, long)) and userId >= 0)
    assert (isinstance(msgpack, basestring))
    return _communicateServer(_connServer, userId, userId, msgpack, 'S1', 0)


def queryConnServer(msgpack, userId=0):
    """
    发送查询请求消息至CONN服务, 若userId大于0, 那么按照userId取模获得CONN进程, 否则随机选择一个CONN进程进行发送
    返回CONN的响应消息
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(userId, (int, long)) and userId >= 0)
    assert (isinstance(msgpack, basestring))
    return _communicateServer(_connServer, userId, userId, msgpack, 'Q1', 1)


def sendUtilServer(msgpack, userId=0):
    """
    发送消息至UTIL服务, 若userId大于0, 那么按照userId取模获得UTIL进程, 否则随机选择一个UTIL进程进行发送
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(userId, (int, long)) and userId >= 0)
    assert (isinstance(msgpack, basestring))
    return _communicateServer(_utilServer, userId, userId, msgpack, 'S2', 0)


def queryUtilServer(msgpack, userId=0):
    """
    发送查询请求消息至UTIL服务, 若userId大于0, 那么按照userId取模获得UTIL进程, 否则随机选择一个UTIL进程进行发送
    返回UTIL的响应消息
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(userId, (int, long)) and userId >= 0)
    assert (isinstance(msgpack, basestring))
    return _communicateServer(_utilServer, userId, userId, msgpack, 'Q2', 1)


def sendRobotServer(msgpack, userId=0):
    """
    发送消息至ROBOT服务, 若userId大于0, 那么按照userId取模获得ROBOT进程, 否则随机选择一个ROBOT进程进行发送
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(userId, (int, long)) and userId >= 0)
    assert (isinstance(msgpack, basestring))
    return _communicateServer(_robotServer, userId, userId, msgpack, 'S3', 0)


def queryRobotServer(msgpack, userId=0):
    """
    发送查询请求消息至ROBOT服务, 若userId大于0, 那么按照userId取模获得ROBOT进程, 否则随机选择一个ROBOT进程进行发送
    返回ROBOT的响应消息
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(userId, (int, long)) and userId >= 0)
    assert (isinstance(msgpack, basestring))
    return _communicateServer(_robotServer, userId, userId, msgpack, 'Q3', 1)


def sendCenterServer(msgpack, logicName):
    """
    发送消息至CENTER服务
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(msgpack, basestring))
    for dst, logics in gdata.centerServerLogics().items():
        if logicName in logics:
            return wrapper.send(dst, msgpack, 'S7', logicName)
    raise Exception('the center logicName not found !!' + str(logicName))


def queryCenterServer(msgpack, logicName):
    """
    发送查询请求消息至CENTER服务
    返回CENTER的响应消息
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(msgpack, basestring))
    for dst, logics in gdata.centerServerLogics().items():
        if logicName in logics:
            return wrapper.query(dst, msgpack, 'Q7', logicName, _runenv._RPC_TIME_OUT)
    raise Exception('the center logicName not found !!' + str(logicName))


def sendHttpServer(msgpack, userId=0):
    """
    发送消息至HTTP服务, 若userId大于0, 那么按照userId取模获得HTTP进程, 否则随机选择一个HTTP进程进行发送
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(userId, (int, long)) and userId >= 0)
    assert (isinstance(msgpack, basestring))
    return _communicateServer(_httpServer, userId, userId, msgpack, 'S4', 0)


def queryHttpServer(msgpack, userId=0):
    """
    发送查询请求消息至HTTP服务, 若userId大于0, 那么按照userId取模获得HTTP进程, 否则随机选择一个HTTP进程进行发送
    返回HTTP的响应消息
    """
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    assert (isinstance(userId, (int, long)) and userId >= 0)
    assert (isinstance(msgpack, basestring))
    return _communicateServer(_httpServer, userId, userId, msgpack, 'Q4', 1)


def __changeMsgRoomId(msgpack, newRoomId, clientRoomId):
    """
    处理结果返回给客户端时，部分游戏（例如德州、三顺）需要判断返回的roomId是否与本地一致
    """
    if isinstance(msgpack, MsgPack):
        msgpack.setParam("roomId", newRoomId)
        msgpack.setParam("clientRoomId", clientRoomId)
        return msgpack
    else:
        newMsgPack = MsgPack()
        try:
            newMsgPack.unpack(msgpack)
        except:
            raise Exception('the json data error 3 !! [' + repr(msgpack) + ']')
        newMsgPack.setParam("roomId", newRoomId)
        newMsgPack.setParam("clientRoomId", clientRoomId)
        return newMsgPack


def _communicateRoomServer(userId, roomId, msgpack, head1, isQuery, timeout=None, notimeoutex=0):
    if timeout == None:
        timeout = _runenv._RPC_TIME_OUT
    assert (isinstance(msgpack, (MsgPack, basestring)))
    assert (isinstance(roomId, (int, long)) and roomId >= 0)
    allrooms = gdata.roomIdDefineMap()
    if roomId in allrooms:
        roomDef = allrooms[roomId]
        if roomDef.parentId > 0:  # this roomId is shadowRoomId
            ctrlRoomId = roomDef.parentId
            roomDef = allrooms[ctrlRoomId]
            msgpack = __changeMsgRoomId(msgpack, ctrlRoomId, roomId)
    else:  # this roomId is big roomId
        assert (isinstance(userId, (int, long)) and userId >= 0)
        bigrooms = gdata.bigRoomidsMap()
        if roomId in bigrooms:
            ctrlroomIds = bigrooms[roomId]
            ctrlRoomId = ctrlroomIds[userId % len(ctrlroomIds)]  # ctrlRoom0 做为 ctrlRooms 的调度器
            roomDef = allrooms[ctrlRoomId]
            msgpack = __changeMsgRoomId(msgpack, ctrlRoomId, roomId)
        else:
            ftlog.warn('ERROR, cat not localtion the roomId of->', userId, roomId, msgpack)
            return
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    dst = roomDef.serverId
    ftlog.debug('_communicateRoomServer->dst=', dst, 'head1=', head1, 'roomId=', str(roomId), 'timeout=', timeout,
                'msgpack=[' + msgpack + ']')

    if isQuery:
        response = wrapper.query(dst, msgpack, head1, str(roomId), timeout, notimeoutex=notimeoutex)
        ftlog.debug('_communicateRoomServer->dst=', dst, 'head1=', head1, 'roomId=', str(roomId),
                    'response=[' + str(response) + ']')
        return response
    else:
        return wrapper.send(dst, msgpack, head1, str(roomId))


def sendRoomServer(msgpack, roomId):
    """
    发送一个消息至指定的房间处理进程
    """
    return _communicateRoomServer(0, roomId, msgpack, 'S5', 0)


def queryRoomServer(msgpack, roomId):
    """
    发送一个查询请求消息至指定的房间处理进程, 并返回目标进程的响应消息
    """
    return _communicateRoomServer(0, roomId, msgpack, 'Q5', 1)


def sendTableServer(msgpack, roomId):
    """
    发送一个消息至指定的桌子处理进程
    """
    return _communicateTableServer(0, roomId, msgpack, 'S6', 0)


def queryTableServer(msgpack, roomId):
    """
    发送一个查询请求消息至指定的桌子处理进程, 并返回目标进程的响应消息
    """
    return _communicateTableServer(0, roomId, msgpack, 'Q6', 1)


def __getRoomIdByTableId(msgpack):
    """
    部分游戏（例如德州、三顺）老版本牌桌周边功能需要使用bigRoomId，发送给GT的协议里roomId也是bigRoomId
    """
    if isinstance(msgpack, MsgPack):
        tableId = msgpack.getParam("tableId", 0)
        shadowRoomId = tableId / 10000
        msgpack.setParam("roomId", shadowRoomId)
        return msgpack, shadowRoomId
    else:
        newMsgPack = MsgPack()
        try:
            newMsgPack.unpack(msgpack)
        except:
            raise Exception('the json data error 4 !! [' + repr(msgpack) + ']')

        tableId = newMsgPack.getParam("tableId", 0)
        shadowRoomId = tableId / 10000
        newMsgPack.setParam("roomId", shadowRoomId)
        return newMsgPack, shadowRoomId


def _communicateTableServer(userId, roomId, msgpack, head1, isQuery, timeout=None, notimeoutex=0):
    if timeout == None:
        timeout = _runenv._RPC_TIME_OUT
    assert (isinstance(msgpack, (MsgPack, basestring)))
    assert (isinstance(roomId, (int, long)) and roomId >= 0)
    assert (isinstance(userId, (int, long)) and userId >= 0)
    allrooms = gdata.roomIdDefineMap()
    if roomId in allrooms:
        roomDef = allrooms[roomId]
        if roomDef.parentId == 0:
            ftlog.warn('ERROR, cat not localtion the roomId of->', userId, roomId, msgpack)
            return
    else:  # this roomId is big roomId
        assert (isinstance(userId, (int, long)) and userId >= 0)
        bigrooms = gdata.bigRoomidsMap()
        if roomId in bigrooms:
            msgpack, shadowRoomId = __getRoomIdByTableId(msgpack)
            ftlog.debug('_communicateTableServer allrooms = ', allrooms, 'shadowRoomId =', shadowRoomId)
            if shadowRoomId:
                roomDef = allrooms[shadowRoomId]
            else:
                ftlog.warn('ERROR, cat not localtion the roomId of->', userId, roomId, msgpack)
                return
        else:
            ftlog.warn('ERROR, cat not localtion the roomId of->', userId, roomId, msgpack)
            return
    if isinstance(msgpack, MsgPack):
        msgpack = msgpack.pack()
    dst = roomDef.serverId
    ftlog.debug('_communicateTableServer->dst=', dst, 'head1=', head1, 'roomId=', str(roomId), 'timeout=', timeout,
                'msgpack=[' + msgpack + ']')

    if isQuery:
        response = wrapper.query(dst, msgpack, head1, str(roomId), timeout, notimeoutex=notimeoutex)
        ftlog.debug('_communicateTableServer->dst=', dst, 'head1=', head1, 'roomId=', str(roomId),
                    'response=[' + str(response) + ']')
        return response
    else:
        return wrapper.send(dst, msgpack, head1, str(roomId))


def routeConnTcpMsg(cmd, userId, roomId, msgpack):
    """
    CONN服务调用, 路由消息到其他的服务
    """
    routeinfo = _cmd_route_map.get(cmd, None)
    if not routeinfo:
        routeinfo = oldcmd.findTargetInfo(cmd)
    ftlog.debug('cmd=', cmd, 'userId=', userId, 'roomId=', roomId, 'routeinfo=', routeinfo, 'msgpack=', msgpack)
    if not routeinfo:
        ftlog.warn('ERROR the cmd not in route map ! cmd.json', cmd, userId, roomId, msgpack)
        return
    srvtype = routeinfo['target']
    if srvtype == gdata.SRV_TYPE_UTIL:
        sendUtilServer(msgpack, userId)
    elif srvtype == gdata.SRV_TYPE_ROOM:
        sendRoomServer(msgpack, roomId)
    elif srvtype == gdata.SRV_TYPE_TABLE:
        sendTableServer(msgpack, roomId)
    else:
        ftlog.error('ERROR the cmd route false !!', cmd)


def filterCmdAct(cmd, userId, roomId, msgpack):
    try:
        if roomId == 8888 or roomId == 99 or roomId == 1:
            ftlog.info('filterCmdAct drop->', cmd, roomId, msgpack)
            return 1
        if cmd == 'htmls_info':
            if msgpack.find('"Winpc_') > 0 or msgpack.find('"MAC_') > 0:
                ftlog.info('filterCmdAct drop->', cmd, roomId, msgpack)
                return 1
        if cmd == 'decoration':
            if msgpack.find('"Winpc_') > 0 or msgpack.find('"MAC_') > 0:
                if strutil.getJsonInt(msgpack, 'gameId', 0) <= 0 and strutil.getJsonStr(msgpack, 'action',
                                                                                        '') == 'query':
                    ftlog.info('filterCmdAct drop->', cmd, roomId, msgpack)
                    return 1
    except:
        ftlog.error()
    return 0


def routeConnTcpMsgQuery(cmd, userId, roomId, msgpack):
    """
    CONN服务调用, 路由消息到其他的服务
    """
    routeinfo = _cmd_route_map.get(cmd, None)
    if not routeinfo:
        routeinfo = oldcmd.findTargetInfo(cmd)
    ftlog.debug('cmd=', cmd, 'userId=', userId, 'roomId=', roomId, 'routeinfo=', routeinfo, 'msgpack=', msgpack)
    if not routeinfo:
        if cmd in _cmd_notuse_map:
            ftlog.debug('the cmd is not used !!', cmd)
            return
        ftlog.warn('ERROR the cmd not in route map ! cmd.json', cmd, userId, roomId, msgpack)
        return

    if filterCmdAct(cmd, userId, roomId, msgpack):
        return

    mo = None
    notimeoutex = 1  # 不打印CO到其他进程的超时异常
    srvtype = routeinfo['target']

    # 分组大比赛的命令检查路由，部分消息需由UT进行二次分发处理
    if roomId:
        roomConf = gdata.getRoomConfigure(roomId)
        if roomConf and roomConf.get('typeName') == 'group_match':
            act = strutil.getJsonStr(msgpack, 'action', '')
            cmdpath = cmd + '#' + act
            if cmdpath in _cmd_group_match_set:
                srvtype = gdata.SRV_TYPE_UTIL

    if srvtype == gdata.SRV_TYPE_UTIL:
        mo = _communicateServer(_utilServer, userId, userId, msgpack, 'CQ', 1, notimeoutex=notimeoutex)
    elif srvtype == gdata.SRV_TYPE_ROOM:
        mo = _communicateRoomServer(userId, roomId, msgpack, 'CQ', 1, notimeoutex=notimeoutex)
    elif srvtype == gdata.SRV_TYPE_TABLE:
        mo = _communicateTableServer(userId, roomId, msgpack, 'CQ', 1, notimeoutex=notimeoutex)
    elif srvtype == gdata.SRV_TYPE_CENTER:
        mo = _communicateServer(_centerServer, userId, userId, msgpack, 'CQ', 1, notimeoutex=notimeoutex)
    else:
        ftlog.error('ERROR the cmd route false !!', cmd, msgpack)
    ftlog.debug('the cmd route return !!', cmd, 'result=', mo)


def _remoteCall(markParams, argl, argd):
    srvtype = markParams['remoteServerType']
    syncCall = markParams['remoteSyncCall']
    remoteGroupByIndex = markParams['remoteGroupByIndex']
    remoteGroupBy = markParams['remoteGroupBy']
    cmd = markParams['remoteCmd']
    action = markParams['remoteAction']
    groupVal = argl[remoteGroupByIndex]
    msgpack = MsgPack()
    msgpack.setCmdAction(cmd, action)
    msgpack.setParam(remoteGroupBy, groupVal)
    msgpack.setParam('argl', argl[1:])  # 去掉self, cls
    msgpack.setParam('argd', argd)
    msgpack.setParam('clientId', configure.CLIENTID_RPC)
    msgpack = msgpack.pack()
    jstr = None
    if srvtype == gdata.SRV_TYPE_UTIL:
        jstr = _communicateServer(_utilServer, groupVal, groupVal, msgpack, 'RQ', syncCall)
    elif srvtype == gdata.SRV_TYPE_ROOM:
        assert (groupVal in gdata.roomIdDefineMap())
        jstr = _communicateRoomServer(0, groupVal, msgpack, 'RQ', syncCall)
    elif srvtype == gdata.SRV_TYPE_TABLE:
        assert (groupVal in gdata.roomIdDefineMap())
        jstr = _communicateTableServer(0, groupVal, msgpack, 'RQ', syncCall)
    elif srvtype == gdata.SRV_TYPE_CENTER:
        jstr = _communicateServer(_centerServer, groupVal, groupVal, msgpack, 'RQ', syncCall)
    else:
        raise Exception('ERROR RPC cmd route false !!' + cmd + '.' + action)
    ret = None
    if syncCall and jstr:
        mo = MsgPack()
        try:
            mo.unpack(jstr)
        except:
            raise Exception('the json data error 5 !! [' + repr(jstr) + ']')
        ret = mo.getKey('result')
    return ret
