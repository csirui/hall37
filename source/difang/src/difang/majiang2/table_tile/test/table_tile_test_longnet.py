# -*- coding=utf-8
'''
Created on 2016年9月23日
牌桌麻将牌的管理器
包括：
1）发牌
2）牌桌上的出牌
3）宝牌

发牌说明：
发牌涉及到好牌点
@author: zhaol
'''
import json

from difang.majiang2.table_tile.test.table_tile_test import MTableTileTest
from freetime.util import log as ftlog
from poker.entity.dao import daobase


class MTableTileTestLongNet(MTableTileTest):
    def __init__(self, playerCount, playMode):
        super(MTableTileTestLongNet, self).__init__(playerCount, playMode)

    def initTiles(self):
        """初始化手牌，用于摆牌测试"""
        key = 'put_card:' + self.playMode
        ftlog.debug('MTableTileTestLongNet key:', key)

        tile_info = daobase.executeMixCmd('get', key)
        ftlog.debug('MTableTileTestLongNet.initTiles tile_info:', tile_info)
        if not tile_info:
            return False

        tileObj = json.loads(tile_info)

        seat1 = tileObj.get('seat1', [])
        seat2 = tileObj.get('seat2', [])
        seat3 = tileObj.get('seat3', [])
        seat4 = tileObj.get('seat4', [])
        pool = tileObj.get('pool', [])
        # 数据校验
        if len(seat1) > 13:
            return False
        if len(seat2) > 13:
            return False
        if len(seat3) > 13:
            return False
        if len(seat4) > 13:
            return False

        self.setHandTiles([seat1, seat2, seat3, seat4])
        self.setTiles(pool)

        return True
