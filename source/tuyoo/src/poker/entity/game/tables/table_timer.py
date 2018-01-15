# -*- coding: utf-8 -*-
'''
Created on 2015年7月7日

@author: zqh
'''
import stackless

from freetime.core.timer import FTTimer
from freetime.entity.msg import MsgPack
from poker.protocol import runcmd


class TYTableTimer(object):
    '''
    桌子使用的专用的计时器, 当计时器触发时, 触发桌子的同步方法:doTableCall
    '''

    def __init__(self, table):
        self._table = table  # 桌子对象
        self._fttimer = None  # 计时器对象
        self._interval = 0  # 倒计时时间,单位: 秒

    def _onTimeOut(self):
        '''
        计时器到时, 触发table的doTableCall方法
        '''
        msg = stackless.getcurrent()._fttask.run_argl[0]
        seatId = msg.getParam('seatId')
        if seatId == None:
            seatId = 0
        userId = msg.getParam('userId')
        if userId == None:
            userId = 0
        assert (isinstance(userId, int))
        assert (isinstance(seatId, int))
        action = msg.getParam('action')
        clientId = runcmd.getClientId(msg)
        self._table.doTableCall(msg, userId, seatId, action, clientId)

    def setup(self, interval, action, msgPackParams, cancelLastTimer=True):
        '''
        启动计时器
        interval 倒计时的时间, 单位: 秒
        action table_call命令下(params中)的action值
        msgPackParams 传递的其他的参数数据集合dict, 可以在doTableCall中的msg中使用msg.getParam(key)来取得其中的参数
        '''
        if self._fttimer and cancelLastTimer:
            self._fttimer.cancel()
        self._interval = interval
        userId = msgPackParams.get('userId', 0)
        clientId = msgPackParams.get('clientId', None)
        assert (isinstance(userId, int))
        assert (isinstance(action, (unicode, str)))
        if clientId != None:
            assert (isinstance(clientId, (unicode, str)))
        msg = MsgPack()
        msg.updateParam(msgPackParams)
        msg.setCmdAction('table_call', action)
        msg.setParam('gameId', self._table.gameId)
        msg.setParam('roomId', self._table.roomId)
        msg.setParam('tableId', self._table.tableId)
        msg.setParam('userId', userId)
        msg.setParam('clientId', clientId)
        self._fttimer = FTTimer(interval, self._onTimeOut, msg)

    def cancel(self):
        '''
        取消当前的计时器
        '''
        if self._fttimer:
            self._fttimer.cancel()
            self._fttimer = None

    def reset(self, interval):
        '''
        重置当前的计时器
        '''
        self._interval = interval
        self._fttimer.reset(interval)

    def getInterval(self):
        '''
        取得当前计时器的倒计时时间
        '''
        return self._interval

    def getTimeOut(self):
        '''
        取得当前计时器的剩余的倒计时时间, 若没有开始倒计时, 那么返回0
        '''
        if self._fttimer:
            time = self._fttimer.getTimeOut()
            if time < 0 or time > 3600:
                time = 0
            return time
        return 0
