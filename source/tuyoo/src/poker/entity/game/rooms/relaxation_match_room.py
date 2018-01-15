# -*- coding:utf-8 -*-
'''
Created on 2016年6月7日

@author: luoguanggui
'''

import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack
from poker.entity.configure import gdata
from poker.entity.dao import userdata
from poker.entity.game.rooms.relaxation_match_ctrl.config import MatchConfig
from poker.entity.game.rooms.relaxation_match_ctrl.exceptions import MatchException
from poker.entity.game.rooms.relaxation_match_ctrl.match import MatchRelaxation
from poker.entity.game.rooms.relaxation_match_ctrl.models import Player
from poker.entity.game.rooms.room import TYRoom
from poker.protocol import router


class TYRelaxationMatchRoom(TYRoom):
    def __init__(self, roomdefine):
        super(TYRelaxationMatchRoom, self).__init__(roomdefine)
        self.bigmatchId = self.bigRoomId
        self.matchPlugin = gdata.games()[self.gameId].getRelaxationMatchPlugin()
        self.match = None
        self.matchMaster = None
        serverType = gdata.serverType()
        if serverType == gdata.SRV_TYPE_ROOM:
            self.initMatch()  # 此处会给self.match赋值

    def initMatch(self):

        ftlog.info('TYRelaxationMatchRoom.initMatch ...')
        conf = MatchConfig.parse(self.gameId, self.roomId, self.bigmatchId,
                                 self.roomConf['name'],
                                 self.matchConf)
        match = self.matchPlugin.buildMatch(conf, self)
        match.initTableManager(self, conf.tableSeatCount, self.bigmatchId)
        self.match = match
        self.matchPlugin.setMatch(self.roomId, match)
        match.start()

    def doEnter(self, userId):
        if ftlog.is_debug():
            ftlog.debug('TYRelaxationMatchRoom.doEnter',
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
        if ftlog.is_debug():
            ftlog.debug('TYRelaxationMatchRoom.doLeave',
                        'userId=', userId)
        self.match.leave(userId)
        super(TYRelaxationMatchRoom, self).doLeave(userId, msg)

    def doGetDescription(self, userId):
        if ftlog.is_debug():
            ftlog.debug('TYRelaxationMatchRoom.doGetDescription',
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
        if ftlog.is_debug():
            ftlog.debug('TYRelaxationMatchRoom.doUpdateInfo',
                        'userId=', userId)
        self._getMatchStatas(userId)
        self._getMatchRanksQuick(userId)

    def doWinlose(self, msg):
        tableId = msg.getParam('tableId', 0)
        if ftlog.is_debug():
            ftlog.debug('TYRelaxationMatchRoom.doWinlose',
                        'tableId=', tableId)
        userWinloseList = msg.getParam('users')
        assert (isinstance(userWinloseList, list))
        for userWinlose in userWinloseList:
            userId = userWinlose.get('userId', 0)
            seatId = userWinlose.get('seatId', 0)
            isWin = userWinlose.get('isWin', 0)
            deltaScore = userWinlose.get('deltaScore', 0)
            if userId > 0:
                if ftlog.is_debug():
                    ftlog.debug('TYRelaxationMatchRoom.doWinlose',
                                'tableId=', tableId,
                                'userId=', userId,
                                'seatId=', seatId,
                                'deltaScore=', deltaScore,
                                'isWin=', isWin)
                player = self.match.findPlayer(userId)
                self.match.winlose(player, deltaScore, isWin)
        # 归还桌子以及更新比赛排名
        table = self.match.findTable(tableId)
        if table:
            self.match.tableController.notifyTableClearTable(table)
            self.match.returnTable(table)

    def doQuickStart(self, msg):
        userId = msg.getParam('userId')
        tableId = msg.getParam('tableId')
        shadowRoomId = msg.getParam('shadowRoomId')
        clientId = msg.getParam('clientId')

        ftlog.info('TYRelaxationMatchRoom.doQuickStart',
                   'userId=', userId,
                   'tableId=', tableId,
                   'shadowRoomId=', shadowRoomId,
                   'clientId=', clientId)
        # 先判断比赛是否已经开始
        if self.match.state != MatchRelaxation.ST_START:
            mq = MsgPack()
            mq.setCmd('quick_start')
            mq.setResult('userId', userId)
            mq.setResult('gameId', self.gameId)
            mq.setResult('roomId', 0)
            mq.setResult('tableId', 0)
            mq.setResult('isMatch', 1)
            mq.setResult('seatId', 0)
            mq.setResult('reason', u'比赛还未开始！')
            # 发送用户的quick_start
            router.sendToUser(mq, userId)
            return

        # 从playerMap里取得玩家对象， 没有就创建
        player = self.match.findPlayer(userId)
        maxPlayCount = self.match.matchConf.start.maxPlayCount
        isNewPlayer = False
        if not player:
            isNewPlayer = True
            player = Player(userId)
            _, userName = userdata.getAttrs(userId, ['sessionClientId', 'name'])
            player.fillUserInfo(userName, clientId)
            self.match.addPlayer(player)
        elif player.playCount >= maxPlayCount:
            mq = MsgPack()
            mq.setCmd('quick_start')
            mq.setResult('userId', userId)
            mq.setResult('gameId', self.gameId)
            mq.setResult('roomId', 0)
            mq.setResult('tableId', 0)
            mq.setResult('isMatch', 1)
            mq.setResult('seatId', 0)
            mq.setResult('reason', u'你的比赛局数已超过上限')
            # 发送用户的quick_start
            router.sendToUser(mq, userId)
            return
        # 开始分配桌子
        table = self.match.tableManager.getTableSitdown(player)
        if table:
            # 发送通知发送quck_start
            self.match.onPlayerSitdown(player, table, isNewPlayer)
            self.match.tableController.notifyTableSendQuickStart(table, player)
        else:
            mq = MsgPack()
            mq.setCmd('quick_start')
            mq.setResult('userId', userId)
            mq.setResult('gameId', self.gameId)
            mq.setResult('roomId', 0)
            mq.setResult('tableId', 0)
            mq.setResult('isMatch', 1)
            mq.setResult('seatId', 0)
            mq.setResult('reason', u'比赛桌位已满，请稍后再试')
            # 发送用户的quick_start
            router.sendToUser(mq, userId)
            return

    def _getMatchRanksQuick(self, userId):
        player = self.match.findPlayer(userId)
        if player:
            self.match.playerNotifier.notifyMatchRank(player)
        else:
            self.match.playerNotifier.notifyMatchRankGuest(userId)
