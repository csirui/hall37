# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''


class ReadonlyDict(object):
    '''
    类似dict的所有行为, 但是剔除dict的所有"写"方法, 即: 只读的dict
    '''

    def __init__(self, objdict):
        self.__objdict = objdict

    def __setattr__(self, *args, **kwargs):
        if args[0] == '_ReadonlyDict__objdict':
            return object.__setattr__(self, *args, **kwargs)

    def __contains__(self, key):
        return key in self.__objdict

    def __getitem__(self, key):
        return self.__objdict[key]

    def __iter__(self):
        return iter(self.__objdict)

    def __len__(self):
        return len(self.__objdict)

    def __repr__(self):
        return repr(self.__objdict)

    def __str__(self):
        return str(self.__objdict)

    def get(self, key, default=None):
        return self.__objdict.get(key, default)

    def has_key(self, key):
        return self.__objdict.has_key(key)

    def items(self):
        return self.__objdict.items()

    def iteritems(self):
        return self.__objdict.iteritems()

    def iterkeys(self):
        return self.__objdict.iterkeys()

    def itervalues(self):
        return self.__objdict.itervalues()

    def keys(self):
        return self.__objdict.keys()

    def values(self):
        return self.__objdict.values()


def makeReadonly(obj):
    '''
    返回对应obj的只读的数据
    例如: list替换为tuple, dict替换为只读的dict
    '''
    if isinstance(obj, (list, set)):
        newobj = []
        for v in obj:
            newobj.append(makeReadonly(v))
        return tuple(newobj)
    if isinstance(obj, dict):
        newobj = {}
        for k, v in obj.items():
            newobj[k] = makeReadonly(v)
        return ReadonlyDict(newobj)
    return obj
