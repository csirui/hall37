# -*- coding=utf-8
'''
Created on 2015年8月17日

@author: zhaojiangang
'''
import json

import freetime.util.log as ftlog
import poker.entity.biz.message.message as pkmessage
import poker.util.timestamp as pktimestamp
from hall.entity import hallconf, datachangenotify
from hall.entity import hallitem
from hall.entity.hallconf import HALL_GAMEID
from hall.entity.hallitem import TYExchangeItem
from poker.entity.biz.exceptions import TYBizException
from poker.entity.dao import paydata, exchangedata


class TYExchangeRecord(object):
    STATE_NORMAL = 0
    STATE_AUDIT = 1
    STATE_ACCEPT = 2
    STATE_REJECT = 3

    def __init__(self, exchangeId):
        self.exchangeId = exchangeId
        self.itemId = None
        self.itemKindId = None
        self.createTime = None
        self.state = TYExchangeRecord.STATE_NORMAL
        self.params = None

    def toDict(self):
        return {
            'st': self.state,
            'itemId': self.itemId,
            'itemKindId': self.itemKindId,
            'ct': self.createTime,
            'params': self.params
        }

    def fromDict(self, d):
        self.state = d['st']
        self.itemId = d['itemId']
        self.itemKindId = d['itemKindId']
        self.createTime = d['ct']
        self.params = d['params']
        return self


def _makeExchangeId():
    return paydata.makeExchangeId()


def _buildExchangeKey(userId):
    return 'eo:9999:%s' % (userId)


def _saveRecordData(userId, exchangeId, recordData):
    return exchangedata.setExchangeData(userId, HALL_GAMEID, exchangeId, recordData)


def _loadRecordData(userId, exchangeId):
    return exchangedata.getExchangeData(userId, HALL_GAMEID, exchangeId)


def _loadRecordDatas(userId):
    return exchangedata.getExchangeDataAll(userId, HALL_GAMEID)


RESULT_OK = 0
RESULT_REJECT = 1
RESULT_REJECT_RETURN = 2


def loadRecord(userId, exchangeId):
    data = _loadRecordData(userId, exchangeId)
    if data:
        d = json.loads(data)
        record = TYExchangeRecord(exchangeId)
        record.fromDict(d)
        return record
    else:
        return None


def getExchangeRecords(userId):
    '''
    获取用户兑换记录
    '''
    ret = []
    datas = _loadRecordDatas(userId)
    if not datas:
        return ret

    for i in xrange(len(datas) / 2):
        try:
            jstr = datas[i * 2 + 1]
            d = json.loads(jstr)
            record = TYExchangeRecord(datas[i * 2])
            record.fromDict(d)
            ret.append(record)
        except:
            ftlog.error()
    return ret


def requestExchange(userId, item, params, timestamp):
    assert (isinstance(item, TYExchangeItem))
    exchangeId = _makeExchangeId()
    record = TYExchangeRecord(exchangeId)
    record.itemId = item.itemId
    record.itemKindId = item.kindId
    record.createTime = timestamp
    record.params = params
    record.errorCode = 0
    record.state = TYExchangeRecord.STATE_AUDIT
    jstr = json.dumps(record.toDict())
    _saveRecordData(userId, exchangeId, jstr)

    parasDict = {}
    parasDict["user_id"] = userId
    parasDict["exchange_id"] = exchangeId
    parasDict["prod_id"] = item.itemId
    parasDict["prod_kind_name"] = item.itemKind.displayName
    parasDict["prod_num"] = 1
    parasDict["exchange_type"] = params.get("type", 0)
    parasDict["exchange_amount"] = params.get("count", 0)
    parasDict["exchange_desc"] = params.get("desc", "")
    parasDict["user_phone"] = params.get("phone", "")
    parasDict["user_name"] = params.get("uName", "")
    parasDict["user_addres"] = params.get("uAddres", "")
    gdssUrl = hallconf.getItemConf().get("exchangeGdssUrl",
                                         "http://gdss.touch4.me/?act=api.propExchange")
    from poker.util import webpage
    try:
        hbody, _ = webpage.webgetGdss(gdssUrl, parasDict)
        resJson = json.loads(hbody)
    except:
        ftlog.exception()
        raise TYExchangeRequestError()
    retcode = resJson.get("retcode", -1)
    retmsg = resJson.get("retmsg", '兑换请求出错')
    if retcode != 1:
        raise TYExchangeRequestError(retmsg)

    ftlog.debug("requestExchange userId=", userId, "exchangeId=", exchangeId, "kindId=", item.kindId)
    return record


class TYExchangeRequestError(TYBizException):
    def __init__(self, message='兑换请求出错'):
        super(TYExchangeRequestError, self).__init__(-1, message)


class TYUnknownExchangeOrder(TYBizException):
    def __init__(self, message='未知的订单'):
        super(TYUnknownExchangeOrder, self).__init__(-1, message)


class TYBadStateExchangeOrder(TYBizException):
    def __init__(self, message='错误的订单状态'):
        super(TYBadStateExchangeOrder, self).__init__(-1, message)


def handleExchangeAuditResult(userId, exchangeId, result):
    '''
    处理审核结果
    '''
    record = loadRecord(userId, exchangeId)
    if not record:
        raise TYUnknownExchangeOrder()

    if record.state != TYExchangeRecord.STATE_AUDIT:
        raise TYBadStateExchangeOrder()

    userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
    item = userBag.findItem(record.itemId)

    if not isinstance(item, TYExchangeItem):
        raise TYBizException(-1, '系统错误')

    if item.state != TYExchangeItem.STATE_AUDIT:
        raise TYBizException(-1, '道具状态错误')

    ftlog.debug('hallexchange.handleExchangeAuditResult userId=', userId,
                'exchangeId=', exchangeId,
                'result=', result)

    timestamp = pktimestamp.getCurrentTimestamp()
    if result == RESULT_OK:
        record.state = TYExchangeRecord.STATE_ACCEPT
        userBag.removeItem(HALL_GAMEID, item, timestamp, 'EXCHANGE', item.kindId)
    else:
        record.state = TYExchangeRecord.STATE_REJECT
        if result == RESULT_REJECT_RETURN:
            item.state = TYExchangeItem.STATE_NORMAL
            userBag.updateItem(HALL_GAMEID, item, timestamp)
        else:
            userBag.removeItem(HALL_GAMEID, item, timestamp, 'EXCHANGE', item.kindId)
    itemDisPlayName = item.itemKind.displayName
    exchangeDesc = record.params.get("desc", '')
    if result == RESULT_OK:
        mail = "您申请用%s兑换(领取)%s，已成功为您办理，请查收。" % (itemDisPlayName, exchangeDesc)
    else:
        mail = "您申请用%s兑换(领取)%s，审核未通过，抱歉。" % (itemDisPlayName, exchangeDesc)
    ftlog.debug("handleExchangeAuditResult,mail:", mail)
    pkmessage.send(HALL_GAMEID, pkmessage.MESSAGE_TYPE_SYSTEM, userId, mail)
    datachangenotify.sendDataChangeNotify(HALL_GAMEID, userId, 'message')

    jstr = json.dumps(record.toDict())
    _saveRecordData(userId, exchangeId, jstr)
    return record
