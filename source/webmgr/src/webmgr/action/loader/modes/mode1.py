# -*- coding: utf-8 -*-
'''
Created on 2015年12月4日

@author: zqh

完全配置文件控制

'''
from webmgr.action import actlog
from tyserver.tyutils import fsutils

def get_max_ag_count(machinedict):
    return -1

def make_process_list(options, machinedict, gameids):
    jname = 'poker/process.json'
    jsonfile = fsutils.appendPath(options.poker_path, jname)
    actlog.log('load %-15s :' % (jname), jsonfile)
    processlist = fsutils.readJsonFile(jsonfile, True)
    if not isinstance(processlist, dict) :
        return actlog.error(jname + ' : format error, root object must be dict'), machinedict
    return processlist, machinedict

