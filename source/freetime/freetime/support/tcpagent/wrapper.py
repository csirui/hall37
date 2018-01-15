# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.4.15
"""
收集管理agent相关的方法:
    初始化普通进程和Agent进程的监听和连接
    以及封装send,query,response三个基本方法
"""
import json
import sys
from time import time

import stackless
from twisted.internet import reactor
from twisted.internet.protocol import Factory

import freetime.entity.config as ftcon
import freetime.support.tcpagent.msg as agentmsg
import freetime.util.log as ftlog
from freetime.style import ide_debug, ide_print_pack
from freetime.support.tcpagent.factory import FTReconnectFactory
from freetime.support.tcpagent.protocol import A2AProtocol
from freetime.support.tcpagent.protocol import A2SProtocol
from freetime.util import performance


def connect_agent_eachother(server_id):
    """
    Agent进程调用，监听自己的端口，并与其他Agent建立连接
    """
    ftlog.debug('connect_agent_eachother', server_id)
    myconf = ftcon.server_map[server_id]
    myip = myconf['ip']
    agentids = ftcon.server_type_map.get('AG', None)
    for agentid in agentids:
        agent = ftcon.server_map.get(agentid, None)
        ip = agent['ip']
        inner_port = agent['protocols']['server']['a2s']
        outer_port = agent['protocols']['server']['a2a']
        if agentid == server_id:
            # listen inner port for inner process
            factory = Factory()
            factory.protocol = A2SProtocol
            reactor.listenTCP(inner_port, factory)
            ftlog.info('Agent Start, listen for services port', inner_port)
            # listen outer port for other agent
            factory = Factory()
            factory.protocol = A2AProtocol
            reactor.listenTCP(outer_port, factory)
            ftlog.info('Agent Start, listen for agent port', outer_port)
        else:
            # 只连接比自己的ID大的agent，这样节省一半的连接，n*(n-1)/2
            if cmp(agentid, server_id) > 0:
                factory = FTReconnectFactory()
                factory.protocol = A2AProtocol
                if ip == myip:
                    ip = '127.0.0.1'
                reactor.connectTCP(ip, outer_port, factory)
                ftlog.info('Agent connect Agent', agentid, server_id)


def connect_agent(server_id, proto_func):
    """
    Service进程调用，连接配置的Agent
    """
    _c = proto_func("s2a")
    if _c == None:
        ftlog.error("s2a protocol must be implemented!!!")
        ftlog.error("read demo/protocol/__init__.py")
        sys.exit(0)

    server_conf = ftcon.getServerConf(server_id)
    agent_id = server_conf['agent']
    myip = server_conf['ip']

    agent_conf = ftcon.getServerConf(agent_id)
    ip = agent_conf['ip']
    inner_port = agent_conf['protocols']['server']['a2s']
    # outer_port = agent_conf['protocols']['server']['a2a']
    if ip == myip:
        ip = '127.0.0.1'
    factory = FTReconnectFactory()
    factory.protocol = _c
    reactor.connectTCP(ip, inner_port, factory)
    ftlog.info("Service connect to agent", server_id, agent_id)


def send(dst, data, userheader1='', userheader2=''):
    src = ftcon.global_config["server_id"]
    server_conf = ftcon.getServerConf(src)
    agent_id = server_conf['agent']
    if ide_debug():
        ide_print_pack("Send_[%s]" % dst.split("-")[0], json.loads(data))
    message = agentmsg.packstr(src, dst, '', userheader1, userheader2, data)
    protocol = ftcon.serverid_protocol_map[agent_id]
    ftlog.debug('transport.write', message)
    protocol.transport.write(message)


_QUERY_SLOW_TIME = 0.25


def query(dst, data, userheader1='', userheader2='', timeout=2, notimeoutex=0, returnDeffer=0):
    src = ftcon.global_config["server_id"]
    server_conf = ftcon.getServerConf(src)
    agent_id = server_conf['agent']
    protocol = ftcon.serverid_protocol_map[agent_id]
    if ide_debug():
        ide_print_pack("Query[%s]" % dst.split("-")[0], json.loads(data))
    d = protocol.query(src, dst, userheader1, userheader2, data, timeout, notimeoutex=notimeoutex)
    if returnDeffer == 1:
        return d
    res = stackless.getcurrent()._fttask.waitDefer(d)
    global _QUERY_SLOW_TIME
    if isinstance(res, tuple):
        msg = res[0]
        query_write_time = res[1]
        query_recive_time = res[2]
        ct = time()
        if ct - query_write_time > _QUERY_SLOW_TIME:
            if performance.PERFORMANCE_NET:
                msg = performance.linkMsgTime('DO', msg)
            ftlog.warn('QUERY REPLAY SLOW ! reply=%0.6f' % (query_recive_time - query_write_time),
                       'schedule=%0.6f' % (ct - query_recive_time), 'total=%0.6f' % (ct - query_write_time),
                       'dst=', dst, 'request=', data, 'response=', msg)
        return msg
    return res


def isQuery():
    taskarg = stackless.getcurrent()._fttask.run_args
    return 'query_id' in taskarg


# 封装了response，利用保存在tasklet里的数据，作为回应的参数
# 简化API
def response(data, userheader1=None, userheader2=None):
    taskarg = stackless.getcurrent()._fttask.run_args
    # query包的src，是response的dst
    userheader1 = userheader1 if userheader1 != None else taskarg['userheader1']
    userheader2 = userheader2 if userheader2 != None else taskarg['userheader2']
    _response(taskarg['src'], data, taskarg['query_id'], userheader1, userheader2)


def _response(dst, data, queryid, userheader1, userheader2):
    src = ftcon.global_config["server_id"]
    server_conf = ftcon.getServerConf(src)
    if 'agent' in server_conf:
        agent_id = server_conf['agent']
    else:
        agent_id = dst
        if dst in ftcon.serverid_protocol_map:
            agent_id = dst
        else:
            server_conf = ftcon.getServerConf(dst)
            if 'agent' in server_conf:
                agent_id = server_conf['agent']

    message = agentmsg.packstr(src, dst, queryid, userheader1, userheader2, data)
    protocol = ftcon.serverid_protocol_map[agent_id]
    if performance.PERFORMANCE_NET:
        message = performance.linkMsgTime('LW', message)
    ftlog.debug('transport.write', message)
    if ide_debug():
        ide_print_pack("Resp [%5s]" % dst.split("-")[0], data)
    protocol.transport.write(message)


'''

#getServerId是一个例子, 说明如何取得要路由的serverid

def getServerId(cmd, server_type = '', arg_dict = {}):
    server_id = 0

    if server_type == '': # 按cmd get server_type
        server_type = ftcon.cmd_route_map.get(cmd, '')

    if server_type == '':
        ftlog.error('cmd route error, cmd=', cmd)
        return ''

    serverids = ftcon.server_type_map[server_type]

    if not arg_dict.has_key('mode'):
        ftlog.info('arg_dict not exist mode, default by random')
        server_id = random.choice(serverids)
    else:
        mode = arg_dict['mode']
        if mode == 1:
            server_id = random.choice(serverids)
        elif mode == 2:
            if arg_dict.has_key('userheader'):
                userheader = arg_dict['userheader']
                index = userheader % len(serverids)
                server_id = serverids[index]
            else:
                server_id = random.choice(serverids)
        else:
            server_id = random.choice(serverids)
    return server_id
'''
