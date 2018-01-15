# -*- coding=utf-8
'''
Created on 2015年7月1日

@author: zhaoqh
'''

import freetime.util.log as ftlog
import poker.entity.events.tyeventbus as pkeventbus
from hall.entity import hallconf
from poker.entity.biz import bireport
from poker.entity.dao import userdata, userchip, daoconst
from poker.entity.events.tyevent import EventConfigure

_inited = False
newuser_startchip = 3000


def sendStartChip(userId, gameId, clientId):
    """发放启动资金
    """
    global newuser_startchip

    canGive = False
    startChip = 0
    final = 0
    try:
        count = userdata.delAttr(userId, 'sendMeGift')
        if (count == 1) and (newuser_startchip > 0):
            canGive = True

        if ftlog.is_debug():
            ftlog.debug('hallstartchip.sendStartChip userId=', userId,
                        'gameId=', gameId,
                        'clientId=', clientId,
                        'chip=', startChip,
                        'canGive=', canGive)

        if canGive:
            startChip = newuser_startchip
            _, final = userchip.incrChip(userId, gameId, startChip, daoconst.CHIP_NOT_ENOUGH_OP_MODE_NONE,
                                         'USER_STARTUP', 0, clientId)
            bireport.gcoin('in.chip.newuser.startchip', gameId, startChip)
            ftlog.debug('hallstartchip.sendStartChip userId=', userId,
                        'gameId=', gameId,
                        'clientId=', clientId,
                        'chip=', startChip,
                        'startChip=', startChip,
                        'final=', final)
        return canGive, startChip, final
    except:
        ftlog.error()

    return False, 0, 0


def needSendStartChip(userId, gameId):
    '''是否发放启动资金
    '''
    global newuser_startchip

    return (1 == userdata.getAttr(userId, 'sendMeGift')) and (newuser_startchip > 0)


def _reloadConf():
    global newuser_startchip
    conf = hallconf.getHallPublic()
    newuser_startchip = conf['newuser_startchip']


def _onConfChanged(event):
    if _inited and event.isChanged('game:9999:public:0'):
        ftlog.debug('startChip._onConfChanged')
        _reloadConf()


def _initialize():
    ftlog.debug('NewUserStartChip initialize begin')
    global _inited
    if not _inited:
        _inited = True
        _reloadConf()
        pkeventbus.globalEventBus.subscribe(EventConfigure, _onConfChanged)
    ftlog.debug('NewUserStartChip initialize end')
