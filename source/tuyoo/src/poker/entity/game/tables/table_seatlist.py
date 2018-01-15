# -*- coding: utf-8 -*-
'''
Created on 2015年7月7日

@author: zqh, zhouhao
'''

from freetime.util import log as ftlog
from poker.entity.game.tables.table_seat import TYSeat


class TYSeatList(object):
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
            assert (isinstance(item, TYSeat))
        self.__list[index] = item

    def __len__(self):
        return len(self.__list)

    def __str__(self):
        return self.__list.__str__()

    def __repr__(self):
        return self.__list.__repr__()

    # 功能函数
    def findNextSeat(self, seatIndex):
        if self.table.maxSeatN <= 0:
            return 1
        return seatIndex + 1 if seatIndex < self.table.maxSeatN - 1  else 0

    def findNextPlayingSeat(self, seatIndex):
        if ftlog.is_debug():
            ftlog.debug('<< |tableId, seatIndex, seats:', self.table.tableId, seatIndex, self, caller=self)
        nextSeatIndex = self.findNextSeat(seatIndex)
        while nextSeatIndex != seatIndex and not self[nextSeatIndex].isPlayingSeat():
            nextSeatIndex = self.findNextSeat(nextSeatIndex)
        if ftlog.is_debug():
            ftlog.debug('>> |tableId, nextSeatIndex:', self.table.tableId, nextSeatIndex, caller=self)
        return nextSeatIndex

    def findNextSittingSeat(self, seatIndex):
        if ftlog.is_debug():
            ftlog.debug('<< |tableId, seatIndex, seats:', self.table.tableId, seatIndex, self, caller=self)
        nextSeatIndex = self.findNextSeat(seatIndex)
        while nextSeatIndex != seatIndex and self[nextSeatIndex].isEmptySeat():
            nextSeatIndex = self.findNextSeat(nextSeatIndex)
        if ftlog.is_debug():
            ftlog.debug('>> |tableId, nextSeatIndex:', self.table.tableId, nextSeatIndex, caller=self)
        return nextSeatIndex

    def findNextEmptySeat(self, seatIndex):
        if ftlog.is_debug():
            ftlog.debug('<< |tableId, seatIndex, seats:', self.table.tableId, seatIndex, self, caller=self)
        nextSeatIndex = self.findNextSeat(seatIndex)
        while nextSeatIndex != seatIndex and not self[nextSeatIndex].isEmptySeat():
            nextSeatIndex = self.findNextSeat(nextSeatIndex)
        if ftlog.is_debug():
            ftlog.debug('>> |tableId, nextSeatIndex:', self.table.tableId, nextSeatIndex, caller=self)
        return nextSeatIndex

    def calcEmptySeatN(self, startSeatIndex, endSeatIndex):
        if ftlog.is_debug():
            ftlog.debug('<< |tableId, startSeatIndex, endSeatIndex, seats:', self.table.tableId, startSeatIndex,
                        endSeatIndex, self, caller=self)
        nextSeatIndex = self.findNextSeat(startSeatIndex)
        emptySeatN = 0
        while nextSeatIndex != endSeatIndex:
            if self[nextSeatIndex].isEmptySeat():
                emptySeatN += 1
            nextSeatIndex = self.findNextSeat(nextSeatIndex)

        if ftlog.is_debug():
            ftlog.debug('>> |tableId, emptySeatN:', self.table.tableId, emptySeatN, caller=self)
        return emptySeatN
