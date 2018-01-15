# -*- coding:utf-8 -*-
'''
Created on 2016年7月6日

@author: zhaojiangang
'''
from poker.entity.biz.exceptions import TYBizException


class MatchException(TYBizException):
    def __init__(self, ec, message):
        super(MatchException, self).__init__(ec, message)


class MatchConfException(MatchException):
    def __init__(self, message):
        super(MatchConfException, self).__init__(-1, message)


class BadStateException(MatchException):
    def __init__(self, message='状态错误'):
        super(BadStateException, self).__init__(-1, message)


class MatchStoppedException(MatchException):
    def __init__(self, message='比赛已停止'):
        super(MatchStoppedException, self).__init__(-1, message)


class AleadyInMatchException(MatchException):
    def __init__(self, message='已经在比赛中'):
        super(AleadyInMatchException, self).__init__(-1, message)


class SigninException(MatchException):
    def __init__(self, message='报名失败'):
        super(SigninException, self).__init__(-1, message)


class SigninNotStartException(SigninException):
    def __init__(self, message='报名还未开始'):
        super(SigninNotStartException, self).__init__(message)


class SigninStoppedException(SigninException):
    def __init__(self, message='报名已截止'):
        super(SigninStoppedException, self).__init__(message)


class SigninFullException(SigninException):
    def __init__(self, message='报名人数已满'):
        super(SigninFullException, self).__init__(message)


class AlreadySigninException(SigninException):
    def __init__(self, message='已经报名'):
        super(AlreadySigninException, self).__init__(message)


class SigninConditionNotEnoughException(SigninException):
    def __init__(self, message='报名条件不足'):
        super(SigninConditionNotEnoughException, self).__init__(message)


class SigninFeeNotEnoughException(SigninException):
    def __init__(self, fee, message='报名费不足'):
        super(SigninFeeNotEnoughException, self).__init__(message)
        self.fee = fee
