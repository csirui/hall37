# -*- coding=utf-8

from poker.entity.dao import daobase


def _setKeyValue(key, val):
    ret = daobase._executeKeyMapCmd('SET', key, val)
    return ret


def _getKeyValue(key):
    ret = daobase._executeKeyMapCmd('GET', key)
    return ret
