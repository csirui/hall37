# -*- coding=utf-8 -*-
'''
Created on 2015年10月17日

@author: liaoxx
'''
import functools

from difang.majiang2.entity import majiang_conf
from freetime.util import log as ftlog
from hall.entity import hallshare, hallled
from hall.entity.hallconf import HALL_GAMEID
from hall.entity.todotask import TodoTaskHelper, TodoTaskShowInfo, TodoTaskPopTip
from poker.entity.biz.message import message
from poker.entity.dao import sessiondata
from poker.protocol import router
from poker.util import strutil


class Util(object):
    @classmethod
    def dict2list(cls, d):
        l = []
        if isinstance(d, dict):
            for k, v in d.iteritems():
                l.append(k)
                l.append(v)
        return l

    @classmethod
    def list2dict(cls, l):
        d = {}
        if isinstance(l, list):
            length = len(l)
            while length > 1:
                d[l[length - 2]] = l[length - 1]
                length -= 2
        return d

    @classmethod
    def list_merge(cls, l1, l2):
        l = []
        for i, j in zip(l1, l2):
            l.append(i)
            l.append(j)
        return l

    @classmethod
    def check_msg_result(cls, msg):
        if not msg._ht.has_key('result'):
            msg._ht['result'] = {}

    @classmethod
    def sendShowInfoTodoTask(cls, uid, gid, msg):
        info = TodoTaskShowInfo(msg, True)
        TodoTaskHelper.sendTodoTask(gid, uid, info)

    @classmethod
    def getClientVerAndDeviceType(cls, clientId):
        infos = clientId.split('_')
        if len(infos) > 2:
            try:
                clientVer = float(infos[1])
                deviceType = infos[0].lower()
                return clientVer, deviceType
            except:
                pass
        return 0, ''

    @classmethod
    def getClientId(self, uid):
        if uid < 10000:
            clientId = "IOS_3.711_tyGuest.appStore.0-hall7.test.kuaile"
        else:
            clientId = sessiondata.getClientId(uid)
        return clientId

    @classmethod
    def getClientIdVer(self, uid):
        if uid < 10000:
            clientId = 3.7
        else:
            clientId = sessiondata.getClientIdVer(uid)
        return clientId

    @classmethod
    def list_diff(cls, short_list, long_list):
        '''获取list差集
        '''
        l_list = strutil.cloneData(long_list)
        for l in short_list:
            if l in l_list:
                l_list.remove(l)
        return l_list

    @classmethod
    def list_intersection(cls, a_list, b_list):
        '''获取list交集
        '''
        return [v for v in a_list if v in b_list]

    @classmethod
    def list_union(cls, a_list, b_list):
        '''不去重复元素的list并集
        '''
        return a_list + [v for v in b_list if v not in a_list]


def sendPrivateMessage(userId, msg):
    """ 发送个人消息
    """
    if not isinstance(msg, unicode):
        msg = unicode(msg)
    message.sendPrivate(9999, userId, 0, msg)


def safemethod(method):
    """ 方法装饰，被装饰函数不会将异常继续抛出去
    """

    @functools.wraps(method)
    def safetyCall(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except:
            ftlog.exception()

    return safetyCall


def sendPopTipMsg(userId, msg):
    task = TodoTaskPopTip(msg)
    task.setParam('duration', 3)
    mo = TodoTaskHelper.makeTodoTaskMsg(HALL_GAMEID, userId, task)
    router.sendToUser(mo, userId)


def sendTableInviteShareTodoTask(userId, gameId, tableNo, playMode, cardCount, contentStr):
    '''牌桌上邀请处理
    '''
    shareId = hallshare.getShareId('mj_invite_play_share', userId, gameId)
    if shareId:
        share = hallshare.findShare(shareId)
        if not share:
            return

        retDesc = ''
        play_mode_dict = majiang_conf.get_room_other_config(gameId).get('playmode_desc_map', {})
        retDesc += play_mode_dict.get(playMode, '') if playMode else ''
        retDesc += contentStr
        ftlog.debug('sendTableInviteShareTodoTask last retDesc:', retDesc)
        share.setDesc(retDesc)

        title = share.title.getValue(userId, gameId)
        title = '房间号：' + tableNo + '，' + title
        share.setTitle(title)

        todotask = share.buildTodotask(gameId, userId, 'mj_invite_play_share')
        mo = TodoTaskHelper.makeTodoTaskMsg(gameId, userId, todotask)
        router.sendToUser(mo, userId)


def send_led(cls, gameId, msg):
    '''系统led'''
    hallled.sendLed(gameId, msg, 0)
