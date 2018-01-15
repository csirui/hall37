# -*- coding=utf-8
'''
Created on 2015年4月15日

@author: zhaojiangang
'''
from poker.entity.biz.exceptions import TYBizException


class TYRankingException(TYBizException):
    def __init__(self, ec, message):
        super(TYRankingException, self).__init__(ec, message)


class TYRankingUnknownException(TYRankingException):
    def __init__(self, rankingId):
        super(TYRankingUnknownException, self).__init__(-1, 'Not found ranking: %s' % (rankingId))
        self.rankingId = rankingId


class TYRankingConfException(TYRankingException):
    def __init__(self, conf, message):
        super(TYRankingConfException, self).__init__(-1, message)
        self.conf = conf
