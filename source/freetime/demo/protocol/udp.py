#-*- coding=utf-8 -*-
 
# Author:        zipxing@hotmail.com
# Created:       2015年04月06日 星期一 18时23分59秒
# 
import json
import time
import stackless
import struct
import random
from freetime.core.protocol import FTUDPServerProtocol
from freetime.core.timer import FTTimer
from freetime.util.cron import FTCron
import freetime.core.lock as ftlock
import freetime.entity.service as ftsvr
import freetime.support.tcpagent.wrapper as ftagent
import freetime.util.log as ftlog
import freetime.entity.config as ftcon
import freetime.aio.http as fthttp

class Interface:
    def mget(self):
        pass

class InterfaceImpl(Interface):
    def mget(self):
        return ftsvr.doRedis("user01", "HMGET", "user:11111", "name", "clientid")
        

"""
继承freetime提供的protocol基类，
实现getTaskletFunc方法，用于识别请求包，返回对应的tasklet入口执行方法
在这里，可以实现消息注册机制，以便更好的管理消息处理方法
"""
class MyProto(FTUDPServerProtocol):
    _LOCK = ftlock.FTLock("")
    _impl = InterfaceImpl()
    _BIDATA = struct.pack("<IIqqqIIHHIB", int(time.time()), 83180761, 0, 0, 0, 0, 0, 0, 0, 0, 0)


    def doSomeLogic(self):
        #for x in xrange(1):
        now = time.time();
        ftagent.query("GA01", "2222222222222:")
        spent = time.time()-now
        if spent>0.1:
            ftlog.info("SPENT PPS...", spent)
        ftsvr.doRedis("user01", "SET", "zx", 1)
        for x in xrange(50000):
            x = x*2
            x = x/2
                #ftsvr.doRedis("user01", "SET", "zx", 1)
        #ftlog.info("runHttp SENDBI......")
        #fthttp.runHttpNoResponse("POST", 'http://10.3.0.23:10001', 
        #    {'log-type':['chip'], 'log-group':['user1']}, MyProto._BIDATA, 
        #    0.5, {'try' : 0, 'max' : 6})
        #print MyProto._impl.mget()
        #ret, retry, tuse = ftlog.testSendBi('http://10.3.0.23:10001', {'log-type':['chip'], 'log-group':['user1']}, MyProto._BIDATA) 
        #if not ret:
        #    ftlog.info("SENDBI-ERROR", ret, retry, tuse)
        #else:
        #    ftlog.info("SENDBI-OK", ret, retry, tuse)


    def doSomeLogic2(self):
        ftlog.info("MyProto do some logic in tasklet")
        #test redis aio
        ftsvr.doRedis("user01", "SET", "zx", 1)

        #Testing doHttp...
        #code, page = ftsvr.doHttp("GET", "http://www.google.com", 
        #       {'User-Agent': ['Twisted']}) #test connect timeout
        #code, page = ftsvr.doHttp("GET", "http://news.sina.com.cn/", 
        #       {'User-Agent': ['Twisted']}, '', 15, 0.1) #test request timeout
        #page = ftsvr.doHttp("GET", "http://news.sina.com.cn/sssss", 
        #       {'User-Agent': ['Twisted']}) #test 404
        code, page = ftsvr.doHttp("POST", "http://127.0.0.1:8003/", 
                                 {'User-Agent': ['Twisted']}, "HAHAHA")
        print code, page
        print "HTTP", code, len(page), page

        log_data = struct.pack("64s", "HAHAHA")
        ftlog.sendHttpLog("user01", "chip", log_data)

        #pipeline需要加锁，否则结果可能混乱，框架中已经加了lock，参见ftsvr代码
        count = 1000
        pipecount = 100
        st = time.time()
        for x in xrange(count/pipecount):
            if x%100==0:
                ftlog.info(x)
            pl = ftsvr.getRedisPipe("user01")
            for y in xrange(pipecount):
                pl.set("zx", 1)
            result = ftsvr.doRedisPipe(pl)
            if len(result)!=pipecount:
                ftlog.debug("ERRORPIPELINE")
        ftlog.info("SetPerS:", count/(time.time()-st))

        #test ftagent and udpquery
        ftlog.debug(ftcon.getConf("server"), caller=self)
        ftlog.debug(ftsvr.getTaskRunArg())
        ftlog.debug(ftsvr.doUdpQuery("LO01", "abcdefgh"))
        ftlog.debug(ftagent.query("GA01", "TCPTCPSENDBYAGENT"))

        #test cron 
        _tstr = time.strftime('%Y%m%d', time.localtime())
        cron2 = FTCron('{"times_in_day":{"first":"15:00","interval":5, "count":32},\
                        "days":{"first":"%s", "interval":"2m", "count":10}}'%(_tstr))
        ftlog.debug(cron2.getTimeList(), cron2.getDaysList())
        ftlog.debug("SEC=", cron2.getTodayNextLater())

        #test timer
        tr = FTTimer(3, self.timerFunc, 1, 2, 3, aaa=111)


    def timerFunc(self):
        ftlog.debug(ftsvr.getTaskRunArg())


    def madeHandler(self):
        pass


    def lostHandler(self, reason):
        pass


    def parseData(self, data):
        return data
        try:
            return json.loads(data)
        except:
            return None


    def getTaskletFunc(self, argd):
        return self.doSomeLogic


class EchoProto(FTUDPServerProtocol):
    def echoPack(self):
        self.transport.write(ftsvr.getTaskPack(), ftsvr.getTaskUdpSrc())

    def madeHandler(self):
        pass

    def lostHandler(self, reason):
        pass

    def getTaskletFunc(self, argd):
        return self.echoPack

