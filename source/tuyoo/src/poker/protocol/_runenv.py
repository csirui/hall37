# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import freetime.util.log as ftlog
from freetime.core.lock import FTLock

# RPC 命令的名称
_CMD_RPC_ = 'rpc'
# RPC 调用的超时时间
_RPC_TIME_OUT = 6
# RPC 命令的命令配置中心
_rpc_methods = {}
# 消息命令，RPC命令的全局锁集合
_FTLOCKS = {}
# TCP命令的集合中心, key为:TCP的命令路径 cmd#action
# value为区分版本的命令的执行者[(version, callable), (version, callable)]
_cmd_path_methods = {}
# 老版本RPC的命令中心
_cmd_path_rpc_methods = {}


def _lockResource(lockName, lockval, relockKey):
    # TODO 处理重入锁定
    lockkey = 'lock:' + lockName + ':' + str(lockval)
    ftlock = _FTLOCKS.get(lockkey, None)
    if ftlock == None:
        ftlock = FTLock(lockkey, relockKey)
        _FTLOCKS[lockkey] = ftlock
    ftlog.debug('lock resource of', lockkey, 'wait !!', relockKey)
    ftlock.lock(relockKey)
    ftlog.debug('lock resource of', lockkey, 'locked !!', relockKey)
    return ftlock


def _unLockResource(ftlock):
    ftlog.debug('lock resource of', ftlock.lockkey, 'released !!')
    if ftlock.unlock() == 0:
        del _FTLOCKS[ftlock.lockkey]
        ftlog.debug('lock resource of', ftlock.lockkey, 'released delete !!')
