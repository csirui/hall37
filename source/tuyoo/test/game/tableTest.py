# coding=UTF-8
'''牌桌基类测试模块
'''
from poker.entity.game.seat import tySeatStateConst
from poker.entity.game.table_mixin import tyTableStateConst

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>', 
]


import unittest
import random
import sys
import os
import signal

from freetime.util import log as ftlog, processtool
from freetime.entity.msg import MsgPack
from freetime.core.timer import FTTimer

from poker.entity.configure import gdata

        
class Test(unittest.TestCase):

    def setUp(self):
        pass

        
    def tearDown(self):
        pass


    def testGT(self):
        serverId = "GT60011001"
        
        process =processtool.getOneProcessByKeyword("pypy run.py %s" % serverId)
        print "process of %s : %s" % (serverId, process)
        if process :
            os.kill(process.pid, signal.SIGINT)
        
        config_redis=("172.16.8.111", 6379, 0)
#         config_redis=("192.168.10.73", 6379, 0)
        
        sys.argv = sys.argv[0:1]
        sys.argv.append(serverId)
        sys.argv.append(config_redis[0])
        sys.argv.append(config_redis[1])
        sys.argv.append(config_redis[2])
        print sys.path
        print sys.argv
        
        self.asyncTestSuit()
        
        import run
        run.main()


    def asyncTestSuit(self):
        ftlog.debug("=" * 30)
        testStartTime = 0 # seconds
        
#         testStartTime +=1
#         for _ in xrange(1):
#             FTTimer(testStartTime, self.asyncTestOldTable)
     
        testStartTime +=1
        for _ in xrange(1):
            FTTimer(testStartTime, self.asyncTestDoSit)

        ftlog.debug("=" * 30)



    def asyncTestOldTable(self):
        '''测试老Table属性兼容性
        '''
        ftlog.debug("=" * 30)
        tableDemo = gdata.rooms()[60011001].maptable[1]
        
        #_seat的操作
        tableDemo._seat.append([0, tySeatStateConst.PLAYING]) # 兼容老属性
        tableDemo.data.seats.append([0, tySeatStateConst.WAITING]) # 新属性
        tableDemo.data.seats[0].userId = 1234
        tableDemo.data.seats[1].userId = 4321
        print tableDemo.data.seats
        
        #_stat的操作
        with self.assertRaises(AttributeError) : #不允许直接给_stat赋值
            tableDemo._stat = [] 
        tableDemo._stat._update([tyTableStateConst.IDLE])
        print tableDemo._stat


    def asyncTestDoSit(self):
        ftlog.debug("=" * 30)
        shadowRoomId = 60011001
        tableId = 600110010001
        table = gdata.rooms()[shadowRoomId].maptable[tableId]
        clientId = "Android_3.501_tuyoo.YDJD.0-hall6.apphui.happy" 
        userId1 = random.randint(10000, 20000)
        mpSitReq = table.room.makeSitReq(userId1, shadowRoomId, tableId, clientId)
        table.doSit(mpSitReq)
        robotId1 = random.randint(1,10000)
        mpSitReq = table.room.makeSitReq(robotId1, shadowRoomId, tableId, clientId)
        table.doSit(mpSitReq)
        userId2 = random.randint(10000, 20000)
        mpSitReq = table.room.makeSitReq(userId2, shadowRoomId, tableId, clientId)
        table.doSit(mpSitReq)
        

if __name__ == "__main__":
#     sys.argv = ['', 'Test.testTableInit']
    unittest.main()
