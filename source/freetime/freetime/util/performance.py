# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.4.3
from time import time

from freetime.core.timer import FTLoopTimer
from freetime.util import log as ftlog

try:
    import psutil

    _myps = psutil.Process()
except:
    _myps = None
    ftlog.info('psutil not installed')

PERFORMANCE_NET = 0
SLOW_CALL_TIME = 0.2


def watchSlowCall(fun, funArgl, funArgd, slowTime, slowFun):
    t = time()
    r = fun(*funArgl, **funArgd)
    if slowTime == None:
        slowTime = SLOW_CALL_TIME
    t = time() - t
    if t > SLOW_CALL_TIME:
        ftlog.warn('SLOW CALL, TIME=', slowTime, 'USETIME=%0.4f' % (t), slowFun(fun, funArgl, funArgd))
    return r


MSG_KEY = 'RPC.'
NET_KEY = 'xxxnettimexxx'
NET_KEY_LEN = len(NET_KEY)


def linkMsgTime(tag2, msg):
    if not PERFORMANCE_NET:
        return msg
    try:
        i = msg.find(MSG_KEY)
        if i <= 0:
            i = msg.find(NET_KEY)
            if i < 0:
                return msg

        import freetime.entity.config as ftcon
        tag1 = ftcon.global_config["server_id"]
        i = msg.find(NET_KEY)
        if i < 0:
            x = msg.rfind('}')
            if x <= 0:
                return msg
            msg = msg[0:x] + ',"' + NET_KEY + '":["%s","%s",%0.4f]' % (tag1, tag2, time()) + msg[x:]
            i = msg.find(NET_KEY)
        else:
            x = msg.find(']', i)
            if i + 16 == x:
                msg = msg[0:x] + '"%s","%s",%0.4f' % (tag1, tag2, time()) + msg[x:]
            else:
                msg = msg[0:x] + ',"%s","%s",%0.4f' % (tag1, tag2, time()) + msg[x:]
        return msg
    except:
        ftlog.exception()
        return msg


# msg = "{}"
# msg = '{"argd":{},"rpc":"hall.servers.util.rpc.user_remote.queryUserWeardItemKindIds","cmd":"rpc","argl":[6,121571302]}'
# msg = linkMsgTime('A', msg)
# print msg
# msg = linkMsgTime('B', msg)
# print msg
# msg = linkMsgTime('C', msg)
# print msg
# msg = linkMsgTime('D', msg)
# print msg
# msg = linkMsgTime('E', msg)
# print msg
# msg = linkMsgTime('F', msg)
# print msg
# import json
# print json.loads(msg)


def threadInfo():
    if _myps:
        mem = _myps.memory_info_ex()
        infos = []
        infos.append('pid')
        infos.append(str(_myps.pid))
        infos.append('ppid')
        infos.append(str(_myps.ppid()))
        infos.append('cpu')
        infos.append(str(_myps.cpu_percent()))
        infos.append('threads')
        infos.append(str(_myps.num_threads()))
        infos.append('rss')
        infos.append('%dM' % (int(mem.rss / 1024 / 1024)))
        infos.append('vms')
        infos.append('%dM' % (int(mem.vms / 1024 / 1024)))
        infos.append('shr')
        # PATCH: osx下没有shared
        infos.append('%dM' % (int(getattr(mem, 'shared', 0) / 1024 / 1024)))
        ftlog.hinfo('THREADINFO', ','.join(infos))
    else:
        ftlog.hinfo('THREADINFO psutil not install')


_ppsTimer = None
_ppsFunCounts = []


def regPPSCounter(funCount):
    global _ppsTimer
    if callable(funCount):
        if _ppsTimer == None:
            _ppsTimer = FTLoopTimer(3, -1, _ppsCounter)
            _ppsTimer.start()
        if funCount not in _ppsFunCounts:
            _ppsFunCounts.append(funCount)


def _ppsCounter():
    if _ppsFunCounts:
        for fun in _ppsFunCounts:
            try:
                fun()
            except:
                ftlog.error()
