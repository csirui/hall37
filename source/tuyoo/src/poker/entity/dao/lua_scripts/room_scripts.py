# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
from poker.entity.dao.lua_scripts.util_scripts import LUA_FUN_TY_TOBMBER

ALIAS_GET_BEST_TABLE_ID_LUA = 'GET_BEST_TABLE_ID_LUA'

GET_BEST_TABLE_ID_LUA = '''
    local datas = redis.call("ZRANGE", KEYS[1], -1, -1, "WITHSCORES")
    redis.call("ZREM", KEYS[1], datas[1])
    return datas
'''

ALIAS_UPDATE_TABLE_SCORE_LUA = 'UPDATE_TABLE_SCORE_LUA'

UPDATE_TABLE_SCORE_LUA = LUA_FUN_TY_TOBMBER + '''
    local tableKey = KEYS[1]
    local tableId = KEYS[2]
    local tableScore = KEYS[3]
    local force = KEYS[4]
    if force then
        return redis.call("ZADD", tableKey, tableScore, tableId)
    else
        local oldScore = redis.call("ZSCORE", tableKey, tableId)
        oldScore = ty_tonumber(oldScore)
        if oldScore <= 0 then
            return redis.call("ZADD", tableKey, tableScore, tableId)
        else
            return oldScore
        end
    end
'''
