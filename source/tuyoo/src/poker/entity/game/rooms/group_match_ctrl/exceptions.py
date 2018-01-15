# -*- coding:utf-8 -*-
'''
Created on 2016年1月16日

@author: zhaojiangang
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


class SigninException(MatchException):
    def __init__(self, message):
        super(SigninException, self).__init__(4, message)


class SigninNotStartException(SigninException):
    def __init__(self, message='报名还未开始'):
        super(SigninNotStartException, self).__init__(message)


class SigninStoppedException(SigninException):
    def __init__(self, message=u'报名已截止'):
        super(SigninStoppedException, self).__init__(message)


class SigninFullException(SigninException):
    def __init__(self, message=u'比赛人数已满，请等待下一场比赛'):
        super(SigninFullException, self).__init__(message)


class SigninConditionNotEnoughException(SigninException):
    def __init__(self, message=u'报名条件不足'):
        super(SigninConditionNotEnoughException, self).__init__(message)


class SigninFeeNotEnoughException(SigninException):
    def __init__(self, fee, message=u'报名费不足'):
        super(SigninFeeNotEnoughException, self).__init__(message)
        self.fee = fee


class MatchStoppedException(SigninException):
    def __init__(self, message=u'比赛已经下线'):
        super(MatchStoppedException, self).__init__(message)


class AlreadySigninException(SigninException):
    def __init__(self, message='已经报名'):
        super(AlreadySigninException, self).__init__(message)


class AlreadyInMatchException(SigninException):
    def __init__(self, message=u'已经在比赛中'):
        super(AlreadyInMatchException, self).__init__(message)


class BadStateException(MatchException):
    def __init__(self, message='错误的状态'):
        super(BadStateException, self).__init__(-1, message)


class NotFoundGroupException(MatchException):
    def __init__(self, message='没有找到分组'):
        super(NotFoundGroupException, self).__init__(-1, message)


if __name__ == '__main__':
    pass
