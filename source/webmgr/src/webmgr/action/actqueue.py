# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import threading

import stackless
from datetime import datetime
from twisted.internet.threads import deferToThread

from tyserver.tyutils import tylog
from webmgr.action.actthread import thread_run_action

actnum = 0
actionlist = []
actionlistcond = threading.Condition()


def add_action(action_name, params, username):
    tylog.info('add_action->', action_name, params, username)
    actionlistcond.acquire()
    try:
        global actnum
        actnum += 1
        if actnum > 9999:
            actnum = 1
        atime = datetime.now().strftime('%Y%m%d_%H%M%S')
        uuid = atime + '_%04d' % (actnum)
        act = {'action': action_name, 'params': params, 'uuid': uuid, 'time': atime, 'user': username}
        actionlist.append(act)
        return act
    finally:
        actionlistcond.release()


def pop_action():
    actionlistcond.acquire()
    try:
        #         tylog.info('pop_action->', len(actionlist))
        if actionlist:
            action = actionlist.pop(0)
            return action
    finally:
        actionlistcond.release()


def get_actions():
    actionlistcond.acquire()
    try:
        return actionlist[:]
    finally:
        actionlistcond.release()


def remove_actions(actuuidlist):
    actionlistcond.acquire()
    try:
        for x in xrange(len(actionlist) - 1, -1, -1):
            act = actionlist[x]
            if act['uuid'] in actuuidlist:
                del actionlist[x]
    finally:
        actionlistcond.release()


def trigger_action(options):
    action = pop_action()
    #     tylog.info('trigger_action->', json.dumps(action))
    if action:
        d = deferToThread(thread_run_action, options, action)
        fttask = stackless.getcurrent()._fttask
        result = fttask.waitDefer(d)
        #         tylog.info('trigger_action result->', result)
        return result
