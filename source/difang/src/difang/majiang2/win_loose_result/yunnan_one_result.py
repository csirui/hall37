# -*- coding=utf-8
'''
Created on 2016年11月17日

    云南曲靖飞小鸡结算

@author: zhangwei
'''
import copy

from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.tile.tile import MTile
from difang.majiang2.win_loose_result.one_result import MOneResult
from difang.majiang2.win_rule.win_rule_yunnan import MWinRuleYunnan
from freetime.util import log as ftlog


class MYunnanOneResult(MOneResult):
    WUJI = 'wuji'
    XIAOJIGUIWEI = 'xiaojiguiwei'
    YIGANG = 'yigang'
    LIANGGANG = 'lianggang'
    SANGANG = 'sangang'
    SIGANG = 'sigang'
    BUQIUREN = 'buqiuren'
    QUANQIUREN = 'quanqiuren'
    HUNYISE = 'hunyise'
    QINGYISE = 'qingyise'
    ZIYISE = 'ziyise'
    DADUIZI = 'daduizi'
    XIAOQIDUI = 'xiaoqidui'
    LONGZHUABEI = 'longzhuabei'
    HUNSANYUAN = 'hunsanyuan'
    SANYUAN = 'sanyuan'
    WUXINGLAN = 'wuxinglan'
    LIUXINGLAN = 'liuxinglan'
    QIXINGLAN = 'qixinglan'
    GANGSHANGHUAWUMEIHUA = 'gangshanghuawumeihua'
    GANGSHANGHUA = 'gangshanghua'
    GANGSHANGPAO = 'gangshangpao'
    SIYAOJI = 'siyaoji'
    SHIFENG = 'shifeng'
    SHISANYAO = 'shisanyao'
    QIANGGANGHU = 'qiangganghu'

    WIN_MODE_SHIFENG = 4
    WIN_MODE_SIYAOJI = 5
    WIN_MODE_SHISANYAO = 6
    WIN_MODE_BUQIUREN = 7

    def __init__(self):
        super(MYunnanOneResult, self).__init__()
        self.__fan_xing = {
            self.WUJI: {"name": "无鸡", "index": 1},
            self.XIAOJIGUIWEI: {"name": "小鸡归位", "index": 1},
            #             self.YIGANG:{"name":"一杠", "index":1},
            self.LIANGGANG: {"name": "两杠", "index": 1},
            self.SANGANG: {"name": "三杠", "index": 3},
            self.SIGANG: {"name": "四杠", "index": 3},
            self.BUQIUREN: {"name": "不求人", "index": 1},
            self.QUANQIUREN: {"name": "全求人", "index": 1},
            self.HUNYISE: {"name": "混一色", "index": 1},
            self.QINGYISE: {"name": "清一色", "index": 2},
            self.ZIYISE: {"name": "字一色", "index": 2},
            self.DADUIZI: {"name": "大对子", "index": 1},
            self.XIAOQIDUI: {"name": "小七对", "index": 2},
            self.LONGZHUABEI: {"name": "龙爪背", "index": 3},
            self.HUNSANYUAN: {"name": "混三元", "index": 3},
            self.SANYUAN: {"name": "三元", "index": 3},
            self.WUXINGLAN: {"name": "五星烂", "index": 1},
            self.LIUXINGLAN: {"name": "六星烂", "index": 1},
            self.QIXINGLAN: {"name": "七星烂", "index": 2},
            self.GANGSHANGHUAWUMEIHUA: {"name": "杠上花五梅花", "index": 2},
            self.GANGSHANGHUA: {"name": "杠上花", "index": 1},
            self.GANGSHANGPAO: {"name": "杠上炮", "index": 1},
            self.SIYAOJI: {"name": "四幺鸡", "index": 3},
            self.SHIFENG: {"name": "十风", "index": 3},
            self.SHISANYAO: {"name": "十三幺", "index": 3},
            self.QIANGGANGHU: {"name": "抢杠胡", "index": 1}
        }

    @property
    def fanXing(self):
        return self.__fan_xing

    def getZiTypeCountBySeatId(self, seatId):
        count = 0
        for temp in self.ziState[seatId]:
            if temp > 0:
                count += 1
        return count

    def getZiCountByTypeBySeatId(self, seatId, fengType):
        if fengType < MTile.TILE_DONG_FENG or fengType > MTile.TILE_BAI_BAN:
            return 0
        else:
            return self.ziState[seatId][fengType - MTile.TILE_DONG_FENG]

    def calcScore(self):
        """算分"""

        # 序列化
        self.serialize()

        # 牌型数据都在tabletilemgr里面可以取到
        playerAllTiles = [[] for _ in range(self.playerCount)]
        playerAllTilesArr = [[] for _ in range(self.playerCount)]
        playerHandTiles = [[] for _ in range(self.playerCount)]
        for player in self.tableTileMgr.players:
            # 按手牌格式的数组
            playerAllTiles[player.curSeatId] = player.copyTiles()
            # 合到一个数组中
            playerAllTilesArr[player.curSeatId].extend(MHand.copyAllTilesToList(playerAllTiles[player.curSeatId]))
            # 只获取手牌                
            playerHandTiles[player.curSeatId] = player.copyHandTiles()
        ftlog.debug("playerHandTiles", playerHandTiles)
        ftlog.debug("playerAllTiles", playerAllTiles)
        ftlog.debug("playerAllTilesArr", playerAllTilesArr)
        ftlog.debug("self.winTile", self.winTile)
        self.results[self.KEY_TYPE] = ''
        self.results[self.KEY_NAME] = ''
        self.results[self.KEY_SCORE] = [0 for _ in range(self.playerCount)]
        self.results[self.KEY_WIN_TILE] = [0 for _ in range(self.playerCount)]
        self.results[self.KEY_WIN_MODE] = [MOneResult.WIN_MODE_LOSS for _ in range(self.playerCount)]
        # 在和牌时统计自摸，点炮，最大番数
        self.results[self.KEY_STAT] = [[] for _ in range(self.playerCount)]
        self.results[self.KEY_FAN_PATTERN] = [[] for _ in range(self.playerCount)]
        fanArr = [0 for _ in range(self.playerCount)]
        baseScore = 1

        # 流局不走后面的结算,确保没有设置的值不会被使用
        if self.resultType == self.RESULT_FLOW:
            self.results[self.KEY_TYPE] = MOneResult.KEY_TYPE_NAME_FLOW
            ftlog.debug("MYunnanOneResult calcScore Type = RESULT_FLOW return")
            return

        self.results[self.KEY_TYPE] = MOneResult.KEY_TYPE_NAME_HU

        if len(self.winSeats) <= 0:
            ftlog.debug("MYunnanOneResult self.winSeats error no winner")
            return
        ftlog.debug("MYunnanOneResultCalcScore self.winSeats = ", self.winSeats)

        if self.lastSeatId not in self.winSeats:
            self.results[self.KEY_WIN_MODE][self.lastSeatId] = MOneResult.WIN_MODE_DIANPAO

        # 计算胡牌者的番型和分数
        for seatId in self.winSeats:
            # 番型
            patterns = []
            fan = 0
            ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang dealwith seatId:'
                        , seatId
                        , 'lastSeatId:', self.lastSeatId
                        , 'winSeatId:', self.winSeatId
                        , 'self.winSeats:', self.winSeats
                        , 'self.actionID:', self.actionID
                        )
            ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan, "seatId = ", seatId)
            if seatId == self.lastSeatId:
                self.results[self.KEY_WIN_MODE][seatId] = MOneResult.WIN_MODE_ZIMO
            else:
                self.results[self.KEY_WIN_MODE][seatId] = MOneResult.WIN_MODE_PINGHU
            magicTiles = self.tableTileMgr.getMagicTiles()
            tempArrColor = copy.deepcopy(playerAllTilesArr[seatId])
            # colorState里面要去掉赖子包含的花色
            magicTileCount = 0
            for magicTile in magicTiles:
                while magicTile in tempArrColor:
                    tempArrColor.remove(magicTile)
                    magicTileCount += 1
            # 重新处理一次花色,不算赖子
            oldColorState = copy.deepcopy(self.colorState)
            ftlog.debug("MYunnanOneResultCalcScore tempArrColor = ", tempArrColor)
            ftlog.debug("MYunnanOneResultCalcScore self.colorState1 = ", self.colorState)
            self.colorState[seatId] = MTile.getColorCount(MTile.changeTilesToValueArr(tempArrColor))
            ftlog.debug("MYunnanOneResultCalcScore self.colorState2 = ", self.colorState)
            isUnique = False

            # 七对和五六七星烂,十风,十三幺,四幺鸡
            # 取出dropTiles来判断是否十风和十三幺
            dropTiles = self.tableTileMgr.dropTiles[seatId]
            nowTiles = playerAllTiles[seatId]
            nowTiles[MHand.TYPE_HAND].append(self.winTile)

            # 杠上花和杠上炮
            ftlog.debug("MYunnanOneResultCalcScorelatestGangState = ", self.latestGangState)
            ftlog.debug("MYunnanOneResultCalcScorelatestGangState self.winSeatId:= ", self.winSeatId)
            ftlog.debug("MYunnanOneResultCalcScorelatestGangState seatId:= ", seatId)
            ftlog.debug("MYunnanOneResultCalcScorelatestGangState self.lastSeatId:= ", self.lastSeatId)

            if self.latestGangState != -1:
                if self.latestGangState == seatId:
                    # 杠牌的是自己
                    wumeihuaTiles = copy.deepcopy(nowTiles)
                    if self.winTile in wumeihuaTiles[MHand.TYPE_HAND]:
                        wumeihuaTiles[MHand.TYPE_HAND].remove(self.winTile)
                    wumeihuaTiles[MHand.TYPE_HAND].append(MTile.TILE_FIVE_TONG)
                    result, _ = MWinRuleYunnan.checkHuByMagicTiles(wumeihuaTiles, magicTiles)
                    if result and (self.winTile == MTile.TILE_FIVE_TONG or self.winTile in magicTiles):
                        # 五梅花,包括幺鸡当五筒
                        if not isUnique:
                            patterns.append(self.fanXing[self.GANGSHANGHUAWUMEIHUA]['name'])
                            fan += self.fanXing[self.GANGSHANGHUAWUMEIHUA]['index']
                            ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                    else:
                        if not isUnique:
                            patterns.append(self.fanXing[self.GANGSHANGHUA]['name'])
                            fan += self.fanXing[self.GANGSHANGHUA]['index']
                            ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                elif self.latestGangState == self.lastSeatId:
                    # 杠牌的是别人
                    if not isUnique:
                        patterns.append(self.fanXing[self.GANGSHANGPAO]['name'])
                        fan += self.fanXing[self.GANGSHANGPAO]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)

            # 四幺鸡,必须是自摸,必须是手牌
            if nowTiles[MHand.TYPE_HAND].count(MTile.TILE_ONE_TIAO) == 4 and (seatId == self.lastSeatId):
                if not isUnique:
                    self.results[self.KEY_WIN_MODE][seatId] = MYunnanOneResult.WIN_MODE_SIYAOJI
                    patterns = []
                    patterns.append(self.fanXing[self.SIYAOJI]['name'])
                    isUnique = True
                    fan = 0
                    fan += self.fanXing[self.SIYAOJI]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)

            ftlog.debug("MYunnanOneResult dropTiles = ", dropTiles, "nowTiles = ", nowTiles)
            if self.isShifeng(dropTiles, nowTiles):
                if not isUnique:
                    self.results[self.KEY_WIN_MODE][seatId] = MYunnanOneResult.WIN_MODE_SHIFENG
                    patterns.append(self.fanXing[self.SHIFENG]['name'])
                    fan = 0
                    fan += self.fanXing[self.SHIFENG]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                    isUnique = True
                    self.setDropHuFlag(1)
            if self.isShisanyao(dropTiles, nowTiles):
                if not isUnique:
                    self.results[self.KEY_WIN_MODE][seatId] = MYunnanOneResult.WIN_MODE_SHISANYAO
                    patterns.append(self.fanXing[self.SHISANYAO]['name'])
                    fan = 0
                    fan += self.fanXing[self.SHISANYAO]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                    isUnique = True
                    self.setDropHuFlag(1)
            ftlog.debug("MYunnanOneResult check lanpai nowTiles =", nowTiles, "magicTiles =", magicTiles)
            result, fengCount, lanPanMagicCount = self.isLanPaiCheck(nowTiles, magicTiles)
            lanPaiPatternForWuji = False
            if result:
                lanPaiPatternForWuji = True
                if fengCount + lanPanMagicCount >= 7:
                    # 七星烂
                    if not isUnique:
                        patterns.append(self.fanXing[self.QIXINGLAN]['name'])
                        fan += self.fanXing[self.QIXINGLAN]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                elif fengCount + lanPanMagicCount >= 6:
                    # 六星烂
                    if not isUnique:
                        patterns.append(self.fanXing[self.LIUXINGLAN]['name'])
                        fan += self.fanXing[self.LIUXINGLAN]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                elif fengCount + lanPanMagicCount >= 5:
                    # 五星烂
                    if not isUnique:
                        patterns.append(self.fanXing[self.WUXINGLAN]['name'])
                        fan += self.fanXing[self.WUXINGLAN]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
            # 七对必须门清
            isPairs = False
            if self.menState[seatId] == 1:
                if seatId == self.lastSeatId:
                    # 自摸
                    pairResult, leftMagicCount, fourCount, _ = self.isPairsCheck(nowTiles, magicTiles)
                    if pairResult:
                        isPairs = True
                        if fourCount >= 1:
                            if not isUnique:
                                patterns.append(self.fanXing[self.LONGZHUABEI]['name'])
                                fan += self.fanXing[self.LONGZHUABEI]['index']
                                ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                        else:
                            # 小七对
                            if not isUnique:
                                patterns.append(self.fanXing[self.XIAOQIDUI]['name'])
                                fan += self.fanXing[self.XIAOQIDUI]['index']
                                ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                else:
                    # 点炮
                    if self.winTile in magicTiles:
                        transferTiles = copy.deepcopy(nowTiles)
                        magicCount = 0
                        for magicTile in magicTiles:
                            while magicTile in transferTiles[MHand.TYPE_HAND]:
                                transferTiles[MHand.TYPE_HAND].remove(magicTile)
                                transferTiles[MHand.TYPE_HAND].append(0)
                                magicCount += 1
                            if magicCount >= 1:
                                transferTiles[MHand.TYPE_HAND].remove(0)
                                transferTiles[MHand.TYPE_HAND].append(magicTile)
                        pairResult, leftMagicCount, fourCount, _ = self.isPairsCheck(transferTiles, [0])
                        if pairResult:
                            isPairs = True
                            if leftMagicCount >= 2:
                                if not isUnique:
                                    patterns.append(self.fanXing[self.LONGZHUABEI]['name'])
                                    fan += self.fanXing[self.LONGZHUABEI]['index']
                                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                            else:
                                # 小七对
                                if not isUnique:
                                    patterns.append(self.fanXing[self.XIAOQIDUI]['name'])
                                    fan += self.fanXing[self.XIAOQIDUI]['index']
                                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                    else:
                        pairResult, leftMagicCount, fourCount, _ = self.isPairsCheck(nowTiles, magicTiles)
                        if pairResult:
                            isPairs = True
                            if nowTiles[MHand.TYPE_HAND].count(self.winTile) + leftMagicCount >= 3:
                                # 一定是龙爪背
                                if not isUnique:
                                    patterns.append(self.fanXing[self.LONGZHUABEI]['name'])
                                    fan += self.fanXing[self.LONGZHUABEI]['index']
                                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                            else:
                                # 小七对
                                if not isUnique:
                                    patterns.append(self.fanXing[self.XIAOQIDUI]['name'])
                                    fan += self.fanXing[self.XIAOQIDUI]['index']
                                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)

                                    # 杠数
                                    #         if len(self.playerGangTiles[seatId]) == 1:
                                    #             if not isUnique:
                                    #                 self.results[self.KEY_NAME] = self.fanXing[self.YIGANG]['name']
                                    #                 patterns.append(self.fanXing[self.YIGANG]['name'])
                                    #                 fan += self.fanXing[self.YIGANG]['index']
                                    #                 ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                                    #         el
            if len(self.playerGangTiles[seatId]) == 2:
                if not isUnique:
                    self.results[self.KEY_NAME] = self.fanXing[self.LIANGGANG]['name']
                    patterns.append(self.fanXing[self.LIANGGANG]['name'])
                    fan += self.fanXing[self.LIANGGANG]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
            elif len(self.playerGangTiles[seatId]) == 3:
                if not isUnique:
                    self.results[self.KEY_NAME] = self.fanXing[self.SANGANG]['name']
                    patterns.append(self.fanXing[self.SANGANG]['name'])
                    fan += self.fanXing[self.SANGANG]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
            elif len(self.playerGangTiles[seatId]) == 4:
                if not isUnique:
                    self.results[self.KEY_NAME] = self.fanXing[self.SIGANG]['name']
                    patterns.append(self.fanXing[self.SIGANG]['name'])
                    fan += self.fanXing[self.SIGANG]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)

            # 字一色
            ziyiseWuji = False
            if self.colorState[seatId] == 0:
                if self.getZiTypeCountBySeatId(seatId) > 0:
                    ziyiseWuji = True
                    if not isUnique:
                        self.results[self.KEY_NAME] = self.fanXing[self.ZIYISE]['name']
                        patterns.append(self.fanXing[self.ZIYISE]['name'])
                        fan += self.fanXing[self.ZIYISE]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)

            # 大对子,门前不能有吃,手牌多加一个赖子,能保证都是3张
            if len(nowTiles[MHand.TYPE_CHI]) == 0:
                duiziTiles = copy.deepcopy(nowTiles[MHand.TYPE_HAND])
                for magicTile in magicTiles:
                    while magicTile in duiziTiles:
                        duiziTiles.remove(magicTile)
                # 如果点炮胡,需要给牌堆里加回去一张赖子,并当普通牌处理
                if seatId != self.lastSeatId and self.winTile in magicTiles:
                    duiziTiles.append(self.winTile)
                duiziArr = MTile.changeTilesToValueArr(duiziTiles)
                ftlog.debug("MYunnanOneResult duiziArr = ", duiziArr)
                cardTypeCount = 0
                # 假设多一张赖子
                duiziMagicCount = magicTileCount + 1
                for index in range(len(duiziArr)):
                    if duiziArr[index] != 0:
                        cardTypeCount += 1
                        if duiziArr[index] < 3:
                            duiziMagicCount = duiziMagicCount - (3 - duiziArr[index])
                if cardTypeCount <= 5 and duiziMagicCount >= 0:
                    patterns.append(self.fanXing[self.DADUIZI]['name'])
                    fan += self.fanXing[self.DADUIZI]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                    # 清一色和混一色
            qingyiseForWuji = False
            if self.colorState[seatId] == 1:
                qingyiseForWuji = True
                if self.getZiTypeCountBySeatId(seatId) > 0:
                    if not isUnique:
                        self.results[self.KEY_NAME] = self.fanXing[self.HUNYISE]['name']
                        patterns.append(self.fanXing[self.HUNYISE]['name'])
                        fan += self.fanXing[self.HUNYISE]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                else:
                    if not isUnique:
                        self.results[self.KEY_NAME] = self.fanXing[self.QINGYISE]['name']
                        patterns.append(self.fanXing[self.QINGYISE]['name'])
                        fan += self.fanXing[self.QINGYISE]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)


                        # 不求人 门清并自摸
            # 暗杠也算门清,重新计算
            # 烂牌和七对牌型时不计算不求人
            if not lanPaiPatternForWuji and not isPairs:
                isMenQing = False
                gangInfo = playerAllTiles[seatId][MHand.TYPE_GANG]
                chiInfo = playerAllTiles[seatId][MHand.TYPE_CHI]
                pengInfo = playerAllTiles[seatId][MHand.TYPE_PENG]
                if len(chiInfo) == 0 and len(pengInfo) == 0:
                    isMenQing = True
                    for gang in gangInfo:
                        if gang['style'] == 1:
                            isMenQing = False
                if isMenQing and seatId == self.lastSeatId:
                    if not isUnique:
                        self.results[self.KEY_WIN_MODE][seatId] = MYunnanOneResult.WIN_MODE_BUQIUREN
                        patterns.append(self.fanXing[self.BUQIUREN]['name'])
                        fan += self.fanXing[self.BUQIUREN]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)

            # 全求人 最后手里只有一张牌 单钓 不能有暗杠
            if len(playerHandTiles[seatId]) == 1 and seatId != self.lastSeatId:
                noAnGang = True
                for gangInfo in nowTiles[MHand.TYPE_GANG]:
                    if gangInfo.has_key('style'):
                        gangStyle = gangInfo.get('style', 1)
                        if gangStyle == 0:
                            noAnGang = False
                            break;
                if noAnGang:
                    if not isUnique:
                        patterns.append(self.fanXing[self.QUANQIUREN]['name'])
                        fan += self.fanXing[self.QUANQIUREN]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)

                        # 三元和混三元
            sanyuanForWuji = False
            baibanCount = self.getZiCountByTypeBySeatId(seatId, MTile.TILE_BAI_BAN)
            hongzhongCount = self.getZiCountByTypeBySeatId(seatId, MTile.TILE_HONG_ZHONG)
            facaiCount = self.getZiCountByTypeBySeatId(seatId, MTile.TILE_FA_CAI)
            sanyuanMagicCount = nowTiles[MHand.TYPE_HAND].count(MTile.TILE_ONE_TIAO)
            if baibanCount + sanyuanMagicCount >= 2 \
                    and hongzhongCount + sanyuanMagicCount >= 2 \
                    and facaiCount + sanyuanMagicCount >= 2:
                if baibanCount + hongzhongCount + sanyuanMagicCount >= 5 \
                        and baibanCount + facaiCount + sanyuanMagicCount >= 5 \
                        and hongzhongCount + facaiCount + sanyuanMagicCount >= 5:
                    if baibanCount + hongzhongCount + facaiCount + sanyuanMagicCount >= 8:
                        if self.colorState[seatId] == 1 and self.noFengPai(seatId):
                            # 混三元
                            if not isUnique:
                                sanyuanForWuji = True
                                patterns.append(self.fanXing[self.HUNSANYUAN]['name'])
                                fan += self.fanXing[self.HUNSANYUAN]['index']
                                ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                        else:
                            # 三元
                            if not isUnique:
                                patterns.append(self.fanXing[self.SANYUAN]['name'])
                                fan += self.fanXing[self.SANYUAN]['index']
                                ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)

            # 无鸡
            isWuji = False
            wujiTiles = copy.deepcopy(nowTiles)
            # 手牌不要赖子能胡
            result0, _ = MWinRuleYunnan.checkHuByMagicTiles(wujiTiles, [])
            for temp in nowTiles[MHand.TYPE_CHI]:
                wujiTiles[MHand.TYPE_HAND].extend(temp)
            for temp in nowTiles[MHand.TYPE_PENG]:
                wujiTiles[MHand.TYPE_HAND].extend(temp)
            ftlog.debug("MYunnanOneResult wujiTiles = ", wujiTiles)
            # 加上碰吃,不要赖子也能胡
            result1, _ = MWinRuleYunnan.checkHuByMagicTiles(wujiTiles, [])
            wujiMagicCount = playerAllTilesArr[seatId].count(MTile.TILE_ONE_TIAO)
            ftlog.debug("MYunnanOneResult wujiTiles = ", wujiTiles, "result1=", result1)
            result2 = True
            # 算杠,不是4个幺鸡都是有赖子
            for magicTile in magicTiles:
                for gangInfo in wujiTiles[MHand.TYPE_GANG]:
                    wujiGangMagicCount = 0
                    if gangInfo.has_key('pattern'):
                        tempGangInfo = copy.deepcopy(gangInfo['pattern'])
                        while magicTile in tempGangInfo:
                            tempGangInfo.remove(magicTile)
                            wujiGangMagicCount += 1
                        if wujiGangMagicCount != 4 and wujiGangMagicCount != 0:
                            result2 = False
                            break
            ftlog.debug("MYunnanOneResult wujiTiles = ", wujiTiles
                        , "result1=", result1
                        , "result2=", result2
                        , "result0=", result0)
            if result1 and result2 and result0:
                isWuji = True
            if isWuji:
                if wujiMagicCount > 0:
                    canXiaojiguiwei = True
                    # 小鸡归位,要排除赖子应用在其它番型导致小鸡归位和其它番型不同存的情况
                    ftlog.debug("MYunnanOneResult canXiaojiguiwei oldColorState", oldColorState
                                , "lanPaiPatternForWuji", lanPaiPatternForWuji
                                , "qingyiseForWuji", qingyiseForWuji
                                , "ziyiseWuji", ziyiseWuji
                                , "sanyuanForWuji", sanyuanForWuji)

                    if lanPaiPatternForWuji:
                        # 如果是烂牌的小鸡归位,重新检查在没有赖子的情况能不能胡
                        resultNoMagic, fengCountNoMagic, lanPanMagicCountNoMagic = self.isLanPaiCheck(nowTiles, [])
                        if lanPanMagicCount > 0:
                            # 带赖子的六星烂,如果无赖子判定能胡,那就可以胡五星烂+小鸡归位
                            if self.fanXing[self.LIUXINGLAN]['name'] in patterns and resultNoMagic:
                                patterns.remove(self.fanXing[self.LIUXINGLAN]['name'])
                                fan -= self.fanXing[self.LIUXINGLAN]['index']
                                patterns.append(self.fanXing[self.WUXINGLAN]['name'])
                                fan += self.fanXing[self.WUXINGLAN]['index']
                                canXiaojiguiwei = True
                            elif self.fanXing[self.QIXINGLAN][
                                'name'] in patterns and resultNoMagic and fengCountNoMagic >= 7:
                                canXiaojiguiwei = True
                            else:
                                canXiaojiguiwei = False
                        else:
                            canXiaojiguiwei = True
                    if qingyiseForWuji:
                        if oldColorState[seatId] > 1:
                            canXiaojiguiwei = False
                    if ziyiseWuji:
                        if oldColorState[seatId] > 0:
                            canXiaojiguiwei = False
                    if sanyuanForWuji:
                        if oldColorState[seatId] > 1:
                            canXiaojiguiwei = False
                    if canXiaojiguiwei:
                        if not isUnique:
                            patterns.append(self.fanXing[self.XIAOJIGUIWEI]['name'])
                            fan += self.fanXing[self.XIAOJIGUIWEI]['index']
                            ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                else:
                    if not isUnique:
                        patterns.append(self.fanXing[self.WUJI]['name'])
                        fan += self.fanXing[self.WUJI]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
            self.results[self.KEY_FAN_PATTERN][seatId] = patterns
            self.results[self.KEY_WIN_TILE][seatId] = self.winTile
            fanArr[seatId] = fan

        if self.lastSeatId in self.winSeats:
            self.results[self.KEY_STAT][self.lastSeatId].append({MOneResult.STAT_ZIMO: 1})
        else:
            # 点炮,点炮者点炮+1
            self.results[self.KEY_STAT][self.lastSeatId].append({MOneResult.STAT_DIANPAO: 1})
        # 最大番,当前的赢家番数
        self.results[self.KEY_STAT][seatId].append({MOneResult.STAT_ZUIDAFAN: fan})

        # 计算积分
        winScore = baseScore * (self.multiple)
        if self.qiangGang:
            if self.winRuleMgr.itemParams.get('QGHSanbei', 1) == 2:
                winScore = winScore
            else:
                winScore = winScore * 3
            for player in self.tableTileMgr.players:
                if player.curSeatId == self.lastSeatId and self.lastSeatId not in self.winSeats:
                    ftlog.debug("MYunnanOneResultQGH lose seatId:", player.curSeatId, "lastSeatId:", self.lastSeatId)
                    if self.winTile in player.handTiles:
                        ftlog.debug("MYunnanOneResultQGH lose seatId:", player.curSeatId, "lastSeatId:",
                                    self.lastSeatId, "remove tile:", self.winTile)
                        player.handTiles.remove(self.winTile)
                    else:
                        if self.showTile in player.handTiles and self.showTile != 0:
                            ftlog.debug("MYunnanOneResultQGH lose seatId:", player.curSeatId, "lastSeatId:",
                                        self.lastSeatId, "remove tile:", self.showTile)
                            player.handTiles.remove(self.showTile)
            for seatId in self.winSeats:
                if self.winRuleMgr.itemParams.get('QGHJiafan', 1) == 2:
                    fanArr[seatId] += 1
                self.results[self.KEY_WIN_MODE][seatId] = MOneResult.WIN_MODE_QIANGGANGHU

        # 番数上限3
        for win in self.winSeats:
            if fanArr[win] > 3:
                fanArr[win] = 3

        # 计算分数增减
        if self.lastSeatId in self.winSeats:
            for i in range(self.playerCount):
                if self.lastSeatId == i:
                    self.results[self.KEY_SCORE][i] = winScore * (2 ** fanArr[i]) * (self.playerCount - 1)
                else:
                    self.results[self.KEY_SCORE][i] = -winScore * (2 ** fanArr[self.lastSeatId])
        else:
            dianPaoScore = 0
            for i in range(self.playerCount):
                if i in self.winSeats:
                    self.results[self.KEY_SCORE][i] = winScore * (2 ** fanArr[i])
                    dianPaoScore += winScore * (2 ** fanArr[i])
            self.results[self.KEY_SCORE][self.lastSeatId] = -dianPaoScore

        ftlog.debug('MYunnanOneResult calcScore:KEY_SCORE:', self.results[self.KEY_SCORE])
        ftlog.debug('MYunnanOneResult calcScore:KEY_NAME:', self.results[self.KEY_NAME])
        ftlog.debug('MYunnanOneResult calcScore:KEY_TYPE:', self.results[self.KEY_TYPE])
        ftlog.debug('MYunnanOneResult calcScore:KEY_WIN_MODE:', self.results[self.KEY_WIN_MODE])
        ftlog.debug('MYunnanOneResult calcScore:KEY_FAN_PATTERN:', self.results[self.KEY_FAN_PATTERN])
        ftlog.debug('MYunnanOneResult calcScore:KEY_STAT:', self.results[self.KEY_STAT])

    def noFengPai(self, seatId):
        """是否包含东南西北的判断
        ziState:31到37的牌数组成的数组
        """
        dongfengCount = self.getZiCountByTypeBySeatId(seatId, MTile.TILE_DONG_FENG)
        nanfengCount = self.getZiCountByTypeBySeatId(seatId, MTile.TILE_NAN_FENG)
        xifengCount = self.getZiCountByTypeBySeatId(seatId, MTile.TILE_XI_FENG)
        beifengCount = self.getZiCountByTypeBySeatId(seatId, MTile.TILE_BEI_FENG)
        if dongfengCount > 0 or nanfengCount > 0 or xifengCount > 0 or beifengCount > 0:
            return False
        return True

    def isShifeng(self, dropTiles, nowTiles):
        """特殊牌型十风的胡牌判断"""
        # 十风和十三幺都是必须从开局开始连出,并且不能吃碰杠
        if len(dropTiles) <= 0:
            return False
        else:
            if len(nowTiles[MHand.TYPE_CHI]) > 0 or len(nowTiles[MHand.TYPE_PENG]) > 0 or len(
                    nowTiles[MHand.TYPE_GANG]) > 0:
                return False
            if not self.isZipai(dropTiles[0]):
                return False
            count = 0
            for tempTile in dropTiles:
                if self.isZipai(tempTile):
                    count += 1
                else:
                    count = 0
                    break
            if count >= 10:
                return True
        return False

    def isShisanyao(self, dropTiles, nowTiles):
        """特殊牌型十三幺的胡牌判断"""
        # 十风和十三幺都是必须从开局开始连出,并且不能吃碰杠
        if len(dropTiles) <= 0:
            return False
        else:
            if len(nowTiles[MHand.TYPE_CHI]) > 0 or len(nowTiles[MHand.TYPE_PENG]) > 0 or len(
                    nowTiles[MHand.TYPE_GANG]) > 0:
                return False
            if not self.isYaopai(dropTiles[0]):
                return False
            count = 0
            for tempTile in dropTiles:
                if self.isYaopai(tempTile):
                    count += 1
                else:
                    count = 0
                    break
            if count >= 13:
                return True

        return False

    def isZipai(self, tile):
        """检查满足十风的牌型"""
        if tile >= MTile.TILE_DONG_FENG and tile <= MTile.TILE_BAI_BAN:
            return True
        return False

    def isYaopai(self, tile):
        """检查满足十三幺的牌型"""
        if tile >= MTile.TILE_DONG_FENG and tile <= MTile.TILE_BAI_BAN:
            return True
        if tile % 10 == 1 or tile % 10 == 9:
            return True
        return False

    def isLanPaiCheck(self, tiles, magicTiles):
        """先做简单的牌型检查,如果符合再进行细节判断"""
        if len(tiles[MHand.TYPE_HAND]) != 14:
            return False, 0, 0
        ftlog.debug("isLanPaiCheck handcard is ok")
        # 去除手牌赖子,并计数
        haveMagicCount = 0
        lanpaiTiles = copy.deepcopy(tiles[MHand.TYPE_HAND])
        for magicTile in magicTiles:
            while magicTile in lanpaiTiles:
                lanpaiTiles.remove(magicTile)
                haveMagicCount += 1
        ftlog.debug("isLanPaiCheck haveMagicCount =", haveMagicCount, "lanpaiTiles =", lanpaiTiles)
        tileArr = MTile.changeTilesToValueArr(lanpaiTiles)
        # 去除赖子后手牌数不能有超过2张的
        for count in tileArr:
            if count <= 1:
                continue
            else:
                return False, 0, 0

        # 去除赖子后不重复字牌加赖子数要大于等于5,并且可用赖子数＝字牌＋赖子-5
        # canUseMagicCount = haveMagicCount
        tempFengTiles = MTile.traverseTile(MTile.TILE_FENG)
        fengArr = tileArr[tempFengTiles[0]:tempFengTiles[len(tempFengTiles) - 1] + 1]
        ftlog.debug("isLanPaiCheck fengArr =", fengArr)
        # 检查字牌种类和每种的数量,之前因为已经判断过数量小于等于1,这里不再重复
        fengCount = 0
        for count in fengArr:
            if count == 1:
                fengCount += 1

        # 如果字牌每种不超过1张且有五种,开始判断其它花色
        if fengCount + haveMagicCount >= 5:
            # 分别判断三种花色
            ftlog.debug("isLanPaiCheck checkBukao begin tileArr = ", tileArr)
            if self.checkBukao(tileArr, MTile.TILE_WAN) and self.checkBukao(tileArr,
                                                                            MTile.TILE_TONG) and self.checkBukao(
                    tileArr, MTile.TILE_TIAO):
                return True, fengCount, haveMagicCount
        else:
            return False, 0, 0

        return False, 0, 0

    def checkBukao(self, tileArr, tileType):
        """烂牌检查三种花色的不靠"""
        tempTiles = MTile.traverseTile(tileType)
        colorArr = tileArr[tempTiles[0]:tempTiles[len(tempTiles) - 1] + 1]
        colorTiles = []
        for i in range(len(colorArr)):
            if colorArr[i] > 0:
                colorTiles.append(i)
            if len(colorTiles) > 3:
                ftlog.debug("checkBukao break1 tileType =", tileType)
                return False
            # 然后只需要判断不靠即可
            elif len(colorTiles) == 2:
                if (colorTiles[0] - colorTiles[1]) % 3 != 0:
                    ftlog.debug("checkBukao break2 tileType =", tileType)
                    return False

            elif len(colorTiles) == 3:
                if (colorTiles[0] - colorTiles[1]) % 3 != 0 or (colorTiles[0] - colorTiles[2]) % 3 != 0 or (
                    colorTiles[1] - colorTiles[2]) % 3 != 0:
                    ftlog.debug("checkBukao break3 tileType =", tileType)
                    return False
        return True

    def isPairsCheck(self, tiles, magicTiles):
        """判断七对型胡牌"""
        # 不能吃碰杠
        if len(tiles[MHand.TYPE_CHI]) != 0:
            return False, 0, 0, 0
        if len(tiles[MHand.TYPE_PENG]) != 0:
            return False, 0, 0, 0
        if len(tiles[MHand.TYPE_GANG]) != 0:
            return False, 0, 0, 0
        # 用赖子给其他牌配对
        pairTiles = copy.deepcopy(tiles[MHand.TYPE_HAND])
        fourCount = 0
        twoCount = 0
        haveMagicCount = 0
        for magicTile in magicTiles:
            while magicTile in pairTiles:
                pairTiles.remove(magicTile)
                haveMagicCount += 1
        tileArr = MTile.changeTilesToValueArr(pairTiles)
        for count in tileArr:
            if count % 2 == 0:
                if count == 4:
                    fourCount += 1
                elif count == 2:
                    twoCount += 1
                continue
            else:
                if haveMagicCount <= 0:
                    return False, 0, 0, 0
                else:
                    haveMagicCount -= 1
                    if count == 3:
                        fourCount += 1
                    elif count == 1:
                        twoCount += 1
                    continue
        # 配对结束,赖子必须剩偶数个
        if haveMagicCount % 2 == 0:
            # 尽量凑4个的
            while haveMagicCount >= 2 and twoCount >= 1:
                twoCount -= 1
                fourCount += 1
                haveMagicCount -= 2
            return True, haveMagicCount, fourCount, twoCount
        return False, 0, 0, 0

    def testYunnan(self, ):
        """测试方法"""
        # 三元和混三元
        baibanCount = 2
        hongzhongCount = 2
        facaiCount = 0
        laiziCount = 4
        if baibanCount + laiziCount >= 2 \
                and hongzhongCount + laiziCount >= 2 \
                and facaiCount + laiziCount >= 2:
            if baibanCount + hongzhongCount + laiziCount >= 5 \
                    and baibanCount + facaiCount + laiziCount >= 5 \
                    and hongzhongCount + facaiCount + laiziCount >= 5:
                if baibanCount + facaiCount + hongzhongCount + laiziCount >= 8:
                    return True
        return False


if __name__ == "__main__":
    result = MYunnanOneResult()
    o = result.testYunnan()
    print o
