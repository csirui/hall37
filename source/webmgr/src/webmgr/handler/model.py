# coding: utf-8

'''
'''

__author__ = ['WangTao']

import json
import os

from tyserver.tycmds import runhttp
from tyserver.tycmds.runhttp import markHttpRequestEntry
from tyserver.tyutils import fsutils, strutil, tylog, tyhttp
from tyserver.tyutils.msg import MsgPack
from webmgr.action import actqueue, acthistory
from webmgr.action.debugs import redisdata
from webmgr.handler import getResourcePath
from webmgr.action.remote import hotfix


def get_incidence():
    data = {"test": 'get done!'}
    tylog.info('model.get_incidence->', data)
    return data

def set_incidence(data):
    tylog.info('model.set_incidence->', data)


models = {
        'game/incidence.json': {'get': get_incidence, 'set': set_incidence},
        }  # key: http path; value: func