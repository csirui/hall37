# -*- coding=utf-8
"""
Created on 2016年9月23日

@author: zhaol
"""


class MPlayMode(object):
    # 最简单的麻将玩法
    SIMPLE = 'simple'
    # 四川玩法
    SICHUAN = 'sichuan'
    # 国标玩法
    GUOBIAO = 'guobiao'
    # 哈尔滨玩法
    HAERBIN = 'harbin'
    # 云南幺鸡麻将
    YUNNAN = 'qujing'
    # 湖北卡五星
    KAWUXING = 'kawuxing'
    # 云南昭通麻将
    ZHAOTONG = "zhaotong"
    # 鸡西麻将
    JIXI = "jixi"
    # 济南麻将
    JINAN = "jinan"

    def __init__(self):
        super(MPlayMode, self).__init__()

    def isSubPlayMode(self, curPlayMode, defPlayMode):
        """
        :param curPlayMode:
        :param defPlayMode:
        :return:
        """
        if curPlayMode.find('#'):
            # 为支持各种玩法自类型，例如，随州卡五星定义为kawuxing#suizhou
            return curPlayMode.split('#')[0] == defPlayMode
        else:
            return curPlayMode == defPlayMode
