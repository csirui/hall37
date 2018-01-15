# -*- coding=utf-8
"""
Created on 2016年9月23日

@author: zhaol
"""
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.tile.tile import MTile, human_tiles, new_hand_tails, HandTiles
from difang.majiang2.win_rule.win_rule_factory import MWinRuleFactory
from freetime.util import log as ftlog

"""
结果样例：
[{'dropTile': 11, 'winNodes': [{'winTile': 1, 'winTileCount': 3, 'pattern': [[6, 6], [5, 6, 7], [4, 5, 6], [1, 2, 3]]}, {'winTile': 2, 'winTileCount': 2, 'pattern': [[6, 6, 6], [5, 6, 7], [3, 4, 5], [2, 2]]}, {'winTile': 4, 'winTileCount': 3, 'pattern': [[6, 6], [5, 6, 7], [4, 5, 6], [2, 3, 4]]}, {'winTile': 5, 'winTileCount': 2, 'pattern': [[6, 6, 6], [5, 6, 7], [5, 5], [2, 3, 4]]}, {'winTile': 7, 'winTileCount': 1, 'pattern': [[6, 6], [5, 6, 7], [5, 6, 7], [2, 3, 4]]}, {'winTile': 8, 'winTileCount': 1, 'pattern': [[6, 7, 8], [6, 6, 6], [5, 5], [2, 3, 4]]}]}]
"""


class MTing(object):
    """是否可以听牌
    如果可以听牌，可以和哪些牌
    判断流程：
    去掉一张手牌，加入一张牌，是否可以和
    如果可以和，去掉改手牌，进入听牌状态，和可以和的牌。可以和的牌会有多个
    
    对可以和的牌，提示剩余牌的张数
    """

    def __init__(self):
        super(MTing, self).__init__()

    @classmethod
    def chooseBestTingSolution(cls, tingReArr):
        """选择最好的听牌方案"""
        chooseTile = 0
        maxCount = 0
        chooseWinNodes = []
        for tingSolution in tingReArr:
            dropTile = tingSolution['dropTile']
            winNodes = tingSolution['winNodes']
            count = 0
            for node in winNodes:
                winTileCount = node['winTileCount']
                count += winTileCount
            if count > maxCount:
                maxCount = count
                chooseTile = dropTile
                chooseWinNodes = winNodes

        return chooseTile, chooseWinNodes

    @classmethod
    def canTing(cls, tiles, leftTiles, winRule, cur_tile, magicTiles=list()):
        """
        判断所有的听牌情况
        :param tiles 手牌
        :param leftTiles 剩余未发的牌
        :param winRule:
        :param cur_tile:
        :param magicTiles:
        :type tiles HandTiles
        :return
        """
        ftlog.debug('MTile.changeTilesToValueArr', tiles[MHand.TYPE_HAND])
        handTileArr = MTile.changeTilesToValueArr(tiles[MHand.TYPE_HAND])

        leftTileArr = MTile.changeTilesToValueArr(leftTiles)
        leftTileCount = len(leftTileArr)
        ftlog.debug('MTing.canTing leftTileArr:', leftTileArr, ' leftTileCount:', leftTileCount)

        result = []
        for tile, _ in handTileArr.tile_items():
            # 打出一张牌后可以听牌
            newTiles = HandTiles.clone(tiles)
            newTiles.dropHand(tile)
            resultNode = cls.canWinAddOneTile(leftTileArr, leftTileCount, newTiles, winRule, 0, magicTiles)
            if len(resultNode) > 0:
                winNode = {
                    'dropTile': tile,
                    'winNodes': resultNode
                }
                result.append(winNode)

        return len(result) > 0, result

    @classmethod
    def canWinAddOneTile(cls, leftTileArr, leftTileCount, tiles, winRule, last_tile, magicTiles=list()):
        """
        摸一张胡牌的检查
        :param leftTileArr:
        :param leftTileCount:
        :param tiles:
        :param winRule:
        :param last_tile: 上一张打出来的牌
        :param magicTiles:
        :return:
        :type tiles: HandTiles
        """
        result = []
        for tile, _ in leftTileArr.tile_items():
            # 剩余的牌中存在胡牌
            newTile = HandTiles.clone(tiles)
            newTile.addHand(tile)
            # 测试停牌时，默认听牌状态
            winResult, winPattern = winRule.isHu(newTile, True, tile, magicTiles)
            if winResult:
                winNode = {
                    'winTile': tile,
                    'winTileCount': leftTileArr[tile]
                }
                ftlog.debug('MTing.canWinAddOneTile winTileCount:', winNode['winTileCount'])
                winNode['pattern'] = winPattern
                result.append(winNode)

        return result


if __name__ == "__main__":
    def test():
        tiles = new_hand_tails(human_tiles("幺鸡二条三条二万二万五万六万七万7筒八筒9筒5条6条4条"))
        leftTiles = human_tiles("1万1万1万2万2万4万4万4万5万5万7万8万9万2筒")
        winRule = MWinRuleFactory.getWinRule(MPlayMode.SICHUAN)
        print MTing.canTing(tiles, leftTiles, winRule, 1)


    test()
