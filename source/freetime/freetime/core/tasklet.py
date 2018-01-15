# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.3.28


from time import time

import stackless
from datetime import datetime
from twisted.internet import defer, reactor

import freetime.util.log as ftlog
from channel import FTChannel
from freetime.core.reactor import REACTOR_RUN_NORMAL

DEBUG_TASK_MAIN_TIME = 0
DEBUG_TASK_SCHEDULE = 0
DEBUG_TASK_MAP = {}

SLOW_TASK_TIMES = 0.2


def _tasklet_schedule_cb(prevTask, nextTask):
    global DEBUG_TASK_MAIN_TIME, DEBUG_TASK_MAP, DEBUG_TASK_SCHEDULE
    if not DEBUG_TASK_SCHEDULE:
        return

    pkey = repr(prevTask)
    nkey = repr(nextTask)
    try:
        if pkey == '<tasklet[, 1]>':
            DEBUG_TASK_MAIN_TIME = time()
        if pkey not in DEBUG_TASK_MAP:
            DEBUG_TASK_MAP[pkey] = [(time(), "1st-prev")]
        else:
            DEBUG_TASK_MAP[pkey].append((time(), "prev"))
    except Exception, e:
        print e
        ftlog.info("process pkey error...")

    try:
        if nkey == '<tasklet[, 1]>':
            mts = time() - DEBUG_TASK_MAIN_TIME
            if mts > 0.01:
                ftlog.info("main.task.slow...", time() - DEBUG_TASK_MAIN_TIME)
        if nkey not in DEBUG_TASK_MAP:
            DEBUG_TASK_MAP[nkey] = [(time(), "1st-next")]
        else:
            DEBUG_TASK_MAP[nkey].append((time(), "next"))
    except Exception, e:
        print e
        ftlog.info("process nkey error...")

    ftlog.info("P", prevTask, "N", nextTask)


class FTTasklet():
    BUSY_FLAG = 0
    concurrent_task_count = 0
    MAX_CONCURRENT = 4000
    PEAKVALUE = 0
    PEAKTIME = datetime.now()

    def __init__(self, argl, argd):
        FTTasklet.concurrent_task_count += 1
        if FTTasklet.concurrent_task_count > FTTasklet.PEAKVALUE:
            FTTasklet.PEAKVALUE = FTTasklet.concurrent_task_count
            FTTasklet.PEAKTIME = datetime.now()

        self.run_argl = argl
        self.run_args = argd
        self.handle = argd['handler']
        self.pack = argd.get('pack', None)
        self.udpsrc = argd.get('udpsrc', None)
        self.session = {}  # store some data in current task
        argd['creattime'] = time()

    def tasklet(self):
        global DEBUG_TASK_MAIN_TIME, DEBUG_TASK_MAP, DEBUG_TASK_SCHEDULE, SLOW_TASK_TIMES
        self._return_channel = FTChannel()
        self._me = stackless.getcurrent()
        if DEBUG_TASK_SCHEDULE:
            tkey = repr(self._me)
            DEBUG_TASK_MAP[tkey].insert(0, (self.run_args['creattime'], "create"))
            DEBUG_TASK_MAP[tkey].append((time(), "run"))
        self._timeocall = None
        self._me._fttask = self
        ctn = time()
        try:
            self.handle()
            ct = time()
            rtime = ct - ctn
            time_recv = self.run_args.get('time_recv', 0)
            if time_recv:
                time_recv = ctn - time_recv
            if rtime > SLOW_TASK_TIMES or time_recv > SLOW_TASK_TIMES:
                ftlog.warn('TASKLET TOO SLOW !! runtime=%0.6f' % (rtime), 'schedule=%0.6f' % (time_recv), 'ct=', ct,
                           'args=', self.run_args)
        except:
            ftlog.error('tasklet handle error', self.run_args)
        FTTasklet.concurrent_task_count -= 1
        if DEBUG_TASK_SCHEDULE:
            del DEBUG_TASK_MAP[tkey]

    # Non-blocking sleep...
    def sleepNb(self, timeout):
        d = defer.Deferred()
        reactor.callLater(timeout, d.callback, '')
        return self.waitDefer(d)

    def waitDefer(self, deferred, timeout=0):
        if timeout > 0:
            self._timeocall = reactor.callLater(timeout, self._timeout, deferred)
        deferred.addCallback(self._successful)
        deferred.addErrback(self._error)
        return self._wait_channel()

    def _timeout(self, d):
        ftlog.error("Tasklet.waitDefer timeout!!!", d)
        d.cancel()

    @classmethod
    def create(cls, argl, argd):
        if cls._checkBusy():
            return
        c = FTTasklet(argl, argd)
        if REACTOR_RUN_NORMAL:
            t = stackless.tasklet(c.tasklet)()
            reactor.callLater(0, stackless.schedule)
            return t
        return stackless.tasklet(c.tasklet)()

    @classmethod
    def _checkBusy(self):
        if FTTasklet.concurrent_task_count >= FTTasklet.MAX_CONCURRENT:
            # 只在空闲向繁忙转换时，打印一次
            if FTTasklet.BUSY_FLAG == 0:
                ftlog.error("_checkBusy: too much task(%d)!" % FTTasklet.concurrent_task_count)
            FTTasklet.BUSY_FLAG = 1
            ftlog.warn("_checkBusy: too much task(%d)!" % FTTasklet.concurrent_task_count)
        else:
            # 只在繁忙向空闲转换时，打印一次
            if FTTasklet.BUSY_FLAG == 1:
                ftlog.info("_checkBusy: task count recover(%d)!" % FTTasklet.concurrent_task_count)
            FTTasklet.BUSY_FLAG = 0
        return FTTasklet.BUSY_FLAG

    @classmethod
    def getCurrentFTTasklet(cls):
        return stackless.getcurrent()._fttask

    def _successful(self, resmsg):
        if self._timeocall:
            if self._timeocall.active():
                self._timeocall.cancel()
        self._return_channel.send_nowait(resmsg)

    def _wait_channel(self):
        return self._return_channel.receive()

    def _error(self, fault):
        if self._timeocall:
            if self._timeocall.active():
                self._timeocall.cancel()
        self._return_channel.send_exception_nowait(fault.type, fault.value)
