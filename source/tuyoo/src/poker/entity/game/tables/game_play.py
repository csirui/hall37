# coding=UTF-8
'''
    经典玩法模块
'''
__author__ = ['Zhou Hao']

import functools
import time

from freetime.util import log as ftlog


class TYGamePlay(object):
    '''玩法基类
    '''

    # 游戏阶段状态值
    GAME_PLAY_STATE_WAIT = 0  # 准备阶段, 桌子上已经有人, 或者在队列里等待调度
    GAME_PLAY_STATE_START = 1  # 开局阶段
    GAME_PLAY_STATE_FINAL = 8  # 结算阶段

    # 客户端不使用状态字符串，服务端仅用来打日志
    gamePlayStateStrs = {
        GAME_PLAY_STATE_WAIT: "WAIT",
        GAME_PLAY_STATE_START: "START",
        GAME_PLAY_STATE_FINAL: "FINAL",
    }

    def __init__(self, table):
        self.table = table

        self._initField()

        self.transitToStateWait()

        if ftlog.is_debug():
            ftlog.info("__init__ >>", self.getBasicAttrsLog())

    def getBasicAttrsLog(self, caller=None):
        if caller == None:
            caller = self
        return "%s |%s %s %s %s" % (
            caller.__class__.__name__, self.table.tableId, self.gameSeq, self.table.playersNum, self.getStateStr())

    def _initField(self):
        '''初始化类字段
        '''
        self.gameSeq = 0  # 游戏局自增长ID

        self.anpaiMode = False  # 是否暗牌模式，Gamble框架中要调用，默认为False
        self.sharedCards = []  # 公用插件（BiReporter）里会读取

        # self.foldedPlayerBets = []  # Player.doFold 里会操作

    def _initGamePlayData(self):
        '''新的一局开始前做数据初始化
        '''
        self.table.cancelTimerAll()
        self.startTime = 0  # 开局时间点
        self.gameEndDelayTime = 0

    @property
    def _state(self):
        return self.__state

    def setState(self, state):
        self.__state = state

    def transitToStateWait(self):
        self.__state = self.GAME_PLAY_STATE_WAIT
        ftlog.info("transitToStateWait <<", self.getBasicAttrsLog())

        self._initGamePlayData()

    def doActionCheckStartGame(self):
        '''检查游戏人数是否达到开局要求
        Note： 先补足筹码，然后踢掉筹码不足的玩家
        '''
        ftlog.debug("<<", self.getBasicAttrsLog(), caller=self)
        if self.__state != self.GAME_PLAY_STATE_WAIT:
            ftlog.warn("doActionCheckStartGame state error!", self.getBasicAttrsLog())
            return False

    def _calcGameStartAnimatTime(self):
        '''计算游戏开始动画时间
        '''
        return 0

    def transitToStateStartGame(self):
        '''准备开始游戏, 减抽水、下前注、确定庄家和大小盲注
        '''
        self.__state = self.GAME_PLAY_STATE_START
        self.gameSeq += 1
        self.startTime = time.time()
        ftlog.info("transitToStateStartGame <<", self.getBasicAttrsLog())

    def _calcDealCardAnimatTime(self):
        '''计算发牌动画时间
        '''
        return 0

    def _calcGameWinAnimatTime(self):
        '''计算游戏结束动画时间
        '''
        return self.gameEndDelayTime

    def transitToStateFinal(self):
        self.__state = self.GAME_PLAY_STATE_FINAL
        ftlog.info("transitToStateFinal <<", self.getBasicAttrsLog(), caller=self)

        func = functools.partial(self.doActionGameEnd)
        self.table.callLaterFunc(self._calcGameWinAnimatTime(), func)

    def doActionGameEnd(self):
        if ftlog.is_debug():
            ftlog.info("doActionGameEnd <<", self.getBasicAttrsLog(), caller=self)
        if self.__state != self.GAME_PLAY_STATE_FINAL:
            ftlog.warn("state error!", self.getBasicAttrsLog(), caller=self)
            return

        self.transitToStateWait()

    '''
            功能性 函数
    '''

    def getStateStr(self):
        return self.gamePlayStateStrs[self.__state]

    def isWaitingState(self):
        return self.__state == self.GAME_PLAY_STATE_WAIT

    def isStartState(self):
        return self.__state == self.GAME_PLAY_STATE_START

    def isFinalState(self):
        return self.__state == self.GAME_PLAY_STATE_FINAL

    def isActionState(self):
        '''玩家可操作状态
        '''
        return self.GAME_PLAY_STATE_START < self.__state < self.GAME_PLAY_STATE_FINAL

    def isPlayingState(self):
        '''游戏已开始，玩牌状态； 此时玩家站起，需做弃牌处理。
        '''
        return self.GAME_PLAY_STATE_START <= self.__state < self.GAME_PLAY_STATE_FINAL

    def getStateScore(self):  # 公用插件（BiReporter）里会读取
        return 0
