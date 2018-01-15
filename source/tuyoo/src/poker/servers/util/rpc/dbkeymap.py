# -*- coding=utf-8

from poker.entity.dao import daobase
from poker.protocol.rpccore import markRpcCall


@markRpcCall(groupName="", lockName="", syncCall=1)
def _setKeyValue(key, val):
    ret = daobase._executeKeyMapCmd('SET', key, val)
    return ret


@markRpcCall(groupName="", lockName="", syncCall=1)
def _getKeyValue(key):
    ret = daobase._executeKeyMapCmd('GET', key)
    return ret
