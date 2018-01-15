# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import os
import urllib

import stackless
from datetime import datetime
from twisted.internet import defer, reactor
from twisted.internet.defer import succeed
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from zope.interface import implements

import freetime.util.log as ftlog
from freetime.core.tasklet import FTTasklet
from freetime.entity.msg import MsgPack
from poker.entity.configure import gdata
from poker.util import strutil

TRACE_RESPONSE = 0  # 是否跟踪打印所有的REQUEST和RESPONSE
CONTENT_TYPE_JSON = {'Content-Type': 'application/json;charset=UTF-8'}
CONTENT_TYPE_HTML = {'Content-Type': 'text/html;charset=UTF-8'}
CONTENT_TYPE_PLAIN = {'Content-Type': 'application/octet-stream', 'Content-Disposition': 'attachment'}
CONTENT_TYPE_GIF = {'Content-Type': 'image/gif'}

_http_path_methods = {}  # HTTP命令集合中心, key为HTTP的全路径, value为处理该路径的callable
_path_webroots = []  # 静态资源的查找路径列表


def isHttpTask():
    '''
    判定当前是否是HTTP请求引发的tasklet
    '''
    return gdata.getTaskSession().get('ishttp', 0)


def getRequest():
    '''
    取得当前HTTP请求的原始的request对象
    '''
    return stackless.getcurrent()._fttask.run_args['data']


def getClientIp():
    '''
    取得当前HTTP请求的远程IP地址(以考虑nginx进行代理的模式, nginx代理时需设定:x-real-ip头)
    '''
    request = getRequest()
    ip = request.getHeader('x-real-ip')
    if ip is None:
        ip = request.getClientIP()
    return ip


def getHeader(headName):
    '''
    取得HTTP请求头的值
    '''
    request = getRequest()
    val = request.getHeader(headName)
    return val


def getPath():
    '''
    取得当前HTTP请求的路径
    '''
    request = getRequest()
    return request.path


def getRawData():
    '''
    取得当前HTTP请求的数据内容(全体数据信息)
    '''
    r = getRequest()
    return ['HEADERS', r.getAllHeaders(),
            'METHOD', r.method, 'URI', r.uri, 'CLIENTPROTO', r.clientproto,
            'CONTENT', r.content.getvalue(), ]


def getParamStr(key, defaultVal=None):
    '''
    取得当前HTTP请求的一个参数值
    '''
    request = getRequest()
    args = request.args
    if key in args:
        vals = args[key]
        return vals[0]
    return defaultVal


def getParamInt(key, defaultVal=0):
    '''
    取得当前HTTP请求的一个参数的int值
    '''
    val = getParamStr(key, defaultVal)
    try:
        return int(val)
    except:
        pass
    return defaultVal


def getParamFloat(key, defaultVal=0.0):
    '''
    取得当前HTTP请求的一个参数的float值
    '''
    val = getParamStr(key, defaultVal)
    try:
        return float(val)
    except:
        pass
    return defaultVal


def getMsgPack(keys=None):
    '''
    将当前的HTTP请求的路径和参数内容, 转换为一个MsgPack
    '''
    request = getRequest()
    args = request.args
    msg = MsgPack()
    if keys == None:
        keys = args.keys()
    for key in keys:
        if key in args:
            value = args[key][0]
        else:
            value = ''
        msg.setParam(key, value.strip())
    rpath = request.path.lower().replace('/', '_')
    msg.setCmd(rpath[1:])
    return msg


def getDict():
    '''
    将当前的HTTP请求的所有参数内容, 转换为一个dict
    '''
    request = getRequest()
    args = request.args
    rparam = {}
    for k, v in args.items():
        rparam[k] = v[0].strip()
    return rparam


def setParam(key, val):
    '''
    设置当前HTTP请求参数的键值对
    注: 此方法仅在某些特殊需求下才会被调用
    '''
    request = getRequest()
    request.args[key] = [val]


def getBody():
    '''
    取得当前HTTP的POST发送的BODY的字符串
    '''
    session = stackless.getcurrent()._fttask.session
    body = session.get('http_body_data', None)
    if body is None:
        request = getRequest()
        body = request.content.read().strip()
        session['http_body_data'] = body
    return body


def doRedirect(redirectUrl):
    '''
    对当前的HTTP请求进行302转向处理
    '''
    request = getRequest()
    request.redirect(redirectUrl)
    doFinish('', {}, False)


def doFinish(content, fheads, debugreturn=True):
    '''
    完结当前的HTTP的请求, 并发送响应数据
    '''
    request = getRequest()
    rpath = request.path
    if debugreturn:
        debugcontent = content
        if len(debugcontent) > 128 and debugcontent[0] != '{':
            debugcontent = repr(debugcontent[0:128]) + '......'
        if TRACE_RESPONSE:
            ftlog.info('HTTPRESPONSE', rpath, debugcontent)
    else:
        if TRACE_RESPONSE:
            ftlog.info('HTTPRESPONSE', rpath)

    if getattr(request, 'finished', 0) == 1:
        ftlog.error('HTTPRESPONSE already finished !!', rpath)
        return

    request.setHeader('Content-Length', len(content))
    try:
        for k, v in fheads.items():
            request.setHeader(k, v)
    except:
        ftlog.error(rpath)

    try:
        request.write(content)
    except:
        try:
            request.write(content.encode('utf8'))
        except:
            ftlog.error(rpath)

    try:
        request.channel.persistent = 0
    except:
        pass

    try:
        request.finish()
    except:
        if TRACE_RESPONSE:
            ftlog.error(rpath)

    setattr(request, 'finished', 1)


def __stringifyResponse(isjsonp, content, content_type=''):
    """
    序列化响应的数据内容
    """
    if isinstance(content, (str, unicode)):
        pass
    elif isinstance(content, MsgPack):
        content = content.pack()
    elif isinstance(content, (list, tuple, dict)):
        content = strutil.dumps(content)
    elif isinstance(content, set):
        content = strutil.dumps(list(content))
    elif isinstance(content, (int, float, bool)):
        content = str(content)
    else:
        content = repr(content)
    if 'utf-8' in content_type:
        content = content.encode('utf-8')
    if isjsonp:
        callback = getParamStr('callback', '').strip()
        if len(callback) > 0:
            content = '%s(%s);' % (callback, content)
    return content


def _checkRequestParams(apiobj, paramkeys):
    '''
    检查校验HTTP请求的输入参数
    '''
    values = []
    params = {}
    if not paramkeys:
        return None, values
    key, funname = None, None
    for key in paramkeys:
        funname = '_check_param_' + key
        func = getattr(apiobj, funname, None)
        if func == None:
            ftlog.error('__checkCmdParams->', funname, 'is none !', apiobj)
        error, value = func(key, params)
        if error:
            return error, None
        values.append(value)
        params[key] = value
    return None, values


def handlerHttpRequest(httprequest):
    """
    HTTP请求处理总入口
    """
    rpath = httprequest.path
    try:
        session = stackless.getcurrent()._fttask.session
        session['ishttp'] = 1

        if TRACE_RESPONSE:
            ftlog.info('HTTPREQUEST', rpath, httprequest.args)

        # 当前服务处理
        markParams = _http_path_methods.get(rpath, None)
        if markParams == None:
            __handlerHttpStatic(httprequest)
            return  # 查找静态资源返回

        # IP 地址过滤
        fun_ip_filter = markParams['fun_ip_filter']
        if fun_ip_filter:
            ip = getClientIp()
            mo = fun_ip_filter(ip)
            if mo:
                mo = __stringifyResponse(markParams['jsonp'], mo, markParams['content_type'])
                doFinish(mo, markParams['content_type'])
                return  # IP 过滤失败, 返回

        # 执行动态调用
        try:
            handler = markParams['handler']
            fun_method = markParams['fun_method']
            mo, values = _checkRequestParams(handler, markParams['paramkeys'])
            if not mo:  # 参数检测, 没有错误
                mo = fun_method(*values)
            if mo is None:
                mo = MsgPack()
                mo.setCmd(rpath)
                mo.setError(1, 'http api return None')
        except Exception, e:
            ftlog.error()
            mo = MsgPack()
            mo.setCmd(rpath)
            mo.setResult('Exception', str(e))
            mo.setError(1, 'http api exception')

        mo = __stringifyResponse(markParams['jsonp'], mo, markParams['content_type'])
        doFinish(mo, markParams['content_type'], rpath)
    except Exception, e:
        ftlog.error()
        mo = MsgPack()
        mo.setCmd(rpath)
        mo.setResult('Exception', str(e))
        mo.setError(1, 'system exception return')
        mo = __stringifyResponse(0, mo, '')
        doFinish(mo, CONTENT_TYPE_HTML)


def addWebRoot(webroot):
    '''
    添加静态资源查找路径
    '''
    if not webroot in _path_webroots:
        webroot = os.path.abspath(webroot) + os.path.sep
        if TRACE_RESPONSE:
            ftlog.info('HTTP Add WEBROOT ->', webroot)
        _path_webroots.append(webroot)
    else:
        if TRACE_RESPONSE:
            ftlog.info('HTTP Add WEBROOT already add !!->', webroot)


def __handlerHttpStatic(httprequest):
    '''
    HTTP请求静态资源
    '''
    rpath = httprequest.path

    fgmt, fcontent, fheads = None, None, None
    for wpath in _path_webroots:
        fpath = wpath + rpath
        fpath = os.path.abspath(fpath)
        if fpath.find(wpath) == 0 and os.path.isfile(fpath):
            fgmt, fcontent, fheads = __loadResource(fpath)
            if fgmt != None:
                break

    if fgmt == None:
        httprequest.setResponseCode(404, 'Not Found')
        doFinish('', {}, False)
    elif httprequest.getHeader('If-Modified-Since') == fgmt:
        httprequest.setResponseCode(304, 'Not Modified')
        doFinish('', fheads, False)
    elif httprequest.getHeader('If-None-Match') == fgmt:
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
    if fpath.endswith('.html') or fpath.endswith('.txt'):
        fheads['Content-Type'] = 'text/html;charset=UTF-8'
    elif fpath.endswith('.css'):
        fheads['Content-Type'] = 'text/css;charset=UTF-8'
    elif fpath.endswith('.js'):
        fheads['Content-Type'] = 'application/x-javascript;charset=UTF-8'
    elif fpath.endswith('.jpeg') or fpath.endswith('.jpg'):
        fheads['Content-Type'] = 'image/jpeg'
    elif fpath.endswith('.png'):
        fheads['Content-Type'] = 'image/png'
    elif fpath.endswith('.zip'):
        fheads['Content-Type'] = 'application/zip'
    elif fpath.endswith('.apk'):
        fheads['Content-Type'] = 'application/vnd.android.package-archive'

    fheads['Date'] = fgmt
    fheads['Etag'] = fgmt
    fheads['Last-Modified'] = fgmt
    fheads['Cache-Control'] = 'no-cache'
    return fgmt, fcontent, fheads


class __StringProducer(object):
    '''
    代理服务使用的HTTP BODY的产生器
    '''
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
    '''
    进行HTTP的代理协议处理
    '''
    postdata_ = ''
    if datas:
        postdata_ = urllib.urlencode(datas)
    body = __StringProducer(postdata_)
    agent = Agent(reactor)
    headers = {}
    if headers_:
        for k, v in headers_:
            headers[k] = [v]
    headers['User-Agent'] = ['Twisted Web Client Proxy']
    if datas:
        headers['Content-type'] = ['application/x-www-form-urlencoded']
    d = agent.request('POST', httpurl, Headers(headers), body)

    request = getRequest()
    resultDeferred = defer.Deferred()

    def cbProxyBody(responsebody):
        try:
            request.write(responsebody)
        except:
            ftlog.error('doProxy->cbProxyBody', httpurl)
        try:
            resultDeferred.callback('')
        except:
            ftlog.error('doProxy->cbProxyBody', httpurl)

    def cbProxyRequest(response):
        try:
            request.setResponseCode(response.code)
            for k, v in response.headers.getAllRawHeaders():
                if isinstance(v, (list, tuple)):
                    for vv in v:
                        request.setHeader(k, vv)
                else:
                    request.setHeader(k, v)
        except:
            ftlog.error('doProxy->cbProxyRequest', httpurl)
        dd = readBody(response)
        dd.addCallback(cbProxyBody)
        return dd

    d.addCallback(cbProxyRequest)
    tasklet = FTTasklet.getCurrentFTTasklet()
    tasklet.waitDefer(resultDeferred, timeout)
    doFinish('', {})


def _createLinkString(rparam):
    sk = rparam.keys()
    sk.sort()
    ret = ""
    for k in sk:
        ret = ret + str(k) + '=' + str(rparam[k]) + '&'
    return ret[:-1]


def checkHttpParamCode(appKey, codeKey='code'):
    request = getRequest()
    args = request.args
    ftlog.debug('checkHttpParamCode->', args)
    rparam = {}
    for k, v in args.items():
        rparam[k] = v[0]
    code = rparam[codeKey]
    del rparam[codeKey]
    signStr = _createLinkString(rparam)
    md5code = strutil.md5digest(str(appKey) + signStr + str(appKey))
    if md5code != code:
        return False
    return True
