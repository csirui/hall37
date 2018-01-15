# -*- coding: utf-8 -*-
'''
Created on 2015年5月20日

@author: zqh
'''

import freetime.util.log as ftlog
from poker.entity.configure import gdata
from poker.protocol import router
from poker.protocol.rpccore import markRpcCall


def forceLogOut(userId, logoutmsg):
    if gdata.ENABLIE_DEFENCE_2:
        return forceLogOut3(userId, logoutmsg)
    assert (isinstance(userId, int))
    assert (userId > 0)
    assert (isinstance(logoutmsg, (str, unicode)))
    return _forceLogOut(userId, logoutmsg)


@markRpcCall(groupName="userId", lockName="userId", syncCall=0)
def _forceLogOut(userId, logoutmsg):
    '''
    强制某一个用户推出TCP登录
    '''
    from poker.protocol.conn import protocols
    ret = protocols.forceUserLogOut(userId, logoutmsg)
    ftlog.info('doConnLogOut->', userId, 'result=', ret)
    return ret


def notifyUsers(message, userIds=[]):
    '''
    通知所有在线用户, 
    strMessage 字符串，为需要发送的消息
    '''
    assert (isinstance(message, (str, unicode)))
    if userIds != None:
        assert (isinstance(userIds, (list, tuple)))
    count = 0
    colen = router._connServer.sidlen
    for x in xrange(colen):
        res = _notifyUsers(x, message, userIds)
        if isinstance(res, (int, long)):
            count += res
    return count


@markRpcCall(groupName="intServerId", lockName="intServerId", syncCall=0)
def _notifyUsers(intServerId, message, userIds):
    from poker.protocol.conn import protocols
    return protocols.sendCarryMessage(message, userIds)


def forceLogOut2(userId, connId, logoutmsg):
    ftlog.info('forceLogOut2->', userId, connId, logoutmsg)
    if connId:
        assert (isinstance(userId, int))
        assert (userId > 0)
        assert (isinstance(logoutmsg, (str, unicode)))
        colen = router._connServer.sidlen
        for x in xrange(colen):
            if router._connServer.sids[x] == connId:
                ftlog.info('forceLogOut2 go->', userId, connId, logoutmsg)
                _forceLogOut2(x, userId, logoutmsg)


def forceLogOut3(userId, logoutmsg):
    ftlog.info('forceLogOut3->', userId, logoutmsg)
    assert (isinstance(userId, int))
    assert (userId > 0)
    assert (isinstance(logoutmsg, (str, unicode)))
    colen = router._connServer.sidlen
    from poker.entity.dao import sessiondata
    connId = sessiondata.getConnId(userId)
    if connId:
        for x in xrange(colen):
            if router._connServer.sids[x] == connId:
                ftlog.info('forceLogOut3->', userId, connId, logoutmsg)
                _forceLogOut2(x, userId, logoutmsg)


@markRpcCall(groupName="intServerId", lockName="intServerId", syncCall=0)
def _forceLogOut2(intServerId, userId, logoutmsg):
    '''
    强制某一个用户推出TCP登录
    '''
    return _forceLogOut2_(intServerId, userId, logoutmsg)


def _forceLogOut2_(intServerId, userId, logoutmsg):
    '''
    强制某一个用户推出TCP登录
    '''
    from poker.protocol.conn import protocols
    ret = protocols.forceUserLogOut(userId, logoutmsg)
    ftlog.info('doConnLogOut->', userId, intServerId, logoutmsg, 'result=', ret)
    return ret
