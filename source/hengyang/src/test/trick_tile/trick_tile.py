# -*- coding=utf-8
'''
Created on 2017年3月10日
庄家规则
@author: nick.kai.lee

使用说明:
from test.trick_tile.trick_tile import HYTestTrickTile
HYTestTrickTile.Debug = True
HYTestTrickTile.Tiles[0] = [1,2,3,4,4,4,7,8,8,8,12,13,14,4]
HYTestTrickTile.Tiles[1] = [1,2,3,5,5,6,7,8,9,11,12,13,14,8]
HYTestTrickTile.Tiles[2] = [1,2,3,4,5,6,7,8,9,11,12,13,14]
HYTestTrickTile.Tiles[3] = [1,2,3,4,5,6,7,8,9,11,12,13,14]
'''
from hengyangmj.hengyang_log import HYLog


class HYTestTrickTile(object):
	"""
	指定发牌
	"""
	Debug = False  # 开启时才能获取
	Tiles = [[], [], [], []]