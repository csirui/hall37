# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.dealer.dealer_all_color import AllColorDealer
from difang.majiang2.dealer.dealer_sanmen_nofeng import SanMenNoFengDealer
from difang.majiang2.dealer.dealer_sanmen_zhong import SanMenWithZhonggDealer
from difang.majiang2.dealer.dealer_tongtiao_zfb import TongTiaoWithZFBDealer
from difang.majiang2.dealer.dealer_tongtiao_zhong import TongTiaoWithZhonggDealer
from freetime.util import log as ftlog


class DealerFactory(object):
    # 只发万筒条，没有风
    DEALER_SANMEN_WUFENG = 'sanmen_wufeng'
    # 包含所有的牌
    DEALER_ALL_COLORS = 'all_colors'
    # 万/筒/条+红中
    DEALER_SANMENG_ZHONG = 'sanmen_zhong'
    # 筒/条+红中
    DEALER_TONGTIAO_ZHONG = 'tongtiao_zhong'
    # 筒/条+中发白
    DEALER_TONGTIAO_ZFB = 'tongtiao_zfb'

    def __init__(self):
        super(DealerFactory, self).__init__()

    @classmethod
    def getDealer(cls, playMode, playerCount=-1):
        """发牌器获取工厂
        输入参数：
            playMode - 玩法
        
        返回值：
            对应玩法的发牌算法
        """
        dType = cls.getDealerTypeByPlayMode(playMode, playerCount)
        ftlog.debug('dealer type: ', dType)

        if dType == cls.DEALER_SANMEN_WUFENG:
            return SanMenNoFengDealer()
        elif dType == cls.DEALER_ALL_COLORS:
            return AllColorDealer()
        elif dType == cls.DEALER_SANMENG_ZHONG:
            return SanMenWithZhonggDealer()
        elif dType == cls.DEALER_TONGTIAO_ZFB:
            return TongTiaoWithZFBDealer()
        elif dType == cls.DEALER_TONGTIAO_ZHONG:
            return TongTiaoWithZhonggDealer()

        return None

    @classmethod
    def getDealerTypeByPlayMode(cls, playMode, playerCount):
        """根据玩法返回发牌类型
            后续可作为配置
        """
        ftlog.debug('DealerFactory.getDealerTypeByPlayMode playMode:', playMode, ' playerCount:', playerCount)
        if playMode == MPlayMode.SICHUAN:
            return cls.DEALER_SANMEN_WUFENG
        elif playMode == MPlayMode.GUOBIAO:
            return cls.DEALER_ALL_COLORS
        elif playMode == MPlayMode.YUNNAN:
            return cls.DEALER_ALL_COLORS
        elif playMode == MPlayMode.ZHAOTONG:
            return cls.DEALER_SANMEN_WUFENG
        elif playMode == MPlayMode.HAERBIN:
            return cls.DEALER_SANMENG_ZHONG
        elif playMode == MPlayMode.JIXI:
            if playerCount == 3:
                return cls.DEALER_TONGTIAO_ZHONG
            else:
                return cls.DEALER_SANMENG_ZHONG
        elif MPlayMode().isSubPlayMode(playMode, MPlayMode.KAWUXING):
            return cls.DEALER_TONGTIAO_ZFB

        return None
