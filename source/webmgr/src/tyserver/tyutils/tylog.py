# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from datetime import datetime
from os.path import sys
import stackless
import traceback

from twisted.python import log
from twisted.python.logfile import DailyLogFile


LOG_LEVEL_DEBUG = 0
LOG_LEVEL_INFO = 1
LOG_LEVEL_ERROR = 2

log_level = 0
log_file_opend = 0
_tracemsg = []


def initLog(log_file, log_path, loglevel=0):
    global log_level, _tracemsg
    log_level = loglevel
    fout = DailyLogFile(log_file, log_path)
    if _tracemsg :
        for msg in _tracemsg :
            fout.write(msg)
            fout.write('\n')
        _tracemsg = None

    class _(log.FileLogObserver):
        log.FileLogObserver.timeFormat = '%m-%d %H:%M:%S.%f'
        def emit(self, eventDict):
            taskinfo = "%r" % stackless.getcurrent() 
            eventDict['system'] = taskinfo[9:-2]   
            log.FileLogObserver.emit(self, eventDict)
    fl = _(fout)
    log.startLoggingWithObserver(fl.emit)


def _log(*argl, **argd):
    argl = ' '.join(map(unicode, argl))
    argd = ' '.join(['%s=%s' % kv for kv in argd.items()])
    return ' '.join([argl, argd])


def _log_bad(*argl, **argd):
    _log_msg = ""
    for l in argl:
        if l == ():
            # empty tuple can't print with %r 
            # TypeError: not enough arguments for format string
            ps = "()"
        else:
            ps = "%r" % l
        if type(l) == str: 
            _log_msg += ps[1:-1] + ' '
        elif type(l) == unicode:
            _log_msg += ps[2:-1] + ' '
        else:
            _log_msg += ps + ' '
    if len(argd) > 0:
        _log_msg += str(argd)
    return _log_msg


def trace(*argl, **argd):
    """
    这个方法仅用于initLog方法之前进行日志打印
    """
    ct = datetime.now().strftime('%m-%d %H:%M:%S.%f')
    msg = ct + ' TRACE ' + _log(*argl, **argd)
    if _tracemsg != None and len(_tracemsg) < 10000 :
        _tracemsg.append(msg)
    return msg


def trace_stdout(*argl, **argd):
    print trace(*argl, **argd)


def info(*argl, **argd):
    if log_level > LOG_LEVEL_INFO:
        return
    print "INFO",
    print _log(*argl, **argd)


def debug(*argl, **argd):
    if log_level > LOG_LEVEL_DEBUG:
        return
    print "DEBUG",

    try :
        _caller = argd["caller"]
        if not hasattr(_caller, "__name__"):
            _caller = _caller.__class__
        callerClsName = _caller.__name__
    except :
        callerClsName = ""
    
    print "[" + callerClsName + "." + sys._getframe().f_back.f_code.co_name + "]",
    
    print _log(*argl, **argd)


def error(*argl, **argd):
    if log_level > LOG_LEVEL_ERROR:
        return
    print "ERROR",
    print _log(*argl, **argd)
    print "--------------------TRACEBACK--------------------"
    traceback.print_exc()
    print "-------------------------------------------------"


def getMethodName():
    return sys._getframe().f_back.f_code.co_name

