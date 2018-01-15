# coding: utf-8
'''
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>', 
]

import unittest

import freetime.util.log as ftlog
from freetime.util.log import catchedmethod, getMethodName


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testLog(self):
        
        @catchedmethod
        def errorFun():
            "" + 1
            
        ftlog.debug(file=__file__)
        print "=" * 30 
        
        ftlog.info(getMethodName())
        print "=" * 30 
        
        ftlog.warn(getMethodName())
        print "=" * 30 
            
        ftlog.error(getMethodName())
        print "=" * 30 
         
        errorFun()


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testLog']
    unittest.main()