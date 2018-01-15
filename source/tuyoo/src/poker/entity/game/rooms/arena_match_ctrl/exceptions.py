# -*- coding:utf-8 -*-
'''
Created on 2014年9月17日

@author: zjgzzz@126.com
'''
from poker.entity.biz.exceptions import TYBizException


class MatchException(TYBizException):
    def __init__(self, matchId, errorCode, message):
        super(MatchException, self).__init__(errorCode, message)
        self._matchId = matchId

    @property
    def matchId(self):
        return self._matchId


class MatchExpiredException(MatchException):
    def __init__(self, matchId, message=u'比赛已经结束'):
        super(MatchExpiredException, self).__init__(matchId, 4, message)


class MatchSigninException(MatchException):
    def __init__(self, matchId, errorCode, message):
        super(MatchSigninException, self).__init__(matchId, errorCode, message)


class AlreadySigninException(MatchSigninException):
    def __init__(self, matchId, message=u'已经报名了该比赛'):
        super(AlreadySigninException, self).__init__(matchId, 4, message)


class AlreadyInMatchException(MatchSigninException):
    def __init__(self, matchId, message=u'已经在比赛中'):
        super(AlreadyInMatchException, self).__init__(matchId, 4, message)


class SigninNotStartException(MatchSigninException):
    def __init__(self, matchId, message=u'报名还未开始'):
        super(SigninNotStartException, self).__init__(matchId, 4, message)


class SigninStoppedException(MatchSigninException):
    def __init__(self, matchId, message=u'报名已截止'):
        super(SigninStoppedException, self).__init__(matchId, 4, message)


class SigninFullException(MatchSigninException):
    def __init__(self, matchId, message=u'比赛人数已满，请等待下一场比赛'):
        super(SigninFullException, self).__init__(matchId, 4, message)


class SigninFeeNotEnoughException(MatchSigninException):
    def __init__(self, matchId, fee, message=u'报名费不足'):
        super(SigninFeeNotEnoughException, self).__init__(matchId, 4, message)
        self.fee = fee


class NotSigninException(MatchSigninException):
    def __init__(self, matchId, message=u'还没有报名'):
        super(NotSigninException, self).__init__(matchId, 4, message)


class EnterMatchLocationException(MatchException):
    def __init__(self, matchId, message=u'锁定用户失败'):
        super(EnterMatchLocationException, self).__init__(matchId, 4, message)


class ClientVersionException(MatchException):
    pass


class MatchSigninConditionException(MatchException):
    pass
