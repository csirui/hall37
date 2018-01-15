# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''


class RobotEvent(object):
    def __init__(self, delayTime, cmd, *argl, **argd):
        self.delayTime = delayTime
        self.cmd = cmd
        self.argl = argl
        self.argd = argd
