# -*- coding=utf-8 -*-

"""defer工具模块，模块是天然的单例模式
    
"""
__author__ = '"Zhouhao <zhouhao@tuyoogame.com>"'

import freetime.util.log as ftlog


def _succ_cb(*argl, **argd):
    pass


def _error_cb(fault, params, *args, **argd):
    ftlog.error(fault, 'Params=', params, args, argd)


def _error_cb_2(fault, *args, **argd):
    ftlog.error(fault, args, argd)


def setDefaultCallback(defer_, filename, func, *params, **argd):
    defer_.addCallback(_succ_cb)
    defer_.addErrback(_error_cb, params)


def setDefaultCallbackSimple(defer_, params):
    defer_.addCallback(_succ_cb)
    defer_.addErrback(_error_cb_2, params)
