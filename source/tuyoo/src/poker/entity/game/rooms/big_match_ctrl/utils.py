# -*- coding:utf-8 -*-
'''
Created on 2014年9月22日

@author: zjgzzz@126.com
'''
import random
import time

from poker.entity.game.rooms.big_match_ctrl.const import ChipCalcType, SeatQueuingType


class Utils(object):
    currentTimestamp = None

    @classmethod
    def timestamp(cls):
        if cls.currentTimestamp:
            return cls.currentTimestamp
        return int(time.time())


class PlayerSort(object):
    @classmethod
    def cmpByChip(cls, p1, p2):
        if p1.chip == p2.chip:
            return cls.cmpBySigninTime(p1, p2)
        if p1.chip < p2.chip:
            return 1
        return -1

    @classmethod
    def cmpBySigninTime(cls, p1, p2):
        return cmp(p1.signinTime, p2.signinTime)

    @classmethod
    def cmpByTableRanking(cls, p1, p2):
        if p1.tableRank <= 0 and p2.tableRank <= 0:
            return cls.cmpByChip(p1, p2)
        if (p1.tableRank == p2.tableRank):
            return cls.cmpByChip(p1, p2)
        if p1.tableRank <= 0:
            return 1
        if p2.tableRank <= 0:
            return -1
        if p1.tableRank > p2.tableRank:
            return 1
        return -1


class PlayerChipCalcImpl(object):
    def calc(self, chip):
        raise NotImplemented()


class PlayerChipCalcFixed(PlayerChipCalcImpl):
    def __init__(self, value):
        self._value = value

    def calc(self, chip):
        if self._value == 0:
            return chip
        return int(self._value)


class PlayerChipCalcPingFangGen(PlayerChipCalcImpl):
    def calc(self, chip):
        return int(chip ** 0.5)


class PlayerChipCalcBaiFenBi(PlayerChipCalcImpl):
    def __init__(self, rate):
        self._rate = rate

    def calc(self, chip):
        return int(chip * self._rate)


class PlayerChipCalcKaiFangFangDa(PlayerChipCalcImpl):
    def __init__(self, base, middle):
        self._base = base
        self._middle = max(middle, 1)
        self._rate = self._base / self._middle ** 0.5

    def calc(self, chip):
        if chip < 0:
            chip = 0
        return int((chip ** 0.5) * self._rate)


class PlayerChipCalc:
    __pingFangGenInstance = PlayerChipCalcPingFangGen()

    @classmethod
    def makeCalc(cls, stageConf, playerList):
        calcType = stageConf.chipUser
        if calcType == ChipCalcType.PING_FANG_GEN:
            return cls.__pingFangGenInstance
        elif calcType == ChipCalcType.BAI_FEN_BI:
            rate = float(stageConf.chipUserRate)
            return PlayerChipCalcBaiFenBi(rate)
        elif calcType == ChipCalcType.KAI_FANG_FANG_DA:
            base = float(stageConf.chipUserBase)
            middle = len(playerList) / 2
            return PlayerChipCalcKaiFangFangDa(base, playerList[middle].chip)
        else:
            return PlayerChipCalcFixed(calcType)


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


class PlayerQueuingChip(PlayerQueuingImpl):
    def sort(self, matchUserList):
        return matchUserList.sort(PlayerSort.cmpByChip)


class PlayerQueuingSigninTime(PlayerQueuingImpl):
    def sort(self, matchUserList):
        return matchUserList.sort(PlayerSort.cmpBySigninTime)


class PlayerQueuing(object):
    __defaultQueuing = PlayerQueuingRandom()
    __queuingMap = {SeatQueuingType.RANDOM: __defaultQueuing,
                    SeatQueuingType.SNAKE: PlayerQueuingSnake(),
                    SeatQueuingType.SEED: PlayerQueuingChip(),
                    SeatQueuingType.SIGNIN_TIME: PlayerQueuingSigninTime()}

    @classmethod
    def sort(cls, queuingType, players):
        if queuingType in cls.__queuingMap:
            return cls.__queuingMap[queuingType].sort(players)
        return cls.__defaultQueuing.sort(players)


class PlayerGrouping(object):
    @classmethod
    def groupingByGroupCount(cls, playerList, groupCount):
        pos = 0
        countPerGroup = len(playerList) / groupCount
        mod = len(playerList) % groupCount
        ret = []
        for i in xrange(groupCount):
            nextPos = pos + countPerGroup
            if i < mod:
                nextPos += 1
            ret.append(playerList[pos:nextPos])
            pos = nextPos
        return ret

    @classmethod
    def groupingByMaxUserCountPerGroup(cls, playerList, userCount):
        groupCount = (len(playerList) + userCount - 1) / userCount
        return cls.groupingByGroupCount(playerList, groupCount)

    @classmethod
    def groupingByFixedUserCountPerGroup(cls, playerList, userCount):
        pos = 0
        ret = []
        while (pos < len(playerList)):
            nextPos = pos + userCount
            ret.append(playerList[pos:nextPos])
            pos = nextPos
        return ret
