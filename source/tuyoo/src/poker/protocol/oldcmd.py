# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import freetime.util.log as ftlog
from poker.entity.configure import pokerconf
from poker.util import strutil

_oldcmd_target_map = {}
_oldcmd_convert_map = {}


def _initialize():
    '''
    初始化命令路由
    '''
    ftlog.debug('oldcmd._initialize begin')
    oldcmds = pokerconf.getOldCmds()
    for cmdpath, info in oldcmds.items():
        _oldcmd_target_map[cmdpath.split('#')[0]] = strutil.cloneData(info)
        info['cmdpath'] = info['cmd'] + '#' + info['act']
        if cmdpath.find('#') > 0:
            _oldcmd_convert_map[cmdpath] = info
        else:
            _oldcmd_convert_map[cmdpath + '#'] = info
    ftlog.debug('oldcmd._initialize end')


def findTargetInfo(cmd):
    return _oldcmd_target_map.get(cmd)


def convertCmdPath(cmd, action, msg):
    cmdpath = str(cmd) + '#' + str(action)
    cmdinfo = _oldcmd_convert_map.get(cmdpath)
    if cmdinfo:
        msg.setCmd(cmdinfo['cmd'])
        msg.setParam('action', cmdinfo['act'])
        return cmdinfo['cmdpath'], cmdinfo['cmd'], cmdinfo['act']
    return cmdpath, cmd, action
