# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import functools
import inspect
import sys
from time import time

import stackless
from stackless import bomb
from twisted.internet import defer

import freetime.entity.service as ftsvr
import freetime.util.log as ftlog
from freetime.core.exception import FTMsgPackException
from freetime.core.timer import FTLoopTimer
from freetime.support.tcpagent import wrapper
from freetime.util import performance
from poker.entity.configure import gdata
from poker.protocol import _runenv, decorator, router
from poker.util import strutil

_DEBUG = 0
if _DEBUG:
    debug = ftlog.info
else:
    def debug(*argl, **argd):
        pass


class RpcException(Exception):
    def __init__(self, msg):
        super(RpcException, self).__init__(msg)


_MARKED_METHOD = []
_RPC_ID_COUNT_ = 0
_SYS_RPC_PACKAGES = ['poker.servers.rpc']
RPC_FIRST_SERVERID = '_SERVERID_'


def markRpcCall(groupName, lockName, syncCall=1, future=0):
    '''
    标记一个方法为RPC远程命令的入口
    注意: 使用此标记的方法必须为模块级别的方法(py文件中的顶级方法)
         RPC方法必须返回非None的结果
    '''
    assert (isinstance(groupName, (str, unicode)))
    assert (isinstance(lockName, (str, unicode)))
    assert (isinstance(syncCall, int))
    assert (isinstance(future, int))
    markParams = {
        'type': sys._getframe().f_code.co_name,
        'syncCall': syncCall,
        'groupName': groupName,
        'lockName': lockName,
        'future': future,
    }

    def decorating_function(method):
        markParams['original'] = method

        @functools.wraps(method)
        def rpcfunwarp(*argl, **argd):
            return _invokeRpcMethod(markParams, argl, argd)

        setattr(rpcfunwarp, decorator._METHOD_MARKE, markParams)
        _MARKED_METHOD.append(rpcfunwarp)
        return rpcfunwarp

    return decorating_function


def _initializeRpcMehodss(gdata_):
    '''
    初始化RPC的命令入口, 获取各个游戏的实例的handler进行注册处理
    分游戏自动搜索自定义的RPC方法
    '''
    ftlog.debug('_initializeRpcMehodss begin')
    mpkgs = ['poker']
    for _, tygame in gdata.games().items():
        mpkgs.append(tygame._packageName)

    for mpkg in mpkgs:
        ftlog.debug('_initializeRpcMehodss package->', mpkg)
        # 注册RCP Server调用入口
        for rpcSevPkg in gdata.SRV_TYPE_PKG_NAME.values():
            pkg = mpkg + '.servers.' + rpcSevPkg + '.rpc'
            methods = decorator._loadDecoratorModuleMethods(pkg, 'markRpcCall')
            for method in methods:
                assert (method in _MARKED_METHOD)
                del _MARKED_METHOD[_MARKED_METHOD.index(method)]
                _registerRpcCall(method)
    for pkg in _SYS_RPC_PACKAGES:
        methods = decorator._loadDecoratorModuleMethods(pkg, 'markRpcCall')
        for method in methods:
            assert (method in _MARKED_METHOD)
            del _MARKED_METHOD[_MARKED_METHOD.index(method)]
            _registerRpcCall(method)

    if _MARKED_METHOD:
        for m in _MARKED_METHOD:
            ftlog.warn('this method marked as RCP, but not in rpc packages !!', getattr(m, decorator._METHOD_MARKE))
    cps = _runenv._rpc_methods.keys()
    cps.sort()
    for cp in cps:
        ftlog.debug('RPC CMD->', cp, _runenv._rpc_methods[cp])
    ftlog.debug('_initializeRpcMehodss end')


def _registerRpcCall(method, rpc=None):
    markParams = getattr(method, decorator._METHOD_MARKE, None)
    ftlog.debug('_registerRpcCall->', markParams)
    assert (isinstance(markParams, dict))

    omethod = markParams['original']
    assert (callable(omethod))

    paramkeys, _, __, ___ = inspect.getargspec(omethod)
    markParams['paramkeys'] = paramkeys[:]

    syncCall = markParams.get('syncCall', 0)
    assert (syncCall in (0, 1))

    groupName = markParams.get('groupName', None)
    if groupName == RPC_FIRST_SERVERID:
        groupIndex = 0
    else:
        if groupName:
            assert (groupName in paramkeys)
            groupIndex = paramkeys.index(groupName)
        else:
            groupIndex = -1

    lockName = markParams.get('lockName', None)
    if lockName:
        assert (lockName in paramkeys)
        lockIndex = paramkeys.index(lockName)
    else:
        lockIndex = -1

    pyPkg = omethod.__module__
    rpcSrvType = None
    if groupName == RPC_FIRST_SERVERID:
        rpcSrvType = RPC_FIRST_SERVERID
    else:
        srvPkg = pyPkg.split('.')[-3]
        for k, v, in gdata.SRV_TYPE_PKG_NAME.items():
            if v == srvPkg:
                rpcSrvType = k
                break
        assert (rpcSrvType in gdata.SRV_TYPE_PKG_NAME)

    if not rpc:
        rpc = pyPkg + '.' + method.__name__

    markParams['rpc'] = rpc
    markParams['lockIndex'] = lockIndex
    # 3个主要再调用端使用的参数
    markParams['rpcSrvType'] = rpcSrvType
    markParams['syncCall'] = syncCall
    markParams['groupIndex'] = groupIndex

    if rpcSrvType == gdata.serverType() or rpcSrvType == RPC_FIRST_SERVERID:
        _runenv._rpc_methods[rpc] = markParams


def _getRpcId():
    targs = ftsvr.getTaskRunArg()
    rpcid = targs.get('rpcid', None)
    if not rpcid:
        rpcid = targs.get('userheader1', None)
        if rpcid and rpcid.find('RPC.') == 0:
            targs['rpcid'] = rpcid
        else:
            global _RPC_ID_COUNT_
            _RPC_ID_COUNT_ += 1
            rpcid = 'RPC.' + gdata.serverId() + '.' + str(_RPC_ID_COUNT_)
            targs['rpcid'] = rpcid
    return rpcid


def _invokeMethodLocked(markParams, argl, argd):
    # 锁定当前mark定义的资源
    ret = None
    ftlock = None
    lockIndex = markParams['lockIndex']
    if lockIndex >= 0:
        lockName = markParams['lockName']
        lockval = argl[lockIndex]
        rpcid = _getRpcId()
        ftlock = _runenv._lockResource(lockName, lockval, rpcid)
    try:
        originalMethod = markParams['original']
        ret = originalMethod(*argl, **argd)
    finally:
        # 释放当前mark定义的资源
        if ftlock:
            _runenv._unLockResource(ftlock)
    return ret


def _handlerRpcCommand(msg):
    '''
    处理接收到的一个远程RPC调用
    '''
    t1 = time()
    if performance.PERFORMANCE_NET:
        netkey = msg.getKey(performance.NET_KEY)
        if netkey:
            netkey.append(gdata.serverId())
            netkey.append('DO')
            netkey.append(float('%0.4f' % t1))
    try:
        rpc = msg.getKey('rpc')
        argl = msg.getKey('argl')
        argd = msg.getKey('argd')
        markParams = _runenv._rpc_methods.get(rpc, None)
        ret = _invokeMethodLocked(markParams, argl, argd)
        if markParams['syncCall']:
            if performance.PERFORMANCE_NET:
                netkey = msg.getKey(performance.NET_KEY)
                if not netkey:
                    netkey = []
                mo = strutil.dumps({'ret': ret,
                                    performance.NET_KEY: netkey})
            else:
                mo = strutil.dumps({'ret': ret})
            router.responseQurery(mo)
    except Exception, e:
        ftlog.error('_handlerRpcCommand msg=', msg)
        try:
            if router.isQuery():
                targs = ftsvr.getTaskRunArg()
                if not targs.get('responsed'):
                    if performance.PERFORMANCE_NET:
                        netkey = msg.getKey(performance.NET_KEY)
                        if not netkey:
                            netkey = []
                        mo = strutil.dumps({'ex': '_handlerRpcCommand Exception : ' + str(e),
                                            performance.NET_KEY: netkey})
                    else:
                        mo = strutil.dumps({'ex': '_handlerRpcCommand Exception : ' + str(e)})
                    router.responseQurery(mo)
        except:
            ftlog.error()
    time_recv = ftsvr.getTaskRunArg().get('time_recv', 0)
    if time_recv and time_recv > 0:
        t = t1 - time_recv
        if t > 0.2:
            ftlog.warn('RPC RESPONSE SLOW !! TIME=%0.4f' % (t), 'RECVTIME=%0.4f' % time_recv, msg)


def _getRpcDstServerId(rsrv, groupId):
    if groupId <= 0:
        if rsrv.srvType == gdata.serverType():
            return gdata.serverId()
        groupId = rsrv.sididx
        rsrv.sididx += 1
    dst = rsrv.sids[groupId % rsrv.sidlen]
    return dst


def getRpcDstRoomServerId(roomId, canChangeRoomId):
    allrooms = gdata.roomIdDefineMap()
    if roomId in allrooms:
        roomDef = allrooms[roomId]
        return roomDef.serverId
    elif canChangeRoomId:  # this roomId may be big roomId
        bigrooms = gdata.bigRoomidsMap()
        if roomId in bigrooms:
            ctrlroomIds = bigrooms[roomId]
            ctrlRoomId = ctrlroomIds[0]  # ctrlRoom0 做为 ctrlRooms 的调度器
            roomDef = allrooms[ctrlRoomId]
            return roomDef.serverId
    ftlog.warn('getRpcDstRoomServerId roomId error !!', roomId, canChangeRoomId)


def _invokeRpcMethod(markParams, argl, argd):
    '''
    进程内其它方法调用RPC方法的代理方法
    '''
    rpc = markParams['rpc']
    rpcSrvType = markParams['rpcSrvType']
    groupIndex = markParams['groupIndex']
    future = markParams['future']
    groupVal = 0
    dstSid = None
    if rpcSrvType == RPC_FIRST_SERVERID:
        dstSid = argl[0]
    else:
        if groupIndex >= 0:
            groupVal = argl[groupIndex]
        if rpcSrvType == gdata.SRV_TYPE_UTIL:
            dstSid = _getRpcDstServerId(router._utilServer, groupVal)
        elif rpcSrvType == gdata.SRV_TYPE_ROOM:
            dstSid = getRpcDstRoomServerId(groupVal, 1)
        elif rpcSrvType == gdata.SRV_TYPE_TABLE:
            dstSid = getRpcDstRoomServerId(groupVal, 0)
        elif rpcSrvType == gdata.SRV_TYPE_CONN:
            dstSid = _getRpcDstServerId(router._connServer, groupVal)
        elif rpcSrvType == gdata.SRV_TYPE_HTTP:
            dstSid = _getRpcDstServerId(router._httpServer, groupVal)
        elif rpcSrvType == gdata.SRV_TYPE_ROBOT:
            dstSid = _getRpcDstServerId(router._robotServer, groupVal)
        elif rpcSrvType == gdata.SRV_TYPE_AGENT:
            dstSid = _getRpcDstServerId(router._agentServer, groupVal)
        elif rpcSrvType == gdata.SRV_TYPE_SDK_HTTP:
            dstSid = _getRpcDstServerId(router._sdkHttpServer, groupVal)
        elif rpcSrvType == gdata.SRV_TYPE_SDK_GATEWAY:
            dstSid = _getRpcDstServerId(router._gatewayHttpServer, groupVal)
        elif rpcSrvType == gdata.SRV_TYPE_CENTER:
            for dst, logics in gdata.centerServerLogics().items():
                if groupVal in logics:
                    dstSid = dst
                    break
            if not dstSid:
                dstSid = router._centerServer.sids[0]

    if not dstSid:
        raise RpcException('RpcException ' + rpc + '! can not location the target server, rpcSrvType=' + str(
            rpcSrvType) + ' groupVal=' + str(groupVal))

    rpcid = _getRpcId()
    if dstSid == gdata.serverId():
        if markParams['syncCall']:
            if future:
                # TODO: Future RPC CALL 1
                return _FutureResultLocal(markParams, argl, argd)
            else:
                ret = _invokeMethodLocked(markParams, argl, argd)
                return strutil.cloneData(ret)
        else:
            ftt = FTLoopTimer(0.01, 0, _invokeMethodLocked, markParams, argl, argd)
            ftt.start()
            return None

    mi = strutil.dumps({'cmd': _runenv._CMD_RPC_,
                        'rpc': rpc,
                        'argl': argl,
                        'argd': argd
                        })

    if markParams['syncCall']:
        if future:
            # TODO: Future RPC CALL 1
            return _FutureResultRemote(rpc, dstSid, mi, rpcid, str(groupVal), _runenv._RPC_TIME_OUT)
        else:
            try:
                jstr = wrapper.query(dstSid, mi, rpcid, str(groupVal), _runenv._RPC_TIME_OUT)
            except FTMsgPackException, e:
                raise e
            except Exception, e:
                ftlog.warn('RpcException msg=', mi)
                raise RpcException('RpcException ' + rpc + ' ! query remote false, ' + str(e))
            return _parseRpcResult(mi, jstr, rpc)
    else:
        try:
            wrapper.send(dstSid, mi, rpcid, str(groupVal))
        except Exception, e:
            ftlog.warn('RpcException msg=', mi)
            raise RpcException('RpcException ' + rpc + ' ! send to remote false, ' + str(e))
        return None


def _parseRpcResult(mi, jstr, rpc):
    if jstr:
        try:
            modict = strutil.loads(jstr)
        except:
            ftlog.warn('RpcException msg=', mi)
            raise RpcException('RpcException ' + rpc + ' ! remote return format false, json=[' + repr(jstr) + ']')
    else:
        raise RpcException('RpcException ' + rpc + ' ! remote return is Empty !')

    if modict.get('ex', None):
        ftlog.warn('RpcException msg=', mi)
        raise RpcException('RpcException ' + rpc + ' ! remote Exception=' + modict.get('ex'))

    if modict.has_key('ret'):
        ret = modict['ret']
    else:
        ftlog.warn('RpcException msg=', mi)
        raise RpcException('RpcException ' + rpc + ' ! remote has no return !')
    return ret


class FutureResult(object):
    STATUS_NONE = 0
    STATUS_RUN = 1
    STATUS_OK = 2
    STATUS_ERROR = 3

    def __init__(self):
        self._status = FutureResult.STATUS_NONE
        self._result = None
        self._exception = None
        self._waitDeffer = None

    def _doFutureDone(self):
        if _DEBUG:
            debug('FutureResult._doFutureDone->', self._waitDeffer)
        if self._waitDeffer != None:
            self._waitDeffer.callback(1)

    def getResult(self):
        '''
        如果返回None，说明有异常发生，可以查看异常日志判定原因
        '''
        if _DEBUG:
            debug('FutureResult.getResult->', self._status)
        if self._status == FutureResult.STATUS_OK or self._status == FutureResult.STATUS_ERROR:
            # 如果已经完成远程调用，那么直接返回结果
            if _DEBUG:
                debug('FutureResult.getResult OUT->', self._status)
            return self._result
        else:
            # 还未完成远程调用，生成deffer，等待远程结果
            if _DEBUG:
                debug('FutureResult.getResult WAIT->', self._status)
            self._waitDeffer = defer.Deferred()
            stackless.getcurrent()._fttask.waitDefer(self._waitDeffer)
            if _DEBUG:
                debug('FutureResult.getResult OUT->', self._status)
            return self._result


class _FutureResultLocal(FutureResult):
    def __init__(self, markParams, argl, argd):
        super(_FutureResultLocal, self).__init__()
        try:
            ftt = FTLoopTimer(0.01, 0, self._invokeLocal, markParams, argl, argd)
            ftt.start()
        except Exception, e:
            self._status = FutureResult.STATUS_ERROR
            self._exception = e
            ftlog.error()
        self._doFutureDone()

    def _invokeLocal(self, markParams, argl, argd):
        try:
            if _DEBUG:
                debug('_FutureResultLocal._invokeLocal IN->', argl)
            self._status = FutureResult.STATUS_RUN
            ret = _invokeMethodLocked(markParams, argl, argd)
            self._result = strutil.cloneData(ret)
            assert (ret == None), 'the future result can not be None'
            self._status = FutureResult.STATUS_OK
            if _DEBUG:
                debug('_FutureResultLocal._invokeLocal OUT->', argl)
        except Exception, e:
            self._status = FutureResult.STATUS_ERROR
            self._exception = e
            ftlog.error()
        self._doFutureDone()


class _FutureResultRemote(FutureResult):
    def __init__(self, rpc, dstSid, mi, rpcid, groupVal, timeout):
        super(_FutureResultRemote, self).__init__()
        self._mi = mi
        self._rpc = rpc
        self._groupVal = groupVal
        self._dstSid = dstSid
        self._doRemoteWrite(rpc, dstSid, mi, rpcid, groupVal, timeout)

    def _doRemoteWrite(self, rpc, dstSid, mi, rpcid, groupVal, timeout):
        self._remoteDeffer = None
        try:
            rd = wrapper.query(dstSid, mi, rpcid, str(groupVal), _runenv._RPC_TIME_OUT, returnDeffer=1)
            rd.addCallback(self._doRemoteSuccessful)
            rd.addErrback(self._doRemoteError)
            self._remoteDeffer = rd
            if _DEBUG:
                debug('._FutureResultRemote._doRemoteWrite->', groupVal, self._rpc)
        except FTMsgPackException, e:
            self._status = FutureResult.STATUS_ERROR
            self._exception = e
            ftlog.error()
            self._remoteDeffer = None
            self._doFutureDone()
        except Exception, e:
            self._status = FutureResult.STATUS_ERROR
            self._exception = e
            ftlog.error()
            self._remoteDeffer = None
            self._doFutureDone()

    def _doRemoteSuccessful(self, remoteRet):
        try:
            if _DEBUG:
                debug('_FutureResultRemote._doRemoteSuccessful->', self._groupVal, self._rpc, remoteRet)
            jstr, _writeTime, _recvTime = remoteRet[0], remoteRet[1], remoteRet[2]
            self._result = _parseRpcResult(self._mi, jstr, self._rpc)
            assert (self._result != None), 'the future result can not be None'
            self._status = FutureResult.STATUS_OK

            ct = time()
            if ct - _writeTime > wrapper._QUERY_SLOW_TIME:
                ftlog.warn('QUERY REPLAY SLOW FUTURE! reply=%0.6f' % (_recvTime - _writeTime),
                           'schedule=%0.6f' % (ct - _recvTime), 'total=%0.6f' % (ct - _writeTime),
                           'dst=', self._dstSid, 'request=', self._mi, 'response=', jstr)

        except Exception, e:
            self._status = FutureResult.STATUS_ERROR
            self._exception = e
            ftlog.error()
        self._remoteDeffer = None
        self._doFutureDone()

    def _doRemoteError(self, fault):
        try:
            ntype, value = fault.type, fault.value
            if isinstance(value, ntype):
                b = bomb(ntype, value)
            else:
                b = bomb(ntype, ntype(value))
            b.raise_()
        except Exception, e:
            self._status = FutureResult.STATUS_ERROR
            self._exception = e
            ftlog.error()
        self._remoteDeffer = None
        self._doFutureDone()
