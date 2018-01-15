# -*- coding:utf-8 -*-
'''
Created on 2016年1月25日

@author: zhaojiangang
'''
import functools
import random

import freetime.util.log as ftlog
from freetime.core.lock import FTLock
from freetime.core.timer import FTTimer
from poker.entity.game.rooms.group_match_ctrl.const import ScoreCalcType, \
    SeatQueuingType


class Lockable(object):
    def __init__(self):
        self.locker = FTLock(self.__class__.__name__ + '_%d' % id(self))


class Logger(object):
    def __init__(self, kvs=None):
        self._args = []
        if kvs:
            for k, v in kvs:
                self.add(k, v)

    def add(self, k, v):
        self._args.append('%s=' % (k))
        self._args.append(v)

    def info(self, prefix=None, *args):
        self._log(prefix, ftlog.info, *args)

    def hinfo(self, prefix=None, *args):
        self._log(prefix, ftlog.hinfo, *args)

    def debug(self, prefix=None, *args):
        self._log(prefix, ftlog.debug, *args)

    def warn(self, prefix=None, *args):
        self._log(prefix, ftlog.warn, *args)

    def error(self, prefix=None, *args):
        self._log(prefix, ftlog.error, *args)

    def isDebug(self):
        return ftlog.is_debug()

    def _log(self, prefix, func, *args):
        argl = []
        if prefix:
            argl.append(prefix)
        argl.extend(self._args)
        argl.extend(args)
        func(*argl)


class Heartbeat(object):
    ST_IDLE = 0
    ST_START = 1
    ST_STOP = 2

    def __init__(self, interval, target):
        self._interval = interval
        self._target = target
        self._state = Heartbeat.ST_IDLE
        self._timer = None
        self._logger = Logger()

    def start(self):
        assert (self._state == Heartbeat.ST_IDLE)
        self._state = Heartbeat.ST_START
        self._timer = FTTimer(self._interval, self._onTimer)

    def stop(self):
        if self._state == Heartbeat.ST_START:
            self._state = Heartbeat.ST_STOP
            if self._timer:
                t = self._timer
                self._timer = None
                t.cancel()

    def _onTimer(self):
        try:
            self._timer = None
            newInterval = self._target()
            if newInterval is not None:
                self._interval = newInterval
        except:
            self._logger.error()
            self._interval = 1
        if self._state == Heartbeat.ST_START:
            self._timer = FTTimer(self._interval, self._onTimer)


class HeartbeatAble(object):
    def __init__(self):
        self._heartbeatCount = 0
        self._postTaskList = []
        self._logger = Logger()
        self._heartbeat = Heartbeat(0, self._doHeartbeat)

    def postCall(self, func, *args, **kwargs):
        self.postTask(functools.partial(func, *args, **kwargs))

    def postTask(self, task):
        if self._heartbeat._state != Heartbeat.ST_STOP:
            self._postTaskList.append(task)

    def _startHeartbeat(self):
        self._heartbeat.start()

    def _stopHeartbeat(self):
        self._heartbeat.stop()

    def _doHeartbeat(self):
        self._heartbeatCount += 1
        self._processPostTaskList()
        return self._doHeartbeatImpl()

    def _processPostTaskList(self):
        if self._logger.isDebug():
            self._logger.debug('HeartbeatAble._processPostTaskList',
                               'taskCount=', len(self._postTaskList))
        taskList = self._postTaskList
        self._postTaskList = []
        for task in taskList:
            try:
                task()
            except:
                self._logger.error('task=', task)

    def _doHeartbeatImpl(self):
        raise NotImplemented()


class PlayerSort(object):
    @classmethod
    def cmpByScore(cls, p1, p2):
        if p1.score == p2.score:
            return cls.cmpBySigninTime(p1, p2)
        if p1.score < p2.score:
            return 1
        return -1

    @classmethod
    def cmpBySigninTime(cls, p1, p2):
        return cmp(p1.signinTime, p2.signinTime)

    @classmethod
    def cmpByTableRanking(cls, p1, p2):
        if p1.tableRank <= 0 and p2.tableRank <= 0:
            return cls.cmpByScore(p1, p2)
        if (p1.tableRank == p2.tableRank):
            return cls.cmpByScore(p1, p2)
        if p1.tableRank <= 0:
            return 1
        if p2.tableRank <= 0:
            return -1
        if p1.tableRank > p2.tableRank:
            return 1
        return -1


class PlayerScoreCalcImpl(object):
    def calc(self, score):
        raise NotImplemented()


class PlayerScoreCalcFixed(PlayerScoreCalcImpl):
    def __init__(self, value):
        self._value = value

    def calc(self, score):
        if self._value == 0:
            return score
        return int(self._value)


class PlayerScoreCalcPingFangGen(PlayerScoreCalcImpl):
    def calc(self, score):
        return int(score ** 0.5)


class PlayerScoreCalcBaiFenBi(PlayerScoreCalcImpl):
    def __init__(self, rate):
        self._rate = rate

    def calc(self, score):
        return int(score * self._rate)


class PlayerScoreCalcKaiFangFangDa(PlayerScoreCalcImpl):
    def __init__(self, base, middle):
        self._base = base
        self._middle = max(middle, 1)
        self._rate = self._base / self._middle ** 0.5

    def calc(self, score):
        if score < 0:
            score = 0
        return int((score ** 0.5) * self._rate)


class PlayerScoreCalc:
    _pingFangGenInstance = PlayerScoreCalcPingFangGen()

    @classmethod
    def makeCalc(cls, stageConf, playerList):
        calcType = stageConf.chipUser
        if calcType == ScoreCalcType.PING_FANG_GEN:
            return cls._pingFangGenInstance
        elif calcType == ScoreCalcType.BAI_FEN_BI:
            rate = float(stageConf.chipUserRate)
            return PlayerScoreCalcBaiFenBi(rate)
        elif calcType == ScoreCalcType.KAI_FANG_FANG_DA:
            base = float(stageConf.chipUserBase)
            middle = len(playerList) / 2
            ftlog.info('PlayerScoreCalc.makeCalc stageIndex=', stageConf.index,
                       'first=', playerList[0].score,
                       'last=', playerList[-1].score,
                       'middle=', middle,
                       'middleScore=', playerList[middle].score)
            return PlayerScoreCalcKaiFangFangDa(base, playerList[middle].score)
        else:
            return PlayerScoreCalcFixed(calcType)


class PlayerQueuingImpl(object):
    def sort(self, players):
        '''排序players，并返回排序后的列表'''
        raise NotImplemented()


class PlayerQueuingRandom(PlayerQueuingImpl):
    def sort(self, players):
        random.shuffle(players)
        return players


class PlayerQueuingSnake(PlayerQueuingImpl):
    def sort(self, players):
        # TODO
        return players


class PlayerQueuingScore(PlayerQueuingImpl):
    def sort(self, matchUserList):
        matchUserList.sort(PlayerSort.cmpByScore)
        return matchUserList


class PlayerQueuingSigninTime(PlayerQueuingImpl):
    def sort(self, matchUserList):
        matchUserList.sort(PlayerSort.cmpBySigninTime)
        return matchUserList


class PlayerQueuing(object):
    _defaultQueuing = PlayerQueuingRandom()
    _queuingMap = {
        SeatQueuingType.RANDOM: _defaultQueuing,
        SeatQueuingType.SNAKE: PlayerQueuingSnake(),
        SeatQueuingType.SEED: PlayerQueuingScore(),
        SeatQueuingType.SIGNIN_TIME: PlayerQueuingSigninTime()
    }

    @classmethod
    def sort(cls, queuingType, players):
        if queuingType in cls._queuingMap:
            return cls._queuingMap[queuingType].sort(players)
        return cls._defaultQueuing.sort(players)


class PlayerGrouping(object):
    @classmethod
    def groupingByGroupCount(cls, playerList, groupCount, tableSeatCount):
        # 计算按userCount分成groupCount组最合适的人数
        countPerGroup = len(playerList) / groupCount
        # 分组人数是tableSeatCount的倍数，选最接近的数
        countPerGroup += cls.calcFixCount(countPerGroup, tableSeatCount)
        ret = []
        pos = 0
        for _ in xrange(groupCount):
            nextPos = pos + countPerGroup
            ret.append(playerList[pos:nextPos])
            pos = nextPos

        rem = len(playerList) - pos
        if rem > 0:
            for i in xrange(groupCount):
                if pos >= len(playerList):
                    break
                ret[i].extend(playerList[pos:pos + tableSeatCount])
                pos += tableSeatCount
        return ret

    @classmethod
    def calcFixCount(cls, userCount, tableSeatCount):
        mod = userCount % tableSeatCount
        if mod == 0:
            return 0
        if mod != 0:
            add = tableSeatCount - mod
            if add < mod or (userCount - mod) < tableSeatCount:
                return add
            return -mod
        return 0

    @classmethod
    def groupingByMaxUserCountPerGroup(cls, playerList, userCount, tableSeatCount):
        groupCount = (len(playerList) + userCount - 1) / userCount
        # 计算按userCount分成groupCount组最合适的人数
        countPerGroup = len(playerList) / groupCount
        # 分组人数是tableSeatCount的倍数，选最接近的数
        countPerGroup += cls.calcFixCount(countPerGroup, tableSeatCount)
        countPerGroup = min(countPerGroup, userCount)
        ret = []
        pos = 0
        for _ in xrange(groupCount):
            nextPos = pos + countPerGroup
            ret.append(playerList[pos:nextPos])
            pos = nextPos

        rem = len(playerList) - pos
        if rem > 0:
            for i in xrange(groupCount):
                if pos >= len(playerList):
                    break
                addCount = min(tableSeatCount, userCount - len(ret[i]))
                ret[i].extend(playerList[pos:pos + addCount])
                pos += addCount
        return ret

    @classmethod
    def groupingByFixedUserCountPerGroup(cls, playerList, userCount):
        pos = 0
        ret = []
        while (pos < len(playerList)):
            nextPos = pos + userCount
            ret.append(playerList[pos:nextPos])
            pos = nextPos
        return ret


class GroupNameGenerator(object):
    GROUP_NAME_PREFIX = [chr(i) for i in range(ord('A'), ord('Z') + 1)]

    @classmethod
    def generateGroupName(cls, groupCount, i):
        assert (i >= 0 and i < groupCount)
        groupName = GroupNameGenerator.GROUP_NAME_PREFIX[i % len(GroupNameGenerator.GROUP_NAME_PREFIX)]
        if groupCount > len(GroupNameGenerator.GROUP_NAME_PREFIX):
            number = i + 1
            if number % len(GroupNameGenerator.GROUP_NAME_PREFIX) != 0:
                groupName += '%s' % (number / len(GroupNameGenerator.GROUP_NAME_PREFIX) + 1)
            else:
                groupName += '%s' % (number / len(GroupNameGenerator.GROUP_NAME_PREFIX))
        return groupName + '组'
