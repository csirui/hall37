# -*- coding=utf-8
'''
Created on 2016年9月23日
听牌规则
@author: zhaol
'''
from difang.majiang2.ai.ting import MTing
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.table.table_config_define import MTDefine
from difang.majiang2.tile.tile import MTile
from difang.majiang2.ting_rule.ting_rule import MTingRule
from difang.majiang2.win_rule.win_rule_haerbin import MWinRuleHaerbin
from freetime.util import log as ftlog


class MTingHaerbinRule(MTingRule):
    """听牌规则
    1）听牌时，牌中必须带至少一个“幺”或“九”。
    2）听牌时，牌中必须带至少一组刻牌（即三张一样的牌，一对红中一般可以代替）。特例：没有刻牌，可以和对倒。和牌时必须至少有一组顺牌（例123或789）
    3）红中就可代替这个“幺九牌条件”。
    4）必需先开门（非“门清”状态）才能听牌，即必须吃、碰一组牌后才可听牌。
    5）特殊玩法：吃听。当手牌吃一次就可以上听时，别人打出一张要吃的牌，不管是不是上家都可以吃。吃后自动报听(注:只有在听牌状态下才可胡牌)
    6）配置了夹起步选项时只能和夹和3，7
    """

    def __init__(self):
        super(MTingHaerbinRule, self).__init__()

    def getKeCount(self, patterns):
        """
        patterns当中有几个刻
        [[6, 6], [5, 6, 7], [4, 5, 6], [1, 2, 3]]
        """
        count = 0
        for pattern in patterns:
            if (len(pattern) == 2) and (pattern[0] == MTile.TILE_HONG_ZHONG):
                count += 1

            if (len(pattern) == 3) and (pattern[0] == pattern[1]) and (pattern[1] == pattern[2]):
                count += 1
        return count

    def getShunCount(self, patterns):
        """获取顺子的数量"""
        count = 0
        for p in patterns:
            if len(p) != 3:
                continue

            if (p[0] + 2 == p[2]) and (p[1] + 1 == p[2]):
                count += 1

        return count

    def canTing(self, tiles, leftTiles, tile, magicTiles=[]):
        """子类必须实现
        参数：
        1）tiles 该玩家的手牌
        2）leftTiles 剩余手牌
        返回值：
        是否可以听牌，听牌详情
        """
        handCount = len(tiles[MHand.TYPE_HAND])
        if handCount < 5:
            return False, []

        #         ftlog.debug( 'MTingHaerbinRule.canTing 0 tiles:', tiles )
        isTing, tingResults = MTing.canTing(MTile.cloneTiles(tiles), leftTiles, self.winRuleMgr, tile, magicTiles)
        #         ftlog.debug( 'MTingHaerbinRule.canTing 1 tiles:', tiles )
        ftlog.debug('MTingHaerbinRule.MTing.canTing isTing:', isTing, ' tingResults:', tingResults)
        #         [{'dropTile': 11, 'winNodes': [{'winTile': 1, 'winTileCount': 3, 'pattern': [[6, 6], [5, 6, 7], [4, 5, 6], [1, 2, 3]]}, {'winTile': 2, 'winTileCount': 2, 'pattern': [[6, 6, 6], [5, 6, 7], [3, 4, 5], [2, 2]]}, {'winTile': 4, 'winTileCount': 3, 'pattern': [[6, 6], [5, 6, 7], [4, 5, 6], [2, 3, 4]]}, {'winTile': 5, 'winTileCount': 2, 'pattern': [[6, 6, 6], [5, 6, 7], [5, 5], [2, 3, 4]]}, {'winTile': 7, 'winTileCount': 1, 'pattern': [[6, 6], [5, 6, 7], [5, 6, 7], [2, 3, 4]]}, {'winTile': 8, 'winTileCount': 1, 'pattern': [[6, 7, 8], [6, 6, 6], [5, 5], [2, 3, 4]]}]}]

        if not isTing:
            return False, []

        chiCount = len(tiles[MHand.TYPE_CHI])
        pengCount = len(tiles[MHand.TYPE_PENG])
        gangCount = len(tiles[MHand.TYPE_GANG])

        if (chiCount + pengCount + gangCount) == 0:
            return False, []

        # 检查刻，刻的来源，碰牌/明杠牌/手牌
        keCount = pengCount + gangCount
        # 必须有顺牌
        shunCount = chiCount

        newTingResults = []
        for tingResult in tingResults:
            newWinNodes = []
            winNodes = tingResult['winNodes']
            for winNode in winNodes:
                newTiles = MTile.cloneTiles(tiles)
                newTiles[MHand.TYPE_HAND].remove(tingResult['dropTile'])
                newTiles[MHand.TYPE_HAND].append(winNode['winTile'])
                tileArr = MTile.changeTilesToValueArr(MHand.copyAllTilesToList(newTiles))
                #       ftlog.debug( 'MTingHaerbinRule.canTing tileArr:', tileArr )

                # 夹起步(顺牌只能和夹和3，7) 除单吊
                chunJiaConfig = self.getTableConfig(MTDefine.MIN_MULTI, 0)
                if chunJiaConfig:
                    chunJiaContinue = False
                    patterns = winNode['pattern']
                    for pattern in patterns:
                        if winNode['winTile'] in pattern:
                            if len(pattern) == 3 and pattern[0] != pattern[1]:
                                if (pattern.index(winNode['winTile'])) == 2 and MTile.getValue(winNode['winTile']) != 3:
                                    chunJiaContinue = True
                                    break
                                if (pattern.index(winNode['winTile'])) == 0 and MTile.getValue(winNode['winTile']) != 7:
                                    chunJiaContinue = True
                                    break

                            # 夹起步不能和对倒
                            if len(pattern) == 3 and pattern[0] == pattern[1]:
                                chunJiaContinue = True
                                break

                    if chunJiaContinue:
                        ftlog.debug('MTingHaerbinRule.canTing chunJiaConfig:', chunJiaConfig, ' can not win tile:',
                                    winNode['winTile'], ', continue....')
                        continue

                if self.getTableConfig(MTDefine.YISE_CAN_TING, 0) != 1:
                    # 清一色不可以听牌/和牌
                    colorCount = MTile.getColorCount(tileArr)
                    if colorCount == 1:
                        # 清一色不能和牌
                        ftlog.debug('MTingHaerbinRule.canTing colorCount:', colorCount, ' can not win, continue....')
                        continue

                zhongCount = tileArr[MTile.TILE_HONG_ZHONG]
                #         ftlog.debug( 'MTingHaerbinRule.canTing hongzhong count: ', zhongCount )

                # 检查牌中的幺/九
                yaoCount = tileArr[MTile.TILE_ONE_WAN] + tileArr[MTile.TILE_ONE_TONG] + tileArr[MTile.TILE_ONE_TIAO]
                jiuCount = tileArr[MTile.TILE_NINE_WAN] + tileArr[MTile.TILE_NINE_TONG] + tileArr[MTile.TILE_NINE_TIAO]
                #         ftlog.debug( 'MTingHaerbinRule.canTing yaoCount:', yaoCount, ' jiuCount:', jiuCount )

                if (yaoCount + jiuCount + zhongCount) == 0:
                    continue

                patterns = winNode['pattern']
                checkKeCount = keCount + self.getKeCount(patterns)
                checkShunCount = shunCount + self.getShunCount(patterns)
                ftlog.debug('MTingHaerbinRule.canTing keCount:', keCount, ' shunCount:', shunCount)

                if checkKeCount and checkShunCount:
                    newWinNodes.append(winNode)

            if len(newWinNodes) > 0:
                newTingResult = {}
                newTingResult['dropTile'] = tingResult['dropTile']
                newTingResult['winNodes'] = newWinNodes
                newTingResults.append(newTingResult)

        return len(newTingResults) > 0, newTingResults


if __name__ == "__main__":
    tiles = [[3, 4, 15, 5, 5, 6, 9, 9], [[26, 27, 28]], [[8, 8, 8]], [], [], []]
    rule = MTingHaerbinRule()
    rule.setWinRuleMgr(MWinRuleHaerbin())
    ftlog.debug(rule.canTing(tiles, [], 4, []))
