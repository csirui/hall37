# -*- coding:utf-8 -*-
'''
Created on 2014年9月17日

@author: zjgzzz@126.com
'''


class MatchType(object):
    # 人满开赛
    USER_COUNT = 1
    # 定时赛
    TIMING = 2
    VALID_TYPES = (USER_COUNT, TIMING)

    @classmethod
    def isValid(cls, value):
        return value in cls.VALID_TYPES


class FeesType(object):
    TYPE_NO_RETURN = 0
    TYPE_RETURN = 1
    VALID_TYPES = (TYPE_NO_RETURN, TYPE_RETURN)

    @classmethod
    def isValid(cls, value):
        return value in cls.VALID_TYPES


class ScoreCalcType(object):
    PING_FANG_GEN = 1
    BAI_FEN_BI = 2
    KAI_FANG_FANG_DA = 3


class GroupingType(object):
    TYPE_NO_GROUP = 0
    TYPE_GROUP_COUNT = 1
    TYPE_USER_COUNT = 2
    VALID_TYPES = (TYPE_NO_GROUP, TYPE_GROUP_COUNT, TYPE_USER_COUNT)

    @classmethod
    def isValid(cls, value):
        return value in cls.VALID_TYPES


class MatchFinishReason(object):
    FINISH = 0
    USER_WIN = 1
    USER_LOSER = 2
    USER_NOT_ENOUGH = 3
    RESOURCE_NOT_ENOUGH = 4
    USER_LEAVE = 5
    OVERTIME = 7

    @classmethod
    def toString(cls, reason):
        if reason == cls.USER_NOT_ENOUGH:
            return u'由于参赛人数不足,比赛取消'
        elif reason == cls.RESOURCE_NOT_ENOUGH:
            return u'由于比赛过多,系统资源不足,比赛取消'
        elif reason == cls.USER_LEAVE:
            return u'您未能及时进入比赛房间,请报名参加下一场比赛'
        elif reason == cls.OVERTIME:
            return u'比赛超时'
        return u''


class StageType(object):
    # ASS
    ASS = 1
    # 定局
    DIEOUT = 2

    VALID_TYPES = (ASS, DIEOUT)

    @classmethod
    def isValid(cls, value):
        return value in cls.VALID_TYPES


MAX_CARD_COUNT = 100


class SeatQueuingType(object):
    # 随机
    RANDOM = 1
    # 蛇形
    SNAKE = 2
    # 种子
    SEED = 3
    # 报名时间
    SIGNIN_TIME = 4

    VALID_TYPES = (RANDOM, SNAKE, SEED, SIGNIN_TIME)

    @classmethod
    def isValid(cls, value):
        return value in cls.VALID_TYPES


class AnimationType(object):
    UNKNOWN = -1
    HAIXUAN = 0
    COUNT = 1
    FINALS = 2
    VS = 3
    ASSIGN_TABLE = 4

    VALID_TYPES = (UNKNOWN, HAIXUAN, COUNT, FINALS, VS, ASSIGN_TABLE)

    @classmethod
    def isValid(cls, value):
        return value in cls.VALID_TYPES


class WaitReason(object):
    UNKNOWN = 0
    WAIT = 1
    BYE = 2
    RISE = 3


class WaitCallReason(object):
    INIT_STAGE = 1
    WINLOSE = 2
    RISE = 3
