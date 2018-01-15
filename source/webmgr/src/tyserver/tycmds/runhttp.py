# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
from datetime import datetime
import functools, inspect, os, stackless, urllib

from twisted.internet import defer, reactor
from twisted.internet.defer import succeed
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from zope.interface import implements

from tyserver.tyutils import tylog, strutil
from tyserver.tyutils.msg import MsgPack
from tyserver.tycmds import InitFlg


TRACE_RESPONSE = 1
CONTENT_TYPE_JSON = {'Content-Type':'application/json;charset=UTF-8'}
CONTENT_TYPE_HTML = {'Content-Type': 'text/html;charset=UTF-8'}

__http_path_methods = {}
__path_webroots = []


def isHttpTask():
    session = stackless.getcurrent()._fttask.session
    return session.get('ishttp', 0)


def getRequest():
    return stackless.getcurrent()._fttask.run_args['httprequest']


def getClientIp():
    request = getRequest()
    ip = request.getHeader('x-real-ip')
    if ip == None :
        ip = request.getClientIP()
    return ip


def getHeader(headName):
    request = getRequest()
    val = request.getHeader(headName)
    return val


def getPath():
    request = getRequest()
    return request.path


def getRawData():
    r = getRequest()
    return ['HEADERS', r.getAllHeaders(),
            'METHOD', r.method, 'URI', r.uri, 'CLIENTPROTO', r.clientproto,
            'CONTENT', r.content.getvalue(), ]


def getParamStr(key, defaultVal=None):
    request = getRequest()
    args = request.args
    if key in args :
        vals = args[key]
        return vals[0]
    return defaultVal


def getParamInt(key, defaultVal=0):
    val = getParamStr(key, defaultVal)
    try:
        return int(val)
    except:
        pass
    return defaultVal


def getParamFloat(key, defaultVal=0.0):
    val = getParamStr(key, defaultVal)
    try:
        return float(val)
    except:
        pass
    return defaultVal


def getMsgPack(keys=None):
    request = getRequest()
    args = request.args
    msg = MsgPack()
    if keys == None :
        keys = args.keys()
    for key in keys :
        if key in args :
            value = args[key][0]
        else:
            value = ''
        msg.setParam(key, value.strip())
    rpath = request.path.lower().replace('/', '_')
    msg.setCmd(rpath[1:])
    return msg


def getDict():
    request = getRequest()
    args = request.args
    rparam = {}
    for k, v in args.items() :
        rparam[k] = v[0].strip()
    return rparam


def setParam(key, val):
    request = getRequest()
    request.args[key] = [val]


def getBody():
    session = stackless.getcurrent()._fttask.session
    body = session.get('http_body_data', None)
    if body == None :
        request = getRequest()
        body = request.content.read().strip()
        session['http_body_data'] = body
    return body


def doRedirect(redirectUrl):
    request = getRequest()
    request.redirect(redirectUrl)
    doFinish('', {}, False)


def doFinish(content, fheads, debugreturn=True):

    request = getRequest()
    rpath = request.path
    if debugreturn :
        debugcontent = content
        if len(debugcontent) > 128 and debugcontent[0] != '{':
            debugcontent = repr(debugcontent[0:128]) + '......'
        if TRACE_RESPONSE :
            tylog.info('HTTPRESPONSE', rpath, debugcontent)
    else:
        if TRACE_RESPONSE :
            tylog.info('HTTPRESPONSE', rpath)

    if getattr(request, 'finished', 0) == 1 :
        tylog.error('HTTPRESPONSE already finished !!', rpath)
        return

    request.setHeader('Content-Length', len(content))
    try:
        for k, v in fheads.items() :
            request.setHeader(k, v)
    except:
        tylog.error(rpath)

    try:
        request.write(content)
    except:
        try:
            request.write(content.encode('utf8'))
        except:
            tylog.error(rpath)

    try:
        request.channel.persistent = 0
    except:
        pass

    try:
        request.finish()
    except:
        if TRACE_RESPONSE :
            tylog.error(rpath)

    setattr(request, 'finished', 1)


def markHttpRequestEntry(httppath=None, jsonp=False, ip_filter=False, extend_tag=None, response='json'):
    jsonp = 1 if jsonp else 0
    ip_filter = 1 if ip_filter else 0
    if not response in ('json', 'html'):
        response = 'json'

    entry = {
            'jsonp' : jsonp,
            'need_ip_filter' : ip_filter,
            'extend_tag' : extend_tag,
            'response' : response,
            'httppath' : httppath
    }

    def decorating_function(method):
        paramkeys, _, __, ___ = inspect.getargspec(method)
        if len(paramkeys) > 0 :  # 去除self和cls关键字
            if paramkeys[0] in ('self', 'cls') :
                paramkeys = paramkeys[1:]
            else:
                raise Exception('a http method must be a class or object instance')
        entry['paramkeys'] = paramkeys
        @functools.wraps(method)
        def funwarp(*args, **argd):
            return __httpEntryWrapCall(entry, method, *args, **argd)
        setattr(funwarp, '_http_request_entry_', entry)
        return funwarp
    return decorating_function


def __httpEntryWrapCall(entry, method, *args, **argd):
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
        callback = getParamStr('callback', '').strip()
        if len(callback) > 0 and not content.startswith(callback):
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
    添加一个HTTP请求处理的入口实例
    参数: handler HTTP请求的类或实例, 其定义的HTTP方法必须使用: @markHttpRequestEntry 进行修饰
    '''
    tylog.info('HTTP Add Handler ->', handler)
    for key in dir(handler):
        method = getattr(handler, key)
        if callable(method) :
            entry = getattr(method, '_http_request_entry_', None)
            if isinstance(entry, dict) :
                __registerHttpEntry(handler, method, entry)


def __registerHttpEntry(handler, method, entry):
    # 确定HTTP的API路径
    httppath = entry.get('httppath', None)
    if not isinstance(httppath, (str, unicode)) or len(httppath) <= 0 :
        httppath = method.__name__.replace('_', '/')
        if httppath.find('do/http/') == 0 :
            httppath = httppath[7:]
        if httppath[0] != '/' :
            httppath = '/' + httppath
        while httppath.find('//') >= 0 :
            httppath = httppath.replace('//', '/')
        entry['httppath'] = httppath
    # 确定是否需要IP过滤
    entry['ip_filter'] = __dummyIpFilter
    if entry['need_ip_filter'] :
        ip_filter = getattr(handler, 'ip_filter', None)
        if callable(ip_filter) :
            entry['ip_filter'] = ip_filter
    # 确定返回的ContentType
    if entry['response'] == 'json' or entry['jsonp'] == 1:
        entry['content_type'] = CONTENT_TYPE_JSON
    else:
        entry['content_type'] = CONTENT_TYPE_HTML

    if httppath in __http_path_methods :
        tylog.info('WARRING !! the http path already defined !! httppath=' + str(httppath))
    __http_path_methods[httppath] = (method, entry)
    tylog.info('HTTP Add Entry ->', httppath, 'method=' , method)
    return httppath


def handlerHttpRequest(httprequest):
    if InitFlg.isInitOk != 1:
        mo = MsgPack()
        mo.setError(1, 'http system not startup')
        mo = __stringifyResponse(0, mo)
        doFinish(mo, CONTENT_TYPE_HTML)
        return

    mo = None
    try:
        session = stackless.getcurrent()._fttask.session
        session['ishttp'] = 1

        rpath = httprequest.path
        if TRACE_RESPONSE :
            tylog.info('HTTPREQUEST', rpath, httprequest.args)
        
        # 当前服务处理
        funhttp, entry = __http_path_methods.get(rpath, (None, None))
        if funhttp == None or entry == None:
            __handlerHttpStatic(httprequest)
            return  # 查找静态资源返回

        # IP 地址过滤
        if entry['need_ip_filter'] :
            ip = getClientIp()
            mo = entry['ip_filter'](ip)
            if mo :
                mo = __stringifyResponse(entry['jsonp'], mo)
                doFinish(mo, entry['content_type'])
                return  # IP 过滤失败, 返回

        # 执行动态调用
        try:
            mo = funhttp()  # 最新版本的 @http_request_entry 方法
            if mo == None:
                mo = MsgPack()
                mo.setCmd(rpath)
                mo.setError(1, 'http api return None')
        except:
            tylog.error()
            mo = MsgPack()
            mo.setCmd(rpath)
            mo.setError(1, 'http api exception')

        mo = __stringifyResponse(entry['jsonp'], mo)
        doFinish(mo, entry['content_type'], rpath)
    except:
        tylog.error()
        mo = MsgPack()
        mo.setCmd(rpath)
        mo.setError(1, 'system exception return')
        mo = __stringifyResponse(0, mo)
        doFinish(mo, CONTENT_TYPE_HTML)


def addWebRoot(webroot):
    if not webroot in __path_webroots :
        webroot = os.path.abspath(webroot) + os.path.sep
        tylog.info('HTTP Add WEBROOT ->', webroot)
        __path_webroots.append(webroot)
    else:
        tylog.info('HTTP Add WEBROOT already add !!->', webroot)


def __handlerHttpStatic(httprequest):

    rpath = httprequest.path

    fgmt, fcontent, fheads = None, None, None
    for wpath in __path_webroots :
        fpath = wpath + rpath
        fpath = os.path.abspath(fpath)
        if fpath.find(wpath) == 0 and os.path.isfile(fpath) :
            fgmt, fcontent, fheads = __loadResource(fpath)
            if fgmt != None:
                break

    if fgmt == None :
        httprequest.setResponseCode(404, 'Not Found')
        doFinish('', {}, False)
    elif httprequest.getHeader('If-Modified-Since') == fgmt :
        httprequest.setResponseCode(304, 'Not Modified')
        doFinish('', fheads, False)
    elif httprequest.getHeader('If-None-Match') == fgmt :
        httprequest.setResponseCode(304, 'Not Modified')
        doFinish('', fheads, False)
    else:
        doFinish(fcontent, fheads, False)


def __loadResource(fpath):
    filemt = os.path.getmtime(fpath)
    fdt = datetime.fromtimestamp(filemt)
    fgmt = fdt.strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    ffile = file(fpath, 'r')
    fcontent = ffile.read()
    ffile.close()

    fheads = {}
    if fpath.endswith('.html') or fpath.endswith('.ty'):
        fheads['Content-Type'] = 'text/html;charset=UTF-8'
    elif fpath.endswith('.css') :
        fheads['Content-Type'] = 'text/css;charset=UTF-8'
    elif fpath.endswith('.js') :
        fheads['Content-Type'] = 'application/x-javascript;charset=UTF-8'
    elif fpath.endswith('.jpeg') or fpath.endswith('.jpg') :
        fheads['Content-Type'] = 'image/jpeg'
    elif fpath.endswith('.png') :
        fheads['Content-Type'] = 'image/png'
    elif fpath.endswith('.zip') :
        fheads['Content-Type'] = 'application/zip'
    elif fpath.endswith('.apk') :
        fheads['Content-Type'] = 'application/vnd.android.package-archive'

    fheads['Date'] = fgmt
    fheads['Etag'] = fgmt
    fheads['Last-Modified'] = fgmt
    fheads['Cache-Control'] = 'no-cache'
    return fgmt, fcontent, fheads


class __StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


def doProxy(httpurl, datas, headers_=None, timeout=3):
    postdata_ = ''
    if datas :
        postdata_ = urllib.urlencode(datas)
    body = __StringProducer(postdata_)
    agent = Agent(reactor)
    headers = {}
    if headers_ :
        for k, v in headers_:
            headers[k] = [v]
    headers['User-Agent'] = ['Twisted Web Client Proxy']
    if datas :
        headers['Content-type'] = ['application/x-www-form-urlencoded']
    d = agent.request('POST', httpurl, Headers(headers), body)

    request = getRequest()
    resultDeferred = defer.Deferred()
    def cbProxyBody(responsebody):
        try:
            request.write(responsebody)
        except:
            tylog.error('doProxy->cbProxyBody', httpurl)
        try:
            resultDeferred.callback('')
        except:
            tylog.error('doProxy->cbProxyBody', httpurl)

    def cbProxyRequest(response):
        try:
            request.setResponseCode(response.code)
            for k, v in response.headers.getAllRawHeaders():
                if isinstance(v, (list, tuple)) :
                    for vv in v :
                        request.setHeader(k, vv)
                else:
                    request.setHeader(k, v)
        except:
            tylog.error('doProxy->cbProxyRequest', httpurl)
        dd = readBody(response)
        dd.addCallback(cbProxyBody)
        return dd

    d.addCallback(cbProxyRequest)
    tasklet = stackless.getcurrent()._fttask
    tasklet._report_wait_prep_(httpurl)
    tasklet.waitDefer(resultDeferred, timeout)
    doFinish('', {})

