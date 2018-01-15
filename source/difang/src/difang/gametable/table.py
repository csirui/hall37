# coding=UTF-8
'''
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import difang.entity.plugin_event_const as PluginEvents
from freetime.util import log as ftlog
from poker.entity.dao import onlinedata, sessiondata
from poker.entity.game.plugin import TYPluginCenter, TYPluginUtils
from poker.entity.game.rooms.room import TYRoom
from poker.entity.game.tables.table import TYTable
from poker.entity.game.tables.table_seat import TYSeat
from poker.entity.game.tables.table_timer import TYTableTimer
from poker.protocol import router
from poker.util import strutil


class DiFangTable(TYTable):
    '''地方棋牌牌桌基类
    '''

    #     GamePlaysFactory = None
    #     PlayerClass = None

    def __init__(self, room, tableId):
        super(DiFangTable, self).__init__(room, tableId)

        self.table = self  # 为了和 gamePlay 里调用table属性和方法的代码保持一致
        # 初始化牌桌配置、类型、座位、玩家等
        self._resetTableConf()
        self._initTableType()
        self._initSeatsAndPlayers()
        # 初始化桌子计时器
        self.tableTimer = TYTableTimer(self)
        # 实例化玩法逻辑处理
        self.gamePlay = self.GamePlaysFactory.getInstance(self, room.roomConf.get("playMode", "classic"))
        # 初始化桌子全量配置
        self.clear()
        # 清理遗留的代入金币
        # self.cleanUpLastUserTableChips()

        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd=PluginEvents.EV_AFTER_TABLE_CHILD_INIT, params={
            'table': self, 'tableType': self.tableType}), self.gameId)

        if ftlog.is_debug():
            ftlog.info("__init__ >> |tableId:", self.tableId, caller=self)

    def _baseLogStr(self, des="", userId=None):
        if ftlog.is_debug():
            baseTableInfo = '%s |tableId, playersNum: %d, %d' % (des, self.tableId, self.playersNum)
        else:
            baseTableInfo = '%s |tableId: %d' % (des, self.tableId)
        baseUserInfo = '' if not userId else ' |userId: %d' % (userId)

        return self.__class__.__name__ + " " + baseTableInfo + baseUserInfo

    def _checkReloadRunConfig(self):
        if ftlog.is_debug():
            ftlog.debug('<< |self.playersNum:', self.playersNum, caller=self)
        if self.playersNum == 0:
            self._resetTableConf()

    def _resetTableConf(self):
        if ftlog.is_debug():
            ftlog.debug('<< |self.configChanged:', self.configChanged, caller=self)
        if self.configChanged:
            runconf = strutil.cloneData(self.room.roomConf)
            runconf.update(strutil.cloneData(self.config))  # config 即 tableConf
            self._runConfig = runconf
            self._initTableConf()
            self.configChanged = 0
            if ftlog.is_debug():
                ftlog.debug('>> |self._runConfig:', self._runConfig, caller=self)

    def getTableScore(self):
        """选桌时对桌子的评分
        """
        return 0

    def _initTableConf(self):
        '''table configure全部设为属性. 加c标记, 提示只读. 防止代码误解含义, 修改了不该修改的配置值
        '''
        self.cMaxSeatNum = self.maxSeatN
        self.cName = self._runConfig.get("tname", "undefined")
        self.cOptime = self._runConfig.get("optime", 5)  # 玩家操作时限
        self.cVoteDismissTime = 60  # 玩家投票解散时限
        self.cBaseChip = self._runConfig.get("baseChip", 1)  # 输赢金币底金

        # self.selectedRoomOptions = difangConf.getCustomRoomConf(self.gameId, 'defaultSelectedOptions')
        # self.cMaxSeatNum = self.selectedRoomOptions["maxSeatN"]

    def getName(self):
        return self.cName

    def getAllUserIds(self):
        return [seat.userId for seat in self.seats if seat and not seat.isEmptySeat()] + self.observers.keys()

    def _initSeatsAndPlayers(self):
        self.seatTimers = []
        self.startedPlayers = []  # game_start时参与了游戏的玩家信息，便于玩家离桌后仍可进行结算、统计、任务奖励等处理
        for seatIndex in xrange(self.maxSeatN):
            self.players[seatIndex] = self.PlayerClass(self, seatIndex)
            self.seats[seatIndex] = TYSeat(self)
            self.seatTimers.append(TYTableTimer(self))
            self.startedPlayers.append(None)

    def clear(self):
        self.cancelTimerAll()

    def cancelTimerAll(self):
        '''
        清理所有的计时器
        '''
        self.tableTimer.cancel()
        for t in self.seatTimers:
            t.cancel()

    def _doTableCall(self, msg, userId, seatId, action, clientId):
        '''
        桌子内部处理所有的table_call命令
        具体处理函数自行判定userId和seatId是否吻合

        Notes:
            客户端seatId是从0开始计数的, 对应于服务端的seatIndex
            CL_FUNC_X 是指服务期内部通过callLater技术发送的延迟处理命令
        '''
        seatIndex = seatId
        func = msg.getParam("func")

        if action != "CL_FUNC":
            ftlog.info("handleMsg << receive tableCall, |clientId, userId, action:", clientId, userId, action,
                       "|tableId, seatIndex", self.tableId, seatIndex,
                       caller=self)
        else:
            ftlog.debug("<< |clientId, userId, action:", clientId, userId, action,
                        "|tableId, seatIndex", self.tableId, seatIndex,
                        "|funName:", func.func.func_name,
                        caller=self)

        # ---------------------
        # 内部服务延迟调用函数， 无需验证用户(userId为-1）
        # ---------------------
        if action == "CL_FUNC":
            func()
            return

        # ---------------------
        # 玩家请求、需要验证
        # ---------------------
        if userId <= 0:
            ftlog.error("userId is invalid")
            return

        # -------------------------
        # 玩家游戏操作
        # -------------------------
        self._processTableCallAction(action, userId, seatIndex, clientId, msg)

        msg.getKey("params").update({"table": self})
        TYPluginCenter.event(msg, self.gameId)

    ################# 进入牌桌 ###################

    # def _doEnter(self, msg, userId, clientId):
    #     '''玩家操作, 尝试进入当前的桌子
    #     '''
    #     pass


    def _checkSitCondition(self, userId):
        '''游戏可扩展'''
        return True, TYRoom.ENTER_ROOM_REASON_OK
        # return self.room.checkSitCondition(userId)

    def _onReSit(self, userId, seatId, clientId):
        '''在牌桌坐下的玩家断线重连特殊处理，各Table子类酌情处理
        '''
        ftlog.info(self._baseLogStr("_onReSit <<", userId), caller=self)
        # seatIndex = seatId - 1
        # player = self.players[seatIndex]
        # if player.userId != userId :
        #     ftlog.warn('the seat userId not match userId=', userId, 'seat.userId=', player.userId, caller=self)
        #     return
        # if self.gamePlay.isActionState() and self.gamePlay.betRound.actorPos >= 0:
        #     actor_player = self.players[self.gamePlay.betRound.actorPos]
        #     self.sendBetResponseRes(actor_player, receive_players=[player])

    def _getValidIdleSeatId(self, userId, seatIndex, result):
        '''通用坐下合法性检查函数

        Returns
            idleSeatId：
                >0   ：  为新玩家找到合适座位，需要继续处理
                <0   :   断线重连
                0    ：  坐下失败
         '''

        clientId = sessiondata.getClientId(userId)
        onlineSeatId = onlinedata.getOnlineLocSeatId(userId, self.table.roomId, self.table.tableId)
        if onlineSeatId and onlineSeatId <= self.maxSeatN:  # 断线重连， Note：旁观的人坐下此处不能返回负数，否则无法入座
            ftlog.hinfo('re-sit ok. |userId, tableId, seatId:', userId, self.tableId, onlineSeatId, caller=self)
            result["seatId"] = onlineSeatId
            result["reason"] = TYRoom.ENTER_ROOM_REASON_OK
            self.sendQuickStartRes(userId, clientId, result)
            return -onlineSeatId

        isOk, reason = self._checkSitCondition(userId)
        if not isOk:
            result["isOK"] = False
            result["reason"] = reason
            self.sendQuickStartRes(userId, clientId, result)
            return 0

        # 按指定座位坐下，如果座位上有人则随机分配座位。
        if seatIndex >= 0 and seatIndex < self.maxSeatN:
            if self.seats[seatIndex].isEmptySeat():
                return seatIndex + 1
            else:
                ftlog.warn("seatIndex >=0 but not self.seats[seatIndex].isEmptySeat()",
                           "|userId, roomId, tableId, seatIndex:", userId, self.table.roomId, self.table.tableId,
                           seatIndex,
                           caller=self)

        idleSeatId = self.findIdleSeat(userId)

        if idleSeatId < 0:
            # 断线重连机制出错了??
            # 已经在座位上坐下, 返回成功消息和桌子信息
            ftlog.warn("idleSeatId < 0",
                       "|userId, roomId, tableId, idleSeatId:", userId, self.table.roomId, self.table.tableId,
                       idleSeatId,
                       caller=self)
            result["seatId"] = abs(idleSeatId)
            result["reason"] = TYRoom.ENTER_ROOM_REASON_OK
            self.sendQuickStartRes(userId, clientId, result)
            return idleSeatId

        if idleSeatId == 0:  # 座位已经满了, 返回失败消息
            ftlog.warn("idleSeatId == 0",
                       "|userId, roomId, tableId, idleSeatId:", userId, self.table.roomId, self.table.tableId,
                       idleSeatId,
                       caller=self)
            result["isOK"] = False
            result["reason"] = TYRoom.ENTER_ROOM_REASON_TABLE_FULL
            if userId not in self.observers:  # 玩家从旁观状态点坐下排队，不下发quick_start
                self.sendQuickStartRes(userId, clientId, result)
            return 0

        return idleSeatId

    def onSitOk(self, userId, idleSeatId, result):
        '''坐下条件成功后的处理
        '''
        if ftlog.is_debug():
            ftlog.debug('onSitOk << |userId, tableId, seatId:', userId, self.tableId, idleSeatId,
                        "|observers:", self.observers, caller=self)

        # 设置玩家坐在座位上
        seat = self.table.seats[idleSeatId - 1]
        seat.userId = userId
        seat.setWaitingState()
        if ftlog.is_debug():
            ftlog.debug("|seats:", self.table.seats, caller=self)

        if userId in self.table.observers:
            del self.table.observers[userId]
            onlinedata.removeOnlineLoc(userId, self.roomId, self.tableId)

        # 设置玩家的在线状态
        if ftlog.is_debug():
            ftlog.debug("before addOnlineLoc. |tableId, onlineSeatId:", self.tableId,
                        onlinedata.getOnlineLocSeatId(userId, self.roomId, self.tableId), caller=self)
        onlinedata.addOnlineLoc(userId, self.roomId, self.tableId, idleSeatId)
        if ftlog.is_debug():
            ftlog.debug("after addOnlineLoc. |tableId, onlineSeatId:", self.tableId,
                        onlinedata.getOnlineLocSeatId(userId, self.roomId, self.tableId), caller=self)

        result["seatId"] = idleSeatId
        result["reason"] = TYRoom.ENTER_ROOM_REASON_OK

        ftlog.hinfo('onSitOk >> |userId, tableId, seatId:', userId, self.tableId, idleSeatId,
                    "|observers:", self.observers, caller=self)

    def _playerSit(self, player):
        player.initInfo()
        player.wait()
        if player.isRobotUser:
            player.ready()

    def _doSit(self, msg, userId, seatId, clientId):
        '''
        玩家操作, 尝试在当前的某个座位上坐下
        '''
        if ftlog.is_debug():
            ftlog.info("_doSit << |tableId, userId, seatId:", self.tableId, userId, seatId, caller=self)

        if ftlog.is_debug():
            locList = onlinedata.getOnlineLocList(userId)
            ftlog.debug(self._baseLogStr("<<", userId), "|locList:", locList, caller=self)

        result = {"isOK": True, "userId": userId, "gameId": self.gameId, "roomId": self.bigRoomId,
                  "tableId": self.tableId}

        idleSeatId = self._getValidIdleSeatId(userId, seatId - 1, result)

        if idleSeatId < 0:
            # self.room.sendTableClothRes(self.gameId, userId, self.tableType, self.tableTheme)
            self.sendTableInfoRes(result["seatId"], userId)
            self._onReSit(userId, -idleSeatId, clientId)
            return result

        if idleSeatId == 0:
            return result

        # rid, tid, sid = getOnlineLoc(userId, self.gameId)

        # 为了支持并发坐下，self.getValidIdleSeatId()到此函数执行前，不应该有异步操作
        self.onSitOk(userId, idleSeatId, result)

        # if rid == 0: #旁观坐下时rid!=0
        #     TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_USER_FIRST_SIT', params={
        #                 'table': self, 'userId': userId}), self.gameId)

        player = self.players[idleSeatId - 1]
        self._playerSit(player)

        self.sendQuickStartRes(userId, clientId, result)
        self.sendTableInfoRes(result["seatId"], userId)

        # 发送 newUser 消息, 客户端通过该协议显示新玩家
        mpNewUserRes = self.createMsgPackRes("newUser")
        playerInfo = player.getInfo()
        mpNewUserRes.updateResult(playerInfo)
        self.sendToAllTableUser(mpNewUserRes, exclude=[userId])

        # 扩展事件.
        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd=PluginEvents.EV_AFTER_SITDOWN, params=TYPluginUtils.mkdict(
            table=self, userId=userId, player=player)), self.gameId)

        if ftlog.is_debug():
            ftlog.debug(self._baseLogStr(">>", userId), "|locList:", onlinedata.getOnlineLocList(userId), caller=self)

        ftlog.hinfo("_doSit >> get new seat, |tableId, userId, seatId:",
                    self.tableId, userId, player.seatId, caller=self)
        return result

    ################# 离开牌桌 ###################

    def _playerStandUp(self, player):
        pass

    def onStandUpOk(self, userId, seatId):
        '''坐下条件成功后的处理
        note: 站起后没有自动进入旁观列表
        '''
        if ftlog.is_debug():
            ftlog.debug('<< |userId, tableId, seatId:', userId, self.tableId, seatId, caller=self)
        # 清理在线信息
        onlinedata.removeOnlineLoc(userId, self.roomId, self.tableId)

        seat = self.table.seats[seatId - 1]
        seat.userId = 0

        ftlog.hinfo('onStandUpOk >> |userId, tableId, seatId:', userId, self.tableId, seatId,
                    "|observers:", self.observers, caller=self)

    def _doStandUp(self, msg, userId, seatId, reason, clientId):
        '''
        玩家操作, 尝试离开当前的座位
        子类需要自行判定userId和seatId是否吻合
        '''
        if ftlog.is_debug():
            ftlog.debug(self._baseLogStr("<<", userId), "|seatId, locList:", seatId,
                        onlinedata.getOnlineLocList(userId), caller=self)

        seatIndex = seatId - 1
        player = self.players[seatIndex]
        result = {"isOK": True, "userId": userId, "gameId": self.gameId, "roomId": self.roomId, "tableId": self.tableId}
        if player.userId != userId:
            ftlog.warn('the seat userId not match userId=', userId, 'seat.userId=', player.userId, caller=self)
            return result

        player = self.players[seatId - 1]
        self._playerStandUp(player)
        self.onStandUpOk(userId, seatId)

        mpStandUpRes = self.createMsgPackRes("standup")
        mpStandUpRes.setResult("reason", reason)
        mpStandUpRes.setResult("seatId", seatIndex)
        mpStandUpRes.setResult("userId", userId)
        self.sendToAllTableUser(mpStandUpRes)

        if ftlog.is_debug():
            ftlog.debug(self._baseLogStr(">>", userId), "|locList:", onlinedata.getOnlineLocList(userId), caller=self)
        return result

    def _doLeave(self, msg, userId, clientId):
        '''
        玩家操作, 尝试离开当前的桌子
        实例桌子可以覆盖 _doLeave 方法来进行自己的业务逻辑处理
        '''
        ftlog.hinfo(self._baseLogStr("_doLeave <<", userId), "|msg, observers:", msg, self.observers, caller=self)

        gameId = msg.getParam("gameId", 0)
        if gameId and gameId != self.gameId:
            ftlog.warn("_doLeave gameId != self.gameId", userId, gameId, clientId)
            return {"isOK": False, "reason": TYRoom.LEAVE_ROOM_REASON_SYSTEM}

        reason = msg.getParam("reason", TYRoom.LEAVE_ROOM_REASON_ACTIVE)

        # if reason == TYRoom.LEAVE_ROOM_REASON_LOST_CONNECTION:
        #     self.sendPlayerDataToAll(userId, managed=True)
        #     return {"isOK": False, "reason": reason}

        if ftlog.is_debug():
            ftlog.debug(self._baseLogStr("<<", userId), "|locList:", onlinedata.getOnlineLocList(userId), caller=self)

        result = {"isOK": True, "userId": userId, "gameId": self.gameId, "roomId": self.roomId, "tableId": self.tableId}

        player = self.getPlayer(userId)
        if player:
            self._doStandUp(msg, userId, player.seatId, reason, clientId)

        if userId in self.observers:
            del self.observers[userId]
            onlinedata.removeOnlineLoc(userId, self.roomId, self.tableId)
        if ftlog.is_debug():
            ftlog.debug(self._baseLogStr(">>", userId), "|locList:", onlinedata.getOnlineLocList(userId),
                        "|observers:", self.observers, caller=self)

        mpRes = self.createMsgPackRes("table_leave")
        mpRes.setResult("reason", reason)
        mpRes.setResult("userId", userId)
        router.sendToUser(mpRes, userId)

        if ftlog.is_debug():
            ftlog.info(self._baseLogStr("_doLeave >>", userId), "|reason, observers:", reason, self.observers,
                       caller=self)

        TYPluginCenter.evmsg(self.gameId, PluginEvents.EV_LEAVE_TABLE, {
            'table': self, 'userId': userId, 'reason': reason
        })

        return result

    ################# 功能 ###################

    def callLaterFunc(self, interval, func, userId=0, timer=None, msgPackParams=None):
        '''延时调用table对象的一个函数
           原理：延时调用table.doTableCall命令，通过此命令调用table对象的一个函数
           意义：table.doTableCall函数会锁定table对象，保证数据操作的同步性
        '''

        if msgPackParams == None:
            msgPackParams = {}
        msgPackParams["userId"] = userId
        clientId = sessiondata.getClientId(userId) if userId > 0 else None
        msgPackParams["clientId"] = clientId
        msgPackParams["func"] = func
        action = "CL_FUNC"

        if timer == None:
            timer = TYTableTimer(self)
        timer.setup(interval, action, msgPackParams, cancelLastTimer=False)

        funcName = func.func.func_name
        if ftlog.is_debug():
            ftlog.debug(">> |clientId, userId, tableId:", clientId, userId, self.tableId,
                        "|action, func, interval:", action, funcName, interval, caller=self)


            # def doTableChat(self, suid, chatMsg):
            #     msg = TYPluginUtils.updateMsg(cmd='EV_TABLE_CHAT', params=TYPluginUtils.mkdict(
            #         table=self, suid=suid, chatMsg=chatMsg))
            #     TYPluginCenter.event(msg, self.gameId)
