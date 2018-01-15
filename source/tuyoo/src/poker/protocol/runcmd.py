# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import stackless

import freetime.entity.service as ftsvr
import freetime.util.log as ftlog
from freetime.core.lock import FTLock
from freetime.entity.msg import MsgPack
from poker.protocol import _runenv
from poker.protocol import router, oldcmd, rpccore
from poker.util import strutil


def isCmdTask():
    '''
    判定当前是否是TCP命令,引发的tasklet
    '''
    session = stackless.getcurrent()._fttask.session
    return session.get('iscmd', 0)


def getMsgPack():
    '''
    取得当前TCP的消息
    '''
    return ftsvr.getTaskPack()  # stackless.getcurrent()._fttask.pack


def newErrorMsgPack(errCode, edrrInfo):
    '''
    快速工具, 依据当前接收的命令, 生成一个返回错误信息的MsgPack
    '''
    mi = getMsgPack()
    mo = MsgPack()
    mo.setCmd(mi.getCmd())
    action = mi.getParam('action')
    if action:
        mo.setParam('action', action)
    mo.setError(errCode, edrrInfo)
    return mo


def newOkMsgPack(code=1):
    '''
    快速工具, 依据当前接收的命令, 生成一个返回OK信息的MsgPack
    '''
    mi = getMsgPack()
    mo = MsgPack()
    mo.setCmd(mi.getCmd())
    action = mi.getParam('action')
    if action:
        mo.setParam('action', action)
    mo.setResult('ok', code)
    return mo


def getClientId(msg=None):
    '''
    获取当前命令的clientId的大版本号,
    如果消息中没有clientId,那么取用户的登录时的clientId
    '''
    if not msg:
        msg = getMsgPack()
    clientId = msg.getKey('clientId')
    if clientId:
        return clientId
    return msg.getParam('clientId')


def getClientIdVer(msg):
    '''
    获取当前命令的clientId的大版本号,
    如果消息中没有clientId,那么取用户的登录时的clientId
    '''
    client_ver = 0
    clientId = getClientId(msg)
    if clientId:
        try:
            clientId = float(clientId)  # BUGFIX 老版本的传递有时候是个数字
            return clientId
        except:
            pass
        _, client_ver, _ = strutil.parseClientId(clientId)
        if client_ver > 0:
            return client_ver
    ftlog.warn('WARRING !! the tcp msg clientId is error !!', msg)
    return 0


def handlerCommand(msg):
    """
    TCP消息命令处理总入口
    """
    orgcmd = msg.getCmd()
    if orgcmd == _runenv._CMD_RPC_:
        return rpccore._handlerRpcCommand(msg)

    orgaction = msg.getParam('action')
    gameId = msg.getParam('gameId')
    cmd, action = None, None
    try:
        if orgaction == None:
            orgaction = ''
        # ftlog.debug('handlerCommand->cmd, action->', cmd, action)
        cmdpath, cmd, action = oldcmd.convertCmdPath(orgcmd, orgaction, msg)
        #         ftlog.debug('handlerCommand->cmd, action, cmdpath, ver, gameId ->', cmd, action, cmdpath, ver, gameId)
        # 先以cmd#action#gameId去查找命令处理器
        vercalls = None
        if gameId:
            vercalls = _runenv._cmd_path_methods.get(cmdpath + '#' + str(gameId), None)
        # 再以cmd#action去查找命令处理器
        if not vercalls:
            vercalls = _runenv._cmd_path_methods.get(cmdpath, None)
        # 再以cmd#*去查找名利处理器
        if not vercalls:
            vercalls = _runenv._cmd_path_methods.get(str(cmd) + '#*#' + str(gameId), None)
        # 再以cmd#*去查找名利处理器
        if not vercalls:
            vercalls = _runenv._cmd_path_methods.get(str(cmd) + '#*', None)
        # ftlog.debug('handlerCommand->vercalls->', vercalls)
        # 再经过clietnId的版本号过滤
        markParams = None
        if vercalls:
            if len(vercalls) > 1:
                ver = getClientIdVer(msg)
                for vercall in vercalls:
                    if ver >= vercall[0]:
                        markParams = vercall[1]
                        break
            else:
                markParams = vercalls[0][1]
        else:
            vercalls = []
        # 若未找到对应的mark定义, 错误返回
        if not markParams:
            raise Exception('the cmd path method not found ! cmdpath=' + str(cmdpath) +
                            ' clientIdVer=' + str(getClientIdVer(msg)) + ' vercalls len=' + str(len(vercalls)) +
                            ' gameId=' + str(gameId) + ' msg=' + str(msg))
        # 锁定当前mark定义的资源
        lockParamName = markParams.get('lockParamName', None)
        if lockParamName:
            lockval = msg.getParam(lockParamName)
            if lockParamName == 'userId' or lockParamName == 'tableId':
                assert (isinstance(lockval, int))
            lockkey = 'lock:' + lockParamName + ':' + str(lockval)
            ftlock = _runenv._FTLOCKS.get(lockkey, None)
            if ftlock == None:
                ftlock = FTLock(lockkey)
                _runenv._FTLOCKS[lockkey] = ftlock
            ftlog.debug('lock resource of', lockkey, 'wait !!')
            ftlock.lock()
            ftlog.debug('lock resource of', lockkey, 'locked !!')

        try:
            if markParams['isRpc']:
                # RPC CALL
                _handlerRpcCommand(markParams, msg)
            else:
                # CLIENT MSG CALL
                _handlerMsgCommand(markParams, msg)
        finally:
            # 释放当前mark定义的资源
            if lockParamName:
                ftlog.debug('lock resource of', lockkey, 'released !!')
                if ftlock.unlock() == 0:
                    del _runenv._FTLOCKS[lockkey]
                    pass
    except Exception, e:
        ftlog.error('cmd=' + str(cmd) + ' action=' + str(action) + ' gameId=' + str(gameId),
                    'orgcmdpath=' + str(orgcmd) + '#' + str(orgaction))
        if router.isQuery():
            targs = ftsvr.getTaskRunArg()
            if not targs.get('responsed') and targs.get('userheader1') == 'CQ':
                response = newErrorMsgPack(1, str(e))
                router.responseQurery(response)


def _handlerRpcCommand(markParams, msg):
    handler = markParams['handler']
    fun_method = markParams['fun_method']

    argl = msg.getParam('argl')
    argd = msg.getParam('argd')
    ret = fun_method(handler, *argl, **argd)
    if markParams['syncCall']:
        mo = MsgPack()
        mo.setKey('result', ret)
        router.responseQurery(mo, 'QR')


def _handlerMsgCommand(markParams, msg):
    handler = markParams['handler']
    fun_method = markParams['fun_method']
    #     ftlog.debug('_handlerMsgCommand->', handler, fun_method)
    errmsg, values = _checkCmdParams(handler, markParams['paramkeys'])
    if errmsg:
        ftlog.error('the command params error !! msg=', getMsgPack(), 'errmsg=', errmsg)

    if router.isQuery():
        if errmsg:
            if not isinstance(errmsg, MsgPack):
                errmsg = newErrorMsgPack(2, errmsg)
            router.responseQurery(errmsg)
            try:
                filterErrorMessage(msg)
            except:
                ftlog.error("filterErrorMessage error. msg:", msg)
        else:
            try:
                response = fun_method(*values)
                if not response:
                    response = newOkMsgPack(1)
            except Exception, e:
                ftlog.error('method->', fun_method, 'Exception !', ftsvr.getTaskRunArg())
                response = newErrorMsgPack(1, str(e))
            targs = ftsvr.getTaskRunArg()
            if not targs.get('responsed'):
                if targs.get('userheader1') == 'CQ':
                    if not isinstance(response, MsgPack):
                        response = newOkMsgPack(1)
                router.responseQurery(response)
    else:
        if not errmsg:
            fun_method(*values)
        else:
            try:
                filterErrorMessage(msg)
            except:
                ftlog.error("filterErrorMessage error. msg:", msg)


def filterErrorMessage(msg):
    from poker.util import webpage

    gameId, clientId, userId, action = msg.getParams('gameId', 'clientId', 'userId', 'action')
    cmd = msg.getCmd()
    bugclientId = 'IOS_3.82_tuyoo.appStore,weixinPay,alipay.0-hall6.appStore.tuyoo2016'
    url = 'http://open.touch4.me/open/v3/user/setForbidden'

    if (gameId is None and cmd == 'game' and action == 'leave' and clientId == bugclientId):
        datas = {'lock_users': [userId]}
        ftlog.warn('kill cracker, msg:', msg)
        webpage.webgetJson(url, datas, None, 10)


def _checkCmdParams(handler, paramkeys):
    '''
    检查校验当前TCP命令入口的参数
    '''
    values = []
    params = {}
    if not paramkeys:
        return None, values
    msg = getMsgPack()
    key, funname = None, None
    for key in paramkeys:
        funname = '_check_param_' + key
        func = getattr(handler, funname, None)
        if func == None:
            ftlog.error('__checkCmdParams->', funname, 'is none !', handler)
        error, value = func(msg, key, params)
        if error:
            return error, None
        values.append(value)
        params[key] = value
    return None, values


def debugCmdInfos():
    cmds = set()
    for cmd in _runenv._cmd_path_methods:
        cmds.add(cmd.split('#')[0])
    ftlog.debug('COMMANDS=', cmds)
