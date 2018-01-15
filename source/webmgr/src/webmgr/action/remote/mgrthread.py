# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import os
import psutil
from webmgr.action import actlog

def action(options):
    '''
    '''
    pkey = os.environ.get('MAINCLS', '')
    actlog.log('pkey->', pkey)
    if not pkey :
        return 0

    for p in psutil.process_iter():
        try:
            cmdline = p.cmdline()
        except:
            continue
        actlog.log('cmdline->', cmdline)
        if pkey in cmdline :
            try:
                p.kill()
            except Exception, e:
                actlog.log(e)
    return 1

