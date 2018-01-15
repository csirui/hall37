# coding: utf-8
'''
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>', 
]

import unittest

from freetime.core.lock import FTLock, locked
from freetime.util.log import getMethodName

class Room(object) : 
    def __init__(self):
        self.locker = FTLock(self.__class__.__name__ + "_%d" % id(self))
                
    @locked
    def syncChooseTableAndSit(self, userId):
        print "call %s()" % getMethodName()
        result = userId + 10
        print "return %s " % result
        return result
    
class Test(unittest.TestCase):


    def setUp(self):
        self.room = Room()


    def tearDown(self):
        pass


    def testLockedDecorator(self):
        print getMethodName()
        
        self.assertEqual(133, self.room.syncChooseTableAndSit(123))
        
        print "=" * 30 
        
        with self.assertRaises(TypeError) :
            self.room.syncChooseTableAndSit("123")


if __name__ == "__main__":
    import sys;sys.argv = ['', 'Test.testLockedDecorator']
    unittest.main()