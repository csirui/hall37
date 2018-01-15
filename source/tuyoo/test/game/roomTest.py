# coding=UTF-8
'''房间基类测试模块
'''

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

    def testGR(self):
        serverId = "GR60011"
        
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
        
        self.testSuit()
        
        import run
        run.main()

    def testSuit(self):
        ftlog.debug("=" * 30)
        testStartTime = 0 # seconds
        
#         testStartTime +=1
#         for _ in xrange(10):
#             FTTimer(testStartTime, self.asyncTestQuickStartPlayerSelectTable)
     
        testStartTime +=1
        for _ in xrange(10):
            FTTimer(testStartTime, self.asyncTestRoomQuickStart)

        ftlog.debug("=" * 30)


    def asyncTestRoomQuickStart(self):
        roomId = 60011000
        ftlog.debug('start testing...',
                    caller=self)
        mpRoomQuickStartReq = MsgPack()
        mpRoomQuickStartReq.setCmd("room")
        mpRoomQuickStartReq.setParam("action", "quick_start")
        mpRoomQuickStartReq.setParam("userId", random.randint(10001, 20000))
        mpRoomQuickStartReq.setParam("tableId", 0)
        mpRoomQuickStartReq.setParam("roomId", roomId)
        gdata.rooms()[roomId].doQuickStart(mpRoomQuickStartReq)
      

    def asyncTestQuickStartPlayerSelectTable(self):
        roomId = 60011000
        ftlog.debug('start testing...',
                    caller=self)
        mpRoomQuickStartReq = MsgPack()
        mpRoomQuickStartReq.setCmd("room")
        mpRoomQuickStartReq.setParam("action", "quick_start")
        mpRoomQuickStartReq.setParam("userId", random.randint(10001, 20000))
        mpRoomQuickStartReq.setParam("tableId", 1)
        mpRoomQuickStartReq.setParam("roomId", roomId)
        mpRoomQuickStartReq.setParam("shadowRoomId", roomId + 1)
        gdata.rooms()[roomId].doQuickStart(mpRoomQuickStartReq)
      
        
#         mpRoomQuickStartReq.setParam("tableId", 0)
#         gdata.rooms()[roomId].doQuickStart(mpRoomQuickStartReq)
        


if __name__ == "__main__":
#     sys.argv = ['', 'Test.testRoomQuickStart']
    unittest.main()
