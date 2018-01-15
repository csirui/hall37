# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import urllib

from twisted.web import client

import freetime.util.log as ftlog
from freetime.aio import http
from poker.util import strutil

# add this to suppressing "Starting/Stopping HTTPClientFactory" log by twisted
client.HTTPClientFactory.noisy = False


def webgetJson(httpurl, datas={}, appKey=None, timeout=3):
    '''
    调用远程HTTP接口, 并返回JSON结果
    '''
    response, httpurl = webget(httpurl, datas, appKey, timeout=timeout)
    datas = None
    try:
        datas = strutil.loads(response)
    except:
        ftlog.error(httpurl, 'response=', response)
    return datas, httpurl


def webget(httpurl, querys={}, appKey=None, postdata_='',
           method_='POST', headers_={}, cookies={},
           connect_timeout=3, timeout=3, needresponse=True,
           codeKey='code', appKeyTail=None, filterParams=[], connector="&"):
    '''
    调用远程HTTP接口, 并返回JSON结果
    '''
    params = []
    if isinstance(querys, (list, tuple)):
        params.extend(querys)
    elif isinstance(querys, dict):
        keys = querys.keys()
        keys.sort()
        for k in keys:
            params.append(k)
            params.append(querys[k])

    for x in xrange(len(params)):
        param = params[x]
        if isinstance(param, unicode):
            param = param.encode('utf8')
        else:
            param = str(param)
        params[x] = param

    query2 = []
    query = []
    for x in xrange(len(params) / 2):
        k = params[x * 2]
        v = params[x * 2 + 1]
        if k not in filterParams:
            query.append(k + '=' + v)
        if k == 'authInfo':  # TODO 这部分代码是最老版的第三方的支持
            query2.append(k + '=' + v)
        else:
            query2.append(k + '=' + urllib.quote(v))
    query = connector.join(query)
    query2 = '&'.join(query2)
    if appKey:
        if appKeyTail:
            md5str = str(appKey) + query + str(appKeyTail)
        else:
            md5str = str(appKey) + query + str(appKey)
        ftlog.debug("webgetGdss,md5str:", md5str)
        md5code = strutil.md5digest(md5str)
        query2 = query2 + '&' + codeKey + '=' + md5code

    if isinstance(httpurl, unicode):
        httpurl = httpurl.encode('utf8')

    if len(query2) > 0:
        if httpurl.find('?') > 0:
            httpurl = httpurl + '&' + query2
        else:
            httpurl = httpurl + '?' + query2

    if isinstance(httpurl, unicode):
        httpurl = httpurl.encode('utf8')

    if postdata_ and isinstance(postdata_, dict):
        postdata_ = urllib.urlencode(postdata_)

    if headers_ == None or len(headers_) == 0:
        headers_ = {'Content-type': ['application/x-www-form-urlencoded']}

    if needresponse:
        _, hbody = http.runHttp(method=method_, url=httpurl, header=headers_, body=postdata_,
                                connect_timeout=connect_timeout, timeout=timeout)
        return hbody, httpurl
    else:
        http.runHttpNoResponse(method_, httpurl, headers_, postdata_, connect_timeout)
        return None, httpurl


def webgetGdss(httpurl, querys={}, postdata_='',
               method_='POST', headers_={}, cookies={},
               connect_timeout=6, timeout=6, needresponse=True):
    return webget(httpurl, querys, 'gdss.touch4.me-api-', postdata_,
                  method_, headers_, cookies,
                  connect_timeout, timeout, needresponse,
                  'sign', "-gdss.touch4.me-api", ["act"], "")
