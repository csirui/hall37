# -*- coding=utf-8
"""
Created on 2016年9月23日

@author: zhaol
"""
import copy


class MHand(object):
    # 握在手里的牌，未吃/碰/杠的牌
    TYPE_HAND = 0
    # 吃牌
    TYPE_CHI = 1
    # 碰牌
    TYPE_PENG = 2
    # 明杠牌
    TYPE_GANG = 3
    # 和牌
    TYPE_HU = 4
    # 最新的一手牌
    TYPE_CUR = 5
    # 类别总数
    TYPE_COUNT = 6

    def __init__(self):
        super(MHand, self).__init__()

    @classmethod
    def copyAllTilesToList(cls, tiles):
        """
        拷贝所有的手牌到一个list内
        """
        newTiles = copy.deepcopy(tiles)

        re = []
        re.extend(newTiles[cls.TYPE_HAND])
        for chi in newTiles[cls.TYPE_CHI]:
            re.extend(chi)

        for peng in newTiles[cls.TYPE_PENG]:
            re.extend(peng)

        for gang in newTiles[cls.TYPE_GANG]:
            re.extend(gang['pattern'])

        re.extend(newTiles[cls.TYPE_HU])
        return re
