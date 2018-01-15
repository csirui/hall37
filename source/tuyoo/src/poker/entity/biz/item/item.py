# -*- coding=utf-8
'''
Created on 2015年6月3日

@author: zhaojiangang
'''
import struct
from sre_compile import isstring

from datetime import datetime

import freetime.util.log as ftlog
import poker.entity.biz.bireport as pkbireport
import poker.entity.events.tyeventbus as pkeventbus
import poker.util.timestamp as pktimestamp
from poker.entity.biz.confobj import TYConfableRegister, TYConfable
from poker.entity.biz.content import TYContentUtils
from poker.entity.biz.exceptions import TYBizBadDataException
from poker.entity.biz.item.exceptions import TYItemConfException, \
    TYUnExecuteableException, TYUnknownAssetKindException, \
    TYDuplicateItemIdException, TYItemActionConditionNotEnoughException, \
    TYAssetNotEnoughException, TYItemActionParamException
from poker.entity.events.tyevent import ModuleTipEvent, ItemCountChangeEvent
from poker.util import strutil

MAX_4_BYTEI = 2147483647
MAX_UINT = 4294967295


class TYComponentItem(object):
    '''
    可以合成的道具零件配置
    '''

    def __init__(self, itemKindId, count):
        # 道具零件种类ID
        self.itemKindId = itemKindId
        # 道具零件种类
        self.itemKind = None
        # 需要本种类零件的数量
        self.count = count
        # 其它一些参数
        self.params = None

    @classmethod
    def decodeFromDict(cls, d):
        itemKindId = d.get('itemKindId')
        if not isinstance(itemKindId, int):
            raise TYItemConfException(d, 'TYComponentItem.itemId must be int')
        count = d.get('count')
        if not isinstance(count, int) or count < 0:
            raise TYItemConfException(d, 'TYComponentItem.count must be int >= 0')
        params = d.get('params', {})
        if not isinstance(params, dict):
            raise TYItemConfException(d, 'TYComponentItem.params must be dict')
        return TYComponentItem(itemKindId, count)

    @classmethod
    def decodeList(cls, l):
        ret = []
        for d in l:
            ret.append(cls.decodeFromDict(d))
        return ret


class TYItemData(object):
    '''
    道具的存储对象，用于序列化数据成二进制
    '''
    BASE_STRUCT_FMT = 'H5IB'
    BASE_STRUCT_LEN = struct.calcsize(BASE_STRUCT_FMT)

    def __init__(self):
        self.itemKindId = 0
        self.createTime = 0
        self.remaining = 0
        self.expiresTime = 0
        self.fromUserId = 0
        self.giftHandCount = 0
        self.original = 0

    def toDict(self):
        d = {
            'itemKindId': self.itemKindId,
            'createTime': self.createTime,
            'remaining': self.remaining,
            'expiresTime': self.expiresTime,
            'fromUserId': self.fromUserId,
            'giftHandCount': self.giftHandCount,
            'original': self.original
        }
        fieldNames = self._getFieldNames()
        if fieldNames:
            for fieldName in fieldNames:
                d[fieldName] = getattr(self, fieldName)
        return d

    def fromDict(self, d):
        self.itemKindId = d['itemKindId']
        self.createTime = d['createTime']
        self.remaining = d['remaining']
        self.expiresTime = d['expiresTime']
        self.fromUserId = d['fromUserId']
        self.giftHandCount = d['giftHandCount']
        self.original = d['original']
        fieldNames = self._getFieldNames()
        if fieldNames:
            for fieldName in fieldNames:
                setattr(self, fieldName, d[fieldName])
        return self

    @classmethod
    def decodeKindId(cls, itemData):
        kindIdSize = struct.calcsize('H')
        return struct.unpack('H', itemData[0:kindIdSize])[0]

    @classmethod
    def encodeToBytes(cls, itemData):
        try:
            if itemData.expiresTime > MAX_4_BYTEI:
                itemData.expiresTime = MAX_4_BYTEI
            dataBytes = struct.pack(TYItemData.BASE_STRUCT_FMT, itemData.itemKindId, itemData.createTime,
                                    itemData.remaining, itemData.expiresTime, itemData.fromUserId,
                                    itemData.original, itemData.giftHandCount)
        except:
            ftlog.error('Item.encodeToBytes.pack Error !!',
                        TYItemData.BASE_STRUCT_FMT, [itemData.itemKindId, itemData.createTime,
                                                     itemData.remaining, itemData.expiresTime, itemData.fromUserId,
                                                     itemData.original, itemData.giftHandCount], itemData.__dict__)
            raise

        structFormat = itemData._getStructFormat()
        if structFormat:
            fieldValues = []
            fieldNames = itemData._getFieldNames()
            for fieldName in fieldNames:
                fieldValues.append(getattr(itemData, fieldName))
            try:
                dataBytes = dataBytes + struct.pack(structFormat, *fieldValues)
            except:
                ftlog.error('Item.encodeToBytes.pack Error !!', structFormat, fieldValues, itemData.__dict__)
                raise
        return dataBytes

    @classmethod
    def adjustUint(cls, value):
        return 0 if (value < 0 or value >= MAX_UINT) else value

    @classmethod
    def decodeFromBytes(cls, itemData, dataBytes):
        dataBytes = strutil.unicode2Ascii(dataBytes)
        itemData.itemKindId, itemData.createTime, itemData.remaining, itemData.expiresTime, \
        itemData.fromUserId, itemData.original, itemData.giftHandCount = \
            struct.unpack(TYItemData.BASE_STRUCT_FMT, dataBytes[0:TYItemData.BASE_STRUCT_LEN])

        itemData.createTime = cls.adjustUint(itemData.createTime)
        itemData.remaining = cls.adjustUint(itemData.remaining)
        itemData.expiresTime = cls.adjustUint(itemData.expiresTime)
        itemData.fromUserId = cls.adjustUint(itemData.fromUserId)
        itemData.original = cls.adjustUint(itemData.original)

        structFormat = itemData._getStructFormat()
        if structFormat:
            formatLen = struct.calcsize(structFormat)
            fieldValues = struct.unpack(structFormat,
                                        dataBytes[TYItemData.BASE_STRUCT_LEN:TYItemData.BASE_STRUCT_LEN + formatLen])
            fieldNames = itemData._getFieldNames()
            if len(fieldValues) != len(fieldNames):
                raise TYBizBadDataException('Failed to decode item data')
            for i, fieldName in enumerate(fieldNames):
                setattr(itemData, fieldName, fieldValues[i])
        return itemData

    def _getStructFormat(self):
        return None

    def _getFieldNames(self):
        return None


class TYItemActionCondition(TYConfable):
    '''
    道具动作条件类，用于定义一个条件，在执行某个动作时检查
    '''

    def __init__(self):
        super(TYItemActionCondition, self).__init__()
        self.params = None

    def getParam(self, paramName, defVal=None):
        return self.params.get(paramName, defVal)

    @property
    def failure(self):
        return self.getParam('failure', '')

    def check(self, gameId, userAssets, item, timestamp, params):
        if not self._conform(gameId, userAssets, item, timestamp, params):
            self._onFailure(gameId, userAssets, item, timestamp, params)

    def _conform(self, gameId, userAssets, item, timestamp, params):
        raise NotImplementedError

    def _onFailure(self, gameId, userAssets, item, timestamp, params):
        raise TYItemActionConditionNotEnoughException(item, self)

    def decodeFromDict(self, d):
        params = d.get('params', {})
        if not isinstance(params, dict):
            raise TYItemConfException(d, 'TYItemActionCondition.params must be dict')
        self.params = params


class TYItemActionConditionRegister(TYConfableRegister):
    '''
    道具动作条件类注册，主要是用于根据不同的typeId生成响应的条件类
    '''
    _typeid_clz_map = {}


class TYItemActionResult(object):
    '''
    执行某个动作的返回值
    '''

    def __init__(self, action, item, message='', todotask=None):
        self.action = action
        self.item = item
        self.message = message
        self.todotask = todotask


class TYItemAction(TYConfable):
    '''
    动作类，用于对某个道具执行一个动作
    '''

    def __init__(self):
        self.conf = None
        # 动作的名称
        self._name = None
        # 用于显示的名称
        self._displayName = None
        self._message = None
        self._mail = None
        self._conditionList = None
        self._itemKind = None
        self._inputParams = None

    @property
    def name(self):
        return self._name

    @property
    def displayName(self):
        return self._displayName

    @property
    def message(self):
        return self._message

    @property
    def mail(self):
        return self._mail

    @property
    def itemKind(self):
        return self._itemKind

    def getInputParams(self, gameId, userBag, item, timestamp):
        return self._inputParams

    @property
    def conditionList(self):
        return self._condition

    def checkParams(self, gameId, userAssets, item, timestamp, params):
        paramNameTypeList = self.getParamNameTypeList()
        if paramNameTypeList:
            for paramName, paramTypes in paramNameTypeList:
                value = params.get(paramName)
                if not isinstance(value, paramTypes):
                    raise TYItemActionParamException(self, 'Param %s must be %s' % (paramName, paramTypes))

    def getParamNameTypeList(self):
        return None

    def canDo(self, userBag, item, timestamp):
        '''
        判断是否可以对item执行本动作
        '''
        return False

    def initWhenLoaded(self, itemKind, itemKindMap, assetKindMap):
        '''
        当配置解析工作完成后调用，用于初始化配置中一些itemKind相关的数据
        '''
        self._itemKind = itemKind
        self._initWhenLoaded(itemKind, itemKindMap, assetKindMap)

    def doAction(self, gameId, userAssets, item, timestamp, params):
        '''
        对item执行本动作
        '''
        self.checkParams(gameId, userAssets, item, timestamp, params)
        self._checkConditions(gameId, userAssets, item, timestamp, params)
        return self._doActionImpl(gameId, userAssets, item, timestamp, params)

    def decodeFromDict(self, d):
        '''
        从一个dict配置中解析该动作类
        '''
        self.conf = d
        self._name = d.get('name')
        self._displayName = d.get('displayName')
        self._message = d.get('message')
        self._mail = d.get('mail')
        self._inputParams = d.get('params')
        if self._inputParams is not None and not isinstance(self._inputParams, dict):
            raise TYItemConfException(d, 'TYItemAction.inputParams must be dict')
        conditions = d.get('conditions')
        if conditions:
            self._conditionList = TYItemActionConditionRegister.decodeList(conditions)
        # 实现类解析自己特有的数据
        self._decodeFromDictImpl(d)
        return self

    def _checkConditions(self, gameId, userAssets, item, timestamp, params):
        if self._conditionList:
            for condition in self._conditionList:
                condition.check(gameId, userAssets, item, timestamp, params)

    def _decodeFromDictImpl(self, d):
        '''
        用于子类解析自己特有的数据
        '''
        pass

    def _initWhenLoaded(self, itemKind, itemKindMap, assetKindMap):
        # 当配置解析工作完成后调用，用于初始化配置中一些itemKind相关的数据
        pass

    def _doActionImpl(self, gameId, userAssets, item, timestamp, params):
        # 执行具体的动作，此时各种条件已经检查完毕
        return None


class TYItemActionRegister(TYConfableRegister):
    '''
    用户道具动作类注册
    '''
    _typeid_clz_map = {}


class TYItemUnits(TYConfable):
    '''
    道具单位类，用于道具的增加和消耗
    '''

    def __init__(self):
        super(TYItemUnits, self).__init__()
        # 显示名称
        self.displayName = None

    def isTiming(self):
        raise NotImplementedError

    def add(self, item, count, timestamp):
        '''
        给item增加count个单位
        '''
        raise NotImplementedError

    def balance(self, item, timestamp):
        '''
        剩余多少个单位
        '''
        raise NotImplementedError

    def consume(self, item, count, timestamp):
        '''
        给item消耗count个单位
        @return: consumeCount
        '''
        raise NotImplementedError

    def forceConsume(self, item, count, timestamp):
        '''
        强制消耗count个单位，如果不足则消耗所有
        @return: consumeCount
        '''
        raise NotImplementedError

    def decodeFromDict(self, d):
        if not isinstance(d, dict):
            raise TYItemConfException(d, 'TYItemUnits.units must be dict')
        displayName = d.get('displayName')
        if not isstring(displayName) or not displayName:
            raise TYItemConfException(d, 'TYItemUnits.units.displayName must be valid string')
        self.displayName = displayName
        self._decodeFromDictImpl(d)
        return self

    def _decodeFromDictImpl(self, d):
        # 子类解析自己特有的数据
        return self


class TYItemUnitsRegister(TYConfableRegister):
    '''
    道具单位注册类
    '''
    _typeid_clz_map = {}


class TYItemKind(TYConfable):
    '''
    定义一种具体的道具，比如月光钥匙，记牌器
    '''

    def __init__(self):
        super(TYItemKind, self).__init__()
        self.conf = None
        # 道具种类ID
        self.kindId = None
        # 显示名称
        self.displayName = None
        # 是否在背包显示
        self.visibleInBag = None
        # 道具说明
        self.desc = None
        # 道具图片
        self.pic = None
        # 单位
        self.units = None
        # remaining<=0时是否从背包删除
        self.removeFromBagWhenRemainingZero = None
        # 到期时是否从背包中删除
        self.removeFromBagWhenExpires = None
        # 此道具是否是单例模式
        self.singleMode = None
        # 是哪个道具的组成部分
        self.componentOf = None
        # 由哪些部件组成该道具
        self.componentList = None
        # actionMap
        self.actionMap = {}
        self.actionList = []
        # 到期时间
        self.expires = None

        # 3.9新增字段
        # 游戏ID
        self.gameId = None
        # 道具种类
        self.catagoryId = None
        # 道具描述
        self.catagoryDesc = None
        # 排序id
        self.sortId = None
        # 到期日期,年月日,无需时间转换
        self.expiresTime = None
        # 道具描述
        self.maskinbag = None

    def isExpires(self, timestamp):
        if self.expires is not None:
            return timestamp >= self.expires
        return False

    def newItem(self, itemId, timestamp):
        '''
        产生一个新的本种类的道具，id=itemId
        @param itemId: 道具ID
        @param timestamp: 当前时间戳
        @return: Item的子类
        '''
        raise NotImplementedError

    def newItemForDecode(self, itemId):
        '''
        产生一个本种类的道具，用于反序列化
        '''
        raise NotImplementedError

    def newItemData(self):
        '''
        产生一个ItemData
        '''
        raise NotImplementedError

    def getSupportedActions(self):
        '''
        获取支持的动作列表
        @return: list<TYItemAction>
        '''
        return self.actionList

    def findActionByName(self, actionName):
        '''
        根据action名称查找action
        '''
        for _, action in self.actionMap.iteritems():
            if action.name == actionName:
                return action
        return None

    def findActionsByNames(self, actionNames):
        '''
        查找name在actionNames列表中的action
        '''
        actions = []
        for _, action in self.actionMap.iteritems():
            if action.name in actionNames:
                actions.append(action)
        return actions

    def initWhenLoaded(self, itemKindMap, assetKindMap):
        '''
        '''
        self._initComponentList(itemKindMap)
        for action in self.actionMap.values():
            action.initWhenLoaded(self, itemKindMap, assetKindMap)
        self._initWhenLoaded(itemKindMap, assetKindMap)

    def processWhenUserLogin(self, item, userAssets,
                             gameId, isDayFirst, timestamp):
        pass

    def processWhenAdded(self, item, userAssets,
                         gameId, timestamp):
        pass

    def _initWhenLoaded(self, itemKindMap, assetKindMap):
        pass

    def _initComponentList(self, itemKindMap):
        if not self.componentList:
            return

        # 用于检查是否重复配置了component
        componentSet = set()
        for componentItem in self.componentList:
            # 零件不能是自己
            if componentItem.itemKindId == self.kindId:
                raise TYItemConfException(self.conf,
                                          'TYItemSystemImpl._initComponentList components can not itself %s' % (
                                              self.kindId))

            # 检查是否重复配置了component
            if componentItem.itemKindId in componentSet:
                raise TYItemConfException(self.conf,
                                          'TYItemSystemImpl._initComponentList %s components duplicate %s' % (
                                              self.kindId, componentItem.itemKindId))

            # 查找componentItemKind
            componentItemKind = itemKindMap.get(componentItem.itemKindId)
            if not componentItemKind:
                raise TYItemConfException(self.conf,
                                          'TYItemSystemImpl._initComponentList %s components not found %s' % (
                                              self.kindId, componentItem.itemKindId))

            if componentItemKind.componentOf:
                raise TYItemConfException(self.conf,
                                          'TYItemSystemImpl._initComponentList %s component %s already componentOf %s' \
                                          % (
                                              self.kindId, componentItemKind.kindId,
                                              componentItemKind.componentOf.kindId))

            componentSet.add(componentItem.itemKindId)
            componentItem.itemKind = componentItemKind

            componentItemKind.componentOf = self

    def decodeFromDict(self, d):
        '''
        从d中解析数据
        '''
        self.conf = d
        self.kindId = d.get('kindId')
        if not isinstance(self.kindId, int):
            raise TYItemConfException(d, 'TYItemKind.kindId must be int %s' % (self.kindId))
        # 3.9新增字段
        self.gameId = d.get('gameId')
        if not isinstance(self.gameId, int):
            raise TYItemConfException(d, 'TYItemKind.gameId must be int %s' % (self.gameId))
        self.catagoryId = d.get('catagoryId')
        if not isinstance(self.catagoryId, int):
            raise TYItemConfException(d, 'TYItemKind.catagoryId must be int %s' % (self.catagoryId))
        self.sortId = d.get('sortId')
        if not isinstance(self.sortId, int):
            raise TYItemConfException(d, 'TYItemKind.sortId must be int %s' % (self.sortId))
        self.catagoryDesc = d.get('catagoryDesc')
        if not isstring(self.catagoryDesc) or not self.catagoryDesc:
            raise TYItemConfException(d, 'TYItemKind.catagoryDesc must be valid string')
        self.maskinbag = d.get('maskinbag')
        if self.maskinbag:
            if not isinstance(self.maskinbag, int):
                raise TYItemConfException(d, 'TYItemKind.maskinbag must be int %s' % (self.maskinbag))
        else:
            self.maskinbag = 0

        self.displayName = d.get('displayName')
        if not isstring(self.displayName) or not self.displayName:
            raise TYItemConfException(d, 'TYItemKind.displayName must be valid string')
        self.visibleInBag = d.get('visibleInBag')
        if not isinstance(self.visibleInBag, int) or self.visibleInBag not in (0, 1):
            raise TYItemConfException(d, 'TYItemKind.visibleInBag must be int in (0, 1)')
        self.desc = d.get('desc', '')
        if not isstring(self.desc):
            raise TYItemConfException(d, 'TYItemKind.desc must be string')
        self.pic = d.get('pic')
        if not isstring(self.pic):
            raise TYItemConfException(d, 'TYItemKind.pic must be string')
        self.units = TYItemUnitsRegister.decodeFromDict(d.get('units'))
        self.removeFromBagWhenRemainingZero = d.get('removeFromBagWhenRemainingZero')
        if (not isinstance(self.removeFromBagWhenRemainingZero, int)
            or self.removeFromBagWhenRemainingZero not in (0, 1)):
            raise TYItemConfException(d, 'TYItemKind.removeFromBagWhenRemainingZero must be int in (0, 1)')

        if self.removeFromBagWhenRemainingZero and self.units.isTiming():
            raise TYItemConfException(d, 'TYItemKind.removeFromBagWhenRemainingZero must be 0 when units is timing')

        self.removeFromBagWhenExpires = d.get('removeFromBagWhenExpires')
        if (not isinstance(self.removeFromBagWhenExpires, int)
            or self.removeFromBagWhenExpires not in (0, 1)):
            raise TYItemConfException(d, 'TYItemKind.removeFromBagWhenExpires must be int in (0, 1)')
        self.singleMode = d.get('singleMode', 1)
        if (not isinstance(self.singleMode, int)
            or not self.singleMode in (0, 1)):
            raise TYItemConfException(d, 'TYItemKind.singleMode must be int in (0, 1)')

        componentList = d.get('components')
        if componentList:
            self.componentList = TYComponentItem.decodeList(componentList)

        actionMap = {}
        actionList = []
        actionsConf = d.get('actions')
        if actionsConf:
            for actionConf in actionsConf:
                action = TYItemActionRegister.decodeFromDict(actionConf)
                if action.name in actionMap:
                    raise TYItemConfException(action, 'TYItemKind.actions.action %s already exists' % (action.name))
                actionMap[action.name] = action
                actionList.append(action)
        self.actionMap = actionMap
        self.actionList = actionList

        # 解析expires
        expires = d.get('expires')
        if expires:
            # 3.9 客户端用来做显示
            self.expiresTime = expires
            try:
                self.expires = pktimestamp.datetime2Timestamp(datetime.strptime(expires, '%Y-%m-%d %H:%M:%S'))
            except:
                raise TYItemConfException(d, 'TYItemKind.expires must be string YYYY-MM-DD HH:MM:SS')

        self._decodeFromDictImpl(d)
        return self

    def _decodeFromDictImpl(self, d):
        return self


class TYItem(object):
    '''
    道具基类
    '''

    def __init__(self, itemKind, itemId):
        super(TYItem, self).__init__()
        # 道具定义
        self._itemKind = itemKind
        # 道具ID
        self._itemId = itemId
        # 道具创建时间
        self.createTime = 0
        # 剩余次数或者数量
        self.remaining = 0
        # 过期时间, <0表示永久有效
        self.expiresTime = 0
        # 谁赠送的
        self.fromUserId = 0
        # 是否是原装的，没有执行过任何动作
        self.original = 1
        # 赠送过手次数
        self.giftHandCount = 0

    @property
    def itemKind(self):
        return self._itemKind

    @property
    def kindId(self):
        return self._itemKind.kindId

    @property
    def itemId(self):
        return self._itemId

    def isDied(self, timestamp):
        if self.itemKind.units.isTiming():
            return self.isExpires(timestamp)
        else:
            return self.remaining <= 0
            #         if self.expiresTime < 0:
            #             return self.balance(timestamp) <= 0
            #         return self.isExpires(timestamp) and self.balance(timestamp) <= 0

    def isExpires(self, timestamp):
        '''
        检查道具是否到期
        @param timestamp: 当前时间戳
        @return: 到期返回True, 否则返回False
        '''
        if self.expiresTime <= 0:
            return False
        return timestamp >= self.expiresTime

    def visibleInBag(self, timestamp):
        return True

    def onDied(self, timestamp):
        pass

    def needRemoveFromBag(self, timestamp):
        '''
        检查是否需要从背包删除该道具
        @param timestamp: 当前时间戳
        @return: 需要返回True, 否则返回False
        '''
        if self.itemKind.isExpires(timestamp):
            return True
        if self.itemKind.units.isTiming():
            return self.isExpires(timestamp) and self.itemKind.removeFromBagWhenExpires
        return self.remaining <= 0 and self.itemKind.removeFromBagWhenRemainingZero

    def addUnits(self, count, timestamp):
        '''
        添加count个单位
        '''
        self.itemKind.units.add(self, count, timestamp)

    def balance(self, timestamp):
        '''
        剩余多少个单位
        '''
        return self.itemKind.units.balance(self, timestamp)

    def consume(self, count, timestamp):
        '''
        消耗count个单位
        @return: consumeCount
        '''
        assert (self.itemKind.singleMode)
        consumeCount = self.itemKind.units.consume(self, count, timestamp)
        if consumeCount > 0 and self.isDied(timestamp):
            self.onDied(timestamp)
        return consumeCount

    def forceConsume(self, item, count, timestamp):
        '''
        强制消耗count个单位，如果不足则消耗所有
        @return: consumeCount
        '''
        assert (self.itemKind.singleMode)
        consumeCount = self.itemKind.units.forceConsume(self, count, timestamp)
        if consumeCount > 0 and self.isDied(timestamp):
            self.onDied(timestamp)
        return consumeCount

    def decodeFromItemData(self, itemData):
        assert (isinstance(itemData, TYItemData))
        self.createTime = itemData.createTime
        self.remaining = itemData.remaining
        self.expiresTime = itemData.expiresTime
        self.fromUserId = itemData.fromUserId
        self.original = itemData.original
        self.giftHandCount = itemData.giftHandCount
        self._decodeFromItemData(itemData)
        return self

    def encodeToItemData(self):
        itemData = self.itemKind.newItemData()
        itemData.itemKindId = self._itemKind.kindId
        itemData.createTime = self.createTime
        itemData.remaining = self.remaining
        itemData.expiresTime = self.expiresTime
        itemData.fromUserId = self.fromUserId
        itemData.original = self.original
        itemData.giftHandCount = self.giftHandCount
        self._encodeToItemData(itemData)
        return itemData

    def _decodeFromItemData(self, itemData):
        pass

    def _encodeToItemData(self, itemData):
        pass


class TYItemKindRegister(TYConfableRegister):
    _typeid_clz_map = {}


class TYUserBag(object):
    @property
    def userId(self):
        raise NotImplementedError

    @property
    def userAssets(self):
        raise NotImplementedError

    def findItem(self, itemId):
        '''
        在背包中根据itemId查找道具
        @param itemId: 要查找的道具ID
        @return: item or None
        '''
        raise NotImplementedError

    def getAllItem(self):
        '''
        获取所有item
        @return: list<Item>
        '''
        raise NotImplementedError

    def getItemByKind(self, itemKind):
        '''
        获取某个类型的一个道具
        '''
        raise NotImplementedError

    def getItemByKindId(self, itemKindId):
        '''
        获取某个类型的一个道具
        '''
        raise NotImplementedError

    def getAllKindItem(self, itemKind):
        '''
        获取所有item
        @return: list<Item>
        '''
        raise NotImplementedError

    def getAllKindItemByKindId(self, kindId):
        '''
        获取所有item
        @return: list<Item>
        '''
        raise NotImplementedError

    def getAllTypeItem(self, itemType):
        '''
        获取所有item类类型为itemType的道具
        @return: list<Item>
        '''
        raise NotImplementedError

    def addItem(self, gameId, item, timestamp, eventId, intEventParam):
        '''
        添加一个道具到背包
        '''
        raise NotImplementedError

    def addItemUnits(self, gameId, item, count, timestamp, eventId, intEventParam):
        '''
        给某个道具添加count个单位
        '''
        raise NotImplementedError

    def addItemUnitsByKind(self, gameId, itemKind, count, timestamp, fromUserId, eventId, intEventParam):
        '''
        添加count个单位的道具
        '''
        raise NotImplementedError

    def removeItem(self, gameId, item, timestamp, eventId, intEventParam):
        '''
        在背包中根据itemId删除道具，返回删除的道具
        @param itemId: 要删除的道具ID
        @return: item or None
        '''
        raise NotImplementedError

    def calcTotalUnitsCount(self, itemKind, timestamp=None):
        '''
        计算所有itemKind种类的道具的数量
        @param itemKind: 那种类型
        @param timestamp: 当前时间
        @return: 剩余多少个单位
        '''
        raise NotImplementedError

    def consumeItemUnits(self, gameId, item, unitsCount, timestamp, eventId, intEventParam):
        '''
        消耗item unitsCount个单位
        @param item: 那个道具
        @param unitsCount: 多少个单位
        @return: consumeCount
        '''
        raise NotImplementedError

    def consumeUnitsCountByKind(self, gameId, itemKind, unitsCount, timestamp, eventId, intEventParam):
        '''
        消耗道具种类为itemKind的unitsCount个单位的道具
        @param itemKind: 那种类型
        @param unitsCount: 多少个单位
        @return: consumeCount
        '''
        raise NotImplementedError

    def forceConsumeUnitsCountByKind(self, gameId, itemKind, unitsCount, timestamp, eventId, intEventParam):
        '''
        强制消耗道具种类为itemKind的unitsCount个单位的道具，如果不够则消耗所有的
        @param itemKind: 那种类型
        @param unitsCount: 多少个单位
        @return: consumeCount
        '''
        raise NotImplementedError

    def updateItem(self, gameId, item, timestamp=None):
        '''
        保存道具
        @param item: 要保存的道具
        '''
        raise NotImplementedError

    def processWhenUserLogin(self, gameId, isDayFirst, timestamp=None):
        '''
        当用户登录时调用该方法，处理对用户登录感兴趣的道具
        @param gameId: 哪个游戏驱动
        @param isDayFirst: 是否是
        '''
        raise NotImplementedError

    def getExecutableActions(self, item, timestamp):
        '''
        获取item支持的动作列表
        @return: list<TYItemAction>
        '''
        raise NotImplementedError

    def doAction(self, gameId, item, actionName, timestamp=None, params={}):
        '''
        执行动作
        @param gameId: 哪个游戏驱动的
        @param item: 哪个道具执行
        @param actionName: 执行哪个动作
        @param params: 参数
        '''
        raise NotImplementedError


class TYItemDao(object):
    def __init__(self, itemSystem, itemDataDao):
        super(TYItemDao, self).__init__()
        self._itemSystem = itemSystem
        self._itemDataDao = itemDataDao

    def loadAll(self, userId):
        '''
        加载用户所有的道具
        '''
        itemList = []
        itemDataList = self._itemDataDao.loadAll(userId)
        for itemId, itemDataBytes in itemDataList:
            item = self._decodeItem(userId, itemId, itemDataBytes)
            if item:
                itemList.append(item)
            else:
                ftlog.hinfo('TYItemDao.loadAll userId=', userId,
                            'itemId=', itemId,
                            'itemData=', itemDataBytes,
                            'err=', 'BadItemData')
                # self._itemDataDao.removeItem(userId, itemId)
        return itemList

    def saveItem(self, userId, item):
        '''
        保存用户道具
        '''
        itemDataBytes = TYItemData.encodeToBytes(item.encodeToItemData())
        self._itemDataDao.saveItem(userId, item.itemId, itemDataBytes)

    def removeItem(self, userId, item):
        '''
        删除用户道具
        '''
        self._itemDataDao.removeItem(userId, item.itemId)

    def nextItemId(self):
        '''
        获取一个全局唯一的道具Id
        '''
        return self._itemDataDao.nextItemId()

    def _decodeItem(self, userId, itemId, itemDataBytes):
        kindId = None
        itemKind = None
        itemData = None
        try:
            kindId = TYItemData.decodeKindId(itemDataBytes)
            itemKind = self._itemSystem.findItemKind(kindId)
            if itemKind:
                itemData = itemKind.newItemData()
                TYItemData.decodeFromBytes(itemData, itemDataBytes)
                item = itemKind.newItemForDecode(itemId)
                item.decodeFromItemData(itemData)
                return item
        except:
            ftlog.error('TYItemDao._decodeItem userId=', userId,
                        'itemId=', itemId, 'kindId=', kindId, 'itemKind=', itemKind,
                        'itemData=', itemData, 'data=', itemDataBytes)
        return None


class TYItemSystem(object):
    def getInitItems(self):
        '''
        获取用户初始化配置
        '''
        raise NotImplementedError

    def getInitItemsNew(self):
        '''
        获取用户初始化配置
        '''
        raise NotImplementedError

    def getInitItemsByTemplateName(self, templateName):
        '''
        获取用户初始化模版
        '''
        raise NotImplementedError

    def findAssetKind(self, kindId):
        '''
        根据kindId查找asset定义
        @return: AssetKind or None
        '''
        raise NotImplementedError

    def getAllAssetKind(self):
        '''
        获取所有asset定义
        @return: list<AssetKind>
        '''
        raise NotImplementedError

    def findItemKind(self, kindId):
        '''
        根据kindId查找道具定义
        @param kindId: 道具类型ID 
        @return: ItemKind 
        '''
        raise NotImplementedError

    def getAllItemKind(self):
        '''
        获取所有道具定义
        @return: list<ItemKind>
        '''
        raise NotImplementedError

    def getAllItemKindByType(self, itemKindClassType):
        '''
        获取所有itemKindClassType类型的道具定义
        @return: list<ItemKind>
        '''
        raise NotImplementedError

    def loadUserAssets(self, userId):
        '''
        加载用户资产
        @return: UserAssets
        '''
        raise NotImplementedError

    def newItemFromItemData(self, itemData):
        '''
        '''
        raise NotImplementedError


class TYUserAssets(object):
    @property
    def userId(self):
        '''
        获取用户ID
        @return: userId 
        '''
        raise NotImplementedError

    def getUserBag(self):
        '''
        获取用户背包
        @return: TYUserBag
        '''
        raise NotImplementedError

    def balance(self, gameId, assetKindId, timestamp):
        '''
        获取assetKindId的余额
        @return: (TYAssetKind, balance)
        '''
        raise NotImplementedError

    def addAsset(self, gameId, assetKindId, count, timestamp, eventId, intEventParam):
        '''
        增加Asset
        @param gameId: 哪个游戏驱动的
        @param assetKindId: asset种类ID
        @param count: 个数
        @param timestamp: 时间戳
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: (TYAssetKind, addCount, final)
        '''
        raise NotImplementedError

    def consumeAsset(self, gameId, assetKindId, count, timestamp, eventId, intEventParam):
        '''
        消耗Asset
        @param gameId: 哪个游戏驱动的
        @param assetKindId: asset种类ID
        @param count: 个数
        @param timestamp: 时间戳
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: (TYAssetKind, consumeCount, final)
        '''
        raise NotImplementedError

    def forceConsumeAsset(self, gameId, assetKindId, count, timestamp, eventId, intEventParam):
        '''
        消耗Asset
        @param gameId: 哪个游戏驱动的
        @param assetKindId: asset种类
        @param count: 个数
        @param timestamp: 时间戳
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: (TYAssetKind, consumeCount, final)
        '''
        raise NotImplementedError

    def consumeContentItemList(self, gameId, contentItemList, ignoreUnknown, eventId, intEventParam):
        '''
        消耗contentItemList
        @param gameId: 哪个游戏驱动的
        @param contentItemList: 要消耗的内容
        @param ignoreUnknown: 是否忽略不认识的item, 如果不忽略则会抛出异常
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: list<(TYAssetKind, consumeCount, final)>
        '''
        raise NotImplementedError

    def sendContentItemList(self, gameId, contentItemList, count, ignoreUnknown, timestamp, eventId, intEventParam):
        '''
        给用户发货
        @param gameId: 哪个游戏驱动的
        @param contentItemList: 要发货的内容
        @param count: 数量
        @param ignoreUnknown: 是否忽略不认识的item, 如果不忽略则会抛出异常
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: list<(TYAssetKind, consumeCount, final)>
        '''
        raise NotImplementedError

    def sendContent(self, gameId, content, count, ignoreUnknown, timestamp, eventId, intEventParam):
        '''
        给用户发货
        @param gameId: 哪个游戏驱动的
        @param content: 要发货的内容
        @param count: 发多少个
        @param ignoreUnknown: 是否忽略不认识的item, 如果不忽略则会抛出异常
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: list<(TYAssetKind, consumeCount, final)>
        '''
        raise NotImplementedError


class TYRecycleResult(object):
    def __init__(self, item, gotItems):
        self.item = item
        self.gotItems = gotItems


class TYUserBagImpl(TYUserBag):
    def __init__(self, userId, dao, assets):
        super(TYUserBagImpl, self).__init__()
        self._userId = userId
        self._dao = dao
        # map<itemId, item>
        self._itemIdMap = {}
        # map<kindId, map<itemId, item>>
        self._kindIdMap = {}
        self._assets = assets
        self._loaded = False
        self._isSendToUser = True

    def load(self):
        if not self._loaded:
            self._loaded = True
            itemList = self._dao.loadAll(self.userId)
            for item in itemList:
                found = self.findItem(item.itemId)
                if not found:
                    self._addItemToMap(item)
                else:
                    ftlog.error('TYUserBagImpl.load userId=', self.userId,
                                'duplicate itemId=', item.itemId)
        return self

    @property
    def userId(self):
        return self._userId

    @property
    def userAssets(self):
        return self._assets

    def _onCountChanged(self):
        event = ItemCountChangeEvent(self._userId)
        pkeventbus.globalEventBus.publishEvent(event)

    def findItem(self, itemId):
        '''
        在背包中根据itemId查找道具
        @param itemId: 要查找的道具ID
        @return: item or None
        '''
        return self._itemIdMap.get(itemId)

    def getAllItem(self):
        '''
        获取所有item
        @return: list<Item>
        '''
        return self._itemIdMap.values()

    def getItemByKind(self, itemKind):
        '''
        获取某个类型的一个道具
        '''
        idMap = self._kindIdMap.get(itemKind.kindId)
        return idMap.values()[0] if idMap else None

    def getItemByKindId(self, itemKindId):
        '''
        获取某个类型的一个道具
        '''
        idMap = self._kindIdMap.get(itemKindId)
        return idMap.values()[0] if idMap else None

    def getAllKindItem(self, itemKind):
        '''
        获取所有item
        @return: list<Item>
        '''
        return self.getAllKindItemByKindId(itemKind.kindId)

    def getAllKindItemByKindId(self, kindId):
        '''
        获取所有item
        @return: list<Item>
        '''
        idMap = self._kindIdMap.get(kindId)
        return idMap.values() if idMap else []

    def getAllTypeItem(self, itemType):
        '''
        获取所有item类类型为itemType的道具
        @return: list<Item>
        '''
        ret = []
        for item in self._itemIdMap.values():
            if type(item) == itemType:
                ret.append(item)
        return ret

    def addItem(self, gameId, item, timestamp, eventId, intEventParam):
        '''
        添加一个道具到背包
        '''
        self._addItem(item)
        balance = item.balance(timestamp)
        if item.itemKind.visibleInBag:
            tip = ModuleTipEvent(self._userId, gameId, 'bag', 1)
            pkeventbus.globalEventBus.publishEvent(tip)
        pkbireport.itemUpdate(gameId, self.userId, item.kindId,
                              balance, balance, eventId, intEventParam)
        self._onCountChanged()

    def addItemUnits(self, gameId, item, count, timestamp, eventId, intEventParam):
        '''
        给某个道具添加count个单位
        '''
        found = self.findItem(item.itemId)
        if found != item:
            ftlog.error('TYUserBagImpl.updateItem userId=', self.userId,
                        'item=', item,
                        'found=', found)
            raise ValueError()
        item.addUnits(count, timestamp)
        self.updateItem(gameId, item, timestamp)
        if item.itemKind.visibleInBag:
            tip = ModuleTipEvent(self._userId, gameId, 'bag', 1)
            pkeventbus.globalEventBus.publishEvent(tip)
        pkbireport.itemUpdate(gameId, self.userId, item.kindId,
                              count, self.calcTotalUnitsCount(item.itemKind, timestamp),
                              eventId, intEventParam)
        self._onCountChanged()
        return item

    def addItemUnitsByKind(self, gameId, itemKind, count, timestamp, fromUserId, eventId, intEventParam):
        '''
        添加count个单位的道具
        '''
        assert (count > 0)
        items = []
        is_new = True
        sameKindItemList = self.getAllKindItem(itemKind)
        if not itemKind.singleMode:
            for _ in xrange(count):
                item = itemKind.newItem(self._dao.nextItemId(), timestamp)
                item.fromUserId = fromUserId
                item.addUnits(1, timestamp)
                self._addItem(item)
                items.append(item)
        else:
            if sameKindItemList:
                item = sameKindItemList[0]
                item.fromUserId = fromUserId
                item.addUnits(count, timestamp)
                self.updateItem(gameId, item, timestamp)
                items.append(item)
                is_new = False
            else:
                item = itemKind.newItem(self._dao.nextItemId(), timestamp)
                item.fromUserId = fromUserId
                item.addUnits(count, timestamp)
                self._addItem(item)
                items.append(item)
        if is_new and items and items[0].itemKind.visibleInBag:
            tip = ModuleTipEvent(self._userId, gameId, 'bag', 1)
            pkeventbus.globalEventBus.publishEvent(tip)
        pkbireport.itemUpdate(gameId, self.userId, item.kindId,
                              count, self.calcTotalUnitsCount(itemKind, timestamp),
                              eventId, intEventParam)
        if self._isSendToUser:
            self._onCountChanged()
        return items

    def removeItem(self, gameId, item, timestamp, eventId, intEventParam):
        '''
        在背包中根据itemId删除道具，返回删除的道具
        @param itemId: 要删除的道具ID
        @return: item or None
        '''
        found = self.findItem(item.itemId)
        if found != item:
            ftlog.error('TYUserBagImpl.removeItem userId=', self.userId,
                        'item=', item,
                        'found=', found)
            raise ValueError()
        balance = item.balance(timestamp)
        self._removeItem(item)
        if balance > 0:
            pkbireport.itemUpdate(gameId, self.userId, item.kindId,
                                  -balance, self.calcTotalUnitsCount(item.itemKind, timestamp),
                                  eventId, intEventParam)
        self._onCountChanged()
        return item

    def calcTotalUnitsCount(self, itemKind, timestamp=None):
        '''
        计算所有itemKind种类的道具的数量
        @param itemKind: 那种类型
        @return: 剩余多少个单位
        '''
        timestamp = timestamp if timestamp is not None else pktimestamp.getCurrentTimestamp()
        return self._calcTotalUnitsCount(self.getAllKindItem(itemKind), timestamp)

    def _calcTotalUnitsCount(self, sameKindItemList, timestamp):
        total = 0
        for item in sameKindItemList:
            total += item.balance(timestamp)
        return total

    def consumeItemUnits(self, gameId, item, unitsCount, timestamp, eventId, intEventParam):
        '''
        消耗item unitsCount个单位
        @param item: 那个道具
        @param unitsCount: 多少个单位
        @return: consumeCount
        '''
        assert (item.itemKind.singleMode)
        if unitsCount > 0:
            balance = item.balance(timestamp)
            if balance >= unitsCount:
                item.consume(unitsCount, timestamp)
                self.updateItem(gameId, item, timestamp)
                pkbireport.itemUpdate(gameId, self.userId, item.kindId,
                                      -unitsCount, self.calcTotalUnitsCount(item.itemKind, timestamp),
                                      eventId, intEventParam)
                self._onCountChanged()
                return unitsCount
        return 0

    def consumeUnitsCountByKind(self, gameId, itemKind, unitsCount, timestamp, eventId, intEventParam):
        '''
        消耗道具种类为itemKind的unitsCount个单位的道具
        @param itemKind: 那种类型
        @param unitsCount: 多少个单位
        @return: consumeCount
        '''
        if unitsCount <= 0:
            return 0

        if not itemKind.singleMode:
            sameKindItemList = self.getAllKindItem(itemKind)
            if len(sameKindItemList) < unitsCount:
                return 0
            for i in xrange(unitsCount):
                item = sameKindItemList[i]
                self._removeItem(item)
            pkbireport.itemUpdate(gameId, self.userId, item.kindId,
                                  -unitsCount, len(sameKindItemList) - unitsCount,
                                  eventId, intEventParam)
        else:
            item = self.getItemByKind(itemKind)
            if item is None:
                return 0
            balance = item.balance(timestamp)
            if balance < unitsCount:
                return 0
            item.consume(unitsCount, timestamp)
            self._updateItem(item, timestamp)
            pkbireport.itemUpdate(gameId, self.userId, item.kindId,
                                  -unitsCount, balance - unitsCount,
                                  eventId, intEventParam)
        self._onCountChanged()
        return unitsCount

    def forceConsumeUnitsCountByKind(self, gameId, itemKind, unitsCount, timestamp, eventId, intEventParam):
        '''
        强制消耗道具种类为itemKind的unitsCount个单位的道具，如果不够则消耗所有的
        @param itemKind: 那种类型
        @param unitsCount: 多少个单位
        @return: consumeCount
        '''
        if unitsCount <= 0:
            return 0

        consumeCount = 0
        if not itemKind.singleMode:
            sameKindItemList = self.getAllKindItem(itemKind)
            consumeCount = min(sameKindItemList, unitsCount)
            for i in xrange(consumeCount):
                item = sameKindItemList[i]
                self._removeItem(item)
            pkbireport.itemUpdate(gameId, self.userId, item.kindId,
                                  -consumeCount, len(sameKindItemList) - consumeCount,
                                  eventId, intEventParam)
        else:
            item = self.getItemByKind(itemKind)
            if item:
                balance = item.balance(timestamp)
                consumeCount = min(balance, unitsCount)
                item.consume(consumeCount, timestamp)
                self._updateItem(item, timestamp)
                pkbireport.itemUpdate(gameId, self.userId, item.kindId,
                                      -consumeCount, balance - consumeCount,
                                      eventId, intEventParam)
        self._onCountChanged()
        return unitsCount

    def updateItem(self, gameId, item, timestamp=None):
        '''
        保存道具
        @param item: 要保存的道具
        '''
        found = self.findItem(item.itemId)
        if found != item:
            ftlog.error('TYUserBagImpl.updateItem userId=', self.userId,
                        'item=', item,
                        'found=', found)
            raise ValueError()
        self._updateItem(item, timestamp)
        return item

    def processWhenUserLogin(self, gameId, isDayFirst, timestamp=None):
        '''
        当用户登录时调用该方法，处理对用户登录感兴趣的道具
        @param gameId: 哪个游戏驱动
        @param isDayFirst: 是否是
        '''
        items = list(self._itemIdMap.values())
        timestamp = timestamp if timestamp is not None else pktimestamp.getCurrentTimestamp()
        for item in items:
            if item.needRemoveFromBag(timestamp):
                self._removeItem(item)
            else:
                item.itemKind.processWhenUserLogin(item, self._assets,
                                                   gameId, isDayFirst, timestamp)

    def getExecutableActions(self, item, timestamp):
        '''
        获取item支持的动作列表
        @return: list<TYItemAction>
        '''
        ret = []
        for action in item.itemKind.actionList:
            if action.canDo(self, item, timestamp):
                ret.append(action)
        return ret

    def doAction(self, gameId, item, actionName, timestamp=None, params={}):
        '''
        执行动作
        @param gameId: 哪个游戏驱动的
        @param item: 哪个道具执行
        @param actionName: 执行哪个动作
        '''
        action = item.itemKind.findActionByName(actionName)
        if not action:
            raise TYUnExecuteableException(item, actionName)
        ftlog.debug('TYUserBagImpl.doAction gameId=', gameId,
                    'userId=', self.userId,
                    'itemId=', item.itemId,
                    'itemKindId=', item.kindId,
                    'actionName=', actionName,
                    'timestamp=', timestamp,
                    'params=', params)
        timestamp = timestamp if timestamp is not None else pktimestamp.getCurrentTimestamp()
        return action.doAction(gameId, self._assets, item, timestamp, params)

    def _findActionByName(self, actions, actionName):
        if actions:
            for action in actions:
                if action.name == actionName:
                    return action
        return None

    def _addItem(self, item):
        if item.itemId in self._itemIdMap:
            raise TYDuplicateItemIdException(item.itemId)
        self._addItemToMap(item)
        self._dao.saveItem(self.userId, item)

    def _removeItem(self, item):
        ftlog.debug('TYUserBagImpl._removeItem itemId=', item.itemId,
                    'kindId=', item.itemKind.kindId,
                    'remaining=', item.remaining,
                    'expiresTime=', item.expiresTime)
        self._removeItemFromMap(item)
        self._dao.removeItem(self.userId, item)

    def _updateItem(self, item, timestamp):
        if item.needRemoveFromBag(timestamp):
            self._removeItem(item)
        else:
            self._dao.saveItem(self.userId, item)
        return item

    def _addItemToMap(self, item):
        self._itemIdMap[item.itemId] = item
        idMap = self._kindIdMap.get(item.kindId)
        if not idMap:
            idMap = {}
            self._kindIdMap[item.kindId] = idMap
        idMap[item.itemId] = item

    def _removeItemFromMap(self, item):
        del self._itemIdMap[item.itemId]
        idMap = self._kindIdMap.get(item.kindId)
        del idMap[item.itemId]
        if not idMap:
            del self._kindIdMap[item.kindId]


class TYAssetKind(TYConfable):
    TYPE_ID = 'unknown'

    def __init__(self):
        super(TYAssetKind, self).__init__()
        self.kindId = None
        self.displayName = None
        self.pic = None
        self.desc = None
        self.units = None
        self.keyForChangeNotify = None

    def decodeFromDict(self, d):
        self.kindId = d.get('kindId')
        if not isstring(self.kindId):
            raise TYItemConfException(d, 'TYAssetKind.kindId must be string')
        self.displayName = d.get('displayName')
        if not isstring(self.displayName):
            raise TYItemConfException(d, 'TYAssetKind.displayName must be string')
        self.pic = d.get('pic')
        if not isstring(self.pic):
            raise TYItemConfException(d, 'TYAssetKind.pic must be string')
        self.desc = d.get('desc')
        if not isstring(self.desc):
            raise TYItemConfException(d, 'TYAssetKind.desc must be string')
        self.units = d.get('units')
        if not isstring(self.units):
            raise TYItemConfException(d, 'TYAssetKind.units must be string')
        self.keyForChangeNotify = d.get('keyForChangeNotify')
        if not isstring(self.keyForChangeNotify):
            raise TYItemConfException(d, 'TYAssetKind.keyForChangeNotify must be string')
        return self

    def buildContentForDelivery(self, count):
        return '%s：%s%s' % (self.displayName, count, self.units)

    def buildContent(self, count, needUnits=True):
        if needUnits:
            return '%s%s%s' % (count, self.units, self.displayName)
        return '%s%s' % (count, self.displayName)

    def add(self, gameId, userAssets, kindId, count, timestamp, eventId, intEventParam):
        '''
        @return: finalCount
        '''
        raise NotImplementedError

    def consume(self, gameId, userAssets, kindId, count, timestamp, eventId, intEventParam):
        '''
        @return: consumeCount, finalCount
        '''
        raise NotImplementedError

    def forceConsume(self, gameId, userAssets, kindId, count, timestamp, eventId, intEventParam):
        '''
        @return: consumeCount, finalCount
        '''
        raise NotImplementedError

    def balance(self, userAssets, timestamp):
        '''
        @return: balance
        '''
        return NotImplementedError


class TYAssetKindItem(TYAssetKind):
    def __init__(self, itemKind):
        super(TYAssetKindItem, self).__init__()
        self.itemKind = itemKind
        self.kindId = self.buildKindIdByItemKind(itemKind)
        self.displayName = itemKind.displayName
        self.pic = itemKind.pic
        self.desc = itemKind.desc
        self.units = itemKind.units.displayName
        self.keyForChangeNotify = 'item'

    @classmethod
    def buildKindIdByItemKind(cls, itemKind):
        return cls.buildKindIdByItemKindId(itemKind.kindId)

    @classmethod
    def buildKindIdByItemKindId(cls, itemKindId):
        return 'item:%s' % (itemKindId)

    def add(self, gameId, userAssets, kindId, count, timestamp, eventId, intEventParam):
        '''
        @return: finalCount
        '''
        ftlog.debug('AssetKindItem.add gameId=', gameId,
                    'userId=', userAssets.userId,
                    'kind=', kindId,
                    'count=', count,
                    'eventId=', eventId,
                    'intEventParam=', intEventParam)
        userBag = userAssets.getUserBag()
        items = userBag.addItemUnitsByKind(gameId, self.itemKind, count,
                                           timestamp, 0, eventId, intEventParam)
        for item in items:
            item.itemKind.processWhenAdded(item, userAssets,
                                           gameId, timestamp)
        return userBag.calcTotalUnitsCount(self.itemKind)

    def consume(self, gameId, userAssets, kindId, count, timestamp, eventId, intEventParam):
        '''
        @return: consumeCount, finalCount
        '''
        ftlog.debug('AssetKindItem.consume gameId=', gameId,
                    'userId=', userAssets.userId,
                    'kind=', kindId,
                    'count=', count,
                    'eventId=', eventId,
                    'intEventParam=', intEventParam)
        userBag = userAssets.getUserBag()
        consumeCount = userBag.consumeUnitsCountByKind(gameId, self.itemKind, count,
                                                       timestamp, eventId, intEventParam)
        return consumeCount, userBag.calcTotalUnitsCount(self.itemKind)

    def forceConsume(self, gameId, userAssets, kindId, count, timestamp, eventId, intEventParam):
        '''
        @return: consumeCount
        '''
        ftlog.debug('AssetKindItem.forceConsume gameId=', gameId,
                    'userId=', userAssets.userId,
                    'kind=', kindId,
                    'count=', count,
                    'timestamp=', timestamp,
                    'eventId=', eventId,
                    'intEventParam=', intEventParam)
        userBag = userAssets.getUserBag()
        consumeCount = userBag.forceConsumeUnitsCountByKind(gameId, self.itemKind, count,
                                                            timestamp, eventId, intEventParam)
        return consumeCount, userBag.calcTotalUnitsCount(self.itemKind)

    def balance(self, userAssets, timestamp):
        '''
        @return: balance
        '''
        return userAssets.getUserBag().calcTotalUnitsCount(self.itemKind, timestamp)


class TYAssetKindRegister(TYConfableRegister):
    _typeid_clz_map = {}


class TYItemSystemImpl(TYItemSystem):
    def __init__(self, itemDataDao):
        # key=kindId, value=ItemKind
        self._itemKindMap = {}
        self._itemDao = TYItemDao(self, itemDataDao)
        self._assetKindMap = {}
        # (itemKind, count)
        self._initItemTemplateMap = {}

    def _decodeInitItems(self, initItemDictList, itemKindMap):
        ret = []
        for d in initItemDictList:
            itemKindId = d.get('itemKindId')
            itemKind = itemKindMap.get(itemKindId)
            if not itemKind:
                raise TYItemConfException(d, 'Not found itemKindId %s for initItems' % (itemKindId))
            count = d.get('count')
            if not isinstance(count, int) or count <= 0:
                raise TYItemConfException(d, 'InitItem.count must int > 0')
            ret.append((itemKind, count))
        return ret

    def reloadConf(self, conf):
        itemKindMap = {}
        assetKindMap = {}
        itemKindConfList = conf.get('items', [])
        assetKindConfList = conf.get('assets', [])
        initItemTemplateMap = {}

        # 解析所有的itemKind
        for itemKindConf in itemKindConfList:
            itemKind = TYItemKindRegister.decodeFromDict(itemKindConf)
            if itemKind.kindId in itemKindMap:
                raise TYItemConfException(conf, 'TYItemSystemImpl.itemKindId already exists %s' % (itemKind.kindId))
            itemKind.conf = itemKindConf
            itemKindMap[itemKind.kindId] = itemKind

        # 根据配置查找是否重复配置
        for assetKindConf in assetKindConfList:
            assetKind = TYAssetKindRegister.decodeFromDict(assetKindConf)
            if assetKind.kindId in assetKindMap:
                raise TYItemConfException(conf, 'TYItemSystemImpl.assetKindId already exists %s' % (assetKind.kindId))
            assetKindMap[assetKind.kindId] = assetKind

        # 初始每个itemKind
        for itemKind in itemKindMap.values():
            itemKind.initWhenLoaded(itemKindMap, assetKindMap)

        # 添加道具asset
        for _, itemKind in itemKindMap.iteritems():
            assetKindMap[TYAssetKindItem.buildKindIdByItemKind(itemKind)] = TYAssetKindItem(itemKind)

        if ftlog.is_debug():
            ftlog.debug('TYItemSystemImpl.reloadConf itemKindIds=', itemKindMap.keys())

        for k, initItemDictList in conf.get('user.init.items.templates', {}).iteritems():
            initItems = self._decodeInitItems(initItemDictList, itemKindMap)
            initItemTemplateMap[k] = initItems

        self._itemKindMap = itemKindMap
        self._assetKindMap = assetKindMap
        self._initItemTemplateMap = initItemTemplateMap
        if ftlog.is_debug():
            ftlog.debug('TYItemSystemImpl.reloadConf successed itemKindIds=', self._itemKindMap.keys(),
                        'assetKindIds=', self._assetKindMap.keys(),
                        'initItemTemplateMap=', [self._initItemTemplateMap.keys()])

    def getInitItems(self):
        '''
        获取用户初始化配置
        '''
        return self.getInitItemsByTemplateName('default_old')

    def getInitItemsNew(self):
        '''
        获取用户初始化配置
        '''
        return self.getInitItemsByTemplateName('default')

    def getInitItemsByTemplateName(self, templateName):
        return self._initItemTemplateMap.get(templateName)

    def findAssetKind(self, kindId):
        '''
        根据kindId查找asset定义
        @return: AssetKind or None
        '''
        return self._assetKindMap.get(kindId)

    def getAllAssetKind(self):
        '''
        获取所有asset定义
        @return: list<AssetKind>
        '''
        return self._assetKindMap.values()

    def findItemKind(self, kindId):
        '''
        根据kindId查找道具定义
        @param kindId: 道具类型ID 
        @return: ItemDefine 
        '''
        return self._itemKindMap.get(kindId)

    def getAllItemKind(self):
        '''
        获取所有道具定义
        @return: list<ItemKind>
        '''
        return self._itemKindMap.values()

    def getAllItemKindByType(self, itemKindClassType):
        '''
        获取所有itemKindClassType类型的道具定义
        @return: list<ItemKind>
        '''
        ret = []
        for itemKind in self._itemKindMap.values():
            if isinstance(itemKind, itemKindClassType):
                ret.append(itemKind)
        return ret

    def loadUserAssets(self, userId):
        '''
        加载用户背包
        @return: UserAssets
        '''
        return TYUserAssetsImpl(userId, self, self._itemDao)

    def newItemFromItemData(self, itemData):
        itemKind = self.findItemKind(itemData.itemKindId)
        if itemKind:
            itemId = self._itemDao.nextItemId()
            item = itemKind.newItemForDecode(itemId)
            item.decodeFromItemData(itemData)
            return item
        return None


class TYUserAssetsImpl(TYUserAssets):
    def __init__(self, userId, itemSystem, itemDao):
        super(TYUserAssetsImpl, self).__init__()
        self._userId = userId
        self._itemSystem = itemSystem
        self._itemDao = itemDao
        self._userBag = None

    @property
    def userId(self):
        return self._userId

    def getUserBag(self):
        if not self._userBag:
            userBag = TYUserBagImpl(self.userId, self._itemDao, self).load()
            if not self._userBag:
                self._userBag = userBag
        return self._userBag

    def balance(self, gameId, assetKindId, timestamp):
        '''
        获取assetKindId的余额
        '''
        assetKind = self._itemSystem.findAssetKind(assetKindId)
        if not assetKind:
            raise TYUnknownAssetKindException(assetKindId)
        return assetKind.balance(self, timestamp)

    def addAsset(self, gameId, assetKindId, count, timestamp, eventId, intEventParam):
        '''
        增加Asset
        @param gameId: 哪个游戏驱动的
        @param assetKindId: asset种类ID
        @param count: 个数
        @param timestamp: 时间戳
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: (AssetKind, count, final)
        '''
        assetKind = self._itemSystem.findAssetKind(assetKindId)
        if not assetKind:
            raise TYUnknownAssetKindException(assetKindId)
        final = assetKind.add(gameId, self, assetKind.kindId, count,
                              timestamp, eventId, intEventParam)
        return assetKind, count, final

    def consumeAsset(self, gameId, assetKindId, count, timestamp, eventId, intEventParam):
        '''
        消耗Asset
        @param gameId: 哪个游戏驱动的
        @param assetKindId: asset种类ID
        @param count: 个数
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: (TYAssetKind, consumeCount, final)
        '''
        assetKind = self._itemSystem.findAssetKind(assetKindId)
        if not assetKind:
            raise TYUnknownAssetKindException(assetKindId)
        consumeCount, final = assetKind.consume(gameId, self, assetKindId, count,
                                                timestamp, eventId, intEventParam)
        return assetKind, consumeCount, final

    def forceConsumeAsset(self, gameId, assetKindId, count, timestamp, eventId, intEventParam):
        '''
        消耗Asset
        @param gameId: 哪个游戏驱动的
        @param assetKindId: asset种类
        @param count: 个数
        @param timestamp: 时间戳
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: (TYAssetKind, consumeCount, final)
        '''
        assetKind = self._itemSystem.findAssetKind(assetKindId)
        if not assetKind:
            raise TYUnknownAssetKindException(assetKindId)
        consumeCount, final = assetKind.forceConsume(gameId, self, assetKindId, count,
                                                     timestamp, eventId, intEventParam)
        return assetKind, consumeCount, final

    def __backConsumed(self, gameId, assetList, eventId, intEventParam):
        for assetKind, count, _final in assetList:
            assetKind.add(gameId, self, assetKind.kindId, count, eventId, intEventParam)

    def consumeContentItemList(self, gameId, contentItemList, ignoreUnknown, timestamp, eventId, intEventParam):
        '''
        消耗contentItemList
        @param gameId: 哪个游戏驱动的
        @param contentItemList: 要消耗的内容
        @param ignoreUnknown: 是否忽略不认识的item, 如果不忽略则会抛出异常
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: list<(TYAssetKind, consumeCount, final)>
        '''
        ret = []
        assetKindCountTupleList = []
        for contentItem in contentItemList:
            if contentItem.count <= 0:
                continue
            assetKind = self._itemSystem.findAssetKind(contentItem.assetKindId)
            if not assetKind:
                if ignoreUnknown:
                    continue
                raise TYUnknownAssetKindException(contentItem.assetKindId)
            balance = assetKind.balance(self, timestamp)
            if balance < contentItem.count:
                raise TYAssetNotEnoughException(assetKind, contentItem.count, balance)
            assetKindCountTupleList.append((assetKind, contentItem.count))

        for assetKind, count in assetKindCountTupleList:
            consumeCount, final = assetKind.consume(gameId, self, assetKind.kindId, count, timestamp, eventId,
                                                    intEventParam)
            if consumeCount >= count:
                ret.append((assetKind, consumeCount, final))
            else:
                self.__backConsumed(gameId, ret, eventId, intEventParam)
                raise TYAssetNotEnoughException(assetKind, contentItem.count, final)
        return ret

    def sendContentItemList(self, gameId, contentItemList, count, ignoreUnknown, timestamp, eventId, intEventParam):
        '''
        给用户发货
        @param gameId: 哪个游戏驱动的
        @param contentItemList: 要发货的内容
        @param ignoreUnknown: 是否忽略不认识的item, 如果不忽略则会抛出异常
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: list<(TYAssetKind, consumeCount, final)>
        '''
        assert (count >= 1)
        ret = []
        contentItemList = TYContentUtils.mergeContentItemList(contentItemList)
        assetKindCountTuple = []
        for contentItem in contentItemList:
            assetKind = self._itemSystem.findAssetKind(contentItem.assetKindId)
            if not assetKind and not ignoreUnknown:
                raise TYUnknownAssetKindException(contentItem.assetKindId)
            if not assetKind:
                ftlog.error('TYUserAssetsImpl.sendContentItemList gameId=', gameId,
                            'userId=', self.userId,
                            'assetKindId=', contentItem.assetKindId,
                            'count=', count)
            if assetKind and contentItem.count > 0:
                assetKindCountTuple.append((assetKind, contentItem.count * count))
        i = 0
        try:
            for assetKind, count in assetKindCountTuple:
                i += 1
                self.getUserBag()._isSendToUser = (i == len(assetKindCountTuple))
                final = assetKind.add(gameId
                                      , self
                                      , assetKind.kindId
                                      , count
                                      , timestamp
                                      , eventId
                                      , intEventParam
                                      )
                ret.append((assetKind, count, final))
        finally:
            self.getUserBag()._isSendToUser = True
        return ret

    def sendContent(self, gameId, content, count, ignoreUnknown, timestamp, eventId, intEventParam):
        '''
        给用户发货
        @param gameId: 哪个游戏驱动的
        @param content: 要发货的内容
        @param count: 发多少个
        @param ignoreUnknown: 是否忽略不认识的item, 如果不忽略则会抛出异常
        @param eventId: 哪个事件触发的
        @param intEventParam: eventId相关的参数
        @return: list<(TYAssetKind, consumeCount, final)>
        '''
        return self.sendContentItemList(gameId, content.getItems(), count, ignoreUnknown, timestamp, eventId,
                                        intEventParam)


class TYAssetUtils(object):
    @classmethod
    def buildContent(cls, assetKindTuple, needUnits=True):
        return assetKindTuple[0].buildContent(assetKindTuple[1], needUnits)

    @classmethod
    def buildContents(cls, assetKindTupleList, needUnits=True):
        contents = []
        for assetKindTuple in assetKindTupleList:
            contents.append(cls.buildContent(assetKindTuple, needUnits))
        return contents

    @classmethod
    def buildContentsString(cls, assetKindTupleList, needUnits=True):
        contents = cls.buildContents(assetKindTupleList, needUnits)
        return ','.join(contents)

    @classmethod
    def buildItemContent(cls, itemKindTuple):
        return '%s%s%s' % (itemKindTuple[1], itemKindTuple[0].units.displayName, itemKindTuple[0].displayName)

    @classmethod
    def buildItemContents(cls, itemKindTupleList):
        contents = []
        for itemKindTuple in itemKindTupleList:
            contents.append(cls.buildItemContent(itemKindTuple))
        return contents

    @classmethod
    def buildItemContentsString(cls, itemKindTupleList):
        contents = cls.buildItemContents(itemKindTupleList)
        return ','.join(contents)

    @classmethod
    def getChangeDataNames(cls, assetKindTupleList):
        ret = set()
        for assetKind, _, _ in assetKindTupleList:
            if assetKind.keyForChangeNotify:
                ret.add(assetKind.keyForChangeNotify)
        return ret

    @classmethod
    def getAssetCount(cls, assetKindTupleList, assetKindId):
        ret = 0
        for assetKind, count, _ in assetKindTupleList:
            if assetKind.kindId == assetKindId:
                ret += count
        return ret
