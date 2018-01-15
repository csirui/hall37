# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.4.22

from StringIO import StringIO
from time import time

import stackless
from twisted.internet import reactor
from twisted.internet.ssl import ClientContextFactory
from twisted.web.client import Agent, readBody, FileBodyProducer
from twisted.web.http_headers import Headers

import freetime.util.log as ftlog
from freetime.util import defertool
from freetime.util.encodeobj import decodeObjUtf8


class _WebClientContextFactory(ClientContextFactory):
    def __init__(self, cfile, kfile):
        self.cfile = cfile
        self.kfile = kfile

    def getContext(self):
        ctx = ClientContextFactory.getContext(self)
        if self.cfile:
            ctx.use_certificate_file(self.cfile)
        if self.kfile:
            ctx.use_privatekey_file(self.kfile)
        return ctx


def runHttp(method, url, header, body, connect_timeout, timeout, httpsCertInfo=None):
    """
    Run http request by twisted.web.client.Agent
    instead of client.getPage.
    httpsCertInfo 为https协议时使用的证书控制，
        若httpsCertInfo为dict,则使用定制的WebClientContextFactory进行构造Agent对象
        httpsCertInfo 中可以包含： certificate https使用的证书文件的全路径
                                privatekey https使用的私有KEY文件的全路径
    """
    try:
        ct = time()
        method = decodeObjUtf8(method)
        url = decodeObjUtf8(url)
        header = decodeObjUtf8(header)
        body = decodeObjUtf8(body)
        rbody = None
        if body:
            rbody = FileBodyProducer(StringIO(body))
        if isinstance(httpsCertInfo, dict):
            certificate_file = httpsCertInfo.get('certificate')
            privatekey_file = httpsCertInfo.get('privatekey')
            contextFactory = _WebClientContextFactory(certificate_file, privatekey_file)
            agent = Agent(reactor, connectTimeout=connect_timeout, contextFactory=contextFactory)
        else:
            agent = Agent(reactor, connectTimeout=connect_timeout)

        _fttask = stackless.getcurrent()._fttask
        d = agent.request(method, url, Headers(header), rbody)
        response = _fttask.waitDefer(d, timeout)
        rcode, rpage = None, None
        if response:
            d = readBody(response)
            rpage = _fttask.waitDefer(d, timeout)
            rcode = response.code
        ct = time() - ct
        if ct > 0.3:
            ftlog.warn('WABPAGE TOO SLOW !! ', ct, url, body)
        return rcode, rpage
    except:
        ftlog.error("runHttp error", url, body)


def runHttpNoResponse(method, targetUrl, header, body, base_timeout, retrydata=None, httpsCertInfo=None):
    """
    Run http request by twisted.web.client.Agent
    instead of client.getPage.
    but we dont wait the response
    httpsCertInfo 为https协议时使用的证书控制，
        若httpsCertInfo为dict,则使用定制的WebClientContextFactory进行构造Agent对象
        httpsCertInfo 中可以包含： certificate https使用的证书文件的全路径
                                privatekey https使用的私有KEY文件的全路径
    """
    try:
        method = decodeObjUtf8(method)
        targetUrl = decodeObjUtf8(targetUrl)
        header = decodeObjUtf8(header)
        body = decodeObjUtf8(body)
        rbody = None
        if body:
            rbody = FileBodyProducer(StringIO(body))

        _timeout_call = None
        if isinstance(httpsCertInfo, dict):
            certificate_file = httpsCertInfo.get('certificate')
            privatekey_file = httpsCertInfo.get('privatekey')
            contextFactory = _WebClientContextFactory(certificate_file, privatekey_file)
            agent = Agent(reactor, connectTimeout=base_timeout, contextFactory=contextFactory)
        else:
            agent = Agent(reactor, connectTimeout=base_timeout)

        d = agent.request(method, targetUrl, Headers(header), rbody)

        def _timeout_inner(d):
            #             ftlog.debug("runHttpNoResopnse inner TIMEOUT...")
            d.cancel()

        def _succ_code_inner(response_, *args, **argd):
            if _timeout_call:
                if _timeout_call.active():
                    _timeout_call.cancel()
            b = readBody(response_)
            #             ftlog.debug("runHttpNoResopnse inner SUCCESS...")
            defertool.setDefaultCallback(b, 'runHttpNoResponse', targetUrl)

        def _err_code_inner(*args, **argd):
            if retrydata:
                retrydata['try'] += 1
                if retrydata['try'] > retrydata['max']:
                    ftlog.error('runHttpNoResponse FAIL...', retrydata, targetUrl, args, argd)
                else:
                    #                     ftlog.debug("runHttpNoResopnse RETRY...", base_timeout, retrydata, args, argd)
                    runHttpNoResponse(method, targetUrl, header, body, base_timeout * 1.5, retrydata=retrydata)
            else:
                ftlog.error('runHttpNoResponse FAIL...', retrydata, targetUrl, args, argd)

        d.addCallback(_succ_code_inner)
        d.addErrback(_err_code_inner)
        _timeout_call = reactor.callLater(base_timeout, _timeout_inner, d)
    except:
        ftlog.error("runHttp error", targetUrl, body)
