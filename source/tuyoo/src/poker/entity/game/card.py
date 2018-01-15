# -*- coding=utf-8 -*-
'''
'''
__author__ = [
    'Wangtao',
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]


class Card(object):
    '''一张牌'''

    # 牌面值
    CARD_NUM = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '', '']

    # 牌的花色     黑桃 spade 梅花club 红桃hearts 方块diamonds 小王joker 大王JOKER
    CARD_COLOR = ['S', 'H', 'C', 'D', 'j', 'J']

    # 牌的花色字典
    CARD_COLOR_DICT = {'S': u'黑桃', 'C': u'梅花', 'H': u'红桃', 'D': u'方块', 'j': u'小王', 'J': u'大王'}

    def __init__(self, _type, number):
        self.t, self.n = _type, number

    @staticmethod
    def cmp(a, b):
        """ 两张牌比较，只比较牌值，不管花色。"""
        return a.n - b.n

    def __str__(self):
        return "%d%02d" % (self.t, self.n)

    def __repr__(self):
        return self.__str__()

    def __int__(self):
        return self.t * 100 + self.n

    def toShortInt(self):
        ''' 102 ~ 414 => 1 ~ 52
            515 => 53  616 => 54
        '''
        if self.t == 6: return 54
        if self.t == 5: return 53
        return (self.t - 1) * 13 + (1 if self.n == 14 else self.n)

    @staticmethod
    def _split_card_value(int_card):
        """ _split_card_value(103) --> (1, 3) """

        if int_card > 600:
            return (6, 16)
        elif int_card > 500:
            return (5, 15)
        elif int_card > 400:
            return (4, int_card - 400)
        elif int_card > 300:
            return (3, int_card - 300)
        elif int_card > 200:
            return (2, int_card - 200)
        else:
            return (1, int_card - 100)

    @classmethod
    def _splitShort(cls, cardId):
        ''' 1 ~ 54 => t, n '''
        if cardId == 54:
            t, n = 6, 16
        elif cardId == 53:
            t, n = 5, 15
        elif cardId > 39:
            t, n = 4, cardId - 39
        elif cardId > 26:
            t, n = 3, cardId - 26
        elif cardId > 13:
            t, n = 2, cardId - 13
        else:
            t, n = 1, cardId

        if n == 1:
            n = 14
        return t, n

    @classmethod
    def fromInt(cls, int_card):
        return cls(*Card._split_card_value(int_card))

    @classmethod
    def fromShortInt(cls, cardId):
        return cls(*Card._splitShort(cardId))

    @classmethod
    def intToShort(cls, int_card):
        ''' 102 ~ 414 => 1 ~ 52
            515 => 53  616 => 54
        '''
        t, n = cls._split_card_value(int_card)
        if t == 6: return 54
        if t == 5: return 53
        return (t - 1) * 13 + (1 if n == 14 else n)

    @classmethod
    def shortToInt(cls, cardId):
        ''' 1 ~ 52 => 102 ~ 414
            53 => 515   54 => 616
        '''
        t, n = cls._splitShort(cardId)
        return t * 100 + (14 if n == 1 else n)

    @classmethod
    def getCardColorNumByCardId(cls, cardId):
        """
        返回值：    [花色， 牌面值]
        """
        assert cardId <= 54 and cardId >= 1, "wrong input cardId=%d to getCardColorNumByCardId" % cardId
        t, n = cls._splitShort(cardId)
        return (cls.CARD_COLOR[t - 1], n)

    @classmethod
    def getCardStr(cls, color, num):
        return '%s%s' % (cls.CARD_COLOR_DICT[cls.CARD_COLOR[color - 1]], cls.CARD_NUM[num - 2])


if __name__ == '__main__':

    import sys

    reload(sys)
    sys.setdefaultencoding('utf8')

    for cardIndex in xrange(54):
        # cardInt =  Card.shortToInt(cardIndex + 1)
        # print cardIndex+1, Card.getCardColorNumByCardId(cardIndex+1), cardInt, Card.intToShort(cardInt)
        # cardObj1 = Card.fromShortInt(cardIndex + 1)
        # print cardIndex+1, cardObj1.getCardStr(cardObj1.t, cardObj1.n), cardObj1.toShortInt()
        # cardObj2 = Card.fromInt(cardInt)
        # print cardIndex + 1, cardObj2.getCardStr(cardObj2.t, cardObj2.n), cardObj2.toShortInt()

        cardObj1 = Card.fromShortInt(cardIndex + 1)
        print  cardObj1.shortToInt(cardIndex + 1), cardObj1.getCardStr(cardObj1.t,
                                                                       cardObj1.n), Card.getCardColorNumByCardId(
            cardIndex + 1)
