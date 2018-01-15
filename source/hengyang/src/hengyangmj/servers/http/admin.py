# -*- coding:utf-8 -*-

from freetime.entity.msg import MsgPack
from freetime.util import log as ftlog
from hall.servers.common.base_http_checker import BaseHttpMsgChecker
from poker.protocol import router, runhttp
from poker.protocol.decorator import markHttpHandler, markHttpMethod


@markHttpHandler
class MJAdmin(BaseHttpMsgChecker):
    def __init__(self):
        super(MJAdmin, self).__init__()

    def _check_param_roomId(self, key, params):
        roomId = runhttp.getParamInt(key, -1)
        if isinstance(roomId, int) and roomId >= 0:
            return None, roomId
        return None, 0

    def _check_param_tableId(self, key, params):
        tableId = runhttp.getParamInt(key, -1)
        if isinstance(tableId, int) and tableId >= 0:
            return None, tableId
        return None, 0

    @markHttpMethod(httppath='/hengyangmj/clear_table')
    def clearTable(self, roomId, tableId):
        ftlog.debug('MJAdmin.clearTable roomId:', roomId, ' tableId:', tableId)

        mo = MsgPack()
        mo.setCmd('table_manage')
        mo.setAction('clear_table')
        mo.setParam('roomId', roomId)
        mo.setParam('tableId', tableId)
        router.sendTableServer(mo, roomId)
        return {'info': 'ok', 'code': 0}

    @markHttpMethod(httppath='/hengyangmj/kick_user')
    def kickUser(self, userId, roomId, tableId):
        ftlog.debug('MJAdmin.kickUser roomId:', roomId, ' tableId:', tableId, ' userId:', userId)

        mo = MsgPack()
        mo.setCmd('table_manage')
        mo.setAction('leave')
        mo.setParam('roomId', roomId)
        mo.setParam('tableId', tableId)
        mo.setParam('userId', userId)
        router.sendTableServer(mo, roomId)
        return {'info': 'ok', 'code': 0}

    @markHttpMethod(httppath='/hengyangmj/check_table_tiles')
    def checkTableTiles(self, roomId, tableId):
        ftlog.debug('MJAdmin.checkTableTiles roomId:', roomId, ' tableId:', tableId)

        mo = MsgPack()
        mo.setCmd('table_manage')
        mo.setAction('tableTiles')
        mo.setParam('roomId', roomId)
        mo.setParam('tableId', tableId)
        router.sendTableServer(mo, roomId)
        return {'info': 'ok', 'code': 0}
