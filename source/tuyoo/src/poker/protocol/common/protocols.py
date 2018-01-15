# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import freetime.entity.service as ftsvr
import freetime.util.log as ftlog
from freetime.core.protocol import FTHttpRequest, FTHttpChannel
from freetime.core.tasklet import FTTasklet
from freetime.entity.msg import MsgPack
from freetime.support.tcpagent.protocol import S2AProtocol
from poker.entity.configure import gdata
from poker.protocol import runhttp, runcmd


class TYCommonHttpRequest(FTHttpRequest):
    '''
    通用的HTTP协议
    '''

    def handleRequest(self):
        taskarg = ftsvr.getTaskRunArg()
        request = taskarg['data']
        if not gdata.initializeOk():
            ftlog.info('TYCommonHttpRequest not initialize ok, ignore this request :', request.path)
            request.setResponseCode(503)
            request.finish()
            return
        runhttp.handlerHttpRequest(request)


class TYCommonHttpChannel(FTHttpChannel):
    requestFactory = TYCommonHttpRequest


class TYCommonS2AProto(S2AProtocol):
    """
    通用的S2A协议
    """

    def getTaskletFunc(self, argd):
        return self.doSomeLogic

    def parseData(self, data):
        msg = MsgPack()
        try:
            msg.unpack(data)
            return msg
        except:
            raise Exception('the json data error 1 !! [' + repr(data) + ']')

    def doSomeLogic(self):
        args = ftsvr.getTaskRunArg()
        src = args.get('src')
        dst = args.get('dst')
        userheader1 = args.get('userheader1')
        userheader2 = args.get('userheader2')
        msg = ftsvr.getTaskPack()
        #         ftlog.debug('TYCommonS2AProto id=', id(self), 'src=', src, 'dst=', dst, 'h1=', userheader1, 'h2=', userheader2, 'pack=', msg)
        if not gdata.initializeOk():
            ftlog.info('TYCommonS2AProto not initialize ok, ignore this message :', src, dst, userheader1, userheader2,
                       msg)
            return
        runcmd.handlerCommand(msg)


def onAgentSelfCommand(agentProtocol, src, queryid, userheader1, userheader2, message):
    # 处理AGENT自身的命令, 而非转发的命令
    msg = MsgPack()
    try:
        msg.unpack(message)
    except:
        raise Exception('the json data error 2 !! [' + repr(message) + ']')

    task = FTTasklet.getCurrentFTTasklet()
    task.pack = msg
    task.run_args['src'] = src
    task.run_args['pack'] = msg
    if queryid:
        task.run_args['query_id'] = queryid
    task.run_args['userheader1'] = userheader1
    task.run_args['userheader2'] = userheader2
    runcmd.handlerCommand(msg)
