# coding: utf-8
'''
'''
import functools

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>', 
]

import unittest
import stackless

from freetime.core.timer import FTTimer
from freetime.util.log import getMethodName
from freetime.core.reactor import mainloop, exitmainloop


class Test(unittest.TestCase):


    def setUp(self):
        pass
    

    def tearDown(self):
        exitmainloop()


    def testTimer(self):
        
        print "call %s" % getMethodName()
        
        def fun1(x):
            print "call %s" % getMethodName()
            print x*10
        
        func = functools.partial(fun1, 1)
        timer = FTTimer(1, func)
        
        stackless.tasklet(mainloop)()
        stackless.run()


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testTimer']
    unittest.main()