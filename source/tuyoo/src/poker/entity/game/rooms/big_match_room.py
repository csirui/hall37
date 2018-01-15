# coding=UTF-8
'''大比赛房间类
'''
import functools
import random

import freetime.util.log as ftlog
from freetime.core.timer import FTTimer
from freetime.entity.msg import MsgPack
from freetime.util.log import getMethodName
from poker.entity.configure import gdata
from poker.entity.dao import onlinedata
from poker.entity.game.rooms.big_match_ctrl.config import MatchConfig
from poker.entity.game.rooms.big_match_ctrl.exceptions import MatchException
from poker.entity.game.rooms.big_match_ctrl.match import TableManager, \
    MatchInstance
from poker.entity.game.rooms.room import TYRoom
from poker.entity.game.tables.table_player import TYPlayer
from poker.protocol import router

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]


class TYBigMatchRoom(TYRoom):
    '''大比赛房间类
    
    Attributes:
        matchPlugin： 各游戏通过定义自己的BigMatchPlugin，来扩展数据获取、下发协议、异常处理、结算等功能
        match: 比赛控制器
        bigmatchId: bigRoomId， 兼容老代码
    '''

    def __init__(self, roomdefine):
        super(TYBigMatchRoom, self).__init__(roomdefine)
        self.bigmatchId = self.bigRoomId
        self.matchPlugin = gdata.games()[self.gameId].getBigMatchPlugin()

        serverType = gdata.serverType()
        if serverType == gdata.SRV_TYPE_ROOM:
            self.initMatch()  # 此处会给self.match赋值

    def initMatch(self):
        ftlog.info(getMethodName(), '<< |roomId=', self.roomId)
        assert (self.matchPlugin.getMatch(self.roomId) is None)

        conf = MatchConfig.parse(self.gameId, self.roomId, self.bigmatchId,
                                 self.roomConf["name"],
                                 self.matchConf)
        #             conf.tableId = self.maptable.values()[0]._id
        conf.tableId = self.roomId * 10000  # 用来表示玩家在房间队列的特殊tableId
        conf.seatId = 1

        tableManager = TableManager(self.gameId, conf.tableSeatCount)
        shadowRoomIds = self.roomDefine.shadowRoomIds
        ftlog.info(getMethodName(), 'before add IdleTables.', '|roomId=', self.roomId, 'roomIds=', list(shadowRoomIds))
        for roomId in shadowRoomIds:
            count = self.roomDefine.configure['gameTableCount']
            baseid = roomId * 10000
            ftlog.info(getMethodName(), 'adding IdleTables of one shadowRoom.', '|roomId=', self.roomId,
                       'shadowRoomId=', roomId, 'tableCount=', count,
                       'baseid=', baseid)
            tableManager.addTables(roomId, baseid, count)
        random.shuffle(tableManager._idleTables)
        match = self.matchPlugin.buildMatch(conf, self)
        match.tableManager = tableManager

        if gdata.mode() == gdata.RUN_MODE_ONLINE:
            playerCapacity = int(tableManager.getAllTableCount() * tableManager.tableSeatCount * 0.9)
            ftlog.info(getMethodName(), '<< |roomId=', self.roomId,
                       'allTableCount=', tableManager.getAllTableCount(),
                       'tableSeatCount=', tableManager.tableSeatCount,
                       'playerCapacity=', playerCapacity,
                       'matchUserMaxCount=', conf.start.userMaxCount)
            assert (playerCapacity > conf.start.userMaxCount)

        match.load()
        self.match = match
        self.matchPlugin.setMatch(self.roomId, match)

    def doEnter(self, userId):
        ftlog.debug("<<", "|userId, roomId:", userId, self.roomId, caller=self)
        mo = MsgPack()
        mo.setCmd('m_enter')
        mo.setResult('gameId', self.gameId)
        mo.setResult('roomId', self.roomId)
        mo.setResult('userId', userId)

        try:
            if not self.match.enter(userId):
                mo.setError(1, u'比赛已经下线')
        except MatchException, e:
            self.matchPlugin.handleMatchException(self, e, userId, mo)

        router.sendToUser(mo, userId)

    def doLeave(self, userId, msg):
        ftlog.debug("<<", "|userId, roomId:", userId, self.roomId, caller=self)
        mo = MsgPack()
        mo.setCmd('m_leave')
        mo.setResult('gameId', self.gameId)
        mo.setResult('roomId', self.roomId)
        mo.setResult('userId', userId)
        self.match.leave(userId)
        router.sendToUser(mo, userId)

    def doGetDescription(self, userId):
        ftlog.debug("<<", "|userId, roomId:", userId, self.roomId, caller=self)
        mo = MsgPack()
        mo.setCmd('m_des')
        mo.setResult('gameId', self.gameId)
        self.matchPlugin.getMatchInfo(self, userId, mo)
        router.sendToUser(mo, userId)

    def __getMatchStatas(self, userId):
        mo = MsgPack()
        mo.setCmd('m_update')
        player = self.match.findPlayer(userId)
        self.matchPlugin.getMatchStates(self, player, mo)
        router.sendToUser(mo, userId)

    def doUpdateInfo(self, userId):
        ftlog.debug("<<", "|userId, roomId:", userId, self.roomId, caller=self)

        self.__getMatchStatas(userId)
        self.__getMatchRanksQuick(userId)

    def __getUserMatchSigns(self, uid, signs):
        signs[self.bigRoomId] = 0
        player = self.match.findPlayer(uid)
        if not player:
            return
        if (player.inst.state >= MatchInstance.STATE_IDLE
            and player.inst.state < MatchInstance.STATE_STARTING):
            signs[self.bigRoomId] = 1
        if (player.inst.state >= MatchInstance.STATE_STARTING
            and player.inst.state < MatchInstance.STATE_FINISH):
            signs[self.bigRoomId] = 2

    def doSignin(self, userId, signinParams, feeIndex=0):
        ftlog.debug("<<", "|userId, roomId, signinParams:", userId, self.roomId, feeIndex, signinParams, caller=self)

        try:
            mo = MsgPack()
            mo.setCmd('m_signin')
            self.matchPlugin.ensureCanSignInMatch(self, userId, mo)
            player = self.match.signin(userId, signinParams, feeIndex)
            if TYPlayer.isHuman(userId):
                self.__notifyRobotSigninMatch(player)

            self.reportBiGameEvent("MATCH_SIGN_UP", userId, self.roomId, 0, 0, 0, 0, 0, [], 'match_signin')
        except MatchException, e:
            self.matchPlugin.handleMatchException(self, e, userId, mo)

        self.__getMatchStatas(userId)

        signs = {}
        self.__getUserMatchSigns(userId, signs)
        mo = MsgPack()
        mo.setCmd('m_signs')
        mo.setResult('gameId', self.gameId)
        mo.setResult('roomId', self.bigRoomId)
        mo.setResult('userId', userId)
        mo.setResult('signs', signs)
        mo.setResult('isAll', 0)
        router.sendToUser(mo, userId)

    def doSignout(self, userId):
        ftlog.debug("<<", "|userId, roomId:", userId, self.roomId, caller=self)

        mo = MsgPack()
        mo.setCmd('m_signout')
        mo.setResult('gameId', self.gameId)
        mo.setResult('roomId', self.bigRoomId)
        mo.setResult('userId', userId)
        try:
            if self.match.signout(userId):
                self.reportBiGameEvent("MATCH_SIGN_OUT", userId, self.roomId, 0, 0, 0, 0, 0, [], 'match_signout')
        except MatchException, e:
            self.matchPlugin.handleMatchException(self, e, userId, mo)

        router.sendToUser(mo, userId)

    def doGiveup(self, userId):
        ftlog.debug("<<", "|userId, roomId:", userId, self.roomId, caller=self)

        if not self.match.giveup(userId):
            mo = MsgPack()
            mo.setCmd('room')
            mo.setError(-1, '不能退出比赛')
            router.sendToUser(mo, userId)

    def doWinlose(self, msg):
        mid = msg.getParam('matchId', 0)
        tableId = msg.getParam('tableId', 0)
        ccrc = msg.getParam('ccrc', -1)

        ftlog.debug("<<", "|roomId, tableId, matchId:", self.roomId, tableId, mid, caller=self)

        userWinloseList = msg.getParam('users')
        assert isinstance(userWinloseList, list)

        allPlayers = []
        for userWinlose in userWinloseList:
            userId = userWinlose.get('userId', 0)
            seatId = userWinlose.get('seatId', 0)
            deltaScore = userWinlose.get('deltaScore', 0)
            if userId > 0:
                #                 ftlog.debug(
                #                     'roomId=', rid, 'tableId=', tid, 'ccrc=', ccrc,
                #                     'seatId=', sid, 'userId=', uid, 'deltaScore=', deltaChip)
                player = self.match.winlose(tableId, ccrc, seatId, userId, deltaScore, deltaScore >= 0)
                if player:
                    allPlayers.append(player)

                    # 记录玩家打败的对手，比较deltaScore
                    # 记录玩家的名次顺序
                    #         for i in range(0, len(allPlayers)):
                    #             player = allPlayers[i]
                    #             ftlog.debug("test rank index = ", i, "userId = ", player.userId, "oneplayer.rank = ", player.rank, 'tablerank = ', player.tableRank)

        try:
            for ele in allPlayers:
                # 找他的后一名
                ftlog.debug('test rank my rank = ', ele.tableRank, ' and find rank = ', ele.tableRank + 1)
                nextRankPlayer = self._findUserByTableRank(allPlayers, ele.tableRank + 1)
                if not nextRankPlayer:
                    ftlog.debug('not found')
                    continue
                ftlog.debug('find yet userID = ', nextRankPlayer.userId, ' name = ', nextRankPlayer.userName)
                ele.beatDownUserName = nextRankPlayer.userName
        except:
            ftlog.exception()

    def _findUserByTableRank(self, container, tableRank):
        for ele in container:
            if ele.tableRank == tableRank:
                return ele
        return None

    def doQuickStart(self, msg):
        assert self.roomId == msg.getParam("roomId")

        userId = msg.getParam("userId")
        shadowRoomId = msg.getParam("shadowRoomId")
        tableId = msg.getParam("tableId")
        clientId = msg.getParam("clientId")
        ftlog.info(getMethodName(), "<<", "|userId, clientId, roomId, shadowRoomId, tableId:", userId, clientId,
                   self.roomId, shadowRoomId, tableId)

        if tableId == self.roomId * 10000:
            isOk = True  # 玩家在队列里时断线重连
            player = self.match.findPlayer(userId)
            if player is None or not player.group:
                #             if player is None or not player.group:
                ftlog.warn(getMethodName(), '|room=', self.roomId,
                           'userId=', userId, 'not found player')
                onlinedata.removeOnlineLoc(userId, self.roomId, tableId)
                isOk = False
        else:
            isOk = False

        if isOk:
            reason = self.ENTER_ROOM_REASON_OK
            self.sendQuickStartRes(self.gameId, userId, reason, self.bigRoomId, self.match.tableId)
            # 如果用户已经被分组则发送等待信息
            if player.group:
                self.match.playerNotifier.notifyMatchWait(player, player.group)
        else:
            reason = self.ENTER_ROOM_REASON_INNER_ERROR
            info = u'在线状态错误或其他系统内部错误'
            self.sendQuickStartRes(self.gameId, userId, reason, self.bigRoomId, 0, info)

    def __getMatchRanksQuick(self, userId):
        player = self.match.findPlayer(userId)
        if not player or not player.group:
            return
        self.match.playerNotifier.notifyMatchRank(player, player.group)

    def __notifyRobotSigninMatch(self, player):
        ftlog.debug("<< |roomId, instId, playerId :", self.roomId, player.inst.instId, player.userId, caller=self)
        #         if hasattr(player.inst, "calledRobot") : #同一个比赛实例只召唤一次机器人
        #             return

        if player.inst.state >= player.inst.STATE_PREPARE:
            return

        if self.roomConf.get('hasrobot'):
            #             player.inst.calledRobot = True #同一个比赛实例只召唤一次机器人
            startConf = player.inst.conf.start
            if self.roomConf["robotUserMaxCount"] == -1:
                if startConf.isTimingType():
                    minsize = startConf.userMinCount
                else:
                    minsize = startConf.userCount - 2
            else:
                minsize = self.roomConf["robotUserMaxCount"]

            cur_p = len(player.inst.playerMap)
            if cur_p >= minsize:
                return

            mo = MsgPack()
            mo.setCmd('robotmgr')
            mo.setAction('callmatch')
            mo.setParam('gameId', self.gameId)
            mo.setParam('roomId', self.roomId)
            mo.setParam('robotCount', 4)
            router.sendRobotServer(mo, player.userId)

            func = functools.partial(self.__notifyRobotSigninMatch, player)
            FTTimer(15, func)
