# -*- coding:utf-8 -*-
'''
Created on 2016年6月7日

@author: luoguanggui
'''
import functools

import freetime.util.log as ftlog
from freetime.core.timer import FTTimer


class Logger(object):
    def __init__(self, kvs=None):
        self._args = []
        if kvs:
            for k, v in kvs:
                self.add(k, v)

    def add(self, k, v):
        self._args.append('%s=' % (k))
        self._args.append(v)

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


class Heartbeat(object):
    ST_IDLE = 0
    ST_START = 1
    ST_STOP = 2

    def __init__(self, interval, target):
        self._interval = interval
        self._target = target
        self._state = Heartbeat.ST_IDLE
        self._timer = None
        self._logger = Logger()

    def start(self):
        assert (self._state == Heartbeat.ST_IDLE)
        self._state = Heartbeat.ST_START
        self._timer = FTTimer(self._interval, self._onTimer)

    def stop(self):
        if self._state == Heartbeat.ST_START:
            self._state = Heartbeat.ST_STOP
            if self._timer:
                t = self._timer
                self._timer = None
                t.cancel()

    def _onTimer(self):
        try:
            self._timer = None
            newInterval = self._target()
            if newInterval is not None:
                self._interval = newInterval
        except:
            self._logger.error()
            self._interval = 1
        if self._state == Heartbeat.ST_START:
            self._timer = FTTimer(self._interval, self._onTimer)


class HeartbeatAble(object):
    def __init__(self):
        self._heartbeatCount = 0
        self._postTaskList = []
        self._logger = Logger()
        self._heartbeat = Heartbeat(0, self._doHeartbeat)

    def postCall(self, func, *args, **kwargs):
        self.postTask(functools.partial(func, *args, **kwargs))

    def postTask(self, task):
        if self._heartbeat._state != Heartbeat.ST_STOP:
            self._postTaskList.append(task)

    def _startHeartbeat(self):
        self._heartbeat.start()

    def _stopHeartbeat(self):
        self._heartbeat.stop()

    def _doHeartbeat(self):
        self._heartbeatCount += 1
        self._processPostTaskList()
        return self._doHeartbeatImpl()

    def _processPostTaskList(self):
        if self._logger.isDebug():
            self._logger.debug('HeartbeatAble._processPostTaskList',
                               'taskCount=', len(self._postTaskList))
        taskList = self._postTaskList
        self._postTaskList = []
        for task in taskList:
            try:
                task()
            except:
                self._logger.error('task=', task)

    def _doHeartbeatImpl(self):
        raise NotImplemented()
