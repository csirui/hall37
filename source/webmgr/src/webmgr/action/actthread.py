# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import threading
from optparse import Values

from datetime import datetime

from tyserver.tyutils import fsutils
from webmgr.action import acthistory
from webmgr.action import actlog
from webmgr.action.loader import load_poker
from webmgr.action.loader import load_service, load_project, update_config
from webmgr.action.make import copy_source, copy_webroot, make_compile, \
    make_control, make_clean
from webmgr.action.remote import push_bin, push_webroot, start, svnup, svnupConfig, \
    mgrthread, removelogs, stopall, notify_config_change, push_static, \
    config_status

actlistcond = threading.Condition()


def thread_run_action(options, action):
    try:
        action['stime'] = datetime.now().strftime('%Y%m%d_%H%M%S')
        actlog.open_act_log(options, action)
        acthistory.save_action_history(options, action)
        actlog.log('START ACTION', action)
        thread_do_action(options, action)
        action['result'] = 'Ok'
    except:
        actlog.error()
        action['result'] = 'Exception'
    finally:
        actlog.close_act_log()

    action['etime'] = datetime.now().strftime('%Y%m%d_%H%M%S')
    acthistory.save_action_history(options, action)


def thread_do_action(options_, action):
    options = Values()
    setattr(options, 'poker_path', options_.pokerpath)
    setattr(options, 'pokerfile', fsutils.appendPath(options_.pokerpath, 'poker/global.json'))

    params = action['params']
    actname = action['action']

    if actname == 'config_check':
        thread_do_action_config(options, params)
        return

    if actname == 'config_reload':
        ret = thread_do_action_config(options, params)
        if ret:
            update_config.action(options)
        return

    if actname == 'config_update':
        setattr(options, 'reset', params.get('reset', 0))
        ret = thread_do_action_config(options, params)
        if ret:
            ret = update_config.action(options)
            if options.push_static:
                push_static.action(options)
            if ret:
                notify_config_change.action(options, params.get('keys', []))
        return

    if actname in ('config_compile_start', 'prepare'):
        ret = thread_do_action_config(options, params)
        if ret:
            if not update_config.action(options):
                return
    else:
        if not thread_do_action_config_base(options, params):
            return

    processids = params.get('processids', [])
    setattr(options, 'processids', processids)

    if actname == 'config_status':
        config_status.action(options)
        return

    if actname == 'config_process':
        pass

    if actname == 'compile_source':
        if not copy_source.action(options):
            return
        if not copy_webroot.action(options):
            return
        if not make_compile.action(options):
            return
        if not make_control.action(options):
            return
        return

    if actname == 'prepare':
        if not make_clean.action(options):
            return
        if not copy_source.action(options):
            return
        if not copy_webroot.action(options):
            return
        if not make_compile.action(options):
            return
        if not make_control.action(options):
            return
        if not push_webroot.action(options):
            return
        return

    if actname == 'config_compile_start':
        if not make_clean.action(options):
            return
        if not copy_source.action(options):
            return
        if not copy_webroot.action(options):
            return
        if not make_compile.action(options):
            return
        if not make_control.action(options):
            return
        if not push_bin.action(options):
            return
        if not stopall.action(options):
            return
        if not start.action(options):
            return
        if not push_webroot.action(options):
            return
        return

    if actname == 'reset':
        if not start.action(options):
            return
        return

    if actname == 'push_bin':
        if not push_bin.action(options):
            return
        return

    if actname == 'push_web':
        if not push_webroot.action(options):
            return
        return

    if actname == 'push_source':
        if not push_bin.action(options):
            return
        if not push_webroot.action(options):
            return
        return

    if actname == 'stop_all_process':
        if not stopall.action(options):
            return
        return

    if actname == 'svn_update_all':
        if not svnup.action(options, params):
            return
        return

    if actname == 'svn_update_config':
        if not svnupConfig.action(options, params):
            return
        return

    if actname == 'restart_mgr_thread':
        if not mgrthread.action(options):
            return
        return

    if actname == 'remove_all_logs':
        if not removelogs.action(options):
            return
        return


def thread_do_action_config(options, params):
    ret = load_poker.action(options)
    if not ret:
        return ret

    load_service.action(options)

    allpkgs = options.pokerdict['conf.projects']
    setattr(options, 'checkprojects', allpkgs)
    ret = load_project.action(options)
    if not ret:
        return ret
    return 1


def thread_do_action_config_base(options, params):
    ret = load_poker.action(options)
    if not ret:
        return ret
    return load_service.action(options)
