# coding=UTF-8
'''
'''
from difang.entity.table_record import DiFangTableRecord
from hall.entity.todotask import TodoTaskShowInfo, TodoTaskHelper
from poker.protocol import router

__author__ = ['"Zhouhao" <zhouhao@tuyoogame.com>']

import functools
import time
from datetime import datetime

from freetime.util import log as ftlog

from poker.entity.game.rooms.room import TYRoom
from poker.entity.dao import sessiondata, gamedata
from poker.entity.game.plugin import TYPluginCenter, TYPluginUtils

import difang.entity.plugin_event_const as PluginEvents
from difang.gametable.table import DiFangTable
from difang.gameplayer.players_helper import DiFangPlayersHelper
import difang.entity.conf as difangConf


class DiFangCustomTable(DiFangTable):
    def _initTableType(self):
        ''''''
        self.tableType = {"isCustom": True}

    def clear(self):
        super(DiFangCustomTable, self).clear()
        self.ftId = 0  # 房间号
        self.firstPlayerId = 0  # 房主userId
        self.consumedRoomCardN = 0  # 已经消耗的房卡
        self.agreeN = 0  # 统一散桌的票数
        self.tableRecordInfos = []  # 牌局记录索引
        self.tableRecord = DiFangTableRecord(self)  # 牌局记录
        self.createTime = 0  # 自建桌创建时间

    def _doTableManage(self, msg, action):
        '''
        处理来自GR的table_manage命令
        '''
        if action == 'leave':
            userId = msg.getParam("userId")
            assert isinstance(userId, int) and userId > 0
            clientId = sessiondata.getClientId(userId)
            return self._doLeave(msg, userId, clientId)
        elif action == 'clear_table':
            return self._doClearPlayers()
        if action == 'clear_players':
            return self._doClearPlayers()

    def _processTableCallAction(self, action, userId, seatIndex, clientId, msg):

        player = self.players[seatIndex]
        if player.userId != userId:
            ftlog.warn(self._baseLogStr("_processTableCallAction player.userId != userId!", userId),
                       "|seatIndex, player, action:", seatIndex, player.userId, action, caller=self)
            return False

        if action == 'chu_pai':
            self.PlayerActionHelperClass.onEventChuPai(self, player, msg)
        elif action == 'ready':
            self.PlayerActionHelperClass.onEventReady(self, player, msg)
        elif action == 'vote_dismiss':
            self.PlayerActionHelperClass.onEventVoteDismiss(self, player, msg)
        elif action == 'ping':
            self.PlayerActionHelperClass.onEventPing(self, player, msg)

    def _checkSitCondition(self, userId):
        if len(DiFangPlayersHelper.getSitPlayerIds(self)) == self.cMaxSeatNum:
            return False, TYRoom.ENTER_ROOM_REASON_TABLE_FULL

        return True, TYRoom.ENTER_ROOM_REASON_OK

    def _refreshCustomConf(self, selectedRoomOptions):
        self.selectedRoomOptions = selectedRoomOptions

        maxSeatN = selectedRoomOptions["maxSeatN"]
        if maxSeatN <= self.maxSeatN:
            self.cMaxSeatNum = maxSeatN

        if ftlog.is_debug():
            ftlog.debug(self._baseLogStr("change self.cMaxSeatNum"),
                        "|self.cMaxSeatNum:", self.cMaxSeatNum, caller=self)

        self.gamePlay._initField()
        self.gamePlay.pot._initField()

    # def _checkSitCondition(self, userId):
    #     if self.ftId == 0:
    #         ftlog.warn(self._baseLogStr("ftId == 0", userId), caller=self)
    #         return False, TYRoom.ENTER_ROOM_REASON_NOT_OPEN
    #     return True, TYRoom.ENTER_ROOM_REASON_OK

    def _doSit(self, msg, userId, seatId, clientId, checkGameStart=True):

        selectedRoomOptions = msg.getParam("selectedRoomOptions")
        ftId = msg.getParam("ftId")
        if ftlog.is_debug():
            ftlog.debug(self._baseLogStr("<<", userId),
                        "|selectedRoomOptions, ftId, self.cMaxSeatNum:",
                        selectedRoomOptions, ftId, self.cMaxSeatNum, caller=self)

        if selectedRoomOptions:
            self._refreshCustomConf(selectedRoomOptions)
            self.firstPlayerId = userId  # 房主
            self.ftId = ftId  # 6位自建号
            self.createTime = int(time.time())
            ftlog.info(self._baseLogStr("_doSit <<", userId),
                       "|selectedRoomOptions, ftId, self.cMaxSeatNum:",
                       selectedRoomOptions, ftId, self.cMaxSeatNum, caller=self)

        result = super(DiFangCustomTable, self)._doSit(msg, userId, seatId, clientId)

        if result["reason"] == TYRoom.ENTER_ROOM_REASON_TABLE_FULL:
            tip = u"您好, 牌桌已满。"
            TodoTaskHelper.sendTodoTask(self.gameId, userId, TodoTaskShowInfo(tip, True))
            return result

        if result["reason"] != TYRoom.ENTER_ROOM_REASON_OK:
            return result

        # 坐下成功, 人满后检查开桌
        if ftlog.is_debug():
            ftlog.debug(self._baseLogStr(">>", userId),
                        "|self.playersNum, self.cMaxSeatNum:",
                        self.playersNum, self.cMaxSeatNum, caller=self)

        if selectedRoomOptions:
            for _ in range(self.cMaxSeatNum - self.playersNum):
                self.sendRobotNotifyCallUp(None)

        if self.gamePlay.isWaitingState() and checkGameStart and self.playersNum == self.cMaxSeatNum:
            func = functools.partial(self.gamePlay.doActionCheckStartGame)
            msgPackParams = {"seatId": result["seatId"] - 1}
            self.callLaterFunc(0, func, userId, timer=None, msgPackParams=msgPackParams)  # 需要异步锁桌子

        return result

    def _applyAdjustTablePlayers(self):
        '''向GR申请调整牌桌玩家'''
        if not self.gamePlay.isWaitingState():
            self.gamePlay.transitToStateWait()
        mpReqRecycleTable = self.createMsgPackRequest("room", "adjust_table_players")
        mpReqRecycleTable.setParam("roomId", self.room.ctrlRoomId)
        mpReqRecycleTable.setParam("tableId", self.tableId)
        router.sendRoomServer(mpReqRecycleTable, self.room.ctrlRoomId)

    def _doClearPlayers(self):
        try:
            if ftlog.is_debug():
                ftlog.debug(self._baseLogStr("<<"), "|gameSeq, agreeN:", self.gamePlay.gameSeq, self.agreeN,
                            caller=self)
            needSendRes = False
            if self.agreeN == self.cMaxSeatNum:
                needSendRes = True
            if self.gamePlay.gameSeq == 0:
                needSendRes = True

            TYPluginCenter.event(TYPluginUtils.updateMsg(cmd=PluginEvents.EV_BEFORE_TABLE_CLEAR_PLAYERS, params={
                'table': self}), self.gameId)

            # tip = u"您好,此牌桌已解散。"
            sitUserIds = DiFangPlayersHelper.getSitPlayerIds(self)
            for userId in sitUserIds:
                self.sendRoomLeaveReq(userId, TYRoom.LEAVE_ROOM_REASON_SYSTEM, needSendRes=needSendRes)
                # TodoTaskHelper.sendTodoTask(self.gameId, userId, TodoTaskShowInfo(tip, True))

            self.clear()
            return {"isOK": True}
        except Exception, e:
            ftlog.error(e)
            return {"isOK": False}

    def _doLeave(self, msg, userId, clientId):

        reason = msg.getParam("reason", TYRoom.LEAVE_ROOM_REASON_ACTIVE)
        if reason == TYRoom.LEAVE_ROOM_REASON_LOST_CONNECTION:
            self.sendPlayerDataToAll(userId, managed=True)
            return {"isOK": False, "reason": reason}

        if reason == TYRoom.LEAVE_ROOM_REASON_SYSTEM:
            return super(DiFangCustomTable, self)._doLeave(msg, userId, clientId)

        if reason == TYRoom.LEAVE_ROOM_REASON_ACTIVE and self.gamePlay.gameSeq == 0:
            result = super(DiFangCustomTable, self)._doLeave(msg, userId, clientId)
            if self.firstPlayerId == userId:
                self._doClearPlayers()
                self.firstPlayerId = 0
                return result

        return {"isOK": False, "reason": TYRoom.LEAVE_ROOM_REASON_FORBIT}

    def addTableRecord(self):
        '''添加一局牌局记录'''
        currentTimeStr = datetime.now().strftime("%m-%d %H:%M:%S")

        downloadUrl, token, path = difangConf.getTableRecordDownloadConf(self.gameId)
        # path = difangConf.getPublicConf(self.table.gameId, 'cloudUploadPath')

        tableRecordInfo = dict(gameSeq=self.gamePlay.gameSeq,
                               time=currentTimeStr,
                               tableChips=[player.tableChips for player in DiFangPlayersHelper.getPlayingPlayers(self)],
                               url=downloadUrl + path + self.tableRecord.getKey() + "_" + str(self.gamePlay.gameSeq)
                               )
        ftlog.info("addTableRecord |ftId, tableId, url:", self.ftId, self.tableId, tableRecordInfo.get("url"))

        self.tableRecordInfos.append(tableRecordInfo)
        if ftlog.is_debug():
            ftlog.debug(">> |tableRecordInfo", tableRecordInfo, caller=self)

        self.tableRecord.saveRecord()

    def countGame(self):
        for player in DiFangPlayersHelper.getPlayingPlayers(self):
            userId = player.userId
            # play_game_count
            playGameCount = gamedata.getGameAttr(userId, self.gameId, 'play_game_count')
            if not playGameCount:
                playGameCount = 0
            playGameCount += 1
            gamedata.setGameAttr(userId, self.gameId, 'play_game_count', playGameCount)
            ftlog.info("countGame userId=", userId, "play_game_count=", playGameCount)
            # win_game_count
            if self.gamePlay.pot.allwinchips[player.seatIndex] > 0:
                winGameCount = gamedata.getGameAttr(userId, self.gameId, 'win_game_count')
                if not winGameCount:
                    winGameCount = 0
                winGameCount += 1
                gamedata.setGameAttr(userId, self.gameId, 'win_game_count', winGameCount)
                ftlog.info("countGame userId=", userId, "win_game_count=", winGameCount)

    # --- 各牌桌子类供回调的个性化逻辑
    def _processCheckGameStartFail(self):
        ''''''
        # 发送机器人的邀请通知
        # for _ in range(self.cMaxSeatNum - self.playersNum):
        #     self.sendRobotNotifyCallUp(None)

    def _processAfterGameEnd(self):
        '''
        不同游戏牌桌子类进行GameEnd后处理， 默认什么都不做
        '''
        self.addTableRecord()
        self.countGame()

    def _processStartNextGame(self):
        '''
        不同游戏牌桌子处理开始下一局游戏逻辑， 默认2秒后检查开局
        '''
        if ftlog.is_debug():
            ftlog.debug(self._baseLogStr("<<"), "|gameSeq, gameRoudN:",
                        self.gamePlay.gameSeq, self.selectedRoomOptions["gameRoundN"], caller=self)

        if self.gamePlay.gameSeq >= self.selectedRoomOptions["gameRoundN"]:
            self._applyAdjustTablePlayers()
            return

        self._resetTableConf()
        # func = functools.partial(self.gamePlay.doActionCheckStartGame)
        # self.callLaterFunc(self._runConfig.get('readyInterval', 2), func)

    def _processPlayerActTimeOut(self, player):
        player.isManaged = True  # 托管
        self.sendPlayerDataToAll(player.userId, managed=True)
