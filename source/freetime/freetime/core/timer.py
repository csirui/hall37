# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com, zhouhao@tuyoogame.com
# Created:       2015.3.28

import functools
import sys
from time import time

from twisted.internet import reactor

import freetime.util.log as ftlog
from tasklet import FTTasklet


class FTTimer():
    """
    封装calllater,启动tasklet的机制...
    """

    def __init__(self, interval, task_handler, *argl, **argd):
        #         self.interval = interval
        self.task_handler = task_handler
        self.argl = argl
        self.argd = argd
        self.handle = reactor.callLater(interval, self._onTime)

        if ftlog.is_debug():
            timerCaller = sys._getframe().f_back.f_code.co_name
            timerCallee = task_handler.func.func_name if isinstance(task_handler,
                                                                    functools.partial) else task_handler.func_name
            if "HeartBeat" not in timerCallee:
                ftlog.debug("|timerCaller, timerCallee, interval:", timerCaller, timerCallee, interval, caller=self)

    def _onTime(self):
        timerCallee = self.task_handler.func.func_name if isinstance(self.task_handler,
                                                                     functools.partial) else self.task_handler.func_name
        if "HeartBeat" not in timerCallee:
            ftlog.debug("<<", "|timerCallee:", timerCallee, caller=self)

        self.argd["handler"] = self.task_handler
        FTTasklet.create(self.argl, self.argd)

    def cancel(self):
        if not self.handle:
            return False
        try:
            self.handle.cancel()
        except:
            pass
        self.handle = None
        return True

    def isActive(self):
        if self.handle:
            return self.handle.active()
        return False

    def getTimeOut(self):
        ts = self.handle
        if not ts:
            return 0.0
        try:
            return ts.getTime()
        except:
            pass
        return 0.0

    def reset(self, interval):
        ts = self.handle
        if ts:
            try:
                ts.reset(interval)
                return True
            except:
                pass
        return False


class FTLoopTimer():
    """
    封装calllater,启动tasklet的机制...
    loopCount 为－1时，不停止的进行timer触发调用
    loopCount 大于0时，循环触发loopCount次调用
    每次触发均使用新的tasklet进行调用 task_handler(*argl, **argd)
    必须显示调用timer.start()才能启动此timer
    """

    def __init__(self, interval, loopCount, task_handler, *argl, **argd):
        self.interval = interval
        self.loopCount = int(loopCount)
        self.task_handler = task_handler
        self.argl = argl if argl else []
        self.argd = argd if argd else {}
        self.handle = None

    def __repr__(self):
        return '<freetime.core.timer.FTLoopTimer instance at 0x%016x of handler %s>' % (id(self), self.task_handler)

    def start(self):
        if self.handle == None:
            self._start()

    def _start(self):
        self.handle = reactor.callLater(self.interval, self._onTime)

    def _onTime(self):
        targd = {}
        targd["handler"] = self._invoke
        FTTasklet.create([], targd)

    def _invoke(self):
        try:
            self.task_handler(*self.argl, **self.argd)
        except:
            ftlog.error()
            pass

        if self.loopCount == -1:
            self._start()
        elif self.loopCount > 0:
            self.loopCount -= 1
            self._start()

    def cancel(self):
        if self.handle:
            try:
                self.handle.cancel()
            except:
                pass
        self.loopCount = 0
        self.handle = None
        return True

    def getTimeOut(self):
        ts = self.handle
        if not ts:
            return 0.0
        try:
            return int(ts.getTime() - time())
        except:
            ftlog.error()
            pass
        return 0.0

    def reset(self, interval):
        ts = self.handle
        if ts:
            try:
                ts.reset(interval)
                return True
            except:
                ftlog.error()
                pass
        return False
