# -*- coding=utf-8
'''
Created on 2015年6月8日

@author: zhaojiangang
'''
from poker.entity.biz.exceptions import TYBizException


class TYStoreException(TYBizException):
    def __init__(self, errorCode, message):
        super(TYStoreException, self).__init__(errorCode, message)


class TYStoreConfException(TYStoreException):
    def __init__(self, conf, message):
        super(TYStoreConfException, self).__init__(-1, message)
        self.conf = conf

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.conf)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.conf)


class TYBuyProductUnknownException(TYStoreException):
    def __init__(self, productId):
        super(TYBuyProductUnknownException, self).__init__(-1, '没有该商品')
        self.productId = productId

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.productId)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.productId)


class TYProductNotSupportExchangeException(TYStoreException):
    def __init__(self, productId):
        super(TYProductNotSupportExchangeException, self).__init__(-1, '该商品不支持兑换')
        self.productId = productId

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.productId)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.productId)


class TYProductExchangeNotEnoughException(TYStoreException):
    def __init__(self, productId, message):
        super(TYProductExchangeNotEnoughException, self).__init__(-1, message)
        self.productId = productId

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.productId)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.productId)


class TYBuyProductOverCountException(TYStoreException):
    def __init__(self, productId, buyCountLimit, record, limit):
        super(TYBuyProductOverCountException, self).__init__(-1, buyCountLimit.getFailureByLimit(limit))
        self.productId = productId
        self.buyCountLimit = buyCountLimit
        self.record = record

    def __str__(self):
        return '%s:%s %s %s:%s' % (self.errorCode, self.message, self.productId,
                                   self.record.count, self.buyCountLimit.count)

    def __unicode__(self):
        return u'%s:%s %s %s:%s' % (self.errorCode, self.message, self.productId,
                                    self.record.count, self.buyCountLimit.count)


class TYBuyConditionNotEnoughException(TYStoreException):
    def __init__(self, productId, buyCondition):
        super(TYBuyConditionNotEnoughException, self).__init__(7, buyCondition.failure)
        self.productId = productId
        self.buyCondition = buyCondition


class TYOrderNotFoundException(TYStoreException):
    def __init__(self, orderId):
        super(TYOrderNotFoundException, self).__init__(-1, '没有找到该订单')
        self.orderId = orderId

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.orderId)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.orderId)


class TYDeliveryOrderDiffUserException(TYStoreException):
    def __init__(self, orderId, orderUserId, userId):
        super(TYDeliveryOrderDiffUserException, self).__init__(-1, '订单用户不匹配')
        self.orderId = orderId
        self.orderUserId = orderUserId
        self.userId = userId

    def __str__(self):
        return '%s:%s %s %s:%s' % (self.errorCode, self.message, self.orderId, self.orderUserId, self.userId)

    def __unicode__(self):
        return u'%s:%s %s %s:%s' % (self.errorCode, self.message, self.orderId, self.orderUserId, self.userId)


class TYDeliveryOrderDiffProductException(TYStoreException):
    def __init__(self, orderId, orderProductId, productId):
        super(TYDeliveryOrderDiffProductException, self).__init__(-1, '订单商品不匹配')
        self.orderId = orderId
        self.orderProductId = orderProductId
        self.productId = productId

    def __str__(self):
        return '%s:%s %s %s:%s' % (self.errorCode, self.message, self.orderId, self.orderProductId, self.productId)

    def __unicode__(self):
        return u'%s:%s %s %s:%s' % (self.errorCode, self.message, self.orderId, self.orderProductId, self.productId)


class TYDeliveryProductNotFoundException(TYStoreException):
    def __init__(self, orderId, productId):
        super(TYDeliveryProductNotFoundException, self).__init__(-1, '没有找到要发货的商品')
        self.orderId = orderId
        self.productId = productId

    def __str__(self):
        return '%s:%s %s %s' % (self.errorCode, self.message, self.orderId, self.productId)

    def __unicode__(self):
        return u'%s:%s %s %s' % (self.errorCode, self.message, self.orderId, self.productId)


class TYBadOrderStateException(TYStoreException):
    def __init__(self, orderId, orderState, expectState):
        super(TYBadOrderStateException, self).__init__(-1, '订单状态错误')
        self.orderId = orderId
        self.orderState = orderState
        self.expectState = expectState

    def __str__(self):
        return '%s:%s %s %s:%s' % (self.errorCode, self.message, self.orderId, self.orderState, self.expectState)

    def __unicode__(self):
        return u'%s:%s %s %s:%s' % (self.errorCode, self.message, self.orderId, self.orderState, self.expectState)
