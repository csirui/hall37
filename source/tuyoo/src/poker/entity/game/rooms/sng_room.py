# coding=UTF-8
'''SNG（Sit and Go， 单桌赛）房间类
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import freetime.util.log as ftlog
from poker.entity.configure import gdata
from poker.entity.game.plugin import TYPluginUtils
from poker.entity.game.rooms.queue_room import TYQueueScheduler, TYQueueRoom
from poker.entity.game.rooms.room import TYRoom


class TYSNGQueueScheduler(TYQueueScheduler):
    '''SNG队列调度器类
    
    Attributes:
        _state : 队列管理器状态， 
           STATE_IDLE 队列空闲状态，即关闭循环调度；
           STATE_LOOP 队列开启循环调度状态。
           STATE_START_TABLE 开桌转态，此时不允许玩家leave room，以免造成开局缺人问题。
    
    Configure：
      
    '''
    pass


class TYSngRoom(TYQueueRoom):
    '''SNG（Sit and Go， 单桌赛）房间类
    
    Attributes:
    '''

    def __init__(self, roomDefine):
        super(TYSngRoom, self).__init__(roomDefine)
        self.__initMatch()

    def doReloadConf(self, roomDefine):
        return  # SNG 已下线
        super(TYSngRoom, self).doReloadConf(roomDefine)
        self.matchPlugin.refreshMatchInfo(roomDefine)

    def __initMatch(self):
        return  # SNG 已下线

        self.matchPlugin = gdata.games()[self.gameId].getSngMatchPlugin()
        self.matchPlugin.initMatchConfs(self.gameId)

        serverType = gdata.serverType()
        if serverType == gdata.SRV_TYPE_ROOM:
            self.matchPlugin.cancelMatch(self)


            #     def _initScheduler(self):
            #         self.scheduler = TYSNGQueueScheduler(self)

    def _tableType(self):
        return {'isSng': True}

    def _tableTheme(self):
        return "sng"

    def _onLeaveQueueOk(self, userId):
        self.matchPlugin.doAbortMatch(self, userId)

    def _onQuickStartOk(self, userId):
        super(TYSngRoom, self)._onQuickStartOk(userId)
        self.matchPlugin.doEnterMatch(self, userId)

    def checkSitCondition(self, userId):
        return self.matchPlugin.checkSitCondition(self.bigRoomId, userId)

    def doGetMatchList(self, userId, page=0, number=10, tag="all"):
        self.matchPlugin.getMatchList(self.gameId, userId, self.bigRoomId, page, number, tag)

    def doGetDescription(self, userId):
        if ftlog.is_debug():
            ftlog.debug("<<", "|userId, roomId:", userId, self.roomId, caller=self)
        match_desc = {}
        self.matchPlugin.getMatchDes(userId, self.bigRoomId, match_desc)
        TYPluginUtils.sendMessage(self.gameId, [userId], 'm_des',
                                  result={'roomId': self.bigRoomId, 'm_type': self.roomConf['typeName'],
                                          'desc': match_desc})

        rooms = [{"desc": self.matchConf["signinDesc"], "roomId": self.bigRoomId}]
        TYPluginUtils.sendMessage(self.gameId, [userId], 'm_rooms', result={'rooms': rooms, 'selected': self.bigRoomId})

    def doGetRankList(self, userId, msg):
        tableId = msg.getParam("tableId")
        table = self.maptable[tableId]
        results = self.matchPlugin.getRankList(userId, self.roomId, table)
        TYPluginUtils.sendMessage(self.gameId, [userId], 'matchRank', results)

    def doMatchStart(self, table, msg):
        self.matchPlugin.doMatchStart(table, msg)

    def doLeaveMatch(self, userId, table, leaveReason):
        needSendRewardTodoTask = False if leaveReason == TYRoom.LEAVE_ROOM_REASON_ACTIVE else True
        self.matchPlugin.doLeaveMatch(userId, table, needSendRewardTodoTask)
