# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import freetime.util.log as ftlog
from poker.resource import getResourcePath
from poker.util import fsutils

# postcode to province name
pc2prov_map = {
    10: '北京',
    20: '上海',
    30: '天津',
    40: '重庆',
    01: '内蒙古',
    03: '山西',
    05: '河北',
    11: '辽宁',
    13: '吉林',
    15: '黑龙江',
    21: '江苏',
    23: '安徽',
    25: '山东',
    31: '浙江',
    33: '江西',
    35: '福建',
    41: '湖南',
    43: '湖北',
    45: '河南',
    51: '广东',
    53: '广西',
    55: '贵州',
    57: '海南',
    61: '四川',
    65: '云南',
    71: '陕西',
    73: '甘肃',
    75: '宁夏',
    81: '青海',
    83: '新疆',
    85: '西藏',
    99: '香港',
}

prov2pc_map = {}
for k, v in pc2prov_map.items():
    prov2pc_map[v] = k


# postcode to zipcode: pc*10000


class ContradictError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class CoarseError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


_trie = None


def _initialize():
    global _trie
    _trie = {}
    filename = getResourcePath('phone_prefix.txt')
    if fsutils.fileExists(filename):
        with open(filename, 'r') as f:
            for line in f:
                tp = line[:-1].split(' ')
                _insert((tp[0], prov2pc_map[tp[1]]))
    else:
        ftlog.error('ERROR, the resource file not found !', filename)
    _deredundant(_trie)


def _insert(t):
    global _trie
    prefix, prov = t
    d = _trie
    for i in xrange(len(prefix)):
        p = prefix[i]
        if p not in d:
            d[p] = [prefix], prov
            return
        o = d[p]
        if isinstance(o, tuple):
            if prefix in o[0]:
                if o[1] != prov:
                    raise ContradictError("")
                return
            if prov == o[1]:
                o[0].append(prefix)
                return
            if i >= len(prefix) - 1:
                raise CoarseError("")
            d[p] = {prefix[i + 1]: ([prefix], prov)}
            for pre in o[0]:
                _insert((pre, o[1]))
            return
        if isinstance(o, dict):
            d = o
            continue
        raise Exception('inserting ' + str(t) + ' into ' + str(_trie))


def _deredundant(triedict):
    for s in triedict:
        if isinstance(triedict[s], tuple):
            del triedict[s][0][:]
        elif isinstance(triedict[s], dict):
            _deredundant(triedict[s])
        else:
            raise Exception("")


def _common(prefix, triedict):
    for s in triedict:
        if isinstance(triedict[s], tuple):
            print prefix + s, triedict[s][1]
        elif isinstance(triedict[s], dict):
            _common(prefix + s, triedict[s])
        else:
            raise Exception("")


def find(phonestr):
    global _trie
    if _trie == None:
        _initialize()
    m = _trie
    for d in phonestr:
        if d not in m:
            raise Exception(phonestr + " not found")
        if isinstance(m[d], tuple):
            return m[d][1]
        if isinstance(m[d], dict):
            m = m[d]
            continue
        raise Exception(phonestr + " not found")
