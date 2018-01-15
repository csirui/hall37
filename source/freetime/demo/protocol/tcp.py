#-*- coding=utf-8 -*-
 
# Author:        zipxing@hotmail.com
# Created:       2015年04月06日 星期一 18时23分59秒
# 
import freetime.entity.service as ftsvr
import freetime.util.log as ftlog
import freetime.support.tcpagent.wrapper as ftagent
from freetime.support.tcpagent.protocol import S2AProtocol

"""
继承freetime提供的protocol基类，
实现getTaskletFunc方法，用于识别请求包，返回对应的tasklet入口执行方法
在这里，可以实现消息注册机制，以便更好的管理消息处理方法
"""
class S2AProto(S2AProtocol):
    def doSomeLogic(self):
        ftlog.debug(ftsvr.getId(), "receive from agent", ftsvr.getTaskPack())

        taskarg = ftsvr.getTaskRunArg()
        print taskarg

        #这里简单调用response即可，不需要指定dst
        #框架会使用保存在tasklet的arg字典里的信息
        #自动设置回应包的src和dst
        ftagent.response("RESPONSE-TCP-QUERY")


    def getTaskletFunc(self, argd):
        #if pack.cmd=='dosomelogic': 
        return self.doSomeLogic


