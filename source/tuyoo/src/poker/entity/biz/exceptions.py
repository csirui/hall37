# -*- coding=utf-8
'''
Created on 2015年6月1日

@author: zhaojiangang
'''


class TYBizException(Exception):
    def __init__(self, errorCode, message):
        super(TYBizException, self).__init__(errorCode, message)

    @property
    def errorCode(self):
        return self.args[0]

    @property
    def message(self):
        return self.args[1]

    def __str__(self):
        return '%s:%s' % (self.errorCode, self.message)

    def __unicode__(self):
        return u'%s:%s' % (self.errorCode, self.message)


class TYBizBadDataException(Exception):
    def __init__(self, message):
        super(TYBizBadDataException, self).__init__(-1, message)


class TYBizConfException(TYBizException):
    def __init__(self, conf, message):
        super(TYBizConfException, self).__init__(-1, message)
        self.conf = conf

    def __str__(self):
        return '%s:%s:%s' % (self.errorCode, self.message, self.conf)

    def __unicode__(self):
        return u'%s:%s:%s' % (self.errorCode, self.message, self.conf)
