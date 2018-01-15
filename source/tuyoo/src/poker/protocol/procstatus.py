# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import fcntl
import json
import os

import freetime.entity.config as ftcon
import freetime.util.log as ftlog
from freetime.style import ide_print
from poker.util import timestamp


def updateStatus(status):
    stfile = None
    try:
        sid = ftcon.global_config["server_id"]
        log_path = ftcon.global_config["log_path"]
        stpath = log_path + '/status.' + sid
        if os.path.isfile(stpath):
            stfile = open(stpath, 'r')
            datas = json.load(stfile)
            stfile.close()
            stfile = None
        else:
            datas = {'creatTime': timestamp.formatTimeMs()}

        _updateProcessStatus(datas)

        datas['status'] = status
        datas['updateTime'] = timestamp.formatTimeMs()

        ide_print("updateStatus(%s)" % status)

        stfile = open(stpath, 'w')
        fcntl.flock(stfile, fcntl.LOCK_EX)
        stfile.write(json.dumps(datas, sort_keys=True, indent=4, separators=(', ', ' : ')))
        fcntl.flock(stfile, fcntl.LOCK_UN)
        stfile.close()
        stfile = None
    except:
        ftlog.error()
    finally:
        try:
            if stfile:
                fcntl.flock(stfile, fcntl.LOCK_UN)
        except:
            pass
        try:
            if stfile:
                stfile.close()
        except:
            pass


def _updateProcessStatus(datas):
    if 'pid' not in datas:
        datas['pid'] = os.getpid()
        datas['ppid'] = os.getppid()
