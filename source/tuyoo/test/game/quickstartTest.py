# coding=UTF-8
'''quickstart测试模块
'''
import random

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>', 
]

import unittest
import sys
import os
import signal

from freetime.util import processtool
from freetime.util import log as ftlog
from freetime.entity.msg import MsgPack
from freetime.core.timer import FTTimer

from poker.entity.configure import configure, pokerconf
from poker.entity.dao import onlinedata, userchip, userdata
from poker.entity.game.quick_start import BaseQuickStartDispatcher


# class Test(unittest.TestCase):
class Test():


    def setUp(self):
        serverId = "UT001"
        
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


    def tearDown(self):
        pass


    def testSuit(self):
        ftlog.debug("=" * 30)
        testStartTime = 0 # seconds
        
        testStartTime +=1
        for _ in xrange(1):
            FTTimer(testStartTime, self.testReconnect)
        
        testStartTime +=1
        for _ in xrange(1):
            FTTimer(testStartTime, self.testQuickStart)
              
        testStartTime +=1
        for _ in xrange(1):
            FTTimer(testStartTime, self.testQuickEnterRoom)
              
        testStartTime +=1
        for _ in xrange(1):
            FTTimer(testStartTime, self.testQuickEnterTable)
         
        ftlog.debug("=" * 30)
                
                
    def testReconnect(self):
        '''测试断线重连
        '''
        gameId = 6
        userId = random.randint(10000, 20000)
        roomId = 60011001
        tableId = 1
        seatId = 3
        clientId = "Android_3.501_tuyoo.YDJD.0-hall6.apphui.happy"
        playMode = "happy"
        
        onlinedata.setOnlineState(userId, onlinedata.ONLINE)
        onlinedata.addOnlineLoc(userId, roomId, tableId, seatId)
        
        msg = MsgPack()
        msg.setCmd("quick_start")
        msg.setParam("userId", userId)
        msg.setParam("roomId", roomId)
        msg.setParam("tableId", tableId)
        msg.setParam("clientId", clientId)
        print '='*30
        print msg
        BaseQuickStartDispatcher.dispatchQuickStart(msg, userId, gameId, roomId, tableId, playMode, clientId)
        print '='*30

        
    def testQuickStart(self):
        '''测试快速开始'''
        gameId = 6
        userId = random.randint(10000, 20000)
        roomId = 0
        tableId = 0
        chip = 800
        clientId = "Android_3.501_tuyoo.YDJD.0-hall6.apphui.happy"
        playMode = "happy"
        
        onlinedata.setOnlineState(userId, onlinedata.ONLINE)
        onlinedata.cleanOnlineLoc(userId)
        
        userdata.setAttr(userId, "sessionClientId", clientId)
#         datas = sessiondata._getUserSessionValues(userId)
#         ftlog.debug("|userId, session:", userId, datas)
        
        oldChip = userchip.getChip(userId)
        userchip.incrChip(userId, gameId, chip - oldChip, 0, "GM_ADJUST_COIN", 0, clientId)
        
        msg = MsgPack()
        msg.setCmd("quick_start")
        msg.setParam("gameId", gameId)
        msg.setParam("userId", userId)
#         msg.setParam("roomId", roomId)
#         msg.setParam("tableId", tableId)
        msg.setParam("clientId", clientId)
        print '='*30
        print msg
        BaseQuickStartDispatcher.dispatchQuickStart(msg, userId, gameId, roomId, tableId, playMode, clientId)
        print '='*30
        
        
    def testQuickEnterRoom(self):
        '''测试快速进入房间'''
        gameId = 6
        userId = random.randint(10000, 20000)
        roomId = 6001
        tableId = 0
        clientId = "Android_3.501_tuyoo.YDJD.0-hall6.apphui.happy"
        playMode = "happy"
        
        onlinedata.setOnlineState(userId, onlinedata.ONLINE)
        onlinedata.cleanOnlineLoc(userId)
        
        msg = MsgPack()
        msg.setCmd("quick_start")
        msg.setParam("userId", userId)
        msg.setParam("roomId", roomId)
#         msg.setParam("tableId", tableId)
        msg.setParam("clientId", clientId)
        print '='*30
        print msg
        BaseQuickStartDispatcher.dispatchQuickStart(msg, userId, gameId, roomId, tableId, playMode, clientId)
        print '='*30


    def testQuickEnterTable(self):
        '''测试快速进入桌子'''
        gameId = 6
        userId = random.randint(10000, 20000)
        roomId = 60011001
        tableId = 1
        clientId = "Android_3.501_tuyoo.YDJD.0-hall6.apphui.happy"
        playMode = "happy"
        
        onlinedata.setOnlineState(userId, onlinedata.ONLINE)
        onlinedata.cleanOnlineLoc(userId)
        
        msg = MsgPack()
        msg.setCmd("quick_start")
        msg.setParam("userId", userId)
        msg.setParam("roomId", roomId)
        msg.setParam("tableId", tableId)
        msg.setParam("clientId", clientId)
        print '='*30
        print msg
        BaseQuickStartDispatcher.dispatchQuickStart(msg, userId, gameId, roomId, tableId, playMode, clientId)
        print '='*30


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testQuickStart', 'Test.testReconnect']
#     unittest.main()
    Test().setUp()