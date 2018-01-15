#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
框架中核心的风格工具
利用大量的`Assert`来替代简单的if判断
最大化的减少代码中的if分支

框架本身使用if是为了尽可能的减少Assert的调用开销

部分常见的for循环也可以统一到这里有个明确的名字
比如:
* 遍历所有的用户
* 遍历给定的用户们
* until循环
* each循环
"""
import json
import logging
import os
import sys
import time

profiler_logger = logging.getLogger("profiler")
debug_logger = logging.getLogger("debug")
logger = logging.getLogger("default")

__DEBUG = False
__IDE_DEBUG = os.environ.get("DEBUG", "FALSE") == "TRUE"


def utf8_reload():
    import sys

    if sys.getdefaultencoding() != "utf-8":
        reload(sys)
        # noinspection PyUnresolvedReferences
        sys.setdefaultencoding("utf-8")


def is_debug():
    return __DEBUG


def ide_debug():
    return __IDE_DEBUG


def ide_print_pack(msg, pack):
    if type(pack) is str:
        try:
            pack = json.loads(pack)
        except:
            ide_print(msg + " [%s]" % pack)
            return
    cmd = pack.get("cmd", "#UNKNOWN#")
    if cmd == "rpc":
        cmd = "rpc#%s" % pack.get("rpc", "#UNKNOWN#")
    if "action" in pack.get("params", {}):
        action = pack["params"]["action"]
    elif "action" in pack.get("result", {}):
        action = pack["result"]["action"]
    else:
        action = None
    if cmd in ("heart_beat",) or action in ("ping", "heart_beat", "mj_timestamp"):
        return
    if action is None:
        ide_print("%s [%s]\n%s" % (msg, cmd, json.dumps(pack, ensure_ascii=False, indent=4, sort_keys=True)))
    else:
        ide_print("%s [%s][%s]\n%s" % (msg, cmd, action, json.dumps(pack, ensure_ascii=False, indent=4)))


def ide_print(msg, fold_start="- =>", fold_prefix="+ =>", prefix="...."):
    """
    增加一个针对pycharm的调试输出
    支持console的折叠
    Editor => General => Console
        => Fold console lines that contain 增加 `+ => `(不包含`)
        => Exceptions 增加启动的py `test.py` `run.py` 以此来屏蔽pydevd.py的启动堆栈部分
    """
    if not __IDE_DEBUG:
        return
    msg = str(msg)
    tmp = msg.split('\n')
    time_str = time.strftime("%H:%M:%S")
    if len(tmp) > 1:
        msg = "\n".join([time_str + " " + fold_start + " " +
                         tmp[0]] + map(lambda x: time_str + " " + fold_prefix + " " + x, tmp[1:]))
    else:
        msg = time_str + " " + prefix + " " + msg
    print >> getattr(sys, "orig_stderr", sys.stderr), msg


class FailError(Exception):
    def __init__(self, error_id, msg, args=None):
        if args is not None:
            msg = msg % args
        Exception.__init__(self, msg)
        self.error_id = error_id


# noinspection PyPep8Naming
def Fail(msg, *args, **kwargs):
    msg = str(msg).__mod__(args)
    msg = str(msg).format(*args, **kwargs)
    raise FailError(-1, msg)


# noinspection PyPep8Naming
def Assert(expr, msg="出现错误了", *args, **kwargs):
    if expr is None or expr is False:
        if len(args) > 0:
            msg = str(msg).__mod__(args)
            msg = str(msg).format(*args, **kwargs)
        raise FailError(-1, msg)


# noinspection PyPep8Naming
def Log(msg):
    logger.info(msg)
    if __DEBUG:
        print("[%s] %s" % (time.strftime("%H:%M:%S"), msg))


def everyone():
    pass


def some():
    pass


def until():
    pass


def each():
    pass
