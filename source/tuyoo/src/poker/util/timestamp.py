# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import time

from datetime import datetime, timedelta
from dateutil import relativedelta


def getDeltaMonthStartTimestamp(timestamp=None, deltamonth=0):
    '''
    获取timestamp所在时间nmonth前后个月的开始时间，nmonth=0表示当前月, -1表示前一个月, 1表示下一个月
    '''
    if timestamp is None:
        timestamp = int(time.time())
    dt = datetime.fromtimestamp(timestamp)
    delta = relativedelta.relativedelta(months=deltamonth)
    dt = dt + delta
    dt = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return time.mktime(dt.timetuple())


def getMonthStartTimestamp(timestamp=None):
    '''
    获取timestamp所在时间当前月的开始时间
    '''
    return getDeltaMonthStartTimestamp(timestamp, 0)


def getWeekStartTimestamp(timestamp=None):
    '''
    获取timestamp这个时间所在周的开始时间
    '''
    if timestamp is None:
        timestamp = int(time.time())
    dt = datetime.fromtimestamp(timestamp)
    return (timestamp - dt.date().weekday() * 86400 -
            dt.hour * 3600 - dt.minute * 60 - dt.second)


def getDayLeftSeconds(timestamp=None):
    '''
    获取timestamp这个时间到timestamp所在的天结束时的秒数
    '''
    return 86400 - getDayPastSeconds(timestamp)


def getDayPastSeconds(timestamp=None):
    '''
    今日零点到现在过去的秒数
    '''
    if timestamp is None:
        timestamp = int(time.time())
    nt = time.localtime(timestamp)
    return nt[3] * 3600 + nt[4] * 60 + nt[5]


def getDayStartTimestamp(timestamp=None):
    '''
    获取timestamp这个时间戳
    '''
    if timestamp is None:
        timestamp = int(time.time())
    return int(timestamp) - getDayPastSeconds(timestamp)


def getHourStartTimestamp(timestamp=None):
    '''
    获取timestamp这个时间戳
    '''
    if timestamp is None:
        timestamp = int(time.time())
    dt = datetime.fromtimestamp(timestamp).replace(minute=0, second=0, microsecond=0)
    return time.mktime(dt.timetuple())


def getCurrentWeekStartTimestamp(timestamp=None):
    ''' 
    获取本周开始的时间戳，本周开始的时间点，到当前时间的秒数
    '''
    if timestamp is None:
        timestamp = int(time.time())
    td = datetime.fromtimestamp(timestamp)
    return (timestamp - td.weekday() * 86400 -
            td.hour * 3600 - td.minute * 60 - td.second)


def getCurrentDayLeftSeconds():
    '''
    获取当前时间开始，到本天结束时的秒数
    '''
    nt = time.localtime()
    ntsec = 86400 - nt[3] * 3600 + nt[4] * 60 + nt[5]
    return ntsec


# 单位秒 s
def getCurrentTimestamp():
    '''
    获取当前时间戳 int (unit: second)
    '''
    return int(time.time())


def getCurrentTimestampFloat():
    '''
    获取当前时间戳 float (unit: second)
    '''
    return time.time()


def getTimeStrDiff(start, end):
    ''' 
    获取两个时间字符串的时间差，end-start，单位为秒
    时间字符串格式:%Y-%m-%d %H:%M:%S.%f
    '''
    t1 = datetime.strptime(start, '%Y-%m-%d %H:%M:%S.%f')
    t2 = datetime.strptime(end, '%Y-%m-%d %H:%M:%S.%f')
    diff = t2 - t1
    return diff.days * 86400 + diff.seconds


def formatTimeMs(ct=None):
    '''
    获取当前时间字符串:%Y-%m-%d %H:%M:%S.%f
    '''
    if ct == None:
        ct = datetime.now()
    ctfull = ct.strftime('%Y-%m-%d %H:%M:%S.%f')
    return ctfull


def parseTimeMs(timestr):
    '''
    解析当前时间字符串:%Y-%m-%d %H:%M:%S.%f
    '''
    return datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S.%f')


def formatTimeSecond(ct=None):
    '''
    获取当前时间字符串:%Y-%m-%d %H:%M:%S
    '''
    if ct == None:
        ct = datetime.now()
    ctfull = ct.strftime('%Y-%m-%d %H:%M:%S')
    return ctfull


def parseTimeSecond(timestr):
    '''
    解析当前时间字符串:%Y-%m-%d %H:%M:%S
    '''
    return datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')


def formatTimeMinute(ct=None):
    '''
    获取当前时间字符串:%Y-%m-%d %H:%M
    '''
    if ct == None:
        ct = datetime.now()
    ctfull = ct.strftime('%Y-%m-%d %H:%M')
    return ctfull


def formatTimeMinuteSort(ct=None):
    '''
    获取当前时间字符串:%Y-%m-%d %H:%M
    '''
    if ct == None:
        ct = datetime.now()
    ctfull = ct.strftime('%Y%m%d%H%M')
    return ctfull


def parseTimeMinute(timestr):
    '''
    解析当前时间字符串:%Y-%m-%d %H:%M
    '''
    return datetime.strptime(timestr, '%Y-%m-%d %H:%M')


def formatTimeHour(ct=None):
    '''
    获取当前时间字符串:%Y-%m-%d %H
    '''
    if ct == None:
        ct = datetime.now()
    ctfull = ct.strftime('%Y-%m-%d %H')
    return ctfull


def parseTimeHour(timestr):
    '''
    解析当前时间字符串:%Y-%m-%d %H
    '''
    return datetime.strptime(timestr, '%Y-%m-%d %H')


def formatTimeDay(ct=None):
    '''
    获取当前时间字符串:%Y-%m-%d
    '''
    if ct == None:
        ct = datetime.now()
    ctfull = ct.strftime('%Y-%m-%d')
    return ctfull


def parseTimeDay(timestr):
    '''
    解析当前时间字符串:%Y-%m-%d
    '''
    return datetime.strptime(timestr, '%Y-%m-%d')


def formatTimeDayShort(ct=None):
    '''
    获取当前时间字符串:%Y%m%d
    '''
    if ct == None:
        ct = datetime.now()
    ctfull = ct.strftime('%Y%m%d')
    return ctfull


def parseTimeDayShort(timestr):
    '''
    解析当前时间字符串:%Y%m%d
    '''
    return datetime.strptime(timestr, '%Y%m%d')


def formatTimeMonthShort(ct=None):
    '''
    获取当前时间字符串:%Y%m
    '''
    if ct == None:
        ct = datetime.now()
    ctfull = ct.strftime('%Y%m')
    return ctfull


def parseTimeMonthShort(timestr):
    '''
    解析当前时间字符串:%Y%m
    '''
    return datetime.strptime(timestr, '%Y%m')


def formatTimeWeekInt(ct=None):
    '''
    取得当前的星期的数值, 例如2015年第二个星期, 返回 int(1502)
    '''
    if ct == None:
        ct = datetime.now()
    return (ct.year % 100) * 100 + int(datetime.strftime(ct, '%W'))


def formatTimeMonthInt(ct=None):
    '''
    取得当前的YYMM的int值, int(1507)
    '''
    if ct == None:
        ct = datetime.now()
    return int(ct.strftime('%Y%m')[-4:])


def formatTimeDayInt(ct=None):
    '''
    取得当前的YYYYMMDD的int值, int(150721)
    '''
    if ct == None:
        ct = datetime.now()
    return int(ct.strftime('%Y%m%d')[-6:])


def formatTimeYesterDayInt(ct=None):
    '''
    取得当前日期的昨天的的YYMMDD的int值, int(150721)
    '''
    if ct == None:
        ct = datetime.now()
    ct = ct - timedelta(days=1)
    return int(ct.strftime('%Y%m%d')[-6:])


def isSameMonth(d1, d2):
    return d1.strftime('%Y%m') == d2.strftime('%Y%m')


def is_same_week(timestamp1, timestamp2):
    return getWeekStartTimestamp(timestamp1) == getWeekStartTimestamp(timestamp2)


def is_same_day(timestamp1, timestamp2):
    return datetime.fromtimestamp(timestamp1).date() == datetime.fromtimestamp(timestamp2).date()


def datetime2Timestamp(dt):
    return int(datetime2TimestampFloat(dt))


def datetime2TimestampFloat(dt):
    return time.mktime(dt.timetuple())


def timestrToTimestamp(timestr, fmt):
    return int(timestrToTimestampFloat(timestr, fmt))


def timestrToTimestampFloat(timestr, fmt):
    dt = datetime.strptime(timestr, fmt)
    return datetime2TimestampFloat(dt)


def timestamp2timeStr(value, pattern="%Y-%m-%d %H:%M:%S"):
    '''
    把时间戳变成datetime
    '''
    timeArr = datetime.utcfromtimestamp(value)
    timeStr = timeArr.strftime(pattern)
    return timeStr
