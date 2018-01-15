# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.4.22
import stackless

from freetime.core.exception import FTException
from freetime.util import log as ftlog
from freetime.util import performance
from freetime.util.defertool import setDefaultCallbackSimple

_NOWAITCMDS_ = frozenset(['SET', 'SETEX', 'HSET', 'HMSET', 'LPUSH', 'SREM', 'EXPIRE',
                          'set', 'setex', 'hset', 'hmset', 'lpush', 'srem', 'expire'])
_REDIS_PERFORMANCE = 1


def _runCmdRedisSlow_(fun, argl, argd):
    return "REDIS argl=" + str(argl[1:])[0:64] + ' fun=' + str(fun) + ' conn=' + str(argl[0])


def _runCmdTxRedis(redis_conn, *argl, **argd):
    cmd = argl[0]
    if str(cmd).lower().strip() == 'eval':
        ftlog.warn('SCRIPT EVAL', argl[1])

    d = redis_conn.send(*argl)
    if cmd in _NOWAITCMDS_:
        setDefaultCallbackSimple(d, argl)
        return 1
    r = stackless.getcurrent()._fttask.waitDefer(d)
    return r


def _sendCmdTxRedis(redis_conn, *argl, **argd):
    cmd = argl[0]
    if str(cmd).lower().strip() == 'eval':
        ftlog.warn('SCRIPT EVAL', argl[1])

    d = redis_conn.send(*argl)
    setDefaultCallbackSimple(d, argl)
    return 1


def _runCmdTxRedis_(redis_conn, *argl, **argd):
    funArgl = [redis_conn]
    funArgl.extend(argl)
    return performance.watchSlowCall(_runCmdTxRedis, funArgl, argd, performance.SLOW_CALL_TIME, _runCmdRedisSlow_)


sendCmd = _sendCmdTxRedis
if _REDIS_PERFORMANCE:
    runCmd = _runCmdTxRedis_
else:
    runCmd = _runCmdTxRedis


def closeAllRedis(redis_pool_map):
    ftlog.info('closeAllRedis !!', redis_pool_map)
    for dbkey in redis_pool_map.keys():
        conn = redis_pool_map[dbkey]
        try:
            conn.close()
        except:
            ftlog.error('ERROR CLOSE MYSQL of', dbkey)


def doRedis(poolname, *argl, **argd):
    import freetime.entity.config as ftcon
    conn = ftcon.redis_pool_map.get(poolname, None)
    if conn == None:
        raise FTException("doRedis:poolname [" + str(poolname) + "] undefined.")
    return runCmd(conn, *argl, **argd)
