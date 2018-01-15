# -*- coding: utf-8 -*-
'''
Created on 2015年7月7日

@author: zqh
'''

from poker.entity.game.tables.table_player import TYPlayer


class TYPlayerList(object):
    '''
    为了兼容老版Table（_seat : [[][]]）， TYSeatList需要实现list的部分函数
    Note： 如果直接继承list的话，在redis化时，没有覆写的函数会出现致数据不一致的问题， 所以不推荐。
    注意: 座位数量(table.maxSeatN)初始化后, 就不在发生变化
    '''

    def __init__(self, table):
        self.table = table
        self.__list = []
        if table.maxSeatN > 0:
            for _ in xrange(table.maxSeatN):
                self.__list.append(None)

    def __getitem__(self, index):
        return self.__list[index]

    def __setitem__(self, index, item):
        if item != None:
            assert (isinstance(item, TYPlayer))
        self.__list[index] = item

    def __len__(self):
        return len(self.__list)

    def __str__(self):
        return self.__list.__str__()

    def __repr__(self):
        return self.__list.__repr__()

    def getList(self):
        return self.__list
