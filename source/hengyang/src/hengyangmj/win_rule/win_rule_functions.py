# -*- coding=utf-8
"""
Created on 2016年11月18日
庄家规则
@author: nick.kai.lee
"""

from hengyangmj.hengyang_log import HYLog


class HYWinRuleFunction(object):
    """
    """

    @classmethod
    def do_tile_to_suit(cls, tile):
        """
        计算麻将值属于什么花色
        @param tile麻将数值
        @return 返回0,1,2 万筒条
        """
        return tile / 10

    @classmethod
    def do_tile_to_single_digit(cls, tile):
        """
        计算麻将值取模到各位数
        @param tile, 麻将数值
        @return 返回每个花色个位数 eg: 11 -> 1, 1->1
        """
        return tile % 10

    @classmethod
    def find_repeat_tile_info(cls, tiles):
        """
        在tiles里查询每一个tile出现的次数
        @param tiles花色一维数组
        @return 返回每个花色的数量 map
        """
        tile_map = {}
        for tile in tiles:
            if tile in tile_map:
                tile_map[tile] += 1
            else:
                tile_map[tile] = 1
        return tile_map

    @classmethod
    def find_repeat_suit_info(cls, tiles):
        """
        在tiles里查询suit(万，筒，条)牌张数量
        @param tiles:花色一维数组
        @return:返回suit个数(几个万,几个筒,几个条) map
        """
        # 万筒条
        suit_map = [0, 0, 0]
        for tile in tiles:
            suit_map[cls.do_tile_to_suit(tile)] += 1
        return suit_map

    @classmethod
    def find_unformed_tiles(cls, tiles=[], pair=2):
        """
        在tiles里找到不成型牌,排除顺子和刻子
        @param tiles:花色一维数组
        @param pair:根据将牌来搜牌型,依次可以搜出3种不同结构
        @return:返回不成型牌列表,刻子列表,顺子列表,杠牌列表

        根据将牌来搜牌型,依次可以搜出3种不同结构,选择unformed_tiles02最少的结果
        """
        tiles_map = HYWinRuleFunction.find_repeat_tile_info(tiles)

        HYLog.debug("find_unformed_tiles: pair&tiles_map:", pair, tiles_map)

        triplet_tiles = []
        sequence_tiles = []
        unformed_tiles00 = {}  # 非刻子花色字典, 标记每个花色的张数, 计数器
        unformed_tiles01 = []  # 非刻子花色数组, 标记剩余的花色
        unformed_tiles02 = []  # 非成型花色数组, 标记剔除刻子,顺子,杠的剩余牌张花色(可能包含将牌)
        pair_tiles = []

        # 剔除刻子&2,5,8 将牌
        for tile in tiles_map:
            if tiles_map[tile] == 4:  # 4张牌按顺子处理, 如果不杠的话
                unformed_tiles00[tile] = 1
                unformed_tiles01.append(tile)
                triplet_tiles.append([tile for _ in range(3)])
                pass
            elif tiles_map[tile] == 3:
                triplet_tiles.append([tile for _ in range(3)])
            elif tiles_map[tile] == 2 and cls.do_tile_to_single_digit(tile) == pair:  # 必须有指定将牌,eg:2 5 8
                pair_tiles.extend([tile for _ in range(2)])
            elif tiles_map[tile] < 3:
                unformed_tiles00[tile] = tiles_map[tile]
                unformed_tiles01.append(tile)

        # 剔除顺子,利用牌张计数器
        count = len(unformed_tiles01)
        i = 0
        unformed_tiles01.sort()  # 非刻子花色数组升序排列
        while (i < count):
            a = unformed_tiles01[i]
            b = 0 if i + 1 >= count else unformed_tiles01[i + 1]
            c = 0 if i + 2 >= count else unformed_tiles01[i + 2]

            if b == 0 or c == 0 or (b != a + 1 or c != a + 2) or (a + c) % 2 != 0:
                if unformed_tiles00[a] > 0:
                    unformed_tiles02.append(a)
                i += 1
            else:
                # 计算至少可以成几个顺子 minv
                minv = min(unformed_tiles00[a], unformed_tiles00[b], unformed_tiles00[c])
                unformed_tiles00[a] -= minv
                unformed_tiles00[b] -= minv
                unformed_tiles00[c] -= minv
                sequence_tiles.extend([[a, b, c] for _ in range(minv)])
                if unformed_tiles00[a] > 0:
                    unformed_tiles02.append(a)
                i += 1
            pass
        return [unformed_tiles02, pair_tiles, sequence_tiles, triplet_tiles]

    @classmethod
    def check_if_sequence(cls, tiles=[]):
        """
        查询tiles是否全是顺子
        @rtype: object
        @param tiles 花色一维数组
        @return Boolean
        """
        tiles.sort()  # 花色数组升序排列
        count = len(tiles)
        if 0 != count % 3:
            return False
        i = 0
        while (i < count):  # 剩下花色不成顺
            if tiles[i + 1] != (tiles[i] + tiles[i + 2]) / 2:
                return False
            i += 3
        return True
