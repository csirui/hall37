# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.3.28

import sys

import stackless
from twisted.internet import reactor

import freetime.util.log as ftlog


def _schedule_reactor():
    tc = stackless.getruncount()
    if tc > 1:
        stackless.schedule()


def exitmainloop():
    try:
        reactor.stop()
        ftlog.info('!!!!! reactor.stop !!!!!')
    except:
        pass


REACTOR_RUN_NORMAL = 0


def mainloop():
    if REACTOR_RUN_NORMAL:
        ftlog.info('Main loop begin. REACTOR_RUN_NORMAL')
        stackless.tasklet(reactor.run)()
        reactor.callLater(0, stackless.schedule)
        stackless.run()
        ftlog.info('Main loop over. REACTOR_RUN_NORMAL')
        return

    loopcount = 0  # 测试代码, 有时接到tcp消息, 却不处理, log也不出, 为何?
    r = reactor  # escape eclipse error
    r.startRunning()
    while r._started:
        try:
            while r._started:
                loopcount += 1
                if loopcount > 1000000000:
                    loopcount = 0
                if loopcount % 100 == 0:
                    ftlog.debug("Main loop 100!")
                # Advance simulation time in delayed event processors.
                r.runUntilCurrent()
                _schedule_reactor()
                t2 = r.timeout()
                t = r.running and t2
                r.doIteration(t)
                _schedule_reactor()
        except:
            ftlog.error("Main loop error!")
        else:
            ftlog.info('Main loop terminated.')
        finally:
            _schedule_reactor()
    ftlog.info('Main loop over.')
    sys.exit(0)
