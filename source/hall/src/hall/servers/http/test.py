# -*- coding=utf-8
'''
Created on 2015年6月24日

@author: zhaojiangang
'''

import base64
import json
import time
from sre_compile import isstring

from datetime import datetime

import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from freetime.entity.msg import MsgPack
from hall.entity import hallaccount
from hall.entity import hallitem, hallstore, datachangenotify, hallgamelist2, \
    halldailycheckin, hallads, hallranking, hallexchange, hallbenefits, \
    hallsubmember, fivestarrate, hall_first_recharge, hallled, halldomains, \
    hall_game_update, hallroulette, hallpopwnd, hall_friend_table, hall_fangka, \
    hall_wxappid, hall_fangka_buy_info
from hall.entity.hallactivity.activity_exchange_code import \
    TYActivityExchangeCode
from hall.entity.hallconf import HALL_GAMEID
from hall.entity.hallitem import TYItemNotEnoughException, TYDecroationItemKind, \
    TYDecroationItem
from hall.entity.todotask import TodoTaskHelper, TodoTaskAddExitNotification, \
    TodoTaskDownloadOrOpenThirdApp, TodoTaskVipLevelUp, TodoTaskTriggerEvent, \
    TodoTaskThirdSDKExtend
from hall.servers.common.base_http_checker import BaseHttpMsgChecker
from hall.servers.http.httpgame import HttpGameHandler
from hall.servers.util.account_handler import AccountTcpHandler
from hall.servers.util.ads_handler import AdsHelper
from hall.servers.util.decroation_handler import DecroationHelper
from hall.servers.util.hall_handler import HallHelper
from hall.servers.util.item_handler import ItemHelper
from hall.servers.util.rpc import user_remote
from hall.servers.util.rpc import vip_remote
from hall.servers.util.store_handler import StoreHelper
from hall.servers.util.vip_handler import VipTcpHandler
from poker.entity.biz.exceptions import TYBizException
from poker.entity.configure import gdata, configure
from poker.entity.dao import gamedata as pkgamedata, sessiondata, daobase, \
    userchip, gamedata, userdata
from poker.protocol import runhttp, router
from poker.protocol.decorator import markHttpHandler, markHttpMethod


@markHttpHandler
class TestHttpHandler(BaseHttpMsgChecker):
    def __init__(self):
        pass

    def isEnable(self):
        return gdata.enableTestHtml()

    def makeErrorResponse(self, ec, message):
        return {'error': {'ec': ec, 'message': message}}

    def makeResponse(self, result):
        return {'result': result}

    def _check_param_vipExp(self, key, params):
        vipExp = runhttp.getParamInt(key, 0)
        return None, vipExp

    def _check_param_level(self, key, params):
        level = runhttp.getParamInt(key, 0)
        return None, level

    def _check_param_count(self, key, params):
        count = runhttp.getParamInt(key, 0)
        return None, count

    def _check_param_score(self, key, params):
        value = runhttp.getParamInt(key, 0)
        return None, value

    def _check_param_rankingId(self, key, params):
        rankingId = runhttp.getParamInt(key, 0)
        return None, rankingId

    def _check_param_userIds(self, key, params):
        try:
            jstr = runhttp.getParamStr(key)
            userIdList = jstr.split(',')
            ret = []
            for userId in userIdList:
                ret.append(int(userId))
            return None, ret
        except:
            return 'the jsonstr params is not a list Format !!', None

    def _check_param_rankKey(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value:
            return self.makeErrorResponse(-1, '必须指定rankKey'), None
        return None, value

    def _check_param_inputType(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value:
            return self.makeErrorResponse(-1, '必须指定inputType'), None
        return None, value

    def _check_param_action(self, key, params):
        action = runhttp.getParamStr(key, '')
        if not action:
            return self.makeErrorResponse(-1, '必须指定要执行哪个动作'), None
        return None, action

    def _check_param_newName(self, key, params):
        newName = runhttp.getParamStr(key, '')
        if not newName or not isstring(newName):
            return self.makeErrorResponse(-1, '必须指定新昵称'), None
        return None, newName

    def _check_param_kindId(self, key, params):
        kindId = runhttp.getParamInt(key, 0)
        if kindId <= 0:
            return self.makeErrorResponse(-1, '没有指定道具类型'), None
        return None, kindId

    def _check_param_exchangeId(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value or not isstring(value):
            return self.makeErrorResponse(-1, '必须指定exchangeId'), None
        return None, value

    def _check_param_result(self, key, params):
        value = runhttp.getParamInt(key, -1)
        if value < 0:
            return self.makeErrorResponse(-1, '没有指定审核结果'), None
        return None, value

    def _check_param_times(self, key, params):
        times = runhttp.getParamInt(key, -1)
        if times < 0:
            return self.makeErrorResponse(-1, 'times必须是>=0的整数'), None
        return None, times

    def _check_param_today(self, key, params):
        today = runhttp.getParamStr(key, '')
        if today:
            today = datetime.strptime(today, '%Y%m%d').date()
        else:
            today = datetime.now().date()
        return None, today

    def _check_param_itemId(self, key, params):
        itemId = runhttp.getParamInt(key, 0)
        if itemId <= 0:
            return self.makeErrorResponse(-1, '道具ID必须是>0的整数'), None
        return None, itemId

    def _check_param_expires(self, key, params):
        expires = runhttp.getParamStr(key)
        if not expires or not isstring(expires):
            return self.makeErrorResponse(-1, '必须指定到期时间'), None
        return None, expires

    def _check_param_createTime(self, key, params):
        createTime = runhttp.getParamStr(key)
        if not createTime or not isstring(createTime):
            return self.makeErrorResponse(-1, '必须指定创建时间'), None
        return None, createTime

    def _check_param_productId(self, key, params):
        productId = runhttp.getParamStr(key)
        if not productId or not isstring(productId):
            return self.makeErrorResponse(-1, '必须指定要购买的商品'), None
        return None, productId

    def _check_param_prodId(self, key, params):
        productId = runhttp.getParamStr(key)
        if not productId or not isstring(productId):
            return self.makeErrorResponse(-1, '必须指定商品ID'), None
        return None, productId

    def _check_param_orderId(self, key, params):
        orderId = runhttp.getParamStr(key)
        if not orderId or not isstring(orderId):
            return self.makeErrorResponse(-1, '必须指定orderId'), None
        return None, orderId

    def _check_param_promoteCode(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定promoteCode'), None
        return None, value

    def _check_param_taskId(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定taskId'), None
        return None, value

    def _check_param_time(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定召回提醒时间'), None
        return None, value

    def _check_param_dsc(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value or not isstring(value):
            return self.makeErrorResponse(-1, '必须指定召回提醒内容'), None
        return None, value

    # packageName
    def _check_param_packageName(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value or not isstring(value):
            return self.makeErrorResponse(-1, '必须指定包名/Bundle ID'), None
        return None, value

    # scheme
    def _check_param_scheme(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value or not isstring(value):
            return self.makeErrorResponse(-1, '必须指定scheme'), None
        return None, value

    # appCode
    def _check_param_appCode(self, key, params):
        value = runhttp.getParamInt(key, 0)
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的appCode'), None
        return None, value

    # downloadUrl
    def _check_param_downloadUrl(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的downloadUrl'), None
        return None, value

    # downloadType
    def _check_param_downloadType(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的downloadType'), None
        return None, value

    # MD5
    def _check_param_MD5(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的MD5'), None
        return None, value

    # event
    def _check_param_event(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的event'), None
        return None, value

    # led
    def _check_param_led(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的led'), None
        return None, value

    # scope
    def _check_param_scope(self, key, params):
        value = runhttp.getParamStr(key, '')
        if value <= 0:
            return self.makeErrorResponse(-1, '必须指定有效的scope'), None
        return None, value

    # shareId
    def _check_param_shareId(self, key, params):
        shareId = runhttp.getParamStr(key, '')
        if not shareId:
            return self.makeErrorResponse(-1, '必须指定要检查哪个分享ID'), None
        return None, shareId

    # version
    def _check_param_version(self, key, params):
        version = runhttp.getParamStr(key, '')
        if not version:
            return self.makeErrorResponse(-1, '必须指定要游戏版本'), None
        return None, version

    # updateVersion
    def _check_param_updateVersion(self, key, params):
        updateVersion = runhttp.getParamStr(key, '')
        if not updateVersion:
            return self.makeErrorResponse(-1, '必须指定要游戏更新版本'), None
        return None, updateVersion

    def _check_param_activityId(self, key, params):
        actid = runhttp.getParamStr(key)
        if not actid:
            return self.makeErrorResponse(-1, '必须指定要活动id'), None
        return None, actid

    @markHttpMethod(httppath='/gtest/user/rename/check')
    def doRenameCheck(self, userId):
        ftlog.info('TestHttpHandler.doRenameCheck userId=', userId)
        mo = AccountTcpHandler._doChangeNameCheck(userId, sessiondata.getClientId(userId))
        return self.makeResponse(mo.pack())

    @markHttpMethod(httppath='/gtest/user/rename/try')
    def doRenameTry(self, userId, newName):
        ftlog.info('TestHttpHandler.doRenameTry userId=', userId)
        mo = AccountTcpHandler._doChangeNameTry(userId, sessiondata.getClientId(userId), newName)
        return self.makeResponse(mo.pack())

    @markHttpMethod(httppath='/gtest/game/list')
    def doHttpGameList(self):
        ftlog.info('TestHttpHandler.doHttpGameList')
        gameIdList = list(gdata.gameIds())
        gameIdList.sort()
        return self.makeResponse(gameIdList)

    @markHttpMethod(httppath='/gtest/item/list')
    def doHttpItemList(self):
        ftlog.info('TestHttpHandler.doHttpItemList')
        itemKindList = hallitem.itemSystem.getAllItemKind()
        ret = []
        for itemKind in itemKindList:
            ret.append({
                'kindId': itemKind.kindId,
                'displayName': itemKind.displayName,
                'masks': itemKind.masks if isinstance(itemKind, TYDecroationItemKind) else 0
            })
        return self.makeResponse(ret)

    def _encodeItem(self, userBag, item, timestamp):
        return {
            'itemId': item.itemId,
            'kindId': item.kindId,
            'displayName': item.itemKind.displayName,
            'pic': item.itemKind.pic,
            'count': item.balance(timestamp),
            'units': item.itemKind.units.displayName,
            'actions': ItemHelper.encodeItemActionList(9999, userBag, item, timestamp)
        }

    @markHttpMethod(httppath='/gtest/user/vip/setExp')
    def doVipSetExp(self, userId, vipExp):
        ftlog.info('TestHttpHandler.doVipSetExp userId=', userId,
                   'vipExp=', vipExp)

        pkgamedata.setGameAttr(userId, 9999, 'vip.exp', vipExp)
        return self.makeResponse({'userId': userId, 'vipExp': vipExp})

    @markHttpMethod(httppath='/gtest/user/vip/addExp')
    def doVipAddExp(self, userId, vipExp):
        ftlog.info('TestHttpHandler.doVipAddExp userId=', userId,
                   'vipExp=', vipExp)

        mo = vip_remote.addVipExp(9999, userId, vipExp)
        return self.makeResponse({'userId': userId, 'msg': mo})

    @markHttpMethod(httppath='/gtest/user/vip/vipInfo')
    def doVipInfo(self, userId):
        ftlog.info('TestHttpHandler.doVipAddExp userId=', userId)

        mo = VipTcpHandler._doNewVipInfo(9999, userId)
        return self.makeResponse({'userId': userId, 'msg': mo._ht})

    @markHttpMethod(httppath='/gtest/user/vip/vipGift')
    def doVipGift(self, userId, level):
        ftlog.info('TestHttpHandler.doVipGift userId=', userId,
                   'level=', level)
        mo = VipTcpHandler._doNewVipGift(9999, userId, level)
        return self.makeResponse({'userId': userId, 'msg': mo._ht})

    @markHttpMethod(httppath='/gtest/user/vip/setGiftState')
    def doSetVipGiftState(self, userId, level):
        ftlog.info('TestHttpHandler.doVipGift userId=', userId,
                   'level=', level)

        pkgamedata.delGameAttr(userId, 9999, 'vip.gift.states')

        msg = MsgPack()
        msg.setCmd('newvip')
        msg.setParam('action', 'vipInfo')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        mo = router.queryUtilServer(msg, userId)
        return self.makeResponse({'userId': userId, 'msg': mo._ht})

    @markHttpMethod(httppath='/gtest/user/item/list')
    def doHttpUserItemList(self, userId):
        ftlog.info('TestHttpHandler.doHttpUserItemList')
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        userItemList = []
        timestamp = pktimestamp.getCurrentTimestamp()
        for item in userBag.getAllItem():
            userItemList.append(self._encodeItem(userBag, item, timestamp))
        return self.makeResponse({'userId': userId, 'items': userItemList})

    @markHttpMethod(httppath='/gtest/user/item/incr')
    def doHttpUserItemIncr(self, gameId, userId, kindId, count):
        ftlog.info('TestHttpHandler.doHttpUserItemIncr gameId=', gameId,
                   'userId=', userId,
                   'kindId=', kindId,
                   'count=', count)
        if count > 0:
            return self._doHttpUserItemAdd(gameId, userId, kindId, count)
        elif count < 0:
            return self._doHttpUserItemConsume(gameId, userId, kindId, -count)
        return self.makeErrorResponse(-1, '数量不能为0')

    @markHttpMethod(httppath='/gtest/user/item/remove')
    def doHttpUserItemRemove(self, gameId, userId, itemId):
        ftlog.info('TestHttpHandler.doHttpUserItemRemove gameId=', gameId,
                   'userId=', userId,
                   'itemId=', itemId)
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.findItem(itemId)
        if not item:
            return self.makeErrorResponse(-1, '没有这个道具')
        timestamp = pktimestamp.getCurrentTimestamp()
        userBag.removeItem(gameId, item, timestamp, 'test', 0)
        userItemList = []
        for item in userBag.getAllItem():
            userItemList.append(self._encodeItem(userBag, item, timestamp))
        return self.makeResponse({'userId': userId, 'items': userItemList})

    @markHttpMethod(httppath='/gtest/user/item/setExpires')
    def doHttpUserItemExpires(self, userId, itemId, expires):
        ftlog.info('TestHttpHandler.doHttpUserItemExpires userId=', userId,
                   'itemId=', itemId,
                   'expires=', expires)
        expiresTimestamp = time.mktime(datetime.strptime(expires, '%Y-%m-%d %H:%M:%S').timetuple())
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.findItem(itemId)
        timestamp = int(time.time())
        if not item:
            return self.makeErrorResponse(-1, '没有这个道具')
        if item.itemKind.units.isTiming():
            item.expiresTime = expiresTimestamp
            userBag.updateItem(6, item, timestamp)
            datachangenotify.sendDataChangeNotify(6, userId, 'item')
            return self.makeResponse({'userId': userId, 'item': self._encodeItem(userBag, item, timestamp)})
        return self.makeErrorResponse(-1, '该道具不是时间类型的')

    @markHttpMethod(httppath='/gtest/user/item/setCreateTime')
    def doHttpUserItemCreateTime(self, userId, itemId, createTime):
        ftlog.info('TestHttpHandler.doHttpUserItemCreateTime userId=', userId,
                   'itemId=', itemId,
                   'createTime=', createTime)
        createTimeTimestamp = time.mktime(datetime.strptime(createTime, '%Y-%m-%d %H:%M:%S').timetuple())
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.findItem(itemId)
        timestamp = int(time.time())
        if not item:
            return self.makeErrorResponse(-1, '没有这个道具')
        item.createTime = createTimeTimestamp
        userBag.updateItem(6, item, timestamp)
        datachangenotify.sendDataChangeNotify(6, userId, 'item')
        return self.makeResponse({'userId': userId, 'item': self._encodeItem(userBag, item, timestamp)})

    def _doHttpUserItemAdd(self, gameId, userId, kindId, count):
        ftlog.info('TestHttpHandler.doHttpUserItemAdd')
        itemKind = hallitem.itemSystem.findItemKind(kindId)
        if not itemKind:
            return self.makeErrorResponse(-1, '不能识别的道具类型')
        timestamp = pktimestamp.getCurrentTimestamp()
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.addItemUnitsByKind(gameId, itemKind, count, timestamp, 0,
                                          'TEST_ADJUST', 0)[0]
        changed = ['item']
        if isinstance(item, TYDecroationItem):
            changed.append('decoration')
        datachangenotify.sendDataChangeNotify(gameId, userId, changed)
        return self.makeResponse({'userId': userId, 'item': self._encodeItem(userBag, item, timestamp)})

    def _doHttpUserItemConsume(self, gameId, userId, kindId, count):
        ftlog.info('TestHttpHandler.doHttpUserItemConsume')
        itemKind = hallitem.itemSystem.findItemKind(kindId)
        if not itemKind:
            return self.makeErrorResponse(-1, '不能识别的道具类型')
        if count <= 0:
            return self.makeErrorResponse(-1, '数量必须大于0')

        timestamp = pktimestamp.getCurrentTimestamp()
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        try:
            consumeCount = userBag.consumeUnitsCountByKind(gameId, itemKind, count, timestamp,
                                                           'TEST_ADJUST', 0)
            changed = ['item']
            if isinstance(itemKind, TYDecroationItemKind):
                changed.append('decoration')
            datachangenotify.sendDataChangeNotify(gameId, userId, changed)
            return self.makeResponse({'userId': userId, 'consumeCount': consumeCount, 'kindId': kindId})
        except TYItemNotEnoughException:
            return self.makeErrorResponse(-1, '道具数量不足')

    def _buildParams(self, userBag, item, actionName):
        params = {}
        action = item.itemKind.findActionByName(actionName)
        if action:
            paramNameTypeList = action.getParamNameTypeList()
            if paramNameTypeList:
                for paramName, paramTypes in paramNameTypeList:
                    if isinstance(paramTypes, (list, tuple)):
                        value = paramTypes[0](runhttp.getParamStr(paramName, ''))
                    else:
                        value = paramTypes(runhttp.getParamStr(paramName, ''))
                    params[paramName] = value
        if actionName == 'exchange':
            if 'phone' not in params:
                params['phoneNumber'] = '18618378234'
        return params

    @markHttpMethod(httppath='/gtest/user/item/action')
    def doHttpUserItemAction(self, gameId, userId, itemId, action):
        ftlog.info('TestHttpHandler.doHttpUserItemAction')
        timestamp = pktimestamp.getCurrentTimestamp()
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        item = userBag.findItem(itemId)
        if not item:
            return self.makeErrorResponse(-1, '没有找到该道具')
        try:
            params = self._buildParams(userBag, item, action)
            actionResult = userBag.doAction(gameId, item, action, timestamp, params)
            ftlog.info('doHttpUserItemAction gameId=', gameId,
                       'userId=', userId,
                       'itemId=', itemId,
                       'action=', action,
                       'params=', params,
                       'result=', actionResult)
            datachangenotify.sendDataChangeNotify(gameId, userId, 'item')
            return self.makeResponse({'userId': userId, 'item': self._encodeItem(userBag, item, timestamp)})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)

    @markHttpMethod(httppath='/gtest/user/exchange/listRecord')
    def doHttpUserExchangeList(self, userId):
        records = hallexchange.getExchangeRecords(userId)
        ret = []
        for record in records:
            itemKind = hallitem.itemSystem.findItemKind(record.itemKindId)
            if itemKind:
                ret.append({
                    'exchangeId': record.exchangeId,
                    'date': datetime.fromtimestamp(record.createTime).strftime('%Y-%m-%d'),
                    'consume': itemKind.displayName,
                    'consumeCount': 1,
                    'gotItem': record.params.get('desc'),
                    'state': record.state
                })
        return self.makeResponse(ret)

    @markHttpMethod(httppath='/gtest/user/exchange/audit')
    def doHttpUserExchangeAudit(self, userId, exchangeId, result):
        hallexchange.handleExchangeAuditResult(userId, exchangeId, result)
        return self.doHttpUserExchangeList(userId)

    @markHttpMethod(httppath='/gtest/rank/setUser')
    def doHttpRankSetUser(self, gameId, userId, inputType, score):
        ranks = {}
        timestamp = pktimestamp.getCurrentTimestamp()
        rankingUserMap = hallranking.rankingSystem.setUserByInputType(gameId, inputType, userId, score, timestamp)
        for rankingId, rankingUser in rankingUserMap.iteritems():
            ranks[rankingId] = {
                'score': rankingUser.score,
                'rank': rankingUser.rank,
                'userId': rankingUser.userId
            }
        return self.makeResponse(ranks)

    @markHttpMethod(httppath='/gtest/rank/removeUser')
    def doHttpRankRemoveUser(self, gameId, userId, inputType):
        timestamp = pktimestamp.getCurrentTimestamp()
        hallranking.rankingSystem.removeUserByInputType(gameId, inputType, userId, timestamp)
        return self.makeResponse({'userId': userId, 'inputType': inputType})

    @markHttpMethod(httppath='/gtest/rank/getRank')
    def doHttpRankQuery(self, gameId, userId, rankKey, clientId):
        msg = MsgPack()
        msg.setCmd('custom_rank')
        msg.setParam('action', 'query')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        msg.setParam('rankKey', rankKey)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)

    @markHttpMethod(httppath='/gtest/rank/remove')
    def doRemoveRank(self, rankingId):
        try:
            hallranking.rankingSystem.removeRanking(rankingId)
            return self.makeResponse({'rankingId': rankingId})
        except:
            ftlog.exception()
            return self.makeErrorResponse(1, 'exception')

    @markHttpMethod(httppath='/gtest/rank/removeAll')
    def doRemoveAllRank(self, rankingId):
        try:
            rankingDefineList = hallranking.rankingSystem.getRankingDefines()
            for rankingDefine in rankingDefineList:
                hallranking.rankingSystem.removeRanking(rankingDefine.rankingId)
            return self.makeResponse({})
        except:
            ftlog.exception()
            return self.makeErrorResponse(1, 'exception')

    @markHttpMethod(httppath='/gtest/rank/removeAllStatus')
    def doRemoveAllRankStatus(self):
        try:
            rankingDefineList = hallranking.rankingSystem.getRankingDefines()
            for rankingDefine in rankingDefineList:
                daobase.executeMixCmd('del', 'ranking.status:%s' % (rankingDefine.rankingId))
            return self.makeResponse({})
        except:
            ftlog.exception()
            return self.makeErrorResponse(1, 'exception')

    @markHttpMethod(httppath='/gtest/ads/queryResponse')
    def doHttpQueryAdsResponse(self, gameId, userId, clientId):
        adsTemplate = hallads.queryAds(gameId, userId, clientId)
        mo = AdsHelper.makeAdsQueryResponse(gameId, userId, clientId, adsTemplate)
        return self.makeResponse(mo._ht)

    @markHttpMethod(httppath='/gtest/ads/queryConfig')
    def doHttpQueryAdsConfig(self, gameId, userId, clientId):
        import pickle
        adsTemplate = hallads.queryAds(gameId, userId, clientId)
        return pickle.dumps(adsTemplate)

    @markHttpMethod(httppath='/gtest/user/decroation/query')
    def doDecroationQuery(self, userIds):
        ftlog.info('TestHttpHandler.doDecroationQuery userIds=', userIds)
        mo = DecroationHelper.makeDecroationQueryResponse(HALL_GAMEID, userIds, 0)
        return self.makeResponse(mo._ht)

    @markHttpMethod(httppath='/gtest/user/decroation/config')
    def doDecroationConfig(self, userId):
        ftlog.info('TestHttpHandler.doDecroationConfig userId=', userId)
        mo = DecroationHelper.makeDecoroationConfigResponse(HALL_GAMEID, userId)
        return self.makeResponse(mo._ht)

    def _encodeShelves(self, shelves):
        return {
            'name': shelves.name,
            'displayName': shelves.displayName,
            'isVisible': shelves.visibleInStore,
            'iconType': shelves.iconType,
            'sortValue': shelves.sortValue,
            'products': [StoreHelper.buildProductInfo(product) for product in shelves.productList]
        }

    @markHttpMethod(httppath='/gtest/store/shelves/list')
    def doHttpShelvesList(self, gameId, userId, clientId):
        try:
            if not clientId:
                clientId = sessiondata.getClientId(userId)
            ret = []
            shelvesList = hallstore.storeSystem.getShelvesListByClientId(gameId, userId, clientId)
            ftlog.debug('TestHttpHandler.doHttpShelvesList gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'shelvesList=', shelvesList)
            if shelvesList:
                shelvesList.sort(key=lambda shelves: shelves.sortValue)
                for shelves in shelvesList:
                    if shelves.visibleInStore:
                        ret.append(self._encodeShelves(shelves))
            return self.makeResponse({'userId': userId, 'shelvesList': ret})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)

    @markHttpMethod(httppath='/gtest/store/buy')
    def doHttpBuyProduct(self, gameId, userId, clientId, productId, orderId, count):
        try:
            product = hallstore.storeSystem.findProduct(productId)
            if product.buyType == 'exchange':
                msg = MsgPack()
                msg.setCmd('store')
                msg.setParam('action', 'buy')
                msg.setParam('gameId', gameId)
                msg.setParam('prodId', productId)
                msg.setParam('userId', userId)
                msg.setParam('clientId', clientId)
                router.sendUtilServer(msg, userId)
                return self.makeResponse({'userId': userId, 'productId': productId})
            # orderDeliveryResult = hallstore.exchangeProduct(gameId, userId, clientId,
            #                                                                 orderId, productId, count)
            #                 mo = StoreHelper.makeProductDeliveryResponse(userId, orderDeliveryResult)
            #                 return mo.pack()
            else:
                order = hallstore.storeSystem.buyProduct(gameId, userId, clientId, orderId, productId, count)
                return self.makeResponse({'userId': userId, 'productId': productId, 'orderId': order.orderId})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)

    @markHttpMethod(httppath='/gtest/dizhu/store/deliveryOrder')
    def doHttpDeliveryOrder(self, gameId, userId, clientId, prodId, orderId, count):
        try:
            product = hallstore.storeSystem.findProduct(prodId)
            if product.buyType == 'exchange':
                return self.makeErrorResponse(-1, '兑换类商品不能发货')
            isSub = runhttp.getParamInt('isSub', 0)

            msg = MsgPack()
            msg.setCmd('prod_delivery')
            msg.setParam('userId', userId)
            msg.setParam('orderId', orderId)
            msg.setParam('prodCount', count)
            msg.setParam('prodId', prodId)
            msg.setParam('appId', gameId)
            msg.setParam('orderPlatformId', '')
            msg.setParam('ok', '1')
            isSub = runhttp.getParamInt('is_msgnthly', 0)
            if isSub:
                msg.setParam('isSub', isSub)
            chargeType, chargeMap, consumeMap = HttpGameHandler.getChargeInfos()
            msg.setParam('consumeMap', consumeMap)
            msg.setParam('chargeMap', chargeMap)
            msg.setParam('chargeType', chargeType)
            return router.queryUtilServer(msg, userId)

        # mo = StoreTcpHandler.deliveryProduct(gameId, userId, orderId, prodId,
        #                                                  chargeType, chargeMap, consumeMap, isSub)
        #             return mo.pack()
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)

    @markHttpMethod(httppath='/gtest/gamelist2/query')
    def doQueryGameList2(self, gameId, userId, clientId):
        try:
            template = hallgamelist2.getUITemplate(gameId, userId, clientId)
            games, pages = HallHelper.encodeHallUITemplage(gameId, userId, clientId, template)
            return self.makeResponse({'games': games, 'pages': pages})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)

    @markHttpMethod(httppath='/gtest/dcheckin/status')
    def doDCheckinStatus(self, userId):
        try:
            states = halldailycheckin.dailyCheckin.getStates(HALL_GAMEID, userId, pktimestamp.getCurrentTimestamp())
            return self.makeResponse({'states': TodoTaskHelper.translateDailyCheckinStates(states)})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)

    @markHttpMethod(httppath='/gtest/dcheckin/setdays')
    def doDCheckinSetDays(self, userId):
        try:
            checkinDays = runhttp.getParamInt('ndays', 1)
            reward = runhttp.getParamInt('reward', 1)
            timestamp = pktimestamp.getCurrentTimestamp()

            if checkinDays <= 1 and reward:
                userdata.delAttr(userId, 'firstDailyCheckin')
                userdata.delAttr(userId, 'lastDailyCheckin')
                userdata.clearUserCache(userId)
                states = halldailycheckin.dailyCheckin.getStates(HALL_GAMEID, userId, timestamp)
                return self.makeResponse({'states': TodoTaskHelper.translateDailyCheckinStates(states)})

            checkinDays = max(1, checkinDays)
            # 
            ft = timestamp - (checkinDays - 1) * 86400
            # 最后签到时间改为昨天
            if reward:
                lt = timestamp - 86400
            else:
                lt = timestamp
            userdata.setAttrs(userId, {'firstDailyCheckin': ft, 'lastDailyCheckin': lt})
            states = halldailycheckin.dailyCheckin.getStates(HALL_GAMEID, userId, timestamp)
            return self.makeResponse({'states': TodoTaskHelper.translateDailyCheckinStates(states)})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)

    @markHttpMethod(httppath='/gtest/dcheckin/todotask')
    def doDCheckinTodoTask(self, userId):
        try:
            clientId = sessiondata.getClientId(userId)
            todotask = TodoTaskHelper.makeTodoTaskNsloginReward(HALL_GAMEID, userId, clientId)
            return self.makeResponse({'todotask': todotask.toDict()})
        except TYBizException, e:
            return self.makeErrorResponse(e.errorCode, e.message)

    @classmethod
    def fillUserBenefits(cls, userBenefits, mo):
        mo.setResult('updateDT', datetime.fromtimestamp(userBenefits.updateTime).strftime('%Y-%m-%d %H:%M:%S'))
        mo.setResult('times', userBenefits.times)
        mo.setResult('maxTimes', userBenefits.maxTimes)
        mo.setResult('sendChip', userBenefits.sendChip)
        mo.setResult('extTimes', userBenefits.extTimes)
        mo.setResult('extSendChip', userBenefits.extSendChip)
        mo.setResult('privilege', userBenefits.privilege.name if userBenefits.privilege else '')
        chip = userchip.getUserChipAll(userBenefits.userId)
        mo.setResult('canSend', userBenefits.hasLeftTimes() and chip < userBenefits.minChip)
        return mo

    @markHttpMethod(httppath='/gtest/user/benefits/query')
    def doQueryBenefits(self, userId):
        ftlog.info('TestHttpHandler.doQueryBenefits userId=', userId)
        timestamp = pktimestamp.getCurrentTimestamp()
        userBenefits = hallbenefits.benefitsSystem.loadUserBenefits(9999, userId, timestamp)
        mo = MsgPack()
        mo = self.fillUserBenefits(userBenefits, mo)
        return self.makeResponse(mo._ht)

    @markHttpMethod(httppath='/gtest/user/benefits/send')
    def doBenefitsSend(self, userId, today):
        ftlog.info('TestHttpHandler.doQueryBenefits userId=', userId,
                   'today=', today.strftime('%Y-%m-%d'))
        timestamp = int(time.mktime(today.timetuple()))
        sent, userBenefits = hallbenefits.benefitsSystem.sendBenefits(9999, userId, timestamp)
        mo = MsgPack()
        mo = self.fillUserBenefits(userBenefits, mo)
        mo.setResult('sentBenefits', sent)
        return self.makeResponse(mo._ht)

    @markHttpMethod(httppath='/gtest/user/benefits/setTimes')
    def doBenefitsSetTimes(self, userId, times):
        ftlog.info('TestHttpHandler.doQueryBenefits userId=', userId)
        timestamp = pktimestamp.getCurrentTimestamp()
        d = {'ut': int(time.time()), 'times': times}
        gamedata.setGameAttr(userId, 9999, 'benefits', json.dumps(d))
        userBenefits = hallbenefits.benefitsSystem.loadUserBenefits(9999, userId, timestamp)
        mo = MsgPack()
        mo = self.fillUserBenefits(userBenefits, mo)
        return self.makeResponse(mo._ht)

    def _encodeSubMemberStatus(self, status):
        return {'isSub': status.isSub,
                'subTime': status.subDT.strftime('%Y-%m-%d %H:%M:%S') if status.subDT else None,
                'deliveryDT': status.deliveryDT.strftime('%Y-%m-%d %H:%M:%S') if status.deliveryDT else None,
                'unsubDesc': status.unsubDesc}

    @markHttpMethod(httppath='/gtest/user/subMember/getInfo')
    def doSubMemberGetInfo(self, userId):
        status = hallsubmember.loadSubMemberStatus(userId)
        return self.makeResponse(self._encodeSubMemberStatus(status))

    def _check_param_isSub(self, key, params):
        value = runhttp.getParamInt(key, -1)
        if value not in (0, 1):
            return self.makeErrorResponse(-1, 'isSub必须是0或1的整数'), None
        return None, value

    def _check_param_unsubDesc(self, key, params):
        value = runhttp.getParamStr(key, '')
        return None, value

    def _check_param_subTime(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value:
            return None, None
        return None, datetime.strptime(value, '%Y-%m-%d')

    def _check_param_deliveryTime(self, key, params):
        value = runhttp.getParamStr(key, '')
        if not value:
            return None, None
        return None, datetime.strptime(value, '%Y-%m-%d')

    def _check_param_isTempVipUser(self, key, params):
        value = runhttp.getParamInt(key, -1)
        if value not in (0, 1):
            return self.makeErrorResponse(-1, 'isTempVipUser必须是0或1的整数'), None
        return None, value

    @markHttpMethod(httppath='/gtest/user/subMember/setSubInfo')
    def doSubMemberSetSubInfo(self, userId, isSub, unsubDesc):
        userdata.setAttrs(userId, {'isYouyifuVipUser': 1 if isSub else 0, 'youyifuVipMsg': unsubDesc})
        status = hallsubmember.loadSubMemberStatus(userId)
        return self.makeResponse(self._encodeSubMemberStatus(status))

    @markHttpMethod(httppath='/gtest/user/subMember/setTimeInfo')
    def doSubMemberSetTimeInfo(self, userId, subTime, deliveryTime):
        status = hallsubmember.loadSubMemberStatus(userId)
        status.subDT = subTime
        status.deliveryDT = deliveryTime
        hallsubmember._saveSubMemberStatus(userId, status)
        return self.makeResponse(self._encodeSubMemberStatus(status))

    @markHttpMethod(httppath='/gtest/user/subMember/unsub')
    def doSubMemberUnsub(self, userId, isTempVipUser):
        timestamp = pktimestamp.getCurrentTimestamp()
        userdata.delAttr(userId, 'isYouyifuVipUser')
        userdata.delAttr(userId, 'youyifuVipMsg')
        userdata.clearUserCache(userId)
        hallsubmember.unsubscribeMember(HALL_GAMEID, userId, isTempVipUser, timestamp, 'TEST_ADJUST', 0)
        status = hallsubmember.loadSubMemberStatus(userId)
        return self.makeResponse(self._encodeSubMemberStatus(status))

    def _check_param_fiveStarDesc(self, key, params):
        value = runhttp.getParamStr(key, '')
        return None, value

    @markHttpMethod(httppath='/gtest/fiveStar/triggle')
    def doTriggleFiveStarRate(self, userId, fiveStarDesc, clientId):
        timestamp = pktimestamp.getCurrentTimestamp()
        if not clientId:
            clientId = sessiondata.getClientId(userId)
        if not fiveStarDesc:
            fiveStarDesc = configure.getGameJson(6, 'public', {}).get('five_star_win_desc', '')
        _triggled, todotask = fivestarrate.triggleFiveStarRateIfNeed(userId, clientId, timestamp, fiveStarDesc)
        if todotask:
            return self.makeResponse({'todotask': todotask.toDict()})
        return self.makeResponse({})

    @markHttpMethod(httppath='/gtest/fiveStar/clear')
    def doClearFiveStarRate(self, userId, fiveStarDesc, clientId):
        if not clientId:
            clientId = sessiondata.getClientId(userId)
        fivestarrate.clearFiveStarRate(userId, clientId)
        return self.makeResponse({})

    @markHttpMethod(httppath='/gtest/generateExcode')
    def doGenExcode(self):
        paramsDict = runhttp.getDict()
        mo = TYActivityExchangeCode.doGenerateCode(paramsDict)
        return self.makeResponse(mo._ht)

    @markHttpMethod(httppath='/gtest/neituiguang/queryState')
    def doNeituiguangQueryState(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'query_state')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)

    @markHttpMethod(httppath='/gtest/neituiguang/checkCode')
    def doNeituiguangCheckCode(self, userId, promoteCode, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'code_check')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        msg.setParam('promoteCode', promoteCode)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)

    @markHttpMethod(httppath='/gtest/neituiguang/listInvitee')
    def doNeituiguangListInvitee(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'list_invitee')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)

    @markHttpMethod(httppath='/gtest/neituiguang/cancelCheckCode')
    def doNeituiguangCancelCheckCode(self, userId, promoteCode, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'cancel_code_check')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)

    @markHttpMethod(httppath='/gtest/neituiguang/queryTaskInfo')
    def doNeituiguangQueryTaskInfo(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'query_task_info')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)

    @markHttpMethod(httppath='/gtest/neituiguang/getTaskReward')
    def doNeituiguangGetTaskReward(self, userId, taskId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'get_task_reward')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        msg.setParam('taskId', taskId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)

    @markHttpMethod(httppath='/gtest/neituiguang/queryPrize')
    def doNeituiguangQueryPrize(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'query_prize')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)

    @markHttpMethod(httppath='/gtest/neituiguang/getPrize')
    def doNeituiguangGetPrize(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('promote_info')
        msg.setParam('action', 'get_prize')
        msg.setParam('gameId', 9999)
        msg.setParam('userId', userId)
        if clientId:
            msg.setParam('clientId', clientId)
        result = router.queryUtilServer(msg, userId)
        return self.makeResponse(result)

    @markHttpMethod(httppath='/gtest/firstRecharge/query')
    def doFirstRechargeQuery(self, userId, clientId, gameId):
        itemId = hall_first_recharge.queryFirstRecharge(gameId, userId, clientId)
        return itemId

    @markHttpMethod(httppath='/gtest/addExitNotification')
    def doAddExitNotification(self, userId, time, dsc):
        todotask = TodoTaskAddExitNotification(dsc, time)
        return TodoTaskHelper.sendTodoTask(HALL_GAMEID, userId, todotask)

    @markHttpMethod(httppath='/gtest/openThirdApp')
    def doOpenThirdAPp(self, packageName, scheme, appCode, downloadUrl, downloadType, MD5, userId):
        url = base64.b64decode(downloadUrl)
        todoTask = TodoTaskDownloadOrOpenThirdApp(packageName, scheme, url, downloadType, appCode, MD5)
        return TodoTaskHelper.sendTodoTask(HALL_GAMEID, userId, todoTask);

    @markHttpMethod(httppath='/gtest/vipLevelUp')
    def doVipLevelUp(self, userId):
        vipInfo = {"level": 1, "name": "VIP0", "exp": 50, "expCurrent": 50, "expNext": 100}
        desc = "VIPLEVELUP"
        todoTask = TodoTaskVipLevelUp(vipInfo, desc)
        return TodoTaskHelper.sendTodoTask(HALL_GAMEID, userId, todoTask);

    @markHttpMethod(httppath='/gtest/triggerEvent')
    def doTriggerEvent(self, userId, event):
        params = {}
        todoTask = TodoTaskTriggerEvent(event, params)
        return TodoTaskHelper.sendTodoTask(HALL_GAMEID, userId, todoTask);

    @markHttpMethod(httppath='/gtest/sendLed')
    def doSendLed(self, gameId, scope, led):
        mo = MsgPack()
        mo.setCmd('send_led')
        mo.setParam('msg', led)
        mo.setParam('gameId', gameId)
        mo.setParam('ismgr', 1)
        mo.setParam('scope', scope)
        mo.setParam('clientIds', [])
        router.sendToAll(mo, gdata.SRV_TYPE_UTIL)
        hallled.sendLed(gameId, led, 1, scope)
        return mo

    @markHttpMethod(httppath='/gtest/thirdSDKExtend')
    def doThirdSDKExtend(self, userId, action):
        todotask = TodoTaskThirdSDKExtend(action)
        return TodoTaskHelper.sendTodoTask(HALL_GAMEID, userId, todotask);

    @markHttpMethod(httppath='/gtest/getShareUrl')
    def doGetShareUrl(self, userId, shareId):
        from hall.entity import hallshare
        share = hallshare.findShare(int(shareId))
        return share.getUrl(9999, userId)

    @markHttpMethod(httppath='/gtest/getDashifen')
    def doGetDashifen(self, userId, clientId):
        info = hallaccount.getGameInfo(userId, clientId)
        return info

    @markHttpMethod(httppath='/gtest/getShareId')
    def getShareId(self, userId, gameId, event):
        from hall.entity import hallshare
        info = hallshare.getShareId(event, userId, gameId)
        return info

    @markHttpMethod(httppath='/gtest/free/queryTask')
    def do_free_query_task(self, userId, clientId):
        msg = MsgPack()
        msg.setCmd('game')
        msg.setParam('action', 'query_task')
        msg.setParam('gameId', 9999)
        msg.setParam('clientId', clientId)
        msg.setParam('userId', userId)
        return router.queryUtilServer(msg, userId)

    @markHttpMethod(httppath='/gtest/free/getTaskReward')
    def do_free_get_task_reward(self, userId, taskId, clientId):
        msg = MsgPack()
        msg.setCmd('game')
        msg.setParam('action', 'get_task_reward')
        msg.setParam('userId', userId)
        msg.setParam('gameId', 9999)
        msg.setParam('clientId', clientId)
        msg.setParam('taskid', taskId)
        return router.queryUtilServer(msg, userId)

    def _check_param_progress(self, key, params):
        progress = runhttp.getParamInt(key, 0)
        if progress < 0:
            return self.makeErrorResponse(-1, '进度值不能是负数'), None
        return None, progress

    @markHttpMethod(httppath='/gtest/free/setTaskProgress')
    def do_task_setProgress(self, userId, taskId, progress, clientId):
        return user_remote.free_set_task_progress(userId, taskId, progress, clientId)

    @markHttpMethod(httppath='/gtest/testDomainReplace')
    def do_domain_replace(self, downloadUrl):
        url = base64.b64decode(downloadUrl)
        return halldomains.replacedDomain(url, {})

    @markHttpMethod(httppath='/gtest/store/chargeNotify')
    def doTestChargeNotify(self, gameId, userId, productId, rmbs, diamonds, clientId):
        clientId = clientId or sessiondata.getClientId(userId)
        mo = MsgPack()
        mo.setCmd('charge_notify')
        mo.setParam('gameId', gameId)
        mo.setParam('userId', userId)
        mo.setParam('prodId', productId)
        mo.setParam('rmbs', rmbs)
        mo.setParam('diamonds', diamonds)
        mo.setParam('clientId', clientId)
        router.sendUtilServer(mo, userId)
        return 'success'

    @markHttpMethod(httppath='/gtest/update/getGameUpdateInfo')
    def doGetGameUpdateInfo(self, gameId, userId, clientId, version, updateVersion):
        hall_game_update.getUpdateInfo(gameId, userId, clientId, version, updateVersion)

    @markHttpMethod(httppath='/gtest/testRoulette')
    def doTestRoulette(self, userId, gameId, clientId, count):
        reStr = ''
        total = 0
        for _num in range(0, count):
            number = 1
            if _num % 3 == 1:
                number = 10
            elif _num % 3 == 2:
                number = 50

            reStr += ' ' + str(number)
            total += number
            hallroulette.doGoldLottery(userId, gameId, clientId, number)

        return reStr + ' total:' + str(total)

    @markHttpMethod(httppath='/gtest/activity/credit_query')
    def do_activity_credit_query(self, userId, gameId, clientId, activityId):
        msg = MsgPack()
        msg.setCmd('act')
        msg.setParam('action', 'credit_query')
        msg.setParam('userId', userId)
        msg.setParam('gameId', gameId)
        msg.setParam('clientId', clientId)
        msg.setParam('activityId', activityId)
        return router.queryUtilServer(msg, userId)

    @markHttpMethod(httppath='/gtest/activity/credit_exchange')
    def do_activity_credit_exchange(self, userId, gameId, clientId, activityId, itemId):
        msg = MsgPack()
        msg.setCmd('act')
        msg.setParam('action', 'credit_exchange')
        msg.setParam('userId', userId)
        msg.setParam('gameId', gameId)
        msg.setParam('clientId', clientId)
        msg.setParam('activityId', activityId)
        msg.setParam('productId', itemId)
        return router.queryUtilServer(msg, userId)

    @markHttpMethod(httppath='/gtest/newzhuanyun')
    def do_test_new_zhuanyun(self, userId, gameId, clientId, event):
        timestamp = pktimestamp.getCurrentTimestamp()
        benefitsSend, userBenefits = hallbenefits.benefitsSystem.sendBenefits(gameId, userId, timestamp)
        zhuanyun = hallpopwnd.makeTodoTaskZhuanyunByLevelName(gameId, userId, clientId, benefitsSend, userBenefits,
                                                              event)
        if zhuanyun:
            return TodoTaskHelper.sendTodoTask(gameId, userId, zhuanyun)

    @markHttpMethod(httppath='/gtest/friendTableInfo')
    def do_get_friend_table_info(self, roomId0):
        roomIdStr = hall_friend_table.getStringFTId(roomId0)
        pluginId = hall_friend_table.queryFriendTable(roomIdStr)
        if not pluginId:
            return 'None game use ftId:', roomIdStr
        return pluginId

    @markHttpMethod(httppath='/gtest/createFriendTable')
    def do_create_friend_table(self, gameId):
        ftId = hall_friend_table.createFriendTable(gameId)
        if not ftId:
            return 'No suitable ftId created, please get one more'
        return ftId

    @markHttpMethod(httppath='/gtest/queryFangKaItem')
    def do_query_fangka_item(self, userId, clientId):
        return hall_fangka.queryFangKaItem(9999, userId, clientId)

    @markHttpMethod(httppath='/gtest/queryWXAppid')
    def do_query_wxappid(self, userId, clientId):
        return hall_wxappid.queryWXAppid(9999, userId, clientId)

    @markHttpMethod(httppath='/gtest/queryFangKaBuyInfo')
    def do_query_fangKaBuyInfo(self, userId, clientId):
        return hall_fangka_buy_info.queryFangKaBuyInfo(9999, userId, clientId)
