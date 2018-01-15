# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

 
import stackless
import sys

from twisted.internet import defer, reactor

from tyserver.tytasklet.tychannel import TYChannel
from tyserver.tyutils import tylog


class TyTasklet():

    BUSY_FLAG = 0
    concurrent_task_count = 0
    MAX_CONCURRENT = 10000

    def __init__(self, argl, argd):
        TyTasklet.concurrent_task_count += 1
        self.run_argl = argl
        self.run_args = argd
        self.handle = argd['handler']
        self.pack = argd.get('pack', None)
        self.udpsrc = argd.get('udpsrc', None)
        self.session = {}  # store some data in current task


    def tasklet(self):
        self._return_channel = TYChannel()
        self._me = stackless.getcurrent()
        self._timeocall = None
        self._me._fttask = self
        try:
            self.handle()
        except:
            tylog.error('tasklet handle error')
        TyTasklet.concurrent_task_count -= 1


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
        tylog.error("Tasklet.waitDefer timeout!!!", d)
        d.cancel()


    @classmethod
    def create(cls, argl, argd):
        if cls._checkBusy():
            return
        c = TyTasklet(argl, argd)
        t = stackless.tasklet(c.tasklet)()
        reactor.callLater(0, stackless.schedule)
        return t


    @classmethod
    def _checkBusy(self):
        if TyTasklet.concurrent_task_count >= TyTasklet.MAX_CONCURRENT:
            # 只在空闲向繁忙转换时，打印一次
            if TyTasklet.BUSY_FLAG == 0:
                tylog.error("_checkBusy: too much task(%d)!" % TyTasklet.concurrent_task_count)
            TyTasklet.BUSY_FLAG = 1
        else:
            # 只在繁忙向空闲转换时，打印一次
            if TyTasklet.BUSY_FLAG == 1:
                tylog.info("_checkBusy: task count recover(%d)!" % TyTasklet.concurrent_task_count)
            TyTasklet.BUSY_FLAG = 0
        return TyTasklet.BUSY_FLAG

    
    @classmethod
    def getCurrentTyTasklet(cls):
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


def _schedule_reactor():
    tc = stackless.getruncount()
    if tc > 1:
        stackless.schedule()


def mainloop():
    tylog.info('Main loop begin.')
    stackless.tasklet(reactor.run)()
    reactor.callLater(0, stackless.schedule)
    stackless.run()
    tylog.info('Main loop over.')
    sys.exit(0)
