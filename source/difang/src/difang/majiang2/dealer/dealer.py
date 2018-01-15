# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''
import random

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
"""


class Dealer(object):
    def __init__(self):
        """初始化
            子类在自己的初始化方法里，初始化麻将牌池范围，准备发牌
        """
        super(Dealer, self).__init__()
        self.__tiles = []
        self.__wan_tiles = []
        self.__tiao_tiles = []
        self.__tong_tiles = []
        # 本玩法包含的牌
        self.__card_tiles = []

    def reset(self):
        """重置"""
        self.__tiles = []

    @property
    def tiles(self):
        return self.__tiles

    def setTiles(self, tiles):
        self.__tiles = tiles

    def addTiles(self, tiles):
        self.__tiles.extend(tiles)

    def setCardTiles(self, cardTiles):
        self.__card_tiles = cardTiles

    @property
    def cardTiles(self):
        return self.__card_tiles

    """洗牌/发牌
        子类必须实现
    """

    def shuffle(self, goodPointCount, cardCountPerHand):
        """参数说明
            goodPointCount : 好牌点的个数
            cardCountPerHand ： 每手牌的麻将牌张数
        """
        return None

    def initTiles(self, handTiles, poolTiles):
        """根据摆牌结果初始化手牌"""
        cards = []
        for tiles in self.cardTiles:
            cards.extend(tiles)
        print cards

        for hand in handTiles:
            for tile in hand:
                if tile not in cards:
                    return False

                cards.remove(tile)

        for tile in poolTiles:
            if tile not in cards:
                return False
            cards.remove(tile)

        random.shuffle(cards)
        self.__tiles = []
        print '1:', cards
        for index in range(len(handTiles)):
            print handTiles
            self.__tiles.extend(handTiles[index])
            print self.__tiles
            for _ in range(len(handTiles[index]), 13):
                self.__tiles.append(cards.pop(0))
                print self.__tiles

        self.__tiles.extend(poolTiles)
        self.__tiles.extend(cards)

        return True
