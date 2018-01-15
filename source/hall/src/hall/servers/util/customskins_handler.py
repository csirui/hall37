# -*- coding=utf-8
'''
Created on 2015年8月14日

@author: zhaojiangang
'''
import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack
from hall.entity.hallcustomskins import getConf
from hall.servers.common.base_checker import BaseMsgPackChecker
from poker.protocol import router
from poker.protocol.decorator import markCmdActionHandler, markCmdActionMethod


@markCmdActionHandler
class ActivityTcpHandler(BaseMsgPackChecker):
    def __init__(self):
        pass

    @markCmdActionMethod(cmd='game', action='custom_skins', clientIdVer=0)
    def doCustomSkinsUpdate(self, gameId, userId, clientId):
        try:
            mo = MsgPack()
            mo.setCmd('game')
            mo.setResult('action', 'custom_skins')
            conf = getConf(userId, gameId, clientId)
            mo.setResult('conf', conf)
            ftlog.info('doCustomSkinsUpdate userId =', userId
                       , 'gameId =', gameId
                       , 'clientId =', clientId
                       , 'conf =', conf)
            router.sendToUser(mo, userId)
        except:
            mo = MsgPack()
            mo.setCmd('game')
            mo.setResult('action', 'custom_skins')
            mo.setResult('error', 'doCustomSkinsUpdate error')
            router.sendToUser(mo, userId)
            ftlog.error()
