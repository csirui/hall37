# -*- coding=utf-8
'''
Created on 2016年11月18日
庄家规则
@author: zhangwei
'''
import copy

from difang.majiang2.ai.win import MWin
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.tile.tile import MTile
from difang.majiang2.win_rule.win_rule import MWinRule
from freetime.util import log as ftlog


class MWinRuleYunnan(MWinRule):
    """开局随机庄家，之后连庄的规则
    庄家赢，连庄
    闲家赢，闲家坐庄
    """

    def __init__(self):
        super(MWinRuleYunnan, self).__init__()

    def isHu(self, tiles, tile, isTing, getTileType, magicTiles=[], tingNodes=[]):
        """
            tiles:玩家所有的牌,但是手牌是加入了要胡的那张牌的
        
        """
        # 云南曲靖麻将无听牌
        laiziDandiao = self.itemParams.get('laiziDandiao', 1)
        ftlog.debug('MWinRuleYunnan.isHu tiles:', tiles
                    , 'tile:', tile
                    , 'magicTils:', magicTiles
                    , 'laiziDandiao:', laiziDandiao)
        if getTileType == MWinRule.WIN_BY_MYSELF:
            return MWinRuleYunnan.checkHuByMagicTiles(tiles, magicTiles)
        elif getTileType == MWinRule.WIN_BY_OTHERS:
            # 判定无赖子胡,如果能胡可以胡,注意这时候不一定是无鸡
            resultWithoutMagic, patterns = MWinRuleYunnan.checkHuByMagicTiles(tiles, [])
            for magicTile in magicTiles:
                magicGangCount = 0
                for gang in tiles[MHand.TYPE_GANG]:
                    tempGang = copy.deepcopy(gang)
                    while magicTile in tempGang['pattern']:
                        magicGangCount += 1
                        tempGang['pattern'].remove(magicTile)
                    if magicGangCount != 0 and magicGangCount != 4:
                        resultWithoutMagic = False
                        break
            if resultWithoutMagic:
                return resultWithoutMagic, patterns
            # 先判一次胡,如果不能胡就不走下面的流程,这次判胡是假设拿到的赖子可以当赖子用
            # 而且有赖子的情况下也可以点炮,后面分别排除两种情况
            result, _ = MWinRuleYunnan.checkHuByMagicTiles(tiles, magicTiles)
            if result == False:
                return False, []
            # 没赖子直接判胡
            haveMagicCount = 0
            needNextJudge = 0
            tileArr = MHand.copyAllTilesToList(tiles)
            ftlog.debug('MWinRuleYunnan.isHu tileArr:', tileArr)
            tempArr = copy.deepcopy(tileArr)
            for magicTile in magicTiles:
                while magicTile in tempArr:
                    haveMagicCount += 1
                    tempArr.remove(magicTile)
            if haveMagicCount >= 1:
                # 先判断拿到的是不是幺鸡
                if tile == MTile.TILE_ONE_TIAO:
                    if haveMagicCount == 1:
                        # 只有点炮的这一张幺鸡,可以进入判定,能胡幺鸡就让胡
                        return MWinRuleYunnan.checkHuByMagicTiles(tiles, [])
                    else:
                        # 两张或者以上的幺鸡,得看番型,进入下一步判断
                        needNextJudge = 1
                else:
                    # 拿到的不是幺鸡,又有幺鸡,得看番型,进入下一步判断
                    needNextJudge = 2
            else:
                # 没有幺鸡,直接判定能不能胡   
                return MWinRuleYunnan.checkHuByMagicTiles(tiles, [])

            # 计算番型,如果有番就可胡
            if needNextJudge == 1:
                # 这种情况有两张或者以上的幺鸡,并且胡的也是幺鸡本身
                # 拿0替换幺鸡,判断用0当赖子是否能胡
                # 这里是配置项里幺鸡单吊幺鸡的情况,此情况下配置项不影响
                transferTiles = copy.deepcopy(tiles)
                while MTile.TILE_ONE_TIAO in transferTiles[MHand.TYPE_HAND]:
                    transferTiles[MHand.TYPE_HAND].remove(MTile.TILE_ONE_TIAO)
                    transferTiles[MHand.TYPE_HAND].append(0)
                transferTiles[MHand.TYPE_HAND].remove(0)
                transferTiles[MHand.TYPE_HAND].append(MTile.TILE_ONE_TIAO)
                result, _ = MWinRuleYunnan.checkHuByMagicTiles(transferTiles, [0])
                tempMagicCount = haveMagicCount - 1
                isSpecialHu = MWinRuleYunnan.checkSpecialHu(transferTiles, [0], tempMagicCount, tile)
                if isSpecialHu and result:
                    return True, tiles[MHand.TYPE_HAND]
            elif needNextJudge == 2:
                # 这里判断的前提是幺鸡做赖子能胡,但是做普通牌不能胡,且拿到的牌也不是幺鸡
                # 只判断幺鸡做赖子有特殊番型,不用判断成牌
                # 这里处理配置项里幺鸡单吊非幺鸡的情况,根据配置项决定是否可胡
                isSpecialHu = MWinRuleYunnan.checkSpecialHu(tiles, magicTiles, haveMagicCount, tile)
                # 杠上炮和抢杠胡
                if isSpecialHu == False:
                    if self.lastGangSeat == self.curSeatId:
                        isSpecialHu = True
                if isSpecialHu:
                    # 有特殊牌型了还得判断是否是幺鸡单吊,如果是要看配置
                    testTiles = []
                    if tile / 10 == 0:
                        testTiles.append(16)
                        testTiles.append(28)
                        testTiles.append(32)
                    elif tile / 10 == 1:
                        testTiles.append(6)
                        testTiles.append(28)
                        testTiles.append(32)
                    elif tile / 10 == 2:
                        testTiles.append(5)
                        testTiles.append(16)
                        testTiles.append(32)
                    elif tile / 10 == 3:
                        testTiles.append(5)
                        testTiles.append(16)
                        testTiles.append(28)
                    else:
                        return False, []
                    dandiao = True
                    for testTile in testTiles:
                        tempDandiao = copy.deepcopy(tiles)
                        if tile in tempDandiao[MHand.TYPE_HAND]:
                            tempDandiao[MHand.TYPE_HAND].remove(tile)
                        tempDandiao[MHand.TYPE_HAND].append(testTile)
                        resultDandiao, _ = MWinRuleYunnan.checkHuByMagicTiles(tempDandiao, magicTiles)
                        if not resultDandiao:
                            dandiao = False
                    if dandiao:
                        if laiziDandiao == 2:
                            return True, tiles[MHand.TYPE_HAND]
                    else:
                        return True, tiles[MHand.TYPE_HAND]
        elif getTileType == MWinRule.WIN_BY_QIANGGANGHU:
            # 抢杠胡,抢到赖子只能当幺鸡,但是本身的赖子可以用
            if tile == MTile.TILE_ONE_TIAO:
                # 抢到的是幺鸡,当普通牌使用,抢杠胡不需再判断其它特殊牌型
                transferTiles = copy.deepcopy(tiles)
                while MTile.TILE_ONE_TIAO in transferTiles[MHand.TYPE_HAND]:
                    transferTiles[MHand.TYPE_HAND].remove(MTile.TILE_ONE_TIAO)
                    transferTiles[MHand.TYPE_HAND].append(0)
                transferTiles[MHand.TYPE_HAND].remove(0)
                transferTiles[MHand.TYPE_HAND].append(MTile.TILE_ONE_TIAO)
                result, _ = MWinRuleYunnan.checkHuByMagicTiles(transferTiles, [0])
                if result:
                    return True, tiles[MHand.TYPE_HAND]
            else:
                return MWinRuleYunnan.checkHuByMagicTiles(tiles, magicTiles)
        return False, []

    def isPassHu(self):
        """是否有漏胡规则"""
        return True

    def isAddHu(self, player, tile):
        """判断上牌即胡的类型"""
        nowTiles = player.copyTiles()
        ftlog.debug('MWinRuleYunnan.isAddHu nowHandTiles:', nowTiles[MHand.TYPE_HAND])
        if nowTiles[MHand.TYPE_HAND].count(MTile.TILE_ONE_TIAO) == 4:
            return True
        return False

    def isDropHu(self, player):
        """判断出牌即胡的牌型"""
        dropTiles = self.tableTileMgr.dropTiles
        ftlog.debug('MWinRuleYunnan.isDropHu dropTiles:', dropTiles)
        nowTiles = player.copyTiles()
        seatId = player.curSeatId
        ftlog.debug('MWinRuleYunnan.isDropHu nowHandTiles:', nowTiles[MHand.TYPE_HAND])
        if MWinRuleYunnan.isShifeng(dropTiles, nowTiles, seatId):
            return True, dropTiles[seatId]
        if MWinRuleYunnan.isShisanyao(dropTiles, nowTiles, seatId):
            return True, dropTiles[seatId]
        return False, []

    @classmethod
    def isPairs(cls, tiles, magicTiles):
        if len(tiles[MHand.TYPE_CHI]) != 0:
            return False
        if len(tiles[MHand.TYPE_PENG]) != 0:
            return False
        if len(tiles[MHand.TYPE_GANG]) != 0:
            return False
        pairTiles = copy.deepcopy(tiles[MHand.TYPE_HAND])

        haveMagicCount = 0
        for magicTile in magicTiles:
            while magicTile in pairTiles:
                pairTiles.remove(magicTile)
                haveMagicCount += 1
        ftlog.debug("win_rule_yunnan::isPairs pairTiles = ", pairTiles, "haveMagicCount =", haveMagicCount)
        tileArr = MTile.changeTilesToValueArr(pairTiles)
        for count in tileArr:
            if count % 2 == 0:
                continue
            else:
                if haveMagicCount <= 0:
                    return False
                else:
                    haveMagicCount -= 1
                    continue
        return True

    @classmethod
    def isLanPaiHu(cls, tiles, magicTiles):
        """先做简单的牌型检查,如果符合再进行细节判断"""
        if len(tiles[MHand.TYPE_CHI]) != 0:
            return False
        if len(tiles[MHand.TYPE_PENG]) != 0:
            return False
        if len(tiles[MHand.TYPE_GANG]) != 0:
            return False
        # 去除手牌赖子,并计数
        haveMagicCount = 0
        lanpaiTiles = copy.deepcopy(tiles[MHand.TYPE_HAND])
        for magicTile in magicTiles:
            while magicTile in lanpaiTiles:
                lanpaiTiles.remove(magicTile)
                haveMagicCount += 1
        tileArr = MTile.changeTilesToValueArr(lanpaiTiles)
        # 去除赖子后手牌数不能有超过2张的
        for count in tileArr:
            if count <= 1:
                continue
            else:
                return False

        # 去除赖子后不重复字牌加赖子数要大于等于5,并且可用赖子数＝字牌＋赖子-5
        # canUseMagicCount = haveMagicCount
        tempFengTiles = MTile.traverseTile(MTile.TILE_FENG)
        fengArr = tileArr[tempFengTiles[0]:tempFengTiles[len(tempFengTiles) - 1] + 1]

        # 检查字牌种类和每种的数量,之前因为已经判断过数量小于等于1,这里不再重复
        fengCount = 0
        for count in fengArr:
            if count == 1:
                fengCount += 1

        # 如果字牌每种不超过1张且有五种,开始判断其它花色
        if fengCount + haveMagicCount >= 5:
            # 分别判断三种花色
            if cls.checkBukao(tileArr, MTile.TILE_WAN) and cls.checkBukao(tileArr, MTile.TILE_TONG) and cls.checkBukao(
                    tileArr, MTile.TILE_TIAO):
                return True
        else:
            return False

        return False

    @classmethod
    def isShifeng(cls, dropTiles, nowTiles, seatId):
        """特殊牌型十风的胡牌判断"""
        # 十风和十三幺都是必须从开局开始连出,并且不能吃碰杠
        if len(dropTiles[seatId]) <= 0:
            return False
        else:
            if len(nowTiles[MHand.TYPE_CHI]) > 0 or len(nowTiles[MHand.TYPE_PENG]) > 0 or len(
                    nowTiles[MHand.TYPE_GANG]) > 0:
                return False
            if not cls.isZipai(dropTiles[seatId][0]):
                return False
            count = 0
            for tempTile in dropTiles[seatId]:
                if cls.isZipai(tempTile):
                    count += 1
                else:
                    count = 0
                    break
            if count >= 10:
                return True
        return False

    @classmethod
    def isShisanyao(cls, dropTiles, nowTiles, seatId):
        """特殊牌型十三幺的胡牌判断"""
        # 十风和十三幺都是必须从开局开始连出,并且不能吃碰杠
        if len(dropTiles[seatId]) <= 0:
            return False
        else:
            if len(nowTiles[MHand.TYPE_CHI]) > 0 or len(nowTiles[MHand.TYPE_PENG]) > 0 or len(
                    nowTiles[MHand.TYPE_GANG]) > 0:
                return False
            if not cls.isYaopai(dropTiles[seatId][0]):
                return False
            count = 0
            for tempTile in dropTiles[seatId]:
                if cls.isYaopai(tempTile):
                    count += 1
                else:
                    count = 0
                    break
            if count >= 13:
                return True
        return False

    @classmethod
    def isZipai(cls, tile):
        """检查满足十风的牌型"""
        if tile >= MTile.TILE_DONG_FENG and tile <= MTile.TILE_BAI_BAN:
            return True
        return False

    @classmethod
    def isYaopai(cls, tile):
        """检查满足十三幺的牌型"""
        if tile >= MTile.TILE_DONG_FENG and tile <= MTile.TILE_BAI_BAN:
            return True
        if tile % 10 == 1 or tile % 10 == 9:
            return True
        return False

    @classmethod
    def checkBukao(cls, tileArr, tileType):
        """烂牌检查三种花色的不靠"""
        tempTiles = MTile.traverseTile(tileType)
        colorArr = tileArr[tempTiles[0]:tempTiles[len(tempTiles) - 1] + 1]
        colorTiles = []
        for i in range(len(colorArr)):
            if colorArr[i] > 0:
                colorTiles.append(i)
            if len(colorTiles) > 3:
                return False
            # 然后只需要判断不靠即可
            elif len(colorTiles) == 2:
                if (colorTiles[0] - colorTiles[1]) % 3 != 0:
                    return False
            elif len(colorTiles) == 3:
                if (colorTiles[0] - colorTiles[1]) % 3 != 0 or (colorTiles[0] - colorTiles[2]) % 3 != 0 or (
                    colorTiles[1] - colorTiles[2]) % 3 != 0:
                    return False
        return True

    @classmethod
    def checkHuByMagicTiles(cls, tiles, magicTiles):
        # 判断七对系列
        if cls.isPairs(tiles, magicTiles):
            return True, tiles[MHand.TYPE_HAND]

        # 判定五六七星烂,手牌数必须为14,所有花色最多一张牌,字牌不重复且大于等于5种,其它花色必须都存在且互相不靠
        if cls.isLanPaiHu(tiles, magicTiles):
            return True, tiles[MHand.TYPE_HAND]
        ftlog.debug('checkHuByMagicTiles1 tiles = ', tiles)
        # 判定其它胡牌
        result, rePattern = MWin.isHu(tiles[MHand.TYPE_HAND], magicTiles)
        ftlog.debug('checkHuByMagicTiles2 tiles = ', tiles)
        if result:
            ftlog.debug('MWinRuleYunnan.isHu rePattern:', rePattern)
            return True, rePattern

        return False, []

    @classmethod
    def checkSpecialHu(cls, tiles, magicTiles, magicTileCount, tile):
        # 判断七对系列
        if cls.isPairs(tiles, magicTiles):
            return True

        # 判定五六七星烂,手牌数必须为14,所有花色最多一张牌,字牌不重复且大于等于5种,其它花色必须都存在且互相不靠
        if cls.isLanPaiHu(tiles, magicTiles):
            return True

        # 判断其它特殊牌型

        allTiles = MHand.copyAllTilesToList(tiles)
        tempTiles = copy.deepcopy(allTiles)
        for magicTile in magicTiles:
            while magicTile in tempTiles:
                tempTiles.remove(magicTile)
        tileArr = MTile.changeTilesToValueArr(tempTiles)
        colorState = MTile.getColorCount(tileArr)
        tempFengTiles = MTile.traverseTile(MTile.TILE_FENG)
        ziState = tileArr[tempFengTiles[0]:tempFengTiles[len(tempFengTiles) - 1] + 1]
        #         menState = 0
        #         if len(allTiles) == 14:
        #             menState = 1
        playerGangCount = len(tiles[MHand.TYPE_GANG])

        if playerGangCount >= 2 \
                or colorState == 1 or colorState == 0 \
                or len(tiles[MHand.TYPE_HAND]) == 2 or len(tiles[MHand.TYPE_HAND]) == 3:
            return True

        # 三元和混三元
        baibanCount = cls.getZiCountByTypeBySeatId(MTile.TILE_BAI_BAN, ziState)
        hongzhongCount = cls.getZiCountByTypeBySeatId(MTile.TILE_HONG_ZHONG, ziState)
        facaiCount = cls.getZiCountByTypeBySeatId(MTile.TILE_FA_CAI, ziState)
        if baibanCount + magicTileCount >= 2 \
                and hongzhongCount + magicTileCount >= 2 \
                and facaiCount + magicTileCount >= 2:
            if baibanCount + hongzhongCount + magicTileCount >= 5 \
                    and baibanCount + facaiCount + magicTileCount >= 5 \
                    and hongzhongCount + facaiCount + magicTileCount >= 5:
                if baibanCount + hongzhongCount + facaiCount + magicTileCount >= 8:
                    return True

        # 大对子,门前不能有吃,手牌多加一个赖子,能保证都是3张
        if len(tiles[MHand.TYPE_CHI]) == 0:
            duiziTiles = copy.deepcopy(tiles[MHand.TYPE_HAND])
            for magicTile in magicTiles:
                while magicTile in duiziTiles:
                    duiziTiles.remove(magicTile)
            # 如果点炮胡,需要给牌堆里加回去一张赖子,并当普通牌处理
            if tile in magicTiles:
                duiziTiles.append(tile)
            duiziArr = MTile.changeTilesToValueArr(duiziTiles)
            ftlog.debug("MYunnanOneResult duiziArr = ", duiziArr)
            cardTypeCount = 0
            # 假设多一张可用赖子
            duiziMagicCount = magicTileCount + 1
            for index in range(len(duiziArr)):
                if duiziArr[index] != 0:
                    cardTypeCount += 1
                    if duiziArr[index] < 3:
                        duiziMagicCount = duiziMagicCount - (3 - duiziArr[index])
            if cardTypeCount <= 5 and duiziMagicCount >= 0:
                return True
        return False

    @classmethod
    def getZiCountByTypeBySeatId(cls, fengType, ziState):
        if fengType < MTile.TILE_DONG_FENG or fengType > MTile.TILE_BAI_BAN:
            return 0
        else:
            return ziState[fengType - MTile.TILE_DONG_FENG]
