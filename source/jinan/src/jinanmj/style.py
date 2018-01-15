#!/usr/bin/env python
# -*- coding:utf-8 -*-
from poker.entity.dao import gamedata

# 暂时使用
__GAME_ID = 711


def SetData(user_id, key, value):
    """
    保存数据到指定用户
    """
    gamedata.setGameAttr(user_id, __GAME_ID, key, value)
    return value


def GetData(user_id, key, defaultValue=None, initWithDefaultValue=True):
    """
    获取指定的用户数据
    """
    ret = gamedata.getGameAttr(user_id, __GAME_ID, key)
    if ret is None:
        if defaultValue is None:
            return None
        else:
            if initWithDefaultValue:
                SetData(user_id, key, defaultValue)
            return defaultValue
    else:
        return ret
