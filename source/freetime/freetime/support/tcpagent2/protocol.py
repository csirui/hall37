"""
 server之间通过agent通信拓扑图：

 ----------      -------------              -------------      ----------
|SERVER-s2a|----|a2s-AGENT-a2a|------------|a2a-AGENT-a2s|----|s2a-Server|
 ----------      -------------              -------------      ----------

 a2a用于agent之间相连，用于listenTcp和connectTcp
 a2s用于agent listen server
 s2a用于server connect agent，s2a需要扩展挂接逻辑功能

# 2015.4.14 by zipxing@hotmail.com
# 2015.4.17 modifiedby zhouhao@tuyoogame.com
"""

import stackless
from twisted.internet import defer, reactor
from twisted.python import failure

import freetime.entity.config as ftcon
import freetime.util.log as ftlog
from freetime.core.protocol import FTHead4ServerProtocol, FTTimeoutException, \
    _countProtocolPack
from freetime.support.tcpagent2 import agentmsg


class AgentProtocolMixin(FTHead4ServerProtocol):
    """A2A、A2S、S2A通用代码父类
    """

    def __init__(self):
        # 对端agent的id
        self.peer_id = 0

    def madeHandler(self):
        self.register_self()

    def lostHandler(self, reason):
        ftlog.info(self, 'connection lost, reason=', reason, 'errmsg=', reason.getErrorMessage())

    def register_self(self):
        server_id = ftcon.global_config["server_id"]
        message = agentmsg.packstr(server_id, '', '', '', '', '{"cmd":"register_self"}')
        self.transport.write(message)


class A2AProtocol(AgentProtocolMixin):
    """
    运行在Agent进程内，用于Agent之间连接的协议，
    既用于listenTcp，又用于connectTcp
    """
    onCommand = None  # TODO 在AGENT进程同样要处理一些自身的命令, 例如, 配置变化, 如何挂接? 暂时采用类变量的方式进行挂接

    def getTaskletFunc(self, pack):
        return self.onMsg

    def onMsg(self):
        pack = stackless.getcurrent()._fttask.pack
        ftlog.debug('A2AProtocol->[' + pack + ']')
        src, dst, queryid, userheader1, userheader2, message = agentmsg.unpack(pack)
        if src == None or dst == None:
            ftlog.info("ERROR, recive a error format message")
            return

        if self.peer_id == 0:
            self.peer_id = src
            ftcon.serverid_protocol_map[self.peer_id] = self
            ftlog.info("Receive other agent register, agentid=", self.peer_id)
            return

        # 处理agent服务自身的命令
        if dst == ftcon.global_config["server_id"] and A2AProtocol.onCommand != None:
            #             ftlog.debug('A2AProtocol-> it self command !!')
            A2AProtocol.onCommand(self, src, queryid, userheader1, userheader2, message)
            return

        try:
            # 从其他agent过来的数据，转给连接的dst service
            #             ftlog.debug('A2AProtocol->send to target->', dst)
            protocol = ftcon.serverid_protocol_map[dst]
            protocol.transport.write(pack + '\r\n')
        except:
            ftlog.error('msg route error, dst_server_id=', dst)


class A2SProtocol(AgentProtocolMixin):
    """
    运行在Agent进程内，用于监听Server的连接
    用于listenTcp
    """

    onCommand = None  # TODO 在AGENT进程同样要处理一些自身的命令, 例如, 配置变化, 如何挂接? 暂时采用类变量的方式进行挂接

    #     def onCommand(self, queryid, userheader1, userheader2, message):
    #         # 处理AGENT自身的命令, 而非转发的命令
    #         pass


    def getTaskletFunc(self, pack):
        return self.onMsg

    def onMsg(self):
        pack = stackless.getcurrent()._fttask.pack
        ftlog.debug('A2SProtocol->[' + pack + ']')
        src, dst, queryid, userheader1, userheader2, message = agentmsg.unpack(pack)
        if src == None or dst == None:
            ftlog.info("ERROR, recive a error format message")
            return
        if self.peer_id == 0:
            self.peer_id = src
            ftcon.serverid_protocol_map[self.peer_id] = self
            ftlog.info("Receive service register, serverid=", self.peer_id, self)
            return

        # 处理agent服务自身的命令
        if dst == ftcon.global_config["server_id"] and A2SProtocol.onCommand != None:
            #             ftlog.debug('A2SProtocol-> it self command !!')
            A2SProtocol.onCommand(self, src, queryid, userheader1, userheader2, message)
            return

        if dst.find('AG') == 0:  # 如果是直接发送给另外的一个AGENT, 那器agent就是其本身
            agent_id = dst
        else:
            server_conf = ftcon.getServerConf(dst)
            agent_id = server_conf['agent']
        try:
            # 从src发过来的数据，转给dst所在的agent
            # 如果是agent所属内部进程过来的数据, 直接转发至dst进程
            if agent_id == ftcon.global_config["server_id"]:
                agent_id = dst
            # ftlog.debug('A2SProtocol->send to agentid->', agent_id, 'dst=', dst)
            protocol = ftcon.serverid_protocol_map[agent_id]
            protocol.transport.write(pack + '\r\n')
        except:
            ftlog.error('msg route error, not found agent protocol, dst_server_id=', dst, 'agend=', agent_id)


_LIVE_MESSAGES = {}
_FAILED_MESSAGES = {}
_QUERY_ID = 0


class S2AProtocol(AgentProtocolMixin):
    def __init__(self):
        self.peer_id = 0

    def lineReceived(self, data):
        ftlog.debug('S2AProtocol->lineReceived', data)
        src, dst, query_id, userheader1, userheader2, msg = agentmsg.unpack(data)
        if src == None or dst == None:
            ftlog.info("ERROR, recive a error format message")
            return

        if self.peer_id == 0:
            self.peer_id = src
            ftcon.serverid_protocol_map[self.peer_id] = self
            ftlog.info('receive register, agentid=', self.peer_id)
            return

        _countProtocolPack(1, self)

        # send过来的数据
        if query_id == '':
            self._runTasklet(data=msg, src=src, dst=dst, userheader1=userheader1, userheader2=userheader2)
        else:
            querysrc, _ = query_id.split('.')
            server_id = ftcon.global_config["server_id"]
            # query本服务的请求
            if querysrc != server_id:
                self._runTasklet(data=msg, src=src, dst=dst, query_id=query_id, userheader1=userheader1,
                                 userheader2=userheader2)
            # response回来的请求
            else:
                if userheader1 == 'RQ':  # 本进程内, 异步查询本进程的其他消息接口
                    self._runTasklet(data=msg, src=src, dst=dst, query_id=query_id, userheader1=userheader1,
                                     userheader2=userheader2)
                else:
                    d, c = None, None
                    #                     ftlog.debug('lineReceived', query_id, id(_LIVE_MESSAGES), id(self))
                    if query_id in _LIVE_MESSAGES:
                        d, c = _LIVE_MESSAGES[query_id]
                        del _LIVE_MESSAGES[query_id]
                    else:
                        if query_id in _FAILED_MESSAGES:
                            del _FAILED_MESSAGES[query_id]
                            ftlog.warn('QUERY TOO SLOW !!', query_id, msg, 'left bad querids=', _FAILED_MESSAGES)
                            if len(_FAILED_MESSAGES) > 100:
                                _FAILED_MESSAGES.clear()
                        else:
                            ftlog.warn('NOT KNOW of query_id->', query_id, msg)
                    if d and c:
                        try:
                            c.cancel()
                            d.callback(msg)
                        except:
                            ftlog.error(msg)

    def getTaskletFunc(self, pack):
        pass

    def query(self, src, dst, userheader1, userheader2, data, timeout):
        try:
            if self.transport:
                global _QUERY_ID
                resultDeferred = defer.Deferred()
                _QUERY_ID += 1
                query_id = src + '.' + str(_QUERY_ID)
                msg = agentmsg.packstr(src, dst, query_id, userheader1, userheader2, data)
                cancelCall = reactor.callLater(timeout, self._clearFailed, resultDeferred, query_id, msg)
                _LIVE_MESSAGES[query_id] = (resultDeferred, cancelCall)
                ftlog.debug('transport.write', msg)
                self.transport.write(msg)
                return resultDeferred
            else:
                ftlog.error('tcpquery : not connected !! ', self)
        except:
            ftlog.error('tcpquery exception : agentid=', self.peer_id)
        return None

    def _clearFailed(self, deferred, query_id, msg):
        try:
            del _LIVE_MESSAGES[query_id]
        except KeyError:
            pass
        _FAILED_MESSAGES[query_id] = 1
        ftlog.error('TCP TimeoutException of->', msg)
        deferred.errback(failure.Failure(FTTimeoutException(str(query_id))))
