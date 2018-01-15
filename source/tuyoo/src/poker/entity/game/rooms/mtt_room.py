# coding=UTF-8
'''MTT（Multi-Table Tournament, 多桌赛）房间类
'''
import functools
import random
import time

from freetime.core.timer import FTTimer
from freetime.util.log import getMethodName
from poker.entity.biz import bireport
from poker.entity.dao import daobase
from poker.entity.dao import userdata, onlinedata
from poker.entity.game.rooms.mtt_ctrl.ranking import Ranking
from poker.entity.game.rooms.player_room_dao import PlayerRoomDao
from poker.util import strutil

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

from datetime import datetime, timedelta

import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack

from poker.protocol import router
from poker.entity.configure import gdata
from poker.entity.game.rooms.room import TYRoom
from poker.entity.game.rooms.queue_room import TYQueueScheduler, TYQueueRoom
from poker.entity.game.plugin import TYPluginUtils, TYPluginCenter


class TYSMttQueueScheduler(TYQueueScheduler):
    '''SNG队列调度器类
    
    Attributes:
        _state : 队列管理器状态， 
           STATE_IDLE 队列空闲状态，即关闭循环调度；
           STATE_LOOP 队列开启循环调度状态。
    Configure：
      
    '''

    def shuffleQueue(self):
        # 随机把一个玩家移到队尾，操作N次
        ftlog.debug("shulffQueue << |self.users.keys():", self.baseLogStr(), self.users.keys(), caller=self)
        userIds = self.users.keys()
        random.shuffle(userIds)
        for userId in userIds:
            enterTime = self.users[userId]["enterTime"]
            del self.users[userId]
            self.users[userId] = {"enterTime": enterTime}
        ftlog.debug("shulffQueue << |self.users.keys():", self.baseLogStr(), self.users.keys(), caller=self)

    def startLoop(self, needShuffleQueue=True):

        ftlog.hinfo("startLoop <<", self.baseLogStr(),
                    "|needShuffleQueue:", needShuffleQueue, caller=self)

        if needShuffleQueue:
            self.shuffleQueue()

        while len(self.users) >= self.n_start * 3:
            self._tryStartNewTable(self.n_start)

        leftQueueLen = len(self.users)
        if leftQueueLen > self.n_start * 2:
            oneThirdQueueLen = leftQueueLen / 3
            if ftlog.is_debug():
                ftlog.info(self.baseLogStr(), 'divice last three tables.',
                           '|leftQueueLen, oneThirdQueueLen:', leftQueueLen, oneThirdQueueLen)
            self._tryStartNewTable(oneThirdQueueLen)

            leftQueueLen -= oneThirdQueueLen
            halfQueueLen = leftQueueLen / 2
            if ftlog.is_debug():
                ftlog.info(self.baseLogStr(), 'deuce last two tables.',
                           '|leftQueueLen, halfQueueLen:', leftQueueLen, halfQueueLen)
            self._tryStartNewTable(halfQueueLen)
            self._tryStartNewTable(leftQueueLen - halfQueueLen)

        elif leftQueueLen > self.n_start:
            halfQueueLen = leftQueueLen / 2
            if ftlog.is_debug():
                ftlog.info(self.baseLogStr(), 'deuce last two tables.',
                           '|leftQueueLen, halfQueueLen:', leftQueueLen, halfQueueLen)
            self._tryStartNewTable(halfQueueLen)
            self._tryStartNewTable(leftQueueLen - halfQueueLen)

        elif leftQueueLen > 0:
            self._tryStartNewTable(leftQueueLen)

        super(TYSMttQueueScheduler, self).startLoop()

    def _isValidUser(self, userId):
        return userId not in self.room.mttRebuyUsers

    def doHeartBeat(self):
        if self._state == self.STATE_IDLE:
            return

        FTTimer(1, self.doHeartBeat)

        if len(self.users) > 0:
            if ftlog.is_debug():
                ftlog.debug("<<", self.baseLogStr(), caller=self)
                #         ftlog.debug("|first user, enter time, now, wait_time:", self.users.keys()[0], self.users[self.users.keys()[0]], time.time(), self.wait_time)

        if self._state == self.STATE_LOOP:
            if len(self.users) >= self.n_start:
                self._tryStartNewTable(self.n_start)

    def adjustTablePlayers(self, msg, isFinal=False):
        '''一局游戏结束, 调整牌桌玩家，拆桌或者拉人'''
        tableId = msg.getParam("tableId")
        playersN = msg.getParam("playersN", 0)
        validSeatsN = msg.getParam("validSeatsN", self.n_start - playersN)
        if ftlog.is_debug():
            ftlog.debug("<<", self.baseLogStr(tableId), '|playersN, validSeatsN:',
                        playersN, validSeatsN, caller=self)

        if isFinal:
            self._startTable(tableId)
            return

        if playersN <= 1:
            self._recycleTable(tableId)
            if ftlog.is_debug():
                activeTableN = len(self.activeTableIds)
                playingLen = self.room.getPlayingLen()
                ftlog.debug('|roomId, activeTableN, playersN:', self.room.roomId, activeTableN, playingLen, caller=self)
            return

        activeTableN = len(self.activeTableIds)
        playingLen = self.room.getPlayingLen()
        if ftlog.is_debug():
            ftlog.debug('|roomId, activeTableN, playersN:', self.room.roomId, activeTableN, playingLen, caller=self)

        # 玩家延迟报名后，没有空桌位的特殊处理
        if len(self.users) > 0 and activeTableN * self.n_start == playingLen - len(self.users):
            self.cancelLoop()
            self._recycleTable(tableId)
            self.startLoop()
            return

        # if playersN < self.n_recycle and (activeTableN - 1) * self.n_start >= playingLen: #其他使用中的桌子有足够的座位可以让本桌的人都坐过去
        if (activeTableN - 1) * self.n_start >= playingLen:  # 人多的桌子也参与分桌
            self._recycleTable(tableId)
        else:
            averagePlayersN = (playingLen + activeTableN - 1) / activeTableN
            if ftlog.is_debug():
                ftlog.debug('|roomId, averagePlayersN, playersN:', self.room.roomId, averagePlayersN, playersN,
                            caller=self)
            if averagePlayersN > playersN:  # 牌桌加人
                self._startTable(tableId, min(averagePlayersN - playersN, validSeatsN), 0)
            else:
                self._startTable(tableId, 0, playersN - averagePlayersN)  # 牌桌减人或不变


class TYMttRoom(TYQueueRoom):
    '''MTT（Multi-Table Tournament, 多桌赛）房间类
    
    Attributes:
        state : MTT当前阶段
    '''
    MTT_STATE_IDLE = 0  # 空闲阶段
    MTT_STATE_READY = 1  # 准备阶段
    MTT_STATE_SIGNIN = 2  # 报名阶段
    MTT_STATE_ENTER = 3  # 进入阶段
    MTT_STATE_FORBIT_SIGNOUT = 4  # 禁止退赛阶段
    MTT_STATE_START = 5  # 开赛阶段
    MTT_STATE_QUALIFIER = 6  # 预选赛
    MTT_STATE_PREFINALS = 7  # 决赛准备阶段
    MTT_STATE_FINALS = 8  # 决赛
    MTT_STATE_DAY1_END = 9  # day1比赛结束

    mttStateStrs = {
        MTT_STATE_IDLE: "IDLE",  # 空闲阶段
        MTT_STATE_READY: "READY",  # 空闲阶段
        MTT_STATE_SIGNIN: "SIGNIN",  # 报名阶段
        MTT_STATE_ENTER: "ENTER",  # 进入阶段
        MTT_STATE_FORBIT_SIGNOUT: "FORBIT_SIGNOUT",  # 禁止退赛阶段
        MTT_STATE_START: "START",  # 开赛段
        MTT_STATE_QUALIFIER: "QUALIFIER",  # 预选赛
        MTT_STATE_PREFINALS: "PREFINALS",  # 决赛准备阶段
        MTT_STATE_FINALS: "FINALS",  # 决赛
        MTT_STATE_DAY1_END: "MTT_STATE_DAY1_END"  # day1比赛结束
    }

    def __init__(self, roomdefine):
        super(TYMttRoom, self).__init__(roomdefine)

        self.betsConf = None  # 盲注阶段配置，随时间而变化
        self.mttRebuyUsers = {}  # 正在等待 rebuy 的玩家
        FTTimer(0, self.__initMatch)

    def doReloadConf(self, roomDefine):
        super(TYMttRoom, self).doReloadConf(roomDefine)
        if gdata.serverType() == gdata.SRV_TYPE_ROOM and self.state < self.MTT_STATE_ENTER:
            self.matchPlugin.refreshMatchInfo(self.roomDefine)
            self.matchPlugin.refreshMatchStartTime(self.bigRoomId)
        else:
            self.configChanged = True

        if gdata.serverType() == gdata.SRV_TYPE_TABLE:
            self.matchPlugin.refreshMatchInfo(self.roomDefine)

    def __initMatch(self):
        # 老框架plugin被PluginCenter reload后XXPlugin类的id会发生变化，为了避免此问题，新框架里matchPlugin不再注册到PluginCenter
        self.matchPlugin = gdata.games()[self.gameId].getMttMatchPlugin()
        lastMatchStartTimeStamp = self.matchPlugin.getMatchStartTime(self.bigRoomId)
        self.matchPlugin.refreshMatchInfo(self.roomDefine)
        self.configChanged = False

        self.__initRedisLua()

        self.matchCounter = {}
        self.ranking = Ranking(self, 0)
        self.state = self.MTT_STATE_IDLE

        serverType = gdata.serverType()
        if serverType == gdata.SRV_TYPE_ROOM:
            nowTimeStamp = int(time.time())
            if lastMatchStartTimeStamp and nowTimeStamp + self.matchPlugin.timedeltaEnterMatch >= lastMatchStartTimeStamp:
                # 重启后房间对象数据会被清空，重启前已经进入比赛房间的玩家需要退票；
                self.matchPlugin.cancelMatch(self, isRestart=True)
            else:  # 报名信息在redis中，重启不会丢失；
                self.state = self.MTT_STATE_READY

            self.doHeartBeat()

    def __initRedisLua(self):
        k1, k2, k3 = self.matchPlugin.playingRankingKey(self.bigRoomId), \
                     self.matchPlugin.rankingKey(self.bigRoomId), \
                     self.matchPlugin.enterMatchTotalKey(self.bigRoomId)
        getPlayinLenLua = 'return {redis.call("ZCARD", "%s"), redis.call("LLEN", "%s"), redis.call("GET", "%s")}' % (
            k1, k2, k3)
        userLeaveLua = '''
        local ret = redis.call("ZREM", "%s", ARGV[1])
        if ret == 1 then
            redis.call("RPUSH", "%s", ARGV[1]);
        end

        return {redis.call("ZCARD", "%s"), redis.call("LLEN", "%s"), redis.call("GET", "%s"), ret}
        ''' % (k1, k2, k1, k2, k3)
        # self.userLeaveLua += self.getPlayinLenLua
        userSigninLua = 'redis.call("ZADD", "%s", %s, ARGV[1]);' % (
            k1, self.matchPlugin.match_room_confs[self.bigRoomId]["buyIn"])
        userDelaySigninLua = userSigninLua + 'return redis.call("INCR", "%s");' % (k3)

        # 注册脚本
        self.getPlayinLenLuaSha = daobase.loadLuaScripts("mtt_room_getPlayinLenLua_%s" % self.bigRoomId,
                                                         getPlayinLenLua)
        self.userLeaveLuaSha = daobase.loadLuaScripts("mtt_room_userLeaveLua_%s" % self.bigRoomId, userLeaveLua)
        self.userSigninLuaSha = daobase.loadLuaScripts("mtt_room_userSigninLua_%s" % self.bigRoomId, userSigninLua)
        self.userDelaySigninLuaSha = daobase.loadLuaScripts("mtt_room_userDelaySigninLua_%s" % self.bigRoomId,
                                                            userDelaySigninLua)

    def getStateStr(self):
        return self.mttStateStrs[self.state]

    #     def isMatchingState(self):
    #         return self.state >= self.MTT_STATE_QUALIFIER

    def _initScheduler(self):
        self.scheduler = TYSMttQueueScheduler(self)

    def _tableType(self):
        return {'isMtt': True}

    def _tableTheme(self):
        return "mtt"

    def checkSitCondition(self, userId):
        serverType = gdata.serverType()
        if serverType == gdata.SRV_TYPE_ROOM:
            if self.state == self.MTT_STATE_START or self.state < self.MTT_STATE_ENTER:
                return False, TYRoom.ENTER_ROOM_REASON_WRONG_TIME

        return self.matchPlugin.checkSitCondition(self.bigRoomId, userId)

    #     def doGetMatchList(self, userId, page=0, number=0, tag="all"):
    #         self.matchPlugin.getMatchList(self.gameId, userId, self.bigRoomId, page, number, tag)


    def doGetMatchStatus(self, userId):
        if self.state >= self.MTT_STATE_ENTER and self.state <= self.MTT_STATE_START:  # 此请求太耗redis，在进赛、开赛时间段先禁止响应
            return

        self.matchPlugin.mttStatus(self, userId)

    def doGetDescription(self, userId):
        if ftlog.is_debug():
            ftlog.debug("<<", "|userId, roomId:", userId, self.roomId, caller=self)

        if self.state == self.MTT_STATE_START:
            return

        match_desc = {}
        self.matchPlugin.getMatchDes(userId, self.bigRoomId, match_desc)

        # day1比赛显示day2比赛的奖励
        mconf = self.matchPlugin.match_room_confs[self.bigRoomId]
        day1EndConf = mconf.get('day1EndConf')
        if day1EndConf:
            day2BigRoomId = day1EndConf["day2BigRoomId"]
            match_desc['rank'] = self.matchPlugin.mdes[day2BigRoomId]['rank']

        TYPluginUtils.sendMessage(self.gameId, [userId], 'm_des',
                                  result={'roomId': self.bigRoomId, 'm_type': self.roomConf['typeName'],
                                          'desc': match_desc})

    def doGetRankList(self, userId, msg):
        if self.state == self.MTT_STATE_START:
            return

        self.ranking.sendToUser(userId)

    def doRoomUpdateRankOfAll(self):
        if self.state == self.MTT_STATE_START:
            return
        self.ranking.sendToAll()

    def doSignin(self, userId, signinParams):
        if ftlog.is_debug():
            ftlog.debug("<<", "|userId, roomId, signinParams:", userId, self.roomId, signinParams, caller=self)
        self.matchPlugin.signin(userId, self, signinParams)

    def doAdjustTablePlayers(self, msg):
        if ftlog.is_debug():
            ftlog.debug("<<", "|roomId, state:", self.roomId, self.getStateStr(), caller=self)

        if self.state == self.MTT_STATE_START or self.state == self.MTT_STATE_QUALIFIER:
            self.scheduler.adjustTablePlayers(msg)

        elif self.state == self.MTT_STATE_PREFINALS:
            #             tableId = msg.getParam("tableId")
            msg.setParam("playersN", 0)  # 强制回收牌桌
            self.scheduler.adjustTablePlayers(msg)

            activeTableIds = self.scheduler.activeTableIds
            ftlog.hinfo("before final |roomId:", self.roomId,
                        "|activityTables, queueUsers:", activeTableIds, self.scheduler.users.keys(),
                        caller=self)

            if len(activeTableIds) == 0 \
                    or len(self.scheduler.users) >= self.tableConf["maxSeatN"] - 1:  # 第二个条件是防御代码，为了防止有桌子没有回收时导致决赛开不了。

                if len(activeTableIds) > 0:
                    ftlog.error("before final len(activeTableIds) > 0")
                self.__startFinalTableLater()
            else:
                self.__notifyFinalTable()

        elif self.state == self.MTT_STATE_FINALS:
            self.scheduler.adjustTablePlayers(msg, isFinal=True)

        # elif self.state == self.MTT_STATE_IDLE: #recycle决赛桌
        #             self.scheduler.adjustTablePlayers(msg)
        #             self.state = self.MTT_STATE_READY

        elif self.state == self.MTT_STATE_DAY1_END:
            msg.setParam("playersN", 0)  # 强制回收牌桌
            self.scheduler.adjustTablePlayers(msg)
            day1WinnerIds = strutil.cloneData(self.scheduler.users.keys())
            self.matchPlugin.rewardEnterDay2Match(self, day1WinnerIds)
            for userId in day1WinnerIds:
                self._leave(userId, TYRoom.LEAVE_ROOM_REASON_MATCH_END, needSendRes=False)

            activeTableIds = self.scheduler.activeTableIds
            ftlog.hinfo("before day1 match end |roomId:", self.roomId,
                        "|activityTables, queueUsers:", activeTableIds, self.scheduler.users.keys(),
                        caller=self)

            # if len(activeTableIds) == 0:
            #     self.state = self.MTT_STATE_IDLE
            #     func2 = functools.partial(self.__onMatchEnd)
            #     FTTimer(0, func2) # 异步执行，否则GT会死锁

    def __notifyFinalTable(self):
        now = datetime.now()
        estimatedFinalTableStartTime = now + timedelta(
            seconds=self.tableConf["maxSeatN"] * 4 * 3 + self.matchPlugin.timedeltaStartFinalTable)
        # 每局有4轮下注，平均每人每次操作时间估计为3秒
        if ftlog.is_debug():
            ftlog.info("__notifyFinalTable |roomId, estimatedFinalTableStartTime:", self.roomId,
                       estimatedFinalTableStartTime, caller=self)
        self.__sendFinalTableInfo(estimatedFinalTableStartTime)

    def __startFinalTableLater(self):
        self.state = self.MTT_STATE_FINALS

        now = datetime.now()
        finalTableStartTime = now + timedelta(seconds=self.matchPlugin.timedeltaStartFinalTable)
        if ftlog.is_debug():
            ftlog.info("__startFinalTableLater |roomId, finalTableStartTime:", self.roomId, finalTableStartTime,
                       caller=self)
        self.__sendFinalTableInfo(finalTableStartTime)

        FTTimer(self.matchPlugin.timedeltaStartFinalTable, self.scheduler.startLoop)

    def __sendFinalTableInfo(self, finalTableStartTime):
        waitingUserIds = self.scheduler.users.keys()  # 防止处理过程中users变化导致数据不一致
        waitingUserN = len(waitingUserIds)
        if ftlog.is_debug():
            ftlog.debug("<< |roomId:", self.roomId,
                        "|waitingUserN:", waitingUserN)

        mpToClient = MsgPack()
        mpToClient.setCmd("final_table_info")
        mpToClient.setResult('gameId', self.gameId)
        mpToClient.setResult('roomId', self.bigRoomId)
        mpToClient.setResult('finalTableStartTime', time.mktime(finalTableStartTime.timetuple()))
        mpToClient.setResult('nowServerTime', int(time.time()))

        playerInfos = []
        for seatId, userId in enumerate(waitingUserIds):
            name = userdata.getAttr(userId, 'name')

            playerRoomInfo = PlayerRoomDao.getPlayerRoomRecord(userId, self.bigRoomId)
            if ftlog.is_debug():
                ftlog.debug("get playerRoomInfo |userId, tableId:", userId, self.roomId, playerRoomInfo, caller=self)

            item = {}
            item["userId"] = userId
            item["seatId"] = seatId
            item["tableChip"] = playerRoomInfo["tableChips"]
            item["name"] = name
            playerInfos.append(item)
        mpToClient.setResult("players", playerInfos)
        router.sendToUsers(mpToClient, waitingUserIds)

        self.matchPlugin.refreshBuyin(self)

        # Send final table information to monitor_mtt.py
        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_MTT_FINAL_TABLE', params={
            'roomId': self.roomId}), self.gameId)

    def _onQuickStartOk(self, userId):
        super(TYMttRoom, self)._onQuickStartOk(userId)
        self.matchPlugin.notifyQueueInfo(self, userId)

    def _leave(self, userId, reason, needSendRes):
        ftlog.hinfo("_leave << |roomId, userId, reason, state, _roomUsersN: ",
                    self.roomId, userId, reason, self.getStateStr(), len(self._roomUsers), caller=self)
        if ftlog.is_debug():
            ftlog.debug("<< |roomId, userId, _roomUsers: ", self.roomId, userId, self._roomUsers, caller=self)

        if reason == TYRoom.LEAVE_ROOM_REASON_LOST_CONNECTION:
            return False

        if self.state == self.MTT_STATE_START:
            return False

        if not userId in self._roomUsers:
            locList = onlinedata.getOnlineLocList(userId)
            if locList:
                ftlog.error("_leave >> not userId in self._roomUsers ",
                            "|roomId, userId, _roomUsersN: ", self.roomId, userId, len(self._roomUsers))
                self._remoteTableLeave(userId, reason, locList)
            return True

        if userId in self.scheduler.sittingUsers:  # 从队列分配玩家进牌桌时，该玩家不允许离开队列。
            ftlog.warn("can't leave when start table!", caller=self)
            return False

        if userId not in self.scheduler.users:
            self._remoteTableLeave(userId, reason)

        if userId in self.scheduler.users:
            self.scheduler.leave(userId)

        self._roomUsers.remove(userId)
        if ftlog.is_debug():
            ftlog.debug(">> |roomId, userId, _roomUsersN: ", self.roomId, userId, len(self._roomUsers), caller=self)
            ftlog.debug(">> |roomId, userId, _roomUsers: ", self.roomId, userId, self._roomUsers, caller=self)
        if len(self._roomUsers) < 10:
            ftlog.hinfo("_leave >> |roomId, userId, _roomUsers: ", self.roomId, userId, self._roomUsers, caller=self)

        PlayerRoomDao.clear(userId, self.bigRoomId)

        needSendRewardTodoTask = True
        if reason == TYRoom.LEAVE_ROOM_REASON_ACTIVE:
            self.matchCounter['usersLeaveMatchCount'] += 1
            needSendRewardTodoTask = False

        if self.state > self.MTT_STATE_START:
            if ftlog.is_debug():
                ftlog.debug("|needSendRewardTodoTask:", needSendRewardTodoTask, caller=self)
            self.__leaveMatch(userId, needSendRewardTodoTask=needSendRewardTodoTask)  # 此函数会检查玩家是否已经离开比赛, 主动离赛不弹奖状

        return True

    def doSignout(self, userId):
        if ftlog.is_debug():
            ftlog.debug("<<", "|userId, roomId:", userId, self.roomId, caller=self)
        self.matchPlugin.signout(userId, self)

    def doHeartBeat(self):
        '''定时循环调用，负责比赛状态转移'''

        FTTimer(1, self.doHeartBeat)

        if self.MTT_STATE_IDLE == self.state:
            return

        if self.MTT_STATE_READY == self.state:
            #             self.matchPlugin.refreshMatchStartTime(self.bigRoomId)
            self.matchPlugin.prepareNewMatch(self)  # 会改状态为 MTT_STATE_SIGNIN
            ftlog.hinfo("doHeartBeat >>", "|roomId, state, startTimeStamp:", self.roomId, self.getStateStr(),
                        self.matchPlugin.match_room_confs[self.bigRoomId].get("start_timestamp", "closed"), caller=self)
            return

        # ftlog.debug("<<", "|roomId, state:", self.roomId, self.getStateStr())
        startTimeStamp = self.matchPlugin.match_room_confs[self.bigRoomId]["start_timestamp"]
        nowTimeStamp = int(time.time())
        if nowTimeStamp % 30 == 0:
            if ftlog.is_debug():
                ftlog.info("doHeartBeat <<", "|roomId, state:", self.roomId, self.getStateStr(),
                           "|nowTimeStamp, startTimeStamp:", nowTimeStamp, startTimeStamp, caller=self)

        if self.MTT_STATE_SIGNIN == self.state:
            if nowTimeStamp + self.matchPlugin.timedeltaEnterMatch >= startTimeStamp:
                self.state = self.MTT_STATE_ENTER
                self.matchPlugin.notifyPlayersToEnterMatch(self)
                ftlog.hinfo("doHeartBeat >>", "|roomId, state:", self.roomId, self.getStateStr(), caller=self)
                return

        if self.MTT_STATE_ENTER == self.state:
            if nowTimeStamp + self.matchPlugin.timedeltaForbidSignout >= startTimeStamp:
                self.state = self.MTT_STATE_FORBIT_SIGNOUT
                self.matchPlugin.notifyPlayersToEnterMatch(self)
                ftlog.hinfo("doHeartBeat >>", "|roomId, state:", self.roomId, self.getStateStr(), caller=self)
                return

        if self.MTT_STATE_FORBIT_SIGNOUT == self.state:
            if nowTimeStamp >= startTimeStamp:
                self.matchPlugin.checkStartMatch(self)
                ftlog.hinfo("doHeartBeat >>", "|roomId, state:", self.roomId, self.getStateStr(), caller=self)
                return


                #     def clearEnterUsers(self):
                # #         if self.state >= self.MTT_STATE_START
                #         # TODO: 比赛如果开始了，需要清桌子
                # #         for activeTableId in self.scheduler.activeTableIds:
                #
                #         userList = list(self._roomUsers)
                #         for userId in userList:
                #             self._leave(userId, TYRoom.LEAVE_ROOM_REASON_MATCH_END, True)
                # #         self._roomUsers.clear()

    def getPlayingLen(self):
        """由于playing 列表有未知问题，改用enterMatchTotal - rankingLen来反推，并报异常方便查错。
        """
        # 这种方式比分别访问3次 redis 快3倍左右。访问3次redis需要将近1秒
        playingLen, rankingLen, enterMatchTotal = daobase.executeRankCmd("EVALSHA", self.getPlayinLenLuaSha, 0)

        if playingLen + rankingLen != enterMatchTotal:
            ftlog.error(getMethodName(), "playingLen + rankingLen != enterMatchTotal",
                        "|roomId, playingLen, rankingLen:", self.roomId, playingLen, rankingLen,
                        "|enterMatchTotal:", enterMatchTotal)

        if ftlog.is_debug():
            ftlog.info(">>", "|roomId, playingLen, rankingLen:", self.roomId, enterMatchTotal - rankingLen, rankingLen,
                       caller=self)

        return enterMatchTotal - rankingLen

    def doLeaveMatch(self, userId, tableId):
        self.__leaveMatch(userId, tableId)

    def __leaveMatch(self, userId, tableId=0, needSendRewardTodoTask=True):

        playingLen, rankingLen, enterMatchTotal, isSuccess = daobase.executeRankCmd("EVALSHA", self.userLeaveLuaSha, 0,
                                                                                    userId)
        ftlog.hinfo("__leaveMatch remove user from playingRanking", "|roomId, userId, state", self.roomId, userId,
                    self.getStateStr(),
                    "|playingLen, rankingLen, enterMatchTotal, isSuccess", playingLen, rankingLen, enterMatchTotal,
                    isSuccess,
                    "|tableId, needSendRewardTodoTask", tableId, needSendRewardTodoTask, caller=self)

        # isSuccess 表示成功从 ranking 中删除。加这个检查是为了避免玩家被动离开的同时主动离开，导致二次发奖
        if not isSuccess:
            return

        if playingLen + rankingLen != enterMatchTotal:
            ftlog.error(getMethodName(), "playingLen + rankingLen != enterMatchTotal",
                        "|roomId, playingLen, rankingLen:", self.roomId, playingLen, rankingLen,
                        "|enterMatchTotal:", enterMatchTotal)

        ftlog.hinfo("__leaveMatch |roomId, playingLen, rankingLen:", self.roomId, enterMatchTotal - rankingLen,
                    rankingLen, caller=self)

        playingLen = enterMatchTotal - rankingLen

        if ftlog.is_debug():
            ftlog.debug("|roomId, playingLen:", self.roomId, playingLen, caller=self)
        func = functools.partial(self.ranking.sendToAll)
        FTTimer(1, func)

        if playingLen < 1:  # 第一名离桌
            return

        # 奖励2到n名
        rankingOrder = playingLen + 1
        self.matchPlugin.rewardWinner(None, self, userId, rankingOrder, self.matchPlugin.rankingKey(self.bigRoomId),
                                      self.matchCounter,
                                      tableId, needSendRewardTodoTask)

        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_USER_MATCH_END', params={
            'userId': userId, 'room': self, 'rankingOrder': rankingOrder}), self.gameId)

        mconf = self.matchPlugin.match_room_confs[self.bigRoomId]
        day1EndConf = mconf.get('day1EndConf')
        if day1EndConf:
            endPlayerN = day1EndConf.get("endPlayerN", 1)
            if (self.state == self.MTT_STATE_QUALIFIER and playingLen <= endPlayerN
                and mconf['betConfIndex'] >= mconf.get("delaySigninBlindBetPoint", 0)):
                self.state = self.MTT_STATE_DAY1_END
                ftlog.hinfo("__leaveMatch turn to MTT_STATE_DAY1_END |roomId, playingLen, state:",
                            self.roomId, playingLen, self.getStateStr(), caller=self)
                self.scheduler.cancelLoop()
                self.matchPlugin.notifyDay1MatchEndWithPlayerN(self)
        else:
            if self.state == self.MTT_STATE_QUALIFIER and playingLen <= self.tableConf["maxSeatN"]:
                self.state = self.MTT_STATE_PREFINALS
                ftlog.hinfo("__leaveMatch turn to MTT_STATE_PREFINALS |roomId, playingLen, state:",
                            self.roomId, playingLen, self.getStateStr(), caller=self)
                self.scheduler.cancelLoop()

        if playingLen > 1:
            return

        # 奖励第一名
        userId = daobase.executeRankCmd("ZRANGE", self.matchPlugin.playingRankingKey(self.bigRoomId), -1, -1)[0]
        daobase.executeRankCmd("EVALSHA", self.userLeaveLuaSha, 0, userId)

        # 要让第一名leave，否则拆桌时会被加回队列，如果玩家强退并等到loc清除后上线，就会导致下一场比赛人数多出1人
        func = functools.partial(self._leave, userId, TYRoom.LEAVE_ROOM_REASON_MATCH_END, needSendRes=False)
        FTTimer(0, func)  # 异步执行，否则GT会死锁

        ftlog.hinfo("__leaveMatch remove user from playingRanking,", "|roomId, userId", self.roomId, userId,
                    caller=self)
        rankingOrder = 1
        self.matchPlugin.rewardWinner(None, self, userId, rankingOrder, self.matchPlugin.rankingKey(self.bigRoomId),
                                      self.matchCounter, tableId=0)

        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_USER_MATCH_END', params={
            'userId': userId, 'room': self, 'rankingOrder': rankingOrder}), self.gameId)

        self.state = self.MTT_STATE_IDLE
        func2 = functools.partial(self.__onMatchEnd)
        FTTimer(0, func2)  # 异步执行，否则GT会死锁

    def __onMatchEnd(self):
        mconf = self.matchPlugin.match_room_confs[self.bigRoomId]

        rankinglist = daobase.executeRankCmd("LRANGE", self.matchPlugin.rankingKey(self.bigRoomId), 0, -1)
        getName = lambda userId: userdata.getAttr(userId, 'name')
        rankingListWithName = [(i + 1, userId, getName(userId)) for i, userId in enumerate(reversed(rankinglist))]
        bireport.matchFinish(self.gameId, self.roomId,
                             mconf['start_time'].strftime('%Y-%m-%d_%H:%M:%S_') + str(self.roomId),
                             mconf['name'].replace('\n', ' '),
                             matchTypeId=mconf['match_id'],
                             endTimestamp=time.time(),
                             rewardChip=self.matchCounter['rewardChip'],
                             rewardCoupon=self.matchCounter['rewardCoupon'],
                             rankingList=rankingListWithName,
                             usersLeaveMatchCount=self.matchCounter['usersLeaveMatchCount'],
                             rebuyChip=self.matchCounter['rebuyChip'],
                             addonChip=self.matchCounter['addonChip'],
                             )

        # for check MTT gameEnd
        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_MATCH_END', params={'room': self}), self.gameId)

        if ftlog.is_debug():
            ftlog.debug("len(self.scheduler.activeTableIds):", len(self.scheduler.activeTableIds), caller=self)

        # 回收决赛桌和异常牌桌
        remainActiveTables = strutil.cloneData(self.scheduler.activeTableIds)
        for activeTableId in remainActiveTables:
            self.scheduler._recycleTable(activeTableId)

        if mconf.get('day1EndConf'):
            self.matchPlugin.saveDay2Players(self)

        self.state = self.MTT_STATE_READY

    #         if len(self.scheduler.activeTableIds) == 0: #当GR执行较慢，第二名主动leave时可能出现决赛桌在mathEnd前已回收的情况，无法通过adjustTable来修改比赛状态
    #             ftlog.warn("__onMatchEnd len(self.scheduler.activeTableIds) == 0, set mttRoom.state to READY")
    #             self.state = self.MTT_STATE_READY



    # ---shawdowRoom 使用的函数
    def doChangeBetsConf(self, betsConf):
        '''shawdowRoom 处理升盲注'''
        self.matchPlugin.doChangeBetsConf(self, betsConf)  # MttRoom里不能使用具体游戏的类或方法

    def doGetMatchBuyin(self, userId):
        ''' 用户点了购买'''
        self.matchPlugin.onGetMatchBuyin(self, userId)

    def doMatchBuyin(self, userId, buy):
        ''' 用户点了购买'''
        self.matchPlugin.onMatchBuyin(self, userId, buy)

    def doTryNotifyRebuy(self, userId):
        return self.matchPlugin.tryNotifyRebuy(self.gameId, self.roomId, userId)

    def getDay1EndConf(self):
        return self.matchPlugin.match_room_confs[self.bigRoomId].get('day1EndConf')

    def getDay2StartConf(self):
        return self.matchPlugin.match_room_confs[self.bigRoomId].get('day2StartConf')

    def isDay1Match(self):
        return not not self.getDay1EndConf()

    def isDay2Match(self):
        return not not self.getDay2StartConf()
