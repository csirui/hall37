# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''


class MFTDefine(object):
    """好友自建桌房间相关配置宏定义"""
    # 每轮多少局
    ROUND_COUNT = 'roundCount'
    # 当前局数
    CUR_ROUND_COUNT = 'curRoundCount'
    # 房卡数量
    CARD_COUNT = 'cardCount'
    # 剩余房卡数量，每两局减少一张房卡
    LEFT_CARD_COUNT = 'leftCardCount'
    # 是否自建桌
    IS_CREATE = 'iscreate'
    # 自建桌参数
    ITEMPARAMS = 'itemParams'
    # 自建桌号
    FTID = 'ftId'
    # 自建房主
    FTOWNER = 'ftOwner'
    # 自建房描述
    CREATE_TABLE_DESCS = 'create_table_desc_list'
    # 自建房纯玩法描述(去除cardCount和playerType)
    CREATE_TABLE_PLAY_DESCS = 'create_table_play_desc_list'
    # 投票配置
    LEAVE_VOTE_NUM = 'leave_vote_num'
    # 准备超时，超时自动释放房间
    READY_TIMEOUT = 'ready_max_timeout'

    def __init__(self):
        super(MFTDefine, self).__init__()
