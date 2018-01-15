# -*- coding=utf-8
'''
Created on 2015年6月8日

@author: zhaojiangang
'''

import json
import time
from sre_compile import isstring

from datetime import datetime

import freetime.util.log as ftlog
import poker.entity.biz.message.message as pkmessage
import poker.entity.dao.gamedata as pkgamedata
import poker.util.timestamp as pktimestamp
from poker.entity.biz.confobj import TYConfable, TYConfableRegister
from poker.entity.biz.content import TYContentUtils, TYContentRegister, \
    TYContentItem
from poker.entity.biz.item.item import TYAssetUtils
from poker.entity.biz.store.exceptions import TYStoreConfException, \
    TYBuyProductUnknownException, TYBuyProductOverCountException, \
    TYBuyConditionNotEnoughException, TYOrderNotFoundException, \
    TYDeliveryOrderDiffUserException, TYDeliveryProductNotFoundException, \
    TYBadOrderStateException, TYStoreException, TYDeliveryOrderDiffProductException
from poker.entity.configure import pokerconf
from poker.entity.events.tyevent import UserEvent
from poker.util import strutil


class TYProductBuyType(object):
    BUY_TYPE_CHARGE = 'charge'
    BUY_TYPE_CONSUME = 'consume'
    BUY_TYPE_DIRECT = 'direct'
    BUY_TYPE_EXCHANGE = 'exchange'
    ALL_BUY_TYPES = set([BUY_TYPE_CHARGE, BUY_TYPE_CONSUME, BUY_TYPE_DIRECT, BUY_TYPE_EXCHANGE])

    @classmethod
    def isValidBuyType(cls, buyType):
        return buyType in cls.ALL_BUY_TYPES


class TYBuyCondition(TYConfable):
    '''
    购买条件
    @param userId: 哪个用户购买
    @param product: 购买哪个商品
    @return: 如果符合购买条件则返回True，否则返回False
    '''

    def __init__(self):
        super(TYBuyCondition, self).__init__()
        self.visibleInStore = None
        self.failure = None

    def check(self, userId, product):
        raise NotImplemented()

    def decodeFromDict(self, d):
        visibleInStore = d.get('visibleInStore')
        if not visibleInStore in (0, 1):
            raise TYStoreConfException(d, 'BuyCondition.visibleInStore must in (0, 1)')
        failure = d.get('failure')
        if not isstring(failure):
            raise TYStoreConfException(d, 'BuyCondition.failure must be string')
        self.visibleInStore = visibleInStore
        self.failure = failure
        self._decodeFromDictImpl(d)
        return self

    def _decodeFromDictImpl(self, d):
        return self


class TYBuyConditionRegister(TYConfableRegister):
    _typeid_clz_map = {}


class TYProduct(TYConfable):
    def __init__(self):
        # 商品ID
        self.productId = None
        # 显示的名字
        self.displayName = None
        # 名字的图片
        self.displayNamePic = None
        # 图片
        self.pic = None
        # 价格
        self.price = None
        # 价格图片
        self.pricePic = None
        # 钻石价格
        self.priceDiamond = None
        # 购买类型: 'direct', 'consume', 'charge', exchange''
        self.buyType = None
        # 兑换所需要的物品
        self.exchangeFeeContentItem = None
        self.exchangeFeeNotEnoughText = None
        # 钻石兑换比例
        self.diamondExchangeRate = None
        # 说明
        self.desc = None
        #
        self.extDesc = None
        self.buyLimitDesc = None
        # 给用户发送的私信内容 
        self.mail = None
        # 商品包含的内容
        self.content = None
        # 购买条件
        self.buyConditionList = None
        # 购买限制
        self.buyCountLimit = None
        # 是否记录到快速购买的记录中
        self.recordLastBuy = None
        # 
        self.tag = None
        self.clientParams = None
        # 显示条件
        self.showConditions = None

    def clone(self):
        ret = TYProduct()
        ret.productId = self.productId
        ret.displayName = self.displayName
        ret.displayNamePic = self.displayNamePic
        ret.pic = self.pic
        ret.price = self.price
        ret.pricePic = self.pricePic
        ret.priceDiamond = self.priceDiamond
        ret.buyType = self.buyType
        ret.exchangeFeeContentItem = self.exchangeFeeContentItem
        ret.exchangeFeeNotEnoughText = self.exchangeFeeNotEnoughText
        ret.diamondExchangeRate = self.diamondExchangeRate
        ret.desc = self.desc
        ret.extDesc = self.extDesc
        ret.buyLimitDesc = self.buyLimitDesc
        ret.mail = self.mail
        ret.content = self.content
        ret.buyConditionList = self.buyConditionList
        ret.buyCountLimit = self.buyCountLimit
        ret.recordLastBuy = self.recordLastBuy
        ret.tag = self.tag
        ret.clientParams = self.clientParams
        ret.showConditions = self.showConditions
        return ret

    def getMinFixedAssetCount(self, assetKindId):
        if self.content:
            return TYContentUtils.getMinFixedAssetCount(self.content, assetKindId)
        return 0

    def decodeFromDict(self, d):
        if not isinstance(d, dict):
            raise TYStoreConfException(d, 'product must be dict')
        self.productId = d.get('productId', None)
        if not isstring(self.productId):
            raise TYStoreConfException(d, 'product.productId must be valid string')
        self.displayName = d.get('displayName')
        if not isstring(self.displayName):
            raise TYStoreConfException(d, 'product.displayName must be not empty string')

        self.displayNamePic = d.get('displayNamePic', '')
        if not isstring(self.displayNamePic):
            raise TYStoreConfException(d, 'product.displayNamePic must be not empty string')
        self.pic = d.get('pic')
        if not isstring(self.pic):
            raise TYStoreConfException(d, 'product.pic must be not empty string')
        self.price = d.get('price')
        if not isstring(self.price):
            raise TYStoreConfException(d, 'product.price must be string')
        self.pricePic = d.get('pricePic')
        if self.pricePic is not None and not isstring(self.pricePic):
            raise TYStoreConfException(d, 'product.pricePic must be string')
        self.priceDiamond = d.get('priceDiamond')
        if not isstring(self.priceDiamond):
            raise TYStoreConfException(d, 'product.priceDiamond must be string')
        self.desc = d.get('desc', '')
        if not isstring(self.desc):
            raise TYStoreConfException(d, 'product.desc must be string')

        self.extDesc = d.get('extDesc', '')
        if not isstring(self.extDesc):
            raise TYStoreConfException(d, 'product.extDesc must be string')
        self.buyLimitDesc = d.get('buyLimitDesc', '')
        if not isstring(self.buyLimitDesc):
            raise TYStoreConfException(d, 'product.buyLimitDesc must be string')

        self.buyType = d.get('buyType')
        if not TYProductBuyType.isValidBuyType(self.buyType):
            raise TYStoreConfException(d, 'product.buyType must in %s', (TYProductBuyType.ALL_BUY_TYPES))

        if self.buyType == 'exchange':
            exchangeFeeContentItem = d.get('exchangeFeeContent')
            if not exchangeFeeContentItem or not isinstance(exchangeFeeContentItem, dict):
                raise TYStoreConfException(d, 'product.exchangeFeeContent must be dict')
            self.exchangeFeeContentItem = TYContentItem.decodeFromDict(exchangeFeeContentItem)
            if self.exchangeFeeContentItem.count <= 0:
                raise TYStoreConfException(d, 'product.exchangeFeeContent.count must > 0')
            self.exchangeFeeNotEnoughText = d.get('exchangeFeeNotEnoughText', '')
            if not isstring(self.exchangeFeeNotEnoughText):
                raise TYStoreConfException(d, 'product.exchangeFeeNotEnoughText must be string')
        else:
            try:
                _floatPrice = float(self.price)
            except:
                raise TYStoreConfException(d, 'product.price must be float string')
            try:
                _intPriceDiamond = int(self.priceDiamond)
            except:
                raise TYStoreConfException(d, 'product.priceDiamond must be int string')
        self.diamondExchangeRate = d.get('diamondExchangeRate')
        if self.diamondExchangeRate and not isinstance(self.diamondExchangeRate, int):
            raise TYStoreConfException(d, 'product.diamondExchangeRate must be int')

        self.mail = d.get('mail')
        if self.mail and not isstring(self.mail):
            raise TYStoreConfException(d, 'product.mail must be string')

        content = d.get('content')
        if content:
            self.content = TYContentRegister.decodeFromDict(content)
        else:
            self.content = None
        buyConditionList = d.get('buyConditions')
        if buyConditionList and not isinstance(buyConditionList, list):
            raise TYStoreConfException(d, 'product.buyConditionList must be list')

        if buyConditionList:
            self.buyConditionList = []
            for buyCondition in buyConditionList:
                self.buyConditionList.append(TYBuyConditionRegister.decodeFromDict(buyCondition))
        else:
            self.buyConditionList = None

        buyCountLimit = d.get('buyCountLimit')
        if buyCountLimit:
            self.buyCountLimit = TYBuyCountLimit().decodeFromDict(buyCountLimit)
        else:
            self.buyCountLimit = None
        self.recordLastBuy = d.get('recordLastBuy', 1)
        if self.recordLastBuy not in (0, 1):
            raise TYStoreConfException(d, 'product.recordLastBuy must in (0,1)')
        self.tag = d.get('tag', '')
        if not isstring(self.tag):
            raise TYStoreConfException(d, 'product.tag must be string')
        self.clientParams = d.get('clientParams', {})
        if not isinstance(self.clientParams, dict):
            raise TYStoreConfException(d, 'product.clientParams must be dict')

        self.showConditions = d.get('showConditions', [])
        return self


class TYChargeInfo(object):
    def __init__(self, chargeType, chargeMap,
                 consumeMap):
        assert (chargeType is None or isstring(chargeType))
        assert (chargeMap is None or isinstance(chargeMap, dict))
        assert (consumeMap is None or isinstance(consumeMap, dict))
        if chargeMap:
            for k, v in consumeMap.iteritems():
                assert (isstring(k))
                assert (isinstance(v, (int, float)))
        if consumeMap:
            for k, v in consumeMap.iteritems():
                assert (isstring(k))
                assert (isinstance(v, (int, float)))
        self.chargeType = chargeType or ''
        self.chargeMap = chargeMap or {}
        self.consumeMap = consumeMap or {}

    def __repr__(self):
        return str(self.toDict())

    def __str__(self):
        return str(self.toDict())

    def __unicode__(self):
        return unicode(self.toDict())

    def getCharge(self, name, defValue):
        return self.chargeMap.get(name, defValue)

    def getConsume(self, name, defValue):
        return self.consumeMap.get(name, defValue)

    def toDict(self):
        return {'chargeType': self.chargeType, 'charges': self.consumeMap, 'consumes': self.consumeMap}


class TYOrder(object):
    STATE_CREATE = 0
    STATE_DELIVERYING = 1
    STATE_DELIVERY = 2

    def __init__(self, orderId=None,
                 platformOrderId=None,
                 userId=None,
                 gameId=None,
                 productId=None,
                 count=None,
                 clientId=None,
                 createTime=None,
                 updateTime=None,
                 state=STATE_CREATE,
                 errorCode=None,
                 chargeInfo=None):
        # 订单ID
        self.orderId = orderId
        # 平台订单ID
        self.platformOrderId = platformOrderId
        # 用户ID
        self.userId = userId
        # 在哪个游戏中购买的
        self.gameId = gameId
        # 购买商品的ID
        self.productId = productId
        # 购买的商品
        self.product = None
        # 数量
        self.count = count
        # 创建时间
        self.createTime = createTime
        # 最后更新时间
        self.updateTime = updateTime
        # 购买时的clientId
        self.clientId = clientId
        # 订单状态
        self.state = state
        # 发货失败时的错误信息
        self.errorCode = errorCode
        # 该订单的支付信息
        self.chargeInfo = chargeInfo


class TYOrderDeliveryResult(object):
    def __init__(self, order, assetItems):
        # 订单信息
        self.order = order
        # 发了什么货物
        self.assetItems = assetItems
        # 用什么兑换的
        self.consumeAssetItems = None


class TYOrderDeliveryEvent(UserEvent):
    '''
    发货事件，发货后由商品系统发出
    '''

    def __init__(self, gameId, userId, orderDeliveryResult):
        super(TYOrderDeliveryEvent, self).__init__(userId, gameId)
        self.orderDeliveryResult = orderDeliveryResult


class TYShelves(object):
    '''
    货架类，用于定义该货架能卖什么商品，是否在商城显示等
    '''

    def __init__(self, name, displayName, productList,
                 visibleInStore, iconType, sortValue=0,
                 visibleCondition=None):
        # 货架名称
        self.__name = name
        # 货架显示名称
        self.__displayName = displayName
        # 是否在商城中显示
        self.__visibleInStore = visibleInStore
        # 图标类型
        self.__iconType = iconType
        # 货架排序值
        self.__sortValue = sortValue
        # 商品列表list<TYProduct>
        self.__productList = productList
        # 商品map<productId, TYProduct>
        self._productMap = {p.productId: p for p in productList}
        # 显示条件
        self._visibleCondition = visibleCondition

    def cloneForProducts(self, productList):
        return TYShelves(self.name, self.displayName, self.productList,
                         self.visibleInStore, self.iconType, self.sortValue,
                         self._visibleCondition)

    @property
    def name(self):
        return self.__name

    @property
    def displayName(self):
        return self.__displayName

    @property
    def visibleInStore(self):
        return self.__visibleInStore

    @property
    def iconType(self):
        return self.__iconType

    @property
    def sortValue(self):
        return self.__sortValue

    @property
    def productMap(self):
        return self._productMap

    @property
    def productList(self):
        return self.__productList

    @property
    def visibleCondition(self):
        return self._visibleCondition

    def findProduct(self, productId):
        return self._productMap.get(productId)

    def findProductByAssetMinCount(self, assetKindId, minCount):
        '''
        从本货架中查找最少包含minCount个assetKindId的商品
        @return: Product or None
        '''
        for product in self.__productList:
            count = product.getMinFixedAssetCount(assetKindId)
            if count >= minCount:
                return product
        return None


class TYBuyCountLimitRecord(object):
    '''
    商品购买限制记录，用于记录购买周期内的购买次数
    '''

    def __init__(self, lastBuyTimestamp, count):
        # 最后一次购买时的时间戳
        self.lastBuyTimestamp = lastBuyTimestamp
        # 最后一次购买周期内的购买次数
        self.count = count


class TYBuyCountLimitTimeCycle(TYConfable):
    def __init__(self):
        super(TYBuyCountLimitTimeCycle, self).__init__()

    def isSameCycle(self, timestamp1, timestamp2):
        '''
        判断timestamp1和timestamp2是否在同一个周期
        '''
        raise NotImplemented()

    def decodeFromDict(self, d):
        return self


class TYBuyCountLimitTimeCycleLife(TYBuyCountLimitTimeCycle):
    '''
    本周期内限购
    '''
    TYPE_ID = 'life'

    def isSameCycle(self, timestamp1, timestamp2):
        return True


class TYBuyCountLimitTimeCyclePerDay(TYBuyCountLimitTimeCycle):
    '''
    每日限购
    '''
    TYPE_ID = 'perDay'

    def isSameCycle(self, timestamp1, timestamp2):
        return pktimestamp.getDayStartTimestamp(timestamp1) \
               == pktimestamp.getDayStartTimestamp(timestamp2)


class TYBuyCountLimitTimeCyclePerMonth(TYBuyCountLimitTimeCycle):
    '''
    每月限购
    '''
    TYPE_ID = 'perMonth'

    def isSameCycle(self, timestamp1, timestamp2):
        return pktimestamp.getMonthStartTimestamp(timestamp1) \
               == pktimestamp.getMonthStartTimestamp(timestamp2)


class TYBuyCountLimitTimeCycleRegister(TYConfableRegister):
    _typeid_clz_map = {
        TYBuyCountLimitTimeCycleLife.TYPE_ID: TYBuyCountLimitTimeCycleLife,
        TYBuyCountLimitTimeCyclePerDay.TYPE_ID: TYBuyCountLimitTimeCyclePerDay,
        TYBuyCountLimitTimeCyclePerMonth.TYPE_ID: TYBuyCountLimitTimeCyclePerMonth,
    }


class TYBuyCountLimit(TYConfable):
    '''
    商品购买数量限制类，用于定义该商品的购买周期，以及每个周期内可购买多少数量，以及一些提示信息等
    '''
    LIMIT_NON = 0
    LIMIT_START = 1
    LIMIT_END = 2
    LIMIT_COUNT = 3

    def __init__(self):
        super(TYBuyCountLimit, self).__init__()
        self.startTimestamp = None
        self.endTimestamp = None
        self.failure = None
        self.failureStart = None
        self.failureEnd = None
        self.visibleInStore = None
        self.limitCycle = None
        self.count = None

    def incrRecordCount(self, userId, record, count=1, timestamp=None):
        '''
        增加count次购买次数
        @param record: 购买限制记录TYBuyLimitRecord
        @param count: 增加多少次
        @param timestamp: 当前时间戳
        @return: record
        '''
        timestamp = timestamp if not timestamp else pktimestamp.getCurrentTimestamp()
        if self.limitCycle.isSameCycle(record.lastBuyTimestamp, timestamp):
            record.count += count
        else:
            record.count = count
        record.lastBuyTimestamp = timestamp
        return record

    def checkLimit(self, userId, record, count=1, timestamp=None):
        '''
        检查再购买count次是否超出购买限制
        @param record: 购买限制记录TYBuyLimitRecord
        @param count: 增加多少次
        @param timestamp: 当前时间戳
        @return: LIMIT_XXX
        '''
        timestamp = timestamp if not timestamp else pktimestamp.getCurrentTimestamp()
        if self.startTimestamp != -1 and timestamp < self.startTimestamp:
            return TYBuyCountLimit.LIMIT_START
        if self.endTimestamp != -1 and timestamp >= self.endTimestamp:
            return TYBuyCountLimit.LIMIT_END
        if self._isOverCount(userId, record, count, timestamp):
            return TYBuyCountLimit.LIMIT_COUNT
        return TYBuyCountLimit.LIMIT_NON

    def getFailureByLimit(self, limit):
        '''
        根据limit的值获取failue信息
        '''
        if limit == TYBuyCountLimit.LIMIT_START:
            return self.failureStart
        elif limit == TYBuyCountLimit.LIMIT_END:
            return self.failureEnd
        elif limit == TYBuyCountLimit.LIMIT_COUNT:
            return self.failure
        return ''

    def decodeFromDict(self, d):
        startTimeStr = d.get('startTime')
        endTimeStr = d.get('endTime')
        if startTimeStr:
            self.startTimestamp = time.mktime(datetime.strptime(startTimeStr, '%Y-%m-%d %H:%M:%S').timetuple())
        else:
            self.startTimestamp = -1
        if startTimeStr:
            self.endTimestamp = time.mktime(datetime.strptime(endTimeStr, '%Y-%m-%d %H:%M:%S').timetuple())
        else:
            self.endTimestamp = -1

        if self.endTimestamp != -1 and self.endTimestamp < self.startTimestamp:
            raise TYStoreConfException(d, 'BuyCountLimit.endTime must >= BuyCountLimit.startTime')
        self.count = d.get('count')
        if not isinstance(self.count, int) or self.count < -1:
            raise TYStoreConfException(d, 'BuyCountLimit.count must int >= -1')
        self.failure = d.get('failure')
        if not isstring(self.failure):
            raise TYStoreConfException(d, 'BuyCountLimit.failure must be string')

        self.failureStart = d.get('failureStart', self.failure)
        if not isstring(self.failureStart):
            raise TYStoreConfException(d, 'BuyCountLimit.failureStart must be string')

        self.failureEnd = d.get('failureEnd', self.failure)
        if not isstring(self.failureStart):
            raise TYStoreConfException(d, 'BuyCountLimit.failureEnd must be string')

        self.visibleInStore = d.get('visibleInStore')
        if self.visibleInStore not in (0, 1):
            raise TYStoreConfException(d, 'BuyCountLimit.visibleInStore must in (0,1)')
        cycle = d.get('cycle')
        if not isinstance(cycle, dict):
            raise TYStoreConfException(cycle, 'BuyCountLimit.cycle must be dict')
        self.limitCycle = TYBuyCountLimitTimeCycleRegister.decodeFromDict(cycle)
        return self

    def _isOverCount(self, userId, record, count, timestamp):
        if ftlog.is_debug():
            ftlog.debug('TYBuyCountLimit._isOverCount userId=', userId,
                        'record=', record.__dict__,
                        'count=', count,
                        'timestamp=', timestamp)
        # -1表示不限次数
        if self.count == -1:
            return False
        # 购买次数没有超限
        if record.count + count <= self.count:
            return False
        # 不在同一周期没有超限
        return self.limitCycle.isSameCycle(record.lastBuyTimestamp, timestamp)


class TYStoreSystem(object):
    def getShelvesListByClientId(self, gameId, userId, clientId):
        '''
        根据clientId查找货架列表
        @return list<TYShelves>
        '''
        raise NotImplemented()

    def getShelvesByClientId(self, gameId, userId, clientId, shelvesName):
        '''
        根据clientId查找货架列表
        @return TYShelves or None
        '''
        raise NotImplemented()

    def buyProduct(self, gameId, userId, clientId, orderId, productId, count):
        '''
        购买id=productId的商品
        @return: order
        '''
        raise NotImplemented()

    def findOrder(self, orderId):
        '''
        查找订单
        '''
        raise NotImplemented()

    def deliveryOrder(self, userId, orderId, productId, chargeInfo, switchProductId=None):
        '''
        给订单发货
        '''
        raise NotImplemented()

    def getLastBuyProduct(self, gameId, userId):
        '''
        获取最后购买的商品及购买商品的clientId
        @return: (product, clientId), or (None, None)
        '''
        raise NotImplemented()

    def findProduct(self, productId):
        '''
        根据productId查找product
        @return: TYProduct or None
        '''
        raise NotImplemented()

    def isCloseLastBuy(self, clientId):
        '''
        判断clientId是否关闭了最后购买记录
        '''
        raise NotImplemented()

    @property
    def firstRechargeThreshold(self):
        raise NotImplemented()


class TYLastBuyConf(object):
    def __init__(self):
        self.subText = ''
        self.subTextExt = ''
        self.desc = ''
        self.desc2 = ''
        self.payOrder = None

    def decodeFromDict(self, d):
        self.desc = d.get('desc', '')
        if not isstring(self.desc):
            raise TYStoreConfException(d, 'lastBuy.desc must be string')
        self.desc2 = d.get('desc2', '')
        if not isstring(self.desc):
            raise TYStoreConfException(d, 'lastBuy.desc2 must be string')
        self.subText = d.get('subText')
        if not isstring(self.subText):
            raise TYStoreConfException(d, 'lastBuy.subText must be string')
        self.subTextExt = d.get('subTextExt')
        if not isstring(self.subTextExt):
            raise TYStoreConfException(d, 'lastBuy.subTextExt must be string')
        self.payOrder = d.get('payOrder')
        if self.payOrder and not isinstance(self.payOrder, dict):
            raise TYStoreConfException(d, 'lastBuy.payOrder must be dict')
        return self


class TYStoreSystemImpl(TYStoreSystem):
    def __init__(self, itemSystem, orderDao, clientStoreConf, eventBus, userCondRegister):
        # 道具系统
        self._itemSystem = itemSystem
        # dao
        self._orderDao = orderDao
        # 商城模版配置
        self._clientStoreConf = clientStoreConf
        # key=productId, value=product
        self._productMap = {}
        # key=templateName, value=list<TYShelves>
        self._templateMap = {}
        self._pricePicMap = {}
        self._firstRechargeThreshold = 60
        self._lastBuyConf = TYLastBuyConf()
        self._deliveryConf = {}
        self._eventBus = eventBus
        self._userCondRegister = userCondRegister

    def reloadConf(self, productsConf, storeConf):
        pricePicMap = storeConf.get('pricePics', {})
        exchangePricePics = storeConf.get('exchangePricePics', {})

        productMap = {}
        productConfList = productsConf.get('products')
        for productConf in productConfList:
            product = TYProduct().decodeFromDict(productConf)
            if product.productId in productMap:
                raise TYStoreConfException(productConf, 'duplicate product %s' % (product.productId))
            productMap[product.productId] = product
            if product.buyType == 'exchange' and not product.price:
                product.price = str(product.exchangeFeeContentItem.count)
            if not product.pricePic:
                if product.buyType == 'exchange':
                    product.pricePic = exchangePricePics.get(product.exchangeFeeContentItem.assetKindId, '')
                else:
                    product.pricePic = pricePicMap.get(str(product.price), '')

        deliveryConf = storeConf.get('deliveryConf', {})
        if not isinstance(deliveryConf, dict):
            raise TYStoreConfException(storeConf, 'deliveryConf must be dict')

        firstRechargeThreshold = storeConf.get('firstRechargeThreshold', 60)
        if not isinstance(firstRechargeThreshold, int) or firstRechargeThreshold <= 0:
            raise TYStoreConfException(storeConf, 'firstRechargeThreshold must be int > 0')

        lastBuyConf = storeConf.get('lastBuy')
        if not isinstance(lastBuyConf, dict):
            raise TYStoreConfException(storeConf, 'lastBuyConf must be dict')
        lastBuyConf = TYLastBuyConf().decodeFromDict(lastBuyConf)

        templateMap = {}
        templates = storeConf.get('templates')
        if templates:
            for i, templateConf in enumerate(templates):
                templateName = templateConf.get('name')
                if not templateName or not isstring(templateName):
                    raise TYStoreConfException(templateConf,
                                               'template name must be string: %s index: %s' % (templateName, i))
                if templateName in templateMap:
                    raise TYStoreConfException(templateConf, 'duplicate template name: %s' % (templateName))

                shelvesConfList = templateConf.get('shelves', [])
                if not isinstance(shelvesConfList, list):
                    raise TYStoreConfException(templateConf, 'shelves must be list for template: %s' % (templateName))

                shelvesNameSet = set()
                shelvesList = []
                for j, shelvesConf in enumerate(shelvesConfList):
                    shelvesName = shelvesConf.get('name')
                    if not shelvesName or not isstring(shelvesName):
                        raise TYStoreConfException(shelvesConf,
                                                   'shelves.name must string for template: %s index: %s' % (
                                                       templateName, j))
                    if shelvesName in shelvesNameSet:
                        raise TYStoreConfException(shelvesConf, 'duplicate shelvesName %s for template %s' % (
                            shelvesName, templateName))
                    productIdList = shelvesConf['products']
                    productList = self._productIdListToProductList(productIdList, productMap)
                    visibleCondition = shelvesConf.get('visibleCondition')
                    if visibleCondition is not None:
                        visibleCondition = self._userCondRegister.decodeFromDict(visibleCondition)
                    shelvesNameSet.add(shelvesName)
                    shelvesList.append(TYShelves(shelvesConf['name'], shelvesConf['displayName'],
                                                 productList, shelvesConf['visible'],
                                                 shelvesConf.get('iconType', 'coin'),
                                                 shelvesConf.get('sort', 0),
                                                 visibleCondition))
                templateMap[templateName] = shelvesList
                #             for templateName, shelvesConfList in templates.iteritems():
                #                 shelvesList = []
                #                 shelvesNameSet = set()
                #                 for shelvesConf in shelvesConfList:
                #                     name = shelvesConf['name']
                #                     if name in shelvesNameSet:
                #                         raise TYStoreConfException(productConf, 'duplicate shelvesName %s for template %s' % (name, templateName))
                #                     productIdList = shelvesConf['products']
                #                     productList = self._productIdListToProductList(productIdList, productMap)
                #                     shelvesList.append(TYShelves(shelvesConf['name'], shelvesConf['displayName'],
                #                                                  productList, shelvesConf['visible'],
                #                                                  shelvesConf.get('iconType', 'coin'),
                #                                                  shelvesConf.get('sort', 0)))
                #                     shelvesNameSet.add(name)
                #                 templateMap[templateName] = shelvesList

        self._productMap = productMap
        self._templateMap = templateMap
        self._pricePicMap = pricePicMap
        self._lastBuyConf = lastBuyConf
        self._deliveryConf = deliveryConf
        self._firstRechargeThreshold = firstRechargeThreshold
        if ftlog.is_debug():
            ftlog.debug('TYStoreSystemImpl.reloadConf successed productIds=', productMap.keys(),
                        'firstRechargeThreshold=', firstRechargeThreshold,
                        'templates=', templateMap.keys())

    def getPricePic(self, price):
        return self._pricePicMap.get(str(price))

    @property
    def lastBuyConf(self):
        return self._lastBuyConf

    @property
    def firstRechargeThreshold(self):
        return self._firstRechargeThreshold

    @property
    def deliveryConf(self):
        return self._deliveryConf

    def getShelvesListByClientId(self, gameId, userId, clientId):
        templateName = None
        try:
            templateName = self._clientStoreConf.findTemplateNameByClientId(clientId)
            shelvesList = self._templateMap.get(templateName)
            if not shelvesList:
                return []
            filteredList = []
            timestamp = pktimestamp.getCurrentTimestamp()
            for shelves in shelvesList:
                if (shelves.visibleCondition
                    and not shelves.visibleCondition.check(gameId, userId, clientId, timestamp)):
                    continue
                productList = self._filterBuyLimitProducts(userId, shelves.productList)
                filteredList.append(shelves.cloneForProducts(productList))
            return filteredList
        except:
            ftlog.error('TYStoreSystemImpl.getShelvesListByClientId gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'templateName=', templateName)
            return []

    def getShelvesByClientId(self, gameId, userId, clientId, shelvesName):
        templateName = None
        try:
            templateName = self._clientStoreConf.findTemplateNameByClientId(clientId)
            shelvesList = self._templateMap.get(templateName)
            if shelvesList:
                timestamp = pktimestamp.getCurrentTimestamp()
                for shelves in shelvesList:
                    if (shelves.visibleCondition
                        and not shelves.visibleCondition.check(gameId, userId, clientId, timestamp)):
                        continue
                    if shelves.name == shelvesName:
                        productList = self._filterBuyLimitProducts(userId, shelves.productList)
                        return shelves.cloneForProducts(productList)
            return None
        except:
            ftlog.error('TYStoreSystemImpl.getShelvesByClientId gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'templateName=', templateName,
                        'shelvesName=', shelvesName)

    def buyProduct(self, gameId, userId, clientId, orderId, productId, count):
        product = self.findProduct(productId)
        if not product:
            raise TYBuyProductUnknownException(productId)

        timestamp = pktimestamp.getCurrentTimestamp()

        self._checkProductLimit(userId, product, count, timestamp)

        order = TYOrder(orderId, '', userId, gameId, product.productId, count, clientId,
                        timestamp, timestamp, TYOrder.STATE_CREATE, 0, None)
        order.product = product

        self._orderDao.addOrder(order)

        ftlog.hinfo('TYStoreSystemImpl.buyProduct gameId=', gameId,
                    'userId=', userId,
                    'clientId=', clientId,
                    'orderId=', orderId,
                    'productId=', productId,
                    'count=', count)

        return order

    def findProductInShelves(self, gameId, userId, clientId, productId):
        templateName = self._clientStoreConf.findTemplateNameByClientId(clientId)
        shelvesList = self._templateMap.get(templateName)
        timestamp = pktimestamp.getCurrentTimestamp()
        if shelvesList:
            for shelves in shelvesList:
                if (shelves.visibleCondition
                    and not shelves.visibleCondition.check(gameId, userId, clientId, timestamp)):
                    continue
                product = shelves.findProduct(productId)
                if product:
                    return product, shelves
        return None, None

    def canBuyProduct(self, gameId, userId, clientId, product, count):
        try:
            timestamp = pktimestamp.getCurrentTimestamp()
            product, _ = self.findProductInShelves(gameId, userId, clientId, product.productId)
            if product:
                self._checkProductLimit(userId, product, count, timestamp)
                return True
        except:
            pass
        return False

    def _buyProductImpl(self, gameId, userId, clientId, orderId, product, count):
        timestamp = pktimestamp.getCurrentTimestamp()

        self._checkProductLimit(userId, product, count, timestamp)

        order = TYOrder(orderId, '', userId, gameId, product.productId, count, clientId,
                        timestamp, timestamp, TYOrder.STATE_CREATE, 0, None)
        order.product = product

        self._orderDao.addOrder(order)

        return order

    def findOrder(self, orderId):
        '''
        查找订单
        '''
        return self._loadOrder(orderId)

    def deliveryOrder(self, userId, orderId, productId, chargeInfo, switchProductId=None):
        '''
        给订单发货
        '''
        order = self._loadOrder(orderId)
        if not order:
            ftlog.error('TYStoreSystemImpl.deliveryOrder userId=', userId,
                        'orderId=', orderId,
                        'productId=', productId,
                        'chargeInfo=', chargeInfo,
                        'switchProductId=', switchProductId,
                        'orderUserId=', order.userId,
                        'orderProductId=', order.productId,
                        'err=', 'OrderNotFound')
            raise TYOrderNotFoundException(orderId)

        if order.userId != userId:
            ftlog.error('TYStoreSystemImpl.deliveryOrder userId=', userId,
                        'orderId=', orderId,
                        'productId=', productId,
                        'chargeInfo=', chargeInfo,
                        'switchProductId=', switchProductId,
                        'orderUserId=', order.userId,
                        'orderProductId=', order.productId,
                        'err=', 'DiffUser')
            raise TYDeliveryOrderDiffUserException(orderId, order.userId, userId)

        if order.productId != productId:
            ftlog.error('TYStoreSystemImpl.deliveryOrder userId=', userId,
                        'orderId=', orderId,
                        'productId=', productId,
                        'chargeInfo=', chargeInfo,
                        'switchProductId=', switchProductId,
                        'orderUserId=', order.userId,
                        'orderProductId=', order.productId,
                        'err=', 'DiffProductId')
            raise TYDeliveryOrderDiffProductException(orderId, order.productId, productId)

        if switchProductId is not None and switchProductId != productId:
            switchProduct = self.findProduct(switchProductId)
            if not switchProduct:
                ftlog.error('TYStoreSystemImpl.deliveryOrder userId=', userId,
                            'orderId=', orderId,
                            'productId=', productId,
                            'chargeInfo=', chargeInfo,
                            'switchProductId=', switchProductId,
                            'orderUserId=', order.userId,
                            'orderProductId=', order.productId,
                            'err=', 'SwitchProductNotFound')
                raise TYDeliveryProductNotFoundException(orderId, switchProductId)
            order.product = switchProduct
            order.productId = switchProductId

        if not order.product:
            ftlog.error('TYStoreSystemImpl.deliveryOrder userId=', userId,
                        'orderId=', orderId,
                        'productId=', productId,
                        'chargeInfo=', chargeInfo,
                        'switchProductId=', switchProductId,
                        'orderUserId=', order.userId,
                        'orderProductId=', order.productId,
                        'err=', 'ProductNotFound')
            raise TYDeliveryProductNotFoundException(orderId, order.productId)

        if order.state != TYOrder.STATE_CREATE:
            ftlog.error('TYStoreSystemImpl.deliveryOrder userId=', userId,
                        'orderId=', orderId,
                        'productId=', productId,
                        'chargeInfo=', chargeInfo,
                        'switchProductId=', switchProductId,
                        'orderUserId=', order.userId,
                        'orderProductId=', order.productId,
                        'state=', order.state,
                        'err=', 'BadState')
            raise TYBadOrderStateException(orderId, order.state, TYOrder.STATE_CREATE)

        # 校验消耗的钻石和商品钻石的价格
        if order.product.buyType in (TYProductBuyType.BUY_TYPE_CONSUME,
                                     TYProductBuyType.BUY_TYPE_DIRECT):
            priceDiamond = int(order.product.priceDiamond) * order.count
            consumeDiamond = chargeInfo.getConsume('coin', 0)
            if consumeDiamond < priceDiamond:
                ftlog.warn('TYStoreSystemImpl.deliveryOrder userId=', userId,
                           'orderId=', orderId,
                           'productId=', productId,
                           'chargeInfo=', chargeInfo,
                           'switchProductId=', switchProductId,
                           'orderUserId=', order.userId,
                           'orderProductId=', order.productId,
                           'state=', order.state,
                           'priceDiamond=', priceDiamond,
                           'consumeDiamond=', consumeDiamond,
                           'err=', 'LessPriceDiamond')
                # raise TYStoreException(-1, '订单价格和商品价格不一致')

        try:
            order.updateTime = pktimestamp.getCurrentTimestamp()
            order.chargeInfo = chargeInfo
            order.state = TYOrder.STATE_DELIVERYING
            error, oldState = self._orderDao.updateOrder(order, TYOrder.STATE_CREATE)
            if error:
                raise TYBadOrderStateException(orderId, oldState, TYOrder.STATE_CREATE)

            self._finishDelivery(order, 0)
            orderDeliveryResult = self._deliveryOrder(order)
            self._recordBuy(orderDeliveryResult)
            self._eventBus.publishEvent(TYOrderDeliveryEvent(order.gameId, userId, orderDeliveryResult))
            return orderDeliveryResult
        except TYStoreException, e:
            if not isinstance(e, TYBadOrderStateException):
                self._finishDelivery(order, -1)
            ftlog.error('TYStoreSystemImpl.deliveryOrder userId=', userId,
                        'orderId=', orderId,
                        'chargeInfo=', chargeInfo,
                        'err=', e)
            raise
        except:
            self._finishDelivery(order, -2)
            ftlog.error('TYStoreSystemImpl.deliveryOrder userId=', userId,
                        'orderId=', orderId,
                        'chargeInfo=', chargeInfo,
                        'err=', 'Exception')
            raise

    def getLastBuyProduct(self, gameId, userId):
        '''
        获取最后购买的商品及购买商品的clientId
        '''
        lastBuy = None
        try:
            lastBuy = pkgamedata.getGameAttr(userId, 9999, 'lastbuy')
            if lastBuy is None:
                return None, None
            d = json.loads(lastBuy)
            product = self.findProduct(d['prodId'])
            if product:
                return product, d['clientId']
        except:
            ftlog.error('TYStoreSystem.getLastBuyProduct gameId=', gameId,
                        'userId=', userId,
                        'lastBuy=', lastBuy)
        return None, None

    def findProduct(self, productId):
        '''
        根据userId和clientId获取所有会员商品
        @return: list<Product>
        '''
        return self._productMap.get(productId)

    def isCloseLastBuy(self, clientId):
        '''
        判断clientId是否关闭了最后购买记录
        '''
        return self._clientStoreConf.isClosedLastBuy(clientId)

    def _productIdListToProductList(self, productIdList, allProductMap=None):
        productList = []
        productMap = {}
        allProductMap = allProductMap or self._productMap
        for productId in productIdList:
            if productId not in productMap:
                product = allProductMap.get(productId)
                if product:
                    productList.append(product)
                    productMap[product.productId] = product
                else:
                    ftlog.error('TYStoreSystemImpl._productIdListToProductList productId=', productId,
                                'err=', 'NotFoundProduct')
        return productList

    def _filterBuyLimitProducts(self, userId, productList):
        ret = []
        timestamp = pktimestamp.getCurrentTimestamp()
        for product in productList:
            if product.buyCountLimit:
                if (product.buyCountLimit
                    and not product.buyCountLimit.visibleInStore):
                    limit, record = self._checkBuyCountLimit(userId, product, 1, timestamp)
                    if limit != TYBuyCountLimit.LIMIT_NON:
                        ftlog.debug('TYStoreSystemImpl._filterBuyLimitProducts productId=', product.productId,
                                    'limit=', limit,
                                    'buyCountLimit=', product.buyCountLimit,
                                    'record.lastBuyTimestamp=', record.lastBuyTimestamp,
                                    'record.count=', record.count)
                        continue
            if product.buyConditionList:
                ok, buyCondition = self._checkNotInVisibleBuyConditions(userId, product, 1)
                if not ok:
                    ftlog.debug('TYStoreSystemImpl._filterBuyLimitProducts productId=', product.productId,
                                'buyCondition=', buyCondition)
                    continue
            ret.append(product)
        return ret

    def _checkProductLimit(self, userId, product, count, timestamp):
        ftlog.debug('TYStoreSystemImpl._checkProductLimit userId=', userId,
                    'productId=', product.productId,
                    'count=', count,
                    'buyCountLimit=', product.buyCountLimit,
                    'buyConditions=', product.buyConditionList)

        if product.buyCountLimit:
            limit, record = \
                self._checkBuyCountLimit(userId, product, count, timestamp)
            if limit != TYBuyCountLimit.LIMIT_NON:
                ftlog.debug('TYStoreSystemImpl._checkProductLimit userId=', userId,
                            'productId=', product.productId,
                            'count=', count,
                            'buyCountLimit=', product.buyCountLimit,
                            'limit=', limit)
                raise TYBuyProductOverCountException(product.productId, product.buyCountLimit, record, limit)
        if product.buyConditionList:
            ok, buyCondition = self._checkBuyConditions(userId, product, count)
            if not ok:
                ftlog.debug('TYStoreSystemImpl._checkProductLimit userId=', userId,
                            'productId=', product.productId,
                            'count=', count,
                            'buyCondition=', buyCondition)
                raise TYBuyConditionNotEnoughException(product.productId, buyCondition)

    def _checkBuyCountLimit(self, userId, product, count, timestamp):
        record = self._loadBuyCountLimitRecord(userId, product.productId, timestamp)
        limit = product.buyCountLimit.checkLimit(userId, record, count, timestamp)
        ftlog.debug('TYStoreSystemImpl._checkBuyCountLimit userId=', userId,
                    'productId=', product.productId,
                    'count=', count,
                    'timestamp=', timestamp,
                    'buyCountLimit=', product.buyCountLimit,
                    'limit=', limit)
        return limit, record

    def _checkBuyConditions(self, userId, product, count):
        for buyCondition in product.buyConditionList:
            if not buyCondition.check(userId, product):
                return False, buyCondition
        return True, None

    def _checkNotInVisibleBuyConditions(self, userId, product, count):
        for buyCondition in product.buyConditionList:
            if (not buyCondition.visibleInStore
                and not buyCondition.check(userId, product)):
                return False, buyCondition
        return True, None

    def _recordBuy(self, orderDeliveryResult):
        try:
            self._recordForBuyCountLimit(orderDeliveryResult.order)
            if orderDeliveryResult.order.product.recordLastBuy:
                self._recordLastBuyProduct(orderDeliveryResult.order)
        except:
            ftlog.error('TYStoreImpl._recordBuy orderId=', orderDeliveryResult.order.orderId)

    def _loadOrder(self, orderId):
        order = self._orderDao.loadOrder(orderId)
        if order:
            order.product = self.findProduct(order.productId)
        return order

    def _deliveryOrder(self, order):
        userAssets = self._itemSystem.loadUserAssets(order.userId)
        assetList = userAssets.sendContent(order.gameId, order.product.content,
                                           order.count, True, pktimestamp.getCurrentTimestamp(),
                                           'BUY_PRODUCT', pokerconf.productIdToNumber(order.productId))

        contents = TYAssetUtils.buildContentsString(assetList)
        if order.product.mail:
            mail = strutil.replaceParams(order.product.mail, {
                'count': str(order.count),
                'displayName': order.product.displayName,
                'content': contents
            })
            pkmessage.send(pkmessage.HALL_GAMEID, pkmessage.MESSAGE_TYPE_SYSTEM, order.userId, mail)
        ftlog.hinfo('TYStoreSystemImpl.deliveryOrder',
                    'orderId=', order.orderId,
                    'platformOrderId=', order.platformOrderId,
                    'productId=', order.productId,
                    'userId=', order.userId,
                    'gameId=', order.gameId,
                    'count=', order.count,
                    'chargeInfo=', order.chargeInfo,
                    'contents=', contents)
        return TYOrderDeliveryResult(order, assetList)

    def _finishDelivery(self, order, errorCode):
        order.errorCode = errorCode
        order.state = TYOrder.STATE_DELIVERY
        order.updateTime = pktimestamp.getCurrentTimestamp()
        error, oldState = self._orderDao.updateOrder(order, TYOrder.STATE_DELIVERYING)
        if error != 0:
            ftlog.hinfo('TYStoreSystemImpl._finishDelivery orderId=', order.orderId,
                        'platformOrderId=', order.platformOrderId,
                        'userId=', order.userId,
                        'gameId=', order.gameId,
                        'productId', order.productId,
                        'count=', order.count,
                        'chargeInfo=', order.chargeInfo,
                        'errorCode=', order.errorCode,
                        'oldState=', oldState)
        else:
            ftlog.hinfo('TYStoreSystemImpl._finishDelivery orderId=', order.orderId,
                        'platformOrderId=', order.platformOrderId,
                        'userId=', order.userId,
                        'gameId=', order.gameId,
                        'productId', order.productId,
                        'count=', order.count,
                        'chargeInfo=', order.chargeInfo,
                        'errorCode=', order.errorCode)
        return error, oldState

    def _recordForBuyCountLimit(self, order):
        if order.product.buyCountLimit:
            record = self._loadBuyCountLimitRecord(order.userId, order.productId, order.updateTime)
            order.product.buyCountLimit.incrRecordCount(order.userId, record, order.count, order.updateTime)
            self._saveBuyCountLimitRecord(order.userId, order.productId, record)

    def _buildBuyCountLimitRecordField(self, userId, productId):
        return 'buy.limit.record.%s' % (productId)

    def _loadBuyCountLimitRecord(self, userId, productId, timestamp):
        try:
            field = self._buildBuyCountLimitRecordField(userId, productId)
            jstr = pkgamedata.getGameAttr(userId, 9999, field)
            if jstr:
                d = json.loads(jstr)
                return TYBuyCountLimitRecord(d['ts'], d['count'])
        except:
            ftlog.error('TYStoreImpl._loadBuyCountLimitRecord userId=', userId,
                        'productId=', productId,
                        'timestamp=', timestamp)
        return TYBuyCountLimitRecord(timestamp, 0)

    def _saveBuyCountLimitRecord(self, userId, productId, record):
        d = {
            'ts': record.lastBuyTimestamp,
            'count': record.count
        }
        jstr = json.dumps(d)
        field = self._buildBuyCountLimitRecordField(userId, productId)
        pkgamedata.setGameAttr(userId, 9999, field, jstr)
        return record

    def _recordLastBuyProduct(self, order):
        d = {
            'prodId': order.productId,
            'clientId': order.clientId
        }
        jstr = json.dumps(d)
        pkgamedata.setGameAttr(order.userId, 9999, 'lastbuy', jstr)
