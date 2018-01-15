# coding=UTF-8
'''升级打通关房间类
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import json
import random
import time
from collections import OrderedDict

import freetime.util.log as ftlog
from freetime.core.lock import FTLock
from freetime.core.timer import FTTimer
from freetime.entity.msg import MsgPack
from freetime.util.log import getMethodName, catchedmethod
from poker.entity.configure import gdata
from poker.entity.dao import onlinedata, gamedata
from poker.entity.game.plugin import TYPluginCenter
from poker.entity.game.rooms.player_room_dao import PlayerRoomDao
from poker.entity.game.rooms.room import TYRoom
from poker.protocol import router


class TYDTGQueueScheduler(object):
    '''队列调度器类'''

    STATE_IDLE = 0
    STATE_LOOP = 1

    QUEUE_STATE_STRS = {
        STATE_IDLE: "STATE_IDLE",
        STATE_LOOP: "STATE_LOOP",
    }

    def getStateStr(self):
        return self.QUEUE_STATE_STRS[self._state]

    def __init__(self, room):
        self.room = room
        self.locker = FTLock(self.__class__.__name__ + "_%d" % id(self))

        self._state = self.STATE_IDLE  # 玩家从队列分配到牌桌过程中，不允许玩家leave room，以免造成开局缺人问题。

        # 初始化玩家和牌桌对列
        self.users = OrderedDict()
        self.activeTableIds = set()
        self._initIdleTableIds()

        # 优化性能的辅助存储
        self.pairUsers = OrderedDict()  # 有序双人队列
        # 单人玩家分组, 四维数组, 第一维表示上局是否获胜, 第二维表示玩家打几(级牌数-2), 第三维表示玩家下局是否该当庄, 第四维是userIds
        self.singleUserGroup = [[[OrderedDict() for z in xrange(2)] for y in xrange(14)] for x in xrange(2)]
        # 双人玩家分组, 三维数组, 第一维表示上局是否获胜, 第二维表示玩家打几(级牌数-2), 第四维是userIdPairs
        self.pairUserGroup = [[[OrderedDict() for z in xrange(2)] for y in xrange(14)]]  # 双人玩家队列分组

    def baseLogStr(self, tableId=None, userId=None):
        room_info = "|roomId: %s" % self.room.roomId
        if ftlog.is_debug():
            queue_info = '|queues: u%d %s t%d %s' % (
                len(self.users), self.users.keys(), len(self.idleTableIds), self.getStateStr())
        else:
            queue_info = '|queues: u%d t%d %s' % (len(self.users), len(self.idleTableIds), self.getStateStr())
        table_info = '' if not tableId else '|table: %s' % (tableId)
        user_info = '' if not userId else '|userId: %s' % (userId)

        return self.__class__.__name__ + room_info + queue_info + table_info + user_info

    def _initIdleTableIds(self):
        self.idleTableIds = []
        shadowRoomIds = self.room.roomDefine.shadowRoomIds
        if ftlog.is_debug():
            ftlog.debug("<<", self.baseLogStr(), '|shadowRoomIds=', list(shadowRoomIds))
        for shadowRoomId in shadowRoomIds:
            for i in xrange(self.room.roomDefine.configure['gameTableCount']):
                self.idleTableIds.append(shadowRoomId * 10000 + i + 1)
        random.shuffle(self.idleTableIds)
        if ftlog.is_debug():
            ftlog.debug("_initIdleTableIds >>", self.baseLogStr(), '|len(shadowRoomIds), len(idleTableIds):',
                        len(shadowRoomIds), len(self.idleTableIds))

    def enter(self, userId):
        '''玩家进入队列'''
        if self.users.get(userId) != None:
            ftlog.error(getMethodName(), "already in queue!", self.baseLogStr(None, userId))
            return False

        onlinedata.addOnlineLoc(userId, self.room.roomId, self.room.roomId * 10000, 1)

        cardLevel, isWinner, isToBeBanker = \
            gamedata.getGameAttrs(userId, self.room.gameId, ["cardLevel", "isWinner", "isToBeBanker"])

        if cardLevel == None:  # 新玩家, 必须初始化cardLevel
            cardLevel, isWinner, isToBeBanker = 2, False, False
            gamedata.setGameAttrs(userId, self.room.gameId, ["cardLevel", "isWinner", "isToBeBanker"],
                                  [2, False, False])

        # 修改users数据的代码段中不允许有异步操作
        self.users[userId] = {"enterTime": time.time()}
        self.users[userId]["cardLevel"], self.users[userId]["isWinner"], self.users[userId]["isToBeBanker"] = \
            cardLevel, isWinner, isToBeBanker

        self.matchTeamMate(userId)

        if ftlog.is_debug():
            ftlog.debug(">>", self.baseLogStr(None, userId),
                        "|self.users[userId]:", self.users[userId],
                        "|locList:", onlinedata.getOnlineLocList(userId), caller=self)
        return True

    def leave(self, userId):
        '''玩家离开队列'''

        # 只有玩家在队列里时才锁队列并删除他
        if userId in self.users:
            teamMate = self.users[userId].get("teamMate")
            if teamMate:
                if ftlog.is_debug():
                    ftlog.debug(self.baseLogStr(None, userId), "|teamMate, self.users[teamMate]:",
                                teamMate, self.users[teamMate], caller=self)
                del self.users[teamMate]["teamMate"]
            del self.users[userId]
            onlinedata.removeOnlineLoc(userId, self.room.roomId, self.room.roomId * 10000)

        if ftlog.is_debug():
            ftlog.debug(">>", self.baseLogStr(None, userId),
                        "|locList:", onlinedata.getOnlineLocList(userId), caller=self)
        return True

    def startLoop(self):
        self._state = self.STATE_LOOP
        FTTimer(1, self.doHeartBeat)
        ftlog.info("startLoop >>", self.baseLogStr(), caller=self)

    def cancelLoop(self):
        self._state = self.STATE_IDLE
        ftlog.info("cancelLoop >>", self.baseLogStr(), caller=self)

    def _tryStartNewTable(self, playerIds):
        # 开桌
        ftlog.hinfo("_tryStartNewTable", self.baseLogStr(None, None), '|playerIds:', playerIds)

        if len(self.idleTableIds) == 0:
            ftlog.error(self.baseLogStr(None, None), 'idle tables not enough')
            return

        # 决定打几和庄家
        params = {}
        params["bankerSeatIndex"] = -1
        params["cardLevel"] = 2
        for seatIndex, userId in enumerate(playerIds):
            if self.users[userId]["cardLevel"] > params["cardLevel"]:
                params["cardLevel"] = self.users[userId]["cardLevel"]
            if self.users[userId]["isWinner"] and \
                    (self.users[userId]["isToBeBanker"] or params["bankerSeatIndex"] == -1):
                params["bankerSeatIndex"] = seatIndex
            del self.users[userId]

        tableId = self.idleTableIds.pop()
        self.activeTableIds.add(tableId)
        shadowRoomId = tableId / 10000
        self.room.sendTableManageGameStartReq(shadowRoomId, tableId, playerIds, params=params)

    def _startTable(self, tableId, playerIds, cardLevel):
        # 开桌
        ftlog.hinfo("_startTable", self.baseLogStr(None, None), '|tableId, playerIds:', tableId, playerIds)

        params = {}
        params["bankerSeatIndex"] = -1
        params["cardLevel"] = cardLevel
        for userId in playerIds:
            del self.users[userId]

        shadowRoomId = tableId / 10000
        self.room.sendTableManageGameStartReq(shadowRoomId, tableId, playerIds, params=params)

    @catchedmethod
    def _recycleTable(self, tableId):
        shadowRoomId = tableId / 10000
        resultStr = self.room.queryTableManageClearPlayersReq(shadowRoomId, tableId)
        if resultStr:
            result = json.loads(resultStr)
            if ftlog.is_debug():
                ftlog.debug("|result:", result, caller=self)
        self.idleTableIds.append(tableId)
        self.activeTableIds.remove(tableId)

    def adjustTablePlayers(self, msg):
        '''一局游戏结束, 调整牌桌玩家，拆桌或者拉人'''
        tableId = msg.getParam("tableId")
        playersN = msg.getParam("playersN")
        cardLevel = msg.getParam("cardLevel")
        isWinner = msg.getParam("isWinner")

        if ftlog.is_debug():
            ftlog.debug("<<", self.baseLogStr(tableId), '|msg:', msg, caller=self)

        if playersN == 3:  # 三缺一
            for userId in self.users:
                if self.users[userId].get("teamMate") == None and \
                                self.users[userId]["isWinner"] != isWinner and \
                                self.users[userId]["cardLevel"] == cardLevel:
                    self._startTable(tableId, [userId], cardLevel)
                    return
        elif playersN == 2:  # 缺对手
            for userId in self.users:
                teamMate = self.users[userId].get("teamMate")
                if teamMate != None and \
                                self.users[userId]["isWinner"] != isWinner and \
                                self.users[userId]["cardLevel"] == cardLevel:
                    self._startTable(tableId, [userId, teamMate], cardLevel)
                    return

        # 拉人失败,通知GT拆桌
        self._recycleTable(tableId)

    def notifyRobot(self, robotN=1):
        if ftlog.is_debug():
            ftlog.debug("<< |roomId:", self.room.roomId, caller=self)

        if self.room.roomConf.get('hasrobot'):
            mo = MsgPack()
            mo.setCmd('robotmgr')
            mo.setAction('callmatch')
            mo.setParam('gameId', self.room.gameId)
            mo.setParam('roomId', self.room.roomId)
            mo.setParam('robotCount', robotN)
            router.sendRobotServer(mo)

    def doHeartBeat(self):
        if ftlog.is_debug():
            ftlog.debug("<<", self.baseLogStr(), caller=self)

        if self._state == self.STATE_IDLE:
            return

        if self._state == self.STATE_LOOP:
            self.doLoop()
            FTTimer(1, self.doHeartBeat)

    @catchedmethod
    def doLoop(self):

        if ftlog.is_debug():
            ftlog.debug("<<", self.baseLogStr(), caller=self)

        if len(self.users) == 0:
            return

        nowTime = time.time()
        for firstUserId in self.users.keys():
            teamMate = self.users[firstUserId].get("teamMate")

            if ftlog.is_debug():
                ftlog.debug("", self.baseLogStr(None, firstUserId),
                            "|self.users[firstUserId]:", self.users[firstUserId], caller=self)

            if teamMate:  # 有好基友的幸福人儿
                maxCardLevel = max(self.users[firstUserId]["cardLevel"], self.users[teamMate]["cardLevel"])
                opponent = self.findOpponent(firstUserId, maxCardLevel)
                if opponent:
                    if ftlog.is_debug():
                        ftlog.debug("find opponent", self.baseLogStr(None, firstUserId),
                                    "|strictLevel:", 0,
                                    "|self.users[firstUserId]:", self.users[firstUserId],
                                    "|self.users[opponent]:", self.users[opponent], caller=self)
                    self._tryStartNewTable([firstUserId, teamMate, opponent, self.users[opponent]["teamMate"]])
                    return

                if nowTime - self.users[firstUserId]["enterTime"] > self.room.roomConf.get("waitTime", 15):
                    for strictLevel in xrange(1, 13):
                        opponent = self.findOpponent(firstUserId, maxCardLevel, strictLevel)
                        if opponent:
                            if ftlog.is_debug():
                                ftlog.debug("find opponent", self.baseLogStr(None, firstUserId),
                                            "|strictLevel:", strictLevel,
                                            "|self.users[firstUserId]:", self.users[firstUserId],
                                            "|self.users[opponent]:", self.users[opponent], caller=self)
                            self._tryStartNewTable([firstUserId, opponent, teamMate, self.users[opponent]["teamMate"]])
                            return
            else:  # 单身汪
                if nowTime - self.users[firstUserId]["enterTime"] > self.room.roomConf.get("waitTime", 15):
                    for strictLevel in xrange(1, 3):
                        if self.matchTeamMate(firstUserId, strictLevel):
                            if ftlog.is_debug():
                                ftlog.debug("matchTeamMate", self.baseLogStr(None, firstUserId),
                                            "|strictLevel:", strictLevel,
                                            "|self.users[firstUserId]:", self.users[firstUserId], caller=self)
                            return

    def matchTeamMate(self, userId, strictLevel=0):
        '''抓队友, strictLevel从1开始最严,数字越大越松
           锁住队列, 避免并发操作时数据冲突
        '''
        teamMate = self.findTeamMateWithStrictLevel(userId, strictLevel)

        if teamMate:
            self.users[userId]["teamMate"] = teamMate
            self.users[teamMate]["teamMate"] = userId

            if ftlog.is_debug():
                ftlog.debug(">>", self.baseLogStr(None, userId),
                            "|self.users[userId]:", self.users[userId],
                            "|self.users[teamMate]:", self.users[teamMate], caller=self)

            return True

        return False

    def findTeamMateWithStrictLevel(self, userId, strictLevel):
        for teamMate in self.users:
            if teamMate != userId and self.users[teamMate].get("teamMate") == None and \
                            self.users[userId]["isWinner"] == self.users[teamMate]["isWinner"]:
                if strictLevel == 2:
                    return teamMate
                if self.users[userId]["cardLevel"] == self.users[teamMate]["cardLevel"]:
                    if strictLevel == 1:
                        return teamMate
                    if self.users[userId]["isWinner"] == False:  # 打2的人isWinner都为False
                        return teamMate
                    elif self.users[userId]["isToBeBanker"] != self.users[teamMate]["isToBeBanker"]:
                        return teamMate

        return None

    def findOpponent(self, userId, maxCardLevel, strictLevel=0):
        '''抓对手, strictLevel从0开始最严,数字越大越松
        '''
        for opponent in self.users:
            if opponent != userId and opponent != self.users[userId]["teamMate"]:
                opponentTeamMate = self.users[opponent].get("teamMate")
                if opponentTeamMate:
                    opponentMaxCardLevel = max(self.users[opponent]["cardLevel"],
                                               self.users[opponentTeamMate]["cardLevel"])

                    if abs(maxCardLevel - opponentMaxCardLevel) == strictLevel:
                        if self.users[userId]["cardLevel"] == 2:
                            return opponent
                        if self.users[userId]["isWinner"] != self.users[opponent]["isWinner"]:
                            return opponent

        return None


class TYDTGRoom(TYRoom):
    '''打通关房间类

    Attributes:
        scheduler: 队列调度器
        _roomUsers: 进入房间的玩家集合
    '''

    def __init__(self, roomDefine):
        super(TYDTGRoom, self).__init__(roomDefine)
        serverType = gdata.serverType()
        if serverType == gdata.SRV_TYPE_ROOM:
            self._initScheduler()
            self._roomUsers = set()

    def _baseLogStr(self, des="", userId=None):
        baseRoomInfo = '%s |roomId: %d' % (des, self.roomId)
        baseUserInfo = '' if not userId else ' |userId: %d' % (userId)
        return self.__class__.__name__ + " " + baseRoomInfo + baseUserInfo

    def _initScheduler(self):
        self.scheduler = TYDTGQueueScheduler(self)
        self.scheduler.startLoop()

    def _tableType(self):
        return {'isUpdate': True}

    def _tableTheme(self):
        return "update"

    def checkSitCondition(self, userId):
        '''队列房间的准入条件靠quick_start模块和queue_table模块分别判断， 按产品需求两者标准不同'''
        msg = TYPluginCenter.evmsg(self.gameId, 'EV_CHECK_ENTER_ROOM_CONDITION',
                                   params={'userId': userId, 'room': self})

        reason = msg.getResult("reason")
        if reason and reason != TYRoom.ENTER_ROOM_REASON_OK:
            return False, reason

        return True, TYRoom.ENTER_ROOM_REASON_OK

    def _enter(self, userId):
        ftlog.hinfo("_enter << |roomId, userId, _roomUsersN: ", self.roomId, userId, len(self._roomUsers), caller=self)

        isOk, checkResult = self.checkSitCondition(userId)
        if not isOk:
            return False, checkResult

        if userId in self._roomUsers:
            return False, TYRoom.ENTER_ROOM_REASON_CONFLICT

        if not self.scheduler.enter(userId):
            return False, TYRoom.ENTER_ROOM_REASON_CONFLICT

        self._roomUsers.add(userId)

        if ftlog.is_debug():
            ftlog.debug(">> |roomId, userId, _roomUsersN: ", self.roomId, userId, len(self._roomUsers), caller=self)
            ftlog.debug("|roomId, userId, _roomUsers: ", self.roomId, userId, self._roomUsers, caller=self)
            locList = onlinedata.getOnlineLocList(userId)
            ftlog.debug("|roomId, userId, locList:", self.roomId, userId, locList)

        PlayerRoomDao.clear(userId, self.bigRoomId)  # 防止因系统错误造成的数据遗留问题

        return True, TYRoom.ENTER_ROOM_REASON_OK

    def _leave(self, userId, reason, needSendRes):
        ftlog.hinfo("_leave << |roomId, userId, _roomUsersN, reason: ", self.roomId, userId, len(self._roomUsers),
                    reason, caller=self)
        if ftlog.is_debug():
            ftlog.debug("<< |roomId, userId, _roomUsers: ", self.roomId, userId, self._roomUsers, caller=self)
            ftlog.debug("<< |roomId, userId, scheduler.users: ", self.roomId, userId, self.scheduler.users.keys(),
                        caller=self)

        if reason == TYRoom.LEAVE_ROOM_REASON_LOST_CONNECTION:
            return False

        if not userId in self._roomUsers:
            locList = onlinedata.getOnlineLocList(userId)
            if locList:
                ftlog.error("_leave >> not userId in self._roomUsers ",
                            "|roomId, userId, _roomUsersN: ", self.roomId, userId, len(self._roomUsers))
                self._remoteTableLeave(userId, reason, locList)
            return True

        # if userId in self.scheduler.sittingUsers:  # 从队列分配玩家进牌桌时，该玩家不允许离开队列。
        #     ftlog.warn("can't leave when start table!", caller=self)
        #     return False

        if userId not in self.scheduler.users:
            self._remoteTableLeave(userId, reason)

        if userId in self.scheduler.users:
            self.scheduler.leave(userId)
            self._onLeaveQueueOk(userId)

        self._roomUsers.remove(userId)

        if ftlog.is_debug():
            ftlog.debug(">> |roomId, userId, _roomUsersN: ", self.roomId, userId, len(self._roomUsers), caller=self)
            ftlog.debug(">> |roomId, userId, _roomUsers: ", self.roomId, userId, self._roomUsers, caller=self)

        PlayerRoomDao.clear(userId, self.bigRoomId)

        return True

    def _onLeaveQueueOk(self, userId):
        pass

    def doQuickStart(self, msg):
        assert self.roomId == msg.getParam("roomId")

        userId = msg.getParam("userId")
        shadowRoomId = msg.getParam("shadowRoomId")
        tableId = msg.getParam("tableId")
        clientId = msg.getParam("clientId")
        ftlog.hinfo("doQuickStart <<", "|userId, clientId, roomId, shadowRoomId, tableId:", userId, clientId,
                    self.roomId, shadowRoomId, tableId)

        # msg = TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_QUICK_START', params=TYPluginUtils.mkdict(
        #     userId=userId, roomId=self.roomId), result={}), self.gameId)
        #
        # if msg.getResult("reason") != None:
        #     info = u'玩家需要验证'
        #     self.sendQuickStartRes(self.gameId, userId, msg.getResult("reason"), self.bigRoomId, 0, info)
        #     return

        if tableId == 0:
            isOk, reason = self.doEnter(userId)
        elif tableId == self.roomId * 10000:
            if userId in self._roomUsers:
                isOk = True  # 玩家在队列里时断线重连
                reason = TYRoom.ENTER_ROOM_REASON_OK
            else:  # 服务器重启造成玩家已经不在房间对象里了
                onlinedata.removeOnlineLoc(userId, self.roomId, tableId)
                isOk = False
                reason = TYRoom.ENTER_ROOM_REASON_CONFLICT
        else:  # 防御性代码，处理快速开始online错乱
            onlineSeat = onlinedata.getOnlineLocSeatId(userId, shadowRoomId, tableId)
            if onlineSeat == 0:  # 断线重连过程中玩家因为超时、金币不足或比赛淘汰等原因已被踢出房间
                isOk = False
                reason = TYRoom.ENTER_ROOM_REASON_CONFLICT
                ftlog.warn("doQuickStart conflict!", "|userId, onlineLocList:", userId,
                           onlinedata.getOnlineLocList(userId),
                           "|shadowRoomId, tableId:", shadowRoomId, tableId)
            else:
                ftlog.error("doQuickStart conflict!", "|onlineSeat:", onlineSeat)
                if onlineSeat == gdata.roomIdDefineMap()[shadowRoomId].configure['tableConf']['maxSeatN'] + 1:
                    # 牌桌里旁观的玩家断线重连，请求转给GT
                    self.sendTableCallObserveReq(userId, shadowRoomId, tableId, clientId)
                elif onlineSeat > 0:
                    # 牌桌里坐着的玩家断线重连，请求转给GT
                    self.querySitReq(userId, shadowRoomId, tableId, clientId)
                return

        if isOk:
            self._onQuickStartOk(userId)
        elif reason == TYRoom.ENTER_ROOM_REASON_CONFLICT:
            info = u'玩家已经在游戏中，状态冲突'
            self.sendQuickStartRes(self.gameId, userId, reason, self.bigRoomId, 0, info)
        else:
            self.sendQuickStartRes(self.gameId, userId, reason, self.bigRoomId, 0, '')

    def _onQuickStartOk(self, userId):
        self.sendQuickStartRes(self.gameId, userId, TYRoom.ENTER_ROOM_REASON_OK, self.bigRoomId)
        self.sendTableClothRes(self.gameId, userId, self._tableType(), self._tableTheme())

    def doAdjustTablePlayers(self, msg):
        self.scheduler.adjustTablePlayers(msg)

    def doReturnQueue(self, userId):
        '''玩家换桌时返回队列'''
        if ftlog.is_debug():
            ftlog.debug("<< |roomId, userId, _roomUsersN: ", self.roomId, userId, len(self._roomUsers), caller=self)
        if not userId in self._roomUsers:
            return False

        if not self.scheduler.enter(userId):
            return False

        if ftlog.is_debug():
            ftlog.debug(">> |roomId, userId, _roomUsersN: ", self.roomId, userId, len(self._roomUsers), caller=self)
            ftlog.debug(">> |roomId, userId, _roomUsers: ", self.roomId, userId, self._roomUsers, caller=self)
        if ftlog.is_debug():
            locList = onlinedata.getOnlineLocList(userId)
            ftlog.debug(">> |roomId, userId, locList:", self.roomId, userId, locList, caller=self)

        return True
