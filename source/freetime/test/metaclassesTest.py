# coding: utf-8
'''
'''
from freetime.util.metaclasses import Singleton

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>', 
]

import unittest

import freetime.util.log as ftlog


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testSingleton(self):
      
        class DemoClass(object):
            __metaclass__ = Singleton
            
        
        a = DemoClass()
        print id(a)
        b = DemoClass()
        self.assertEqual(id(a), id(b))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSingleton']
    unittest.main()