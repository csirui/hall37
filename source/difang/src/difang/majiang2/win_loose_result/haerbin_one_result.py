# -*- coding=utf-8
'''
Created on 2016年9月23日

一条和牌结果

@author: zhaol
'''
from difang.majiang2.table.table_config_define import MTDefine
from difang.majiang2.tile.tile import MTile
from difang.majiang2.win_loose_result.one_result import MOneResult
from freetime.util import log as ftlog


class MHaerbinOneResult(MOneResult):
    ZIMO = 'ziMo'
    GANGKAI = 'gangKai'
    QIANGGANG = 'qiangGang'
    HONGZHONGBAO = 'hongZhongBao'
    BAOBIAN = 'baoBian'
    GUADAFENG = 'guaDaFeng'
    BAOZHONGBAOJIA = 'baoZhongBaoJia'
    BAOZHONGBAODAFENG = 'baoZhongBaoDaFeng'
    JIAHU = 'jiaHu'
    BIANHU = 'bianZhang'
    MOBAO = 'moBao'
    BIANJIASHUANG = 'bianJiaShuang'
    DANDIAO = 'danDiao'
    # 输家番型
    DIANPAO = 'dianPao'
    DIANPAOBAOZHUANG = 'dianPaoBaoZhuang'
    BIMEN = 'biMen'
    BAOPAO = 'baoPao'

    def __init__(self):
        super(MHaerbinOneResult, self).__init__()
        self.__fan_xing = {
            self.ZIMO: {"name": "自摸 ", "index": 1},
            self.GANGKAI: {"name": "杠上开花 ", "index": 1},
            self.QIANGGANG: {"name": "抢杠胡 ", "index": 1},
            self.HONGZHONGBAO: {"name": "红中宝 ", "index": 2},
            self.BAOBIAN: {"name": "宝边 ", "index": 3},
            self.GUADAFENG: {"name": "刮大风 ", "index": 2},
            self.BAOZHONGBAOJIA: {"name": "宝夹 ", "index": 4},
            self.BAOZHONGBAODAFENG: {"name": "宝中宝 ", "index": 4},
            self.JIAHU: {"name": "夹胡 ", "index": 1},
            self.BIANHU: {"name": "边胡 ", "index": 1},
            self.MOBAO: {"name": "摸宝 ", "index": 2},
            self.DANDIAO: {"name": "单吊 ", "index": 1},
            # 输家番型
            self.DIANPAO: {"name": "点炮 ", "index": 1},  # winMode展示
            self.DIANPAOBAOZHUANG: {"name": "包庄 ", "index": 1},  # winMode展示
            self.BIMEN: {"name": "闭门 ", "index": 1},
            self.BAOPAO: {"name": "宝炮 ", "index": 1},
        }

    @property
    def fanXing(self):
        return self.__fan_xing

    def isWinTile(self):
        """获胜牌在winNodes中，而且是宝牌"""
        ftlog.debug('MHaerbinOneResult.isWinTile winTile:', self.winTile
                    , ' winNodes:', self.winNodes)

        for wn in self.winNodes:
            if wn['winTile'] == self.winTile:
                return True

        return False

    def isMagicTile(self):
        """是不是宝牌"""
        magics = self.tableTileMgr.getMagicTiles(True)
        ftlog.debug('MHaerbinOneResult.isMagicTile winTile:', self.winTile
                    , ' magicTiles:', magics)

        return self.winTile in magics

    def getMagicTile(self):
        magics = self.tableTileMgr.getMagicTiles(True)
        if len(magics) == 0:
            return None
        return magics[0]

    # 胡的就是宝牌
    def isHuMagicTile(self):
        magics = self.tableTileMgr.getMagicTiles(True)
        for wn in self.winNodes:
            if wn['winTile'] in magics:
                return True
        return False

    def isHongZhong(self):
        return self.winTile == MTile.TILE_HONG_ZHONG

    def isDanDiao(self):
        if not self.isWinTile():
            return False

        for wn in self.winNodes:
            if wn['winTile'] == self.winTile:
                patterns = wn['pattern']
                ftlog.debug('MHaerbinOneResult.isDanDiao winTile:', self.winTile, ' winPatterns:', patterns)
                for p in patterns:
                    if len(p) != 2:
                        continue

                    if (self.winTile in p) and p[0] == p[1]:
                        return True

        # 宝牌情况时判断单吊
        hongZongBaoConfig = self.tableConfig.get(MTDefine.HONG_ZHONG_BAO, 0)
        if self.isMagicTile() or (self.isHongZhong() and hongZongBaoConfig) or self.daFeng:
            for wn in self.winNodes:
                winTile = wn['winTile']
                patterns = wn['pattern']
                ftlog.debug('MHaerbinOneResult.isDanDiao winTile:', self.winTile, ' winPatterns:', patterns)
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
                ftlog.debug('MHaerbinOneResult.isJia winTile:', self.winTile, ' winPatterns:', patterns)
                for p in patterns:
                    if len(p) == 2:
                        continue

                    if p[0] == p[1]:
                        continue

                    if (self.winTile in p) and (p.index(self.winTile)) == 1:
                        return True

        # 宝牌和红中宝刮大风的情况处理(用真实的胡牌来判断夹)
        hongZongBaoConfig = self.tableConfig.get(MTDefine.HONG_ZHONG_BAO, 0)
        if self.isMagicTile() or (self.isHongZhong() and hongZongBaoConfig) or self.daFeng:
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

    def isSanQi(self, winTile=None):
        if winTile == None:
            winTile = self.winTile
        if MTile.getValue(winTile) == 3 or MTile.getValue(winTile) == 7:
            return True
        return False

    def isBian(self):
        """是否夹牌"""
        if not self.isWinTile():
            return False

        for wn in self.winNodes:
            if wn['winTile'] == self.winTile:
                patterns = wn['pattern']
                ftlog.debug('MHaerbinOneResult.isBian winTile:', self.winTile, ' winPatterns:', patterns)
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
        哈麻算番规则：
        1）合并一番
        自摸，特殊情况下的自摸可以有杠开/红中宝两种叫法
            1.1杠开
            1.2红中宝 自己摸到红中
            1.4刮大风 上听后摸到自己的碰牌或刻牌且不是宝牌，宝牌算宝中宝
            1.5宝中宝1 3番 宝牌 夹牌
            1.6宝中宝2 3番 刮大风+宝牌
        2）自摸点炮都算
        2.1夹胡
        2.2三七边
        2.3摸宝
        1.3宝边，2番，自摸的要胡的牌刚好是宝牌
        2.4边夹双 2倍数
        
        """
        scoreBase = self.tableConfig.get(MTDefine.WIN_BASE, 1)
        ftlog.debug('MHaerbinOneResult.calcWin scoreBase:', scoreBase)
        self.results['type'] = MOneResult.KEY_TYPE_NAME_HU

        # 在和牌时统计自摸，点炮，最大番数
        resultStat = [[] for _ in range(self.playerCount)]

        isZiMo = (self.lastSeatId == self.winSeatId)
        if isZiMo:
            resultStat[self.lastSeatId].append({MOneResult.STAT_ZIMO: 1})
        isJia = self.isJia()
        isBian = self.isBian()
        isDanDiao = self.isDanDiao()
        isMagic = self.isMagicTile()
        ftlog.debug('MHaerbinOneResult.calcWin isJia:', isJia
                    , ' isBian:', isBian
                    , ' isDanDiao', isDanDiao
                    , ' isMagic:', isMagic)

        self.clearWinFanPattern()
        # 计算基本番型(只有单吊 夹胡 三七边)
        name, index = self.calcDianPaoFan(isJia, isBian, isDanDiao)
        ftlog.info('MHaerbinOneResult.calcWin name:', name, ' index:', index, ' type:', type)

        # 计算自摸高级番型 都和自摸有关(不包含自摸 杠开 抢杠胡 摸宝 红中宝)
        if isZiMo:
            name2, index2 = self.calcZiMoAdvFan(isZiMo, self.daFeng, self.baoZhongBao, isMagic, isJia, isBian)
            ftlog.info('MHaerbinOneResult.calcWin name2:', name2, ' index2:', index2, ' type:', type)
            # 只是自摸 没有高级番型
            if name2 == self.fanXing[self.ZIMO]['name']:
                # 在基础番型上增加自摸倍数
                hongZongBaoConfig = self.tableConfig.get(MTDefine.HONG_ZHONG_BAO, 0)
                if isMagic:
                    index = index + self.fanXing[self.MOBAO]['index']
                elif self.isHongZhong() and hongZongBaoConfig:
                    index = index + self.fanXing[self.HONGZHONGBAO]['index']
                else:
                    index = index + 1
            # 自摸相关的特殊番型 直接覆盖基本番型
            else:
                name = name2
                index = index2
                self.clearWinFanPattern()
                self.addWinFanPattern(name, index)

        ftlog.info('MHaerbinOneResult.calcWin name:', name, ' index:', index, ' type:', type)

        if self.bankerSeatId == self.winSeatId:
            ftlog.info('MHaerbinOneResult.calcWin name:', name, ' index:', index, ' type:', type
                       , ' bankerSeatId:', self.bankerSeatId
                       , ' winSeatId:', self.winSeatId)
            index += 1

        # 最大番统计
        resultStat[self.winSeatId].append({MOneResult.STAT_ZUIDAFAN: index})

        scoreIndex = self.tableConfig.get(MTDefine.FAN_LIST, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        ftlog.info('MHaerbinOneResult.calcWin scoreIndex:', scoreIndex)

        # 当前局番型处理
        fanPattern = [[] for _ in range(self.playerCount)]
        winMode = [MOneResult.WIN_MODE_LOSS for _ in range(self.playerCount)]
        # 输赢模式 输家番型统计
        for seatId in range(self.playerCount):
            if seatId == self.winSeatId:
                winModeValue = MOneResult.WIN_MODE_PINGHU
                # 自摸
                if self.lastSeatId == self.winSeatId:
                    winModeValue = MOneResult.WIN_MODE_ZIMO
                    # 红中宝
                    hongZongBaoConfig = self.tableConfig.get(MTDefine.HONG_ZHONG_BAO, 0)
                    if self.isHongZhong() and hongZongBaoConfig:
                        self.addWinFanPattern(self.fanXing[self.HONGZHONGBAO]['name'],
                                              self.fanXing[self.HONGZHONGBAO]['index'])

                    if isMagic:
                        self.addWinFanPattern(self.fanXing[self.MOBAO]['name'], self.fanXing[self.MOBAO]['index'])
                if self.gangKai:
                    winModeValue = MOneResult.WIN_MODE_GANGKAI
                    self.addWinFanPattern(self.fanXing[self.GANGKAI]['name'], self.fanXing[self.GANGKAI]['index'])
                if self.qiangGang:
                    winModeValue = MOneResult.WIN_MODE_QIANGGANGHU
                    self.addWinFanPattern(self.fanXing[self.QIANGGANG]['name'], self.fanXing[self.QIANGGANG]['index'])
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
                if self.menState[seatId] == 1:
                    looseFanName = self.fanXing[self.BIMEN]['name']
                    looseFanIndex = self.fanXing[self.BIMEN]['index']
                    fanPattern[seatId].append([looseFanName.strip(), str(looseFanIndex) + "番"])

            else:
                fanPattern[seatId] = []
                # 闭门
                if self.menState[seatId] == 1:
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
            if self.menState[seatId] == 1 and seatId != self.winSeatId:
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
                ftlog.info('MHaerbinOneResult.calcWin dianpaobaozhuang score:', score
                           , ' lastSeatId:', self.lastSeatId
                           , ' winSeatId:', self.winSeatId
                           , ' tingState:', self.tingState)

        self.results[self.KEY_TYPE] = '和牌'
        self.results[self.KEY_NAME] = name
        ftlog.debug('MHaerbinOneResult.calcWin result score:', score)
        self.results[self.KEY_SCORE] = score
        ftlog.debug('MHaerbinOneResult.calcWin result winMode:', winMode)
        self.results[self.KEY_WIN_MODE] = winMode
        self.results[self.KEY_STAT] = resultStat
        ftlog.debug('MHaerbinOneResult.calcWin result fanPattern:', fanPattern)
        self.results[self.KEY_FAN_PATTERN] = fanPattern

    def calcZiMoAdvFan(self, isZiMo, isDaFeng, isBaoZhongBao, isMagic, isJia, isBian):
        if not isZiMo:
            return '', 0

        bianMulti = self.tableConfig.get(MTDefine.BIAN_MULTI, 0)
        # 红中宝情况 如果本来胡的是宝夹
        hongZongBaoConfig = self.tableConfig.get(MTDefine.HONG_ZHONG_BAO, 0)
        if self.isHongZhong() and hongZongBaoConfig:
            if self.isHuMagicTile() and (isJia or (isBian and bianMulti and self.isSanQi(self.getMagicTile()))):
                return self.fanXing[self.BAOZHONGBAOJIA]['name'], self.fanXing[self.BAOZHONGBAOJIA]['index']

                # 哈尔滨宝中宝 听牌之后手里刚好有三张宝牌 直接和牌
        if isBaoZhongBao:
            return self.fanXing[self.BAOZHONGBAODAFENG]['name'], self.fanXing[self.BAOZHONGBAODAFENG]['index']

        if isDaFeng and isMagic:
            return self.fanXing[self.BAOZHONGBAODAFENG]['name'], self.fanXing[self.BAOZHONGBAODAFENG]['index']

        if isMagic and isBian:
            if bianMulti and self.isSanQi():
                return self.fanXing[self.BAOZHONGBAOJIA]['name'], self.fanXing[self.BAOZHONGBAOJIA]['index']
            else:
                return self.fanXing[self.BAOBIAN]['name'], self.fanXing[self.BAOBIAN]['index']

        if isMagic and isJia:
            return self.fanXing[self.BAOZHONGBAOJIA]['name'], self.fanXing[self.BAOZHONGBAOJIA]['index']

        if isDaFeng:
            # 大风时判断宝夹
            if self.isHuMagicTile() and (isJia or (isBian and bianMulti and self.isSanQi(self.getMagicTile()))):
                return self.fanXing[self.BAOZHONGBAOJIA]['name'], self.fanXing[self.BAOZHONGBAOJIA]['index']
            else:
                return self.fanXing[self.GUADAFENG]['name'], self.fanXing[self.GUADAFENG]['index']

        return self.fanXing[self.ZIMO]['name'], self.fanXing[self.ZIMO]['index']

    def calcDianPaoFan(self, isJia, isBian, isDanDiao):
        name = ''
        index = 0

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
        if isBian and bianMulti and self.isSanQi():
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
    result = MHaerbinOneResult()
    result.setTableConfig({})
    result.calcDianPaoFan(True, False, True, False)
