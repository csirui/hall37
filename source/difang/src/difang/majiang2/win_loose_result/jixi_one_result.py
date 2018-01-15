# -*- coding=utf-8
'''
Created on 2016年9月23日

一条和牌结果

@author: zhaol
'''
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.table.table_config_define import MTDefine
from difang.majiang2.tile.tile import MTile
from difang.majiang2.win_loose_result.one_result import MOneResult
from freetime.util import log as ftlog


class MJixiOneResult(MOneResult):
    # 特殊番型
    WUDUIHU = 'wuDuiHu'  # 三人麻将中 起手手牌无对子 直接胡 输家给赢家10分 庄家不翻倍 没有其它叠加
    TIANHU = 'tianHu'
    # 基本番型
    ZIMO = 'ziMo'
    GANGKAI = 'gangKai'
    QIANGGANG = 'qiangGang'
    JIAHU = 'jiaHu'
    DANDIAO = 'danDiao'
    QINGYISE_1 = 'qingYiSe1'  # 当出现三番番型和五番番型时 清一色算1番(叠加) 避免太大
    # 二番番型
    MOBAO = 'moBao'
    BAOBIAN = 'baoBian'  # 通宝 胡的是宝牌的时候 听牌之后直接胡 如果胡的是对倒 两头 飘 七对 就算宝边也叫通宝
    # 三番番型
    QIXIAODUI = 'qiXiaoDui'  # 七小对不算单吊 与单吊平级 二番
    PIAOHU = 'piaoHu'  # 飘胡 对对胡 都是碰
    QINGYISE = 'qingYiSe'  # 和的不是七小对 飘 特大夹 宝中宝的时候算三番 否则算一番
    TEDAJIA = 'teDaJia'
    # 五番番型
    BAOZHONGBAOJIA = 'baoZhongBaoJia'  # 和通宝一样的规则 是夹或者单吊时
    # 预留 先不做
    BIANJIASHUANG = 'bianJiaShuang'
    # 输家番型
    DIANPAO = 'dianPao'
    DIANPAOBAOZHUANG = 'dianPaoBaoZhuang'
    # 闭门可配置 默认不算番
    BIMEN = 'biMen'

    # 最大分数限制
    MAX_SCORE_LIMIT = 128

    def __init__(self):
        super(MJixiOneResult, self).__init__()
        self.__fan_xing = {
            self.WUDUIHU: {"name": "无对胡 ", "index": 0},
            self.TIANHU: {"name": "天胡 ", "index": 6},
            self.ZIMO: {"name": "自摸 ", "index": 1},
            self.GANGKAI: {"name": "杠上开花 ", "index": 1},
            self.QIANGGANG: {"name": "抢杠胡 ", "index": 1},
            self.JIAHU: {"name": "夹胡 ", "index": 1},
            self.DANDIAO: {"name": "单吊 ", "index": 1},
            self.QINGYISE_1: {"name": "清一色 ", "index": 1},
            self.MOBAO: {"name": "摸宝 ", "index": 2},
            self.BAOBIAN: {"name": "通宝 ", "index": 2},
            self.QIXIAODUI: {"name": "七对 ", "index": 3},
            self.PIAOHU: {"name": "飘胡 ", "index": 3},
            self.QINGYISE: {"name": "清一色 ", "index": 3},
            self.TEDAJIA: {"name": "特大夹 ", "index": 3},
            self.BAOZHONGBAOJIA: {"name": "宝中宝 ", "index": 5},
            # 输家番型
            self.DIANPAO: {"name": "点炮 ", "index": 1},  # winMode展示
            self.DIANPAOBAOZHUANG: {"name": "包庄 ", "index": 1},  # winMode展示
            self.BIMEN: {"name": "闭门 ", "index": 1},
        }

    @property
    def fanXing(self):
        return self.__fan_xing

    def isWinTile(self):
        """获胜牌在winNodes中，而且是宝牌"""
        ftlog.debug('MJixiOneResult.isWinTile winTile:', self.winTile
                    , ' winNodes:', self.winNodes)

        for wn in self.winNodes:
            if wn['winTile'] == self.winTile:
                return True

        return False

    def isMagicTile(self):
        """是不是宝牌"""
        magics = self.tableTileMgr.getMagicTiles(True)
        ftlog.debug('MJixiOneResult.isMagicTile winTile:', self.winTile
                    , ' magicTiles:', magics)

        return self.winTile in magics

    def isDanDiao(self):
        if not self.isWinTile():
            return False

        for wn in self.winNodes:
            if wn['winTile'] == self.winTile:
                patterns = wn['pattern']
                ftlog.debug('MJixiOneResult.isDanDiao winTile:', self.winTile, ' winPatterns:', patterns)
                for p in patterns:
                    if len(p) != 2:
                        continue

                    if (self.winTile in p) and p[0] == p[1]:
                        return True

        # 宝牌情况时判断单吊
        if self.isMagicTile():
            for wn in self.winNodes:
                winTile = wn['winTile']
                patterns = wn['pattern']
                ftlog.debug('MJixiOneResult.isDanDiao winTile:', self.winTile, ' winPatterns:', patterns)
                for p in patterns:
                    if len(p) != 2:
                        continue

                    if (winTile in p) and p[0] == p[1]:
                        return True

        return False

    def isJia(self):
        """是否夹牌"""
        if not self.isWinTile():
            return False

        for wn in self.winNodes:
            if wn['winTile'] == self.winTile:
                patterns = wn['pattern']
                ftlog.debug('MJixiOneResult.isJia winTile:', self.winTile, ' winPatterns:', patterns)
                for p in patterns:
                    if len(p) == 2:
                        continue

                    if p[0] == p[1]:
                        continue

                    if (self.winTile in p) and (p.index(self.winTile)) == 1:
                        return True

        # 宝牌情况处理
        if self.isMagicTile():
            for wn in self.winNodes:
                winTile = wn['winTile']
                patterns = wn['pattern']
                for p in patterns:
                    if len(p) == 2:
                        continue

                    if p[0] == p[1]:
                        continue

                    if (winTile in p) and (p.index(winTile)) == 1:
                        return True

        return False

    # 没有吃 没有碰 没有杠
    def isQiDui(self):
        playerChiTiles = self.playerAllTiles[self.winSeatId][MHand.TYPE_CHI]
        if len(playerChiTiles) > 0:
            return False

        playerPengTiles = self.playerAllTiles[self.winSeatId][MHand.TYPE_PENG]
        if len(playerPengTiles) > 0:
            return False

        playerGangTiles = self.playerAllTiles[self.winSeatId][MHand.TYPE_GANG]
        if len(playerGangTiles) > 0:
            return False

        for wn in self.winNodes:
            if wn['winTile'] == self.winTile:
                patterns = wn['pattern']
                ftlog.debug('MJixiOneResult.isQiDui winTile:', self.winTile, ' winPatterns:', patterns)
                for p in patterns:
                    if len(p) == 3:
                        return False

        # 宝牌情况
        if self.isMagicTile():
            for wn in self.winNodes:
                winTile = wn['winTile']
                patterns = wn['pattern']
                for p in patterns:
                    if (winTile in p) and len(p) == 3:
                        return False

        handTiles = self.playerAllTiles[self.winSeatId][MHand.TYPE_HAND]
        newHandTiles = MTile.cloneTiles(handTiles)
        ftlog.debug('MTingJixiRule.MTing.canTing isQiDui handTiles:', handTiles, 'isMagic:', self.isMagicTile(),
                    'winTile:', self.winTile)
        newHandTiles.append(self.winTile)
        handTilesArr = MTile.changeTilesToValueArr(newHandTiles)
        duiCount = 0
        for index in range(len(handTilesArr)):
            if handTilesArr[index] == 2:
                duiCount += 1
            elif handTilesArr[index] == 4:
                duiCount += 2

        if duiCount == 7 or (duiCount == 6 and self.isMagicTile()):  # 宝牌情况
            return True

        return False

    # 胡牌的番型 手牌 没有吃 没有粘 至少有一个刻
    def isPiao(self):
        playerChiTiles = self.playerAllTiles[self.winSeatId][MHand.TYPE_CHI]
        if len(playerChiTiles) > 0:
            return False

        isHasKe = False
        playerPengTiles = self.playerAllTiles[self.winSeatId][MHand.TYPE_PENG]
        if len(playerPengTiles) > 0:
            isHasKe = True

        playerGangTiles = self.playerAllTiles[self.winSeatId][MHand.TYPE_GANG]
        if len(playerGangTiles) > 0:
            isHasKe = True

        playerHandTiles = self.playerAllTiles[self.winSeatId][MHand.TYPE_HAND]
        newPlayerHandTiles = MTile.cloneTiles(playerHandTiles)
        newPlayerHandTilesArr = MTile.changeTilesToValueArr(newPlayerHandTiles)
        for playerHandTileCount in newPlayerHandTilesArr:
            if playerHandTileCount == 3:
                isHasKe = True
                break

        if not isHasKe:
            return False

        for wn in self.winNodes:
            # if wn['winTile'] == self.winTile:
            patterns = wn['pattern']
            ftlog.debug('MJixiOneResult.isPiao winTile:', self.winTile, ' winPatterns:', patterns)
            for p in patterns:
                if len(p) == 3 and p[0] != p[1]:
                    return False

        return True

    def isQingYiSe(self):
        if self.colorState[self.winSeatId] == 1:
            return True
        return False

    # 胡牌是别人的碰牌或者自己的碰牌以及手牌中的刻牌且手牌中的刻牌不能作为他用(34445)
    def isTeDaJia(self):
        if self.isMagicTile():  # 先排除宝牌直接(摸宝)胡牌的情况
            isMoboHu = True
            for wn in self.winNodes:
                if self.winTile == wn['winTile']:
                    isMoboHu = False
                    break
            if isMoboHu:
                return False

        # 他人的碰牌
        isInOtherPeng = False
        for seatId in range(self.playerCount):
            if seatId != self.winSeatId:
                playerPengTiles = self.playerAllTiles[seatId][MHand.TYPE_PENG]
                for pattern in playerPengTiles:
                    if pattern[0] == self.winTile:
                        isInOtherPeng = True
                        break;

        # 自己的手牌
        isInSelfKe = False
        playerHandTiles = self.playerAllTiles[self.winSeatId][MHand.TYPE_HAND]
        for pattern in playerHandTiles:
            if pattern[0] == self.winTile:
                isInSelfKe = True
                break

        playerPengTiles = self.playerAllTiles[self.winSeatId][MHand.TYPE_PENG]
        for pattern in playerPengTiles:
            if pattern[0] == self.winTile:
                isInSelfKe = True
                break

        if not (isInSelfKe or isInOtherPeng):
            return False

        bianMulti = self.tableConfig.get(MTDefine.BIAN_MULTI, 0)
        for wn in self.winNodes:
            winTile = wn['winTile']
            if winTile == self.winTile:
                patterns = wn['pattern']
                for p in patterns:
                    # 夹牌
                    if (winTile in p) and len(p) == 3 and p[0] != p[1]:
                        if (p[1] == self.winTile) or (bianMulti and self.isSanQi()):
                            return True

        return False

    def isSanQi(self, winTile=None):
        if winTile == None:
            winTile = self.winTile
        if MTile.getValue(winTile) == 3 or MTile.getValue(winTile) == 7:
            return True
        return False

    # 胡的就是宝牌
    def isHuMagicTile(self):
        magics = self.tableTileMgr.getMagicTiles(True)
        for wn in self.winNodes:
            if wn['winTile'] in magics:
                return True
        return False

    def isBian(self):
        """是否夹牌"""
        if not self.isWinTile():
            return False

        for wn in self.winNodes:
            if wn['winTile'] == self.winTile:
                patterns = wn['pattern']
                ftlog.debug('MJixiOneResult.isBian winTile:', self.winTile, ' winPatterns:', patterns)
                for p in patterns:
                    if len(p) == 2:
                        continue

                    if p[0] == p[1]:
                        continue

                    if (self.winTile in p) and (p.index(self.winTile) == 0):
                        return True

                    if (self.winTile in p) and (p.index(self.winTile) == 2):
                        return True

        # 宝牌情况处理
        if self.isMagicTile():
            for wn in self.winNodes:
                winTile = wn['winTile']
                patterns = wn['pattern']
                for p in patterns:
                    if len(p) == 2:
                        continue

                    if p[0] == p[1]:
                        continue

                    if (winTile in p) and (p.index(winTile) == 0):
                        return True

                    if (winTile in p) and (p.index(winTile) == 2):
                        return True

        return False

    def calcWin(self):
        """
        鸡西算番规则：
        """
        scoreBase = self.tableConfig.get(MTDefine.WIN_BASE, 1)
        ftlog.debug('MJixiOneResult.calcWin scoreBase:', scoreBase)
        self.results['type'] = MOneResult.KEY_TYPE_NAME_HU

        name = ''
        score = [0 for _ in range(self.playerCount)]
        fanPattern = [[] for _ in range(self.playerCount)]
        winMode = [MOneResult.WIN_MODE_LOSS for _ in range(self.playerCount)]
        # 在和牌时统计自摸，点炮，最大番数
        resultStat = [[] for _ in range(self.playerCount)]

        # 正常和牌
        if not (self.tianHu or self.wuDuiHu):
            isZiMo = (self.lastSeatId == self.winSeatId)
            if isZiMo:
                resultStat[self.winSeatId].append({MOneResult.STAT_ZIMO: 1})
            isJia = self.isJia()
            isBian = self.isBian()
            isDanDiao = self.isDanDiao()
            isQiDui = self.isQiDui()
            isPiao = self.isPiao()
            isQingYiSe = self.isQingYiSe()
            isTeDaJia = self.isTeDaJia()
            isMagic = self.isMagicTile()
            ftlog.debug('MJixiOneResult.calcWin isJia:', isJia
                        , ' isBian:', isBian
                        , ' isDanDiao', isDanDiao
                        , ' isQiDui:', isQiDui
                        , ' isPiao:', isPiao
                        , ' isQingYiSe:', isQingYiSe
                        )

            self.clearWinFanPattern()
            # 计算基本番型(只有单吊 夹胡[3,7边] 七小对)
            name, index = self.calcBaseFan(isJia, isBian, isDanDiao, isQiDui)
            ftlog.debug('MHaerbinOneResult.calcWin BaseFan name:', name, ' index:', index)

            # 自摸番型处理(自摸 摸宝[2番] 杠开 )
            if isZiMo:
                if isMagic:
                    index += self.fanXing[self.MOBAO]['index']
                else:
                    index += self.fanXing[self.ZIMO]['index']
                ftlog.debug('MHaerbinOneResult.calcWin ZiMoFan index:', index)

            # 高级番型处理(清一色 通宝 七对 飘胡 特大夹 宝中宝)
            isBaoZhongBao = False
            isTongBao = False
            if self.magicAfertTing:  # 听牌之后是宝牌 直接和牌
                # 宝中宝 宝夹
                bianMulti = self.tableConfig.get(MTDefine.BIAN_MULTI, 0)
                if isDanDiao or isJia or (isBian and self.isSanQi() and bianMulti):
                    isBaoZhongBao = True
                # 通宝 宝边
                else:
                    isTongBao = True

            if isTongBao:
                nameTongBao = self.fanXing[self.BAOBIAN]['name']
                indexTongBao = self.fanXing[self.BAOBIAN]['index']
                self.addWinFanPattern(nameTongBao, indexTongBao)
                index += self.fanXing[self.BAOBIAN]['index']
                ftlog.debug('MHaerbinOneResult.calcWin MagicAfertTing name:', nameTongBao, ' index:', indexTongBao)

            if isBaoZhongBao:
                nameBaoZhongBao = self.fanXing[self.BAOZHONGBAOJIA]['name']
                indexBaoZhongBao = self.fanXing[self.BAOZHONGBAOJIA]['index']
                self.addWinFanPattern(nameBaoZhongBao, indexBaoZhongBao)
                index += self.fanXing[self.BAOZHONGBAOJIA]['index']
                ftlog.debug('MHaerbinOneResult.calcWin MagicAfertTing name:', nameBaoZhongBao, ' index:',
                            indexBaoZhongBao)

            if isPiao:
                namePiao = self.fanXing[self.PIAOHU]['name']
                indexPiao = self.fanXing[self.PIAOHU]['index']
                self.addWinFanPattern(namePiao, indexPiao)
                index += self.fanXing[self.PIAOHU]['index']
                ftlog.debug('MHaerbinOneResult.calcWin PiaoFan name:', namePiao, ' index:', indexPiao)

            if isTeDaJia:
                nameTeDaJIa = self.fanXing[self.TEDAJIA]['name']
                indexTeDaJia = self.fanXing[self.TEDAJIA]['index']
                self.addWinFanPattern(nameTeDaJIa, indexTeDaJia)
                index += self.fanXing[self.TEDAJIA]['index']
                ftlog.debug('MHaerbinOneResult.calcWin TeDaJiaFan name:', nameTeDaJIa, ' index:', indexTeDaJia)

            if isQingYiSe:
                if isTeDaJia or isQiDui or isPiao or isBaoZhongBao:
                    nameQingYiSe = self.fanXing[self.QINGYISE_1]['name']
                    indexQingYiSe = self.fanXing[self.QINGYISE_1]['index']
                    self.addWinFanPattern(nameQingYiSe, indexQingYiSe)
                    index += self.fanXing[self.QINGYISE_1]['index']
                else:
                    nameQingYiSe = self.fanXing[self.QINGYISE]['name']
                    indexQingYiSe = self.fanXing[self.QINGYISE]['index']
                    self.addWinFanPattern(nameQingYiSe, indexQingYiSe)
                    index += self.fanXing[self.QINGYISE]['index']
                ftlog.debug('MHaerbinOneResult.calcWin QingYiSeFan name:', nameQingYiSe, ' index:', indexQingYiSe)

            if self.bankerSeatId == self.winSeatId:
                index += 1
                ftlog.info('MHaerbinOneResult.calcWin name:', name, ' index:', index, ' type:', type
                           , ' bankerSeatId:', self.bankerSeatId
                           , ' winSeatId:', self.winSeatId)

            # 最大番统计
            resultStat[self.winSeatId].append({MOneResult.STAT_ZUIDAFAN: index})

            scoreIndex = self.tableConfig.get(MTDefine.FAN_LIST, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
            ftlog.info('MHaerbinOneResult.calcWin scoreIndex:', scoreIndex)

            biMenFanConfig = self.tableConfig.get(MTDefine.BI_MEN_FAN, 0)
            # 当前局番型处理
            # 输赢模式 输家番型统计
            for seatId in range(self.playerCount):
                if seatId == self.winSeatId:
                    winModeValue = MOneResult.WIN_MODE_PINGHU
                    # 自摸
                    if self.lastSeatId == self.winSeatId:
                        winModeValue = MOneResult.WIN_MODE_ZIMO
                        if isMagic:
                            self.addWinFanPattern(self.fanXing[self.MOBAO]['name'], self.fanXing[self.MOBAO]['index'])
                    if self.gangKai:
                        winModeValue = MOneResult.WIN_MODE_GANGKAI
                        self.addWinFanPattern(self.fanXing[self.GANGKAI]['name'], self.fanXing[self.GANGKAI]['index'])
                    if self.qiangGang:
                        winModeValue = MOneResult.WIN_MODE_QIANGGANGHU
                        self.addWinFanPattern(self.fanXing[self.QIANGGANG]['name'],
                                              self.fanXing[self.QIANGGANG]['index'])
                    winMode[seatId] = winModeValue
                    fanPattern[self.winSeatId] = self.winFanPattern()
                elif seatId == self.lastSeatId:
                    winModeValue = MOneResult.WIN_MODE_DIANPAO
                    winMode[seatId] = winModeValue
                    resultStat[seatId].append({MOneResult.STAT_DIANPAO: 1})
                    fanPattern[seatId] = []
                    # 点炮包庄
                    if self.tingState[seatId] == 0:
                        winModeValue = MOneResult.WIN_MODE_DIANPAO_BAOZHUANG
                        winMode[seatId] = winModeValue
                    # 闭门
                    if self.menState[seatId] == 1 and biMenFanConfig:
                        looseFanName = self.fanXing[self.BIMEN]['name']
                        looseFanIndex = self.fanXing[self.BIMEN]['index']
                        fanPattern[seatId].append([looseFanName.strip(), str(looseFanIndex) + "番"])

                else:
                    fanPattern[seatId] = []
                    # 闭门
                    if self.menState[seatId] == 1 and biMenFanConfig:
                        looseFanName = self.fanXing[self.BIMEN]['name']
                        looseFanIndex = self.fanXing[self.BIMEN]['index']
                        fanPattern[seatId].append([looseFanName.strip(), str(looseFanIndex) + "番"])

            score = [index for _ in range(self.playerCount)]
            if self.lastSeatId != self.winSeatId:
                score[self.lastSeatId] += 1
                ftlog.info('MHaerbinOneResult.calcWin dianpao score:', score)

            if self.bankerSeatId != self.winSeatId:
                score[self.bankerSeatId] += 1
                ftlog.info('MHaerbinOneResult.calcWin zhuangjia double score:', score
                           , ' bankerSeatId:', self.bankerSeatId
                           , ' winSeatId:', self.winSeatId)

            for seatId in range(len(self.menState)):
                if biMenFanConfig and self.menState[seatId] == 1 and seatId != self.winSeatId:
                    score[seatId] += 1
                    ftlog.info('MHaerbinOneResult.calcWin menqing double score:', score
                               , ' menState:', self.menState)

            winScore = 0
            for seatId in range(len(score)):
                if seatId != self.winSeatId:
                    newIndex = score[seatId]
                    score[seatId] = -scoreIndex[newIndex]
                    winScore += scoreIndex[newIndex]
            score[self.winSeatId] = winScore
            ftlog.info('MHaerbinOneResult.calcWin score before baopei:', score)

            if self.lastSeatId != self.winSeatId:
                if self.tingState[self.lastSeatId] == 0:
                    # 包赔
                    for seatId in range(len(score)):
                        if seatId != self.winSeatId and seatId != self.lastSeatId:
                            s = score[seatId]
                            score[seatId] = 0
                            score[self.lastSeatId] += s
                    ftlog.debug('MHaerbinOneResult.calcWin dianpaobaozhuang score:', score
                                , ' lastSeatId:', self.lastSeatId
                                , ' winSeatId:', self.winSeatId
                                , ' tingState:', self.tingState)
        else:
            if self.tianHu:
                name = self.fanXing[self.TIANHU]['name']
                index = self.fanXing[self.TIANHU]['index']
                self.addWinFanPattern(name, index)
                fanPattern[self.winSeatId] = self.winFanPattern()
                score = [index for _ in range(self.playerCount)]
                scoreIndex = self.tableConfig.get(MTDefine.FAN_LIST, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                ftlog.info('MHaerbinOneResult.calcWin scoreIndex:', scoreIndex)
                winScore = 0
                for seatId in range(len(score)):
                    if seatId != self.winSeatId:
                        newIndex = score[seatId]
                        score[seatId] = -scoreIndex[newIndex]
                        winScore += scoreIndex[newIndex]
                score[self.winSeatId] = winScore
                # fanPattern = [[] for _ in range(self.playerCount)]
                winMode = [MOneResult.WIN_MODE_LOSS for _ in range(self.playerCount)]
                winMode[self.winSeatId] = MOneResult.WIN_MODE_TIANHU
                resultStat[self.winSeatId].append({MOneResult.STAT_ZUIDAFAN: index})

            elif self.wuDuiHu:
                name = self.fanXing[self.WUDUIHU]['name']
                index = self.fanXing[self.WUDUIHU]['index']
                self.addWinFanPattern(name, index)
                fanPattern[self.winSeatId] = self.winFanPattern()
                score = [10 for _ in range(self.playerCount)]
                winScore = 0
                for seatId in range(len(score)):
                    if seatId != self.winSeatId:
                        loseScore = score[seatId]
                        score[seatId] = -loseScore
                        winScore += loseScore
                score[self.winSeatId] = winScore
                # fanPattern = [[] for _ in range(self.playerCount)]
                winMode = [MOneResult.WIN_MODE_LOSS for _ in range(self.playerCount)]
                winMode[self.winSeatId] = MOneResult.WIN_MODE_WUDUIHU

        # 最高128分封顶
        for seatId in range(len(score)):
            if seatId != self.winSeatId:
                if abs(score[seatId]) > self.MAX_SCORE_LIMIT:
                    ftlog.debug('MHaerbinOneResult.calcWin limit max score :', score[seatId]
                                , ' seatId:', seatId)
                    score[self.winSeatId] = score[self.winSeatId] - (abs(score[seatId]) - self.MAX_SCORE_LIMIT)
                    score[seatId] = -self.MAX_SCORE_LIMIT

        # 兑奖
        awardInfos = []
        awardTiles = self.awardTiles
        if len(awardTiles) == 0:
            ftlog.debug('MHaerbinOneResult.calcWin award tile is zero')
        else:
            awardScore = 0
            for awardTile in awardTiles:
                tileValue = MTile.getValue(awardTile)
                realScore = 0
                if tileValue == 1 or awardTile == MTile.TILE_HONG_ZHONG:
                    realScore = 10
                    awardScore += realScore
                else:
                    realScore = tileValue
                    awardScore += realScore
                awardInfo = {'awardTile': awardTile, 'awardScore': realScore}
                awardInfos.append(awardInfo)

            for seatId in range(len(score)):
                if seatId != self.winSeatId:
                    score[seatId] -= awardScore
                    score[self.winSeatId] += awardScore

        self.results[self.KEY_TYPE] = '和牌'
        self.results[self.KEY_NAME] = name
        ftlog.debug('MHaerbinOneResult.calcWin result score:', score)
        self.results[self.KEY_SCORE] = score
        ftlog.debug('MHaerbinOneResult.calcWin result winMode:', winMode)
        self.results[self.KEY_WIN_MODE] = winMode
        self.results[self.KEY_STAT] = resultStat
        ftlog.debug('MHaerbinOneResult.calcWin result fanPattern:', fanPattern)
        self.results[self.KEY_FAN_PATTERN] = fanPattern
        self.results[self.KEY_AWARD_INFO] = awardInfos

    def calcBaseFan(self, isJia, isBian, isDanDiao, isQiDui):
        name = ''
        index = 0

        if isQiDui:
            name = self.fanXing[self.QIXIAODUI]['name']
            index = self.fanXing[self.QIXIAODUI]['index']
            self.addWinFanPattern(name, index)
            return name, index

        if isDanDiao:
            name = self.fanXing[self.DANDIAO]['name']
            index = self.fanXing[self.DANDIAO]['index']
            self.addWinFanPattern(name, index)
            return name, index

        if isJia:
            name = self.fanXing[self.JIAHU]['name']
            index = self.fanXing[self.JIAHU]['index']
            self.addWinFanPattern(name, index)
            return name, index

        # 三七边算夹胡
        bianMulti = self.tableConfig.get(MTDefine.BIAN_MULTI, 0)
        if isBian and self.isSanQi() and bianMulti:
            name = self.fanXing[self.JIAHU]['name']
            index = self.fanXing[self.JIAHU]['index']
            self.addWinFanPattern(name, index)
            return name, index

        print 'name: ', name, ' index: ', index
        return name, index

    def calcScore(self):
        """计算输赢数值"""
        # 序列化，以备后续的查找核实
        self.serialize()

        if self.resultType == self.RESULT_GANG:
            self.calcGang()
        elif self.resultType == self.RESULT_WIN:
            self.calcWin()
        elif self.resultType == self.RESULT_FLOW:
            self.results[self.KEY_TYPE] = ''
            self.results[self.KEY_NAME] = '流局'
            score = [0 for _ in range(self.playerCount)]
            self.results[self.KEY_SCORE] = score
            winMode = [MOneResult.WIN_MODE_LOSS for _ in range(self.playerCount)]
            self.results[self.KEY_WIN_MODE] = winMode
            resultStat = [[] for _ in range(self.playerCount)]
            self.results[self.KEY_STAT] = resultStat
            fanPattern = [[] for _ in range(self.playerCount)]
            self.results[self.KEY_FAN_PATTERN] = fanPattern


if __name__ == "__main__":
    result = MJixiOneResult()
    result.setTableConfig({})
    result.calcDianPaoFan(True, False, True, False)
