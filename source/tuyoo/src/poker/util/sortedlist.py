# -*- coding:utf-8 -*-
'''
Created on 2015年11月21日

@author: zhaojiangang
'''
import bisect


def indexOf(l, v):
    i = bisect.bisect_left(l, v)
    if i != len(l) and l[i] == v:
        return i
    return -1


def insert(l, v):
    i = bisect.bisect(l, v)
    bisect.insort(l, v)
    return i


def upperBound(l, v):
    return bisect.bisect_right(l, v)


def lowerBound(l, v):
    return bisect.bisect_left(l, v)


def remove(l, v):
    i = indexOf(l, v)
    if i == -1:
        raise ValueError('v not in list')
    l.pop(i)


if __name__ == '__main__':
    l = [0, 2]
    print upperBound(l, 2)
    print lowerBound(l, 2)
