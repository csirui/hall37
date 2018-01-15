# -*- coding=utf-8 -*-

'''
Created on 2014年2月20日

@author: zjgzzz@126.com
'''
import time

from freetime.util import log as ftlog
from freetime.util.metaclasses import Singleton


class TYEvent(object):
    '''
    事件基类
    '''

    def __init__(self):
        self.timestamp = int(time.time())


class EventConfigure(TYEvent):
    '''
    当配置信息发生变化时, 触发此事件, 
    '''

    def __init__(self, keylist, reloadlist):
        super(EventConfigure, self).__init__()
        self.keylist = set(keylist)
        self.reloadlist = reloadlist
        self.modules = []
        for k in self.keylist:
            if k == 'all':
                self.modules = ['all']
                break
            else:
                if k.startswith('game'):
                    ks = k.split(':')
                    self.modules.append(ks[2])
                else:
                    self.modules.append(k)
        ftlog.debug('EventConfigure->self.modules=', self.modules)

    def isModuleChanged(self, keys):
        if 'all' in self.modules:
            return True
        if isinstance(keys, (list, set)):
            for key in keys:
                if key in self.modules:
                    return True
            return False
        return keys in self.modules

    def isChanged(self, keys):
        if 'all' in self.keylist:
            return True
        if isinstance(keys, (list, set)):
            for key in keys:
                if key in self.keylist:
                    return True
            return False
        return keys in self.keylist


class EventHeartBeat(TYEvent):
    '''
    每秒钟系统服务心跳处理
    每秒钟一次的心跳事件广播, 执行之后间隔一秒再次启动, 即: 这个每秒心跳是个大约值,非准确值
    '''
    __metaclass__ = Singleton
    count = 0

    def __init__(self):
        super(EventHeartBeat, self).__init__()


class UserEvent(TYEvent):
    def __init__(self, userId, gameId):
        super(UserEvent, self).__init__()
        self.__gameId = gameId
        self.__userId = userId

    @property
    def gameId(self):
        return self.__gameId

    @property
    def userId(self):
        return self.__userId


# class EventUserAttrsChanged(UserEvent):
#     '''
#     用户的基本属性发生变化, 例如 昵称, 性别
#     由Account.updateUserBaseInfo方法发送至全局globalEventBus
#     用途举例: 斗牛的修改昵称送金币的业务逻辑
#     '''
#     def __init__(self, userId, attNameList):
#         super(EventUserAttrsChanged, self).__init__(userId, 0)
#         self.attNameList = attNameList


class EventUserLogin(UserEvent):
    '''
    用户登录一个游戏的事件
    由Account.loginGame方法发送至游戏实例的tygame.getEventBus()
    '''

    def __init__(self, userId, gameId, dayFirst, isCreate, clientId):
        super(EventUserLogin, self).__init__(userId, gameId)
        self.dayFirst = dayFirst
        self.isCreate = isCreate
        self.clientId = clientId


class MatchEvent(UserEvent):
    def __init__(self, userId, gameId, matchId):
        super(MatchEvent, self).__init__(userId, gameId)
        self.__matchId = matchId

    @property
    def matchId(self):
        return self.__matchId


class MatchPlayerEvent(MatchEvent):
    def __init__(self, userId, gameId, matchId, player):
        super(MatchPlayerEvent, self).__init__(userId, gameId, matchId)
        self.player = player


class MatchPlayerSigninEvent(MatchPlayerEvent):
    def __init__(self, userId, gameId, matchId, player):
        super(MatchPlayerSigninEvent, self).__init__(userId, gameId, matchId, player)


class MatchPlayerSignoutEvent(MatchPlayerEvent):
    def __init__(self, userId, gameId, matchId, player):
        super(MatchPlayerSignoutEvent, self).__init__(userId, gameId, matchId, player)


class MatchPlayerOverEvent(MatchPlayerEvent):
    def __init__(self, userId, gameId, matchId, player, reason, rankRewards):
        super(MatchPlayerOverEvent, self).__init__(userId, gameId, matchId, player)
        self.reason = reason
        self.rankRewards = rankRewards


class MatchWinloseEvent(MatchEvent):
    def __init__(self, userId, gameId, matchId, isWin, rank, signinUserCount, rewards=None):
        super(MatchWinloseEvent, self).__init__(userId, gameId, matchId)
        self.__isWin = isWin
        self.__rank = rank
        self.__signinUserCount = signinUserCount
        self.rewards = rewards

    @property
    def isWin(self):
        return self.__isWin

    @property
    def rank(self):
        return self.__rank

    @property
    def signinUserCount(self):
        return self.__signinUserCount


class DataChangeEvent(UserEvent):
    def __init__(self, userId, gameId, reason):
        super(DataChangeEvent, self).__init__(userId, gameId)
        self.__dataType = []
        self.__reason = reason

    def addDataType(self, dataType):
        if isinstance(dataType, (list, set)):
            self.__dataType.extend(dataType)
        else:
            self.__dataType.append(dataType)
        return self

    @property
    def dataTypes(self):
        return self.__dataType

    @property
    def reason(self):
        return self.__reason


class DelvieryProduct(UserEvent):
    def __init__(self, userId, gameId, productId, count, buyGameId=0):
        super(DelvieryProduct, self).__init__(userId, gameId)
        self.productId = productId
        self.buyGameId = buyGameId or gameId


class RaffleEvent(DelvieryProduct):
    def __init__(self, userId, gameId, productId, count, buyGameId=0):
        super(RaffleEvent, self).__init__(userId, gameId, productId, count, buyGameId)


class ItemUsedEvent(UserEvent):
    def __init__(self, userId, gameId, itemUseResult):
        super(ItemUsedEvent, self).__init__(userId, gameId)
        self.itemUseResult = itemUseResult


class OnLineTcpChangedEvent(UserEvent):
    def __init__(self, userId, gameId, isOnline):
        super(OnLineTcpChangedEvent, self).__init__(userId, gameId)
        self.isOnline = isOnline


class OnLineGameChangedEvent(UserEvent):
    def __init__(self, userId, gameId, isEnter, clientId=None):
        super(OnLineGameChangedEvent, self).__init__(userId, gameId)
        self.isEnter = isEnter
        self.clientId = clientId


class OnLineRoomChangedEvent(UserEvent):
    def __init__(self, userId, gameId, roomId, isEnter):
        super(OnLineRoomChangedEvent, self).__init__(userId, gameId)
        self.roomId = roomId
        self.isEnter = isEnter


class OnLineAttrChangedEvent(UserEvent):
    def __init__(self, userId, gameId, attName, attFinalValue, attDetalValue):
        super(OnLineAttrChangedEvent, self).__init__(userId, gameId)
        self.attName = attName
        self.attFinalValue = attFinalValue
        self.attDetalValue = attDetalValue


class ModuleTipEvent(UserEvent):
    def __init__(self, userId, gameId, name, count=1):
        super(ModuleTipEvent, self).__init__(userId, gameId)
        self.name = name
        self.count = count


class ChargeNotifyEvent(UserEvent):
    def __init__(self, userId, gameId, rmbs, diamonds, productId, clientId):
        super(ChargeNotifyEvent, self).__init__(userId, gameId)
        self.rmbs = rmbs
        self.diamonds = diamonds
        self.productId = productId
        self.clientId = clientId


class ActivityEvent(TYEvent):
    def __init__(self, userId, gameId, clientId, attrDict={}):
        super(ActivityEvent, self).__init__()
        self.userId = userId
        self.gameId = gameId
        self.clientId = clientId
        self.attrDict = attrDict  # 事件属性dict

    def get(self, attr):
        if hasattr(self, attr):
            return getattr(self, attr)
        else:
            return self.attrDict.get(attr, None)


class GameOverEvent(ActivityEvent):
    def __init__(self, userId, gameId, clientId, roomId, tableId,
                 gameResult, roomLevel=0, role="", roundNum=1, attrDict={}):
        super(GameOverEvent, self).__init__(userId, gameId, clientId, attrDict)
        self.roomId = roomId
        self.tableId = tableId
        self.gameResult = gameResult  # 整数, 0 tie 1 win -1 lose
        self.role = role  # 字符串, "landlord"
        self.roomLevel = roomLevel  # 整数
        self.roundNum = roundNum  # 玩了几局


class TableStandUpEvent(UserEvent):
    '''
    当用户离开座位,站起时,发送此事件
    在此事件的监听者中, 处理例如: 江湖救急, 救济金发放, 购买金币提示等信息
    '''
    REASON_USER_CLICK_BUTTON = 0  # 表示用户主动调用，离开桌子
    REASON_TCP_CLOSED = 1  # 网络系统短线，系统踢出，离开桌子
    REASON_READY_TIMEOUT = 2  # ready超时，系统踢出，离开桌子
    REASON_GAME_ABORT = 3  # 牌桌流局，全部托管状态下，系统踢出，离开桌子
    REASON_CHIP_NOT_ENOUGHT = 4  # 游戏币不够，系统踢出，离开桌子
    REASON_CHIP_TOO_MUCH = 5  # 游戏币太多了，系统踢出，离开桌子
    REASON_MATCH_AUTO = 6  # 比赛，服务器自动换桌子
    REASON_GAME_OVER = 7  # 正常牌局结束
    REASON_SYSTEM_SHUTDOWN = 99  # 系统维护，踢出，关闭房间

    def __init__(self, userId, gameId, roomId, tableId, reason):
        super(TableStandUpEvent, self).__init__(userId, gameId)
        assert (reason in (self.REASON_USER_CLICK_BUTTON, self.REASON_TCP_CLOSED,
                           self.REASON_READY_TIMEOUT, self.REASON_GAME_ABORT,
                           self.REASON_CHIP_NOT_ENOUGHT, self.REASON_CHIP_TOO_MUCH,
                           self.REASON_MATCH_AUTO, self.REASON_SYSTEM_SHUTDOWN,
                           self.REASON_GAME_OVER))
        self.roomId = roomId
        self.tableId = tableId
        self.reason = reason


class ItemCountChangeEvent(TYEvent):
    '''
    道具数量变化
    '''

    def __init__(self, userId):
        super(ItemCountChangeEvent, self).__init__()
        self.userId = userId


class BetOnEvent(UserEvent):
    """
    小游戏下注事件
    """

    def __init__(self, userId, gameId, amount):
        super(BetOnEvent, self).__init__(userId, gameId)
        self.amount = amount
