# coding=UTF-8
'''LTS（Limited Time Score, 限时积分赛）房间类
'''
from freetime.core.timer import FTTimer

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import time
from datetime import datetime

import freetime.util.log as ftlog

from poker.entity.configure import gdata
from poker.entity.game.rooms.room import TYRoom
from poker.entity.game.rooms.vip_room import TYVipRoom
from poker.entity.game.plugin import TYPluginUtils
from poker.entity.dao import daobase


class TYLtsRoom(TYVipRoom):
    '''LTS（Limited Time Score, 限时积分赛）房间类
    
    Attributes:
    '''

    def __init__(self, roomdefine):
        super(TYLtsRoom, self).__init__(roomdefine)
        self.__initMatch()

    def doReloadConf(self, roomDefine):
        return  # 游轮赛已下线
        super(TYLtsRoom, self).doReloadConf(roomDefine)
        self.__initMatch()  # reload后matchPlugin会发生变化

    def __initMatch(self):
        return  # 游轮赛已下线

        self.matchPlugin = gdata.games()[self.gameId].getLtsMatchPlugin()
        self.matchPlugin.initMatchConfs(self.gameId)

        serverType = gdata.serverType()
        if serverType == gdata.SRV_TYPE_TABLE:
            endTimestamp = self.matchPlugin.match_room_confs[self.bigRoomId]["end_timestamp"]
            FTTimer(endTimestamp - int(time.time()) + 5, self._checkMatchEnd)

    def checkSitCondition(self, userId):
        now = datetime.now()
        if not self.matchPlugin.isMatchTime(now, self.bigRoomId):
            return False, TYRoom.ENTER_ROOM_REASON_WRONG_TIME

        return True, TYRoom.ENTER_ROOM_REASON_OK

    def doGetDescription(self, userId):
        ftlog.debug("<<", "|userId, roomId:", userId, self.roomId, caller=self)
        match_desc = {}
        self.matchPlugin.checkMatchStartTime(self.bigRoomId)
        self.matchPlugin.getMatchDes(userId, self.bigRoomId, match_desc)
        # 每次取m_des的时候 取一次服务器当前的时间
        match_desc.update({'nowServerTime': int(time.time())})
        TYPluginUtils.sendMessage(self.gameId, [userId], 'm_des',
                                  result={'roomId': self.bigRoomId, 'm_type': self.roomConf['typeName'],
                                          'desc': match_desc})

    def doGetRankList(self, userId, msg):
        results = {}
        self.matchPlugin.checkMatchStartTime(self.bigRoomId)
        self.matchPlugin.getRankList(self.gameId, userId, self.bigRoomId, results)
        TYPluginUtils.sendMessage(self.gameId, [userId], 'linerMatchRank', results)

    def incrMatchScore(self, userId, score):
        '''
        Note: 比赛时间结束后，还会有牌桌未完结，这些牌桌完结后也需要记录成绩。
        '''
        ftlog.debug("<< |userId, self.bigRoomId, score:", userId, self.bigRoomId, score, caller=self)
        rankingKey = self.matchPlugin.rankingKey(self.bigRoomId)
        daobase.executeRankCmd('ZINCRBY', rankingKey, score, userId)
        # 设置比赛结果公布过期时间
        DEFAULT_RESULT_EXPIRE = 12 * 60 * 60
        resultExpire = self.matchConf.get("resultExpire", DEFAULT_RESULT_EXPIRE)
        daobase.executeRankCmd('EXPIRE', rankingKey, resultExpire)

    #         ftlog.debug(methodFullName, "set resultExpire |roomId:", table.roomId,
    #                                 "|resultExpire:", resultExpire)


    def doAdjustTablePlayers(self, table):
        ftlog.debug("<< |tableId:", table.tableId, caller=self)

        if self.matchPlugin.isMatchTime(datetime.now(), self.bigRoomId):
            return

        self.matchPlugin.recycleOneTable(table)
        self._checkMatchEnd()

    def _checkMatchEnd(self):

        if self.matchPlugin.isMatchTime(datetime.now(), self.bigRoomId):
            return

        isAllTableFinished = self.matchPlugin.recycleAllTables(self)
        if isAllTableFinished:
            self.doMatchEnd()

    def doMatchEnd(self):
        ftlog.info("<< |roomId:", self.roomId, caller=self)

        # TODO: 向所有人发送 todotask，提示比赛已结束

        rankingKey = self.matchPlugin.rankingKey(self.bigRoomId)
        # 更新翅膀，发奖励
        userIds = daobase.executeRankCmd('ZREVRANGE', rankingKey, 0, -1)
        self.matchPlugin.rewardUsers(userIds, self)

        # 重新计算比赛时间
        self.matchPlugin.refreshMatchStartTime(self.bigRoomId, self.matchConf["openTime"].get("minutes", 60))
        endTimestamp = self.matchPlugin.match_room_confs[self.bigRoomId]["end_timestamp"]
        FTTimer(endTimestamp - int(time.time()) + 5, self._checkMatchEnd)
