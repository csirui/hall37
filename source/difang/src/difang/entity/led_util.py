# -*- coding=utf-8 -*-
'''
'''
__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import json
import time

import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack
from hall.servers.util.rpc import user_remote
from poker.entity.dao import sessiondata, gamedata
from poker.servers.conn.rpc import onlines

# led consts
LED_ON = True  # led开关
RICH_TEXT_LED_MSG_HEADER = 'richTextLedMsg'  # 彩色LED头
SEND_COUNT_LIMIT = 100


# LED工具类
class LedUtils(object):
    @classmethod
    def mkRichTextBody(cls, content):
        return [{'color': color, 'text': text} for color, text in content]

    @classmethod
    def _mkRichTextLedBody(cls, content, _type='led', roomId=0, tableId=0):
        """ _type:
        led      纯LED消息，带颜色
        watch    LED消息，带颜色，观战按钮
        vip      LED消息，带颜色，进入（坐下）按钮
        mtt
        """

        richText = {
            'text': cls.mkRichTextBody(content),
            'type': _type,
            'roomId': roomId,
            'tableId': tableId
        }

        return RICH_TEXT_LED_MSG_HEADER + json.dumps({'richText': richText})

    @classmethod
    def sendLed(cls, gameId, plain_text):
        """发送一条GDSS那样的LED消息。玩家会在心跳协议中陆续收到该消息
        """
        content = [['FFFFFF', plain_text]]
        cls.sendColorfulLed(gameId, content)

    @classmethod
    def sendColorfulLed(cls, gameId, content, scope=None):
        """ 发送一条彩色LED消息
        gameId - 参数，gameId
        content - 参数，LED发送内容
        """
        if not LED_ON:
            ftlog.debug("<< not LED_ON")
            return

        if not scope:
            scope = "hall%d" % gameId
        user_remote.sendHallLed(gameId, json.dumps({'text': cls.mkRichTextBody(content)}), ismgr=1, scope=scope)

    @classmethod
    def sendGameLed(cls, msgPackIn):
        '''
        '''
        if not LED_ON:
            ftlog.debug("<< not LED_ON")
            return

        if ftlog.is_debug():
            ftlog.debug("<< |msgPackIn:", msgPackIn, caller=cls)

        gameId = msgPackIn.getResult('gameId', 0)
        if gameId <= 0:
            ftlog.warn("gameId <=0", gameId, caller=cls)
            return

        ledWithTodoTask = msgPackIn.getResult('ledWithTodoTask')
        if not ledWithTodoTask:
            ftlog.warn("ledWithTodoTask is None!", caller=cls)
            return
        ledMsg = MsgPack()
        ledMsg.setCmd('led')
        ledMsg.setKey('result', ledWithTodoTask)

        receivers = msgPackIn.getResult('receivers')
        if not receivers:
            ftlog.warn("receivers is None!", caller=cls)
            return

        excludeUsers = msgPackIn.getResult('excludeUsers', set())

        force = msgPackIn.getResult('force', [])  # 这里指定的用户不能过滤，必须收
        #         receivers = receivers + force

        timelimit = msgPackIn.getResult('timelimit', {})
        intervals = timelimit.get('timeLimitIntervals')  # 这个时间内收过led的不再收
        limitName = timelimit.get('timeLimitName')  # 时间间隔的种类，反射机制设置到 user 对象中去

        sendLedCount = [0]  # 为了控制每次发送的led数量，使用list类型是为了在闭包里能修改此值

        def sendled():
            clientVer = sessiondata.getClientIdVer(userId)
            if clientVer < 3.6:
                return

            if sendLedCount[0] <= SEND_COUNT_LIMIT:
                sendLedCount[0] += 1
                if ftlog.is_debug():
                    ftlog.debug("|send led count:", sendLedCount, caller=cls)
                if sendLedCount[0] % 10 == 0:
                    if ftlog.is_debug():
                        ftlog.info("|send led count:", sendLedCount, caller=cls)
                onlines.notifyUsers(ledMsg.pack(), [userId])

        # 需求：两次同类型led之间需要相隔intervals
        now = time.time()
        if ftlog.is_debug():
            ftlog.info("|len of receivers:", len(receivers), caller=cls)

        for userId in receivers:
            if userId in force:
                if limitName:
                    gamedata.setGameAttr(userId, gameId, limitName, now)
                sendled()
                continue

            if userId not in excludeUsers:
                if limitName and intervals:  # 时间限制
                    lastSendTime = gamedata.getGameAttr(userId, gameId, limitName)
                    if not lastSendTime:
                        lastSendTime = 0
                    if ftlog.is_debug():
                        ftlog.debug('|userId, limitName, intervals, lastSendTime, now:',
                                    userId, limitName, intervals, lastSendTime, now, caller=cls)
                    if lastSendTime + intervals <= now:
                        gamedata.setGameAttr(userId, gameId, limitName, now)
                        sendled()
                else:
                    sendled()
