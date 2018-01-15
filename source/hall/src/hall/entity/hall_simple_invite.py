# -*- coding=utf-8 -*-
'''
Created on 2016年12月1日

一个简单的邀请有礼模块
邀请功能在内推广模块上做了一定的简化
1）配置基于主次渠道
2）设计上，不防刷，只要用户的游戏行为符合条件即可领取
3）不要求绑定手机号
4）界面也相对简单
5）奖励不是大厅统一发，奖励配置设置在游戏中

@author: zhaol
'''

import json
from sre_compile import isstring

import freetime.util.log as ftlog
import poker.entity.events.tyeventbus as pkeventbus
import poker.util.timestamp as pktimestamp
from hall.entity import hallconf
from hall.entity.hallconf import HALL_GAMEID
from poker.entity.biz.content import TYContentItem
from poker.entity.biz.exceptions import TYBizException, TYBizBadDataException, \
    TYBizConfException
from poker.entity.configure import pokerconf, gdata
from poker.entity.dao import gamedata, userdata
from poker.entity.events.tyevent import EventConfigure
from poker.entity.game.game import TYGame

MAX_INVITEE = 500


class Invitation(object):
    '''
    邀请
    '''
    # 初始条件，未领取奖励
    STATE_NORMAL = 0
    # 可以领取奖励
    STATE_CAN_GET_REWARD = 1
    # 已领取奖励
    STATE_REWARDED = 2

    def __init__(self, userId, index, inviterState=STATE_NORMAL):
        # 用户ID
        self.__userId = userId
        # 排序位置
        self.__index = index
        # 推荐人是否领奖状态(根据被推荐人的状态决定)
        self.__inviterState = inviterState

    @property
    def userId(self):
        return self.__userId

    @property
    def index(self):
        return self.__index

    @property
    def inviterState(self):
        return self.__inviterState

    @inviterState.setter
    def inviterState(self, value):
        assert (isinstance(value, int))
        self.__inviterState = value

    def getInviterState(self, userId, clientId):
        if getGameCount(userId, clientId) > 0 and self.__inviterState == self.STATE_NORMAL:
            return self.STATE_CAN_GET_REWARD
        return self.__inviterState


class NeituiguangSimpleStatus(object):
    OLD_KEY = 'neituiguang'
    NEW_KEY = 'neituiguang_simple'
    INVITER = 'inviter'
    INVITEES = 'invitees'
    REWARD_STATE = 'rewardState'

    def __init__(self, userId, timestamp):
        self.__userId = userId
        # 当前时间
        self.__timestamp = timestamp
        # 推荐人，上线
        self.__inviter = 0
        # 下线集合，被推荐人map，key=userId, value=InvitationUser
        self.__inviteeMap = {}
        # 绑定上线奖励的状态
        self.__rewardState = Invitation.STATE_NORMAL

    @property
    def userId(self):
        return self.__userId

    @property
    def timestamp(self):
        return self.__timestamp

    @property
    def inviter(self):
        return self.__inviter

    @property
    def inviteeCount(self):
        return len(self.__inviteeMap)

    @property
    def inviteeMap(self):
        return self.__inviteeMap

    def findInvitee(self, userId):
        return self.__inviteeMap.get(userId, None)

    @property
    def rewardState(self):
        return self.__rewardState

    def getRewardState(self, userId, gameId, clientId):
        """返回是否可领奖的状态"""
        if (self.__rewardState == Invitation.STATE_NORMAL) and \
                        getGameCount(userId, clientId) > 0:
            return Invitation.STATE_CAN_GET_REWARD
        return self.rewardState

    def setRewardState(self, state):
        self.__rewardState = state

    def setInviter(self, userId):
        self.__inviter = userId

    def addInvitee(self, userId, inviteeState):
        invitee = Invitation(userId, len(self.__inviteeMap), inviteeState)
        self.__inviteeMap[userId] = invitee

    def decodeFromDict(self, d):
        self.__inviter = d.get(self.INVITER, 0)
        inviteeList = d.get(self.INVITEES, [])
        if not isinstance(inviteeList, list):
            raise TYBizBadDataException('InviteStatus.invitees must be list')
        for i, invitee in enumerate(inviteeList):
            invitation = Invitation(invitee['uid'], i, invitee['st'])
            self.__inviteeMap[invitation.userId] = invitation
        rewardState = d.get(self.REWARD_STATE, Invitation.STATE_NORMAL)
        self.__rewardState = rewardState
        return self

    def encodeToDict(self, d):
        d[self.INVITER] = self.inviter
        if self.__inviteeMap:
            sl = sorted(self.__inviteeMap.values(), key=lambda invitee: invitee.index)
            d[self.INVITEES] = [{'uid': invitee.userId, 'st': invitee.inviterState} for invitee in sl]
        d[self.REWARD_STATE] = self.__rewardState
        return d


class InviteException(TYBizException):
    def __init__(self, ec, message):
        super(InviteException, self).__init__(ec, message)


class BadStateException(InviteException):
    def __init__(self, message):
        super(BadStateException, self).__init__(1, message)


class BadInviterException(InviteException):
    def __init__(self, message):
        super(BadInviterException, self).__init__(2, message)


class AlreadyInviteException(InviteException):
    def __init__(self):
        super(AlreadyInviteException, self).__init__(3, '已经推荐了该用户')


class FullInviteException(InviteException):
    def __init__(self):
        super(AlreadyInviteException, self).__init__(4, '推荐用户达到上限')


def loadStatus(userId, timestamp):
    '''
    加载用户推广状态
    麻将先于大厅做过邀请有礼，从麻将merge数据
    '''
    d = None
    status = None
    try:
        # 优先迁移跑胡子的配置
        ftlog.debug('hall_simple_invite.loadStatus try load from paohuzi...')
        d = gamedata.getGameAttrJson(userId, 21, NeituiguangSimpleStatus.OLD_KEY)
        gamedata.delGameAttr(userId, 21, NeituiguangSimpleStatus.OLD_KEY)
        if not d:
            # 其次迁移麻将的配置
            ftlog.debug('hall_simple_invite.loadStatus try load from majiang...')
            d = gamedata.getGameAttrJson(userId, 7, NeituiguangSimpleStatus.OLD_KEY)
            gamedata.delGameAttr(userId, 7, NeituiguangSimpleStatus.OLD_KEY)

        if not d:
            # 使用大厅数据
            ftlog.debug('hall_simple_invite.loadStatus try load from hall at last...')
            d = gamedata.getGameAttrJson(userId, HALL_GAMEID, NeituiguangSimpleStatus.NEW_KEY)

        ftlog.debug('hall_simple_invite.loadStatus status:', d)
        if d:
            status = NeituiguangSimpleStatus(userId, timestamp).decodeFromDict(d)
    except:
        ftlog.error('invite.loadStatus userId=', userId, 'd=', d)

    if not status:
        status = NeituiguangSimpleStatus(userId, timestamp)

    return status


def saveStatus(status):
    d = status.encodeToDict({})
    jstr = json.dumps(d)
    gamedata.setGameAttr(status.userId, HALL_GAMEID, NeituiguangSimpleStatus.NEW_KEY, jstr)


def ensureCanAddInviter(status, inviter):
    '''
    检查用户是否可以成为被推荐人
    '''
    if not userdata.checkUserData(inviter):
        raise BadInviterException('推荐人不存在')

    if status.inviter:
        raise BadStateException('已经填写了推荐人')

    if status.userId == inviter:
        raise BadInviterException('不能推荐自己')

    return True


def ensureCanBeInviter(status, invitee):
    if not userdata.checkUserData(invitee):
        raise BadInviterException('您的账号信息有误')

    if status.userId == invitee:
        raise BadInviterException('不能推荐自己')

    if status.findInvitee(invitee):
        raise BadInviterException('已推荐此用户')

    if status.inviteeCount + 1 > MAX_INVITEE:
        ftlog.info('invite.addInvitee overCountLimit userId=', status.userId,
                   'invitee=', invitee,
                   'inviteeCount=', status.inviteeCount,
                   'MAX_INVITEE=', MAX_INVITEE)
        raise FullInviteException()


def bindSimpleInviteRelationShip(inviter, invitee):
    '''
    设置invitee的inviter
    
    @param inviter: 上线
    @param invitee: 下线
    @return: status
    '''
    timestamp = pktimestamp.getCurrentTimestamp()
    inviteeStatus = loadStatus(invitee, timestamp)
    inviterStatus = loadStatus(inviter, timestamp)

    ensureCanAddInviter(inviteeStatus, inviter)
    ensureCanBeInviter(inviterStatus, invitee)

    inviteeStatus.setInviter(inviter)
    saveStatus(inviteeStatus)

    inviterStatus.addInvitee(invitee, inviteeStatus.rewardState)
    saveStatus(inviterStatus)


class InviteConf(object):
    def __init__(self):
        self.inviteRewardItem = None
        self.gotoTitle = None
        self.gotoDesc = None
        self.gotoUrl = None
        self.inviteTitle = None
        self.inviteDesc = None
        self.inviteUrl = None
        self.name = None

    def decodeFromDict(self, d):
        inviteRewardItem = d.get('inviteRewardItem', {})
        if not isinstance(inviteRewardItem, dict):
            raise TYBizConfException(d, 'InviteConf.inviteRewardItem must be dict')
        if inviteRewardItem:
            self.inviteRewardItem = TYContentItem.decodeFromDict(inviteRewardItem)

        self.gotoTitle = d.get('gotoTitle', '')
        if not isstring(self.gotoTitle):
            raise TYBizConfException(d, 'InviteConf.gotoTitle must be string')

        self.gotoDesc = ''
        if not isstring(self.gotoDesc):
            raise TYBizConfException(d, 'InviteConf.gotoDesc must be string')

        self.gotoUrl = d.get('gotoUrl', '')
        if not isstring(self.gotoUrl):
            raise TYBizConfException(d, 'InviteConf.gotoUrl must be string')

        self.inviteTitle = d.get('inviteTitle', '')
        if not isstring(self.inviteTitle):
            raise TYBizConfException(d, 'InviteConf.inviteTitle must be string')

        self.inviteDesc = d.get('inviteDesc', '')
        if not isstring(self.inviteDesc):
            raise TYBizConfException(d, 'InviteConf.inviteDesc must be string')

        self.inviteUrl = d.get('inviteUrl', '')
        if not isstring(self.inviteUrl):
            raise TYBizConfException(d, 'InviteConf.inviteUrl must be string')

        self.name = d.get('name', '')
        if not isstring(self.name):
            raise TYBizConfException(d, 'InviteConf.name must be string')

        return self


_inited = False
_conf = None


def _reloadConf():
    global _conf
    confMap = {}
    confs = hallconf.getAllTcDatas('simple_invite')
    ftlog.debug('hall_simple_invite confs:', confs)
    for templateDict in confs.get('templates'):
        template = InviteConf().decodeFromDict(templateDict)
        if template.name in confMap:
            raise TYBizConfException(templateDict, 'Duplicate simple_invite %s' % (template.name))
        confMap[template.name] = template
    _conf = confMap
    ftlog.info('hall_simple_invite._reloadConf conf=', _conf)


def _onConfChanged(event):
    if _inited and event.isModuleChanged(['simple_invite']):
        ftlog.info('hall_simple_invite._onConfChanged')
        _reloadConf()


def initialize():
    ftlog.info('hall_simple_invite initialize begin')
    global _inited
    if not _inited:
        _inited = True
        _reloadConf()
        pkeventbus.globalEventBus.subscribe(EventConfigure, _onConfChanged)
    ftlog.info('hall_simple_invite initialize end')


def getSimpleInviteConf(userId, gameId, clientId):
    vcTemp = hallconf.getVcTemplateConf(clientId, 'simple_invite')
    if not vcTemp:
        ftlog.error('hall_simple_invite.getSimpleInviteConf has no template for clientId:', clientId,
                    ' Please check...')

    ftlog.debug('hall_simple_invite getSimpleInviteConf:', vcTemp)
    return _conf.get(vcTemp, None)


def getGameCount(userId, clientId):
    count = 0
    for gameId in pokerconf.getConfigGameIds():
        if gameId not in gdata.games():
            continue

        gCount = gdata.games()[gameId].getPlayGameInfoByKey(userId, clientId, TYGame.PLAY_COUNT)
        ftlog.debug('hall_simple_invite.getGameCount gameId:', gameId, ' gameCount:', gCount)
        if gCount:
            count += gCount

    ftlog.debug('hall_simple_invite.getGameCount gameIds:', pokerconf.getConfigGameIds()
                , ' gameCount:', count)
    return count
