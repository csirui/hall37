# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import os
import traceback

from datetime import datetime

from tyserver.tyutils import tylog, fsutils

_logf = None
_with_std = 0


def open_act_log(options, action):
    global _logf
    close_act_log()
    logpath = options.logpath
    fpath = fsutils.appendPath(logpath, 'action.' + action['uuid'] + '.log')
    if 'DEBUG' in os.environ:
        _logf = None
    else:
        _logf = open(fpath, 'a')
    action['logfile'] = fpath
    pass


def close_act_log():
    global _logf
    if _logf:
        log('-------- done --------')
        _logf.close()
        _logf = None


def log(*argl, **argd):
    global _logf
    ct = datetime.now().strftime('%m-%d %H:%M:%S.%f ')
    msg = ct + tylog._log(*argl, **argd)
    if _logf:
        _logf.write(msg + '\n')
        _logf.flush()
        if _with_std:
            print msg
    else:
        print msg


def error(*argl, **argd):
    global _logf
    log('ERROR', *argl, **argd)
    log("-------------------- TRACEBACK --------------------")
    traceback.print_exc(file=_logf)
    if _with_std:
        traceback.print_exc()
    log("-------------------- Call Stack -------------------")
    traceback.print_stack(file=_logf)
    if _with_std:
        traceback.print_stack()
    log("-------------------------------------------------")


class FormatPrintInfo(object):
    def __init__(self, mainhead, datadict, fixsize=0):
        self.lines = []
        self.fixsize = fixsize
        self.maxsize = 0
        self.mainhead = mainhead
        self.datadict = datadict

    def push_line(self, key):
        data = self.datadict.get(key, None)
        if data != None:
            self.maxsize = max(self.maxsize, len(key))
            self.lines.append([key, data])

    def printout(self):
        tsize = self.fixsize
        if tsize == 0:
            tsize = self.maxsize
        fmt = self.mainhead + ' %-' + str(tsize) + 's = %s'
        log('--------------------------------------------------------------------------------')
        for x in self.lines:
            log(fmt % (str(x[0]), str(x[1])))
        log('--------------------------------------------------------------------------------')
