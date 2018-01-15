# -*- coding: utf-8 -*-
"""
Created on 2015-5-12
@author: zqh
"""

import inspect

import freetime.util.log as ftlog
from poker.entity.configure import gdata
from poker.protocol import runhttp, decorator, _runenv


def _initializeCommands(gdatas):
    """
    初始化HTTP和TCP, RPC的命令入口, 获取各个游戏的实例的handler进行注册处理
    分游戏自动搜索所需要的handler
    分服务类型自动注册相应的服务handler
    对远程调用接口自动进行local和remote的预处理
    """
    ftlog.debug('initializeCommands begin')
    stype = gdata.serverType()
    for gameId, tygame in gdata.games().items():
        hpkg = gdata.SRV_TYPE_PKG_NAME[stype]
        mpkg = tygame._packageName
        pkg = mpkg + '.servers.' + hpkg
        ftlog.debug('initializeCommands package->', gameId, pkg)
        # 动态查找注册HTTP的命令入口
        hclazzs = decorator._loadDecoratorClass(pkg, 'markHttpHandler')
        for fullName, hclazz in hclazzs.items():
            handler = hclazz()
            if __isHandlerEnable(handler):
                hmts = decorator._findDecoratorMethod(handler, 'markHttpMethod')
                for mt in hmts:
                    __registerHttpMethod(gameId, fullName, handler, mt[0], mt[1])
        # 动态查找注册CMD#ACTION的命令入口
        hclazzs = decorator._loadDecoratorClass(pkg, 'markCmdActionHandler')
        for fullName, hclazz in hclazzs.items():
            handler = hclazz()
            if __isHandlerEnable(handler):
                hmts = decorator._findDecoratorMethod(handler, 'markCmdActionMethod')
                for mt in hmts:
                    __registerCmdActionMethod(gameId, fullName, handler, mt[0], mt[1])

        if stype != gdata.SRV_TYPE_AGENT:
            # 动态查找注册RPC的命令入口
            hclazzs = decorator._loadDecoratorClass(pkg, 'markRpcHandler')
            for fullName, hclazz in hclazzs.items():
                handler = hclazz()
                if __isHandlerEnable(handler):
                    hmts = decorator._findDecoratorMethod(handler, 'markRpcMethod')
                    for mt in hmts:
                        __registerLocalRpcMethod(gameId, fullName, handler, mt[0], mt[1])

            # 查找所有的游戏的RPC Client的, 进行预处理
            for rpcSrvType, rpcSevPkg in gdata.SRV_TYPE_PKG_NAME.items():
                pkg = mpkg + '.servers.' + rpcSevPkg
                hclazzs = decorator._loadDecoratorClass(pkg, 'markRpcHandler')
                for fullName, hclazz in hclazzs.items():
                    handler = hclazz()
                    if __isHandlerEnable(handler):
                        hmts = decorator._findDecoratorMethod(handler, 'markRpcMethod')
                        for mt in hmts:
                            __registerRemoteRpcMethod(gameId, rpcSrvType, fullName, handler, mt[0], mt[1])

    cps = _runenv._cmd_path_methods.keys()
    cps.sort()
    for cp in cps:
        ftlog.debug('TCP CMD->', cp, _runenv._cmd_path_methods[cp])
    ftlog.debug('initializeCommands end')


def __isHandlerEnable(handler):
    ret = True
    isEnable = getattr(handler, 'isEnable', None)
    if callable(isEnable):
        ret = isEnable()
    return 1 if ret else 0


def __registerHttpMethod(gameId, fullName, handler, method, markParams):
    # 确定HTTP的API路径
    httppath = markParams.get('httppath', None)
    assert (isinstance(httppath, (str, unicode)))
    httppath = httppath.strip()
    assert (len(httppath) > 0)
    assert (httppath[0] == '/')
    assert (httppath[-1] != '/')

    jsonp = markParams.get('jsonp', 0)
    assert (jsonp in (0, 1))

    ip_filter = markParams.get('ip_filter', 0)
    assert (ip_filter in (0, 1))

    responseType = markParams.get('responseType', 'json')
    assert (responseType in ('json', 'html', 'gif', "plain"))

    scope = markParams.get('scope', 'global')
    assert (scope in ('global', 'game'))
    if scope == 'game':
        httppath = httppath + '/' + str(gameId)

    # 确定是否需要IP过滤
    if ip_filter:
        ip_filter = getattr(handler, 'ip_filter', None)
        assert (callable(ip_filter))
        markParams['fun_ip_filter'] = ip_filter
    else:
        markParams['fun_ip_filter'] = None

    # 确定返回的ContentType
    if responseType == 'json' or jsonp:
        markParams['content_type'] = runhttp.CONTENT_TYPE_JSON
    elif responseType == 'gif':
        markParams['content_type'] = runhttp.CONTENT_TYPE_GIF
    elif responseType == 'plain':
        markParams['content_type'] = runhttp.CONTENT_TYPE_PLAIN
    else:
        markParams['content_type'] = runhttp.CONTENT_TYPE_HTML

    if httppath in runhttp._http_path_methods:
        raise Exception('the http path already defined !! httppath=' + str(httppath))

    paramkeys, _, __, ___ = inspect.getargspec(method)
    assert (len(paramkeys) > 0)
    assert (paramkeys[0] in ('self', 'cls'))
    markParams['paramkeys'] = paramkeys[1:]

    markParams['handler'] = handler
    markParams['fun_method'] = method
    runhttp._http_path_methods[httppath] = markParams
    ftlog.info('HTTP Add Handler -> gameId=', gameId, 'path=', httppath, 'method=', method,
               markParams['content_type'])
    return httppath


def __registerCmdActionMethod(gameId, fullName, handler, method, markParamsOrg):
    markParams = {}
    markParams.update(markParamsOrg)

    cmd = markParams.get('cmd', None)
    assert (isinstance(cmd, (str, unicode)) and len(cmd.strip()) > 0)
    assert (cmd.find('#') < 0)

    action = markParams.get('action', '')
    assert (isinstance(action, (str, unicode)))
    action = action.strip()
    assert (action.find('#') < 0)

    lockParamName = markParams.get('lockParamName', '')
    assert (isinstance(lockParamName, (str, unicode)))

    clientIdVer = markParams.get('clientIdVer', 0.0)
    assert (isinstance(clientIdVer, (int, float)))

    paramkeys, _, __, ___ = inspect.getargspec(method)
    assert (len(paramkeys) > 0)
    assert (paramkeys[0] in ('self', 'cls'))

    markParams['isRpc'] = 0
    markParams['handler'] = handler
    markParams['paramkeys'] = paramkeys[1:]
    markParams['fun_method'] = method

    scope = markParams.get('scope', 'global')
    assert (scope in ('global', 'game'))

    cmdpath = cmd + '#' + action
    if scope == 'game':
        cmdpath = cmdpath + '#' + str(gameId)

    vcalls = _runenv._cmd_path_methods.get(cmdpath, None)
    if not vcalls:
        vcalls = []
        _runenv._cmd_path_methods[cmdpath] = vcalls
    vcalls.append((clientIdVer, markParams))
    vcalls.sort(key=lambda x: x[0], reverse=True)
    vers = set()
    for x in vcalls:
        vers.add(x[0])
    if len(vers) != len(vcalls):
        ftlog.info('ERROR !!! TCP CMD Entry, find same version with double callable !!')
        for x in vcalls:
            ftlog.info('ERROR !!!', x)
        raise Exception('TCP CMD Entry, find same version with double callable !!')
    ftlog.debug('TCP CMD Entry ->cmdpath=', cmdpath, 'clientIdVer=', clientIdVer, 'method=', method)


def __registerLocalRpcMethod(gameId, fullName, handler, method, markParamsOrg):
    markParams = {}
    markParams.update(markParamsOrg)
    assert (callable(markParams['fun_method_original']))

    syncCall = markParams.get('syncCall', 0)
    assert (syncCall in (0, 1))

    lockParamName = markParams.get('lockParamName', '')
    assert (isinstance(lockParamName, (str, unicode)))

    omethod = markParams['fun_method_original']
    paramkeys, _, __, ___ = inspect.getargspec(omethod)
    assert (len(paramkeys) > 0)
    assert (paramkeys[0] in ('self', 'cls'))
    markParams['paramkeys'] = paramkeys[1:]

    if lockParamName:
        lockIndex = markParams['paramkeys'].index(lockParamName)
    else:
        lockIndex = -1

    markParams['isRpc'] = 1
    markParams['syncCall'] = syncCall
    markParams['lockIndex'] = lockIndex
    markParams['handler'] = handler  # 原始的方法为未绑定的方法, 调用时, 第一个参数self为handler的实例
    markParams['fun_method'] = omethod

    cmdpath = '_remote_rpc_#' + fullName + '.' + method.__name__

    vcalls = _runenv._cmd_path_methods.get(cmdpath, None)
    if not vcalls:
        vcalls = []
        _runenv._cmd_path_methods[cmdpath] = vcalls
    vcalls.append((0, markParams))
    vcalls.sort(key=lambda x: x[0], reverse=True)
    vers = set()
    for x in vcalls:
        vers.add(x[0])
    if len(vers) != len(vcalls):
        ftlog.info('ERROR !!! RPC CMD Entry, find same version with double callable !!')
        for x in vcalls:
            ftlog.info('ERROR !!!', str(x))
        raise Exception('RPC CMD Entry, find same version with double callable !!')
    ftlog.info('TCP RPC Entry ->cmdpath=', cmdpath, 'method=', method)


def __registerRemoteRpcMethod(gameId, serverType, fullName, handler, method, markParams):
    syncCall = markParams.get('syncCall', 0)
    assert (syncCall in (0, 1))

    groupBy = markParams.get('groupBy', '')
    assert (isinstance(groupBy, (str, unicode)))

    omethod = markParams['fun_method_original']
    paramkeys, _, __, ___ = inspect.getargspec(omethod)
    remoteGroupByIndex = paramkeys.index(groupBy)

    markParams['remoteServerType'] = serverType
    markParams['remoteSyncCall'] = syncCall
    markParams['remoteGroupByIndex'] = remoteGroupByIndex
    markParams['remoteGroupBy'] = groupBy
    markParams['remoteCmd'] = '_remote_rpc_'
    markParams['remoteAction'] = fullName + '.' + method.__name__
    markParams['remoteGameId'] = gameId

    ftlog.info('TCP RPC Remote ->remote=', fullName, 'method=', method)
