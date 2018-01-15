# -*- coding:utf-8 -*-
'''
Created on 2016年1月15日

@author: zhaojiangang
'''
import functools
import random

import freetime.util.log as ftlog
from freetime.core.timer import FTTimer
from freetime.entity.msg import MsgPack
from poker.entity.configure import gdata
from poker.entity.dao import onlinedata
from poker.entity.game.rooms.group_match_ctrl.config import MatchConfig
from poker.entity.game.rooms.group_match_ctrl.exceptions import MatchException
from poker.entity.game.rooms.group_match_ctrl.models import TableManager
from poker.entity.game.rooms.group_match_ctrl.utils import Logger
from poker.entity.game.rooms.room import TYRoom
from poker.entity.game.tables.table_player import TYPlayer
from poker.protocol import router


class TYGroupMatchRoom(TYRoom):
    def __init__(self, roomdefine):
        super(TYGroupMatchRoom, self).__init__(roomdefine)
        self.bigmatchId = self.bigRoomId
        self.matchPlugin = gdata.games()[self.gameId].getGroupMatchPlugin()
        self.match = None
        self.matchMaster = None
        self._logger = Logger()
        self._logger.add('roomId', self.roomId)
        self._logger.add('bigmatchId', self.bigmatchId)
        serverType = gdata.serverType()
        if serverType == gdata.SRV_TYPE_ROOM:
            self.initMatch()  # 此处会给self.match赋值

    def initMatch(self):
        assert (self.matchPlugin.getMatch(self.roomId) is None)
        self._logger.info('TYGroupMatchRoom.initMatch ...')
        conf = MatchConfig.parse(self.gameId, self.roomId, self.bigmatchId,
                                 self.roomConf['name'],
                                 self.matchConf)
        conf.tableId = self.roomId * 10000  # 用来表示玩家在房间队列的特殊tableId
        conf.seatId = 1

        tableManager = TableManager(self, conf.tableSeatCount)
        shadowRoomIds = self.roomDefine.shadowRoomIds

        self._logger.info('TYGroupMatchRoom.initMatch',
                          'shadowRoomIds=', list(shadowRoomIds))

        for roomId in shadowRoomIds:
            count = self.roomDefine.configure['gameTableCount']
            baseid = roomId * 10000
            self._logger.info('TYGroupMatchRoom.initMatch addTables',
                              'shadowRoomId=', roomId,
                              'tableCount=', count,
                              'baseid=', baseid)
            tableManager.addTables(roomId, baseid, count)
        random.shuffle(tableManager._idleTables)
        match, master = self.matchPlugin.buildMatch(conf, self)
        match.tableManager = tableManager

        if gdata.mode() == gdata.RUN_MODE_ONLINE:
            playerCapacity = int(tableManager.allTableCount * tableManager.tableSeatCount * 0.9)
            if playerCapacity <= conf.start.userMaxCountPerMatch:
                self._logger.error('TYGroupMatchRoom.initMatch',
                                   'allTableCount=', tableManager.allTableCount,
                                   'tableSeatCount=', tableManager.tableSeatCount,
                                   'playerCapacity=', playerCapacity,
                                   'userMaxCount=', conf.start.userMaxCount,
                                   'confUserMaxCountPerMatch=', conf.start.userMaxCountPerMatch,
                                   'err=', 'NotEnoughTable')
            assert (playerCapacity > conf.start.userMaxCountPerMatch)

        self.match = match
        self.matchMaster = master
        self.matchPlugin.setMatch(self.roomId, match)
        if master:
            master.start()
        match.start()

    def doEnter(self, userId):
        if self._logger.isDebug():
            self._logger.debug('TYGroupMatchRoom.doEnter',
                               'userId=', userId)
        mo = MsgPack()
        mo.setCmd('m_enter')
        mo.setResult('gameId', self.gameId)
        mo.setResult('roomId', self.roomId)
        mo.setResult('userId', userId)

        try:
            self.match.enter(userId)
        except MatchException, e:
            self.matchPlugin.handleMatchException(self, e, userId, mo)
        router.sendToUser(mo, userId)

    def doLeave(self, userId, msg):
        if self._logger.isDebug():
            self._logger.debug('TYGroupMatchRoom.doLeave',
                               'userId=', userId)
        mo = MsgPack()
        mo.setCmd('m_leave')
        mo.setResult('gameId', self.gameId)
        mo.setResult('roomId', self.roomId)
        mo.setResult('userId', userId)
        self.match.leave(userId)
        router.sendToUser(mo, userId)

    def doGetDescription(self, userId):
        if self._logger.isDebug():
            self._logger.debug('TYGroupMatchRoom.doGetDescription',
                               'userId=', userId)
        mo = MsgPack()
        mo.setCmd('m_des')
        mo.setResult('gameId', self.gameId)
        self.matchPlugin.getMatchInfo(self, userId, mo)
        router.sendToUser(mo, userId)

    def _getMatchStatas(self, userId):
        mo = MsgPack()
        mo.setCmd('m_update')
        self.matchPlugin.getMatchStates(self, userId, mo)
        router.sendToUser(mo, userId)

    def doUpdateInfo(self, userId):
        if self._logger.isDebug():
            self._logger.debug('TYGroupMatchRoom.doUpdateInfo',
                               'userId=', userId)
        self._getMatchStatas(userId)
        self._getMatchRanksQuick(userId)

    def _getUserMatchSigns(self, uid, signs):
        signs[self.bigRoomId] = 0
        if self.match.curInst:
            signer = self.match.curInst.findSigner(uid)
            if signer:
                signs[self.bigRoomId] = 1
                return
        player = self.match.findPlayer(uid)
        if player:
            signs[self.bigRoomId] = 2

    def doSignin(self, userId, signinParams, feeIndex=0):
        if self._logger.isDebug():
            self._logger.debug('TYGroupMatchRoom.doSignin',
                               'userId=', userId,
                               'feeIndex=', feeIndex,
                               'signinParams=', signinParams)

        try:
            mo = MsgPack()
            mo.setCmd('m_signin')
            self.matchPlugin.ensureCanSignInMatch(self, userId, mo)
            signer = self.match.signin(userId, signinParams, feeIndex)
            if TYPlayer.isHuman(userId):
                self._notifyRobotSigninMatch(signer)

            self.reportBiGameEvent('MATCH_SIGN_UP', userId, self.roomId, 0, 0, 0, 0, 0, [], 'match_signin')
        except MatchException, e:
            self.matchPlugin.handleMatchException(self, e, userId, mo)

        self._getMatchStatas(userId)

        signs = {}
        self._getUserMatchSigns(userId, signs)
        mo = MsgPack()
        mo.setCmd('m_signs')
        mo.setResult('gameId', self.gameId)
        mo.setResult('roomId', self.bigRoomId)
        mo.setResult('userId', userId)
        mo.setResult('signs', signs)
        mo.setResult('isAll', 0)
        router.sendToUser(mo, userId)

    def doSignout(self, userId):
        if self._logger.isDebug():
            self._logger.debug('TYGroupMatchRoom.doSignout',
                               'userId=', userId)

        mo = MsgPack()
        mo.setCmd('m_signout')
        mo.setResult('gameId', self.gameId)
        mo.setResult('roomId', self.bigRoomId)
        mo.setResult('userId', userId)
        try:
            if self.match.signout(userId):
                self.reportBiGameEvent('MATCH_SIGN_OUT', userId, self.roomId, 0, 0, 0, 0, 0, [], 'match_signout')
        except MatchException, e:
            self.matchPlugin.handleMatchException(self, e, userId, mo)

        router.sendToUser(mo, userId)

    def doGiveup(self, userId):
        if self._logger.isDebug():
            self._logger.debug('TYGroupMatchRoom.doGiveup',
                               'userId=', userId)

        if not self.match.giveup(userId):
            mo = MsgPack()
            mo.setCmd('room')
            mo.setError(-1, '不能退出比赛')
            router.sendToUser(mo, userId)

    def doWinlose(self, msg):
        mid = msg.getParam('matchId', 0)
        tableId = msg.getParam('tableId', 0)
        ccrc = msg.getParam('ccrc', -1)

        if self._logger.isDebug():
            self._logger.debug('TYGroupMatchRoom.doWinlose',
                               'mid=', mid,
                               'tableId=', tableId,
                               'ccrc=', ccrc)

        userWinloseList = msg.getParam('users')
        assert (isinstance(userWinloseList, list))

        allPlayers = []
        for userWinlose in userWinloseList:
            userId = userWinlose.get('userId', 0)
            seatId = userWinlose.get('seatId', 0)
            deltaScore = userWinlose.get('deltaScore', 0)
            if userId > 0:
                if self._logger.isDebug():
                    self._logger.debug('TYGroupMatchRoom.doWinlose',
                                       'mid=', mid,
                                       'tableId=', tableId,
                                       'ccrc=', ccrc,
                                       'userId=', userId,
                                       'seatId=', seatId,
                                       'deltaScore=', deltaScore)
                player = self.match.winlose(tableId, ccrc, seatId, userId, deltaScore, deltaScore >= 0)
                if player:
                    allPlayers.append(player)

        try:
            for ele in allPlayers:
                # 找他的后一名
                nextRankPlayer = self._findUserByTableRank(allPlayers, ele.tableRank + 1)
                if not nextRankPlayer:
                    continue
                ele.beatDownUserName = nextRankPlayer.userName
        except:
            ftlog.exception()

    def _findUserByTableRank(self, container, tableRank):
        for ele in container:
            if ele.tableRank == tableRank:
                return ele
        return None

    def doQuickStart(self, msg):
        userId = msg.getParam('userId')
        tableId = msg.getParam('tableId')
        shadowRoomId = msg.getParam('shadowRoomId')
        clientId = msg.getParam('clientId')

        self._logger.info('TYGroupMatchRoom.doQuickStart',
                          'userId=', userId,
                          'tableId=', tableId,
                          'shadowRoomId=', shadowRoomId,
                          'clientId=', clientId)

        if tableId == self.roomId * 10000:
            isOk = True  # 玩家在队列里时断线重连
            player = self.match.findPlayer(userId)
            if player is None:
                self._logger.warn('TYGroupMatchRoom.doQuickStart',
                                  'userId=', userId,
                                  'tableId=', tableId,
                                  'shadowRoomId=', shadowRoomId,
                                  'clientId=', clientId,
                                  'err=', 'NotFoundPlayer')
                try:
                    onlinedata.removeOnlineLoc(userId, self.roomId, tableId)
                except:
                    self._logger.error('TYGroupMatchRoom.doQuickStart',
                                       'userId=', userId,
                                       'tableId=', tableId,
                                       'shadowRoomId=', shadowRoomId,
                                       'clientId=', clientId)
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

    def _getMatchRanksQuick(self, userId):
        player = self.match.findPlayer(userId)
        if not player or not player.group:
            return
        self.match.playerNotifier.notifyMatchRank(player)

    def _notifyRobotSigninMatch(self, signer):
        if self._logger.isDebug():
            self._logger.warn('TYGroupMatchRoom._notifyRobotSigninMatch',
                              'userId=', signer.userId,
                              'instId=', signer.inst)

        if self.roomConf.get('hasrobot'):
            startConf = self.match.matchConf.start
            if self.roomConf['robotUserMaxCount'] == -1:
                if startConf.isTimingType():
                    minsize = startConf.userMinCount
                else:
                    minsize = startConf.userCount - 2
            else:
                minsize = self.roomConf['robotUserMaxCount']

            if signer.inst.signerCount >= minsize:
                return

            mo = MsgPack()
            mo.setCmd('robotmgr')
            mo.setAction('callmatch')
            mo.setParam('gameId', self.gameId)
            mo.setParam('roomId', self.bigRoomId)
            mo.setParam('robotCount', 4)
            router.sendRobotServer(mo, signer.userId)

            func = functools.partial(self._notifyRobotSigninMatch, signer)
            FTTimer(15, func)
