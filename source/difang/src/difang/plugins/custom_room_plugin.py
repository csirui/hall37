# coding: UTF-8
'''
自建房间插件
'''
from difang.gameplayer.players_helper import DiFangPlayersHelper
from hall.entity.hallitem import TYDecroationItem

__author__ = ['ZhouHao']

import json
from datetime import datetime

import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack

from poker.entity.configure import gdata
from poker.entity.dao import daobase, sessiondata, gamedata
import poker.util.timestamp as pktimestamp
from poker.protocol import router, runcmd

from hall.entity import hall_friend_table, hallitem, hall_fangka, datachangenotify
from hall.entity.todotask import TodoTaskHelper, TodoTaskShowInfo

import difang.entity.plugin_event_const as PluginEvent
import difang.entity.conf as difangConf
from difang.quick_start import DiFangQuickStart


class DiFangCustomRoomPlugin(object):
    CREATE_CUSTOM_TABLE_ERR_NO_NOT_ENOUGH = "1"
    CREATE_CUSTOM_TABLE_ERR_NO_NOT_ALLOW = "2"
    ENTER_CUSTOM_TABLE_ERR_NO_WRONG_ROOMNO = "3"
    ENTER_CUSTOM_TABLE_ERR_NO_FULL = "4"

    REDIS_KEY_ROOM_NO_TO_TABLE_ID = "roomNoToTableId:"

    def event_handle(self, gameId):
        serverType = gdata.serverType()
        if serverType not in (gdata.SRV_TYPE_UTIL,
                              gdata.SRV_TYPE_ROOM,
                              gdata.SRV_TYPE_HTTP,
                              gdata.SRV_TYPE_TABLE):
            return {}

        common_handlers = {
            # PluginEvent.EV_NEW_TIME: self.onEvNewTime,
            PluginEvent.EV_RELOAD_CONFIG: self.onEvReloadConfig,
        }

        handlers = {}

        if serverType == gdata.SRV_TYPE_UTIL:
            handlers = {
                ('game', 'create_custom_table'): self.onGameCreateCustomTable,
                ('game', 'get_custom_options'): self.onGameGetCustomOptions,
                ('game', 'get_custom_records'): self.getCustomRecords,
            }
        elif serverType == gdata.SRV_TYPE_ROOM:
            handlers = {
                ('room', 'create_custom_table'): self.onRoomCreateCustomTable,
            }
        elif serverType == gdata.SRV_TYPE_TABLE:
            handlers = {
                PluginEvent.EV_SEND_TABLE_INFO: self.onSendTableInfo,
                PluginEvent.EV_TRANSIT_TO_STATE_START_GAME: self.onTableGameStart,
                PluginEvent.EV_BEFORE_TABLE_CLEAR_PLAYERS: self.onTableClearPlayers,
            }
        elif serverType == gdata.SRV_TYPE_HTTP:
            handlers = {
                PluginEvent.EV_HTTP_COMMON_REQUEST: self.onHttpRequest,
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

    def onHttpRequest(self, gameId, msg):
        ''' 处理 http 消息 '''

        httpRequest, httpArgs = msg.getParams('httpRequest', 'httpArgs')
        httpResult = msg.getResult('httpResult')
        httpArgs = dict([(k, v[0] if len(v) == 1 else v)
                         for k, v in httpArgs.items()])

        if ftlog.is_debug():
            ftlog.debug('httpArgs', httpArgs)

        action = httpArgs.get('a')
        if action != 'custome':
            return

        subaction = httpArgs.get('sa')
        # if subaction == 'getAllTable':
        #     self._doHttpGetAllTable(gameId, httpRequest, httpArgs, httpResult)

    def assignFriendTableId(self, gameId, tableId):
        '''分配房间号, 并将房间号保存到redis中，方便查找'''
        ftId = hall_friend_table.createFriendTable(gameId)
        if ftId:
            daobase.executeMixCmd('HSET', self.REDIS_KEY_ROOM_NO_TO_TABLE_ID + str(gameId), ftId, tableId)
        else:
            ftlog.error("assign roomNo error! |gameId, tableId:", gameId, tableId)
        return ftId

    @classmethod
    def getTableIdOfFtId(cls, gameId, ftId):
        return daobase.executeMixCmd('HGET', cls.REDIS_KEY_ROOM_NO_TO_TABLE_ID + str(gameId), ftId)

    def releaseFriendTable(self, gameId, ftId):
        '''解散房间'''
        daobase.executeMixCmd('HDEL', self.REDIS_KEY_ROOM_NO_TO_TABLE_ID + str(gameId), ftId)
        hall_friend_table.releaseFriendTable(gameId, ftId)

    def onGameGetCustomOptions(self, gameId, msg):
        # def onRoomGetCustomOptions(self, gameId, msg):
        '''在GR处理获取自建桌配置逻辑
        '''
        if ftlog.is_debug():
            ftlog.debug("<< |msg", msg, caller=self)

        msg = runcmd.getMsgPack()
        userId = msg.getParam("userId")

        selectedRoomOptions = self._getSelectedRoomOptions(userId, gameId)

        msgRes = MsgPack()
        msgRes.setCmd("game")
        msgRes.setResult("action", "get_custom_options")
        msgRes.setResult("userId", userId)
        msgRes.setResult("gameId", gameId)
        msgRes.setResult("selectedRoomOptions", selectedRoomOptions)
        msgRes.setResult("customRoomOptions", difangConf.getCustomRoomConf(gameId, 'options'))
        msgRes.setResult("customConfVer", difangConf.getCustomRoomConf(gameId, 'ver'))
        router.sendToUser(msgRes, userId)

    def _checkUserLastSelectedCustomRoomConfVer(self, userId, gameId):
        confVer = difangConf.getCustomRoomConf(gameId, 'ver')
        userLastSelectedCustomRoomConfVer = gamedata.getGameAttr(userId, gameId, "customConfVer")
        if ftlog.is_debug():
            ftlog.debug("|userId, gameId, confVer, userLastSelectedCustomRoomConfVer:",
                        userId, gameId, confVer, userLastSelectedCustomRoomConfVer, caller=self)
        if userLastSelectedCustomRoomConfVer and confVer != userLastSelectedCustomRoomConfVer:
            return False

        return True

    def _getSelectedRoomOptions(self, userId, gameId):

        if ftlog.is_debug():
            ftlog.debug("|userId, gameId:", userId, gameId, caller=self)

        if not self._checkUserLastSelectedCustomRoomConfVer(userId, gameId):
            return difangConf.getCustomRoomConf(gameId, 'defaultSelectedOptions')

        selectedRoomOptions = gamedata.getGameAttrJson(userId, gameId, "selectedRoomOptions")
        if not selectedRoomOptions:  # 新加玩法类型
            return difangConf.getCustomRoomConf(gameId, 'defaultSelectedOptions')

        if ftlog.is_debug():
            ftlog.debug("|userId, gameId:", userId, gameId, "|selectedRoomOptions:", selectedRoomOptions, caller=self)

        return selectedRoomOptions

    def onGameCreateCustomTable(self, gameId, msg):
        '''创建自建桌的请求入口, 具体逻辑转发给GR执行
        '''
        if ftlog.is_debug():
            ftlog.debug("<< |msg", msg, caller=self)

        userId = msg.getParam("userId")
        clientId = msg.getParam("clientId")

        if DiFangQuickStart.checkReConnect(userId, clientId, gameId):
            # self.sendGameCreateCustomTableRes(0, userId)
            return

        # 转发给GR处理具体逻辑
        roomId = msg.getParam("roomId", 0)
        if not roomId:
            roomId = gdata.gameIdBigRoomidsMap()[gameId][0]
            msg.setParam("roomId", roomId)
        msg.setCmdAction("room", "create_custom_table")

        # 需要用query模式等待GR回复再return,return前UT会锁住userId,从而避免客户端同时发多个请求时出现混乱
        router.queryRoomServer(msg, roomId)

    def onRoomCreateCustomTable(self, gameId, msg):
        '''在GR处理自建桌逻辑
        '''
        if ftlog.is_debug():
            ftlog.debug("<< |msg", msg, caller=self)

        userId = msg.getParam("userId")
        selectedRoomOptions = msg.getParam("selectedRoomOptions")
        if not selectedRoomOptions:
            return
        customConfVer = msg.getParam("customConfVer")
        if customConfVer != difangConf.getCustomRoomConf(gameId, 'ver'):
            ftlog.warn("onRoomCreateCustomTable confVer error! |msg:", msg, caller=self)
            return
        gameRoundN = selectedRoomOptions.get("gameRoundN")
        if not gameRoundN:
            return
        roomId = msg.getParam("roomId")
        room = gdata.rooms()[roomId]
        clientId = msg.getParam("clientId")

        needRoomCardN = difangConf.getCustomRoomConf(gameId, 'roomCardNCost').get(str(gameRoundN), -1)
        if needRoomCardN == -1:
            tips = difangConf.getCustomRoomConf(difangConf.GAME_ID, 'err_tips')
            tip = tips[self.CREATE_CUSTOM_TABLE_ERR_NO_NOT_ALLOW]
            TodoTaskHelper.sendTodoTask(gameId, userId, TodoTaskShowInfo(tip, True))
            ftlog.warn("onRoomCreateCustomTable get needRoomCardN error! |msg:", msg, caller=self)
            self.sendGameCreateCustomTableRes(0, userId)
            return

        if ftlog.is_debug():
            ftlog.debug("|userId, gameId, customConfVer, gameRoundN, needRoomCardN:",
                        userId, gameId, customConfVer, gameRoundN, needRoomCardN, caller=self)

        if needRoomCardN > 0 and not self.isCardEnough(gameId, userId, needRoomCardN, clientId):
            tips = difangConf.getCustomRoomConf(difangConf.GAME_ID, 'err_tips')
            tip = tips[self.CREATE_CUSTOM_TABLE_ERR_NO_NOT_ENOUGH]
            TodoTaskHelper.sendTodoTask(gameId, userId, TodoTaskShowInfo(tip, True))
            self.sendGameCreateCustomTableRes(0, userId)
            return

        tableId = room.getIdleTableId()
        if not tableId:
            ftlog.error("there are no idle tables!", "|userId, roomId:", userId, room.roomId)
            return

        ftId = self.assignFriendTableId(gameId, tableId)

        ftlog.info("onRoomCreateCustomTable |userId, tableId, ftId:", userId, tableId, ftId, caller=self)
        self.sendGameCreateCustomTableRes(ftId, userId)
        gamedata.setGameAttr(userId, gameId, "selectedRoomOptions", json.dumps(selectedRoomOptions))
        gamedata.setGameAttr(userId, gameId, "customConfVer", customConfVer)

        shadowRoomId = tableId / 10000
        room.querySitReq(userId, shadowRoomId, tableId, clientId,
                         extParams={"selectedRoomOptions": selectedRoomOptions, "ftId": ftId})

    def sendGameCreateCustomTableRes(self, ftId, userId):
        '''返回房间号
        '''
        if ftlog.is_debug():
            ftlog.debug("<< |userId, ftId:", userId, ftId, caller=self)
        msgRes = MsgPack()
        msgRes.setCmd("game")
        msgRes.setResult("action", "create_custom_table")
        msgRes.setResult("userId", userId)
        msgRes.setResult("ftId", ftId)
        router.sendToUser(msgRes, userId)

    def onSendTableInfo(self, gameId, msg):
        if ftlog.is_debug():
            ftlog.debug("<< |msg", msg, caller=self)

        userId = msg.getParam("userId")
        table = msg.getParam("table")
        mpTableInfoRes = msg.getParam("mpTableInfoRes")

        winxinDesc = u"房间号:" + table.ftId
        selectedOptionNames = []
        options = difangConf.getCustomRoomConf(gameId, "options")

        for option in options:
            key = option["key"]
            for i, value in enumerate(option["values"]):
                if value == table.selectedRoomOptions[key]:
                    name = unicode(option["names"][i])
                    winxinDesc += " ," + name
                    selectedOptionNames.append(name)

        # maxSeatN = table.selectedRoomOptions["maxSeatN"]
        # gameRoundN = table.selectedRoomOptions["gameRoundN"]

        # for option in options:
        #     if option["key"] == "bankerRule":
        #         for i, value in enumerate(option["values"]):
        #             if value == table.selectedRoomOptions["bankerRule"]:
        #                 bankerRuleName = option["names"][i]
        #         if option["key"] == "bombMultipleType":
        #             for i, value in enumerate(option["values"]):
        #                 if value == table.selectedRoomOptions["bombMultipleType"]:
        #                     bombMultipleTypeName = option["names"][i]
        #         if option["key"] == "bombMultipleMax":
        #             for i, value in enumerate(option["values"]):
        #                 if value == table.selectedRoomOptions["bombMultipleMax"]:
        #                     bombMultipleMaxName = option["title"] + option["names"][i]

        # 微信配置
        weixinShare = difangConf.getPublicConf(gameId, "weixinShare")
        weixinurl, weixintitle = difangConf.getShareInfo(userId, gameId, "gdy_invite_play_share")
        if weixinurl:
            weixinShare["weixinurl"] = weixinurl
            weixinShare["weixintitle"] = weixintitle
        weixinShare["weixindesc"] = winxinDesc
        mpTableInfoRes.setResult('weixinShare', weixinShare)
        mpTableInfoRes.setResult('selectedOptionNames', selectedOptionNames)

    def consumeRooCardsFirstWay(self, table, needRoomCardN):
        gameId = table.gameId

        oneRoomCardGameRoundN = difangConf.getCustomRoomConf(gameId, "oneRoomCardGameRoundN")
        if not oneRoomCardGameRoundN:
            return

        if table.gamePlay.gameSeq % oneRoomCardGameRoundN != 1:
            return

        userId = table.firstPlayerId
        clientId = sessiondata.getClientId(userId)
        self.consumeRoomCard(gameId, userId, 1, clientId)
        table.consumedRoomCardN += 1

    def consumeRooCardsSecondWay(self, table, needRoomCardN):
        gameId = table.gameId
        userId = table.firstPlayerId
        clientId = sessiondata.getClientId(userId)
        self.consumeRoomCard(gameId, userId, needRoomCardN, clientId)
        table.consumedRoomCardN += needRoomCardN

    def onTableGameStart(self, gameId, msg):
        '''在GT处理牌局开始时扣房卡
        '''
        if ftlog.is_debug():
            ftlog.debug("<< |msg", msg, caller=self)

        table = msg.getParam("table")

        gameRoundN = table.selectedRoomOptions["gameRoundN"]
        needRoomCardN = difangConf.getCustomRoomConf(gameId, 'roomCardNCost').get(str(gameRoundN), -1)
        if needRoomCardN <= 0 or needRoomCardN == table.consumedRoomCardN:
            return

        way = msg.getParam("way", 2)
        if way == 2:
            self.consumeRooCardsSecondWay(table, needRoomCardN)

        ftlog.info("onTableGameStart >> |userId, tableId, ftId, consumedRoomCardN:",
                   table.firstPlayerId, table.tableId, table.ftId, table.consumedRoomCardN, caller=self)

    def consumeRoomCard(self, gameId, userId, needRoomCardN, clientId):
        """消耗房卡"""
        ftlog.info("consumeRoomCard << |userId, needRoomCardN, clientId", userId, needRoomCardN, clientId, caller=self)
        if not needRoomCardN:
            return

        if not clientId:
            clientId = sessiondata.getClientId(userId)
        itemId = hall_fangka.queryFangKaItem(gameId, userId, clientId)

        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.getItemByKindId(itemId)
        if not item:
            return

        timestamp = pktimestamp.getCurrentTimestamp()
        count = userBag.consumeItemUnits(gameId, item, needRoomCardN, timestamp, 'ITEM_USE', item.kindId)

        changed = ['item']
        if isinstance(item, TYDecroationItem):
            changed.append('decoration')
        datachangenotify.sendDataChangeNotify(gameId, userId, changed)

    def isCardEnough(self, gameId, userId, needRoomCardN, clientId):
        count = self.queryFangKaCount(gameId, userId, clientId)
        if ftlog.is_debug():
            ftlog.debug("<< |count, userId, needRoomCard, clientId:",
                        count, userId, needRoomCardN, clientId, caller=self)
        if count >= needRoomCardN:
            return True

        ftlog.warn("not enough room cards! |userId, count, needRoomCardN, clientId:",
                   userId, count, needRoomCardN, clientId, caller=self)
        return False

    def queryFangKaCount(self, gameId, userId, clientId):
        if not clientId:
            clientId = sessiondata.getClientId(userId)
        itemId = hall_fangka.queryFangKaItem(gameId, userId, clientId)

        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.getItemByKindId(itemId)
        if not item:
            return 0

        timestamp = pktimestamp.getCurrentTimestamp()
        return item.balance(timestamp)

    def getCustomRecords(self, gameId, msg):
        '''获取战绩
        '''
        if ftlog.is_debug():
            ftlog.debug("<< |msg", msg, caller=self)

        userId = msg.getParam("userId")

        records = gamedata.getGameAttr(userId, gameId, "customTableRecords")
        if records:
            records = json.loads(records)
        else:
            records = []
        for record_item in records:
            if not record_item.get("totalPlayNum"):
                record_item['totalPlayNum'] = "-"
        msgRes = MsgPack()
        msgRes.setCmd("game")
        msgRes.updateResult({"action": "get_custom_records"})
        msgRes.setResult("records", records)
        router.sendToUser(msgRes, userId)

    def saveCustomTableRecordInfos(self, table):
        '''将房间所有牌局记录索引存入redis
        '''
        if table.gamePlay.gameSeq == 0:
            return

        playerInfos = []
        for player in DiFangPlayersHelper.getSitPlayers(table):
            playerInfo = {}
            playerInfo['userId'] = player.userId
            playerInfo['name'] = player.name
            playerInfo['tableChips'] = player.tableChips
            playerInfos.append(playerInfo)

        if ftlog.is_debug():
            ftlog.debug("playerInfos:", playerInfos, caller=self)

        record = {}
        record["ftId"] = table.ftId
        record["gameSeq"] = table.gamePlay.gameSeq
        record['tableRecordInfos'] = table.tableRecordInfos
        record['playerInfos'] = playerInfos
        # timestamp = pktimestamp.getCurrentTimestamp()
        # record['time'] = pktimestamp.timestamp2timeStr(timestamp) # 使用的UTC时区
        record['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for player in DiFangPlayersHelper.getSitPlayers(table):
            if player.tableChips > 0:
                record["res"] = "win"
            elif player.tableChips == 0:
                record["res"] = "drawn"
            else:
                record["res"] = "lose"

            if ftlog.is_debug():
                ftlog.debug("|tableId, userId, record:", table.tableId, player.userId, record, caller=self)

            records = gamedata.getGameAttr(player.userId, table.gameId, "customTableRecords")
            if records:
                records = json.loads(records)
            else:
                records = []
            records.insert(0, record)

            if len(records) > 10:
                del records[-1]

            if ftlog.is_debug():
                ftlog.debug("|tableId, userId, records:", table.tableId, player.userId, records, caller=self)

            gamedata.setGameAttr(player.userId, table.gameId, "customTableRecords", json.dumps(records))

    def onTableClearPlayers(self, gameId, msg):
        if ftlog.is_debug():
            ftlog.debug("<< |msg", msg, caller=self)

        table = msg.getParam("table")

        self.releaseFriendTable(table.gameId, table.ftId)
        self.saveCustomTableRecordInfos(table)
