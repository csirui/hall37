# coding=UTF-8
'''online测试模块
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>', 
]

import sys;
import unittest

from poker.entity.game import online
from poker.entity.game.online import tyOnlineConst


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testOnlineState(self):
        print "=" * 30
        with self.assertRaises(AssertionError) :
            online.getOnlineState(0)
            
        self.assertEqual(tyOnlineConst.STATE_OFFLINE, online.getOnlineState(1234))
        online.setOnLine(1234)
        self.assertEqual(tyOnlineConst.STATE_ONLINE, online.getOnlineState(1234))
        
    
    def testOnlineLoc(self):
        print "=" * 30
        with self.assertRaises(AssertionError) :
            online.getOnlineLocDict(0)
        with self.assertRaises(AssertionError) :
            online.setOnlineLoc(0, 1, 1)
       
        online.clearOnlineDict(1234)
        online.delOnlineLoc(1234, 60110001, 100)
        self.assertEqual({}, online.getOnlineLocDict(1234))
        online.setOnlineLoc(1234, 60110001, 100, 1)
        self.assertEqual(1, online.getOnlineLocDict(1234)[60110001100])
        online.delOnlineLoc(1234, 60110001, 100)
        self.assertEqual(None, online.getOnlineLocDict(1234).get(60110001100, None))

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.testOnlineState', 'Test.testOnlineLoc']
    unittest.main()