# -*- coding=utf-8
"""
Created on 2016年9月23日

@author: zhaol
"""


class MTDefine(object):
    """麻将牌桌配置，room.json中的tableConfig"""
    # 用户坐下后的准备状态
    READY_AFTER_SIT = 'ready_after_sit'
    # 清一色是否可以听牌
    YISE_CAN_TING = 'qingyise_can_ting'
    # 牌池还剩多少张牌时不可点炮，只能自摸
    TILES_NO_PAO = 'tiles_no_pao'
    # 手牌张数
    HAND_COUNT = 'hand_tiles_count'
    # 手牌默认张数
    HAND_COUNT_DEFAULT = 13
    # 杠牌的默认积分
    GANG_BASE = 'gang_base'
    # 和牌的起始番数
    WIN_BASE = 'win_base'
    # 用户的积分带入
    SCORE_BASE = 'score_base'
    # 番型对应的输赢倍数
    FAN_LIST = 'fan_list'
    # 哈麻中边牌的倍数
    BIAN_MULTI = 'bian_multi'
    # 换宝，哈麻中的换宝开关
    CHANGE_MAGIC = 'change_baopai'
    # 最小赢牌倍数
    MIN_MULTI = 'min_multi'
    # 红中宝开关
    HONG_ZHONG_BAO = 'hong_zhong_bao'
    # 闭门算番(鸡西麻将默认闭门不算番)
    BI_MEN_FAN = 'bi_men_fan'
    # 最后兑奖算番(鸡西麻将默认最后抽奖的数量)
    AWARD_TILE_COUNT = 'award_tile_count'
    # 暗宝开关(鸡西麻将默认宝牌隐藏并且没人听牌宝牌不更新)
    MAGIC_HIDE = 'magic_hide'
    # 刮大风开关
    GUA_DA_FENG = 'gua_da_feng'
    # 卡五星中频道
    PIN_DAO = 'pin_dao'
    # 卡五星中跑恰摸八
    PAOQIAMOBA = 'paoqiamoba'
    # 卡五星中定漂
    DING_PIAO = 'ding_piao'
    # 卡五星中买马
    MAI_MA = 'mai_ma'
    # 卡五星中数坎
    SHU_KAN = 'shu_kan'
    # 卡五星中听牌时亮牌规则
    LIANG_PAI = 'liang_pai'
    # 托管配置
    TRUSTTEE_TIMEOUT = 'trustee_timeout'
    NEVER_TIMEOUT = -1
    # 牌桌人数
    MAXSEATN = 'maxSeatN'
    # 无效的座位号
    INVALID_SEAT = -1
    # 最大番数
    MAX_FAN = 'max_fan'
    # 卡五星番数
    KAWUXING_FAN = 'kawuxing_fan'
    # 碰碰胡番数
    PENGPENGHU_FAN = 'pengpenghu_fan'
    # 杠上花番数
    GANGSHANGHUA_FAN = 'gangshanghua_fan'

    def __init__(self):
        super(MTDefine, self).__init__()
