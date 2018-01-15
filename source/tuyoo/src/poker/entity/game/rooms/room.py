# coding=UTF-8
'''房间基类
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack
from freetime.util.log import getMethodName, catchedmethod
from poker.entity.configure import gdata, pokerconf
from poker.entity.dao import sessiondata, onlinedata, userchip
from poker.entity.game.plugin import TYPluginCenter, TYPluginUtils
from poker.entity.game.tables.table_player import TYPlayer
from poker.protocol import router


class TYRoom(object):
    '''游戏房间基类
    
    Attributes:
        roomDefine： 房间配置信息
        maptable:    房间牌字典
    '''
    # 进入房间返回的reason常量
    ENTER_ROOM_REASON_OK = 0
    ENTER_ROOM_REASON_CONFLICT = 1  # 玩家在玩牌时退出，然后重新开始另一个游戏，出现gameId冲突
    ENTER_ROOM_REASON_INNER_ERROR = 2  # 服务器内部错误
    ENTER_ROOM_REASON_ROOM_FULL = 3  # 房间已坐满
    ENTER_ROOM_REASON_LESS_MIN = 4  # 玩家所持金币数 < 该房间准入最小金币数
    ENTER_ROOM_REASON_GREATER_MAX = 5  # 玩家所持金币数 > 该房间准入最大金币数
    ENTER_ROOM_REASON_GREATER_ALL = 6  # 玩家所持金币数 > 该类房间所有准入最大金币数
    ENTER_ROOM_REASON_TABLE_FULL = 7  # 桌子已坐满
    ENTER_ROOM_REASON_WRONG_TIME = 8  # 比赛时间未到
    ENTER_ROOM_REASON_NOT_QUALIFIED = 9  # 没有资格进入此房间
    ENTER_ROOM_REASON_ROOM_ID_ERROR = 10  # 客户端发送的roomId参数错误

    ENTER_ROOM_REASON_VIP_LEVEL = 11  # 玩家的VIP级别不够
    ENTER_ROOM_REASON_DASHIFEI_LEVEL = 12  # 玩家的大师分级别不够
    ENTER_ROOM_REASON_NOT_OPEN = 13  # 房间/牌桌暂未开放
    ENTER_ROOM_REASON_NEED_VALIDATE = 14  # 需要验证
    ENTER_ROOM_REASON_NEED_ENERGY = 15  # 体力不足

    # 离开房间/牌桌原因常量
    LEAVE_ROOM_REASON_FORBIT = -1  # 不允许玩家离开房间, 玩家还在牌桌里 或者 队列房间正在调度
    LEAVE_ROOM_REASON_ACTIVE = 0  # 玩家主动离开房间
    LEAVE_ROOM_REASON_LOST_CONNECTION = 1  # 网络连接丢失被踢出房间
    LEAVE_ROOM_REASON_TIMEOUT = 2  # 操作超时被踢出房间
    LEAVE_ROOM_REASON_ABORT = 3  # 流局 
    LEAVE_ROOM_REASON_LESS_MIN = 4  # 玩家所持金币数 < 该房间准入最小金币数
    LEAVE_ROOM_REASON_GREATER_MAX = 5  # 玩家所持金币数 > 该房间准入最大金币数
    LEAVE_ROOM_REASON_MATCH_END = 6  # 比赛完成。所有玩家离桌
    LEAVE_ROOM_REASON_CHANGE_TABLE = 7  # 换桌
    LEAVE_ROOM_REASON_GAME_START_FAIL = 8  # 队列分桌开局坐下时失败，具体原因需要去GT里查
    LEAVE_ROOM_REASON_NEED_VALIDATE = 9  # 需要验证
    LEAVE_ROOM_REASON_SYSTEM = 99  # 系统把玩家踢出房间

    def __init__(self, roomDefine):
        '''
        Args:
            roomDefine:
                RoomDefine.bigRoomId     int 当前房间的大房间ID, 即为game/<gameId>/room/0.json中的键
                RoomDefine.parentId      int 父级房间ID, 当前为管理房间时, 必定为0 (管理房间, 可以理解为玩家队列控制器)
                RoomDefine.roomId        int 当前房间ID
                RoomDefine.gameId        int 游戏ID
                RoomDefine.configId      int 配置分类ID
                RoomDefine.controlId     int 房间控制ID
                RoomDefine.shadowId      int 影子ID
                RoomDefine.tableCount    int 房间中桌子的数量
                RoomDefine.shadowRoomIds tuple 当房间为管理房间时, 下属的桌子实例房间的ID列表
                RoomDefine.configure     dict 房间的配置内容, 即为game/<gameId>/room/0.json中的值
        '''
        if ftlog.is_debug():
            ftlog.debug("<<", "|roomDefine", str(roomDefine), caller=self)
        self.__define = roomDefine
        self.maptable = {}

    # ---read only attributes
    @property
    def roomDefine(self):
        return self.__define

    @property
    def bigRoomId(self):
        return self.__define.bigRoomId

    @property
    def ctrlRoomId(self):
        if self.__define.parentId == 0:
            return self.__define.roomId
        else:
            return self.__define.parentId

    @property
    def roomId(self):
        return self.__define.roomId

    @property
    def gameId(self):
        return self.__define.gameId

    @property
    def roomConf(self):
        return self.__define.configure

    @property
    def tableConf(self):
        return self.__define.configure['tableConf']

    @property
    def matchConf(self):
        return self.__define.configure['matchConf']

    @property
    def matchId(self):
        # TODO 返回当前房间的比赛ID, 若为非比赛房间,返回0
        return 0


        # 兼容旧版

    #     @property
    #     def _id(self):
    #         return self.__define.roomId
    #
    #     @property
    #     def _gid(self):
    #         return self.__define.gameId
    #
    #     @property
    #     def _info(self):
    #         return self.__define.configure


    # ---event funcs
    def doReloadConf(self, roomDefine):
        if ftlog.is_debug():
            ftlog.info(getMethodName(), '<<', "|roomDefine.configure:", roomDefine.configure)

        self.__define = roomDefine

        for table in self.maptable.values():
            table.doReloadConf(self.tableConf)

        if ftlog.is_debug():
            ftlog.debug(getMethodName(), '>>', "|roomId:", self.roomId)

    def doShutDown(self):
        ftlog.debug(getMethodName(), '<<', "|roomId:", self.roomId)
        for table in self.maptable.values():
            table.doShutDown()
        if ftlog.is_debug():
            ftlog.debug(getMethodName(), '>>', "|roomId:", self.roomId)

    def doQuickStart(self, msg):
        pass

    def doCheckUserLoc(self, userId, gameId, roomId, tableId, clientId):
        '''
        检查给出的玩家是否再当前的房间和桌子上,
        依照个个游戏的自己的业务逻辑进行判定,
        seatId >= 0 
        isObserving == 1|0 旁观模式
        当seatId > 0 或 isObserving == 1时表明此玩家在当前的桌子内
        '''
        if not tableId in self.maptable:
            return -1, 0
        seatId = 0
        isObserving = 0
        table = self.maptable[tableId]
        for x in xrange(len(table.players)):
            if table.players[x] and table.players[x].userId == userId:
                seatId = x + 1
                break
        if seatId == 0:
            if userId in table.observers:
                isObserving = 1
        return seatId, isObserving

    @catchedmethod
    def doEnter(self, userId):
        isOk, reason = self._enter(userId)
        if isOk:
            TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_ENTER_ROOM', params=TYPluginUtils.mkdict(
                userId=userId, roomId=self.roomId)), self.gameId)
        return isOk, reason

    def _enter(self, userId):
        return True, TYRoom.ENTER_ROOM_REASON_OK

    @catchedmethod
    def doLeave(self, userId, msg):

        ftlog.hinfo("doLeave |userId, msg:", userId, msg, caller=self)

        reason = msg.getParam("reason", TYRoom.LEAVE_ROOM_REASON_ACTIVE)
        assert isinstance(reason, int)
        needSendRes = msg.getParam("needSendRes", True)
        assert isinstance(needSendRes, bool)
        clientRoomId = msg.getParam("clientRoomId", self.roomId)
        assert isinstance(clientRoomId, int)

        if not self._leave(userId, reason, needSendRes):
            reason = TYRoom.LEAVE_ROOM_REASON_FORBIT

        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_LEAVE_ROOM', params=TYPluginUtils.mkdict(
            userId=userId, roomId=self.roomId, reason=reason)), self.gameId)

        msgRes = MsgPack()
        if not pokerconf.isOpenMoreTable(sessiondata.getClientId(userId)):
            msgRes.setCmd("room_leave")
        else:
            msgRes.setCmd("room")
            msgRes.setResult("action", "leave")

        msgRes.setResult("reason", reason)
        msgRes.setResult("gameId", self.gameId)
        msgRes.setResult("roomId", clientRoomId)  # 处理结果返回给客户端时，部分游戏（例如德州、三顺）需要判断返回的roomId是否与本地一致
        msgRes.setResult("userId", userId)

        if needSendRes or TYPlayer.isRobot(userId):  # 需要通知机器人stop
            router.sendToUser(msgRes, userId)

    def _leave(self, userId, reason, needSendRes):
        if ftlog.is_debug():
            ftlog.debug("<< |roomId, userId:", self.roomId, userId, caller=self)
        if not self._remoteTableLeave(userId, reason):
            return False
        return True

    def _remoteTableLeave(self, userId, reason=LEAVE_ROOM_REASON_ACTIVE, locList=None):
        if not locList:
            locList = onlinedata.getOnlineLocList(userId)
        if ftlog.is_debug():
            ftlog.debug("<< |roomId, userId: ", self.roomId, userId,
                        "|locList:", locList, caller=self)
        for loc in locList:
            onlineRoomId, onlineTableId = loc[0], loc[1]
            if not onlineRoomId in gdata.roomIdDefineMap():
                onlinedata.removeOnlineLoc(userId, onlineRoomId, onlineTableId)
                continue
            ctrlRoomId = gdata.roomIdDefineMap()[onlineRoomId].parentId
            if ctrlRoomId == self.roomId:
                ftlog.hinfo("table leave |userId, onlineRoomId, onlineTableId:", userId, onlineRoomId, onlineTableId,
                            caller=self)
                clientId = sessiondata.getClientId(userId)
                tableLeaveResultStr = self.queryTableManageTableLeaveReq(userId, onlineRoomId, onlineTableId, clientId,
                                                                         {"reason": reason})
                if not tableLeaveResultStr:
                    ftlog.warn("table leave timeout, |userId, onlineRoomId, onlineTableId, reason:",
                               userId, onlineRoomId, onlineTableId, reason, caller=self)

                    # 玩家离开牌桌只返回成功
                #                 tableLeaveResult = json.loads(tableLeaveResultStr)
                #                 ftlog.debug("|tableLeaveResult:", tableLeaveResult)
                #                 if tableLeaveResult.get("error"):
                #                     return False
                #                 if not tableLeaveResult["result"]["isOK"]:
                #                     return False

                if ftlog.is_debug():
                    locList = onlinedata.getOnlineLocList(userId)
                    ftlog.debug(">> |roomId, userId: ", self.roomId, userId,
                                "|locList:", locList, caller=self)
                    #                 return True

        return True

    def updateTableScore(self, tableScore, tableId, force=False):
        pass

    def checkSitCondition(self, userId):
        chip = userchip.getChip(userId)

        if chip < self.roomConf['minCoin']:
            ftlog.warn("chip not enough",
                       "|userId, roomId:", userId, self.roomId, caller=self)
            return False, TYRoom.ENTER_ROOM_REASON_LESS_MIN

        if self.roomConf['maxCoin'] > 0 and chip > self.roomConf['maxCoin']:
            ftlog.warn("chip too much",
                       "|userId, roomId:", userId, self.roomId, caller=self)
            return False, TYRoom.ENTER_ROOM_REASON_GREATER_MAX

        return True, TYRoom.ENTER_ROOM_REASON_OK

    def getRoomOnlineInfo(self):
        ucount, pcount, ocount = 0, 0, 0
        if self.maptable:
            for t in self.maptable.values():
                num = t.playersNum
                if num > 0:
                    pcount += 1
                    ucount += num
                ocount += t.observersNum
        return ucount, pcount, ocount

    def getRoomOnlineInfoDetail(self):
        ucount, pcount = 0, 0
        tables = {}
        if self.maptable:
            for t in self.maptable.values():
                tcount, uids = t.getSeatUserIds()
                if tcount > 0:
                    pcount += 1
                    ucount += tcount
                uids.append(t.state.state)
                tables[t.tableId] = uids
        return ucount, pcount, tables

    def getRoomRobotUserCount(self):
        c = 0
        if self.maptable:
            for t in self.maptable.values():
                c = c + t.getRobotUserCount()
        return c
