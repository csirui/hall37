# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''


from tyserver.tyutils import tyhttp, strutil
from webmgr.action import actlog
from webmgr.action.debugs import redisdata


def action(options, withlog=1):
    serverIds = options.serverIds
    hotfixpy = options.hotfixpy
    if not hotfixpy.startswith('code://') :
        hotfixpy = 'file://' + hotfixpy

    httpgame = getattr(options, '_httpgame', None)
    if not httpgame :
        datas = redisdata._getLastOkDefines(options)
        httpgame = datas['pokerdict']['http_game'] + '/_http_manager_hotfix'
        setattr(options, '_httpgame', httpgame)
    hotparams = getattr(options, 'hotparams', None)
    if not isinstance(hotparams, dict) :
        hotparams = {}

    if withlog :
        actlog.log("hotfixpy   =", hotfixpy)
        actlog.log("hotfixwait =", options.hotfixwait)
        actlog.log("serverIds  =", serverIds)
        actlog.log("httpgame   =", httpgame)
        actlog.log('hotparams  =', hotparams)

    result = tyhttp.dohttpquery(httpgame, {'hotfixpy' : hotfixpy,
                                           'wait' : options.hotfixwait,
                                           'serverIds' : serverIds,
                                           'hotparams' : strutil.dumps(hotparams)})
    if withlog :
        actlog.log('result    =', result)
        return 1
    return result


def printErrorRet(ret):
    if ret.find('"error"') >= 0 :
        actlog.log('ERROR !!')
        try:
            errs = strutil.loads(ret)
            for sid in errs :
                actlog.log('============ EXCEPTIONS OF %s ============' % (sid))
                excs = errs[sid]['error']
                l = excs.split('\n')
                for x in l :
                    if x != '' :
                        actlog.log(x)
        except:
            actlog.log('ERROR !!', ret)
        actlog.log('ERROR !!')
        return 1
    else:
        actlog.log(ret)
    return 0
