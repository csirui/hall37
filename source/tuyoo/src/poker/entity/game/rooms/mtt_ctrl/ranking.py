# coding=UTF-8
'''德州扑克MTT排行榜
'''
from itertools import izip

from freetime.util.log import catchedmethod
from poker.entity.game.rooms.player_room_dao import PlayerRoomDao
from poker.util import strutil

__author__ = ['Zhou Hao', 'Wang Tao']

import time

from freetime.util import log as ftlog

from poker.entity.game.plugin import TYPluginUtils
from poker.entity.dao import userdata, gamedata
from poker.entity.dao import daobase


def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)


class Ranking(object):
    ''' 排行榜管理 '''

    BUILD_RANKING_INTERVAL = 10  # 排榜间隔秒数
    SEND_RANKING_INTERVAL = 3  # 发榜间隔秒数

    def __init__(self, room, starttimestamp):
        self.room = room
        self.bigRoomId = room.bigRoomId
        self.roomId = room.roomId
        self.gameId = self.room.gameId

        self.starttimestamp = starttimestamp
        self.udatas = {}  # userId: (name, purl)
        self.userRanking = {}  # userId: (tablechip, pos)
        self.ranking = []  # [userId}]

        self.canSendRankToAll = True
        self.lastBuildTime = 0  # 上次排榜时间
        self.lastSendTime = 0  # 上次发榜时间
        self.rankResults = {}
        self.rankResultsForSend = {}

    def getUData(self, userId):
        if userId not in self.udatas:
            udata = userdata.getAttrs(userId, ['name', 'purl'])
            photo = gamedata.getGameAttr(userId, self.gameId, 'photo')
            udata.append(photo)
            self.udatas[userId] = udata
            return udata
        return self.udatas[userId]

    def setUData(self, userId, name, purl, photo):
        self.udatas[userId] = [name, purl, photo]

    def setHunterInfo(self, userId, rankItem):

        gameInfo = PlayerRoomDao.getPlayerRoomRecord(userId, self.room.bigRoomId)

        rankItem['huntPlayersN'] = gameInfo.get('huntPlayersN', 0)  # 猎杀人数
        rankItem['huntBonusTotal'] = gameInfo.get('huntBonusTotal', 0)  # 获得总赏金
        # 猎人奖金

    #         rankItem['hunterReward'] = gameInfo.get('hunterReward', None)
    #         if rankItem['hunterReward'] == None:
    #             if tableChip > 0:
    #                 rankItem['hunterReward'] = self.room.matchPlugin.getHunterRewardConf(userId, self.room)
    #             else:
    #                 rankItem['hunterReward'] = 0

    def __buildRankData(self):
        now = time.time()
        if now - self.lastBuildTime < self.BUILD_RANKING_INTERVAL:
            return
        self.lastBuildtime = now

        results = {'roomId': self.bigRoomId}
        results['matchType'] = self.room.matchPlugin.match_room_confs[self.room.bigRoomId].get("matchType", "")
        results['ranks'] = []

        leftPlayers = [(userId, 0) for userId in
                       daobase.executeRankCmd("LRANGE", self.room.matchPlugin.rankingKey(self.bigRoomId), 0, -1)]  # 淘汰的
        if ftlog.is_debug():
            ftlog.debug("get leftPlayers", "|", leftPlayers, caller=self)
        playingPlayersWithScores = list(pairwise(
            daobase.executeRankCmd("ZRANGE", self.room.matchPlugin.playingRankingKey(self.bigRoomId), 0, -1,
                                   'WITHSCORES')))
        if ftlog.is_debug():
            ftlog.debug("get playingPlayersWithScores", "|", playingPlayersWithScores)

        allPlayers = list(reversed(leftPlayers + playingPlayersWithScores))  # 1, 2, ... 最后一名

        if ftlog.is_debug():
            ftlog.debug("get all players", "|", allPlayers)

        self.userRanking = {}
        self.ranks = []
        for i, (userId, tableChip) in enumerate(allPlayers):
            name, purl, photo = self.getUData(userId)
            rankItem = {
                'id': userId,
                'tableChip': tableChip,
                'name': name,
                'purl': purl,
                'head': photo,
                'rank': i + 1,
            }
            if results['matchType'] in ['hunter', 'snowball']:
                self.setHunterInfo(userId, rankItem)
            self.ranks.append(rankItem)
            self.userRanking[userId] = i

        results['totalPlayersNum'] = len(playingPlayersWithScores)
        results['pos'] = 1
        self.rankResults = results

        self.rankResultsForSend = strutil.cloneData(results)
        self.rankResultsForSend['ranks'] = strutil.cloneData(self.ranks[:30])  # 3.6 以前版本，发30个

        self.rankResultsForSend_3_6 = strutil.cloneData(results)
        blank = {'id': 0, 'tableChip': 0, 'name': '', 'purl': '', 'rank': 1}
        self.rankResultsForSend_3_6['ranks'] = strutil.cloneData([blank] + self.ranks[:30])  # 3.6 以后版本，发31个，第一个是自己

    @catchedmethod
    def sendToUser(self, userId):
        # 针对day2比赛:
        # day1结束后,没有通知day2 build榜的机制,所以这里在玩家获取榜的时候build一次
        if self.room.isDay2Match():
            self.__buildRankData()
        # if not self.canSend():
        #             return

        # 加个检查，防止极特殊情况下，前端在开赛前请求榜导致异常
        if not self.rankResultsForSend:
            return

        userRank = self.userRanking.get(userId, -1)
        #         if userRank < 0:
        #             return

        #         clientVer = sessiondata.getClientIdVer(userId)
        # if TyContext.ClientUtils.isWinPcClient(user.clientId) or user.clientVer < 3.6:
        #         if clientVer < 3.6:
        #             self.rankResultsForSend['pos'] = userRank + 1
        #             TYPluginUtils.sendMessage(self.gameId, userId, 'matchRank', self.rankResultsForSend, logInfo=False)
        #         else:

        if userRank >= 0:
            self.rankResultsForSend_3_6['pos'] = userRank + 1
            self.rankResultsForSend_3_6['ranks'][0].update(self.ranks[userRank])
            TYPluginUtils.sendMessage(self.gameId, userId, 'matchRank', self.rankResultsForSend_3_6, logInfo=False)
        else:
            self.rankResultsForSend['pos'] = userRank + 1
            TYPluginUtils.sendMessage(self.gameId, userId, 'matchRank', self.rankResultsForSend, logInfo=False)

    @catchedmethod
    def sendToAll(self):
        if not self.canSendRankToAll:
            return
        # if not self.canSend(): #确保不在比赛前开赛， GT没有比赛状态信息
        #             return
        ftlog.debug("<<", caller=self)
        self.canSendRankToAll = False
        self._sendToAll()
        self.canSendRankToAll = True

    @catchedmethod
    def _sendToAll(self):
        now = time.time()
        if now - self.lastSendTime < self.SEND_RANKING_INTERVAL:
            return
        self.lastSendTime = now

        self.__buildRankData()

        allPlayersIds = list(self.room._roomUsers)

        for uid in allPlayersIds:
            self.sendToUser(uid)

    def beforeMatchStart(self):
        self.canSendRankToAll = False

    def afterMatchStart(self):
        self.canSendRankToAll = True

# def canSend(self):
#         return self.room.isMatchingState() # 开赛前发送榜没有意义
