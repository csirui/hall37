# coding=UTF-8
'''
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import functools

from freetime.core.timer import FTTimer
from freetime.entity.msg import MsgPack
from freetime.util import log as ftlog
from poker.protocol import router


class DiFangTableSenderMixin(object):
    '''
    桌子使用的发送消息的工具集合类
    '''

    def createMsgPackRes(self, cmd, action=None):
        mp = MsgPack()
        mp.setCmd(cmd)
        if action:
            mp.setResult('action', action)
        mp.setResult('gameId', self.table.gameId)
        mp.setResult('roomId', self.table.bigRoomId)  # 客户端和GT之间传递的roomId都是bigRoomId
        mp.setResult('tableId', self.table.tableId)
        return mp

    def createMsgPackRequest(self, cmd, action=None):
        mp = MsgPack()
        mp.setCmd(cmd)
        if action:
            mp.setParam('action', action)
        mp.setParam('gameId', self.table.gameId)
        mp.setParam('roomId', self.table.room.ctrlRoomId)  # 目标进程是GR
        mp.setParam('tableId', self.table.tableId)
        return mp

    def sendToAllTableUser(self, mo, exclude=None):
        if ftlog.is_debug():
            ftlog.debug('<< |tableId:', self.tableId,
                        '|len players=', self.table.playersNum,
                        'len observers=', self.table.observers,
                        'exclude=', exclude,
                        '|mo:', mo, caller=self)
        if isinstance(mo, MsgPack):
            mo = mo.pack()
        if exclude == None:
            exclude = []
        for p in self.table.players:
            if p.userId > 0 and not p.userId in exclude:
                router.sendToUser(mo, p.userId)
        for userId in self.table.observers:
            router.sendToUser(mo, userId)

    def sendQuickStartRes(self, userId, clientId, result):
        if ftlog.is_debug():
            ftlog.debug("<< |params", userId, clientId, result, caller=self)
        mpSitRes = self.createMsgPackRes("quick_start")
        mpSitRes.updateResult(result)
        router.sendToUser(mpSitRes, userId)

    @classmethod
    def sendNotifyMsg(cls, gameId, uid, showTime, content):
        """
        {
            "cmd": "notifyMsg",
            "result":
            {
                "showTime": 0.5,
                "content": [{
                    "color": "RRGGBB",
                    "text": "bababababa"
                }, {
                    "color": "RRGGBB",
                    "text": "bababababa"
                }]
            }
        }
        """

        msg_content = [dict(zip(("color", "text"), segment)) for segment in content]

        message = MsgPack()
        message.setCmd('notifyMsg')
        message.setResult("userId", uid)
        message.setResult("gameId", gameId)
        message.setResult("showTime", showTime)
        message.setResult("content", msg_content)

        router.sendToUser(message, uid)

    def queryRoomEnterReq(self, userId):
        mpReqRoomEnter = self.createMsgPackRequest("room", "enter")
        mpReqRoomEnter.setParam("userId", userId)
        mpReqRoomEnter.setParam('roomId', self.table.room.ctrlRoomId)
        router.queryRoomServer(mpReqRoomEnter, self.table.room.ctrlRoomId)

    def sendRoomLeaveReq(self, userId, reason, needSendRes=True):
        mpReqRoomLeave = self.createMsgPackRequest("room", "leave")
        mpReqRoomLeave.setParam("userId", userId)
        mpReqRoomLeave.setParam('roomId', self.table.room.ctrlRoomId)
        mpReqRoomLeave.setParam('reason', reason)
        mpReqRoomLeave.setParam('needSendRes', needSendRes)
        router.sendRoomServer(mpReqRoomLeave, self.table.room.ctrlRoomId)

    def sendRobotNotifyCallUp(self, params):
        hasrobot = self.table.runConfig.get("hasrobot", 0)
        if ftlog.is_debug():
            ftlog.debug("|hasrobot, params", hasrobot, params, caller=self)
        if hasrobot:
            if params and params['test']:
                ucount, uids = 0, [0] * self.table.cMaxSeatNum
            else:
                ucount, uids = self.getSeatUserIds()
            mo = self.createMsgPackRequest("robotmgr")
            if params:
                mo.updateParam(params)
            mo.setAction('callup')
            mo.setParam('userCount', ucount)
            mo.setParam('seatCount', len(uids))
            mo.setParam('users', uids)
            router.sendRobotServer(mo, self.tableId)

    def sendRobotNotifyShutDown(self, params):
        hasrobot = self.table.runConfig["hasrobot"]
        if ftlog.is_debug():
            ftlog.debug("|hasrobot, params", hasrobot, params, caller=self)
        if hasrobot:
            ucount, uids = self.getSeatUserIds()
            mo = self.createMsgPackRequest("robotmgr")
            if params:
                mo.updateParam(params)
            mo.setAction('shutdown')
            mo.setParam('userCount', ucount)
            mo.setParam('seatCount', len(uids))
            mo.setParam('users', uids)
            router.sendRobotServer(mo, self.tableId)

    def getTableLabel(self):
        return self.cName

    def sendTableLabelRes(self):
        mpRes = self.createMsgPackRes("table_call", "table_label")
        mpRes.setResult('tableLabel', self.getTableLabel())
        self.sendToAllTableUser(mpRes)

    def sendTableInfoRes(self, seatId=0, userId=-1):
        mpRes = self.createMsgPackRes("table", "info")
        self.sendToAllTableUser(mpRes)

    def sendTableCallReadyRes(self, player):
        mpRes = self.createMsgPackRes("table_call", 'ready')
        mpRes.setResult("seatId", player.seatIndex)
        mpRes.setResult("userId", player.userId)
        self.sendToAllTableUser(mpRes)

    def sendHoleCardsResToAll(self):
        ''' 给所有人发消息，触发前端发牌动画 '''
        mpSendHoleCardsRes = self.createMsgPackRes("table_call", "send_hole_cards")
        self.sendToAllTableUser(mpSendHoleCardsRes)

    def sendTableCallGameStartRes(self):
        mpRes = self.createMsgPackRes("table_call", 'game_start')
        self.sendToAllTableUser(mpRes)

    def sendGameWinRes(self, delay=0):
        mpRes = self.createMsgPackRes("table_call", 'game_win')

        if delay:
            func = functools.partial(self.sendToAllTableUser, mpRes)
            FTTimer(delay, func)
        else:
            self.sendToAllTableUser(mpRes)

    def sendPlayerDataToAll(self, userId, *arglist, **keywords):
        mpPlayerDataRes = self.createMsgPackRes("table_call", "playerData")
        mpPlayerDataRes.setResult('userId', userId)
        player = self.getPlayer(userId)
        if player:
            mpPlayerDataRes.setResult('seatId', player.seatIndex)
        # if 'userChips' in keywords :
        #             mpPlayerDataRes.setResult('userChips', keywords['userChips'])
        if 'ranking' in keywords:
            mpPlayerDataRes.setResult('ranking', keywords['ranking'])
        if 'managed' in keywords:
            mpPlayerDataRes.setResult('managed', keywords['managed'])
        self.sendToAllTableUser(mpPlayerDataRes)
        self.tableRecord.addResMsg(mpPlayerDataRes)

    # def sendVoteDismissNotifyResToAll(self):
    #     mpRes = self.createMsgPackRes("table_call", 'vote_dismiss_notify')
    #     mpRes.setResult('firstVoteName', self.firstVotePlayer.name)
    #     mpRes.setResult("voteTime", self.cVoteDismissTime)
    #     self.sendToAllTableUser(mpRes)

    def sendVoteDismissRes(self, player, agree):
        mpRes = self.createMsgPackRes("table_call", 'vote_dismiss')
        mpRes.setResult('firstVoteName', self.firstVotePlayer.name)
        mpRes.setResult("voteTime", self.cVoteDismissTime)
        mpRes.setResult("userId", player.userId)
        mpRes.setResult('seatId', player.seatIndex)
        mpRes.setResult("name", player.name)
        mpRes.setResult("agree", agree)
        self.sendToAllTableUser(mpRes)
        self.tableRecord.addResMsg(mpRes)

    def sendPingRes(self, userId, pingDelays, timeStamp):
        """下发玩家网络状况
        """
        mpRes = self.createMsgPackRes("table_call", 'ping')
        mpRes.setResult('timeStamp', timeStamp)
        mpRes.setResult('pingDelays', pingDelays)  # [10,100,20,10]
        router.sendToUser(mpRes, userId)
