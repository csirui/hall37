# -*- coding:utf-8 -*-
'''
Created on 2014年9月17日

@author: zjgzzz@126.com
'''


class MatchException(Exception):
    def __init__(self, errorCode, message):
        super(MatchException, self).__init__(errorCode, message)

    @property
    def errorCode(self):
        return self.args[0]

    @property
    def message(self):
        return self.args[1]


class ConfigException(MatchException):
    def __init__(self, message):
        super(ConfigException, self).__init__(-1, message)


class MatchExpiredException(MatchException):
    def __init__(self, matchId, message=u'比赛已经下线'):
        super(MatchExpiredException, self).__init__(4, message)
        self.matchId = matchId


class AlreadySigninException(MatchException):
    def __init__(self, matchId, message=u'已经报名了该比赛'):
        super(AlreadySigninException, self).__init__(4, message)
        self.matchId = matchId


class SigninNotStartException(MatchException):
    def __init__(self, matchId, message=u'报名还未开始'):
        super(SigninNotStartException, self).__init__(4, message)
        self.matchId = matchId


class SigninStoppedException(MatchException):
    def __init__(self, matchId, message=u'报名已截止'):
        super(SigninStoppedException, self).__init__(4, message)
        self.matchId = matchId


class SigninFullException(MatchException):
    def __init__(self, matchId, message=u'比赛人数已满，请等待下一场比赛'):
        super(SigninFullException, self).__init__(4, message)
        self.matchId = matchId


class SigninFeeNotEnoughException(MatchException):
    def __init__(self, matchInst, fee, message=u'报名费不足'):
        super(SigninFeeNotEnoughException, self).__init__(4, message)
        self.matchId = matchInst.matchId
        self.matchInst = matchInst
        self.fee = fee


class MatchAlreadyStartedException(MatchException):
    def __init__(self, matchId, message=u'比赛已经开始'):
        super(MatchAlreadyStartedException, self).__init__(4, message)
        self.matchId = matchId


class AlreadyInMatchException(MatchException):
    def __init__(self, matchId, message=u'已经在比赛中'):
        super(AlreadyInMatchException, self).__init__(4, message)
        self.matchId = matchId


class EnterMatchLocationException(MatchException):
    def __init__(self, matchId, message=u'锁定用户失败'):
        super(EnterMatchLocationException, self).__init__(4, message)
        self.matchId = matchId


class ClientVersionException(MatchException):
    pass


class MatchSigninConditionException(MatchException):
    pass
