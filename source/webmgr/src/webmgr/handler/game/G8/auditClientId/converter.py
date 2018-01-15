# coding: utf-8

"""
红包配置转换器
"""

__author__ = ['Wang Tao']

import copy

import webmgr.utils.cfgutil as util


def convert(handler, all_tables={}):
    res = []
    tables = {}

    if not all_tables:
        matcher = lambda name: name.startswith('auditClientId')
        tables = handler.getConn().queryTable(matcher)
    else:
        for name, data in all_tables.items():
            if name.startswith('auditClientId'):
                tables[name] = copy.deepcopy(data)

    # 基本配置
    res['common'] = tables['auditClientId']

    return res