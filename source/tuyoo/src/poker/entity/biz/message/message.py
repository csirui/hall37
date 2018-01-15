# -*- coding: utf-8 -*-
"""
站内消息,类似邮箱功能,可以带附件
"""

from sre_compile import isstring

import freetime.util.log as ftlog
import poker.entity.events.tyeventbus as pkeventbus
from poker.entity.biz.content import TYContentItem
from poker.entity.dao import daobase
from poker.entity.dao import gamedata
from poker.entity.events.tyevent import ModuleTipEvent
from poker.util import timestamp, strutil

MAX_SIZE = 50

MESSAGE_TYPE_PRIVATE = 1  # 游戏记录
MESSAGE_TYPE_SYSTEM = 2  # 系统通知
MESSAGE_TYPES = {
    MESSAGE_TYPE_PRIVATE: 'msg.id.private',
    MESSAGE_TYPE_SYSTEM: 'msg.id.system',
}

HALL_GAMEID = 9999
REDIS_KEY = 'message_{}:{}:{}'


# =====================
# class
# =====================

class Attachment(object):
    """
    附件基类
    """
    TYPE_ID = 'unkown'
    ORDER_KEY = 99999

    def marshal(self):
        """
        对象序列化为字典
        @return: dict
        """
        raise NotImplementedError

    def unmarshal(self, d):
        """
        字典反序列化为对象
        @param d:
        @return:
        """
        raise NotImplementedError


class AttachmentAsset(Attachment):
    """
    附件:物品或者货币
    """
    TYPE_ID = 'asset'
    ORDER_KEY = 1

    def __init__(self, content_item_list=None, eventid=None, eventparam=None):
        """
        @param content_item_list: list<poker.entity.biz.content.TYContentItem>,可以是物品或者货币
        @param eventid: 起因,来历
        @param eventparam: eventid需要的参数
        """
        self._itemlist = content_item_list
        self._eventid = eventid
        self._eventparam = eventparam

    @property
    def itemlist(self):
        return self._itemlist

    @property
    def eventid(self):
        return self._eventid

    @property
    def eventparam(self):
        return self._eventparam

    def marshal(self):
        ret = {'typeid': self.TYPE_ID}
        assets = []  # 不直接用字典,考虑到顺序或许有用
        for content_item in self._itemlist:
            if not isinstance(content_item, TYContentItem):
                raise Exception("AttachmentAsset.marshal _itemlist wrong type:{}".format(self._itemlist))
            assets.append(content_item.toDict())
        ret['assets'] = assets

        if not isstring(self._eventid):
            raise Exception("AttachmentAsset.marshal _eventid wrong type:{}".format(self._eventid))
        ret['eventid'] = self._eventid

        if not isinstance(self._eventparam, int):
            raise Exception("AttachmentAsset.marshal _eventparam wrong type:{}".format(self._eventparam))
        ret['eventparam'] = self._eventparam
        return ret

    def unmarshal(self, d):
        assets = d.get('assets')  # 格式必须是：[{'itemId':'item:0011', 'count':1}, ...]
        if not isinstance(assets, list):
            raise Exception("AttachmentAsset.unmarshal assets wrong:{}".format(assets))
        self._itemlist = []
        for kind_2_cnt in assets:
            d_item = {'itemId': kind_2_cnt['itemId'],
                      'count': int(kind_2_cnt['count'])}
            self._itemlist.append(TYContentItem.decodeFromDict(d_item))

        self._eventid = d.get('eventid')
        if not isstring(self._eventid):
            raise Exception("AttachmentAsset.unmarshal eventid wrong:{}".format(self._eventid))

        self._eventparam = d.get('eventparam')
        if not isinstance(self._eventparam, int):
            raise Exception("AttachmentAsset.unmarshal eventparam wrong:{}".format(self._eventparam))


class AttachmentTodoTask(Attachment):
    """
    附件:跳转链接
    """
    TYPE_ID = 'todotask'
    ORDER_KEY = 2

    def __init__(self, todo_task, duration=0):
        """
        @param duration: 展示时间(分钟),<=0表示永久
        @param todo_task: hall.entity.TodoTask
        """
        self._expire = (timestamp.getCurrentTimestamp() + duration * 60) if duration > 0 else 0
        self._todo_task = todo_task

    def marshal(self):
        ret = {'typeid': self.TYPE_ID, 'expire': self._expire}
        todo_str = self._todo_task.toDict()
        ret['todotask'] = todo_str
        return ret


MESSAGE_ATTACHMENT_CLASS = {
    AttachmentAsset.TYPE_ID: AttachmentAsset,
    AttachmentTodoTask.TYPE_ID: AttachmentTodoTask,
}


# =====================
# function
# =====================

def send(gameid, typeid, touid, text, fromuid=None, attachment=None):
    """
    发送消息给指定用户
    @param gameid: 哪个游戏发的
    @param typeid: 类型, L{message.MESSAGE_TYPES}
    @param touid: 接收用户id
    @param text: 消息文本
    @param fromuid: 发送用户id, 默认系统
    @param attachment: 消息附件, 默认没有
    @return:
    """
    if typeid not in MESSAGE_TYPES:
        raise Exception("message.send, unkown type:{}".format(typeid))
    ct = timestamp.formatTimeSecond()
    msg = {'gameid': gameid, 'time': ct, 'text': text}
    if fromuid:
        msg['from'] = fromuid
    if attachment:
        if not isinstance(attachment, Attachment):
            raise Exception("message.send, unkown attachment!!")
        msg['attachment'] = attachment.marshal()

    rediskey = REDIS_KEY.format(typeid, HALL_GAMEID, touid)
    msglist = _msg_load_and_expire(touid, rediskey)
    if len(msglist) >= MAX_SIZE:  # 超50条删除
        lastmsgval = None
        for msgval in msglist:
            if lastmsgval:
                if _msg_order(lastmsgval) > _msg_order(msgval):
                    continue
            lastmsgval = msgval
        if lastmsgval:
            daobase.executeUserCmd(touid, 'HDEL', rediskey, lastmsgval['id'])

    maxid = gamedata.incrGameAttr(touid, HALL_GAMEID, 'msg.id.max', 1)
    daobase.executeUserCmd(touid, 'HSET', rediskey, maxid, strutil.dumps(msg))
    tip = ModuleTipEvent(touid, HALL_GAMEID, "message", 1)
    pkeventbus.globalEventBus.publishEvent(tip)
    return maxid


def _msg_order(msg):
    attach = msg.get('attachment')
    if not attach:
        order_pri = Attachment.ORDER_KEY
    else:
        typeid = attach['typeid']
        order_pri = MESSAGE_ATTACHMENT_CLASS[typeid].ORDER_KEY
    return order_pri, -msg['id']


def get(userid, typeid):
    """
    获取消息列表
    @param userid:
    @param typeid: 类型, L{message.MESSAGE_TYPES}
    @return:
    """
    if typeid not in MESSAGE_TYPES:
        raise Exception("message.get, unkown type:{}".format(typeid))
    rediskey = REDIS_KEY.format(typeid, HALL_GAMEID, userid)
    msglist = _msg_load_and_expire(userid, rediskey)
    msglist.sort(key=_msg_order)

    readkey = MESSAGE_TYPES[typeid]
    maxid, readid = gamedata.getGameAttrs(userid, HALL_GAMEID, ['msg.id.max', readkey])
    maxid, readid = strutil.parseInts(maxid, readid)
    if maxid > readid:
        gamedata.setGameAttr(userid, HALL_GAMEID, readkey, maxid)
    return {'readid': readid, 'list': msglist}


def _msg_load_and_expire(userid, rediskey):
    key_vals = daobase.executeUserCmd(userid, 'HGETALL', rediskey)
    now = timestamp.getCurrentTimestamp()
    msglist = []
    for i in xrange(0, len(key_vals), 2):
        msg = strutil.loads(key_vals[i + 1])
        attach = msg.get('attachment')
        if attach and attach.get('typeid') == AttachmentTodoTask.TYPE_ID:
            expire = attach.get('expire')
            if 0 < expire <= now:
                daobase.executeUserCmd(userid, 'HDEL', rediskey, key_vals[i])
                continue
        msg['id'] = key_vals[i]
        if 'from' not in msg:
            msg['from'] = 'System'
        msglist.append(msg)
    return msglist


def get_unread_count(userid, typeid):
    """
    取得当前用户的未读站内消息的个数
    """
    readkey = MESSAGE_TYPES[typeid]
    maxid, readid = gamedata.getGameAttrs(userid, HALL_GAMEID, ['msg.id.max', readkey])
    maxid, readid = strutil.parseInts(maxid, readid)
    return maxid - readid


def attachment_receive(userid, typeid, msgid, itemsystem):
    """
    收取附件的物品或者货币
    @param itemsystem: poker.entity.biz.item.TYItemSystem
    @param typeid: 类型, L{message.MESSAGE_TYPES}
    @param userid:
    @param msgid: 消息id
    @return:
    """
    rediskey = REDIS_KEY.format(typeid, HALL_GAMEID, userid)
    data = daobase.executeUserCmd(userid, 'HGET', rediskey, msgid)
    if not data:
        ftlog.debug('message.attachment_receive msg not exsit,uid=', userid, 'tid=', typeid, 'msgid=', msgid)
        return

    msg = strutil.loads(data)
    attach = msg.get('attachment')
    if not attach or attach.get('typeid') != AttachmentAsset.TYPE_ID:
        ftlog.debug('message.attachment_receive no asset,uid=', userid, 'tid=', typeid, 'msgid=', msgid)
        return

    daobase.executeUserCmd(userid, 'HDEL', rediskey, msgid)
    asset = AttachmentAsset()
    asset.unmarshal(attach)
    ua = itemsystem.loadUserAssets(userid)
    gameid = msg.get('gameid')
    return gameid, ua.sendContentItemList(gameid, asset.itemlist, 1, True, timestamp.getCurrentTimestamp(),
                                          asset.eventid, asset.eventparam)


# def sendPrivate(gameId, toUid, fromUid, msg, button=None):
#     '''
#     发送站内消息到用户
#     '''
#     maxid = gamedata.incrGameAttr(toUid, gameId, 'msg.id.max', 1)
#     ct = timestamp.formatTimeSecond()
#     msg = {'id':maxid, 'from':fromUid, 'time':ct, 'msg':msg}
#     daobase.executeUserCmd(toUid, 'LPUSH', 'msg:' + str(gameId) + ':' + str(toUid), strutil.dumps(msg))
#     tip = ModuleTipEvent(toUid, gameId, "message", 1)
#     pkeventbus.globalEventBus.publishEvent(tip)
#     return 1
def convertOldData(gameId, userId):
    """
    大厅v3.9存储改动,user数据库:
    键message:g(gameid)u(userid),废弃
    键msg:(gameId):(toUid),废弃
    """
    oldkey = 'message:g{}u{}'.format(gameId, userId)
    daobase.executeUserCmd(userId, 'DEL', oldkey)

    # from datetime import datetime
    # sendPrivate(9999, 10004, 0, 'oldmsg test now:{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')))
    hall37key = 'msg:{}:{}'.format(gameId, userId)
    rediskey = REDIS_KEY.format(MESSAGE_TYPE_PRIVATE, HALL_GAMEID, userId)
    new_msg_len = daobase.executeUserCmd(userId, 'HLEN', rediskey)  # 限制50条
    datas = daobase.executeUserCmd(userId, 'LRANGE', hall37key, 0, MAX_SIZE - new_msg_len - 1)
    if datas:
        for msgstr in datas:
            msg = strutil.loads(msgstr, ignoreException=True)
            if msg:
                new_msg = {'gameid': gameId, 'time': msg['time'], 'text': msg['msg']}
                if msg['from'] > 0:
                    new_msg['from'] = msg['from']
                maxid = gamedata.incrGameAttr(userId, HALL_GAMEID, 'msg.id.max', 1)
                daobase.executeUserCmd(userId, 'HSET', rediskey, maxid, strutil.dumps(new_msg))
    daobase.executeUserCmd(userId, 'DEL', hall37key)


# =====================
# deprecated
# =====================

def sendPrivate(gameId, toUid, fromUid, msg, button=None):
    """
    已废弃,留着只为了兼容以前代码
    发送站内消息到用户
    """
    send(gameId, MESSAGE_TYPE_PRIVATE, toUid, msg, fromUid)
    return 1


def getPrivate(gameId, userId, pageNo=1):
    """
    已废弃,留着只为了兼容以前代码
    取得当前用户的未读私信的内容
    """
    return get(userId, MESSAGE_TYPE_PRIVATE)


def getPrivateUnReadCount(gameId, userId):
    """
    已废弃,留着只为了兼容以前代码
    取得当前用户的未读站内消息的个数
    """
    return get_unread_count(userId, MESSAGE_TYPE_PRIVATE)


def sendGlobal(gameId, msg, button=None):
    """
    已废弃,待删除
    发送站内消息到全体游戏用户
    """
    maxid = daobase.executeMixCmd('HINCRBY', 'msg', 'msg.id.max.' + str(gameId))
    ct = timestamp.formatTimeSecond()
    msg = {'id': maxid, 'from': 0, 'time': ct, 'msg': msg}
    daobase.executeMixCmd('LPUSH', 'msg:' + str(gameId), strutil.dumps(msg))
    return 1


def getGlobalUnReadCount(gameId, userId):
    """
    已废弃,待删除
    取得当前用户的未读站内消息的个数
    """
    maxglobalid = daobase.executeMixCmd('HGET', 'msg', 'msg.id.max.' + str(gameId))
    globalid = gamedata.getGameAttr(userId, gameId, 'msg.id.global')
    maxglobalid, globalid = strutil.parseInts(maxglobalid, globalid)
    return maxglobalid - globalid


def getGlobal(gameId, userId, pageNo=1):
    """
    已废弃,待删除
    取得当前用户的全局未读私信的内容
    """
    maxMsgId = daobase.executeMixCmd('HGET', 'msg', 'msg.id.max.' + str(gameId))
    readMaxId = gamedata.getGameAttrs(userId, gameId, 'msg.id.global')
    rediskey = 'msg:' + str(gameId)

    maxMsgId, readMaxId = strutil.parseInts(maxMsgId, readMaxId)
    msglist = []
    maxId = readMaxId
    if pageNo < 1:
        pageNo = 1
    lstart = (pageNo - 1) * 20
    lend = lstart + 20 - 1
    datas = daobase.executeMixCmd('LRANGE', rediskey, lstart, lend)
    count = 0
    if datas:
        for msgstr in datas:
            msg = strutil.loads(msgstr, ignoreException=True)
            if msg:
                maxId = max(maxId, msg['id'])
                msglist.append(msg)
                count += 1
    if maxId > readMaxId:
        gamedata.setGameAttr(userId, gameId, 'msg.id.global', maxId)
    return {'count': count, 'maxId': maxMsgId, 'readId': readMaxId, 'pageNo': pageNo, 'list': msglist}
