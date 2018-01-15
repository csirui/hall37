# -*- coding: utf-8 -*-
'''
Created on 2015年5月20日

@author: zqh
'''

import freetime.util.log as ftlog
from poker.entity.configure import gdata, synccenter
from poker.protocol import _runenv
from poker.protocol.rpccore import markRpcCall, RPC_FIRST_SERVERID


def hotFix(hotfixpy, serverIds, isWait, hotparams):
    assert (isinstance(serverIds, (list, tuple)))
    assert (isinstance(hotfixpy, (str, unicode)))
    assert (hotfixpy.startswith('file://') or hotfixpy.startswith('code://'))
    assert (isinstance(isWait, int))
    allSrvIds = gdata.allServersMap().keys()
    for srvId in serverIds:
        assert (srvId in allSrvIds)
    rets = {}
    for srvId in serverIds:
        if isWait:
            oldt = _runenv._RPC_TIME_OUT  # 对于目前配置更新超时，临时调整超时时间
            _runenv._RPC_TIME_OUT = 24.5
            rets[srvId] = _syncHotFix(srvId, hotfixpy, hotparams)
            if _runenv._RPC_TIME_OUT == 24.5:
                _runenv._RPC_TIME_OUT = oldt
        else:
            _asyncHotFix(srvId, hotfixpy, hotparams)
            rets[srvId] = 'async'
    return rets


@markRpcCall(groupName=RPC_FIRST_SERVERID, lockName="", syncCall=1)
def _syncHotFix(serverId, hotfixpy, hotparams):
    return _doHotFix(hotfixpy, hotparams)


@markRpcCall(groupName=RPC_FIRST_SERVERID, lockName="", syncCall=0)
def _asyncHotFix(serverId, hotfixpy, hotparams):
    return _doHotFix(hotfixpy, hotparams)


def _doHotFix(hotfixpy, hotparams):
    ftlog.info('hotfix  in :', hotfixpy, 'hotparams=', hotparams)
    execfile_result = {}
    execfile_globals = {
        'results': execfile_result,
        'params': hotparams
    }
    if hotfixpy.startswith('file://'):
        pyfile = gdata.pathBin() + '/' + hotfixpy[7:]
        ftlog.info('hotfix pyfile=', pyfile)
        import os
        if not os.path.isfile(pyfile):
            execfile_result['error'] = 'File Not Found !' + pyfile
        else:
            try:
                execfile(pyfile, execfile_globals, execfile_globals)
            except:
                execfile_result['error'] = ftlog.format_exc()
                ftlog.exception()
    else:  # elif hotfixpy.startswith('code://') :
        hotcode = hotfixpy[7:]
        try:
            exec hotcode in execfile_globals, execfile_globals
        except:
            execfile_result['error'] = ftlog.format_exc()
            ftlog.exception()
    ftlog.info('hotfix out :', execfile_result)
    return execfile_result


def reloadConfig(serverIds, keylist, reloadlist, sleepTime=0.01):
    assert (isinstance(serverIds, (list, tuple)))
    assert (isinstance(keylist, (list, tuple)))
    assert (isinstance(reloadlist, (list, tuple)))
    assert (isinstance(sleepTime, (int, float)))

    allSrvIds = gdata.allServersMap().keys()
    for srvId in serverIds:
        assert (srvId in allSrvIds)
    rets = {}
    for srvId in serverIds:
        rets[srvId] = _reloadConfig(srvId, keylist, reloadlist, sleepTime)
    return rets


@markRpcCall(groupName=RPC_FIRST_SERVERID, lockName="serverId", syncCall=1)
def _reloadConfig(serverId, keylist, reloadlist, sleepTime):
    synccenter._doCheckReloadConfig(None)
    return 'OK'
