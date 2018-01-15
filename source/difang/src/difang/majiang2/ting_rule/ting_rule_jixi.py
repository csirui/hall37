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
from difang.majiang2.win_rule.win_rule_jixi import MWinRuleJixi
from freetime.util import log as ftlog


class MTingJixiRule(MTingRule):
    """听牌规则
    1）听牌时，牌中必须带至少一个“幺”或“九”（飘[全是刻牌]和七小对可以没有1，9）
    2）听牌时，牌中必须带至少一组刻牌（即三张一样的牌，一对红中一般可以代替）。特例：没有刻牌，可以和对倒。和牌时必须至少有一组顺牌（例123或789）
    3）红中就可代替这个“幺九牌条件”。
    4）[鸡西闭门可以听牌]必需先开门（非“门清”状态）才能听牌，即必须吃、碰一组牌后才可听牌。
    5）清一色可以听牌／和牌
    6）听牌不一定要有顺牌（飘和七小对） 检查飘和七小对
    5）特殊玩法：吃听。当手牌吃一次就可以上听时，别人打出一张要吃的牌，不管是不是上家都可以吃。吃后自动报听(注:只有在听牌状态下才可胡牌)
    6）配置了夹起步选项时只能和夹和3，7
    """

    def __init__(self):
        super(MTingJixiRule, self).__init__()

    def isPiaoHu(self, patterns, newTiles):

        shunCount = self.getShunCount(patterns)
        shunCount += len(newTiles[MHand.TYPE_CHI])
        if shunCount > 0:
            return False

        keCount = self.getKeCount(patterns)
        keCount += len(newTiles[MHand.TYPE_PENG])
        keCount += len(newTiles[MHand.TYPE_GANG])

        if keCount == 0:  # 七小对
            return False

        return True

    def isQiDui(self, patterns, newTiles):

        shunCount = self.getShunCount(patterns)
        shunCount += len(newTiles[MHand.TYPE_CHI])

        if shunCount > 0:
            return False

        keCount = self.getKeCount(patterns)
        keCount += len(newTiles[MHand.TYPE_PENG])
        keCount += len(newTiles[MHand.TYPE_GANG])

        if keCount > 0:
            return False

        return True

    def tingQiDui(self, tiles, cur_tile, leftTiles):
        """
        检查是否可以听七小对
        二种牌型可听
        * 别人打牌 五对(包括杠) 一刻 粘一张
        * 自己上牌 六对(包括杠) 两个单张
        :param tiles 手牌
        :param cur_tile 刚刚摸的牌
        :param leftTiles: 全局剩余的牌
        :return
          [
            {
              'isQiDui' : 1
              'dropTile' : 11, # 出牌`一筒`
              'winNodes' : [{ # 听牌细节
                  'winTile' : 1, # 听`一万`
                  'winTileCount' : 3, # 剩`三张一万`
                  'pattern' : [
                    [6, 6], # 听牌的条件
                    ...
                  ]
                }]
            }
          ]
        """
        ftlog.debug('MTingHaerbinJixi.MTing.tingQiDui handTiles:', tiles[MHand.TYPE_HAND], ' tile:', cur_tile)
        handTiles = tiles[MHand.TYPE_HAND]
        newHandTiles = MTile.cloneTiles(handTiles)
        # 不考虑摸牌
        newHandTiles.remove(cur_tile)
        if len(newHandTiles) < 13:
            # 手牌不够
            return False, []

        newHandTilesArr = MTile.changeTilesToValueArr(newHandTiles)
        duiCount = 0
        singleTiles = []
        duiPattern = []
        for tile, number in newHandTilesArr.tile_items():
            if number == 2:
                # 对
                duiCount += 1
                duiPattern.append([tile, tile])
            elif number == 4:
                # 杠算两对
                duiCount += 2
                duiPattern.append([tile, tile])
                duiPattern.append([tile, tile])
            elif number == 3:
                # 碰
                if tile != cur_tile:
                    # 摸牌不能凑杠 有单张了
                    singleTiles.append(tile)
                duiPattern.append([tile, tile])
            elif tile != cur_tile:
                # 摸牌不能凑对 有单张了
                singleTiles.append(tile)
            else:
                duiPattern.append([cur_tile, cur_tile])

        if len(singleTiles) != 2:
            # 单张过多不能听七对
            # 单张过少则已经可以胡牌(不能听了)
            # ftlog.debug('MTingJixiRule.MTing.canTing tingQiDui the singleTiles count error: ', len(singleTiles))
            return False, []

        # 站牌处理 手里有五对 并且有一张或三张上的牌 那么可以听 方案就是剩下的两张
        newLeftTilesArr = MTile.changeTilesToValueArr(leftTiles)
        tingResult = [{  # 听第2张单牌
            'isQiDui': 1,
            'dropTile': singleTiles[0],
            'winNodes': [{
                'winTile': singleTiles[1],
                'winTileCount': newLeftTilesArr[singleTiles[1]],
                'pattern': duiPattern + [[singleTiles[1], singleTiles[1]]]
            }]
        }, {  # 听第1张单牌
            'isQiDui': 1,
            'dropTile': singleTiles[1],
            'winNodes': [{
                'winTile': singleTiles[0],
                'winTileCount': newLeftTilesArr[singleTiles[0]],
                'pattern': duiPattern + [[singleTiles[0], singleTiles[0]]]
            }]
        }]

        return True, tingResult

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

        if len(tiles[MHand.TYPE_CHI]) == 0 and len(tiles[MHand.TYPE_PENG]) == 0 and len(tiles[MHand.TYPE_GANG]) == 0:
            isTing, tingResults = self.tingQiDui(tiles, tile, leftTiles)
            if isTing:
                ftlog.debug('MTingJixiRule.MTing.canTing tingQiDui tingResults:', tingResults)
                return isTing, tingResults

                #         ftlog.debug( 'MTingJixiRule.canTing 0 tiles:', tiles )
        isTing, tingResults = MTing.canTing(MTile.cloneTiles(tiles), leftTiles, self.winRuleMgr, tile, magicTiles)
        #         ftlog.debug( 'MTingJixiRule.canTing 1 tiles:', tiles )
        ftlog.debug('MTingJixiRule.MTing.canTing isTing:', isTing, ' tingResults:', tingResults)

        if not isTing:
            return False, []

        pengCount = len(tiles[MHand.TYPE_PENG])
        gangCount = len(tiles[MHand.TYPE_GANG])

        # 检查刻，刻的来源，碰牌/明杠牌/手牌
        keCount = pengCount + gangCount

        newTingResults = []
        for tingResult in tingResults:
            newWinNodes = []
            winNodes = tingResult['winNodes']
            for winNode in winNodes:
                newTiles = MTile.cloneTiles(tiles)
                newTiles[MHand.TYPE_HAND].remove(tingResult['dropTile'])
                newTiles[MHand.TYPE_HAND].append(winNode['winTile'])
                tileArr = MTile.changeTilesToValueArr(MHand.copyAllTilesToList(newTiles))
                patterns = winNode['pattern']
                isQiDui = False
                isPiaoHu = self.isPiaoHu(patterns, newTiles)

                # 飘和七对可以手把一
                if (isPiaoHu or isQiDui):
                    if handCount < 1:
                        continue
                else:
                    if handCount < 5:
                        continue

                # 夹起步(顺牌只能和夹和3，7) 不能和两头 可以单吊
                chunJiaConfig = self.getTableConfig(MTDefine.MIN_MULTI, 0)
                if chunJiaConfig:
                    bianMulti = self.tableConfig.get(MTDefine.BIAN_MULTI, 0)
                    hasJia = False
                    for pattern in patterns:
                        if winNode['winTile'] in pattern:
                            if len(pattern) == 3 and pattern[0] != pattern[1]:
                                if pattern.index(winNode['winTile']) == 2:
                                    if bianMulti:
                                        if MTile.getValue(winNode['winTile']) == 3:
                                            hasJia = True
                                            break
                                if pattern.index(winNode['winTile']) == 0:
                                    if bianMulti:
                                        if MTile.getValue(winNode['winTile']) == 7:
                                            hasJia = True
                                            break

                                if pattern.index(winNode['winTile']) == 1:
                                    hasJia = True
                                    break

                            # 单吊
                            if len(pattern) == 2 and pattern[0] == pattern[1]:
                                hasJia = True
                                break

                    if not hasJia:
                        ftlog.debug('MTingHaerbinRule.canTing :, can not win tile:', winNode['winTile'],
                                    ', not has jia continue....')
                        continue

                zhongCount = tileArr[MTile.TILE_HONG_ZHONG]

                # 检查牌中的幺/九
                yaoCount = tileArr[MTile.TILE_ONE_WAN] + tileArr[MTile.TILE_ONE_TONG] + tileArr[MTile.TILE_ONE_TIAO]
                jiuCount = tileArr[MTile.TILE_NINE_WAN] + tileArr[MTile.TILE_NINE_TONG] + tileArr[MTile.TILE_NINE_TIAO]

                # 飘和七小对不需要1,9
                if (yaoCount + jiuCount + zhongCount) == 0 and (not isPiaoHu) and (not isQiDui):
                    continue

                patterns = winNode['pattern']
                checkKeCount = keCount + self.getKeCount(patterns)
                ftlog.debug('MTingHaerbinRule.canTing keCount:', keCount)

                # 胡牌必须有刻牌 七小对除外
                if checkKeCount or isQiDui:
                    newWinNodes.append(winNode)

            if len(newWinNodes) > 0:
                newTingResult = {}
                newTingResult['dropTile'] = tingResult['dropTile']
                newTingResult['winNodes'] = newWinNodes
                newTingResults.append(newTingResult)

        return len(newTingResults) > 0, newTingResults


if __name__ == "__main__":
    def test():
        tiles = [[13, 13, 15, 15, 16, 17, 21, 21, 21, 25, 26, 27, 28, 29], [], [], [], [], []]
        rule = MTingJixiRule()
        rule.setWinRuleMgr(MWinRuleJixi())
        ftlog.debug(rule.canTing(tiles, [], 21, []))


    test()
