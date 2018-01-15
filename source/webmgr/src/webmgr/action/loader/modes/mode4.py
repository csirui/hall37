# -*- coding: utf-8 -*-
'''
Created on 2015年12月4日

@author: zqh

完全忽律配置文件，最小配置

'''
from webmgr.action import actlog
from webmgr.action.loader.modes import mode1


def get_max_ag_count(machinedict):
    return 1


def make_process_list(options, machinedict, gameids):
    processlist, machinedict = mode1.make_process_list(options, machinedict, gameids)
    haspl = 1 if 'PL' in processlist else 0

    actlog.log('Use tiny process config !')
    gs = {}
    for gameId in gameids :
        gs[str(gameId) + '-001-998-1'] = [gameId * 1000 + 1, gameId * 1000 + 999]
    mn = machinedict.keys()[0]
    macs = { mn: machinedict[mn]}
    machinedict = macs
    processlist = {"CO" : { "count" : 1, "machines" : [mn]},
                   "HT" : { "count" : 1, "machines" : [mn]},
                   "RB" : { "count" : 1, "machines" : [mn]},
                   "CT" : { "count" : 1, "machines" : [mn]},
                   "UT" : { "count" : 1, "machines" : [mn]},
                   "GR" : { "count" : 1, "machines" : [mn]},
                   "GT" : { "count" : 1, "machines" : [mn]},
                   "GROUPS" :  gs
                   }
    if haspl :
        processlist['PL'] = { "count" : 1, "machines" : [mn]}

    return processlist, macs
