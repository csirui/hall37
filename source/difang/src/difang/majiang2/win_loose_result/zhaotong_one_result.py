# -*- coding=utf-8
'''
Created on 2016年11月17日

 昭通麻将结算

@author: zhangwei
'''
import copy

from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.tile.tile import MTile
from difang.majiang2.win_loose_result.one_result import MOneResult
from difang.majiang2.win_rule.win_rule_zhaotong import MWinRuleZhaotong
from freetime.util import log as ftlog


class MZhaotongOneResult(MOneResult):
    DUIDUIHU = 'duiduihu'
    QIDUI = 'qidui'
    LONGQIDUI = 'longqidui'
    SHUANGLONGDUI = 'shuanglongdui'
    QINGYISE = 'qingyise'
    QINGYISEDADUIZI = 'qingyisedaduizi'
    TIANHU = 'tianhu'
    DIHU = 'dihu'
    GANGSHANGHUA = 'gangshanghua'
    GANGSHANGPAO = 'gangshangpao'
    MEITINGYONG = 'meitingyong'
    YIGEN = 'yigen'
    LIANGGEN = 'lianggen'
    SANGEN = 'sangen'
    SIGEN = 'sigen'

    def __init__(self):
        super(MZhaotongOneResult, self).__init__()
        self.__fan_xing = {
            self.DUIDUIHU: {"name": "对对胡", "index": 3},
            self.QIDUI: {"name": "七对", "index": 3},
            self.LONGQIDUI: {"name": "龙七对", "index": 4},
            self.SHUANGLONGDUI: {"name": "双龙对", "index": 5},
            self.QINGYISE: {"name": "清一色", "index": 3},
            self.QINGYISEDADUIZI: {"name": "清一色大对子", "index": 5},
            self.GANGSHANGHUA: {"name": "杠上花", "index": 1},
            self.GANGSHANGPAO: {"name": "杠上炮", "index": 1},
            self.MEITINGYONG: {"name": "没听用", "index": 1},
            self.TIANHU: {"name": "天胡", "index": 4},
            self.DIHU: {"name": "地胡", "index": 4},
            self.YIGEN: {"name": "根", "index": 1},
            self.LIANGGEN: {"name": "两根", "index": 2},
            self.SANGEN: {"name": "三根", "index": 3},
            self.SIGEN: {"name": "四根", "index": 4}
        }

    @property
    def fanXing(self):
        return self.__fan_xing

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

        # 获得癞子数据
        magicTiles = self.tableTileMgr.getMagicTiles()
        colorStateNoMagic = [0 for _ in range(self.playerCount)]
        magicTileCountArr = [0 for _ in range(self.playerCount)]
        # 处理玩家手牌,得到一手不带癞子的花色
        for seatId in range(self.playerCount):
            tempArrColor = copy.deepcopy(playerAllTilesArr[seatId])
            # colorState里面要去掉赖子包含的花色
            for magicTile in magicTiles:
                while magicTile in tempArrColor:
                    tempArrColor.remove(magicTile)
                    magicTileCountArr[seatId] += 1
            # 重新处理一次花色,不算赖子
            colorStateNoMagic[seatId] = MTile.getColorCount(MTile.changeTilesToValueArr(tempArrColor))

        if self.resultType == self.RESULT_FLOW:
            # 昭通的流局需要查花猪和大叫
            # 查花猪,赖子不算,赖子可以算作任何已有的花色,要先处理一下赖子s
            pigs = []
            noTings = []
            tings = []
            huSeats = []
            for player in self.tableTileMgr.players:
                if player.hasHu:
                    huSeats.append(player.curSeatId)
            for seatId in range(self.playerCount):
                if colorStateNoMagic[seatId] >= 3:
                    pigs.append(seatId)
            tempScore = [0 for _ in range(self.playerCount)]
            if len(pigs) > 0:
                pigInfo = {
                    'pigs': pigs,
                    'playerCount': self.playerCount,
                    'scoreBase': baseScore,
                    'fanMax': 4,
                    'huSeats': []
                }

                # 会修改传入的score参数
                self.calcPigsScore(pigInfo, tempScore)
                self.setPigs(pigs)
                ftlog.debug("MYunnanOneResult calcScore Type = RESULT_FLOW calcPigsScore tempScore:", tempScore)

            # 开始查大叫
            # 查大叫,
            # 多给一个赖子能胡牌就算有叫
            for seatId in range(self.playerCount):
                if seatId in pigs or seatId in huSeats:
                    continue
                zhaoTongRule = MWinRuleZhaotong()
                tempNoTingTiles = copy.deepcopy(playerAllTiles[seatId])
                tempNoTingTiles[MHand.TYPE_HAND].append(magicTiles[0])
                result, _ = zhaoTongRule.checkHuByMagicTiles(tempNoTingTiles, magicTiles)
                if result:
                    tings.append(seatId)
                else:
                    noTings.append(seatId)
            fanTings = [0 for _ in range(self.playerCount)]
            # 计算听牌人的番型
            for ting in tings:
                # 番型
                fanData = {
                    'fan': 0,
                    'patterns': [],
                    'isUnique': False
                }
                fan = 1
                patterns = []
                isUnique = fanData.get('isUnique', False)
                tempTingTiles = copy.deepcopy(playerAllTiles[ting])
                tempTingTiles[MHand.TYPE_HAND].append(magicTiles[0])
                # 取出dropTiles和手牌
                dropTiles = self.tableTileMgr.dropTiles[ting]
                # 计算根,修改传入的fanData参数
                self.calcFanGen(fanData, tempTingTiles, magicTiles)
                # 七对必须门清,修改传入的fanData参数
                self.calcFanPairsSeven(fanData, tempTingTiles, magicTiles)
                # 没听用,只要有听用就不算,不管用不用来当赖子
                self.calcFanNoTingYong(fanData, playerAllTilesArr[ting], magicTiles)
                isDaduizi = False
                magicCount = 0
                # 大对子,门前不能有吃,手牌多加一个赖子,能保证都是3张
                if len(tempTingTiles[MHand.TYPE_CHI]) == 0:
                    duiziTiles = copy.deepcopy(tempTingTiles[MHand.TYPE_HAND])
                    for magicTile in magicTiles:
                        while magicTile in duiziTiles:
                            duiziTiles.remove(magicTile)
                            magicCount += 1
                    duiziArr = MTile.changeTilesToValueArr(duiziTiles)
                    ftlog.debug("MYunnanOneResult duiziArr = ", duiziArr)
                    cardTypeCount = 0
                    # 假设多一张赖子
                    duiziMagicCount = magicCount + 1
                    for index in range(len(duiziArr)):
                        if duiziArr[index] != 0:
                            cardTypeCount += 1
                            if duiziArr[index] < 3:
                                duiziMagicCount = duiziMagicCount - (3 - duiziArr[index])
                    if cardTypeCount <= 5 and duiziMagicCount >= 0:
                        patterns.append(self.fanXing[self.DUIDUIHU]['name'])
                        fan += self.fanXing[self.DUIDUIHU]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                        isDaduizi = True
                        # 清一色
                if colorStateNoMagic[ting] == 1:
                    if isDaduizi:
                        if not isUnique:
                            if self.fanXing[self.DUIDUIHU]['name'] in patterns:
                                patterns.remove(self.fanXing[self.DUIDUIHU]['name'])
                            patterns.append(self.fanXing[self.QINGYISEDADUIZI]['name'])
                            fan -= self.fanXing[self.DUIDUIHU]['index']
                            fan += self.fanXing[self.QINGYISEDADUIZI]['index']
                            ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                    else:
                        if not isUnique:
                            patterns.append(self.fanXing[self.QINGYISE]['name'])
                            fan += self.fanXing[self.QINGYISE]['index']
                            ftlog.debug("MYunnanOneResuFlt fanxing = ", patterns, "fan = ", fan)

                fanData['fan'] = fanData['fan'] + fan
                fanData['patterns'].extend(patterns)
                ftlog.debug("MYunnanOneResult gameFlow fanData = ", fanData)
                fanTings[ting] = fanData.get('fan', 0)
                # 打出过赖子最大只能胡一番
                for magicTile in magicTiles:
                    if magicTile in dropTiles:
                        if fanTings[ting] > 1:
                            fanTings[ting] = 1
                if fanTings[ting] >= 5:
                    fanTings[ting] = 5
            if len(noTings) > 0:
                tingInfo = {
                    'noTings': noTings,
                    'tings': tings,
                    'scoreBase': baseScore,
                    'fanArr': fanTings
                }
                self.calcTingScore(tingInfo, tempScore)
                self.setNoTings(noTings)
                ftlog.debug("MYunnanOneResult calcScore Type = RESULT_FLOW calcTingScore tempScore:", tempScore)

            self.results[self.KEY_TYPE] = MOneResult.KEY_TYPE_NAME_FLOW
            self.results[self.KEY_SCORE] = tempScore
            # 如果是最终结算,把数据取出来放在results里
            for seatId in huSeats:
                result = self.winRuleMgr.getHasHuDataBySeatId(seatId)
                if result:
                    self.results[self.KEY_WIN_MODE][seatId] = result.get('winMode', -1)
                    self.results[self.KEY_FAN_PATTERN][seatId] = result.get('fan', [])
                    self.results[self.KEY_WIN_TILE][seatId] = result.get('winTile', 0)
            # 清空保存的这些数据
            self.winRuleMgr.clearHasHuData()
            ftlog.debug("MYunnanOneResult calcScore Type = RESULT_FLOW return")
            return

        self.results[self.KEY_TYPE] = MOneResult.KEY_TYPE_NAME_HU

        if len(self.winSeats) <= 0:
            ftlog.debug("MYunnanOneResult self.winSeats error no winner")
            return
        ftlog.debug("MYunnanOneResultCalcScore self.winSeats = ", self.winSeats)

        if self.lastSeatId not in self.winSeats:
            self.results[self.KEY_WIN_MODE][self.lastSeatId] = MOneResult.WIN_MODE_DIANPAO

        maxFan = 0
        # 计算胡牌者的番型和分数
        for seatId in self.winSeats:
            # 番型
            fanData = {
                'fan': 0,
                'patterns': [],
                'isUnique': False,
                'isSpecial': False
            }
            ftlog.debug("MYunnanOneResultCalcScorelatestGangState = ", self.latestGangState)
            ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang dealwith seatId:'
                        , seatId
                        , 'lastSeatId:', self.lastSeatId
                        , 'winSeatId:', self.winSeatId
                        , 'self.winSeats:', self.winSeats
                        , 'self.actionID:', self.actionID
                        , 'self.bankerSeatId:', self.bankerSeatId
                        )
            if seatId == self.lastSeatId:
                self.results[self.KEY_WIN_MODE][seatId] = MOneResult.WIN_MODE_ZIMO
            else:
                self.results[self.KEY_WIN_MODE][seatId] = MOneResult.WIN_MODE_PINGHU

            # 取出dropTiles和手牌
            dropTiles = self.tableTileMgr.dropTiles[seatId]
            nowTiles = playerAllTiles[seatId]
            nowTiles[MHand.TYPE_HAND].append(self.winTile)
            # 计算根
            self.calcFanGen(fanData, nowTiles, magicTiles)
            # 杠上花和杠上炮
            self.calcFanAfterGang(fanData, self.latestGangState, seatId, self.lastSeatId)
            # 天胡地胡,没有出过牌,没有吃碰杠
            self.calcFanTianDiHu(fanData, seatId, self.bankerSeatId, self.lastSeatId, nowTiles, dropTiles)
            # 七对必须门清
            self.calcFanPairsSeven(fanData, nowTiles, magicTiles)
            # 没听用,只要有听用就不算,不管用不用来当赖子
            self.calcFanNoTingYong(fanData, playerAllTilesArr[seatId], magicTiles)
            # 大对子,门前不能有吃,手牌多加一个赖子,能保证都是3张
            isDaduizi = False
            _, _, _, isDaduizi = self.calcFanDaduizi(fanData, nowTiles, magicTiles, magicTileCountArr[seatId],
                                                     self.winTile, seatId, self.lastSeatId)
            # 清一色
            self.calcFanQingyise(fanData, colorStateNoMagic[seatId], isDaduizi)
            # 自摸是否加番的处理
            if self.winRuleMgr.zimoBonus == 2:
                if self.lastSeatId == seatId:
                    fanData['fan'] += 1
            # 如果对对胡,清一色,七对,龙七对,天胡,地胡,双龙对,清一色大对子,当不存在以上番型时 有平胡的1番
            if not fanData.get('isSpecial', False):
                fanData['fan'] += 1
            ftlog.debug("MYunnanOneResult fanData = ", fanData)
            self.results[self.KEY_WIN_TILE][seatId] = self.winTile
            self.results[self.KEY_FAN_PATTERN][seatId] = copy.deepcopy(fanData['patterns'])
            fanArr[seatId] = fanData.get('fan', 0)
            # 打出过赖子最大只能胡一番
            for magicTile in magicTiles:
                if magicTile in dropTiles:
                    if fanArr[seatId] > 1:
                        fanArr[seatId] = 1
            if fanArr[seatId] > maxFan:
                maxFan = fanArr[seatId]
        if self.lastSeatId in self.winSeats:
            self.results[self.KEY_STAT][self.lastSeatId].append({MOneResult.STAT_ZIMO: 1})
        else:
            # 点炮,点炮者点炮+1
            self.results[self.KEY_STAT][self.lastSeatId].append({MOneResult.STAT_DIANPAO: 1})
        # 最大番,当前的赢家番数
        self.results[self.KEY_STAT][seatId].append({MOneResult.STAT_ZUIDAFAN: maxFan})

        # 番数上限5
        for win in self.winSeats:
            if fanArr[win] > 5:
                fanArr[win] = 5

        # 把血战里面已经胡牌的人的位置挑出来
        hasHu = []
        for player in self.tableTileMgr.players:
            if player.hasHu:
                hasHu.append(player.curSeatId)
        if len(hasHu) >= self.playerCount - 1:
            ftlog.error("MZhaotongOneReuslt hasHu Error hasHu:", hasHu)

            # 计算积分
        #         winScore = baseScore*(self.multiple)
        winScore = baseScore
        if self.qiangGang:
            # 如果是最后一个输的人被抢杠胡,需要把被抢的牌从他手中拿掉
            if len(hasHu) + len(self.winSeats) >= self.playerCount - 1:
                for player in self.tableTileMgr.players:
                    if player.curSeatId == self.lastSeatId and self.lastSeatId not in self.winSeats:
                        if self.winTile in player.handTiles:
                            player.handTiles.remove(self.winTile)
                        else:
                            player.handTiles.remove(magicTiles[0])
            for seatId in self.winSeats:
                self.results[self.KEY_WIN_MODE][seatId] = MOneResult.WIN_MODE_QIANGGANGHU

        # 计算分数增减
        if self.lastSeatId in self.winSeats:
            for i in range(self.playerCount):
                if self.lastSeatId == i:
                    looseCount = self.playerCount - 1 - len(hasHu)
                    if looseCount <= 0:
                        looseCount = 1
                    self.results[self.KEY_SCORE][i] = winScore * (2 ** (fanArr[i] - 1)) * looseCount
                elif i in hasHu:
                    continue
                else:
                    self.results[self.KEY_SCORE][i] = -winScore * (2 ** (fanArr[self.lastSeatId] - 1))
        else:
            dianPaoScore = 0
            for i in range(self.playerCount):
                if i in self.winSeats:
                    if i not in hasHu:
                        self.results[self.KEY_SCORE][i] = winScore * (2 ** (fanArr[i] - 1))
                        dianPaoScore += winScore * (2 ** (fanArr[i] - 1))
            self.results[self.KEY_SCORE][self.lastSeatId] = -dianPaoScore

        if self.playerCount - len(hasHu) - len(self.winSeats) == 1:
            # 如果是最终结算,把数据取出来放在results里
            for seatId in hasHu:
                result = self.winRuleMgr.getHasHuDataBySeatId(seatId)
                if result:
                    self.results[self.KEY_WIN_MODE][seatId] = result.get('winMode', -1)
                    self.results[self.KEY_FAN_PATTERN][seatId] = result.get('fan', [])
                    self.results[self.KEY_WIN_TILE][seatId] = result.get('winTile', 0)
            # 清空保存的这些数据
            self.winRuleMgr.clearHasHuData()
        else:
            # 如果不是最终结算,把胜者的一些信息存起来
            for seatId in self.winSeats:
                result = {
                    'winMode': self.results[self.KEY_WIN_MODE][seatId],
                    'fan': self.results[self.KEY_FAN_PATTERN][seatId],
                    'winTile': self.results[self.KEY_WIN_TILE][seatId]
                }
                self.winRuleMgr.saveHasHuData(result, seatId)

        ftlog.debug('MYunnanOneResult calcScore:KEY_SCORE:', self.results[self.KEY_SCORE])
        ftlog.debug('MYunnanOneResult calcScore:KEY_NAME:', self.results[self.KEY_NAME])
        ftlog.debug('MYunnanOneResult calcScore:KEY_TYPE:', self.results[self.KEY_TYPE])
        ftlog.debug('MYunnanOneResult calcScore:KEY_WIN_MODE:', self.results[self.KEY_WIN_MODE])
        ftlog.debug('MYunnanOneResult calcScore:KEY_FAN_PATTERN:', self.results[self.KEY_FAN_PATTERN])
        ftlog.debug('MYunnanOneResult calcScore:KEY_STAT:', self.results[self.KEY_STAT])

    def isPairsCheck(self, tiles, magicTiles):
        """判断七对型胡牌"""
        # 不能吃碰杠
        if len(tiles[MHand.TYPE_CHI]) != 0:
            return False, 0, 0, 0, 0
        if len(tiles[MHand.TYPE_PENG]) != 0:
            return False, 0, 0, 0, 0
        if len(tiles[MHand.TYPE_GANG]) != 0:
            return False, 0, 0, 0, 0
        # 用赖子给其他牌配对
        pairTiles = copy.deepcopy(tiles[MHand.TYPE_HAND])
        fourCount = 0
        specialFourCount = 0
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
                    return False, 0, 0, 0, 0
                else:
                    haveMagicCount -= 1
                    if count == 3:
                        specialFourCount += 1
                        fourCount += 1
                    elif count == 1:
                        twoCount += 1
                    continue
        # 配对结束,赖子必须剩偶数个
        if haveMagicCount % 2 == 0:
            # 尽量凑4个的
            while haveMagicCount >= 2 and twoCount >= 1:
                twoCount -= 1
                specialFourCount += 1
                fourCount += 1
                haveMagicCount -= 2
            return True, haveMagicCount, fourCount, twoCount, specialFourCount
        return False, 0, 0, 0, 0

    def calcPigsScore(self, pigInfo, score):
        """计算查花猪的分数"""
        if pigInfo.has_key('pigs') \
                and pigInfo.has_key('playerCount') \
                and pigInfo.has_key('scoreBase') \
                and pigInfo.has_key('fanMax') \
                and pigInfo.has_key('huSeats'):
            pigs = pigInfo['pigs']
            playerCount = pigInfo['playerCount']
            fanMax = pigInfo['fanMax']
            scoreBase = pigInfo['scoreBase']
            huSeats = pigInfo['huSeats']
            ftlog.debug("calcPigsScore pigInfo pigs:", pigs
                        , "playerCount:", playerCount
                        , "fanMax:", fanMax
                        , "scoreBase:", scoreBase
                        , "huSeats:", huSeats
                        , "score:", score)
            if playerCount != len(score):
                ftlog.debug("calcPigsScore playerCount!=len(score) error playerCount:", playerCount, 'score:', score)
                return
            for pig in pigs:
                if pig in huSeats:
                    ftlog.debug("calcPigsScore error pig hasHu pigs:", pigs, 'huSeats:', huSeats)
                    return
                    # 遍历花猪不检查是否胡牌,因为计算花猪时就要排除
            for pig in pigs:
                for index in range(playerCount):
                    if index in huSeats:
                        continue
                    else:
                        if index not in pigs:
                            score[index] += scoreBase * (2 ** (fanMax - 1))
                            score[pig] -= scoreBase * (2 ** (fanMax - 1))
            ftlog.debug("calcPigsScore score:", score)
        else:
            ftlog.debug("calcPigsScore pigInfo error, pigInfo:", pigInfo)
            return

    def calcTingScore(self, tingInfo, score):
        """计算查大叫的分数"""
        if tingInfo.has_key('noTings') \
                and tingInfo.has_key('tings') \
                and tingInfo.has_key('scoreBase') \
                and tingInfo.has_key('fanArr'):
            noTings = tingInfo['noTings']
            tings = tingInfo['tings']
            fanArr = tingInfo['fanArr']
            scoreBase = tingInfo['scoreBase']
            ftlog.debug("calcPigsScore tingInfo pigs:", noTings
                        , "tings:", tings
                        , "fanArr:", fanArr
                        , "scoreBase:", scoreBase
                        , "score:", score)
            for noTing in noTings:
                for ting in tings:
                    if ting not in noTings:
                        score[ting] += scoreBase * (2 ** (fanArr[ting] - 1))
                        score[noTing] -= scoreBase * (2 ** (fanArr[ting] - 1))
            ftlog.debug("calcPigsScore score:", score)
        else:
            ftlog.debug("calcPigsScore pigInfo error, tingInfo:", tingInfo)
            return

    '''
    计算番数的方法
    '''

    def calcGenCount(self, tiles, magicTile, mFactor):
        """算单癞子情况下一手牌里的根,墙上牌三张就算一根,三张+一个癞子还能多加一番"""
        genCount = 0
        extraFan = 0
        workTiles = copy.deepcopy(tiles)
        matchedPattern = {'gang': [],
                          'peng': []}
        if len(tiles[MHand.TYPE_GANG]) > 0:
            for gangInfo in tiles[MHand.TYPE_GANG]:
                if mFactor in gangInfo['pattern']:
                    extraFan = 1
                matchedPattern['gang'].append(gangInfo)
                ftlog.debug("gangAdd0")
                break
            genCount += len(tiles[MHand.TYPE_GANG])
        if len(tiles[MHand.TYPE_PENG]) > 0:
            # 先找一遍因子,优先匹配因子
            for peng in tiles[MHand.TYPE_PENG]:
                if mFactor in peng:
                    genCount += 1
                    #                     extraFan = 1
                    matchedPattern['peng'].append(peng)
                    ftlog.debug("pengAdd0")
                    break
            # 再找其他的 跳过因子  
            for peng in tiles[MHand.TYPE_PENG]:
                matchedOk = False
                if mFactor in peng:
                    continue
                for pengTile in peng:
                    if pengTile != magicTile:
                        # 优先匹配非癞子
                        for handTile in workTiles[MHand.TYPE_HAND]:
                            if pengTile == handTile:
                                # 碰的母牌 手里还有  一定算一根
                                genCount += 1
                                matchedOk = True
                                ftlog.debug("pengAdd1")
                                matchedPattern['peng'].append(peng)
                                break
                        if matchedOk:
                            # 匹配成功直接找下一组碰
                            break
                        else:
                            for handTile in workTiles[MHand.TYPE_HAND]:
                                if handTile == magicTile:
                                    # 手里有癞子, 替换成碰的母牌 看是否能胡牌,能胡的话算一根
                                    workTiles[MHand.TYPE_HAND].remove(handTile)
                                    workTiles[MHand.TYPE_HAND].append(pengTile)
                                    result, _ = MWinRuleZhaotong.checkHuByMagicTiles(workTiles, [magicTile])
                                    if result:
                                        genCount += 1
                                        ftlog.debug("pengAdd2")
                                        matchedPattern['peng'].append(peng)
                                    else:
                                        # 还原手牌
                                        workTiles[MHand.TYPE_HAND].remove(pengTile)
                                        workTiles[MHand.TYPE_HAND].append(handTile)
                                    break

                        break
        tempGenArr = copy.deepcopy(workTiles[MHand.TYPE_HAND])
        genMagicCount = 0
        ftlog.debug("MYunnanOneResultCalcScore GENINFO tempGenArr", tempGenArr
                    , "genMagicCount", genMagicCount
                    , "magicTile", magicTile
                    , "mFactor", mFactor
                    , "genCount", genCount
                    )

        while magicTile in tempGenArr:
            tempGenArr.remove(magicTile)
            genMagicCount += 1
        factorCount = 0
        while mFactor in tempGenArr:
            tempGenArr.remove(mFactor)
            factorCount += 1
        if factorCount + genMagicCount >= 4:
            genCount += 1
            extraFan = 1
            ftlog.debug("handAdd0")
            genMagicCount -= 4 - factorCount
        elif factorCount + genMagicCount >= 3:
            genCount += 1
            ftlog.debug("handAdd0.5")
            genMagicCount -= 3 - factorCount
        tileValueArr = MTile.changeTilesToValueArr(tempGenArr)
        tileIndex = 0
        handTileCount = {3: [], 2: [], 1: []}
        # 4个癞子的情况单独考虑
        for count in tileValueArr:
            if tileIndex <= 0 or tileIndex >= 30:
                tileIndex += 1
                continue
            if count == 4:
                genCount += 1
                ftlog.debug("handAdd1")
            elif count == 3:
                handTileCount[3].append(tileIndex)
            elif count == 2:
                handTileCount[2].append(tileIndex)
            elif count == 1:
                handTileCount[1].append(tileIndex)
            tileIndex += 1
        addGenCount = {}
        for i in range(3):
            if genMagicCount > 0 and len(handTileCount[i + 1]) > 0:
                addGenCount[i + 1], genMagicCount = self.dealWithGenCount(workTiles, handTileCount[i + 1], i + 1,
                                                                          genMagicCount, magicTile)
            else:
                break
        for i in range(3):
            if addGenCount.has_key(i + 1):
                genCount += addGenCount.get(i + 1, 0)
        ftlog.debug("MYunnanOneResultCalcScore GENINFO tempGenArr", tempGenArr
                    , "genMagicCount", genMagicCount
                    , "magicTile", magicTile
                    , "mFactor", mFactor
                    , "genCount", genCount
                    , "matchedPattern", matchedPattern
                    )
        return genCount, extraFan

    def dealWithGenCount(self, tiles, genTileInfo, count, genMagicCount, magicTile):
        genCount = 0
        for tile in genTileInfo:
            if genMagicCount > 0 and tile > 0 and tile < 30:
                if count + genMagicCount >= 4:
                    for _ in range(4 - count):
                        tiles[MHand.TYPE_HAND].remove(magicTile)
                        tiles[MHand.TYPE_HAND].append(tile)
                    result3, _ = MWinRuleZhaotong.checkHuByMagicTiles(tiles, [magicTile])
                    if result3:
                        ftlog.debug("handAdd2")
                        genCount += 1
                        genMagicCount -= 4 - count
                    else:
                        for _ in range(4 - count):
                            tiles[MHand.TYPE_HAND].remove(tile)
                            tiles[MHand.TYPE_HAND].append(magicTile)
        return genCount, genMagicCount

    def calcFanGen(self, fanData, tiles, magicTiles):
        fan = fanData.get('fan', 0)
        patterns = fanData.get('patterns', [])
        isUnique = fanData.get('isUnique', False)
        # 找出最开始弃掉的那张牌
        genCount = 0
        extraFan = 0
        magicFactors = []
        for magicTile in magicTiles:
            if magicTile >= MTile.TILE_DONG_FENG:
                continue
            if magicTile % 10 == 1:
                magicFactors.append(magicTile + 8)
            else:
                magicFactors.append(magicTile - 1)
        genCount, extraFan = self.calcGenCount(tiles, magicTiles[0], magicFactors[0])
        if genCount == 1:
            if not isUnique:
                patterns.append(self.fanXing[self.YIGEN]['name'])
                fan += self.fanXing[self.YIGEN]['index'] + extraFan
                ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
        elif genCount == 2:
            if not isUnique:
                patterns.append(self.fanXing[self.LIANGGEN]['name'])
                fan += self.fanXing[self.LIANGGEN]['index'] + extraFan
                ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
        elif genCount == 3:
            if not isUnique:
                patterns.append(self.fanXing[self.SANGEN]['name'])
                fan += self.fanXing[self.SANGEN]['index'] + extraFan
                ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
        elif genCount == 4:
            if not isUnique:
                patterns.append(self.fanXing[self.SIGEN]['name'])
                fan += self.fanXing[self.SIGEN]['index'] + extraFan
                ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
        fanData['isUnique'] = isUnique
        fanData['fan'] = fan
        return fan, patterns, isUnique

    def calcFanPairsSeven(self, fanData, nowTiles, magicTiles):
        fan = fanData.get('fan', 0)
        patterns = fanData.get('patterns', [])
        isUnique = fanData.get('isUnique', False)
        isSpecial = fanData.get('isSpecial', False)
        pairResult, leftMagicCount, fourCount, _, spFourCount = self.isPairsCheck(nowTiles, magicTiles)
        if pairResult:
            if fourCount >= 2:
                if spFourCount >= 1:
                    # 四张超过两个,并且有一个四张包含至少一个赖子,就是双龙对
                    if not isUnique:
                        patterns.append(self.fanXing[self.SHUANGLONGDUI]['name'])
                        fan += self.fanXing[self.SHUANGLONGDUI]['index']
                        ftlog.debug("MYunnanOneResult fanxing = SHUANGLONGDUI", patterns, "fan = ", fan)
                        isSpecial = True
                else:
                    # 没有赖子参与4张的只能算龙七对
                    if not isUnique:
                        patterns.append(self.fanXing[self.LONGQIDUI]['name'])
                        fan += self.fanXing[self.LONGQIDUI]['index']
                        ftlog.debug("MYunnanOneResult fanxing = LONGQIDUI1", patterns, "fan = ", fan)
                        isSpecial = True
            elif fourCount == 1:
                # 一个四张,算龙七对
                if not isUnique:
                    patterns.append(self.fanXing[self.LONGQIDUI]['name'])
                    fan += self.fanXing[self.LONGQIDUI]['index']
                    ftlog.debug("MYunnanOneResult fanxing = LONGQIDUI2", patterns, "fan = ", fan)
                    isSpecial = True
            else:
                # 普通七对
                if not isUnique:
                    patterns.append(self.fanXing[self.QIDUI]['name'])
                    fan += self.fanXing[self.QIDUI]['index']
                    ftlog.debug("MYunnanOneResult fanxing = QIDUI", patterns, "fan = ", fan)
                    isSpecial = True
        fanData['isUnique'] = isUnique
        fanData['fan'] = fan
        fanData['isSpecial'] = isSpecial
        return fan, patterns, isUnique

    def calcFanAfterGang(self, fanData, latestGangState, seatId, lastSeatId):
        fan = fanData.get('fan', 0)
        patterns = fanData.get('patterns', [])
        isUnique = fanData.get('isUnique', False)
        if latestGangState != -1:
            if latestGangState == seatId:
                # 杠牌的是自己
                if not isUnique:
                    patterns.append(self.fanXing[self.GANGSHANGHUA]['name'])
                    fan += self.fanXing[self.GANGSHANGHUA]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
            elif latestGangState == lastSeatId:
                # 杠牌的是别人
                if not isUnique:
                    patterns.append(self.fanXing[self.GANGSHANGPAO]['name'])
                    fan += self.fanXing[self.GANGSHANGPAO]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
        fanData['isUnique'] = isUnique
        fanData['fan'] = fan
        return fan, patterns, isUnique

    def calcFanTianDiHu(self, fanData, seatId, bankerSeatId, lastSeatId, nowTiles, dropTiles):
        fan = fanData.get('fan', 0)
        patterns = fanData.get('patterns', [])
        isUnique = fanData.get('isUnique', False)
        isSpecial = fanData.get('isSpecial', False)
        if len(nowTiles[MHand.TYPE_CHI]) != 0 or len(nowTiles[MHand.TYPE_PENG]) != 0 or len(
                nowTiles[MHand.TYPE_GANG]) != 0:
            return fan, patterns, isUnique
        if len(dropTiles) != 0:
            return fan, patterns, isUnique
        if bankerSeatId == seatId:
            # 如果是庄家是天胡
            if not isUnique:
                patterns.append(self.fanXing[self.TIANHU]['name'])
                fan += self.fanXing[self.TIANHU]['index']
                ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                isSpecial = True
        else:
            # 其它人如果自摸就是地胡,如果点炮看出牌的是不是庄家
            if lastSeatId == seatId:
                if not isUnique:
                    patterns.append(self.fanXing[self.DIHU]['name'])
                    fan += self.fanXing[self.DIHU]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                    isSpecial = True
            else:
                if lastSeatId == bankerSeatId:
                    if not isUnique:
                        patterns.append(self.fanXing[self.DIHU]['name'])
                        fan += self.fanXing[self.DIHU]['index']
                        ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                        isSpecial = True
        fanData['isUnique'] = isUnique
        fanData['fan'] = fan
        fanData['isSpecial'] = isSpecial
        return fan, patterns, isUnique

    def calcFanNoTingYong(self, fanData, allTilesArr, magicTiles):
        """计算没听用番型"""
        fan = fanData.get('fan', 0)
        patterns = fanData.get('patterns', [])
        isUnique = fanData.get('isUnique', False)
        isNoTingYong = True
        ftlog.debug("MYunnanOneResultmeitingyong playerAllTilesArr[seatId]:", allTilesArr, "magicTiles:", magicTiles)
        for tempTile in allTilesArr:
            if tempTile in magicTiles:
                isNoTingYong = False
        if isNoTingYong:
            if not isUnique:
                self.results[self.KEY_NAME] = self.fanXing[self.MEITINGYONG]['name']
                patterns.append(self.fanXing[self.MEITINGYONG]['name'])
                fan += self.fanXing[self.MEITINGYONG]['index']
                ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
        fanData['isUnique'] = isUnique
        fanData['fan'] = fan
        return fan, patterns, isUnique

    def calcFanDaduizi(self, fanData, nowTiles, magicTiles, magicTileCount, winTile, seatId, lastSeatId):
        """计算大对子番型"""
        fan = fanData.get('fan', 0)
        patterns = fanData.get('patterns', [])
        isUnique = fanData.get('isUnique', False)
        isSpecial = fanData.get('isSpecial', False)
        isDaduizi = False
        # 大对子,门前不能有吃,手牌多加一个赖子,能保证都是3张
        if len(nowTiles[MHand.TYPE_CHI]) == 0:
            duiziTiles = copy.deepcopy(nowTiles[MHand.TYPE_HAND])
            for magicTile in magicTiles:
                while magicTile in duiziTiles:
                    duiziTiles.remove(magicTile)
            # 如果点炮胡,需要给牌堆里加回去一张赖子,并当普通牌处理
            if seatId != lastSeatId and winTile in magicTiles:
                duiziTiles.append(winTile)
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
                if not isUnique:
                    patterns.append(self.fanXing[self.DUIDUIHU]['name'])
                    fan += self.fanXing[self.DUIDUIHU]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                    isDaduizi = True
                    isSpecial = True
        fanData['isUnique'] = isUnique
        fanData['fan'] = fan
        fanData['isSpecial'] = isSpecial
        return fan, patterns, isUnique, isDaduizi

    def calcFanQingyise(self, fanData, colorStateNoMagic, isDaduizi=False):
        fan = fanData.get('fan', 0)
        patterns = fanData.get('patterns', [])
        isUnique = fanData.get('isUnique', False)
        isSpecial = fanData.get('isSpecial', False)
        if colorStateNoMagic == 1:
            if isDaduizi:
                if not isUnique:
                    if self.fanXing[self.DUIDUIHU]['name'] in patterns:
                        patterns.remove(self.fanXing[self.DUIDUIHU]['name'])
                    patterns.append(self.fanXing[self.QINGYISEDADUIZI]['name'])
                    fan -= self.fanXing[self.DUIDUIHU]['index']
                    fan += self.fanXing[self.QINGYISEDADUIZI]['index']
                    ftlog.debug("MYunnanOneResult fanxing = ", patterns, "fan = ", fan)
                    isSpecial = True
            else:
                if not isUnique:
                    patterns.append(self.fanXing[self.QINGYISE]['name'])
                    fan += self.fanXing[self.QINGYISE]['index']
                    ftlog.debug("MYunnanOneResuFlt fanxing = ", patterns, "fan = ", fan)
                    isSpecial = True
        fanData['isUnique'] = isUnique
        fanData['fan'] = fan
        fanData['isSpecial'] = isSpecial
        return fan, patterns, isUnique

    '''
    def calcFan(self, fanData):
        fan = fanData.get('fan', 0)
        patterns = fanData.get('patterns', [])
        isUnique = fanData.get('isUnique', False)
        fanData['isUnique'] = isUnique
        fanData['fan'] = fan
        return fan, patterns, isUnique    
    '''
