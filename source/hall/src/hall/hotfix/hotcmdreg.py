# -*- coding=utf-8 -*-
import importlib
import inspect
import sys

import freetime.util.log as ftlog
from poker.protocol import runcmd, decorator

global exec_result


def unRegisterCmdActionMethod(gameId, fullName, handler, method, markParams):
    cmd = markParams.get('cmd', None)
    assert (isinstance(cmd, (str, unicode)) and len(cmd.strip()) > 0)
    assert (cmd.find('#') < 0)

    action = markParams.get('action', '')
    assert (isinstance(action, (str, unicode)))
    action = action.strip()
    assert (action.find('#') < 0)

    clientIdVer = markParams.get('clientIdVer', 0.0)
    assert (isinstance(clientIdVer, (int, float)))

    scope = markParams.get('scope', 'global')
    assert (scope in ('global', 'game'))

    cmdpath = cmd + '#' + action
    if scope == 'game':
        cmdpath = cmdpath + '#' + str(gameId)

    vcalls = runcmd._cmd_path_methods.get(cmdpath, None)
    ftlog.info('unRegisterCmdActionMethod->vcalls=', vcalls)
    if vcalls:
        for x in xrange(len(vcalls)):
            if vcalls[x][0] == clientIdVer:
                ftlog.info('unRegisterCmdActionMethod->cmdpath=', cmdpath, 'clientIdVer=', clientIdVer, 'old=',
                           vcalls[x])
                del vcalls[x]
                return 1
    ftlog.info('unRegisterCmdActionMethod->cmdpath=', cmdpath, 'clientIdVer=', clientIdVer, 'old=notfound !!')
    return 0


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

    vcalls = runcmd._cmd_path_methods.get(cmdpath, None)
    if not vcalls:
        vcalls = []
        runcmd._cmd_path_methods[cmdpath] = vcalls
    vcalls.append((clientIdVer, markParams))
    vcalls.sort(key=lambda x: x[0], reverse=True)
    vers = set()
    for x in vcalls:
        vers.add(x[0])
    if len(vers) != len(vcalls):
        ftlog.debug('ERROR !!! TCP CMD Entry, find same version with double callable !!')
        for x in vcalls:
            ftlog.info('ERROR !!!', x)
        raise Exception('TCP CMD Entry, find same version with double callable !!')
    ftlog.debug('TCP CMD Entry ->cmdpath=', cmdpath, 'clientIdVer=', clientIdVer, 'method=', method)


module_name = 'hall.servers.util.decroation_handler'
old_mod = sys.modules.get(module_name)
ftlog.info('old_mod=', old_mod)
if old_mod:
    del sys.modules[module_name]
module = importlib.import_module(module_name)
reload(module)
ftlog.info('new_mod=', module)

ClsHandler = None
exec 'from ' + module_name + ' import DecroationTcpHandler as ClsHandler'
handler = ClsHandler()
gameId = 9999
ftlog.info('handler=', handler)

hmts = decorator._findDecoratorMethod(handler, 'markCmdActionMethod')
for mt in hmts:
    if unRegisterCmdActionMethod(gameId, '', handler, mt[0], mt[1]):
        __registerCmdActionMethod(gameId, '', handler, mt[0], mt[1])

exec_result['ok'] = 1
