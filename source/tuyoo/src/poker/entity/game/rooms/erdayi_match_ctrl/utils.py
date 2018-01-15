# -*- coding:utf-8 -*-
'''
Created on 2016年5月13日

@author: zhaojiangang
'''

import functools

import freetime.util.log as ftlog
from freetime.core.timer import FTTimer


class Heartbeat(object):
    ST_IDLE = 0
    ST_START = 1
    ST_STOP = 2

    def __init__(self, target, interval):
        self._target = target
        self._state = Heartbeat.ST_IDLE
        self._count = 0
        self._postTaskList = []
        self._timer = None
        self._interval = interval
        self._logger = Logger()
        self._init = False

    def start(self):
        assert (self._state == Heartbeat.ST_IDLE)
        self._state = Heartbeat.ST_START
        self._timer = FTTimer(0, self._onInit)

    def stop(self):
        if self._state != Heartbeat.ST_STOP:
            self._state = Heartbeat.ST_STOP
            if self._timer:
                self._timer.cancel()
            self._timer = None

    @property
    def count(self):
        return self._count

    def postCall(self, func, *args, **kwargs):
        self.postTask(functools.partial(func, *args, **kwargs))

    def postTask(self, task):
        if self._state != Heartbeat.ST_STOP:
            self._postTaskList.append(task)
            if self._init and self._timer:
                self._timer.cancel()
                self._timer = FTTimer(0, self._onTimeout)

    def _onInit(self):
        try:
            self._timer = None
            interval = self._target.onInit()
            if interval:
                self._interval = interval
            self._scheduleTimer()
        except:
            self._logger.error('Heartbeat._onInit')

    def _onTimeout(self):
        try:
            self._timer = None
            self._count += 1
            self._processPostTaskList()
            interval = self._target.onHeartbeat()
            if interval is not None:
                self._interval = interval
        except:
            self._interval = 1
            self._logger.error('Heartbeat._onTimeout')
        self._scheduleTimer()

    def _scheduleTimer(self):
        if self._state == Heartbeat.ST_START:
            interval = 0 if self._postTaskList else self._interval
            self._timer = FTTimer(interval, self._onTimeout)

    def _processPostTaskList(self):
        taskList = self._postTaskList
        self._postTaskList = []
        for task in taskList:
            try:
                task()
            except:
                self._logger.error('task=', task)


class HeartbeatAble(object):
    def __init__(self, interval):
        self._heart = Heartbeat(self, interval)

    def startHeart(self):
        self._heart.start()

    def stopHeart(self):
        self._heart.stop()

    def onInit(self):
        return self._doInit()

    def onHeartbeat(self):
        return self._doHeartbeat()

    def _doInit(self):
        return 1

    def _doHeartbeat(self):
        return 1


class Logger(object):
    def __init__(self, kvs=None):
        self._args = []
        if kvs:
            for k, v in kvs:
                self.add(k, v)

    def add(self, k, v):
        self._args.append('%s=' % (k))
        self._args.append(v)

    def hinfo(self, prefix=None, *args):
        self._log(prefix, ftlog.hinfo, *args)

    def info(self, prefix=None, *args):
        self._log(prefix, ftlog.info, *args)

    def debug(self, prefix=None, *args):
        self._log(prefix, ftlog.debug, *args)

    def warn(self, prefix=None, *args):
        self._log(prefix, ftlog.warn, *args)

    def error(self, prefix=None, *args):
        self._log(prefix, ftlog.error, *args)

    def isDebug(self):
        return ftlog.is_debug()

    def _log(self, prefix, func, *args):
        argl = []
        if prefix:
            argl.append(prefix)
        argl.extend(self._args)
        argl.extend(args)
        func(*argl)
