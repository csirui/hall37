# coding=UTF-8
'''
    玩家操作处理模块
'''
from poker.entity.game.rooms.room import TYRoom

__author__ = ['Zhou Hao']

import functools
import time

from freetime.util import log as ftlog

from hall.entity.todotask import TodoTaskShowInfo, TodoTaskHelper

from difang.gameplayer.players_helper import DiFangPlayersHelper


class DiFangPlayerActionHelper(object):
    '''处理玩家的操作
    '''

    @classmethod
    def applyDismiss(cls, table, player):
        userId, seatIndex = player.userId, player.seatIndex
        if ftlog.is_debug():
            ftlog.debug("<<", table.gamePlay.getBasicAttrsLog(),
                        "|", "userId, seatIndex:", userId, seatIndex, caller=cls)

        nowTime = int(time.time())
        tip = u"您好,解散申请冷却中,\n请1分钟后再申请。"
        if nowTime - player.lastApplyDismissTime < 60:
            TodoTaskHelper.sendTodoTask(table.gameId, player.userId, TodoTaskShowInfo(tip, True))
            return False

        player.lastApplyDismissTime = nowTime
        player.isVotedDismiss = True
        table.firstVotePlayer = player
        # table.agreeN = 0

        func = functools.partial(cls.doAllAgree, table)
        table.callLaterFunc(table.cVoteDismissTime, func, 0, table.tableTimer, {})

        return True

        # table.sendVoteDismissNotifyResToAll()

    @classmethod
    def doAllAgree(cls, table):
        table.agreeN = table.cMaxSeatNum
        if table.gamePlay.gameSeq > 0:
            table.addTableRecord()
        table._applyAdjustTablePlayers()

    @classmethod
    def onEventVoteDismiss(cls, table, player, msg):
        userId, seatIndex = player.userId, player.seatIndex
        if ftlog.is_debug():
            ftlog.debug("<<", table.gamePlay.getBasicAttrsLog(),
                        "|", "userId, seatIndex:", userId, seatIndex,
                        "|table.agreeN:", table.agreeN, caller=cls)

        # 支持未坐满时散桌
        if table.gamePlay.gameSeq == 0:
            if player.userId == table.firstPlayerId:  # 房主解散牌桌
                cls.doAllAgree(table)
            else:  # 非房主离开牌桌
                table.sendRoomLeaveReq(userId, TYRoom.LEAVE_ROOM_REASON_SYSTEM, needSendRes=True)
            return

        agree = msg.getParam("agree")
        if not agree:
            table.tableTimer.cancel()
            table.agreeN = 0
            for player in table.players:
                player.isVotedDismiss = False
        else:
            if player.isVotedDismiss:  # 防止同一玩家重复投票
                return

            if table.agreeN == table.playersNum:
                ftlog.warn("onEventVoteDismiss duplicate vote",
                           "|", "userId, seatIndex:", userId, seatIndex,
                           "|table.agreeN:", table.agreeN, caller=cls)
                return

            table.agreeN += 1
            if table.agreeN == 1:
                if not cls.applyDismiss(table, player):
                    table.agreeN = 0
                    return
            if table.agreeN == table.cMaxSeatNum:
                cls.doAllAgree(table)

        table.sendVoteDismissRes(player, agree)

    @classmethod
    def onEventReady(cls, table, player, msg):
        '''准备、继续
        '''
        userId, seatIndex = player.userId, player.seatIndex
        if ftlog.is_debug():
            ftlog.debug("<<", table.gamePlay.getBasicAttrsLog(),
                        "|", "userId, seatIndex:", userId, seatIndex, caller=cls)

        if not table.gamePlay.isWaitingState():
            ftlog.warn("not table.gamePlay.isWaitingState() |", table.gamePlay.getBasicAttrsLog(),
                       "|", "userId, seatIndex:", userId, seatIndex, caller=cls)
            return

        player.ready()
        if ftlog.is_debug():
            ftlog.debug(table.gamePlay.getBasicAttrsLog(), "|table.playersNum, table.cMaxSeatNum, isAllReady:",
                        table.playersNum, table.cMaxSeatNum, DiFangPlayersHelper.isAllReady(table), caller=cls)
        if table.playersNum == table.cMaxSeatNum and DiFangPlayersHelper.isAllReady(table):
            table.gamePlay.doActionCheckStartGame()

    @classmethod
    def onEventChuPai(cls, table, player, msg):
        ''' 出牌
        '''
        userId, seatIndex = player.userId, player.seatIndex
        cards = msg.getParam("cards")
        cardValue = msg.getParam("cardValue", 0)

        ftlog.info("onEventChuPai <<", table.gamePlay.getBasicAttrsLog(),
                   "|userId, seatIndex:", userId, seatIndex,
                   "|cards, cardValue:", cards, cardValue, caller=cls)

        if not table.gamePlay.isChuPaiState():
            ftlog.warn("not table.gamePlay.isChuPaiState() |", table.gamePlay.getBasicAttrsLog(),
                       "|", "userId, seatIndex:", userId, seatIndex, caller=cls)
            return

        if table.gamePlay.chuPaiRound.actorPos != player.seatIndex:
            ftlog.warn("table.gamePlay.chuPaiRound.actorPos != player.seatIndex|", table.gamePlay.getBasicAttrsLog(),
                       "|", "userId, seatIndex, actorPos:", userId, seatIndex, table.gamePlay.chuPaiRound.actorPos,
                       caller=cls)
            return

        if cards:
            if not cls.doChuPai(table, userId, player, cards, playerCardValue=cardValue):
                return
        else:
            if not cls.doGuoPai(table, player):
                return

        # 操作合法
        # player.actTimeOutN = 0  # 未操作次数清0
        table.seatTimers[player.seatIndex].cancel()  # 这个时候才取消timer

        if ftlog.is_debug():
            ftlog.debug(table.gamePlay.getBasicAttrsLog(), "|userId:", player.userId,
                        "|player.holeCards:", player.holeCards, caller=cls)

        if player.holeCards:
            func = functools.partial(table.gamePlay.chuPaiRound.chuPaiInTurn)
            table.callLaterFunc(0, func)
        else:
            func = functools.partial(table.gamePlay.chuPaiRound.chuPaiRoundOver)
            table.callLaterFunc(2, func)

    @classmethod
    def doGuoPai(cls, table, player):
        pass

    @classmethod
    def doChuPai(cls, table, userId, player, cards, playerCardValue=0):
        pass

    @classmethod
    def onEventPing(cls, table, player, msg):
        """获取桌友网络延迟
        """
        timeStamp = msg.getParam('timeStamp', 0)
        pingDelay = msg.getParam('pingDelay', 0)

        player.lastPingTimeStamp = timeStamp
        player.pingDelay = pingDelay

        pingDelays = []
        for p in table.players[:table.cMaxSeatNum]:
            pingDelays.append(p.pingDelay)

        table.sendPingRes(player.userId, pingDelays, timeStamp)
