# -*- coding=utf-8
'''
Created on 2017年3月7日
给日志加标签 用以过滤
@author: nick.kai.lee
'''
from freetime.util import log as FTLOG


class HYLog(object):
    CONST_TAG = "[HENGYANGMAHJONG_LOG]"  # 对象标记

    @classmethod
    def debug(cls, *argl, **argd):
        FTLOG.debug(cls.CONST_TAG, "[DEBUG] -> ", *argl, **argd)

    @classmethod
    def info(cls, *argl, **argd):
        FTLOG.debug(cls.CONST_TAG, "[INFO] -> ", *argl, **argd)

    @classmethod
    def error(cls, *argl, **argd):
        FTLOG.debug(cls.CONST_TAG, "[ERROR] -> ", *argl, **argd)
