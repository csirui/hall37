# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import threading

from tyserver.tyutils import fsutils
import os


actlistcond = threading.Condition()


def save_action_history(options, action):
    actlistcond.acquire()
    try:
        fpath = fsutils.appendPath(options.logpath, 'action.' + action['uuid'] + '.json')
        fsutils.writeFile('', fpath, action)
    finally:
        actlistcond.release()


def get_action_list(options) :
    fpath = options.logpath
    lfs = os.listdir(fpath)
    actlist = []
    for lf in lfs :
        if lf.startswith('action.') and lf.endswith('.json') :
            af = fsutils.appendPath(fpath, lf)
            action = fsutils.readJsonFile(af)
            actlist.append(action)
    actlist.sort(key=lambda x : x['uuid'])
    
    while len(actlist) > 10 :
        remove_action(options, [actlist[0]['uuid']])
        del actlist[0]

    return actlist


def remove_action(options, uuids) :
    fpath = options.logpath
    for uuid in uuids :
        fpath = fsutils.appendPath(options.logpath, 'action.' + uuid + '.json')
        fsutils.deleteFile(fpath)
        fpath = fsutils.appendPath(options.logpath, 'action.' + uuid + '.log')
        fsutils.deleteFile(fpath)


def get_action_log(options, action_uuid, line_num):
    logpath = options.logpath
    fpath = fsutils.appendPath(logpath, 'action.' + action_uuid + '.log')
    lines = [] 
    if fsutils.fileExists(fpath) :
        f = None
        try:
            f = open(fpath)
            if line_num > 0 :
                for _ in xrange(line_num) :
                    f.readline()
            l = f.readline() 
            while l :
                lines.append(l.strip())
                l = f.readline()
        finally:
            try:
                f.close()
            except:
                pass
    else:
        lines.append('the log file is missing !!')
        lines.append(fpath)
    return lines

