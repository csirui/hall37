# coding=UTF-8
'''
    玩家模块
'''

__author__ = ['Zhou Hao']

import difang.entity.plugin_event_const as PluginEvents
import freetime.util.log as ftlog
from poker.entity.configure import gdata
from poker.entity.dao import userdata, sessiondata
from poker.entity.game.plugin import TYPluginCenter, TYPluginUtils
from poker.entity.game.tables.table_player import TYPlayer


class DiFangPlayer(TYPlayer):
    '''
    '''

    STAT_WAIT = 0
    STAT_READY = 1
    STAT_PLAYING = 2

    def __init__(self, table, seatIndex):
        super(DiFangPlayer, self).__init__(table, seatIndex)
        self._clear()

    def __str__(self):
        return str(self.userId)

    def __repr__(self):
        return str(self.userId)

    def setEmpty(self):
        self.userId = 0

    def isEmpty(self):
        return self.userId == 0

    def isReady(self):
        return self.state == self.STAT_READY

    def isPlay(self):
        return self.state == self.STAT_PLAYING

    def setWait(self):
        self.state = self.STAT_WAIT

    def setReady(self):
        self.state = self.STAT_READY

    def setPlaying(self):
        self.state = self.STAT_PLAYING

    def setHoleCards(self, cards):
        self.holeCards = cards

    def _clear(self):
        # user信息（redis缓存）
        # player的userId是只读属性，从seat.userId取值
        self.name = ""  # 名字
        self.sex = 0  # 性别
        self.purl = ""  # 头像地址
        # game信息（redis缓存）
        # 牌桌积分信息
        self.tableChips = 0  # 用户在牌桌上的积分
        # 手牌信息
        self.holeCards = []  # 用户的手牌
        # 统计信息

        # 状态信息
        self.setWait()
        self.isManaged = False  # 是否托管
        self.actTimeOutN = 0  # 玩家连续操作超时的次数
        self.lastApplyDismissTime = 0  # 玩家上次发起投票散桌的时间
        self.isVotedDismiss = False  # 玩家是否已经投过散桌的票
        self.lastPingTimeStamp = 0
        self.pingDelay = 0

        # self.ip = ""

    def initInfo(self):
        '''从redis或session里初始化player的数据
        '''
        if ftlog.is_debug():
            ftlog.debug("<< |userId, tableId, seatId:", self.userId, self.table.tableId, self.seatId, caller=self)

        self._clear()

        self.name, self.sex, self.purl = userdata.getAttrs(self.userId, ['name', 'sex', 'purl'])
        # self.purl = unicode(self.purl)
        # self.ip = sessiondata.getClientIp(self.userId)

        # gdata_fields = []
        # () = gamedata.getGameAttrs(self.userId, self.table.gameId, gdata_fields)

        if ftlog.is_debug():
            ftlog.debug(">> |userId, tableId, seatId:", self.userId, self.table.tableId, self.seatId, caller=self)

    def getInfo(self):
        item = {}
        item["seatId"] = self.seatIndex  # 德州客户端 seatId 从0开始 ！
        item["userId"] = self.userId
        if self.userId == 0:
            return item
        # user信息
        if gdata.mode() == gdata.RUN_MODE_ONLINE:
            item["name"] = self.name
        else:
            item["name"] = '%s_%s_%s' % (self.userId, self.seatIndex, self.name)
        item["purl"] = self.purl
        item["sex"] = self.sex
        item["ip"] = sessiondata.getClientIp(self.userId)  # 需要实时更新ip数据
        # 牌桌筹码信息
        item["chips"] = self.tableChips
        item["state"] = self.state
        # game信息
        # 统计信息
        # 手牌信息
        # 状态信息
        item["managed"] = self.isManaged

        # 以插件形式来填充palyerInfo数据
        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd=PluginEvents.EV_GET_PLAYER_INFO, params=TYPluginUtils.mkdict(
            table=self.table, userId=self.userId, player=self, playerInfo=item)),
                             self.table.gameId)

        return item

    def wait(self):
        self.setWait()
        self.holeCards = []

    def ready(self):
        self.setReady()
        self.table.sendTableCallReadyRes(self)

    def start(self):
        '''一局开始'''
        if ftlog.is_debug():
            ftlog.debug("<< |userId=", self.userId, "roomId=", self.table.roomId, " tableId=", self.table.tableId,
                        caller=self)
        self.setPlaying()

        msg = TYPluginUtils.updateMsg(cmd=PluginEvents.EV_PLAYER_GAME_FRAME_START, params=TYPluginUtils.mkdict(
            table=self.table, player=self))
        TYPluginCenter.event(msg, self.table.gameId)

    def end(self, extParam):
        '''一局结束'''
        if ftlog.is_debug():
            ftlog.debug("<< |userId=", self.userId, "roomId=", self.table.roomId, " tableId=", self.table.tableId,
                        caller=self)

        msg = TYPluginUtils.updateMsg(cmd=PluginEvents.EV_PLAYER_GAME_FRAME_END, params=TYPluginUtils.mkdict(
            table=self.table, player=self, extParam=extParam))
        TYPluginCenter.event(msg, self.table.gameId)
