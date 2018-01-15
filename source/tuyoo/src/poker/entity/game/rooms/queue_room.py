# coding=UTF-8
'''队列房间类
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
from freetime.util.log import getMethodName
from poker.entity.configure import gdata
from poker.entity.dao import onlinedata
from poker.entity.game.plugin import TYPluginCenter, TYPluginUtils
from poker.entity.game.rooms.player_room_dao import PlayerRoomDao
from poker.entity.game.rooms.room import TYRoom
from poker.entity.game.tables.table_player import TYPlayer
from poker.protocol import router


class TYQueueScheduler(object):
    '''队列调度器类
    
    Attributes:
        _state : 队列管理器状态， 
           STATE_IDLE 队列空闲状态，即关闭循环调度；
           STATE_LOOP 队列开启循环调度状态。
           STATE_START_TABLE 开桌转态，此时不允许玩家leave room，以免造成开局缺人问题。
        users/waitingUsers : 等待分桌的玩家队列, OrdinaryDict类型
        sittingUsers : 正在分桌的玩家集合，set类型
        activeTableIds : 使用的桌子，set类型
        idleTableIds : 空闲牌桌，list类型
    
    Configure：
        n_start :达到这个人数马上开新桌
        n_recycle : 少于这个人数拆桌
        wait_time : 超过这个时间还凑不齐n_start个玩家，但达到minTriggerLen人数，也会开新桌
        minTriggerLen : 参见wait_time
    '''

    STATE_IDLE = 0
    STATE_LOOP = 1
    STATE_START_TABLE = 2

    QUEUE_STATE_STRS = {
        STATE_IDLE: "STATE_IDLE",
        STATE_LOOP: "STATE_LOOP",
        STATE_START_TABLE: "STATE_START_TABLE"
    }

    def getStateStr(self):
        return self.QUEUE_STATE_STRS[self._state]

    def __init__(self, room):
        self.room = room
        self.locker = FTLock(self.__class__.__name__ + "_%d" % id(self))

        self._state = self.STATE_IDLE  # 玩家从队列分配到牌桌过程中，不允许玩家leave room，以免造成开局缺人问题。

        # 初始化玩家和牌桌对列
        self.users = OrderedDict()
        self.sittingUsers = set()  # 正在坐下的玩家，不允许离开
        self.activeTableIds = set()
        self._initIdleTableIds()

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
            ftlog.info("_initIdleTableIds >>", self.baseLogStr(), '|len(shadowRoomIds), len(idleTableIds):',
                       len(shadowRoomIds), len(self.idleTableIds))

    def startLoop(self):
        self._state = self.STATE_LOOP
        FTTimer(1, self.doHeartBeat)
        ftlog.info("startLoop >>", self.baseLogStr(), caller=self)

    def cancelLoop(self):
        self._state = self.STATE_IDLE
        ftlog.info("cancelLoop >>", self.baseLogStr(), caller=self)

    @property
    def n_start(self):
        # 最小开局人数，队列总人数 >= 这个人数才能开局。否则等第一个玩家超时后尝试开最少2 人桌
        return self.room.roomConf.get("triggerLen", 2)

    @property
    def n_recycle(self):
        # 加人后比这个人少就拆桌，否则尝试踢机器人、开局
        return self.room.roomConf.get("n_recycle", 2)

    @property
    def wait_time(self):
        # 玩家进入队列后等待开桌秒数。超过这个时间尝试开最少2人桌
        return self.room.roomConf.get("checkInterval", 5)

    @property
    def minTriggerLen(self):
        return self.room.roomConf.get("minTriggerLen", 2)

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

    def enter(self, userId):
        '''玩家进入队列'''
        if self.users.get(userId) != None:
            ftlog.error(getMethodName(), "already in queue!", self.baseLogStr(None, userId))
            return False

        self.users[userId] = {"enterTime": time.time()}
        onlinedata.addOnlineLoc(userId, self.room.roomId, self.room.roomId * 10000, 1)

        if ftlog.is_debug():
            ftlog.debug(">>", self.baseLogStr(None, userId),
                        "|locList:", onlinedata.getOnlineLocList(userId), caller=self)
        return True

    def leave(self, userId):
        '''玩家离开队列'''

        # 只有玩家在队列里时才锁队列并删除他
        if userId in self.users:
            del self.users[userId]
            onlinedata.removeOnlineLoc(userId, self.room.roomId, self.room.roomId * 10000)

        if ftlog.is_debug():
            ftlog.debug(">>", self.baseLogStr(None, userId),
                        "|locList:", onlinedata.getOnlineLocList(userId), caller=self)
        return True

    def adjustTablePlayers(self, msg):
        '''一局游戏结束, 调整牌桌玩家，拆桌或者拉人'''
        tableId = msg.getParam("tableId")
        playersN = msg.getParam("playersN")
        if ftlog.is_debug():
            ftlog.debug("<<", self.baseLogStr(tableId), '|playersN:', playersN, caller=self)

        if playersN <= 1:
            self._recycleTable(tableId)
            return

        if playersN + len(self.users) < self.n_recycle:  # 人太少，拆桌，回收
            self._recycleTable(tableId)
        else:
            #             self._seatNPlayers(tableId, self.n_start - playersN)
            self._startTable(tableId, self.n_start - playersN)

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
        if self._state == self.STATE_IDLE:
            return

        FTTimer(1, self.doHeartBeat)
        if len(self.users) == 0:
            return

        if ftlog.is_debug():
            ftlog.debug("<<", self.baseLogStr(), caller=self)
        # ftlog.debug("|first user, enter time, now, wait_time:", self.users.keys()[0], self.users[self.users.keys()[0]], time.time(), self.wait_time)
        if self._state == self.STATE_LOOP:
            if len(self.users) >= self.n_start:
                self._tryStartNewTable(self.n_start)
                return

            if time.time() - self.users[self.users.keys()[0]]["enterTime"] < self.wait_time:
                return

            if len(self.users) >= self.minTriggerLen:
                self._tryStartNewTable(self.minTriggerLen)
                return

            if TYPlayer.isRobot(self.users.keys()[0]):
                return

            if len(self.room._roomUsers) < self.n_start:
                self.notifyRobot()

    def _startTable(self, tableId, playerN=0, recyclePlayersN=0):
        ''' 不锁队列，启动一张桌子
            recyclePlayersN表示需要从牌桌回收到队列的人数
        '''
        ftlog.hinfo("_startTable <<", self.baseLogStr(tableId),
                    "|sittingUsers:", self.sittingUsers,
                    "|playerN, recyclePlayersN:", playerN, recyclePlayersN,
                    caller=self)

        sittedN = 0
        userIds = set()

        try:
            while sittedN < playerN and len(self.users) > 0:  # 确保无异步操作
                userId = self._popOneUser()
                if not userId:  # 队列里没有可以参与分桌的玩家
                    break
                userIds.add(userId)
                sittedN += 1
                if ftlog.is_debug():
                    ftlog.debug("bring user to table", self.baseLogStr(tableId, userId),
                                "|userIds:", userIds, caller=self)

                    # 移到GT处理，节约GT时间
                    #             for userId in userIds:
                    #                 onlinedata.removeOnlineLoc(userId, self.room.roomId, self.room.roomId * 10000)
                    #                 if ftlog.is_debug() :
                    #                     ftlog.debug("|userId, locList:", userId, onlinedata.getOnlineLocList(userId), caller=self)

            shadowRoomId = tableId / 10000
            self.room.sendTableManageGameStartReq(shadowRoomId, tableId, list(userIds), recyclePlayersN)
        # resultStr = self.room.queryTableManageGameStartReq(shadowRoomId, tableId, list(userIds))
        #             result = json.loads(resultStr)
        #             ftlog.debug("|result:", result)
        except:
            ftlog.exception()

        self.sittingUsers.difference_update(userIds)

        ftlog.hinfo("_startTable >>", self.baseLogStr(tableId),
                    "|sittingUsers:", self.sittingUsers,
                    "|len(userIds):", len(userIds),
                    caller=self)

    def _recycleTable(self, tableId):
        try:
            shadowRoomId = tableId / 10000
            resultStr = self.room.queryTableManageClearPlayersReq(shadowRoomId, tableId)
            if resultStr:
                result = json.loads(resultStr)
                if ftlog.is_debug():
                    ftlog.debug("|result:", result, caller=self)
            self.idleTableIds.append(tableId)
            self.activeTableIds.remove(tableId)
        except:
            ftlog.exception()

    def _tryStartNewTable(self, minPlayersN):
        #         self._state = self.STATE_START_TABLE # TODO: 约束：没法同时开桌

        # 开桌
        ftlog.hinfo("_tryStartNewTable", self.baseLogStr(None, None), '|minPlayersN:', minPlayersN)

        if len(self.users) < minPlayersN:  # 不够开局
            ftlog.warn(self.baseLogStr(None, None), 'users & robots not enough')
        elif len(self.idleTableIds) == 0:
            ftlog.error(self.baseLogStr(None, None), 'idle tables not enough')
        else:
            tableId = self.idleTableIds.pop()
            self.activeTableIds.add(tableId)
            #             self._seatNPlayers(tableId, minPlayersN)
            self._startTable(tableId, minPlayersN)

            #         self._state = self.STATE_LOOP

    def _isValidUser(self, userId):
        return True

    def _popOneUser(self):
        '''从等待玩家队列中pop一个玩家，pop过程中无异步操作'''
        for userId in self.users.keys():
            if self._isValidUser(userId):
                del self.users[userId]
                self.sittingUsers.add(userId)
                return userId
            else:
                ftlog.warn("_popOneUser user %d is not valid:" % userId)
        return None


# def _seatNPlayers(self, tableId, n):
#         '''让桌子凑够 n 个人'''
# 
#         ftlog.debug("<<", self.baseLogStr(), "|sittingUsers:", self.sittingUsers, caller=self)
#         sittedN = 0
#         while sittedN < n and len(self.users) > 0:
#             userId = self._popOneUser()
#             onlinedata.removeOnlineLoc(userId, self.room.roomId, self.room.roomId * 10000)
#             ftlog.debug("bring user to table", self.baseLogStr(tableId, userId),
#                        "|sittingUsers:", self.sittingUsers, 
#                        "|locList:", onlinedata.getOnlineLocList(userId), caller=self)   
#             sitReason = self._seatPlayer(tableId, userId)
#             self.sittingUsers.remove(userId)
#             
#             if sitReason == self.room.ENTER_ROOM_REASON_OK:
#                 sittedN += 1
#             else :
#                 ftlog.warn(getMethodName(), self.baseLogStr(tableId, userId), 'user sit fail, call room.leave with reason', sitReason)
#                 roomLeaveReq = MsgPack()
#                 roomLeaveReq.setParam("reason", self.room.LEAVE_ROOM_REASON_SYSTEM)
#                 self.room.doLeave(userId, roomLeaveReq)
# #                 if TYPlayer.isRobot(userId):
# #                     self._callupRobots(1)
#             
# #         ftlog.info(getMethodName(), ">>", self.baseLogStr(table), "|sittingUsers:", self.sittingUsers)


#     def _seatPlayer(self, tableId, userId):
#         '''玩家入座到桌子
#            以query方式给GT发请求，并异步等待结果
#         '''
#         ftlog.info("<<", self.baseLogStr(tableId, userId), 'bring user sit at table', caller=self)
#         try:
#             shadowRoomId = tableId / 10000
#             clientId = sessiondata.getClientId(userId)
#             sitResultStr = self.room.queryTableManageSitReq(userId, shadowRoomId, tableId, clientId)
#             sitResult = json.loads(sitResultStr)
#             ftlog.debug("|sitResult:", sitResult)
#             if sitResult.get("error"):
#                 return self.room.ENTER_ROOM_REASON_INNER_ERROR
#             return sitResult["result"]["reason"]
#          
#         except:
#             ftlog.exception()
#             return self.room.ENTER_ROOM_REASON_INNER_ERROR





class TYQueueRoom(TYRoom):
    '''队列房间类
    
    Attributes:
        scheduler: 队列调度器
        _roomUsers: 进入房间的玩家集合
    '''

    def __init__(self, roomDefine):
        super(TYQueueRoom, self).__init__(roomDefine)
        serverType = gdata.serverType()
        if serverType == gdata.SRV_TYPE_ROOM:
            self._initScheduler()
            self._roomUsers = set()

    def _baseLogStr(self, des="", userId=None):
        baseRoomInfo = '%s |roomId: %d' % (des, self.roomId)
        baseUserInfo = '' if not userId else ' |userId: %d' % (userId)
        return self.__class__.__name__ + " " + baseRoomInfo + baseUserInfo

    def _initScheduler(self):
        self.scheduler = TYQueueScheduler(self)
        self.scheduler.startLoop()

    def _tableType(self):
        return {'isQuick': True}

    def _tableTheme(self):
        return "queue"

    def checkSitCondition(self, userId):
        '''队列房间的准入条件靠quick_start模块和queue_table模块分别判断， 按产品需求两者标准不同'''
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
            ftlog.info("_enter add to _roomUsers.add |roomId, userId, _roomUsersN: ", self.roomId, userId,
                       len(self._roomUsers), caller=self)

        if ftlog.is_debug():
            ftlog.debug(">> |roomId, userId, _roomUsersN: ", self.roomId, userId, len(self._roomUsers), caller=self)
            ftlog.debug(">> |roomId, userId, _roomUsers: ", self.roomId, userId, self._roomUsers, caller=self)
            locList = onlinedata.getOnlineLocList(userId)
            ftlog.debug(">> |roomId, userId, locList:", self.roomId, userId, locList)

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

        if userId in self.scheduler.sittingUsers:  # 从队列分配玩家进牌桌时，该玩家不允许离开队列。
            ftlog.warn("can't leave when start table!", caller=self)
            return False

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

        msg = TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_QUICK_START', params=TYPluginUtils.mkdict(
            userId=userId, roomId=self.roomId), result={}), self.gameId)

        if msg.getResult("reason") != None:
            info = u'玩家需要验证'
            self.sendQuickStartRes(self.gameId, userId, msg.getResult("reason"), self.bigRoomId, 0, info)
            return

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
        #             self.sendTableClothRes(self.gameId, userId, {'isQuick': True, 'isLinerMatch': False, 'isSng': False, 'isMtt': False})

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

    def doRoomUpdateRankOfAll(self):
        pass

    def doGetDescription(self, userId):
        pass

    def doGetMatchStatus(self, userId):
        pass
