# -*- coding=utf-8 -*-
'''
'''
__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
    'Wangtao'
]

import functools
from functools import wraps
from itertools import izip, ifilter, ifilterfalse

from datetime import date, datetime, timedelta
from dateutil import parser

import freetime.util.log as ftlog
from freetime.core.timer import FTTimer
from freetime.entity.msg import MsgPack
from hall.entity import hallvip
from poker.entity.configure import pokerconf, gdata, configure
from poker.entity.dao import onlinedata
from poker.entity.dao import userdata, userchip, sessiondata, gamedata
from poker.protocol import router
from poker.util import strutil


def getOnlineLoc(userId, gameId, roomId=0, tableId=0, locList=None):
    if not locList:
        locList = onlinedata.getOnlineLocList(userId)

    for onlineLoc in locList:
        if gameId != strutil.getGameIdFromInstanceRoomId(onlineLoc[0]):
            continue

        if roomId == 0:
            return onlineLoc

        if gdata.getBigRoomId(onlineLoc[0]) == gdata.getBigRoomId(roomId):
            if tableId == 0:
                return onlineLoc

            if onlineLoc[1] == tableId:
                return onlineLoc

    return [0, 0, 0]


def getOldOnlineLoc(userId, gameId):
    '''
    获取老的loc字段，现在还没有实现多游戏，先从获取的list里取第一个
    多游戏todo
    '''
    onlineLoc = getOnlineLoc(userId, gameId)
    onlineLoc.insert(0, gameId)
    return onlineLoc


def buildColorText(*segs):
    return [dict(zip(("color", "text"), segment)) for segment in segs]


def sendNotifyMsg(gameId, uid, showTime, content):
    """
    {
        "cmd": "notifyMsg",
        "result":
        {
            "showTime": 0.5,
            "content": [{
                "color": "RRGGBB",
                "text": "bababababa"
            }, {
                "color": "RRGGBB",
                "text": "bababababa"
            }]
        }
    }
    """

    msg_content = [dict(zip(("color", "text"), segment)) for segment in content]

    message = MsgPack()
    message.setCmd('notifyMsg')
    message.setResult("userId", uid)
    message.setResult("gameId", gameId)
    message.setResult("showTime", showTime)
    message.setResult("content", msg_content)

    router.sendToUser(message, uid)


def updateMsg(msg=None, cmd=None, params=None, result=None):
    if not msg:
        msg = MsgPack()
    if cmd:
        msg.setCmd(cmd)
    if params is not None:
        msg.setKey('params', params)
    if result is not None:
        msg.setKey('result', result)

    return msg


def mkdict(**kwargs):
    return kwargs


def sendMessage(gameId, targetUserIds, cmd, result, printLog=False):
    if isinstance(targetUserIds, int):
        targetUserIds = [targetUserIds]
    msg = updateMsg(cmd=cmd, result=result)
    msg.setResult('gameId', gameId)
    if printLog:
        ftlog.info('|to targetUserIds:', targetUserIds, '|msg:', msg)
    router.sendToUsers(msg, targetUserIds)


def dict2obj(_dict):
    class Blank(object): pass

    blankObj = Blank()
    blankObj.__dict__ = _dict
    return blankObj


def obj2dict(obj):
    return obj.__dict__


def getTotalChip(userId, gameId, tableId):
    user_chip = userchip.getChip(userId)
    if tableId == 0:
        table_chip = sum([pair[1] for pair in pairwise(userchip.getTableChipsAll(userId))])
        # table_chip = 0
        # for index, v in enumerate(userchip.getTableChipsAll(userId)):
        #    if index % 2:
        #        table_chip += v
    else:
        table_chip = userchip.getTableChip(userId, gameId, tableId)
    return user_chip + table_chip


class MaxInt(int):
    '''recommend sys.maxint
    '''

    def __gt__(self, other):
        return True


def consumeEmoticonNameToBIEventId(ename):
    numDict = {
        'egg': pokerconf.biEventIdToNumber("EMOTICON_EGG_CONSUME"),
        'bomb': pokerconf.biEventIdToNumber("EMOTICON_BOMB_CONSUME"),
        'flower': pokerconf.biEventIdToNumber("EMOTICON_FLOWER_CONSUME"),
        'diamond': pokerconf.biEventIdToNumber("EMOTICON_DIAMOND_CONSUME"),

        'eggs': pokerconf.biEventIdToNumber("EMOTICON_EGG_CONSUME"),
        'rose': pokerconf.biEventIdToNumber("EMOTICON_FLOWER_CONSUME"),
        'ring': pokerconf.biEventIdToNumber("EMOTICON_DIAMOND_CONSUME"),
    }
    num = numDict.get(ename, pokerconf.biEventIdToNumber("UNKNOWN"))

    return num


def logTableChat(gameId, roomId, tableId, senderUserId, chatText):
    if not chatText:
        return
    if senderUserId <= 0:
        return
    try:
        username = unicode(str(userdata.getAttr(senderUserId, 'name')))
        roomName = unicode(str(gdata.getRoomConfigure(roomId)['name']))
        ftlog.hinfo('tableChatLog gameId=%s; room="%s"; table=%s; userId=%s; name="%s"; msg="%s"' % (
            gameId, roomName, tableId, senderUserId, username, chatText))
    except Exception, e:
        ftlog.exception('exception locals():', locals())


def pstruct(idata):
    try:
        odata = idata.encode('utf-8')
    except:
        odata = idata
    return odata


def isplit(predicate, iterable):
    """ 返回按 predicate 为 True 和 False 分开的两组 """
    return ifilter(predicate, iterable), ifilterfalse(predicate, iterable)


def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)


def safemethod(method):
    @wraps(method)
    def safetyCall(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except:
            ftlog.exception()

    return safetyCall


def isNewUser(userId, gameId):
    # 区别新老玩家
    isToday = False
    createTime = gamedata.getGameAttr(userId, gameId, 'createTime')

    if not createTime:
        return isToday
    else:
        isToday = date.fromtimestamp(int(createTime)) == date.today()
        return isToday


def callLater(delay, func, *args, **keywords):
    '''
    用FTTimer实现的callLater
    '''
    if ftlog.is_debug():
        ftlog.debug('args', args)
        ftlog.debug('timedelay', delay)
        ftlog.debug('callable', callable(func))
    func = functools.partial(func, *args, **keywords)
    return FTTimer(delay, func)


def lazyCall(funcs):
    for func in funcs:
        yield func()


def photoConvert(photo, userId=0, clientVer=0.0):
    """
    转换头像，让新老版本在相遇时能正确显示对方头像。

    userId: 头像接收者的 userId
    clientVer: 头像接收者的 clientVer
    """

    if not photo:
        ftlog.error("error header photo", photo)
        return photo

    if not userId and not clientVer:
        return photo

    if not clientVer:
        clientVer = sessiondata.getClientIdVer(userId)

    if not clientVer:
        return photo

    newClient = clientVer >= 1.9

    old_to_new = {
        'head_01.png': 'head_360_01.png',
        'head_02.png': 'head_du.png',
        'head_03.png': 'head_360_02.png',
        'head_04.png': 'head_360_03.png',
        'head_05.png': 'head_360_04.png',
        'head_06.png': 'head_hanhou.png',
        'head_07.png': 'head_360_05.png',
        'head_08.png': 'head_360_06.png',
        'head_09.png': 'head_360_07.png',
        'head_10.png': 'head_360_07.png',  # 重复使用。
        'head_11.png': 'head_360_08.png',
        'head_12.png': 'head_360_09.png',
        'head_13.png': 'head_360_10.png',
        'head_14.png': 'head_360_11.png',
        'head_15.png': 'head_360_12.png',
    }

    new_to_old = dict(zip(old_to_new.values(), old_to_new.keys()))

    if newClient:
        if photo in new_to_old:
            return photo
        elif photo in old_to_new:
            return old_to_new[photo]
        else:
            return photo
    else:
        if photo in new_to_old:
            return new_to_old[photo]
        elif photo in old_to_new:
            return photo
        else:
            return photo

    return photo


def inToday(lastTimeStr, dayStartTime):
    """
    检查当前时间与上次操作时间是不是在"同一天"。

    为了提高性能，创建了一个全局的 dayStartTimeMap，用来缓存由 dayStartTime 生
    成的两个 time str

    lastTimeStr: 最后一次记录数据的时间：示例："2014 06 10 22 33 44"
    dayStartTime: “天”的开始点。如：(22, 33, 44) 表示 22:33:44 为一天的开始点
    """

    if not lastTimeStr:
        return True

    hour, minute, second = dayStartTime
    now = datetime.now()
    tmptime = datetime(now.year, now.month, now.day, hour, minute, second)
    if now < tmptime:
        day_beg = tmptime + timedelta(days=-1)
    else:
        day_beg = tmptime

    day_end = day_beg + timedelta(days=1)
    day_beg_str = day_beg.strftime("%Y %m %d %H %M %S")
    day_end_str = day_end.strftime("%Y %m %d %H %M %S")

    return day_beg_str <= lastTimeStr < day_end_str


def n2wan(n, points=2):
    ''' 转换一个数到字符串描述 '''
    if n > 10000:
        formatter = '%%.%df' % points
        s = formatter % (float(n) / 10000)
        return s.rstrip('0').rstrip('.') + u'万'
    return str(n)


def module_bridge_to_class(names, namespace={}):
    '''转换module函数为类方法'''

    def _de(_class):
        for name in names:
            setattr(_class, name, namespace[name])
        return _class

    return _de


def runAsDebugMode():
    return gdata.mode() not in (gdata.RUN_MODE_ONLINE, gdata.RUN_MODE_SIMULATION)


def reload_mod(module):
    import sys, importlib
    module_name = module.__name__
    old_mod = sys.modules.get(module_name)
    if old_mod:
        del sys.modules[module_name]
    module = importlib.import_module(module_name)
    reload(module)
    return module


def isColdUser(userId):
    '''判断是否冷用户'''
    userdatas = userdata.getAttrs(userId, ['userId', 'createTime', 'name'])
    return None in userdatas


def isOpenTime(openTimeConfig):
    if not openTimeConfig:
        return True

    beginDay = parser.parse(openTimeConfig.get('begin_day', "19700101"))
    endDay = parser.parse(openTimeConfig.get('end_day', "99991231"))
    now = datetime.now()

    if not (beginDay.date() <= now.date() <= endDay.date()):
        return False

    weekDays = set(map(int, openTimeConfig.get('week', "1,2,3,4,5,6,7").split(',')))
    if (now.weekday() + 1) not in weekDays:  # datetime.weekday(): 周1=0, ..., 周日 = 6
        return False

    timePeriods = openTimeConfig.get('time_periods', [])
    if not timePeriods:
        return True

    for timePeriod in timePeriods:
        beginTime = parser.parse(timePeriod[0])
        endTime = parser.parse(timePeriod[1])
        # 注意 visibleBeginTime 和 visibleEndTime 由 dateutil.parser 解析而来，是个 datetime
        #  date 是当天的。如果时间到了第二天，则这个判断为假:
        # if mconf['visibleBeginTime'] <= datetime.now() <= mconf['visibleEndTime']:
        # 所以改为：
        if beginTime.time() <= now.time() <= endTime.time():
            return True

    return False


def getLuckyChipByVip(userId, gameId):
    vipLevel = hallvip.userVipSystem.getUserVip(userId).vipLevel.level
    luckyChipsByVip = configure.getGameJson(gameId, 'lead_to_pay')['luckyChipsByVip']
    if vipLevel < len(luckyChipsByVip):
        return luckyChipsByVip[vipLevel]
    else:
        return luckyChipsByVip[-1]
