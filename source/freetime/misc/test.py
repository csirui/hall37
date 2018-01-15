#-*- coding=utf-8 -*-
 
# Author:        zipxing@hotmail.com
# Created:       2015年04月03日 星期五 10时59分44秒
# FileName:      t.py
# 
import stackless
import txredisapi as redis
from twisted.internet import defer, reactor

from freetime.core.reactor import mainloop
import freetime.aio.redis as ftredis
import freetime.util.encry as encry
import freetime.util.log as log
from freetime.core.protocol import FTUDPServerProtocol

gdata={}

@defer.inlineCallbacks
def init():
    redis_pool = redis.lazyConnectionPool(host='127.0.0.1', port=7979, dbid=0, poolsize=10)
    print 'before redis pool'
    con=yield redis_pool._connected
    print redis_pool
    gdata["redis_conn"]=redis_pool


class MyProto(FTUDPServerProtocol):
    def func1(self):
        print self
        print self.gdata
        ftredis.runCmd(self.gdata["redis_conn"], "SET", "ZX", 1)
        print "FFFFF"

    def getTaskletFunc(self, pack):
        return self.func1


init()
print encry.ftcode(1111,'aaaa')
log.loginfo()
mp = MyProto()
print mp
mp.gdata = gdata
reactor.listenUDP(8989, mp)
stackless.tasklet(mainloop)()
stackless.run()
