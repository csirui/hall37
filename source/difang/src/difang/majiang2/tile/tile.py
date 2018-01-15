# coding=utf-8
"""
Created on 2016年9月24日

@author: zhaol
"""
import copy

from difang.majiang2.player.hand.hand import MHand
from freetime.style import Assert, utf8_reload

"""
麻将手牌编码
万 1-9
筒 11-19
条 21-29
东 31
南 32
西 33
北 34
中 35
发 36
白 37
春 41
夏 42
秋 43
冬 44
梅 45
兰 46
竹 47
菊 48
"""


def _helper(start_or_target, values):
    if type(start_or_target) is int:
        return zip(values, range(start_or_target, start_or_target + len(values)))
    else:
        return zip(values, [start_or_target] * len(values))


_human = {}
_human.update(_helper(01, ["一万", "二万", "三万", "四万", "五万", "六万", "七万", "八万", "九万"]))
_human.update(_helper(11, ["一饼", "二饼", "三饼", "四饼", "五饼", "六饼", "七饼", "八饼", "九饼"]))
_human.update(_helper(21, ["一条", "二条", "三条", "四条", "五条", "六条", "七条", "八条", "九条"]))
_human.update(_helper(31, ["东", "南", "西", "北", "中", "发", "白"]))
_human.update(_helper(41, ["春", "夏", "秋", "冬", "梅", "兰", "竹", "菊"]))
# 保留一个 id => 官方文案 的字典
_human_official = dict(zip(*reversed(zip(*_human.items()))))

# 其它的叫法
_human.update(_helper(11, ["一筒", "二筒", "三筒", "四筒", "五筒", "六筒", "七筒", "八筒", "九筒"]))
_human.update(_helper(11, ["一桶", "二桶", "三桶", "四桶", "五桶", "六桶", "七桶", "八桶", "九桶"]))
_human.update(_helper(21, ["一索", "二索", "三索", "四索", "五索", "六索", "七索", "八索", "九索"]))
_human.update(_helper(31, ["东风", "南风", "西风", "北风"]))
_human.update(_helper(31, ["东边的", "南边的", "西边的", "北边的"]))
# 个别叫法
_human.update(
    _helper("一条", ["幺鸡"]) +
    _helper("一筒", ["大饼", "月饼"]) +
    _helper("二筒", ["眼睛"]) +
    _helper("中", ["铜锤"]) +
    _helper("发", ["发财", "發"]) +
    _helper("白", ["白板"]) +
    []
)


def _human_ex():
    """

    :return:
    """
    utf8_reload()
    for each in filter(lambda k: k[0] in "一二三四五六七八九", _human.keys()):
        new = reduce(lambda x, y: x.replace(y[0], str(y[1])), _helper(1, unicode("一二三四五六七八九")), each)
        _human[str(new)] = _human[each]

    for key, value in filter(lambda (k, v): type(v) is str, _human.items()):
        _human[key] = _human[value]

    for key, value in _human.items():
        _human[unicode(key)] = value


_human_ex()
_human_key_set = _human.keys()
_human_key_all_set = set("".join(_human.keys()))


def to_human(tiles):
    """
    :type tiles: list
    :rtype str
    """
    return " ".join(map(_human_official.get, tiles))


class Tiles(list):
    """
    一组牌而已
    """

    def __str__(self):
        return "[%s]" % " ".join(map(_human_official.get, self))

    def __repr__(self):
        return self.__str__()


class TileArray(list):
    """
    牌=>数量(方便算牌的那种)
    """

    def __init__(self, tiles):
        super(TileArray, self).__init__()
        self.extend([0 for _ in range(MTile.TILE_MAX_VALUE)])
        for tile in tiles:
            self[tile] += 1

    def clone_one(self):
        ret = TileArray([])
        ret[:] = self[:]
        return ret

    def tile_items(self):
        """
        :return: 牌=>数量
        """
        return filter(lambda (x, y): y > 0, enumerate(self))

    def tiles_shun_left(self):
        """
        所有的[万|饼|条]顺子
        :rtype list[Tiles], TileArray
        """
        tmp = self.clone_one()
        ret = []
        for index, num in enumerate(tmp[:30]):
            if tmp[index + 0] == 0 or tmp[index + 1] == 0 or tmp[index + 2] == 0:
                continue
            ret.append(Tiles([index, index + 1, index + 2]))
            tmp[index + 0] -= 1
            tmp[index + 1] -= 1
            tmp[index + 2] -= 1
        return ret, tmp

    def tiles_dui(self):
        """
        所有的对
        """
        return filter(lambda (x, y): y == 2, enumerate(self))

    def tiles_peng(self):
        """
        所有的刻
        """
        return filter(lambda (x, y): y == 3, enumerate(self))

    def tiles_gang(self):
        """
        所有的杠
        """
        return filter(lambda (x, y): y == 4, enumerate(self))

    def __len__(self):
        return sum(self)

    def __str__(self):
        if sum(self) <= 14:
            return "[%s]" % "|".join(
                map(lambda (index, num): "|".join([unicode(_human_official[index])] * num), self.tile_items()))
        else:
            return "[%s]" % " ".join(
                map(lambda (index, num): "%s:%d" % (_human_official[index], num), self.tile_items()))

    def __repr__(self):
        return self.__str__()


class HuTiles(list):
    def __init__(self, ):
        super(HuTiles, self).__init__()
        self.__title = None

    def human(self, title):
        self.__title = title

    @property
    def title(self):
        return self.__title

    def __str__(self):
        ret = []
        for each in sorted(self, key=len, reverse=True):
            ret.append("[%s]" % Tiles(each))
        return "%s %s" % (self.__title, " ".join(ret))

    def __repr__(self):
        return self.__str__()


class HandTiles(list):
    def __init__(self, *args):
        list.__init__(self)
        self.extend(args)
        if len(self) < MHand.TYPE_COUNT:
            self.extend([Tiles()] * (MHand.TYPE_COUNT - len(self)))

    def __str__(self):
        return '''\
手牌:%s
吃牌:%s
碰牌:%s
明杠牌:%s
和牌:%s
最新的一手牌:%s
''' % (self[0], self[1], self[2], self[3], self[4], self[5])

    def __repr__(self):
        return self.__str__()

    def dropHand(self, tile):
        self[0].remove(tile)

    def addHand(self, tile):
        self[0].append(tile)

    @classmethod
    def clone(cls, tiles):
        """
        :type tiles: HandTiles
        """
        return copy.deepcopy(tiles)


def new_hand_tails(tiles):
    """
    构造一个新的手牌(没有碰/吃之类的任何操作)
    :param tiles: 手牌数组
    :type tiles:list
    :return list
    """
    return HandTiles(tiles)


def human_one_tile(src):
    """
    读得懂的牌型
    :rtype int
    """
    return _human[src]


def human_tiles(src):
    """
    读得懂的牌型
    :rtype list
    """
    ret = Tiles()
    prefix = ""
    for each in unicode(src):
        if prefix + each in _human_key_set:
            ret.append(_human[prefix + each])
            prefix = ""
            continue
        if each not in _human_key_all_set:
            # 分割字符
            Assert(len(prefix) == 0, "存在不能识别的定义请确认[%s]", prefix)
            continue
        prefix += each
    return ret


class MTile(object):
    @classmethod
    def human(cls, src):
        """
        通过文案构造指定的牌
        """
        return _human[src]

    TILE_NONE = -1
    # 万
    TILE_WAN = 0
    # 筒
    TILE_TONG = 1
    # 条
    TILE_TIAO = 2
    # 风
    TILE_FENG = 3
    # 花色个数
    COLOR_COUNT = 4

    TILE_DONG_FENG = 31
    TILE_NAN_FENG = 32
    TILE_XI_FENG = 33
    TILE_BEI_FENG = 34
    TILE_HONG_ZHONG = 35
    TILE_FA_CAI = 36
    TILE_BAI_BAN = 37

    TILE_ONE_WAN = TILE_WAN * 10 + 1
    TILE_TWO_WAN = TILE_WAN * 10 + 2
    TILE_THREE_WAN = TILE_WAN * 10 + 3
    TILE_FOUR_WAN = TILE_WAN * 10 + 4
    TILE_FIVE_WAN = TILE_WAN * 10 + 5
    TILE_SIX_WAN = TILE_WAN * 10 + 6
    TILE_SEVEN_WAN = TILE_WAN * 10 + 7
    TILE_EIGHT_WAN = TILE_WAN * 10 + 8
    TILE_NINE_WAN = TILE_WAN * 10 + 9

    TILE_ONE_TONG = TILE_TONG * 10 + 1
    TILE_TWO_TONG = TILE_TONG * 10 + 2
    TILE_THREE_TONG = TILE_TONG * 10 + 3
    TILE_FOUR_TONG = TILE_TONG * 10 + 4
    TILE_FIVE_TONG = TILE_TONG * 10 + 5
    TILE_SIX_TONG = TILE_TONG * 10 + 6
    TILE_SEVEN_TONG = TILE_TONG * 10 + 7
    TILE_EIGHT_TONG = TILE_TONG * 10 + 8
    TILE_NINE_TONG = TILE_TONG * 10 + 9

    TILE_ONE_TIAO = TILE_TIAO * 10 + 1
    TILE_TWO_TIAO = TILE_TIAO * 10 + 2
    TILE_THREE_TIAO = TILE_TIAO * 10 + 3
    TILE_FOUR_TIAO = TILE_TIAO * 10 + 4
    TILE_FIVE_TIAO = TILE_TIAO * 10 + 5
    TILE_SIX_TIAO = TILE_TIAO * 10 + 6
    TILE_SEVEN_TIAO = TILE_TIAO * 10 + 7
    TILE_EIGHT_TIAO = TILE_TIAO * 10 + 8
    TILE_NINE_TIAO = TILE_TIAO * 10 + 9

    TILE_MAX_VALUE = 40

    FENG_DONG = 0b1
    FENG_NAN = 0b10
    FENG_XI = 0b100
    FENG_BEI = 0b1000
    FENG_ZHONG = 0b10000
    FENG_FA = 0b100000
    FENG_BAI = 0b1000000

    __tileType_range_map = {
        TILE_WAN: range(TILE_ONE_WAN, TILE_NINE_WAN + 1),
        TILE_TONG: range(TILE_ONE_TONG, TILE_NINE_TONG + 1),
        TILE_TIAO: range(TILE_ONE_TIAO, TILE_NINE_TIAO + 1),
        TILE_FENG: range(TILE_DONG_FENG, TILE_BAI_BAN + 1),
    }

    def __init__(self):
        super(MTile, self).__init__()

    @classmethod
    def changeTilesToValueArr(cls, tiles):
        """
        将牌转化为张数数组
        :rtype :TileArray
        """
        return TileArray(tiles)

    @classmethod
    def getColorCount(cls, tileArr):
        """
        获取tileArr花色数量,不包含字牌
        """
        count = 0
        for tile in MTile.traverseTile(MTile.TILE_WAN):
            if tileArr[tile]:
                count += 1
                break

        for tile in MTile.traverseTile(MTile.TILE_TONG):
            if tileArr[tile]:
                count += 1
                break

        for tile in MTile.traverseTile(MTile.TILE_TIAO):
            if tileArr[tile]:
                count += 1
                break

        return count

    @classmethod
    def traverseTile(cls, tileType):
        """
        返回指定牌型的索引
        """
        return cls.__tileType_range_map.get(tileType, [])

    @classmethod
    def cloneTiles(cls, tiles):
        """
        拷贝手牌
        """
        if isinstance(tiles, TileArray):
            return TileArray(tiles)
        elif isinstance(tiles, Tiles):
            return Tiles(tiles)
        elif isinstance(tiles, HandTiles):
            return HandTiles(*tiles)
        else:
            return copy.deepcopy(tiles)

    @classmethod
    def getColor(cls, tile):
        """
        获取手牌颜色
        """
        return tile / 10

    @classmethod
    def getValue(cls, tile):
        """
        获取手牌
        """
        return tile % 10

    @classmethod
    def getTiles(cls, colors, fengDetails=0b1111111):
        """
        获取某个花色的所有牌
        """
        # todo: 简化这个函数
        cards = []
        if cls.TILE_WAN in colors:
            ct = []
            allValue = 9
            for index in range(allValue):
                for _ in range(cls.COLOR_COUNT):
                    ct.append(index + 1 + cls.TILE_WAN * 10)
            cards.append(ct)
        else:
            cards.append([])

        if cls.TILE_TONG in colors:
            ct = []
            allValue = 9
            for index in range(allValue):
                for _ in range(cls.COLOR_COUNT):
                    ct.append(index + 1 + cls.TILE_TONG * 10)
            cards.append(ct)
        else:
            cards.append([])

        if cls.TILE_TIAO in colors:
            ct = []
            allValue = 9
            for index in range(allValue):
                for _ in range(cls.COLOR_COUNT):
                    ct.append(index + 1 + cls.TILE_TIAO * 10)
            cards.append(ct)
        else:
            cards.append([])

        if cls.TILE_FENG in colors:
            ct = []
            if fengDetails & cls.FENG_DONG:
                for _ in range(cls.COLOR_COUNT):
                    ct.append(31)

            if fengDetails & cls.FENG_NAN:
                for _ in range(cls.COLOR_COUNT):
                    ct.append(32)

            if fengDetails & cls.FENG_XI:
                for _ in range(cls.COLOR_COUNT):
                    ct.append(33)

            if fengDetails & cls.FENG_BEI:
                for _ in range(cls.COLOR_COUNT):
                    ct.append(34)

            if fengDetails & cls.FENG_ZHONG:
                for _ in range(cls.COLOR_COUNT):
                    ct.append(35)

            if fengDetails & cls.FENG_FA:
                for _ in range(cls.COLOR_COUNT):
                    ct.append(36)

            if fengDetails & cls.FENG_BAI:
                for _ in range(cls.COLOR_COUNT):
                    ct.append(37)

            cards.append(ct)
        else:
            cards.append([])

        return cards
