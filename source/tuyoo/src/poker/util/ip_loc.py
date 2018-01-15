# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from bisect import bisect

import freetime.util.log as ftlog
from ipaddr import IPAddress
from poker.resource import getResourcePath
from poker.util import fsutils

_prov2pc_map = {
    '北京': 10,
    '上海': 20,
    '天津': 30,
    '重庆': 40,
    '内蒙古': 1,
    '山西': 3,
    '河北': 5,
    '辽宁': 11,
    '吉林': 13,
    '黑龙江': 15,
    '江苏': 21,
    '安徽': 23,
    '山东': 25,
    '浙江': 31,
    '江西': 33,
    '福建': 35,
    '湖南': 41,
    '湖北': 43,
    '河南': 45,
    '广东': 51,
    '广西': 53,
    '贵州': 55,
    '海南': 57,
    '四川': 61,
    '云南': 65,
    '陕西': 71,
    '甘肃': 73,
    '宁夏': 75,
    '青海': 81,
    '新疆': 83,
    '西藏': 85,
    '香港': -1,
    '澳门': -1,
    '台湾': -1,
    # '香港' : 999077,
    # '澳门' : 999078,
    # '台湾' : 86,
}

_ip_list_start = None
_ip_list_end = None


def _initialize():
    global _ip_list_start, _ip_list_end
    _ip_list_start = []
    _ip_list_end = []
    filename = getResourcePath('ip_prov.txt')
    if fsutils.fileExists(filename):
        with open(filename, 'r') as f:
            for line in f:
                if len(line) == 0 or line == '\n':
                    continue
                start, end, provname = line[:-1].split(' ')
                _ip_list_start.append(int(start))
                _ip_list_end.append((int(end), _prov2pc_map[provname]))
    else:
        ftlog.error('ERROR, the resource file not found !', filename)


def _binary_search(x, lo=0, hi=None):
    global _ip_list_start, _ip_list_end
    if hi is None:
        hi = len(_ip_list_start)
    pos = bisect(_ip_list_start, x, lo, hi)
    if pos == 0:
        return -1
    return pos - 1


def find(ipstr):
    ''' 
    return postcode of the province in which the ip addr reside 
    '''
    global _ip_list_start, _ip_list_end
    if _ip_list_start == None:
        _initialize()
    ip = IPAddress(ipstr)
    pos = _binary_search(ip._ip)
    ip_start = IPAddress(_ip_list_start[pos])
    ip_end = IPAddress(_ip_list_end[pos][0])
    if ip > ip_start and ip < ip_end:
        if _ip_list_end[pos][1] < 0:
            raise Exception(ipstr + " not found")
        return _ip_list_end[pos][1]
    else:
        ftlog.info('ERROR ip_loc->find ' + ipstr + " not found")
        return 10
