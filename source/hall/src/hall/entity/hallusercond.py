# -*- coding=utf-8
'''
Created on 2015年8月25日

@author: zhaojiangang
'''
import time
from sre_compile import isstring

from datetime import datetime

import freetime.util.log as ftlog
import poker.entity.dao.userdata as pkuserdata
import poker.util.timestamp as pktimestamp
from hall.entity import hallaccount
from hall.entity import hallsubmember
from hall.entity.hallconf import HALL_GAMEID
from poker.entity.biz.confobj import TYConfableRegister, TYConfable
from poker.entity.biz.exceptions import TYBizConfException
from poker.entity.configure import pokerconf
from poker.entity.dao import onlinedata
from poker.entity.dao import sessiondata
from poker.entity.dao import userdata, gamedata
from poker.util import strutil


class UserCondition(TYConfable):
    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        raise NotImplemented()


class UserConditionFirstRecharged(UserCondition):
    TYPE_ID = 'user.cond.firstRecharged'

    def __init__(self):
        super(UserConditionFirstRecharged, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallstore
        return hallstore.isFirstRecharged(userId)

    def decodeFromDict(self, d):
        return self


class UserConditionUnFirstRecharged(UserCondition):
    TYPE_ID = 'user.cond.unFirstRecharged'

    def __init__(self):
        super(UserConditionUnFirstRecharged, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallstore
        return not hallstore.isFirstRecharged(userId)

    def decodeFromDict(self, d):
        return self


class UserConditionGotFirstRechargeReward(UserCondition):
    TYPE_ID = 'user.cond.gotFirstRechargeReward'

    def __init__(self):
        super(UserConditionGotFirstRechargeReward, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallstore
        return hallstore.isGetFirstRechargeReward(userId)

    def decodeFromDict(self, d):
        return self


class UserConditionUnGotFirstRechargeReward(UserCondition):
    TYPE_ID = 'user.cond.unGotFirstRechargeReward'

    def __init__(self):
        super(UserConditionUnGotFirstRechargeReward, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallstore
        return not hallstore.isGetFirstRechargeReward(userId)

    def decodeFromDict(self, d):
        return self


class UserConditionisMyGameid(UserCondition):
    TYPE_ID = 'user.cond.isMyGameid'

    def __init__(self, myGameId=6):
        super(UserConditionisMyGameid, self).__init__()
        self.myGameId = myGameId

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        mowGameId = strutil.getGameIdFromHallClientId(clientId)
        ftlog.debug('UserConditionisMyGameid.check userId=', userId,
                    'gameId=', gameId,
                    'clientId=', clientId,
                    'nowGameId=', mowGameId,
                    'myGameId=', self.myGameId)
        if mowGameId == self.myGameId:
            return True
        else:
            return False

    def decodeFromDict(self, d):
        self.myGameId = d.get('myGameId', 0)
        if not isinstance(self.myGameId, int) or self.myGameId < 1:
            raise TYBizConfException(d, 'UserConditionisMyGameid.myGameId must be int >= 1')
        return self


class UserConditionVipLevel(UserCondition):
    TYPE_ID = 'user.cond.vipLevel'

    def __init__(self, startLevel=-1, stopLevel=-1):
        super(UserConditionVipLevel, self).__init__()
        self.startLevel = startLevel
        self.stopLevel = stopLevel

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallvip
        try:
            userVip = hallvip.userVipSystem.getUserVip(userId)
            level = userVip.vipLevel.level

            startCondition = (self.startLevel == -1 or level >= self.startLevel)
            stopCondition = (self.stopLevel == -1 or level <= self.stopLevel)
            if ftlog.is_debug():
                ftlog.debug('UserConditionVipLevel.check userId:', userId
                            , ' gameId:', gameId
                            , ' startLevel:', self.startLevel
                            , ' stopLevel:', self.stopLevel
                            , ' startCondition:', startCondition
                            , ' stopCondition:', stopCondition
                            )

            return startCondition and stopCondition
        except:
            ftlog.error()
            return False

    def decodeFromDict(self, d):
        self.startLevel = d.get('startLevel', -1)
        if not isinstance(self.startLevel, int) or self.startLevel < -1:
            raise TYBizConfException(d, 'UserConditionVipLevel.startLevel must be int >= -1')
        self.stopLevel = d.get('stopLevel', -1)
        if not isinstance(self.stopLevel, int) or self.stopLevel < -1:
            raise TYBizConfException(d, 'UserConditionVipLevel.stopLevel must be int >= -1')
        if self.stopLevel != -1 and self.stopLevel < self.startLevel:
            raise TYBizConfException(d, 'UserConditionVipLevel.stopLevel must >= startLevel')
        return self


class UserConditionChip(UserCondition):
    TYPE_ID = 'user.cond.chip'

    def __init__(self, startChip=-1, stopChip=-1):
        super(UserConditionChip, self).__init__()
        self.startChip = startChip
        self.stopChip = stopChip

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from poker.entity.dao import userchip
        try:
            userChip = userchip.getChip(userId)
            if ftlog.is_debug():
                ftlog.debug('userChip:', userChip, ' startChip:', self.startChip, ' stopChip:', self.stopChip)
            return (self.startChip == -1 or userChip >= self.startChip) \
                   and (self.stopChip == -1 or userChip <= self.stopChip)
        except:
            ftlog.error()
            return False

    def decodeFromDict(self, d):
        self.startChip = d.get('startChip', -1)
        if not isinstance(self.startChip, int) or self.startChip < -1:
            raise TYBizConfException(d, 'UserConditionChip.startChip must be int >= -1')

        self.stopChip = d.get('stopChip', -1)
        if not isinstance(self.stopChip, int) or self.stopChip < -1:
            raise TYBizConfException(d, 'UserConditionChip.stopChip must be int >= -1')

        if self.stopChip != -1 and self.stopChip < self.startChip:
            raise TYBizConfException(d, 'UserConditionChip.stopChip must >= startChip')

        return self


class UserConditionCoupon(UserCondition):
    TYPE_ID = 'user.cond.coupon'

    def __init__(self, startCoupon=-1, stopCoupon=-1):
        super(UserConditionCoupon, self).__init__()
        self.startCoupon = startCoupon
        self.stopCoupon = stopCoupon

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from poker.entity.dao import userchip
        try:
            userConpon = userchip.getCoupon(userId)
            if ftlog.is_debug():
                ftlog.debug('userConpon:', userConpon
                            , ' startCoupon:', self.startCoupon
                            , ' stopCoupon:', self.stopCoupon)
            return (self.startCoupon == -1 or userConpon >= self.startCoupon) \
                   and (self.stopCoupon == -1 or userConpon <= self.stopCoupon)
        except:
            ftlog.error()
            return False

    def decodeFromDict(self, d):
        self.startCoupon = d.get('startCoupon', -1)
        if not isinstance(self.startCoupon, int) or self.startCoupon < -1:
            raise TYBizConfException(d, 'UserConditionCoupon.startCoupon must be int >= -1')

        self.stopCoupon = d.get('stopCoupon', -1)
        if not isinstance(self.stopCoupon, int) or self.stopCoupon < -1:
            raise TYBizConfException(d, 'UserConditionCoupon.stopCoupon must be int >= -1')

        if self.stopCoupon != -1 and self.stopCoupon < self.startCoupon:
            raise TYBizConfException(d, 'UserConditionCoupon.stopCoupon must >= startCoupon')

        return self


class UserConditionsignDayMod(UserCondition):
    TYPE_ID = 'user.cond.signDayMod'

    def __init__(self, mod=1, remainder=-1):
        super(UserConditionsignDayMod, self).__init__()
        self.mod = mod
        self.remainder = remainder

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        try:
            nowDate = datetime.fromtimestamp(timestamp).date()
            createDate = datetime.strptime(userdata.getAttr(userId, 'createTime'), '%Y-%m-%d %H:%M:%S.%f').date()
            registerDays = max(0, (nowDate - createDate).days)
            if registerDays % self.mod == self.remainder:
                return True
            else:
                return False
        except:
            ftlog.error()
            return False

    def decodeFromDict(self, d):
        self.mod = int(d.get('mod', 1))
        if not isinstance(self.mod, int) or self.mod < 1:
            raise TYBizConfException(d, 'UserConditionsignDayMod.mod must be int >= 1')
        self.remainder = int(d.get('remainder', -1))
        if not isinstance(self.remainder, int) or self.remainder < -1:
            raise TYBizConfException(d, 'UserConditionsignDayMod.remainder must be int >= -1')
        return self


class UserConditionLoginDays(UserCondition):
    TYPE_ID = 'user.cond.login.days'

    def __init__(self, startDays=1, endDays=-1):
        super(UserConditionLoginDays, self).__init__()
        self.startDays = startDays
        self.endDays = endDays

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        loginDays = gamedata.getGameAttrInt(userId, HALL_GAMEID, 'loginDays')
        startCondition = (self.startDays == -1) or (loginDays >= self.startDays)
        endCondition = (self.endDays == -1) or (loginDays < self.endDays)
        if ftlog.is_debug():
            ftlog.debug('UserConditionLoginDays.check userId:', userId
                        , ' clientId:', clientId
                        , ' loginDays:', loginDays
                        , ' startDays:', self.startDays
                        , ' endDays:', self.endDays
                        , ' startCondition:', startCondition
                        , ' endCondition:', endCondition
                        )
        return startCondition and endCondition

    def decodeFromDict(self, d):
        self.startDays = d.get('startDays', -1)
        if not isinstance(self.startDays, int):
            raise TYBizConfException(d, 'UserConditionLoginDays.startDays must be int')

        self.endDays = d.get('endDays', -1)
        if not isinstance(self.endDays, int):
            raise TYBizConfException(d, 'UserConditionLoginDays.endDays must be int')

        return self


class UserConditionShareCount(UserCondition):
    TYPE_ID = 'user.cond.share.count'

    def __init__(self, start=1, end=-1):
        super(UserConditionShareCount, self).__init__()
        self.start = start
        self.end = end

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        shareCount = gamedata.getGameAttrInt(userId, HALL_GAMEID, 'shareCount')
        startCondition = (self.start == -1) or (shareCount >= self.start)
        endCondition = (self.end == -1) or (shareCount < self.end)
        if ftlog.is_debug():
            ftlog.debug('UserConditionShareCount.check userId:', userId
                        , ' clientId:', clientId
                        , ' shareCount:', shareCount
                        , ' start:', self.start
                        , ' end:', self.end
                        , ' startCondition:', startCondition
                        , ' endCondition:', endCondition
                        )
        return startCondition and endCondition

    def decodeFromDict(self, d):
        self.start = d.get('start', -1)
        if not isinstance(self.start, int):
            raise TYBizConfException(d, 'UserConditionShareCount.start must be int')

        self.end = d.get('end', -1)
        if not isinstance(self.end, int):
            raise TYBizConfException(d, 'UserConditionShareCount.end must be int')

        return self


class UserConditionPlayTime(UserCondition):
    TYPE_ID = 'user.cond.play.time'

    def __init__(self, startTime=1, endTime=-1):
        super(UserConditionPlayTime, self).__init__()
        self.startTime = startTime
        self.endTime = endTime

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        totalTime = gamedata.getGameAttrInt(userId, HALL_GAMEID, 'totaltime')
        startCondition = (self.startTime == -1) or (totalTime >= self.startTime)
        endCondition = (self.endTime == -1) or (totalTime < self.endTime)
        if ftlog.is_debug():
            ftlog.debug('UserConditionPlayTime.check userId:', userId
                        , ' clientId:', clientId
                        , ' totalTime:', totalTime
                        , ' startTime:', self.startTime
                        , ' endTime:', self.endTime
                        , ' startCondition:', startCondition
                        , ' endCondition:', endCondition
                        )
        return startCondition and endCondition

    def decodeFromDict(self, d):
        self.startTime = d.get('startTime', -1)
        if not isinstance(self.startTime, int):
            raise TYBizConfException(d, 'UserConditionPlayTime.startTime must be int')

        self.endTime = d.get('endTime', -1)
        if not isinstance(self.endTime, int):
            raise TYBizConfException(d, 'UserConditionPlayTime.endTime must be int')

        return self


class UserConditionReturnTime(UserCondition):
    '''
    用户再次回归时，与上次登录的时间差
    '''
    TYPE_ID = 'user.cond.return.time'

    def __init__(self, startTime=1, endTime=-1):
        super(UserConditionReturnTime, self).__init__()
        self.startTime = startTime
        self.endTime = endTime

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        lastAuthTime, authTime = userdata.getAttrs(userId, ['lastAuthorTime', 'authorTime'])
        if not lastAuthTime:
            lastAuthTime = pktimestamp.formatTimeMs()

        if ftlog.is_debug():
            ftlog.debug('UserConditionReturnTime.check lastAuthTime:', lastAuthTime)

        if not authTime:
            authTime = pktimestamp.formatTimeMs()
        if ftlog.is_debug():
            ftlog.debug('UserConditionReturnTime.check authTime:', authTime)

        totalTime = pktimestamp.getTimeStrDiff(lastAuthTime, authTime)
        if totalTime < 0:
            totalTime = 0

        startCondition = (self.startTime == -1) or (totalTime >= self.startTime)
        endCondition = (self.endTime == -1) or (totalTime < self.endTime)
        if ftlog.is_debug():
            ftlog.debug('UserConditionReturnTime.check userId:', userId
                        , ' clientId:', clientId
                        , ' totalTime:', totalTime
                        , ' startTime:', self.startTime
                        , ' endTime:', self.endTime
                        , ' startCondition:', startCondition
                        , ' endCondition:', endCondition
                        )
        return startCondition and endCondition

    def decodeFromDict(self, d):
        self.startTime = d.get('startTime', -1)
        if not isinstance(self.startTime, int):
            raise TYBizConfException(d, 'UserConditionReturnTime.startTime must be int')

        self.endTime = d.get('endTime', -1)
        if not isinstance(self.endTime, int):
            raise TYBizConfException(d, 'UserConditionReturnTime.endTime must be int')

        return self


class UserConditionBenefitsTime(UserCondition):
    '''
    用户再次回归时，与上次登录的时间差
    '''
    TYPE_ID = 'user.cond.benefits.time'

    def __init__(self, startTime=1, endTime=-1):
        super(UserConditionBenefitsTime, self).__init__()
        self.startTime = startTime
        self.endTime = endTime

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        '''
        lastAuthorTime > startTime
        and
        authorTime < endTime
        '''
        lastAuthTime = pktimestamp.getCurrentTimestamp();
        authTime = pktimestamp.getCurrentTimestamp();
        lastAuthTimeStr, authTimeStr = userdata.getAttrs(userId, ['lastAuthorTime', 'authorTime'])
        if lastAuthTimeStr:
            lastAuthTime = pktimestamp.timestrToTimestamp(lastAuthTimeStr, '%Y-%m-%d %H:%M:%S.%f')
        if ftlog.is_debug():
            ftlog.debug('UserConditionBenefitsTime.check lastAuthTime:', lastAuthTime)

        if authTimeStr:
            authTime = pktimestamp.timestrToTimestamp(authTimeStr, '%Y-%m-%d %H:%M:%S.%f')
        if ftlog.is_debug():
            ftlog.debug('UserConditionBenefitsTime.check authTime:', authTime)

        loginDays = gamedata.getGameAttrInt(userId, gameId, 'loginDays')
        startCondition = (lastAuthTime < self.startTime) or (loginDays == 1)
        endCondition = (authTime > self.startTime) and (authTime < self.endTime)

        if ftlog.is_debug():
            ftlog.debug('UserConditionBenefitsTime.check userId:', userId
                        , ' clientId:', clientId
                        , ' startTime:', self.startTime
                        , ' endTime:', self.endTime
                        , ' lastAuthTime:', lastAuthTime
                        , ' authTime:', authTime
                        , ' startCondition:', startCondition
                        , ' endCondition:', endCondition
                        )
        return startCondition and endCondition

    def decodeFromDict(self, d):
        startTimeStr = d.get('startTime', None)
        if not isstring(startTimeStr):
            raise TYBizConfException(d, 'UserConditionReturnTime.startTime must be string')
        self.startTime = pktimestamp.timestrToTimestamp(startTimeStr, '%Y-%m-%d %H:%M:%S')

        endTimeStr = d.get('endTime', None)
        if not isstring(endTimeStr):
            raise TYBizConfException(d, 'UserConditionReturnTime.endTime must be string')
        self.endTime = pktimestamp.timestrToTimestamp(endTimeStr, '%Y-%m-%d %H:%M:%S')

        return self


class UserConditionSex(UserCondition):
    TYPE_ID = 'user.cond.sex'

    def __init__(self, sex=0):
        super(UserConditionSex, self).__init__()
        self.sex = sex

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        return userdata.getAttr(userId, 'sex') == self.sex

    def decodeFromDict(self, d):
        self.sex = d.get('sex', 0)
        if self.sex not in (0, 1):
            raise TYBizConfException(d, 'UserConditionSex.sex must be int in (0,1)')
        return self


class UserConditionRegisterDay(UserCondition):
    TYPE_ID = 'user.cond.registerDays'

    def __init__(self, startDays=-1, stopDays=-1):
        super(UserConditionRegisterDay, self).__init__()
        self.startDays = startDays
        self.stopDays = stopDays

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        try:
            if self.startDays == -1 and self.stopDays == -1:
                return True
            nowDate = datetime.fromtimestamp(timestamp).date()
            createDate = datetime.strptime(userdata.getAttr(userId, 'createTime'), '%Y-%m-%d %H:%M:%S.%f').date()
            registerDays = max(0, (nowDate - createDate).days)
            return (self.startDays == -1 or registerDays >= self.startDays) \
                   and (self.stopDays == -1 or registerDays <= self.stopDays)
        except:
            ftlog.error()
            return False

    def decodeFromDict(self, d):
        self.startDays = d.get('startDays', -1)
        if not isinstance(self.startDays, int) or self.startDays < -1:
            raise TYBizConfException(d, 'UserConditionRegisterDay.startDays must be int >= -1')
        self.stopDays = d.get('stopDays', -1)
        if not isinstance(self.stopDays, int) or self.stopDays < -1:
            raise TYBizConfException(d, 'UserConditionRegisterDay.stopDays must be int >= -1')
        if self.stopDays != -1 and self.stopDays < self.startDays:
            raise TYBizConfException(d, 'UserConditionRegisterDay.stopDays must >= startDays')
        return self


class UserConditionNewUser(UserConditionRegisterDay):
    TYPE_ID = 'user.cond.newuser'

    def __init__(self):
        super(UserConditionNewUser, self).__init__(-1, 7)

    def decodeFromDict(self, d):
        return self


class UserConditionIsSubscribeMember(UserCondition):
    TYPE_ID = 'user.cond.isSubscribeMember'

    def __init__(self):
        super(UserConditionIsSubscribeMember, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        subMemberStatus = hallsubmember.loadSubMemberStatus(userId)
        return subMemberStatus.isSub

    def decodeFromDict(self, d):
        return self


class UserConditionNotSubscribeMember(UserCondition):
    TYPE_ID = 'user.cond.notSubscribeMember'

    def __init__(self):
        super(UserConditionNotSubscribeMember, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        subMemberStatus = hallsubmember.loadSubMemberStatus(userId)
        return not subMemberStatus.isSub

    def decodeFromDict(self, d):
        return self


class UserConditionMemberRemDays(UserCondition):
    TYPE_ID = 'user.cond.memberRemDays'

    def __init__(self):
        super(UserConditionMemberRemDays, self).__init__()
        self.startRemDays = None
        self.endRemDays = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallitem
        userAssets = hallitem.itemSystem.loadUserAssets(userId)
        remDays = userAssets.balance(gameId, hallitem.ASSET_ITEM_MEMBER_NEW_KIND_ID, timestamp)
        if self.startRemDays >= 0 and remDays < self.startRemDays:
            return False
        if self.endRemDays >= 0 and remDays > self.endRemDays:
            return False
        return True

    def decodeFromDict(self, d):
        self.startRemDays = d.get('startRemDays')
        self.endRemDays = d.get('endRemDays')
        if not isinstance(self.startRemDays, int):
            raise TYBizConfException(d, 'UserConditionMemberRemDays.startRemDays must be int')
        if not isinstance(self.endRemDays, int):
            raise TYBizConfException(d, 'UserConditionMemberRemDays.endRemDays must be int')
        if self.endRemDays >= 0 and self.endRemDays < self.startRemDays:
            raise TYBizConfException(d, 'UserConditionMemberRemDays.endRemDays must be >= startRemDays')
        return self


class UserConditionIsMemberNotSub(UserCondition):
    TYPE_ID = 'user.cond.isMemberNotSub'

    def __init__(self):
        super(UserConditionIsMemberNotSub, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallitem
        subMemberStatus = hallsubmember.loadSubMemberStatus(userId)
        if subMemberStatus.isSub:
            return False
        userAssets = hallitem.itemSystem.loadUserAssets(userId)
        return userAssets.balance(gameId, hallitem.ASSET_ITEM_MEMBER_NEW_KIND_ID, timestamp) > 0

    def decodeFromDict(self, d):
        return self


class UserConditionTimePeriod(UserCondition):
    TYPE_ID = 'user.cond.timePeriod'

    def __init__(self):
        super(UserConditionTimePeriod, self).__init__()
        self.periods = []

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        if not self.periods:
            return True
        nowT = datetime.fromtimestamp(timestamp).time()
        for period in self.periods:
            if (period[0] is None or nowT >= period[0]) and (period[1] is None or nowT < period[1]):
                if ftlog.is_debug():
                    ftlog.debug('UserConditionTimePeriod.check gameId=', gameId,
                                'userId=', userId,
                                'clientId=', clientId,
                                'period=', [period[0], period[1]],
                                'nowT=', nowT,
                                'inPeriod=', True)
                return True
        if ftlog.is_debug():
            ftlog.debug('UserConditionTimePeriod.check gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'periods=', self.periods,
                        'nowT=', nowT,
                        'inPeriod=', False)
        return False

    def decodeFromDict(self, d):
        periods = d.get('periods')
        if periods:
            timeZero = datetime.strptime('00:00', '%H:%M').time()
            for period in periods:
                s = datetime.strptime(period[0], '%H:%M').time()
                e = datetime.strptime(period[1], '%H:%M').time()
                s = s if s != timeZero else None
                e = e if e != timeZero else None
                if s != e:
                    if (s is None or e is None) or (s < e):
                        self.periods.append((s, e))
                    elif s > e:
                        self.periods.append((s, None))
                        self.periods.append((None, e))
        return self


class UserConditionPayCount(UserCondition):
    TYPE_ID = 'user.cond.payCount'

    def __init__(self, minPayCount=-1, maxPayCount=-1):
        super(UserConditionPayCount, self).__init__()
        self.minPayCount = minPayCount
        self.maxPayCount = maxPayCount

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        payCount = pkuserdata.getAttrInt(userId, 'payCount')
        return ((self.minPayCount < 0 or payCount >= self.minPayCount)
                and (self.maxPayCount < 0 or payCount < self.maxPayCount))

    def decodeFromDict(self, d):
        self.minPayCount = d.get('minPayCount', -1)
        if not isinstance(self.minPayCount, int) or self.minPayCount < -1:
            raise TYBizConfException(d, 'UserConditionPayCount.minPayCount must be int >= -1')
        self.maxPayCount = d.get('maxPayCount', -1)
        if not isinstance(self.maxPayCount, int) or self.maxPayCount < -1:
            raise TYBizConfException(d, 'UserConditionPayCount.maxPayCount must be int >= -1')
        if self.maxPayCount != -1 and self.maxPayCount < self.minPayCount:
            raise TYBizConfException(d, 'UserConditionPayCount.maxPayCount must >= minPayCount')
        return self


class UserConditionNonPay(UserConditionPayCount):
    '''
    用户没有支付
    '''
    TYPE_ID = 'user.cond.nonPay'

    def __init__(self):
        '''
        [0, 1) 也就是0次
        '''
        super(UserConditionNonPay, self).__init__(0, 1)

    def decodeFromDict(self, d):
        return self


class UserConditionPayLeastOnce(UserConditionPayCount):
    TYPE_ID = 'user.cond.payLeastOnce'

    def __init__(self):
        '''
        至少支付一次
        '''
        super(UserConditionPayLeastOnce, self).__init__(1, -1)

    def decodeFromDict(self, d):
        return self


# 是否绑定手机
class UserConditionBindPhone(UserCondition):
    TYPE_ID = 'user.cond.BindPhone'

    def __init__(self):
        super(UserConditionBindPhone, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        bindmobile = userdata.getAttr(userId, 'bindMobile')
        isBindPhene = True if bindmobile == None or bindmobile == "" else False
        return isBindPhene

    def decodeFromDict(self, d):
        return self


# 今天没有签到
class UserConditionNotCheckInToday(UserCondition):
    TYPE_ID = 'user.cond.NotCheckInToday'

    def __init__(self):
        super(UserConditionNotCheckInToday, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import monthcheckin
        status = monthcheckin.loadStatus(userId)
        nowDate = datetime.now().date()
        checked = False
        if nowDate in status.checkinDateList:
            checked = True
        return not checked

    def decodeFromDict(self, d):
        return self


# 今天已经签到  
class UserConditionCheckedInToday(UserCondition):
    TYPE_ID = 'user.cond.CheckedInToday'

    def __init__(self):
        super(UserConditionCheckedInToday, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import monthcheckin
        status = monthcheckin.loadStatus(userId)
        nowDate = datetime.now().date()
        checked = False
        if nowDate in status.checkinDateList:
            checked = True
        return checked

    def decodeFromDict(self, d):
        return self


# 有可补签天数
class UserConditionHasSupCheckinDay(UserCondition):
    TYPE_ID = 'user.cond.HasSupCheckinDay'

    def __init__(self):
        super(UserConditionHasSupCheckinDay, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import monthcheckin
        status = monthcheckin.loadStatus(userId)
        nowDate = datetime.now()
        hasLack = status.checkinCount + status.supplementCheckinCount < nowDate._day

        return hasLack

    def decodeFromDict(self, d):
        return self


# 是否可领取签到奖励(有签到奖励可以领取,且未领取)
class UserConditionCheckInHasReward(UserCondition):
    TYPE_ID = 'user.cond.CheckInHasReward'

    def __init__(self):
        super(UserConditionCheckInHasReward, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import monthcheckin
        status = monthcheckin.loadStatus(userId)
        hasReward = False
        for _days, rewardContent in enumerate(monthcheckin.getConf().get('daysRewards', [])):
            monthRange = monthcheckin.getMonthRange()
            if rewardContent.get('days') < monthRange:
                monthRange = rewardContent.get('days')
            if not status.isReward(monthRange) and status.allCheckinCount >= monthRange:
                hasReward = True
                break
        return hasReward

    def decodeFromDict(self, d):
        return self


# 是否有抽奖卡
class UserConditionHasLuckyCard(UserCondition):
    TYPE_ID = 'user.cond.HasLuckyCard'

    def __init__(self):
        super(UserConditionHasLuckyCard, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallitem
        userAssets = hallitem.itemSystem.loadUserAssets(userId)
        timestamp = pktimestamp.getCurrentTimestamp()
        cardNum = userAssets.balance(gameId, hallitem.ASSET_ITEM_LOTTERY_CARD_ID, timestamp)
        hasLotteryCard = False if cardNum == 0 else True
        return hasLotteryCard

    def decodeFromDict(self, d):
        return self


# 是否是会员
class UserConditionIsMember(UserConditionMemberRemDays):
    TYPE_ID = 'user.cond.IsMember'

    def __init__(self):
        super(UserConditionIsMember, self).__init__()
        self.startRemDays = 1
        self.endRemDays = -1

    def decodeFromDict(self, d):
        return self


# 是否不是会员
class UserConditionNotIsMember(UserConditionMemberRemDays):
    TYPE_ID = 'user.cond.notIsMember'

    def __init__(self):
        super(UserConditionNotIsMember, self).__init__()
        self.startRemDays = 1
        self.endRemDays = -1

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        return not super(UserConditionNotIsMember, self).check(gameId, userId, clientId, timestamp, **kwargs)

    def decodeFromDict(self, d):
        return self


# 是否有会员弹窗配置
class UserConditionHasMemberBuyWindow(UserCondition):
    TYPE_ID = 'user.cond.HasMemberBuyWindow'

    def __init__(self):
        super(UserConditionHasMemberBuyWindow, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallpopwnd
        todotask = hallpopwnd.makeTodoTaskByTemplate(gameId, userId, clientId, 'memberBuy2')
        return todotask is not None

    def decodeFromDict(self, d):
        return self


# 是否有会员签到没有领取
class UserConditionHasMemberReward(UserCondition):
    TYPE_ID = 'user.cond.HasMemberReward'

    def __init__(self):
        super(UserConditionHasMemberReward, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallitem
        userBag = hallitem.itemSystem.loadUserAssets(userId).getUserBag()
        memberCardItem = userBag.getItemByKindId(hallitem.ITEM_MEMBER_NEW_KIND_ID)
        return memberCardItem and memberCardItem.canCheckin(timestamp)

    def decodeFromDict(self, d):
        return self


# 是否有新手任务奖励可以领取
class UserConditionHasTaskReward(UserCondition):
    TYPE_ID = 'user.cond.HasTaskReward'

    def __init__(self):
        super(UserConditionHasTaskReward, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import neituiguangtask
        taskModel = neituiguangtask.newUserTaskSystem.loadTaskModel(userId, timestamp)
        hasTaskReward = False
        for task in taskModel.userTaskUnit.taskList:
            if task.isFinished and not task.gotReward:
                hasTaskReward = True
                break
        return hasTaskReward

    def decodeFromDict(self, d):
        return self


# 是否全部完成新手任务
class UserConditionTaskAllDone(UserCondition):
    TYPE_ID = 'user.cond.TaskAllDone'

    def __init__(self):
        super(UserConditionTaskAllDone, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import neituiguangtask
        taskModel = neituiguangtask.newUserTaskSystem.loadTaskModel(userId, timestamp)
        allFinished = True
        for task in taskModel.userTaskUnit.taskList:
            if not task.isFinished or not task.gotReward:
                allFinished = False
                break
        return allFinished

    def decodeFromDict(self, d):
        return self


# 是否未评价五星评价
class UserConditionNotFiveStar(UserCondition):
    TYPE_ID = 'user.cond.NotFiveStar'

    def __init__(self):
        super(UserConditionNotFiveStar, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import fivestarrate
        canTriggle, _channel = fivestarrate.checkCanTriggleFiveStartRate(userId, clientId, timestamp)
        return canTriggle

    def decodeFromDict(self, d):
        return self


# 是否有每日分享配置
class UserConditionHasDailyShareConfig(UserCondition):
    TYPE_ID = 'user.cond.HasDailyShareConfig'

    def __init__(self):
        super(UserConditionHasDailyShareConfig, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallshare
        shareId = hallshare.getShareId("dailyShare", userId, gameId)
        if shareId is None:
            return False
        share = hallshare.findShare(shareId)
        if not share:
            return False
        return True

    def decodeFromDict(self, d):
        return self


# 是否今天还没有完成每日分享
class UserConditionHasDailyShareReward(UserCondition):
    TYPE_ID = 'user.cond.HasDailyShareReward'

    def __init__(self):
        super(UserConditionHasDailyShareReward, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallshare
        shareId = hallshare.getShareId('dailyShare', userId, gameId)
        if shareId is None:
            return False
        share = hallshare.findShare(shareId)
        if not share:
            return False
        return hallshare.canReward(userId, share, timestamp)

    def decodeFromDict(self, d):
        return self


# 是否有免费福利小红点
class UserConditionHasFreeMark(UserCondition):
    TYPE_ID = 'user.cond.HasFreeMark'

    def __init__(self):
        super(UserConditionHasFreeMark, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallfree
        from hall.servers.util.free_handler import FreeHelper
        freeList = hallfree.getFree(gameId, userId, clientId, timestamp)
        encodeFreeList = FreeHelper.encodeFreeList(gameId, userId, clientId, freeList, timestamp)
        markVisible = False
        if freeList:
            for index in range(len(encodeFreeList)):
                markVisible = markVisible or encodeFreeList[index]['markVisible']
        return markVisible

    def decodeFromDict(self, d):
        return self


class UserConditionClientVersion(UserCondition):
    TYPE_ID = 'user.cond.clientVersion'

    def __init__(self):
        super(UserConditionClientVersion, self).__init__()
        self.minVersion = None
        self.maxVersion = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        _, clientVer, _ = strutil.parseClientId(clientId)
        return (self.minVersion == -1 or clientVer >= self.minVersion) \
               and (self.maxVersion == -1 or clientVer < self.maxVersion)

    def decodeFromDict(self, d):
        self.minVersion = d.get('minVersion', -1)
        if not isinstance(self.minVersion, (int, float)) or self.minVersion < -1:
            raise TYBizConfException(d, 'UserConditionClientVersion.minVersion must be int >= -1')
        self.maxVersion = d.get('maxVersion', -1)
        if not isinstance(self.maxVersion, (int, float)) or self.maxVersion < -1:
            raise TYBizConfException(d, 'UserConditionClientVersion.maxVersion must be int >= -1')
        if self.maxVersion != -1 and self.maxVersion < self.minVersion:
            raise TYBizConfException(d, 'UserConditionClientVersion.maxVersion must >= minVersion')
        return self


class UserConditionInClientIDs(UserCondition):
    TYPE_ID = 'user.cond.in.clientIds'

    def __init__(self):
        super(UserConditionInClientIDs, self).__init__()
        # clientId编码集合
        self.clientIds = []

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        intClientidNum = pokerconf.clientIdToNumber(clientId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionInClientIDs.check self.clientIds:', self.clientIds
                        , ' intClientidNum:', intClientidNum
                        )

        return intClientidNum in self.clientIds

    def decodeFromDict(self, d):
        self.clientIds = d.get('clientIds', [])
        return self


class UserConditionNotInClientIDs(UserCondition):
    TYPE_ID = 'user.cond.notin.clientIds'

    def __init__(self):
        super(UserConditionNotInClientIDs, self).__init__()
        # clientId编码集合
        self.clientIds = []

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        intClientidNum = pokerconf.clientIdToNumber(clientId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionNotInClientIDs.check self.clientIds:', self.clientIds
                        , ' intClientidNum:', intClientidNum
                        )

        return intClientidNum not in self.clientIds

    def decodeFromDict(self, d):
        self.clientIds = d.get('clientIds', [])
        return self


class UserConditionOR(UserCondition):
    """多个条件的或关系，有一个正确，结果就正确
    """
    TYPE_ID = 'user.cond.or'

    def __init__(self):
        super(UserConditionOR, self).__init__()
        self.conditions = []

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        if ftlog.is_debug():
            ftlog.debug('UserConditionOR.check >>> gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'timestamp=', timestamp,
                        'kwargs=', kwargs,
                        'conditions=', self.conditions)

        for condition in self.conditions:
            if condition.check(gameId, userId, clientId, timestamp, **kwargs):
                if ftlog.is_debug():
                    ftlog.debug('UserConditionOR.check <<< gameId=', gameId,
                                'userId=', userId,
                                'clientId=', clientId,
                                'timestamp=', timestamp,
                                'kwargs=', kwargs,
                                'conditions=', self.conditions,
                                'condition=', condition,
                                'ret=', True)
                return True

        if ftlog.is_debug():
            ftlog.debug('UserConditionOR.check <<< gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'timestamp=', timestamp,
                        'kwargs=', kwargs,
                        'conditions=', self.conditions,
                        'ret=', False)
        return False

    def decodeFromDict(self, d):
        self.conditions = UserConditionRegister.decodeList(d.get('list', []))
        return self


class UserConditionAND(UserCondition):
    """多个条件的与关系，所有条件都满足，结果才满足
    """
    TYPE_ID = 'user.cond.and'

    def __init__(self):
        super(UserConditionAND, self).__init__()
        self.conditions = []

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        if ftlog.is_debug():
            ftlog.debug('UserConditionAND.check >>> gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'timestamp=', timestamp,
                        'kwargs=', kwargs,
                        'conditions=', self.conditions)
        for condition in self.conditions:
            if not condition.check(gameId, userId, clientId, timestamp, **kwargs):
                if ftlog.is_debug():
                    ftlog.debug('UserConditionAND.check <<< gameId=', gameId,
                                'userId=', userId,
                                'clientId=', clientId,
                                'timestamp=', timestamp,
                                'kwargs=', kwargs,
                                'conditions=', self.conditions,
                                'condition=', condition,
                                'ret=', False)
                return False
        if ftlog.is_debug():
            ftlog.debug('UserConditionAND.check <<< gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'timestamp=', timestamp,
                        'kwargs=', kwargs,
                        'conditions=', self.conditions,
                        'ret=', True)
        return True

    def decodeFromDict(self, d):
        self.conditions = UserConditionRegister.decodeList(d.get('list', []))
        return self


class UserConditionNOT(UserCondition):
    """单个条件的非关系
    1）条件满足，返回不满足
    2）条件不满足，返回满足
    """
    TYPE_ID = 'user.cond.not'

    def __init__(self):
        super(UserConditionNOT, self).__init__()
        self.condition = {}

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        if ftlog.is_debug():
            ftlog.debug('UserConditionNOT.check >>> gameId=', gameId,
                        'userId=', userId,
                        'clientId=', clientId,
                        'timestamp=', timestamp,
                        'kwargs=', kwargs,
                        'condition=', self.condition,
                        'ret NOT!!!')

        if self.condition.check(gameId, userId, clientId, timestamp, **kwargs):
            return False
        else:
            return True

    def decodeFromDict(self, d):
        self.condition = UserConditionRegister.decodeFromDict(d.get('condition', {}))
        return self


class UserConditionDayFirstLogin(UserCondition):
    TYPE_ID = 'user.cond.dayfirstlogin'

    def __init__(self):
        super(UserConditionDayFirstLogin, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        return kwargs.get('isDayFirstLogin', False)

    def decodeFromDict(self, d):
        return self


class UserConditionNotDayFirstLogin(UserCondition):
    TYPE_ID = 'user.cond.notdayfirstlogin'

    def __init__(self):
        super(UserConditionNotDayFirstLogin, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        return not kwargs.get('isDayFirstLogin', False)

    def decodeFromDict(self, d):
        return self


class UserConditionChargeTotal(UserCondition):
    TYPE_ID = 'user.cond.chargeTotal'

    def __init__(self):
        super(UserConditionChargeTotal, self).__init__()
        self.minCharge = None
        self.maxCharge = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        chargeTotal = pkuserdata.getAttrInt(userId, 'chargeTotal')
        return (self.minCharge == -1 or chargeTotal >= self.minCharge) \
               and (self.maxCharge == -1 or chargeTotal < self.maxCharge)

    def decodeFromDict(self, d):
        self.minCharge = d.get('minCharge', -1)
        if not isinstance(self.minCharge, (int, float)) or self.minCharge < -1:
            raise TYBizConfException(d, 'UserConditionChargeTotal.minCharge must be int >= -1')
        self.maxCharge = d.get('maxCharge', -1)
        if not isinstance(self.maxCharge, (int, float)) or self.maxCharge < -1:
            raise TYBizConfException(d, 'UserConditionChargeTotal.maxCharge must be int >= -1')
        if self.maxCharge != -1 and self.maxCharge < self.minCharge:
            raise TYBizConfException(d, 'UserConditionChargeTotal.maxCharge must >= minCharge')
        return self


class UserConditionTimeInToday(UserCondition):
    TYPE_ID = 'user.cond.time.today'

    def __init__(self):
        super(UserConditionTimeInToday, self).__init__()
        self.begin = None
        self.end = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        curTime = pktimestamp.getDayPastSeconds()
        if ftlog.is_debug():
            ftlog.debug('UserConditionTimeInToday.check curTime: ', curTime, ' begin: ', self.begin, ' end: ', self.end)

        return (self.begin == -1 or curTime >= self.begin) and (self.end == -1 or self.end > curTime)

    def decodeFromDict(self, d):
        self.begin = d.get('begin', -1)
        if not isinstance(self.begin, (int, float)) or self.begin < -1:
            raise TYBizConfException(d, 'UserConditionTimeInToday.begin must be int >= -1')

        self.end = d.get('end', -1)
        if not isinstance(self.end, (int, float)) or self.end < -1:
            raise TYBizConfException(d, 'UserConditionTimeInToday.end must be int >= -1')


class UserConditionInWhichGame(UserCondition):
    TYPE_ID = 'user.cond.which.game'

    def __init__(self):
        super(UserConditionInWhichGame, self).__init__()
        self.gameId = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        gameIdList = onlinedata.getGameEnterIds(userId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionInWhichGame.check gameIdList: ', gameIdList, ' gameId: ', self.gameId)

        return self.gameId in gameIdList

    def decodeFromDict(self, d):
        self.gameId = d.get('gameId', -1)
        if not isinstance(self.gameId, (int, float)) or self.gameId < -1:
            raise TYBizConfException(d, 'UserConditionInWhichGame.gameId must be int >= -1')


# {
#     "dashifen": {
#         "6": {
#             "curmaxscore": 15,
#             "des": "斗地主房间中每次胜利都可获得大师分，高倍数、高级房间、会员获得的更快！",
#             "premaxscore": 5,
#             "name": "斗地主",
#             "level": 2,
#             "index": 0,
#             "pic": "http://111.203.187.150:8040/dizhu/skillscore/imgs/skillscorenew_002.png",
#             "score": 6,
#             "title": "http://111.203.187.150:8040/dizhu/skillscore/imgs/ddz_skill_score_title.png"
#         }
#     }
# }        
class UserConditionFavoriteGameTopN(UserCondition):
    TYPE_ID = 'user.cond.game.dashifen.topn'

    def __init__(self):
        super(UserConditionFavoriteGameTopN, self).__init__()
        self.gameId = None
        self.topn = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        info = hallaccount.getGameInfo(userId, clientId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionFavoriteGameTopN.check gameInfo:', info)

        dashifen = info.get('dashifen', {})
        newDict = {}
        for gameStr in dashifen:
            newDict[gameStr] = dashifen[gameStr].get('level', 0)

        if ftlog.is_debug():
            ftlog.debug('UserConditionFavoriteGameTopN.newDict : ', newDict)

        newList = sorted(newDict.keys(), lambda x, y: cmp(newDict[x], newDict[y]), reverse=True)
        if ftlog.is_debug():
            ftlog.debug('UserConditionFavoriteGameTopN.newList : ', newList, ' topN:', self.topn)

        gameIdStr = str(self.gameId)
        if gameIdStr not in newList:
            return False

        return newList.index(gameIdStr) < self.topn

    def decodeFromDict(self, d):
        self.gameId = d.get('gameId', -1)
        if not isinstance(self.gameId, (int, float)) or self.gameId < -1:
            raise TYBizConfException(d, 'UserConditionFavoriteGameTopN.gameId must be int >= -1')

        self.topn = d.get('topn', -1)
        if not isinstance(self.topn, (int, float)) or self.topn < -1:
            raise TYBizConfException(d, 'UserConditionFavoriteGameTopN.topn must be int >= -1')


class UserConditionGameTimeTopN(UserCondition):
    TYPE_ID = 'user.cond.game.time.topn'

    def __init__(self):
        super(UserConditionGameTimeTopN, self).__init__()
        self.gameId = None
        self.topn = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        info = hallaccount.getGameInfo(userId, clientId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionGameTimeTopN.check gameInfo:', info)

        dashifen = info.get('dashifen', {})
        newDict = {}
        for gameStr in dashifen:
            newDict[gameStr] = dashifen[gameStr].get('gameTime', 0)

        if ftlog.is_debug():
            ftlog.debug('UserConditionGameTimeTopN.newDict : ', newDict)

        newList = sorted(newDict.keys(), lambda x, y: cmp(newDict[x], newDict[y]), reverse=True)
        if ftlog.is_debug():
            ftlog.debug('UserConditionGameTimeTopN.newList : ', newList, ' topn:', self.topn)

        gameIdStr = str(self.gameId)
        if gameIdStr not in newList:
            return False

        return newList.index(gameIdStr) < self.topn

    def decodeFromDict(self, d):
        self.gameId = d.get('gameId', -1)
        if not isinstance(self.gameId, (int, float)) or self.gameId < -1:
            raise TYBizConfException(d, 'UserConditionGameTimeTopN.gameId must be int >= -1')

        self.topn = d.get('topn', -1)
        if not isinstance(self.topn, (int, float)) or self.topn < -1:
            raise TYBizConfException(d, 'UserConditionGameTimeTopN.topn must be int >= -1')


class UserConditionGameWinChipsTopN(UserCondition):
    TYPE_ID = 'user.cond.game.winchips.topn'

    def __init__(self):
        super(UserConditionGameWinChipsTopN, self).__init__()
        self.gameId = None
        self.topn = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        info = hallaccount.getGameInfo(userId, clientId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionGameWinChipsTopN.check gameInfo:', info)

        dashifen = info.get('dashifen', {})
        newDict = {}
        for gameStr in dashifen:
            newDict[gameStr] = dashifen[gameStr].get('winChips', 0)

        if ftlog.is_debug():
            ftlog.debug('UserConditionGameWinChipsTopN.newDict : ', newDict)

        newList = sorted(newDict.keys(), lambda x, y: cmp(newDict[x], newDict[y]), reverse=True)
        if ftlog.is_debug():
            ftlog.debug('UserConditionGameWinChipsTopN.newList : ', newList, ' topN: ', self.topn)

        gameIdStr = str(self.gameId)
        if gameIdStr not in newList:
            return False

        return newList.index(gameIdStr) < self.topn

    def decodeFromDict(self, d):
        self.gameId = d.get('gameId', -1)
        if not isinstance(self.gameId, (int, float)) or self.gameId < -1:
            raise TYBizConfException(d, 'UserConditionGameWinChipsTopN.gameId must be int >= -1')

        self.topn = d.get('topn', -1)
        if not isinstance(self.topn, (int, float)) or self.topn < -1:
            raise TYBizConfException(d, 'UserConditionGameWinChipsTopN.topn must be int >= -1')


class UserConditionGameMatchScoresTopN(UserCondition):
    TYPE_ID = 'user.cond.game.matchScores.topn'

    def __init__(self):
        super(UserConditionGameMatchScoresTopN, self).__init__()
        self.gameId = None
        self.topn = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        info = hallaccount.getGameInfo(userId, clientId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionGameMatchScoresTopN.check gameInfo:', info)

        dashifen = info.get('dashifen', {})
        newDict = {}
        for gameStr in dashifen:
            newDict[gameStr] = dashifen[gameStr].get('matchScores', 0)

        if ftlog.is_debug():
            ftlog.debug('UserConditionGameMatchScoresTopN.newDict : ', newDict)

        newList = sorted(newDict.keys(), lambda x, y: cmp(newDict[x], newDict[y]), reverse=True)
        if ftlog.is_debug():
            ftlog.debug('UserConditionGameMatchScoresTopN.newList : ', newList, ' topN:', self.topn)

        gameIdStr = str(self.gameId)
        if gameIdStr not in newList:
            return False

        return newList.index(gameIdStr) < self.topn

    def decodeFromDict(self, d):
        self.gameId = d.get('gameId', -1)
        if not isinstance(self.gameId, (int, float)) or self.gameId < -1:
            raise TYBizConfException(d, 'UserConditionGameMatchScoresTopN.gameId must be int >= -1')

        self.topn = d.get('topn', -1)
        if not isinstance(self.topn, (int, float)) or self.topn < -1:
            raise TYBizConfException(d, 'UserConditionGameMatchScoresTopN.topn must be int >= -1')


class UserConditionGameLoginSumTopN(UserCondition):
    TYPE_ID = 'user.cond.game.loginsum.topn'

    def __init__(self):
        super(UserConditionGameLoginSumTopN, self).__init__()
        self.gameId = None
        self.topn = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        info = hallaccount.getGameInfo(userId, clientId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionGameLoginSumTopN.check gameInfo:', info)

        dashifen = info.get('dashifen', {})
        newDict = {}
        for gameStr in dashifen:
            newDict[gameStr] = dashifen[gameStr].get('loginSum', 0)

        if ftlog.is_debug():
            ftlog.debug('UserConditionGameLoginSumTopN.newDict : ', newDict)

        newList = sorted(newDict.keys(), lambda x, y: cmp(newDict[x], newDict[y]), reverse=True)
        if ftlog.is_debug():
            ftlog.debug('UserConditionGameLoginSumTopN.newList : ', newList, ' topN: ', self.topn)

        gameIdStr = str(self.gameId)
        if gameIdStr not in newList:
            return False

        return newList.index(gameIdStr) < self.topn

    def decodeFromDict(self, d):
        self.gameId = d.get('gameId', -1)
        if not isinstance(self.gameId, (int, float)) or self.gameId < -1:
            raise TYBizConfException(d, 'UserConditionGameLoginSumTopN.gameId must be int >= -1')

        self.topn = d.get('topn', -1)
        if not isinstance(self.topn, (int, float)) or self.topn < -1:
            raise TYBizConfException(d, 'UserConditionGameLoginSumTopN.topn must be int >= -1')


class UserConditionCity(UserCondition):
    TYPE_ID = 'user.cond.city'

    def __init__(self):
        super(UserConditionCity, self).__init__()
        self.city = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        c = sessiondata.getCityName(userId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionCity.check userCity: ', c, ' city:', self.city)
        return self.city == c

    def decodeFromDict(self, d):
        self.city = d.get('city', '全国')
        if not isstring(self.city):
            raise TYBizConfException(d, 'UserConditionCity.city must be string')


class UserConditionForbiddenCitys(UserCondition):
    TYPE_ID = 'user.cond.forbidden.citys'

    def __init__(self):
        super(UserConditionForbiddenCitys, self).__init__()
        self.citys = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        c = sessiondata.getCityName(userId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionForbiddenCitys.check userCity: ', c, ' citys:', self.citys)
        return c not in self.citys

    def decodeFromDict(self, d):
        self.citys = d.get('citys', [])
        if not isinstance(self.citys, list):
            raise TYBizConfException(d, 'UserConditionForbiddenCitys.citys must be list')


class UserConditionCitys(UserCondition):
    TYPE_ID = 'user.cond.citys'

    def __init__(self):
        super(UserConditionCitys, self).__init__()
        self.citys = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        c = sessiondata.getCityName(userId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionCitys.check userCity: ', c, ' citys:', self.citys)
        return c in self.citys

    def decodeFromDict(self, d):
        self.citys = d.get('citys', [])
        if not isinstance(self.citys, list):
            raise TYBizConfException(d, 'UserConditionCitys.citys must be list')


class UserConditionHasUnSendTuyooRedenvelope(UserCondition):
    TYPE_ID = 'user.cond.unsend.tuyoo.redenvelope'

    def __init__(self):
        super(UserConditionHasUnSendTuyooRedenvelope, self).__init__()
        self.type = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        from hall.entity import hallconf
        from poker.entity.game.game import TYGame

        gameids = hallconf.getDaShiFenFilter(clientId)
        for gid in gameids:
            shareInfo = TYGame(gid).getTuyooRedEnvelopeShareTask(userId, clientId, self.type)
            if ftlog.is_debug():
                ftlog.debug('UserConditionHasUnSendTuyooRedenvelope.check gameId:', gid, ' shareInfo:', shareInfo)

            if shareInfo:
                return True
        return False

    def decodeFromDict(self, d):
        self.type = d.get('type', '')


class UserConditionOS(UserCondition):
    TYPE_ID = 'user.cond.os'

    def __init__(self):
        super(UserConditionOS, self).__init__()
        self.os = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        clientOS, _, _ = strutil.parseClientId(clientId)
        if ftlog.is_debug():
            ftlog.debug('UserConditionOS.check os:', self.os,
                        ' clientOS:', clientOS)

        return clientOS == self.os

    def decodeFromDict(self, d):
        self.os = d.get('os', '')
        if not isstring(self.os):
            raise TYBizConfException(d, 'UserConditionOS.os must be string')


class UserConditionFalse(UserCondition):
    TYPE_ID = 'user.cond.false'

    def __init__(self):
        super(UserConditionFalse, self).__init__()

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        return False

    def decodeFromDict(self, d):
        return self


class UserConditionDateTime(UserCondition):
    TYPE_ID = 'user.cond.datetime'

    def __init__(self):
        super(UserConditionDateTime, self).__init__()
        self.start = None
        self.end = None
        self.format = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        return self.start <= timestamp <= self.end

    def decodeFromDict(self, d):
        self.format = d.get('format')
        self.start = time.mktime(time.strptime(d.get('start'), self.format))
        self.end = time.mktime(time.strptime(d.get('end'), self.format))
        return self


class UserConditionUnGotLoginReward(UserCondition):
    TYPE_ID = 'user.cond.ungot.loginReward'

    def __init__(self):
        super(UserConditionUnGotLoginReward, self).__init__()
        self.start = None
        self.end = None

    def check(self, gameId, userId, clientId, timestamp, **kwargs):
        loginReward = gamedata.getGameAttrInt(userId, HALL_GAMEID, 'login_reward')
        ftlog.debug('UserConditionUnGotLoginReward.check start:', self.start
                    , ' end:', self.end
                    , ' loginReward:', loginReward)
        if self.start <= loginReward <= self.end:
            return False
        return True

    def decodeFromDict(self, d):
        self.start = time.mktime(time.strptime(d.get('start'), '%Y-%m-%d %H:%M:%S'))
        self.end = time.mktime(time.strptime(d.get('end'), '%Y-%m-%d %H:%M:%S'))
        return self


class UserConditionRegister(TYConfableRegister):
    _typeid_clz_map = {
        # AND条件
        UserConditionAND.TYPE_ID: UserConditionAND,
        # OR条件
        UserConditionOR.TYPE_ID: UserConditionOR,
        # 非条件
        UserConditionNOT.TYPE_ID: UserConditionNOT,
        # 已首冲
        UserConditionFirstRecharged.TYPE_ID: UserConditionFirstRecharged,
        # clientId中的gameId是否与我的gameId一致
        UserConditionisMyGameid.TYPE_ID: UserConditionisMyGameid,
        # 未首冲
        UserConditionUnFirstRecharged.TYPE_ID: UserConditionUnFirstRecharged,
        # 已领取首冲奖励
        UserConditionGotFirstRechargeReward.TYPE_ID: UserConditionGotFirstRechargeReward,
        # 没有领取首冲奖励
        UserConditionUnGotFirstRechargeReward.TYPE_ID: UserConditionUnGotFirstRechargeReward,
        # VIP级别
        UserConditionVipLevel.TYPE_ID: UserConditionVipLevel,
        # 奖券携带量
        UserConditionCoupon.TYPE_ID: UserConditionCoupon,
        # 金币携带量
        UserConditionChip.TYPE_ID: UserConditionChip,
        # 性别
        UserConditionSex.TYPE_ID: UserConditionSex,
        # 注册天数
        UserConditionRegisterDay.TYPE_ID: UserConditionRegisterDay,
        # 新用户
        UserConditionNewUser.TYPE_ID: UserConditionNewUser,
        # 是订阅会员
        UserConditionIsSubscribeMember.TYPE_ID: UserConditionIsSubscribeMember,
        # 是会员但不是订阅会员
        UserConditionIsMemberNotSub.TYPE_ID: UserConditionIsMemberNotSub,
        # 非订阅会员
        UserConditionNotSubscribeMember.TYPE_ID: UserConditionNotSubscribeMember,
        # 会员剩余天数
        UserConditionMemberRemDays.TYPE_ID: UserConditionMemberRemDays,
        # 日期判断
        UserConditionTimePeriod.TYPE_ID: UserConditionTimePeriod,
        # 支付至少一次
        UserConditionPayLeastOnce.TYPE_ID: UserConditionPayLeastOnce,
        # 已绑定手机号
        UserConditionBindPhone.TYPE_ID: UserConditionBindPhone,
        # 本日无签到
        UserConditionNotCheckInToday.TYPE_ID: UserConditionNotCheckInToday,
        # 本日已签到
        UserConditionCheckedInToday.TYPE_ID: UserConditionCheckedInToday,
        # 是否有签到奖励
        UserConditionCheckInHasReward.TYPE_ID: UserConditionCheckInHasReward,
        # 是否有抽奖卡
        UserConditionHasLuckyCard.TYPE_ID: UserConditionHasLuckyCard,
        # 是会员
        UserConditionIsMember.TYPE_ID: UserConditionIsMember,
        # 不是会员
        UserConditionNotIsMember.TYPE_ID: UserConditionNotIsMember,
        # 有会员充值弹窗
        UserConditionHasMemberBuyWindow.TYPE_ID: UserConditionHasMemberBuyWindow,
        # 有会员奖励
        UserConditionHasMemberReward.TYPE_ID: UserConditionHasMemberReward,
        # 有任务奖励
        UserConditionHasTaskReward.TYPE_ID: UserConditionHasTaskReward,
        # 任务完成
        UserConditionTaskAllDone.TYPE_ID: UserConditionTaskAllDone,
        # 没有五星好评
        UserConditionNotFiveStar.TYPE_ID: UserConditionNotFiveStar,
        # 有可补签天数
        UserConditionHasSupCheckinDay.TYPE_ID: UserConditionHasSupCheckinDay,
        # 是否有分享奖励
        UserConditionHasDailyShareReward.TYPE_ID: UserConditionHasDailyShareReward,
        # 是否有免费福利小红点
        UserConditionHasFreeMark.TYPE_ID: UserConditionHasFreeMark,
        # 是否有每日分享配置
        UserConditionHasDailyShareConfig.TYPE_ID: UserConditionHasDailyShareConfig,
        # clientIds的版本号
        UserConditionClientVersion.TYPE_ID: UserConditionClientVersion,
        # 非每日第一次登录
        UserConditionNotDayFirstLogin.TYPE_ID: UserConditionNotDayFirstLogin,
        # 每日第一次登陆
        UserConditionDayFirstLogin.TYPE_ID: UserConditionDayFirstLogin,
        # 充值总额
        UserConditionChargeTotal.TYPE_ID: UserConditionChargeTotal,
        # 登录天数取摸
        UserConditionsignDayMod.TYPE_ID: UserConditionsignDayMod,
        # 用户的支付次数
        UserConditionPayCount.TYPE_ID: UserConditionPayCount,
        # 没有支付
        UserConditionNonPay.TYPE_ID: UserConditionNonPay,
        # 时间段
        UserConditionTimeInToday.TYPE_ID: UserConditionTimeInToday,
        # 用户当前在哪个大厅游戏中
        UserConditionInWhichGame.TYPE_ID: UserConditionInWhichGame,
        # 用户最喜欢的游戏 大师分TOPN
        UserConditionFavoriteGameTopN.TYPE_ID: UserConditionFavoriteGameTopN,
        # 用户地区
        UserConditionCity.TYPE_ID: UserConditionCity,
        # 用户在某地区集合内
        UserConditionCitys.TYPE_ID: UserConditionCitys,
        # 用户在某个禁止地区集合内
        UserConditionForbiddenCitys.TYPE_ID: UserConditionForbiddenCitys,
        # 插件游戏时长TOPN
        UserConditionGameTimeTopN.TYPE_ID: UserConditionGameTimeTopN,
        # 用户赢取金币TOPN
        UserConditionGameWinChipsTopN.TYPE_ID: UserConditionGameWinChipsTopN,
        # loginSum 用户登录插件游戏的次数TOPN
        UserConditionGameLoginSumTopN.TYPE_ID: UserConditionGameLoginSumTopN,
        # 用户在插件游戏的比赛积分TOPN
        UserConditionGameMatchScoresTopN.TYPE_ID: UserConditionGameMatchScoresTopN,
        # 用户的clientId是否在特定的列表内
        UserConditionInClientIDs.TYPE_ID: UserConditionInClientIDs,
        # 用户的clientIds不在禁止列表内
        UserConditionNotInClientIDs.TYPE_ID: UserConditionNotInClientIDs,
        # 用户有未发送的途游红包
        UserConditionHasUnSendTuyooRedenvelope.TYPE_ID: UserConditionHasUnSendTuyooRedenvelope,
        # 用户的登录天数
        UserConditionLoginDays.TYPE_ID: UserConditionLoginDays,
        # 用户的累计游戏时长
        UserConditionPlayTime.TYPE_ID: UserConditionPlayTime,
        # 用户的分享次数
        UserConditionShareCount.TYPE_ID: UserConditionShareCount,
        # 用户本次登录与上次登录的时间差
        UserConditionReturnTime.TYPE_ID: UserConditionReturnTime,
        # 判断用户的操作系统
        UserConditionOS.TYPE_ID: UserConditionOS,
        # 福利时间，某段时间内第一次登录
        UserConditionBenefitsTime.TYPE_ID: UserConditionBenefitsTime,
        # 始终返回False的条件
        UserConditionFalse.TYPE_ID: UserConditionFalse,
        # 指定时间范围
        UserConditionDateTime.TYPE_ID: UserConditionDateTime,
        # 指定的时间段内没有领取登录奖励
        UserConditionUnGotLoginReward.TYPE_ID: UserConditionUnGotLoginReward,
    }
