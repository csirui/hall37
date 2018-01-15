# -*- coding=utf-8
'''
Created on 2016年9月23日
下行消息通知

@author: zhaol
'''
import json

from freetime.util import log as ftlog


class MMsg(object):
    def __init__(self):
        super(MMsg, self).__init__()
        self.__tableId = 0
        self.__roomId = 0
        self.__players = []
        self.__playMode = ''
        self.__tableTye = ''
        self.__gameId = 0
        self.__playerCount = 0
        self.__roomConf = {}
        self.__tableConf = {}
        self.__table_tile_mgr = None
        self.__latest_msgs = None
        self.__action_id = 0
        self.__msg_records = []
        self.__gang_rule_mgr = None
        self.__player_steps = {}

    def saveRecord(self, recordName):
        pass

    def reset(self):
        """重置消息模块"""
        self.__action_id = 0
        self.__latest_msgs = [None for _ in range(self.playerCount)]
        self.__msg_records = []
        self.__player_steps = {}

    @property
    def actionId(self):
        return self.__action_id

    def setActionId(self, actionId):
        self.__action_id = actionId

    @property
    def msgRecords(self):
        return self.__msg_records

    @property
    def playerSteps(self):
        return self.__player_steps

    def addPlayerStepByUserId(self, userId):
        if self.__player_steps.has_key(userId):
            self.__player_steps[userId] += 1
        else:
            self.__player_steps[userId] = 1

    def getPlayerStepByUserId(self, userId):
        if self.__player_steps.has_key(userId):
            return self.__player_steps[userId]
        else:
            return 0

    def addMsgRecord(self, message, uidList):
        if not isinstance(uidList, list):
            uidList = [uidList]
        mStr = message.pack()
        mObj = json.loads(mStr)
        if 'result' in mObj:
            # 这条协议下发玩家列表
            mObj['result']['record_uid_list'] = uidList
            # 所有回放数据都加上标记
            mObj['result']['isTableRecord'] = True
        replace = False
        if message.getCmd() == "table_info":
            lastIndex = 0
            userId = message.getResult("userId", 0)
            ftlog.debug("addMsgRecord replace table_info userId:", userId)
            for record in self.__msg_records:
                if record.get("cmd", "") == "table_info":
                    result = record.get("result", None)
                    if result:
                        oldUserId = result.get("userId", -1)
                        ftlog.debug("addMsgRecord replace table_info userId:", userId, "oldUserId", oldUserId)
                        if oldUserId == userId:
                            self.__msg_records[lastIndex] = mObj
                            replace = True
                            break;
                lastIndex += 1
        if not replace:
            self.__msg_records.append(mObj)

    @property
    def latestMsg(self):
        """玩家最新的消息"""
        return self.__latest_msgs

    def table_call_latest_msg(self, seatId):
        """补发最新的消息"""
        pass

    @property
    def gangRuleMgr(self):
        return self.__gang_rule_mgr

    def setGangRuleMgr(self, gangRuleMgr):
        """设置杠牌管理器"""
        self.__gang_rule_mgr = gangRuleMgr

    @property
    def tableTileMgr(self):
        return self.__table_tile_mgr

    def setTableTileMgr(self, tableTileMgr):
        """设置牌桌手牌管理器"""
        self.__table_tile_mgr = tableTileMgr

    @property
    def roomConf(self):
        """房间配置"""
        return self.__roomConf

    @property
    def tableConf(self):
        """牌桌配置"""
        return self.__tableConf

    @property
    def playerCount(self):
        return self.__playerCount

    @property
    def playMode(self):
        return self.__playMode

    @property
    def tableType(self):
        return self.__tableTye

    @property
    def tableId(self):
        return self.__tableId

    @property
    def roomId(self):
        return self.__roomId

    @property
    def gameId(self):
        return self.__gameId

    @property
    def players(self):
        return self.__players

    def setPlayers(self, players):
        """设置玩家"""
        self.__players = players

    def setInfo(self, gameId, roomId, tableId, playMode, tableType, playerCount):
        """设置三个公共信息"""
        self.__gameId = gameId
        self.__roomId = roomId
        self.__tableId = tableId
        self.__playMode = playMode
        self.__tableTye = tableType
        self.__playerCount = playerCount
        self.__latest_msgs = [None for _ in range(playerCount)]
        self.__player_steps = {}

    def setRoomInfo(self, roomConf, tableConf):
        """设置房间配置"""
        self.__roomConf = roomConf
        self.__tableConf = tableConf

    def setTableId(self, tableId):
        """设置tableId
        """
        self.__tableId = tableId

    def setRoomId(self, roomId):
        """设置roomId
        """
        self.__roomId = roomId

    def table_call_add_card(self, player, tile, state, seatId, timeOut, actionId, extendInfo, changeInfo=None):
        """通知庄家游戏开始
        """
        pass

    def table_call_add_card_broadcast(self, seatId, timeOut, actionId, userId, tile, changeInfo=None):
        """通知其他人游戏开始
        """
        pass

    def table_call_drop(self, seatId, player, tile, state, extendInfo, actionId, timeOut):
        """通知玩家出牌
        参数：
            player - 做出牌操作的玩家
        """
        pass

    def table_call_after_chi(self, lastSeatId, seatId, tile, pattern, timeOut, actionId, player, actionInfo=None):
        """吃牌广播"""
        pass

    def table_call_after_peng(self, lastSeatId, seatId, tile, timeOut, actionId, player, pengPattern, actionInfo=None,
                              exInfo=None):
        """碰牌广播"""
        pass

    def table_call_after_gang(self, lastSeatId, seatId, tile, loser_seat_ids, actionId, player, gang, exInfo=None):
        """杠牌广播"""
        pass

    def table_call_after_zhan(self, lastSeatId, seatId, tile, timeOut, actionId, player, pattern, actionInfo=None):
        """粘牌广播"""
        pass

    def sendMsgInitTils(self, tiles, banker, userId, seatId):
        """发牌"""
        pass

    def table_call_table_info(self
                              , userId
                              , banker
                              , seatId
                              , isReconnect
                              , quanMenFeng
                              , curSeat
                              , tableState
                              , cInfo=None
                              , btInfo=None):
        """发送table_info"""
        pass

    def table_call_after_ting(self, player, actionId, userId, allWinTiles):
        """听牌消息"""
        pass

    def table_call_grab_ting(self):
        pass

    def table_call_baopai(self, player, baopai, abandones):
        """宝牌通知"""
        pass

    def table_call_fanpigu(self, pigus, uids, implicitFlag=False):
        """翻屁股通知"""
        pass

    def table_call_QGH_wait(self, userId, implicitFlag=False):
        """发送翻屁股消息"""
        pass

    def table_call_exchange(self, seatId, tile, exchangedInfo, exchangInfo, extendInfo, userId, actionId):
        """换牌消息,发给要换牌的人"""
        pass

    def table_call_exchange_broadcast(self, seatId, tile, exchangedInfo, userId, actionId):
        """换牌消息广播,发给桌上其他人"""
        pass

    def table_call_score(self, players, score, delta):
        """牌桌积分变化"""
        pass

    def table_call_game_win_loose(self
                                  , uids
                                  , wins
                                  , looses
                                  , observers
                                  , winMode
                                  , tile
                                  , totalScore
                                  , deltaScore
                                  , scoreBase
                                  , fanPattern
                                  , customInfo=None):
        """结算"""
        pass

    def table_call_game_all_stat(self, terminate, extendBudgets, ctInfo):
        """牌桌结束大结算"""
        pass

    def table_call_laizi(self, uids, magicTiles=[], magicFactors=[]):
        """下发赖子"""
        pass

    def table_call_online_state(self, uids, onlineInfo):
        """下发玩家在线状态"""
        pass

    def table_call_ping(self, userId, pingInfo, timeStamp):
        """下发玩家网络状况"""
        pass
