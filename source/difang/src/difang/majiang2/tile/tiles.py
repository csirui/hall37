#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
牌型的逻辑全部放这里
"""
from difang.majiang2.tile.tile import Tiles, HuTiles
from freetime.style import Fail


class M14:
    """
    传统的14张成胡的麻将
    """

    def __init__(self):
        pass

    @classmethod
    def find_first(cls, tileArray, hu_tails, *args):
        """
        按顺序找到第一个就停止
        """
        for each in args:
            if each(tileArray, hu_tails):
                return True
        return False

    # noinspection PyUnusedLocal
    @classmethod
    def justPass(cls, tileArray, hu_tails):
        """
        纯跳过的
        """
        return False

    @classmethod
    def is7Dui(cls, tileArray, hu_tails):
        """
        传统7对判断
        :type tileArray: TileArray
        :type hu_tails: HuTiles
        """
        dui_list = tileArray.tiles_dui()
        gang_list = tileArray.tiles_gang()
        if len(dui_list) + len(gang_list) * 2 != 7:
            # 杠当做2个对
            return False
        for each, _ in gang_list:
            hu_tails.append((each, each))
        for each, _ in dui_list:
            # 将杠拆成对
            hu_tails.append((each, each))
        hu_tails.human("七对")
        return True

    @classmethod
    def isPHu(cls, tileArray, hu_tails):
        """
        通用规则中的平胡
        :type tileArray: TileArray
        :type hu_tails: HuTiles
        """
        # 把顺子摘出去
        shun_list, left_array = tileArray.tiles_shun_left()
        # todo: 风牌
        peng_list = []
        gang_list = []
        dui_list = []
        for each, number in left_array.tile_items():
            if number == 1:
                # 余下的牌必须是杠/刻(碰)/对
                return False
            elif number == 2:
                dui_list.append(Tiles([each, each]))
            elif number == 3:
                peng_list.append(Tiles([each, each, each]))
            elif number == 4:
                gang_list.append(Tiles([each, each, each, each]))
            else:
                Fail("根本不可能到这里[%s]", tileArray)
        if len(dui_list) > 1:
            # 只能有一个对子当将牌
            return False
        hu_tails.extend(shun_list)
        hu_tails.extend(peng_list)
        hu_tails.extend(gang_list)
        hu_tails.extend(dui_list)
        hu_tails.human("平胡")
        return True
