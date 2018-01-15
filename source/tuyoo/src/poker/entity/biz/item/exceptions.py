# -*- coding=utf-8
'''
Created on 2015年6月2日

@author: zhaojiangang
'''
from poker.entity.biz.exceptions import TYBizException


class TYItemException(TYBizException):
    def __init__(self, errorCode, message):
        super(TYItemException, self).__init__(errorCode, message)

    def __str__(self):
        return '%s:%s' % (self.errorCode, self.message)

    def __unicode__(self):
        return u'%s:%s' % (self.errorCode, self.message)


class TYItemConfException(TYItemException):
    def __init__(self, conf, message):
        super(TYItemConfException, self).__init__(-1, message)
        self.conf = conf

    def __str__(self):
        return '%s:%s conf=%s' % (self.errorCode, self.message, self.conf)

    def __unicode__(self):
        return u'%s:%s conf=%s' % (self.errorCode, self.message, self.conf)


class TYItemActionException(TYItemException):
    def __init__(self, action, message):
        super(TYItemActionException, self).__init__(-1, message)
        self.action = action

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.action.name)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.action.name)


class TYItemActionParamException(TYItemException):
    def __init__(self, action, message):
        super(TYItemActionParamException, self).__init__(-1, message)
        self.action = action

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.action.name)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.action.name)


class TYItemActionConditionException(TYItemException):
    def __init__(self, item, message):
        super(TYItemActionConditionException, self).__init__(-1, message)
        self.item = item


class TYItemActionConditionNotEnoughException(TYItemActionConditionException):
    def __init__(self, item, condition):
        super(TYItemActionConditionNotEnoughException, self).__init__(item, condition.failure)
        self.condition = condition

    def __str__(self):
        return '%s:%s %s:%s %s' % (
            self.errorCode, self.message, self.item.itemId, self.item.kindId, self.condition.params)

    def __unicode__(self):
        return u'%s:%s %s:%s %s' % (
            self.errorCode, self.message, self.item.itemId, self.item.kindId, self.condition.params)


class TYUnExecuteableException(TYItemException):
    def __init__(self, item, actionName):
        super(TYUnExecuteableException, self).__init__(-1, '不能执行该动作')
        self.item = item
        self.actionName = actionName

    def __str__(self):
        return '%s:%s %s:%s %s' % (self.errorCode, self.message, self.item.itemId, self.item.kindId, self.actionName)

    def __unicode__(self):
        return u'%s:%s %s:%s %s' % (self.errorCode, self.message, self.item.itemId, self.item.kindId, self.actionName)


class TYDuplicateItemIdException(TYItemException):
    def __init__(self, itemId):
        super(TYDuplicateItemIdException, self).__init__(-1, '重复的道具ID')
        self.itemId = itemId

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.itemId)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.itemId)


class TYAssetException(TYBizException):
    def __init__(self, errorCode, message):
        super(TYAssetException, self).__init__(errorCode, message)


class TYUnknownAssetKindException(TYAssetException):
    def __init__(self, kindId):
        super(TYUnknownAssetKindException, self).__init__(-1, '不能识别的资产类型%s' % (kindId))
        self.kindId = kindId

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.kindId)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.kindId)


class TYAssetNotEnoughException(TYAssetException):
    def __init__(self, assetKind, required, actually):
        super(TYAssetNotEnoughException, self).__init__(-1, '%s不足%s:%s' % (assetKind.displayName, required, actually))
        self.assetKind = assetKind
        self.required = required
        self.actually = actually

    def __str__(self):
        return '%s:%s %s:%s' % (self.errorCode, self.message, self.assetKind.kindId, self.assetKind.displayName)

    def __unicode__(self):
        return u'%s:%s %s:%s' % (self.errorCode, self.message, self.assetKind.kindId, self.assetKind.displayName)


class TYUnknownItemKindException(TYItemException):
    def __init__(self, kindId):
        super(TYUnknownItemKindException, self).__init__(-1, '不能识别的道具类型')
        self.kindId = kindId

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.kindId)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.kindId)


class TYItemNotFoundException(TYItemException):
    def __init__(self, itemId):
        super(TYItemNotFoundException, self).__init__(-1, '不能识别的道具ID')
        self.itemId = itemId

    def __str__(self):
        return '%s:%s %s' % (self.errorCode, self.message, self.itemId)

    def __unicode__(self):
        return u'%s:%s %s' % (self.errorCode, self.message, self.itemId)
