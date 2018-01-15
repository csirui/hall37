# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
from tyserver.tyutils import tylog, fsutils
from tyserver.tycmds import runhttp
from webmgr.handler.actions import ActionHandler
from webmgr.handler.game.texas.actions import TexasActionHandler
from webmgr.handler.game.t3card.actions import T3cardActionHandler
from webmgr.handler.game.t3flush.actions import T3flushActionHandler
from webmgr.action import actqueue
from webmgr.handler.game.dizhu.actions import DizhuActionHandler

from webmgr.handler.config_actions import BaseActionEntry as ConfigActionEntry


options = None

def initialize(options_):
    global options
    options = options_
    tylog.info('==== initialize begin ====')
    runhttp.addWebRoot(fsutils.appendPath(options.workpath, 'webroot'))
    runhttp.addHandler(ActionHandler(options))
    runhttp.addHandler(TexasActionHandler(options))
    runhttp.addHandler(T3cardActionHandler(options))
    runhttp.addHandler(T3flushActionHandler(options))
    runhttp.addHandler(DizhuActionHandler(options))
    runhttp.addHandler(ConfigActionEntry(options))
    tylog.info('==== initialize end ====')


def heartbeat(hc):
#     tylog.info('==== heartbeat begin ====')
    actqueue.trigger_action(options)
#     tylog.info('==== heartbeat end ====')

