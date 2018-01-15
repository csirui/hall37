# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from poker.entity.dao import daoconst
from poker.entity.dao.daoconst import UserDataSchema
from poker.servers.util.direct import dbuser


def checkUserData(userId, clientId=None, appId=0, session={}):
    '''
    检查给出的用userId数据是否存在，
    如果在冷数据中则进行导入,
    当用户进行登录时,调用此方法, 因此再此方法中建立该用户的session数据缓冲
    数据缓冲由dbuser层进行处理,即在UT进程中进程缓冲
    '''
    assert (isinstance(userId, int))
    assert (userId > 0)
    assert (isinstance(appId, int))
    assert (appId >= 0)
    if clientId != None:
        assert (isinstance(clientId, (str, unicode)))
    ret = dbuser._checkUserData(userId, clientId, appId, session)
    return ret


def updateUserDataAuthorTime(userId):
    '''
    更新用户的认证时间
    '''
    assert (isinstance(userId, int))
    assert (userId > 0)
    return dbuser._updateUserDataAuthorTime(userId)


def updateUserDataAliveTime(userId):
    '''
    更新用户的CONN链接活动时间
    '''
    assert (isinstance(userId, int))
    assert (userId > 0)
    return dbuser._updateUserDataAliveTime(userId)


def updateUserGameDataAuthorTime(userId, gameId):
    '''
    更新用户的BINDGAME活动时间
    '''
    assert (isinstance(userId, int))
    assert (userId > 0)
    assert (isinstance(gameId, int))
    assert (gameId > 0)
    return dbuser._updateUserGameDataAuthorTime(userId, gameId)


def getSessionData(userId):
    '''
    取得用户的session数据
    '''
    assert (isinstance(userId, int))
    assert (userId > 0)
    return dbuser._getSessionDatas(userId)


def setSessionData(userId, session):
    '''
    设置用户的session数据
    '''
    if session:
        assert (isinstance(userId, int))
        assert (userId > 0)
        assert (isinstance(session, dict))
        return dbuser._setSessionDatas(userId, session)


def clearUserCache(userId):
    '''
    其他外部系统,例如SDK改变用户数据时, 通知本系统进行缓存的清理, 重新加载用户数据
    '''
    dbuser._clearUserCache(userId)
    return 1


def getAttrs(userId, filedList):
    '''
    取得用户的主账户数据
    '''
    assert (isinstance(userId, int))
    assert (userId > 0)
    return dbuser._getUserDatas(userId, filedList)


def setAttrs(userId, datas):
    '''
    设置用户的主账户数据
    '''
    if datas:
        assert (isinstance(userId, int))
        assert (userId > 0)
        assert (isinstance(datas, dict))
        return dbuser._setUserDatas(userId, datas)


def setnxAttr(userId, filed, value):
    assert (isinstance(userId, int))
    assert (userId > 0)
    return dbuser._setUserDatasNx(userId, {filed: value})


def _setAttrsForce(userId, datas):
    '''
    强制设置用户属性列表, 此方法由框架内部调用, 其他代码不允许调用
    '''
    if datas:
        assert (isinstance(userId, int))
        assert (userId > 0)
        assert (isinstance(datas, dict))
        return dbuser._setUserDatasForce(userId, datas)


def delAttr(userId, field):
    '''
    设置用户属性
    '''
    assert (isinstance(userId, int))
    assert (userId > 0)
    assert (field in UserDataSchema.FIELDS_ALL_SET)
    return dbuser._delUserDatas(userId, {field: None})


def incrAttr(userId, field, value):
    '''
    INCR用户属性
    '''
    assert (isinstance(userId, int))
    assert (userId > 0)
    assert (field in UserDataSchema.FIELDS_ALL_SET)
    assert (isinstance(value, int))
    return dbuser._incrUserDatas(userId, field, value)


def incrAttrLimit(userId, field, deltaCount, lowLimit, highLimit, chipNotEnoughOpMode):
    '''
    INCR用户属性
    参考: incr_chip_limit
    '''
    assert (isinstance(userId, int))
    assert (userId > 0)
    assert (field in UserDataSchema.FIELDS_ALL_SET)
    assert (isinstance(deltaCount, int))
    assert (chipNotEnoughOpMode == daoconst.CHIP_NOT_ENOUGH_OP_MODE_CLEAR_ZERO
            or chipNotEnoughOpMode == daoconst.CHIP_NOT_ENOUGH_OP_MODE_NONE)
    trueDetal, finalCount, fixCount, _, _ = dbuser._incrUserDatasLimit(userId, field, deltaCount, lowLimit,
                                                                       highLimit, chipNotEnoughOpMode)
    return trueDetal, finalCount, fixCount


def getAttr(userId, field):
    '''
    获取用户属性值
    '''
    vals = getAttrs(userId, [field])
    return vals[0]


def getAttrInt(userId, field):
    '''
    获取用户属性值
    '''
    vals = getAttrs(userId, [field])
    return int(vals[0])


def setAttr(userId, field, value):
    '''
    设置用户属性
    '''
    return setAttrs(userId, {field: value})


def getExp(uid):
    '''
    取得用户的经验值
    '''
    return getAttr(uid, UserDataSchema.EXP)


def incrExp(userId, detalExp):
    '''
    调整用户的经验值
    '''
    _, finalCount, _ = incrAttrLimit(userId, UserDataSchema.EXP, detalExp, 0, -1,
                                     daoconst.CHIP_NOT_ENOUGH_OP_MODE_CLEAR_ZERO)
    return finalCount


def getCharm(uid):
    '''
    取得用户的魅力值
    '''
    return getAttr(uid, UserDataSchema.CHARM)


def incrCharm(userId, detalCharm):
    '''
    调整用户的魅力值
    '''
    _, finalCount, _ = incrAttrLimit(userId, UserDataSchema.CHARM, detalCharm, 0, -1,
                                     daoconst.CHIP_NOT_ENOUGH_OP_MODE_CLEAR_ZERO)
    return finalCount
