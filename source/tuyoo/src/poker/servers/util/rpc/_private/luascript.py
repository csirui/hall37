# -*- coding=utf-8 -*-
'''
Created on 2015-12-2
@author: zqh
'''

import freetime.util.log as ftlog
from poker.entity.dao import daobase
from poker.servers.util.rpc._private import dataswap_scripts, user_scripts


def _initialize():
    '''
    初始化当前模块的业务逻辑，此方法被动态收集并调用，无需显示调用此方法
    '''
    ftlog.debug('_initialize begin->', __name__)
    daobase.preLoadLuaScript(dataswap_scripts, dataswap_scripts.CHECK_USER_DATA_LUA_SCRIPT)
    daobase.preLoadLuaScript(dataswap_scripts, dataswap_scripts.DATA_SWAP_LUA_SCRIPT)
    daobase.preLoadLuaScript(user_scripts, user_scripts.MAIN_INCR_CHIP_LUA_SCRIPT)
    daobase.preLoadLuaScript(user_scripts, user_scripts.MAIN_MOVE_CHIP_TO_TABLE_LUA_SCRIPT)
    daobase.preLoadLuaScript(user_scripts, user_scripts.MAIN_SET_HASH_DATA_FORCE)
    ftlog.debug('_initialize finis->', __name__)
