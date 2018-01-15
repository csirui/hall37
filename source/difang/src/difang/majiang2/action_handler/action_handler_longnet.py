# -*- coding=utf-8
'''
Created on 2016年9月23日
上行行为处理

@author: zhaol
'''
from difang.majiang2.action_handler.action_handler import ActionHandler
from difang.majiang2.player.player import MPlayerTileGang
from difang.majiang2.table_state.state import MTableState
from freetime.util import log as ftlog


class ActionHandlerLongNet(ActionHandler):
    def __init__(self):
        super(ActionHandlerLongNet, self).__init__()

    def processAction(self, cmd):
        """处理玩家行为
        在本例里为上行的长连接消息
        """
        pass

    def getActionIdFromMessage(self, message):
        """
        从消息中获取action_id
        """
        return message.getParam('action_id')

    def handleTableCallGrabTing(self, userId, seatId, message):
        """处理抢听消息
        
        1）抢听 吃
        {
            "cmd": "table_call",
            "params": {
                "gameId": 7,
                "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
                "userId": 10788,
                "roomId": 75041001,
                "tableId": 750410010199,
                "seatId": 0,
                "action": "grabTing",
                "action_id": 1,
                "chi": 17,
                "pattern": [16, 17, 18]
            }
        }
        
        2）抢听 碰
        {
            "cmd": "table_call",
            "params": {
                "gameId": 7,
                "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
                "userId": 10788,
                "roomId": 75041001,
                "tableId": 750410010200,
                "seatId": 0,
                "action": "grabTing",
                "action_id": 11,
                "peng": 4,
                "pattern": [4, 4, 4]
            }
        }
        
        3）抢听 杠
        {
            "cmd": "table_call",
            "params": {
                "gameId": 7,
                "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
                "userId": 10788,
                "roomId": 75041001,
                "tableId": 750410010200,
                "seatId": 0,
                "action": "grabTing",
                "action_id": 11,
                "gang": 4,
                "pattern": [4, 4, 4, 4],
                "special_tile": 23
            }
        }
        
        4）抢听 粘
        {
            "cmd": "table_call",
            "params": {
                "gameId": 7,
                "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
                "userId": 10788,
                "roomId": 75041001,
                "tableId": 750410010200,
                "seatId": 0,
                "action": "grabTing",
                "action_id": 11,
                "zhan": 4,
                "pattern": [4, 4],
                "special_tile": 23
            }
        }
        
        """
        ftlog.debug('handleTableCallGrabTing message:', message)
        actionId = self.getActionIdFromMessage(message)
        if actionId == self.table.actionID:
            tile = message.getParam('tile', None)

            chi = message.getParam('chi', None)
            if chi:
                self.table.chiTile(seatId
                                   , tile
                                   , chi
                                   , MTableState.TABLE_STATE_CHI | MTableState.TABLE_STATE_GRABTING)

            peng = message.getParam('peng', None)
            if peng:
                self.table.pengTile(seatId
                                    , tile
                                    , peng
                                    , MTableState.TABLE_STATE_PENG | MTableState.TABLE_STATE_GRABTING)

            gang = message.getParam('gang', None)
            if gang:
                gangPattern = gang.get('pattern')
                gangPattern.sort()
                style = gang.get('style')
                tile = gang.get('tile')
                special_tile = gang.get('special_tile', None)
                self.table.gangTile(seatId
                                    , tile
                                    , gangPattern
                                    , style
                                    , MTableState.TABLE_STATE_GANG | MTableState.TABLE_STATE_GRABTING
                                    , special_tile)

            zhan = message.getParam('zhan', None)
            if zhan:
                zhanPattern = zhan.get('pattern')
                tile = zhan.get('tile')
                special_tile = zhan.get('special_tile', None)
                self.table.zhanTile(seatId
                                    , tile
                                    , zhanPattern
                                    , MTableState.TABLE_STATE_ZHAN | MTableState.TABLE_STATE_GRABTING
                                    , special_tile)
        else:
            ftlog.info('wrong actionId:', actionId, ' now table actionId:', self.table.actionID, ' message:', message)

    def handleTableCallGrabHuGang(self, userId, seatId, message):
        """处理抢杠胡"""
        actionId = self.getActionIdFromMessage(message)
        if actionId == self.table.actionID:
            winTile = message.getParam('tile', None)
            if winTile:
                self.table.grabHuGang(seatId, winTile)
            else:
                ftlog.error("handleTableCallGrabHuGang winTile is None")

    def handleTableCallpass(self, userId, seatId, message):
        """处理过消息
        {
            "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
            "cmd": "       table_call",
            "params": {
                "gameId": 7,
                "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
                "userId": 10788,
                "roomId": 75041001,
                "tableId": 750410010200,
                "seatId": 0,
                "action": "pass",
                "action_id": 15
            }
        }
        """
        actionId = self.getActionIdFromMessage(message)
        if actionId == self.table.actionID:
            self.table.playerCancel(seatId)
        else:
            ftlog.info('wrong actionId:', actionId, ' now table actionId:', self.table.actionID, ' message:', message)

    def handleTableCallChi(self, userId, seatId, message):
        """处理吃消息
        {
            "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
            "cmd": "table_call",
            "params": {
                "gameId": 7,
                "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
                "userId": 10788,
                "roomId": 75041001,
                "tableId": 750410010200,
                "seatId": 0,
                "action": "chi",
                "action_id": 34,
                "tile": 19,
                "pattern": [17, 18, 19]
            }
        }
        """
        actionId = self.getActionIdFromMessage(message)
        if actionId == self.table.actionID:
            chi = message.getParam('tile')
            chiResult = message.getParam('pattern', None)
            if not chiResult:
                ftlog.error('handleTableCallChi pattern is None')
            self.table.chiTile(seatId, chi, chiResult, MTableState.TABLE_STATE_CHI)
        else:
            ftlog.info('wrong actionId:', actionId, ' now table actionId:', self.table.actionID, ' message:', message)

    def handleTableCallPeng(self, userId, seatId, message):
        """处理碰牌消息
        {
            "cmd": "table_call",
            "params": {
                "gameId": 7,
                "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
                "userId": 10788,
                "roomId": 75041001,
                "tableId": 750410010200,
                "seatId": 0,
                "action": "peng",
                "action_id": 0,
                "tile": 7,
                "pattern": [7, 7, 7]
            }
        }
        """
        actionId = self.getActionIdFromMessage(message)
        if actionId == self.table.actionID:
            tile = message.getParam('tile')
            pattern = message.getParam('pattern', None)
            pattern.sort()
            self.table.pengTile(seatId, tile, pattern, MTableState.TABLE_STATE_PENG)
        else:
            ftlog.info('wrong actionId:', actionId, ' now table actionId:', self.table.actionID, ' message:', message)

    def handleTableCallGang(self, userId, seatId, message):
        """处理杠牌消息
        {
            "cmd": "table_call",
            "params": {
                "gameId": 7,
                "clientId": "Android_3.776_weixin,tyGuest.alipay.0-hall7.youle.scmj",
                "userId": 10003,
                "roomId": 78051001,
                "tableId": 780510010200,
                "seatId": 0,
                "action": "gang",
                "action_id": 0,
                "gang": {
                    "tile": 1,
                    "pattern": [1, 1, 1, 1],
                    "style": 1
                }
            }
        }
        """
        actionId = self.getActionIdFromMessage(message)
        if actionId == self.table.actionID:
            _tile = message.getParam('tile', None)
            gang = message.getParam('gang', None)
            if not gang:
                ftlog.error('wrong message gang...')
                return

            tile = gang.get('tile', _tile)
            gangPattern = gang.get('pattern')
            gangPattern.sort()
            style = gang.get('style')

            if style == MPlayerTileGang.MING_GANG and not tile:
                ftlog.error('handleTableCallGang error tile:', tile, ' gang:', gang)
                return

            special_tile = gang.get('special_tile', None)
            self.table.gangTile(seatId, tile, gangPattern, style, MTableState.TABLE_STATE_GANG, special_tile)
        else:
            ftlog.info('wrong actionId:', actionId, ' now table actionId:', self.table.actionID, ' message:', message)

    def handleTableCallWin(self, userId, seatId, message):
        """处理和牌消息
        {
            "cmd": "table_call",
            "params": {
                "gameId": 7,
                "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
                "userId": 10788,
                "roomId": 75041001,
                "tableId": 750410010200,
                "seatId": 0,
                "action": "win",
                "action_id": 14,
                "tile": 2
            }
        }
        """
        actionId = self.getActionIdFromMessage(message)
        if actionId == self.table.actionID:
            tile = message.getParam('tile')
            self.table.gameWin(seatId, tile)
        else:
            ftlog.info('wrong actionId:', actionId, ' now table actionId:', self.table.actionID, ' message:', message)

    def handleTableCallPlay(self, userId, seatId, message):
        """
        处理出牌消息
        message: {
            "cmd": "table_call",
            "params": {
                "gameId": 7,
                "clientId": "Android_3.90_360.360,yisdkpay.0-hall6.360.win",
                "userId": 10788,
                "roomId": 75041001,
                "tableId": 750410010200,
                "seatId": 0,
                "action": "play",
                "action_id": 11,
                "tile": 12,
                "ting": 1
            }
        }
        """
        actionId = self.getActionIdFromMessage(message)
        if actionId == self.table.actionID:
            tile = message.getParam('tile')
            if not tile:
                ftlog.error('handleTableCallPlay message error, no valid tile...')
                return

            isTing = message.getParam('ting', 0)
            # 自己摸牌，状态是听
            if (isTing == 1) and (self.table.addCardProcessor.getState() & MTableState.TABLE_STATE_TING):
                exInfo = self.table.addCardProcessor.extendInfo
                ftlog.debug('handleTableCallPlay exInfo.extend:', exInfo.extend)
                self.table.ting(seatId, tile, exInfo)
            else:
                if self.table.qiangGangHuProcessor.getState() == 0:
                    self.table.playerCancel(seatId)
                    self.table.dropTile(seatId, tile)
        else:
            ftlog.info('wrong actionId:', actionId, ' now table actionId:', self.table.actionID, ' message:', message)

    def handleTableCallPing(self, userId, seatId, message):
        """
        处理客户端请求网速
        """
        #         actionId = self.getActionIdFromMessage(message)
        #         if actionId == self.table.actionID:
        #        ftlog.debug('handleTableCallPing message:', message)
        timeStamp = message.getParam('time', 0)
        delta = message.getParam('ping', 0)
        self.table.sendNetStateToUser(userId, seatId, timeStamp, delta)

    #         else:
    #             ftlog.info('wrong actionId:', actionId, ' now table actionId:', self.table.actionID, ' message:', message)

    def handleTableCallExchange(self, userId, seatId, message):
        """
        换牌动作
        """
        if self.table.dropCardProcessor.getState() != 0 or self.table.qiangGangHuProcessor.getState() != 0:
            return
        pengInfo = message.getParam('peng', [])
        gangInfo = message.getParam('gang', {})
        # 换的是碰牌中的癞子
        if pengInfo and len(pengInfo) > 0:
            pengInfo.sort()
            self.table.exchangeMagicTilePeng(userId, pengInfo)
        else:
            if gangInfo and gangInfo.has_key('style'):
                gangInfo['pattern'].sort()
                self.table.exchangeMagicTileGang(userId, gangInfo)
            else:
                ftlog.info('handleTableCallExchange error neither peng nor gang info in message')
