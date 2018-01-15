# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import functools, inspect, stackless

from tyserver.tyutils import tylog, strutil
from tyserver.tyutils.msg import MsgPack
from tyserver.tycmds import InitFlg


TRACE_RESPONSE = 1
__ws_commands = {}


def isWsTask():
    session = stackless.getcurrent()._fttask.session
    return session.get('isws', 0)


def getWsProtocol():
    return stackless.getcurrent()._fttask.run_args['wsprotocol']


def getClientIp():
    wsp = getWsProtocol()
    return wsp.host


def getMsgPack(keys=None):
    return stackless.getcurrent()._fttask.pack


def markWsRequestEntry(wsgameid=0, wscmd=None, wsact=None, jsonp=False, ip_filter=False, extend_tag=None):
    jsonp = 1 if jsonp else 0
    ip_filter = 1 if ip_filter else 0
    assert(isinstance(wsgameid, int))
    if wscmd != None :
        assert(isinstance(wscmd, (str, unicode)))
    if wsact != None :
        assert(isinstance(wsact, (str, unicode)))
    entry = {
            'jsonp' : jsonp,
            'need_ip_filter' : ip_filter,
            'extend_tag' : extend_tag,
            'wsgameid' : wsgameid,
            'wscmd' : wscmd,
            'wsact' : wsact,
    }

    def decorating_function(method):
        paramkeys, _, __, ___ = inspect.getargspec(method)
        if len(paramkeys) > 0 :  # 去除self和cls关键字
            if paramkeys[0] in ('self', 'cls') :
                paramkeys = paramkeys[1:]
            else:
                raise Exception('a WS method must be a class or object instance')
        entry['paramkeys'] = paramkeys
        @functools.wraps(method)
        def funwarp(*args, **argd):
            return __wsEntryWrapCall(entry, method, *args, **argd)
        setattr(funwarp, '_ws_request_entry_', entry)
        return funwarp
    return decorating_function


def __wsEntryWrapCall(entry, method, *args, **argd):
    apiobj = args[0]  # 第0个为self或cls
    msg, values = __checkRequestParams(apiobj, entry['paramkeys'], entry['extend_tag'])
    if msg :
        return __stringifyResponse(entry['jsonp'], msg)
    msg = method(apiobj, *values)
    return __stringifyResponse(entry['jsonp'], msg)


def __stringifyResponse(isjsonp, content):
    if (isinstance(content, (str, unicode))) :
        pass
    elif (isinstance(content, MsgPack)) :
        content = content.pack()
    elif (isinstance(content, (list, tuple, dict, set))) :
        content = strutil.dumps(content)
    elif (isinstance(content, (int, float, bool))) :
        content = str(content)
    else:
        content = repr(content)
    content = content.encode('utf-8')
    if isjsonp :
        msg = getMsgPack()
        callback = msg.getKey('callback')
        if callback :
            callback = str(callback)
            if len(callback) > 0 :
                content = '%s(%s);' % (callback, content)
    return content


def __checkRequestParams(apiobj, paramkeys, extend_tag):
    values = []
    params = {}
    if not paramkeys :
        return None, values
    key, funname = None, None
    for key in paramkeys :
        funname = '_check_param_' + key
        func = getattr(apiobj, funname, None)
        error, value = func(key, params, extend_tag)
        if error :
            return error, None
        values.append(value)
        params[key] = value
    return None, values


def __dummyIpFilter(ip):
    return None


def addHandler(handler):
    '''
    添加一个WS请求处理的入口实例
    参数: handler WS请求的类或实例, 其定义的WS方法必须使用: @markWsRequestEntry 进行修饰
    '''
    tylog.info('WS Add Handler ->', handler)
    for key in dir(handler):
        method = getattr(handler, key)
        if callable(method) :
            entry = getattr(method, '_ws_request_entry_', None)
            if isinstance(entry, dict) :
                __registerWsEntry(handler, method, entry)


def __registerWsEntry(handler, method, entry):
    # 确定HTTP的API路径
    wsgid = entry.get('wsgameid', 0)
    wscmd = entry.get('wscmd', None)
    wsact = entry.get('wsact', None)

    if not isinstance(wscmd, (str, unicode)) or len(wscmd) <= 0 :
        cmdpath = method.__name__
        if cmdpath.find('do_cmd_') == 0 :
            cmdpath = cmdpath[6:]
        while cmdpath.find('__') >= 0 :
            cmdpath = cmdpath.replace('//', '/')
        cmdpaths = cmdpath.split('_', 1)
        wscmd = cmdpaths[0]
        if len(cmdpaths) > 1 :
            wsact = cmdpaths[1]
        else:
            wsact = ''
        entry['wscmd'] = wscmd
        entry['wsact'] = wsact

    # 确定是否需要IP过滤
    entry['ip_filter'] = __dummyIpFilter
    if entry['need_ip_filter'] :
        ip_filter = getattr(handler, 'ip_filter', None)
        if callable(ip_filter) :
            entry['ip_filter'] = ip_filter

    gamecmds = __ws_commands.get(wsgid, None)
    if gamecmds == None :
        gamecmds = {}
        __ws_commands[wsgid] = gamecmds
    
    wscmds = gamecmds.get(wscmd, None)
    if wscmds == None :
        wscmds = {}
        gamecmds[wsgid] = wscmds
    
    wspath = '%s-%s-%s' % (str(wsgid), str(wscmd), str(wsact))
    if wsact in wscmds :
        tylog.info('WARRING !! the ws command already defined !! wspath=' + wspath)
    wscmds[wsact] = (method, entry)

    tylog.info('HTTP Add Entry ->wscommand=,', wspath, 'method=' , method)
    return wspath


def handlerWsRequest(wsprotocol):
    if InitFlg.isInitOk != 1:
        mo = MsgPack()
        mo.setError(1, 'ws system not startup')
        mo = __stringifyResponse(0, mo)
        wsprotocol.sendData(mo)
        wsprotocol.wsClose()
        return

    mo = None
    try:
        tasklet = stackless.getcurrent()._fttask
        session = tasklet.session
        msg = tasklet.run_args['pack']
        session['isws'] = 1
        
        wsgid = msg.getParamInt()
        wscmd = msg.getCmd()
        wsact = msg.getParamAct()

        rpath = '%s-%s-%s' % (str(wsgid), str(wscmd), str(wsact))
        if TRACE_RESPONSE :
            tylog.info('WSREQUEST', rpath, msg)

        # 当前服务处理
        
        funws, entry = None, None
        gamecmds = __ws_commands.get(wsgid, None)
        if gamecmds != None :
            wscmds = gamecmds.get(wscmd, None)
            if wscmds != None :
                funws, entry = wscmds.get(wsact, (None, None))

        if funws == None or entry == None:
            mo = MsgPack()
            mo.setResult('gameId', wsgid)
            mo.setResultActCmd(wsact, wscmd)
            mo.setError(1, 'the command not inplement !')
            mo = __stringifyResponse(entry['jsonp'], mo)
            wsprotocol.sendData(mo)
            return  # 未找到对应的调用失败, 返回

        # IP 地址过滤
        if entry['need_ip_filter'] :
            ip = getClientIp()
            mo = entry['ip_filter'](ip)
            if mo :
                mo = __stringifyResponse(entry['jsonp'], mo)
                wsprotocol.sendData(mo)
                wsprotocol.wsClose()
                return  # IP 过滤失败, 返回

        # 执行动态调用
        try:
            mo = funws()
            if mo == None:
                mo = MsgPack()
                mo.setResult('gameId', wsgid)
                mo.setResultActCmd(wsact, wscmd)
                mo.setError(1, 'ws api return None')
        except:
            tylog.error()
            mo = MsgPack()
            mo.setResult('gameId', wsgid)
            mo.setResultActCmd(wsact, wscmd)
            mo.setError(1, 'ws api exception')

        mo = __stringifyResponse(entry['jsonp'], mo)
        wsprotocol.sendData(mo)
    except:
        tylog.error()
        mo = MsgPack()
        mo.setError(1, 'system exception return')
        mo = __stringifyResponse(0, mo)
        wsprotocol.sendData(mo)

