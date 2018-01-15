# -*- coding: utf-8 -*-
'''
Created on 2015年12月4日

@author: zqh

部分配置文件控制， 每个可重复的进程动态修改为1个

'''
from webmgr.action.loader.modes import mode1


def get_max_ag_count(machinedict):
    return len(machinedict.keys()) * 2


def make_process_list(options, machinedict, gameids):
    processlist, machinedict = mode1.make_process_list(options, machinedict, gameids)
    if not processlist :
        return processlist, machinedict
    for _, v in processlist.items() :
        if v.get('count', 0) > 0 :
            v['count'] = 1
    return processlist, machinedict
