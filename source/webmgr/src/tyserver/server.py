# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import stackless

from tyserver.tycmds import InitFlg
from tyserver.tytasklet.tylisten import listenHttp, listenWs
from tyserver.tytasklet.tytasklet import mainloop, TyTasklet
from tyserver.tyutils import tylog, fsutils


def startup(options):

    logfile = getattr(options, 'logfile', None)
    if logfile :
        tylog.info('Open Log File :', logfile)
        log_path = fsutils.getParentDir(logfile)
        log_file = fsutils.getLastPathName(logfile)
        tylog.initLog(log_file, log_path)

    port = getattr(options, 'httpport', 0)
    if port > 0 :
        listenHttp(port)
        
    port = getattr(options, 'wsport', 0)
    if port > 0 :
        listenWs(port)

    initfunc = getattr(options, 'initialize', None)
    if not callable(initfunc) :
        InitFlg.isInitOk = 1
        initfunc = None
    else:
        InitFlg.isInitOk = 0
        
    heartbeatfunc = getattr(options, 'heartbeat', None)
    if not callable(heartbeatfunc) :
        heartbeatfunc = None

    if heartbeatfunc or initfunc :
        def serverinit():
            hc = 0
            if initfunc :
                try:
                    initfunc(options)
                    InitFlg.isInitOk = 1
                except:
                    tylog.error()
                    return
            while 1 :
                tasklet = stackless.getcurrent()._fttask
                tasklet.sleepNb(1)
                try:
                    heartbeatfunc(hc)
                except:
                    tylog.error()
                hc = hc + 1
        TyTasklet.create([], {"handler":serverinit})

    mainloop()

