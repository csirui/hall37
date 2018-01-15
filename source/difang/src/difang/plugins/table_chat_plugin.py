# coding: UTF-8
'''
牌桌聊天插件
'''

__author__ = ['ZhouHao']

import difang.entity.conf as difangConf
import difang.entity.plugin_event_const as PluginEvent
import freetime.util.log as ftlog
from hall.entity import hallchatlog
from poker.entity.configure import gdata
from poker.util import keywords


class DiFangTabeChatPlugin(object):
    def event_handle(self, gameId):
        serverType = gdata.serverType()
        if serverType not in (gdata.SRV_TYPE_TABLE,
                              ):
            return {}

        common_handlers = {
            PluginEvent.EV_RELOAD_CONFIG: self.onEvReloadConfig,
        }

        handlers = {}

        if serverType == gdata.SRV_TYPE_TABLE:
            handlers = {
                ('table', 'chat'): self.onTableChat,
            }

        handlers.update(common_handlers)
        return handlers

    def __init__(self, gameId):
        self.gameId = gameId

        self._initConf()

    def _initConf(self):
        '''初始化配置'''
        pass

    def onEvReloadConfig(self, gameId, msg):
        '''刷新配置'''
        # keyList = msg.getParam('keylist')
        # if self._configKey in keyList:
        #     self._initConf()

    def onTableChat(self, gameId, msg):
        if ftlog.is_debug():
            ftlog.debug("<< |msg", msg, caller=self)

        table = msg.getParam("table")
        userId = msg.getParam("userId")
        seatIndex = msg.getParam("seatId")
        isFace = msg.getParam("isFace")
        voiceIdx = msg.getParam("voiceIdx")
        chatMsg = msg.getParam("msg")

        player = table.players[seatIndex]
        if player.userId != userId:
            ftlog.warn(table._baseLogStr("onTableChat player.userId != userId!", userId),
                       "|seatIndex, player:", seatIndex, player.userId, caller=self)
            return False

        if isFace == 0:
            # 纯文本内容
            chatMsg = keywords.replace(chatMsg[:80])  # 80个字符长度限制
            if difangConf.isEnableLogChatMsg(gameId):
                hallchatlog.reportChatLog(userId, chatMsg, self.gameId, table.roomId, table.tableId, seatIndex,
                                          userName=player.name, roomName=table.room.roomConf.get('name'))
                ftlog.info('onTableChat |gameId, tableId, userId, name, chatMsg:',
                           gameId, table.tableId, player.userId, player.name, chatMsg, caller=self)

        self.sendTableChatResToAll(table, player, isFace, voiceIdx, chatMsg)

        # if isFace == 1:
        #     # 表情图片
        #     self.sendTableChatResToAll(table, player, isFace, voiceIdx, chatMsg)
        #     return
        #
        # if isFace == 2:
        #     # 语音聊天
        #     self.sendTableChatResToAll(table, player, isFace, voiceIdx, chatMsg)

    def sendTableChatResToAll(self, table, player, isFace, voiceIdx, chatMsg):
        mo = table.createMsgPackRes('table_chat')
        mo.setResult('userId', player.userId)
        mo.setResult('msg', chatMsg)
        mo.setResult('isFace', isFace)
        mo.setResult('seatId', player.seatIndex)
        # mo.setResult('userName', toUserName)
        if voiceIdx != -1:
            mo.setResult('voiceIdx', voiceIdx)
        table.sendToAllTableUser(mo)
