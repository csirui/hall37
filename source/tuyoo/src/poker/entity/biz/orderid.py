# -*- coding=utf-8
'''
Created on 2015年6月3日

@author: zhaoqh
'''
import re

from datetime import datetime

import freetime.util.log as ftlog
from poker.entity.configure import gdata
from poker.entity.dao import daobase
from poker.util import webpage

orderIdVer1 = 'a'  # Decimal62.tostr62(10, 1)  # a
consumeOrderIdVer1 = 'b'  # Decimal62.tostr62(11, 1)  # b
orderIdVer3 = 'c'  # Decimal62.tostr62(12, 1)  # c
consumeOrderIdVer3 = 'd'  # Decimal62.tostr62(13, 1)  # d
danjiOrderIdVer3 = 'f'  # Decimal62.tostr62(15, 1)  # f
smsBindOrderIdVer3 = 's'  # Decimal62.tostr62(13, 1)  # d
changTianYouOrderIdVer3 = 'y'  # Decimal62.tostr62(13, 1)  # d


def is_valid_orderid_str(orderid):
    return re.match(r'^[a-zA-Z0-9]{14}', orderid)


def get_appid_frm_order_id(orderId):
    # a00111x54Lq00l
    # apiVer, appId, seq
    _, appId, _ = get_order_id_info(orderId)
    return appId


def get_order_id_info(orderId):
    # a00111x54Lq00l
    apiVer, appId, seq = 0, 0, 0
    try:
        if len(orderId) == 14:
            apiVer = orderId[0]
            appId = hex(orderId[1:5], 16)
            seq = hex(orderId[5:], 16)
    except:
        ftlog.error('orderId=', orderId)
    return apiVer, appId, seq


def makeConsumeOrderIdV3(userId, appId, clientId):
    return make_order_id(appId, consumeOrderIdVer3)


def makeChargeOrderIdV3(userId, appId, clientId):
    return make_order_id(appId, orderIdVer3)


def makeSmsBindOrderIdV3(userId, appId, clientId):
    return make_order_id(appId, smsBindOrderIdVer3)


def makeChangTianYouOrderIdV3(userId, appId, clientId):
    return make_order_id(appId, changTianYouOrderIdVer3)


def makePlatformOrderIdV1(userId, params):
    appId = int(params['appId'])
    return make_order_id(appId, orderIdVer1)


def makeGameOrderIdV1(userId, params):
    appId = int(params['appId'])
    return make_order_id(appId, consumeOrderIdVer1)


def make_order_id(appId, orderIdVer62, httpcallback=None, isRemote=False):
    if gdata.mode() == gdata.RUN_MODE_ONLINE or isRemote:
        appId = int(appId)
        seqNum = daobase.executeMixCmd('INCR', 'global.orderid.seq.' + orderIdVer62)
        # orderId构成:<1位API版本号>+<4位APPID>+DD+<5位序号>，共14位
        ct = datetime.now()
        dd = ct.strftime('%d')
        a = hex(appId)[2:][-4:]
        a = '0' * (4 - len(a)) + a
        b = hex(seqNum)[2:][-7:]
        b = '0' * (7 - len(b)) + b
        oid = orderIdVer62 + a + dd + b
        # 记录单号回应的回调地址
        if httpcallback != None and isinstance(httpcallback, (str, unicode)) and httpcallback.find('http://') == 0:
            daobase.executeMixCmd('HSET', 'global.orderid.callback', oid, httpcallback)
        return oid
    else:
        # 通知订单数据中心(线上GATEWAY服务), 产生了一个新订单, 需要进行 单号<->回调服务的记录
        httpurl = gdata.httpOnlieGateWay() + '/_testorder_make_id'
        datas = {
            'appId': appId,
            'orderIdVer62': orderIdVer62,
            'httpcallback': gdata.httpSdk()
        }
        result, _ = webpage.webgetJson(httpurl, datas, None, 10)
        return result['orderPlatformId']


def getOrderIdHttpCallBack(orderId):
    # 取得单号对应的callback地址, 如果没有Name意味就是本机线上服务单号
    httpcallback = daobase.executeMixCmd('HGET', 'global.orderid.callback', orderId)
    if httpcallback != None and isinstance(httpcallback, (str, unicode)) and httpcallback.find('http://') == 0:
        nsize = daobase.executeMixCmd('HLEN', 'global.orderid.callback')
        if nsize > 10000:
            daobase.executeMixCmd('DEL', 'global.orderid.callback')
            ftlog.error('the test order "global.orderid.callback" too much (> 10000) !! ' +
                        'auto clean up !! some test order maybe callback to online !' +
                        'this is not an error, just a warring !!')
        return httpcallback
    return gdata.httpSdkInner()


def is_short_order_id_format(shortOrderId):
    if isinstance(shortOrderId, int):
        if len(str(shortOrderId)) == 6:
            return True
    elif isinstance(shortOrderId, (str, unicode)):
        if len(shortOrderId) == 6:
            try:
                shortOrderId = int(shortOrderId)
                return True
            except:
                pass
    return False


def get_short_order_id(orderPlatformId):
    if gdata.mode() == gdata.RUN_MODE_ONLINE:
        # 若是线上正式服, 那么再mix库中生成短单号
        shortOrderId = daobase.executeMixCmd('INCR', 'global.orderid.seq.sort')
        shortOrderId = str(100000 + shortOrderId)[-6:]
        daobase.executeMixCmd('HSET', 'sort.orderid.map', shortOrderId, orderPlatformId)
        return shortOrderId
    else:
        # 若是测试服务, 那么调用正式服远程API生成单号
        httpurl = gdata.httpOnlieGateWay() + '/_testorder_get_short_id'
        datas = {
            'orderPlatformId': orderPlatformId
        }
        result, _ = webpage.webgetJson(httpurl, datas, None, 10)
        return result['sortOrderPlatformId']


def get_long_order_id(shortOrderId):
    if not is_short_order_id_format(shortOrderId):
        return shortOrderId

    if gdata.mode() == gdata.RUN_MODE_ONLINE:
        # 若是线上正式服, 那么重mix库中取得长单号
        orderPlatformId = daobase.executeMixCmd('HGET', 'sort.orderid.map', shortOrderId)
        return str(orderPlatformId)
    else:
        # 若是测试服务, 那么调用正式服远程API取得长单号
        httpurl = gdata.httpOnlieGateWay() + '/_testorder_get_long_id'
        datas = {
            'sortOrderPlatformId': shortOrderId
        }
        result, _ = webpage.webgetJson(httpurl, datas, None, 10)
        return result['orderPlatformId']
