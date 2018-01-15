# -*- coding=utf-8
'''
Created on 2015年6月30日

@author: zhaojiangang
'''
from poker.entity.biz.exceptions import TYBizException


class TYTaskException(TYBizException):
    def __init__(self, errorCode, message):
        super(TYTaskException, self).__init__(errorCode, message)

    def __str__(self):
        return '%s:%s' % (self.errorCode, self.message)

    def __unicode__(self):
        return u'%s:%s' % (self.errorCode, self.message)


class TYTaskConfException(TYTaskException):
    def __init__(self, conf, message):
        super(TYTaskConfException, self).__init__(-1, message)
        self.conf = conf

    def __str__(self):
        return '%s:%s conf=%s' % (self.errorCode, self.message, self.conf)

    def __unicode__(self):
        return u'%s:%s conf=%s' % (self.errorCode, self.message, self.conf)


class TYTaskNotFinisheException(TYTaskException):
    def __init__(self, taskKindId):
        super(TYTaskNotFinisheException, self).__init__(-1, '任务还没有完成')
        self.taskKindId = taskKindId

    def __str__(self):
        return '%s:%s' % (self.errorCode, self.message)

    def __unicode__(self):
        return u'%s:%s' % (self.errorCode, self.message)


class TYTaskAlreayGetRewardException(TYTaskException):
    def __init__(self, taskKindId):
        super(TYTaskAlreayGetRewardException, self).__init__(-1, '已经领取了奖励')
        self.taskKindId = taskKindId

    def __str__(self):
        return '%s:%s' % (self.errorCode, self.message)

    def __unicode__(self):
        return u'%s:%s' % (self.errorCode, self.message)
