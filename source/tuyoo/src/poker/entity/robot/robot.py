# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import random

from freetime.util import log as ftlog
from freetime.util.metaclasses import Singleton
from poker.entity.configure import gdata
from poker.entity.robot.robotevent import RobotEvent

TEST_ROBOT = False
MAX_ROBOT_UID = 10000


class TYRobotManager(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.freeRobotUsers = []
        self.busyRobotUsers = []
        self.eventQueue = []
        self.callUpDelaySecond = -1

    def callUpRobot(self, msg, roomId, tableId, userCount, seatCount, users):
        '''
        唤醒机器人 (由TABLE进程SEND命令触发, 无需响应)
        检查该桌子是否需要进入机器人
        具体的机器人进入策略由各个游戏自己负责
        '''
        ftlog.debug("<<|roomId, tableId, userCount, seatCount, users:", roomId, tableId, userCount, seatCount, users)
        roomConf = gdata.roomIdDefineMap()[roomId].configure
        delay = roomConf.get('robotUserCallUpTime', -1)
        if delay < 0:
            if self.callUpDelaySecond < 0:
                delay = 0
            else:
                delay = random.randint(0, self.callUpDelaySecond)  # 随机延迟进入
        evt = RobotEvent(delay, 'callup', msg, roomId, tableId, userCount, seatCount, users)
        self.eventQueue.append(evt)
        return

    def callUpRobotsToMatch(self, msg, roomId, robotCount):
        '''
        唤醒机器人参加比赛
        '''
        ftlog.debug("<<|roomId, robotCount:", roomId, robotCount, caller=self)
        for _ in xrange(robotCount):
            ru = self.popFreeRobotUser()
            ru.start(roomId, 0, True)

    def shutDownRobot(self, msg, roomId, tableId, userCount, seatCount, users):
        '''
        关闭机器人 (由TABLE进程SEND命令触发, 无需响应)
        检查该桌子是否需要关闭机器人
        具体的机器人关闭策略由各个游戏自己负责
        '''
        ftlog.debug("<<|roomId, tableId, userCount, seatCount, users:", roomId, tableId, userCount, seatCount, users)
        evt = RobotEvent(1, 'shutdown', msg, roomId, tableId, userCount, seatCount, users)
        self.eventQueue.append(evt)
        return

    def getRobotDetail(self, msg):
        '''
        取得当前游戏中机器人的运行状态 (由其他进程QUERY命令触发, 必须响应有效值)
        例如: 机器人的个数, 各个队列的长度等
        具体的内容由各个游戏自己负责
        '''
        return None

    def onHeartBeat(self, event):
        # 检索延迟时间到时的事件
        evts = []
        ques = []
        for x in xrange(len(self.eventQueue)):
            evt = self.eventQueue[x]
            evt.delayTime = evt.delayTime - 1
            if evt.delayTime <= 0:
                evts.append(evt)
            else:
                ques.append(evt)
        self.eventQueue = ques
        # 执行延迟时间到时的事件
        for x in xrange(len(evts)):
            try:
                self._processRobotEvent(evts[x])
            except:
                ftlog.error()
        # 触发所有的机器人的timer事件
        for ru in self.busyRobotUsers:
            try:
                ru.onTimer(event)
            except:
                ftlog.error()
        # 回收所有已经释放的机器人实例
        for x in xrange(len(self.busyRobotUsers) - 1, -1, -1):
            ru = self.busyRobotUsers[x]
            if not ru.isbusy:
                del self.busyRobotUsers[x]
                self.freeRobotUsers.append(ru)

    def isAllRobotOnTable(self, seats):
        if TEST_ROBOT:
            return False
        for s in seats:
            if s > MAX_ROBOT_UID:
                return False
        return True

    def popFreeRobotUser(self):
        ru = self.freeRobotUsers.pop()
        ru.isbusy = 1
        self.busyRobotUsers.append(ru)
        return ru

    def _processRobotEvent(self, evt):
        cmd = evt.cmd
        if cmd == 'callup':
            self._callUpRobot(*evt.argl)
            return 1
        if cmd == 'shutdown':
            self._shutDownRobot(*evt.argl)
            return 1
        return 0

    def _callUpRobot(self, msg, roomId, tableId, userCount, seatCount, users):
        '''
        唤醒机器人 (由TABLE进程SEND命令触发, 无需响应)
        检查该桌子是否需要进入机器人
        具体的机器人进入策略由各个游戏自己负责
        '''
        ftlog.debug(roomId, tableId, userCount, seatCount, users)

        # 如果全是机器人, 那么退出, 不做处理
        if self.isAllRobotOnTable(users):
            ftlog.debug('its all robot , _callUpRobot do nothing !')
            return

        # 如果座位已满,那么不做处理
        if userCount == seatCount:
            ftlog.debug('the seat is full , do nothing !')
            return

        # 取得一个空闲的机器人, 开始登陆, 坐下等流程, 
        # 此过程如果出现异常,必须保障ru.isbusy复位, 这样才能自动回收机器人资源
        ru = self.popFreeRobotUser()
        ru.start(roomId, tableId)

    def _shutDownRobot(self, msg, roomId, tableId, userCount, seatCount, users):
        '''
        斗地主目前全部是打完一局换桌, 那么再地主的机器人里面, 就不必处理shutdown消息
        机器人, 接收到game_win后, 自动的离开, 断开连接
        '''
        ftlog.debug(roomId, tableId, userCount, seatCount, users)
        # 如果全是机器人, 那么退出, 不做处理
        if self.isAllRobotOnTable(users):
            ftlog.debug('its not all robot , _shutDownRobot all robot user !', roomId, tableId)
            for ruser in self.busyRobotUsers:
                ftlog.debug('ruser.roomId=', ruser.roomId, ruser.tableId)
                if ruser.roomId == roomId and ruser.tableId == tableId:
                    if ruser._isMatch:
                        ftlog.debug('its a match room robot !, waiting for the m_over !')
                        return
                    ruser.doShutDown()
        else:
            ftlog.debug('its not all robot , _shutDownRobot do nothing !')
        return
