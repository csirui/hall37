# -*- coding=utf-8
'''
Created on 2016年9月23日

一条和牌结果

@author: dongwei
'''
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.player.player import MPlayerTileGang
from difang.majiang2.table.table_config_define import MTDefine
from difang.majiang2.table_tile.table_tile_factory import MTableTileFactory
from difang.majiang2.tile.tile import MTile
from difang.majiang2.win_loose_result.one_result import MOneResult
from difang.majiang2.win_rule.win_rule import MWinRule
from difang.majiang2.win_rule.win_rule_factory import MWinRuleFactory
from freetime.util import log as ftlog


class MKawuxingOneResult(MOneResult):
    QINGYISE = 'qingyise'
    DASANYUAN = 'dasanyuan'
    XIAOSANYUAN = 'xiaosanyuan'
    QIDUI = 'qidui'
    QIDUIHAO = 'qiduihao'
    QIDUICHAOHAO = 'qiduichaohao'
    QIDUICHAOCHAOHAO = 'qiduichaochaohao'
    PENGPENGHU = 'pengpenghu'
    KAWUXING = 'kawuxing'
    HAIDILAO = 'haidilao'
    HAIDIPAO = 'haidipao'
    SHOUZHUAYI = 'shouzhuayi'
    MINGSIGUI = 'mingsigui'
    ANSIGUI = 'ansigui'
    GANGSHANGPAO = 'gangshangpao'
    MINGHU = 'minghu'
    MINGSHU = 'mingshu'
    GANGKAI = 'gangkai'
    QIANGGANG = 'qiangGang'
    PAO = 'pao'
    QIA = 'qia'
    MO = 'mo'
    BA = 'ba'
    KAN = 'kan'
    MAIMA = 'maima'
    YIPAOSHUANGXIANG = 'yipaoshuangxiang'

    def __init__(self):
        super(MKawuxingOneResult, self).__init__()
        self.__fan_xing = {
            # 赢的番型
            self.QINGYISE: {"name": "清一色", "index": 2},
            self.DASANYUAN: {"name": "大三元", "index": 3},
            self.XIAOSANYUAN: {"name": "小三元", "index": 2},
            self.QIDUI: {"name": "七对", "index": 2},
            self.QIDUIHAO: {"name": "豪华七对", "index": 3},
            self.QIDUICHAOHAO: {"name": "超豪华七对", "index": 5},
            self.QIDUICHAOCHAOHAO: {"name": "超超豪华七对", "index": 7},
            self.PENGPENGHU: {"name": "碰碰胡", "index": 1},
            self.KAWUXING: {"name": "卡五星", "index": 1},
            self.HAIDILAO: {"name": "海底捞", "index": 1},
            self.SHOUZHUAYI: {"name": "手抓一", "index": 2},
            self.MINGSIGUI: {"name": "明四归", "index": 1},
            self.ANSIGUI: {"name": "暗四归", "index": 2},
            self.MINGHU: {"name": "明牌胡", "index": 1},
            self.GANGKAI: {"name": "杠上开花", "index": 1},
            self.QIANGGANG: {"name": "抢杠胡", "index": 1},
            self.PAO: {"name": "跑", "addScore": 1},
            self.QIA: {"name": "恰", "multiplyScore": 1},
            self.MO: {"name": "摸", "addScore": 1},
            self.BA: {"name": "八", "multiplyScore": 1},
            self.KAN: {"name": "数坎", "multiplyScore": 1},
            self.MAIMA: {"name": "买马", "multiplyScore": 1},
            # 输（放炮，只对放炮的人）的番型
            self.HAIDIPAO: {"name": "海底炮", "index": 1},
            self.GANGSHANGPAO: {"name": "杠上炮", "index": 1},
            self.YIPAOSHUANGXIANG: {"name": "一炮双响", "index": 1},
            # 输（只对做过特定操作的人）的番型
            self.MINGSHU: {"name": "明牌输", "index": 1}
        }

    @property
    def fanXing(self):
        return self.__fan_xing

    def calcScore(self):
        """计算输赢数值"""
        # 序列化，以备后续的查找核实
        self.serialize()

        if self.resultType == self.RESULT_GANG:
            self.calcGang()
        elif self.resultType == self.RESULT_WIN:
            # 放在这里补充环境数据，要么不方便单元测试
            self.__player_all_tiles = [[] for _ in range(self.playerCount)]
            self.__player_all_tiles_arr = [[] for _ in range(self.playerCount)]
            self.__player_hand_tiles_with_hu = [[] for _ in range(self.playerCount)]
            self.__player_ting_liang = [False for _ in range(self.playerCount)]

            for player in self.tableTileMgr.players:
                # 按手牌格式的数组
                self.__player_all_tiles[player.curSeatId] = player.copyTiles()
                # 合到一个数组中
                self.__player_all_tiles_arr[player.curSeatId].extend(
                    MHand.copyAllTilesToList(self.__player_all_tiles[player.curSeatId]))
                # 只获取手牌，手牌不包含所胡的牌，加上胡的牌
                self.__player_hand_tiles_with_hu[player.curSeatId] = player.copyHandTiles()
                if player.curSeatId == self.winSeatId:
                    self.__player_hand_tiles_with_hu[player.curSeatId].append(self.winTile)
                # 听亮的状态
                self.__player_ting_liang[player.curSeatId] = player.isTingLiang()

            ftlog.info('MKawuxingOneResult.calcScore __player_all_tiles=', self.__player_all_tiles)
            ftlog.info('MKawuxingOneResult.calcScore __player_all_tiles_arr=', self.__player_all_tiles_arr)
            ftlog.info('MKawuxingOneResult.calcScore __player_hand_tiles_with_hu=', self.__player_hand_tiles_with_hu)
            ftlog.info('MKawuxingOneResult.calcScore __player_ting_liang=', self.__player_ting_liang)

            if self.winSeatId == self.lastSeatId:
                # 自摸
                winMode = MWinRule.WIN_BY_MYSELF
            else:
                winMode = MWinRule.WIN_BY_OTHERS

            tiles = {MHand.TYPE_HAND: self.__player_hand_tiles_with_hu[self.winSeatId]}
            winResult, winPattern = MWinRuleFactory.getWinRule(MPlayMode.KAWUXING).isHu(tiles,
                                                                                        self.winTile,
                                                                                        self.tableTileMgr.players[
                                                                                            self.winSeatId].isTing(),
                                                                                        winMode)
            # 此处有坑，winPattern只有一种牌型，似乎优先一样的牌，比如：[14,14,14,15,15,16,16,16,19,19,19,20,20]，最后抓15
            # 如果卡五星比碰碰胡番数高，此处应该算卡五星，所以isHu应该返回所有可能的胡的牌型，结算时计算最优的番型
            # 此处预留isHu的修改
            # 此处不用winNodes主要原因是，卡五星可以不听/亮牌，直接胡
            self.__win_patterns = [winPattern]
            ftlog.info('MKawuxingOneResult.calcScore __win_patterns=', self.__win_patterns)

            self.calcWin()
        elif self.resultType == self.RESULT_FLOW:
            self.calcFlow()

    def calcGang(self):
        """计算杠的输赢"""
        # 杠分明杠、暗杠，明杠又分蓄杠（碰+最后一张自摸）和放杠（最后一张杠）
        # 暗杠整体2倍，蓄杠整体1倍，放杠出牌人2倍
        resultStat = [[] for _ in range(self.playerCount)]

        self.results[self.KEY_TYPE] = MOneResult.KEY_TYPE_NAME_GANG
        base = self.tableConfig.get(MTDefine.GANG_BASE, 1)
        ftlog.debug('MKawuxingOneResult.calcGang GANG_BASE:', base)
        self.results[self.KEY_FAN_PATTERN] = [[] for _ in range(self.playerCount)]
        if self.style == MPlayerTileGang.AN_GANG:
            self.results[self.KEY_NAME] = "暗杠"
            self.results[self.KEY_FAN_PATTERN][self.winSeatId] = [["暗杠", "2番"]]
            resultStat[self.winSeatId].append({MOneResult.STAT_ANGANG: 1})
            base *= 2
        else:
            if self.lastSeatId != self.winSeatId:
                self.results[self.KEY_NAME] = "明杠"
                self.results[self.KEY_FAN_PATTERN][self.lastSeatId] = [["放杠", "2番"]]
                self.results[self.KEY_FAN_PATTERN][self.winSeatId] = [["明杠", "2番"]]
                base *= 2
            else:
                # 这种情况一定是碰牌后，自摸杠牌
                # 卡五星当中，碰牌后自摸，称为蓄杠（其他地方还叫明杠）
                self.results[self.KEY_NAME] = "蓄杠"
                self.results[self.KEY_FAN_PATTERN][self.winSeatId] = [["蓄杠", "1番"]]

            resultStat[self.winSeatId].append({MOneResult.STAT_MINGGANG: 1})

        # 放杠，放杠一定是明杠
        if self.lastSeatId != self.winSeatId:
            # 明杠, 只有放杠和明杠两家改分
            scores = [0 for _ in range(self.playerCount)]
            scores[self.lastSeatId] = -base
            scores[self.winSeatId] = base
        else:
            # 暗杠+蓄杠, 所有输家扣分
            scores = [-base for _ in range(self.playerCount)]
            scores[self.winSeatId] = (self.playerCount - 1) * base

        self.results[self.KEY_SCORE] = scores
        self.results[self.KEY_STAT] = resultStat

    def calcWin(self):
        """卡五星算番规则"""

        winnerResult = self.getWinnerResults()

        maxFan = self.tableConfig.get(MTDefine.MAX_FAN, 0)
        score = [0 for _ in range(self.playerCount)]
        if self.lastSeatId != self.winSeatId:
            # 放炮和牌
            finalResult = []
            finalResult.extend(winnerResult)
            finalResult.extend(self.getPaoResults())
            finalResult.extend(self.getLooserResults(self.lastSeatId))
            winScore = self.getScoreByResults(finalResult, maxFan)
            score[self.lastSeatId] = -winScore
            score[self.winSeatId] = winScore
        else:
            # 自摸胡牌
            winScore = 0
            for seatId in range(len(score)):
                finalResult = []
                if seatId != self.winSeatId:
                    finalResult.extend(winnerResult)
                    finalResult.extend(self.getLooserResults(seatId))
                    tableScore = self.getScoreByResults(finalResult, maxFan)
                    score[seatId] = -tableScore
                    winScore += tableScore
            score[self.winSeatId] = winScore
        ftlog.info('MKawuxingOneResult.calcWin score:', score)

        self.results[self.KEY_SCORE] = score
        # 只有一种KEY_NAME不合理，名称的优先级根据需求再加
        self.results[self.KEY_NAME] = MOneResult.KEY_TYPE_NAME_HU
        self.results[self.KEY_TYPE] = MOneResult.KEY_TYPE_NAME_HU

        self.results[self.KEY_FAN_PATTERN] = [[] for _ in range(self.playerCount)]
        self.results[self.KEY_FAN_PATTERN][self.winSeatId] = self.getFanPatternListByResults(winnerResult)
        # 目前从前端代码上看，winMode只能区分：平胡（非自摸和牌），自摸，点炮
        self.results[self.KEY_WIN_MODE] = [MOneResult.WIN_MODE_LOSS for _ in range(self.playerCount)]
        self.results[self.KEY_STAT] = [[] for _ in range(self.playerCount)]
        if self.winSeatId == self.lastSeatId:
            # 自摸
            self.results[self.KEY_WIN_MODE][self.winSeatId] = MOneResult.WIN_MODE_ZIMO
            # 自摸者自摸+1
            self.results[self.KEY_STAT][self.winSeatId].append({MOneResult.STAT_ZIMO: 1})
        else:
            # 点炮，赢的人平胡
            self.results[self.KEY_WIN_MODE][self.winSeatId] = MOneResult.WIN_MODE_PINGHU
            # 点炮，放跑者标为点炮
            self.results[self.KEY_WIN_MODE][self.lastSeatId] = MOneResult.WIN_MODE_DIANPAO
            # 点炮,点炮者点炮+1
            self.results[self.KEY_STAT][self.lastSeatId].append({MOneResult.STAT_DIANPAO: 1})
        # 最大番,当前的赢家番数,如果超过封顶,也显示原始番数
        self.results[self.KEY_STAT][self.winSeatId].append(
            {MOneResult.STAT_ZUIDAFAN: self.getFanByResults(winnerResult)})
        ftlog.debug('MYunnanOneResult calcScore:KEY_SCORE:', self.results[self.KEY_SCORE])
        ftlog.debug('MYunnanOneResult calcScore:KEY_NAME:', self.results[self.KEY_NAME])
        ftlog.debug('MYunnanOneResult calcScore:KEY_TYPE:', self.results[self.KEY_TYPE])
        ftlog.debug('MYunnanOneResult calcScore:KEY_WIN_MODE:', self.results[self.KEY_WIN_MODE])
        ftlog.debug('MYunnanOneResult calcScore:KEY_FAN_PATTERN:', self.results[self.KEY_FAN_PATTERN])
        ftlog.debug('MYunnanOneResult calcScore:KEY_STAT:', self.results[self.KEY_STAT])

    def calcFlow(self):
        """卡五星计算流局"""
        self.results[self.KEY_TYPE] = MOneResult.KEY_TYPE_NAME_FLOW
        self.results[self.KEY_NAME] = MOneResult.KEY_TYPE_NAME_FLOW
        score = [0 for _ in range(self.playerCount)]
        self.results[self.KEY_SCORE] = score
        winMode = [MOneResult.WIN_MODE_LOSS for _ in range(self.playerCount)]
        self.results[self.KEY_WIN_MODE] = winMode
        resultStat = [[] for _ in range(self.playerCount)]
        self.results[self.KEY_STAT] = resultStat
        fanPattern = [[] for _ in range(self.playerCount)]
        self.results[self.KEY_FAN_PATTERN] = fanPattern

    def getWinnerResults(self):
        """和牌时，计算胜者的牌对整个牌桌的分数影响"""
        winnerResults = []
        # 不需要根据和牌牌型计算的番型，先计算

        """清一色"""
        if self.isQingyise():
            winnerResults.append(self.processFanXingResult(self.QINGYISE))
        """大三元"""
        if self.isDasanyuan():
            winnerResults.append(self.processFanXingResult(self.DASANYUAN))
        """小三元"""
        if self.isXiaosanyuan():
            winnerResults.append(self.processFanXingResult(self.XIAOSANYUAN))
        """海底捞"""
        if self.isHaidilao():
            winnerResults.append(self.processFanXingResult(self.HAIDILAO))
        """手抓一"""
        if self.isShouzhuayi():
            winnerResults.append(self.processFanXingResult(self.SHOUZHUAYI))
        """明四归"""
        if self.isMingsigui():
            winnerResults.append(self.processFanXingResult(self.MINGSIGUI))
        """暗四归"""
        if self.isAnsigui():
            winnerResults.append(self.processFanXingResult(self.ANSIGUI))
        """明牌胡"""
        if self.isMinghu():
            winnerResults.append(self.processFanXingResult(self.MINGHU))
        """杠开"""
        if self.gangKai:
            winnerResults.append(self.processFanXingResult(self.GANGKAI))
        """抢杠胡"""
        if self.qiangGang:
            winnerResults.append(self.processFanXingResult(self.QIANGGANG))
        """跑恰摸八，跑"""
        if self.isPaoqiaomobaPao():
            winnerResults.append(self.processFanXingResult(self.PAO))
        """跑恰摸八，摸"""
        if self.isPaoqiaomobaMo():
            winnerResults.append(self.processFanXingResult(self.MO))
        """跑恰摸八，算恰"""
        qiaCount = self.getPaoqiaomobaQiaCount()
        if qiaCount:
            winnerResults.append(self.processFanXingResult(self.QIA, qiaCount))
        """跑恰摸八，算八"""
        baCount = self.getPaoqiaomobaBaCount()
        if baCount:
            winnerResults.append(self.processFanXingResult(self.BA, baCount))
        """数坎"""
        kanCount = self.getKanCount()
        if kanCount:
            winnerResults.append(self.processFanXingResult(self.KAN, kanCount))
        """买马"""
        maScore = self.getMaScore()
        if maScore:
            winnerResults.append(self.processFanXingResult(self.MAIMA, maScore))

        # 个别番型和和牌牌型有关，算分时选取分数最大的情况
        winnerResultsByPattern = []
        maxPatternScore = 0
        bestWinnerResultsByPattern = []

        for pattern in self.__win_patterns:
            ftlog.info('MKawuxingOneResult.getWinnerResults win_pattern=', pattern)

            # pattern内，全部是手牌(包含最后一张牌)
            eachWinnerResultsByPattern = []
            """七对"""
            if self.isQidui(pattern):
                eachWinnerResultsByPattern.append(self.processFanXingResult(self.QIDUI))
            """豪华七对"""
            if self.isQiduiHao(pattern):
                eachWinnerResultsByPattern.append(self.processFanXingResult(self.QIDUIHAO))
            """超豪华七对"""
            if self.isQiduiChaoHao(pattern):
                eachWinnerResultsByPattern.append(self.processFanXingResult(self.QIDUICHAOHAO))
            """超超豪华七对"""
            if self.isQiduiChaoChaoHao(pattern):
                eachWinnerResultsByPattern.append(self.processFanXingResult(self.QIDUICHAOCHAOHAO))
            """碰碰胡"""
            if self.isPengpenghu(pattern):
                eachWinnerResultsByPattern.append(self.processFanXingResult(self.PENGPENGHU))
            """卡五星"""
            if self.isKawuxing(pattern):
                eachWinnerResultsByPattern.append(self.processFanXingResult(self.KAWUXING))
            ftlog.info('MKawuxingOneResult.getWinnerResults eachWinnerResultsByPattern=', eachWinnerResultsByPattern)

            # 计算当前牌型的赢牌奖励分数，选取最大值的牌型
            calceachWinnerResultsByPattern = []
            calceachWinnerResultsByPattern.extend(winnerResults)
            calceachWinnerResultsByPattern.extend(eachWinnerResultsByPattern)
            tempScore = self.getScoreByResults(calceachWinnerResultsByPattern)
            if tempScore > maxPatternScore:
                # 分数相同就不管了
                maxPatternScore = tempScore
                bestWinnerResultsByPattern = eachWinnerResultsByPattern

        winnerResults.extend(bestWinnerResultsByPattern)
        ftlog.info('MKawuxingOneResult.getWinnerResults winnerResults=', winnerResults)
        return winnerResults

    def getLooserResults(self, seatId):
        """和牌时，特定人做过特定操作，只对这个人生效"""
        looserResults = []
        """明牌输"""
        if self.isMingshu(seatId):
            looserResults.append(self.processFanXingResult(self.MINGSHU))
        ftlog.info('MKawuxingOneResult.getLooserResults looserResults=', looserResults)
        return looserResults

    def getPaoResults(self):
        """和牌时，计算放炮的人对自身的影响"""
        paoResults = []
        """海底炮"""
        if self.isHaidipao():
            paoResults.append(self.processFanXingResult(self.HAIDIPAO))
        """杠上炮"""
        if self.isGangshangpao():
            paoResults.append(self.processFanXingResult(self.GANGSHANGPAO))

        ftlog.info('MKawuxingOneResult.getPaoResults paoResults=', paoResults)
        return paoResults

    def processFanXingResult(self, fanSymbol, scoreTimes=0):
        res = {"name": '', "index": 0, "score": 0, 'fanSymbol': ''}
        if self.fanXing[fanSymbol]:
            if self.fanXing[fanSymbol]["name"]:
                res['name'] = self.fanXing[fanSymbol]["name"]
            if self.fanXing[fanSymbol].has_key("index"):
                # 三种番型默认使用当前文件的配置，但如果前端提交了配置，则使用前端提交的配置
                scoreIndex = self.tableConfig.get(MTDefine.FAN_LIST, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                if fanSymbol == self.PENGPENGHU:
                    res['index'] = scoreIndex.index(
                        self.tableConfig.get(MTDefine.PENGPENGHU_FAN, scoreIndex[self.fanXing[fanSymbol]["index"]]))
                elif fanSymbol == self.KAWUXING:
                    res['index'] = scoreIndex.index(
                        self.tableConfig.get(MTDefine.KAWUXING_FAN, scoreIndex[self.fanXing[fanSymbol]["index"]]))
                elif fanSymbol == self.GANGKAI:
                    res['index'] = scoreIndex.index(
                        self.tableConfig.get(MTDefine.GANGSHANGHUA_FAN, scoreIndex[self.fanXing[fanSymbol]["index"]]))
                else:
                    res['index'] = self.fanXing[fanSymbol]["index"]
            if self.fanXing[fanSymbol].has_key("addScore"):
                res['score'] += self.fanXing[fanSymbol]["addScore"]
            if self.fanXing[fanSymbol].has_key("multiplyScore"):
                res['score'] += self.fanXing[fanSymbol]["multiplyScore"] * scoreTimes
            res['fanSymbol'] = fanSymbol
        return res

    def getScoreByResults(self, results, maxFan=0):
        index = 0
        score = 0
        for result in results:
            index += result['index']
            score += result['score']
        scoreIndex = self.tableConfig.get(MTDefine.FAN_LIST, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        ftlog.info('MKawuxingOneResult.getScoreByResults scoreIndex:', scoreIndex)
        if len(scoreIndex) < index:
            # 如果超出最大番型的定义，按照len-1计算，防止超出边界
            ftlog.info('MKawuxingOneResult.getScoreByResults exceed fan_list in MTDefine, index=', index)
            index = len(scoreIndex) - 1
        if maxFan:
            # maxFan不为0时，限制最大番数。算最大番型时，不要传递此参数，要么就算不出来了
            if scoreIndex[index] > maxFan:
                fan = maxFan
        fan = scoreIndex[index]
        finalScore = fan + score
        ftlog.info('MKawuxingOneResult.getScoreByResults score=', finalScore)
        return finalScore

    def getFanByResults(self, results, maxFan=0):
        index = 0
        for result in results:
            index += result['index']
        ftlog.info('MKawuxingOneResult.getFanByResults fan=', index)
        return index

    def getFanPatternListByResults(self, results):
        fanIndex = self.tableConfig.get(MTDefine.FAN_LIST, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        fanPatternList = []
        names = []
        for result in results:
            if result['fanSymbol'] in [self.PAO, self.QIA, self.MO, self.BA]:
                # 硬编码，因为目前前端合并一个"跑恰摸八"显示
                # 跑恰摸八不算番，只算分
                name = "跑恰摸八"
                fan = ["跑恰摸八", "算分"]
            else:
                name = result['name']
                if result['index']:
                    fan = [result['name'], str(fanIndex[result['index']]) + "番"]
                else:
                    fan = [result['name'], "算分"]

            if name not in names:
                # 排重
                names.append(name)
                fanPatternList.append(fan)

        ftlog.info('MKawuxingOneResult.getFanPatternListByResults fanPatternList=', fanPatternList)
        return fanPatternList

    def isKawuxing(self, pattern):
        """
        卡五星：卡5筒或5条和牌，并且必须为夹牌
        """
        if self.winTile == MTile.TILE_FIVE_TONG or self.winTile == MTile.TILE_FIVE_TIAO:
            for p in pattern:
                if len(p) == 2:
                    continue

                if p[0] == p[1]:
                    continue

                if (self.winTile in p) and (p.index(self.winTile)) == 1:
                    ftlog.debug('MKawuxingOneResult.isKawuxing result: True')
                    return True
        ftlog.debug('MKawuxingOneResult.isKawuxing result: False')
        return False

    def isQingyise(self):
        """
        清一色：由同一门花色（筒子或条子）组成的和牌牌型
        """
        colorArr = [0, 0, 0, 0]
        for tile in self.__player_all_tiles_arr[self.winSeatId]:
            color = MTile.getColor(tile)
            colorArr[color] = 1

        colorCount = 0
        for eachColor in colorArr:
            if eachColor:
                colorCount += 1
        if colorCount > 1:
            ftlog.debug('MKawuxingOneResult.isQingyise result: False')
            return False
        ftlog.debug('MKawuxingOneResult.isQingyise result: True')
        return True

    def isHaidilao(self):
        """
        海底捞：最后一张牌自摸和牌
        """
        if self.tableTileMgr and self.tableTileMgr.getTilesLeftCount() == 0:
            ftlog.debug('MKawuxingOneResult.isHaidilao result: True')
            return True

        ftlog.debug('MKawuxingOneResult.isHaidilao result: False')
        return False

    def isShouzhuayi(self):
        """
        手抓一：胡牌时自己手上只有一张牌，和牌手牌应该是一对
        """
        if self.__player_hand_tiles_with_hu and len(self.__player_hand_tiles_with_hu[self.winSeatId]) == 2:
            ftlog.debug('MKawuxingOneResult.isShouzhuayi result: True')
            return True

        ftlog.debug('MKawuxingOneResult.isShozhuayi result: False')
        return False

    def isPengpenghu(self, pattern):
        """
        碰碰胡：由四个刻子（杠）和一对组成的胡牌牌型
        """
        pengpengCount = 0
        pengpengList = []
        # pattern中只有手牌
        for p in pattern:
            if len(p) == 4:
                pengpengCount += 1
                pengpengList.append(p[0])
            if len(p) == 3:
                if p[0] == p[1] and p[1] == p[2]:
                    pengpengCount += 1
                    pengpengList.append(p[0])
        # winNode的pattern计算有问题，有时包含碰牌或杠牌，下面排下重
        for gang in self.__player_all_tiles[self.winSeatId][MHand.TYPE_GANG]:
            if gang['pattern'][0] not in pengpengList:
                pengpengCount += 1

        for peng in self.__player_all_tiles[self.winSeatId][MHand.TYPE_PENG]:
            if peng[0] not in pengpengList:
                pengpengCount += 1

        if pengpengCount == 4:
            ftlog.debug('MKawuxingOneResult.isPengpenghu result: True')
            return True
        ftlog.debug('MKawuxingOneResult.isPengpenghu result: False')
        return False

    def isQidui(self, pattern):
        """
        七对：手中有七个对子的胡牌牌型，碰出的牌不算
        """
        tileCountArr = [0 for _ in range(MTile.TILE_MAX_VALUE)]
        jiangCount = 0
        for p in pattern:
            if len(p) == 2:
                jiangCount += 1
                for tile in p:
                    tileCountArr[tile] += 1

        fourCount = 0
        if jiangCount == 7:
            for tileCount in tileCountArr:
                if tileCount == 4:
                    fourCount += 1
            if fourCount == 0:
                ftlog.debug('MKawuxingOneResult.isQidui result: True')
                return True
        ftlog.debug('MKawuxingOneResult.isQidui result: False')
        return False

    def isQiduiHao(self, pattern):
        """
        豪华七对：有四个相同的牌当做两个对子使用
        """
        tileCountArr = [0 for _ in range(MTile.TILE_MAX_VALUE)]
        jiangCount = 0
        for p in pattern:
            if len(p) == 2:
                jiangCount += 1
                for tile in p:
                    tileCountArr[tile] += 1

        fourCount = 0
        if jiangCount == 7:
            for tileCount in tileCountArr:
                if tileCount == 4:
                    fourCount += 1
            if fourCount == 1:
                ftlog.debug('MKawuxingOneResult.isQiduiHao result: True')
                return True
        ftlog.debug('MKawuxingOneResult.isQiduiHao result: False')
        return False

    def isQiduiChaoHao(self, pattern):
        """
        超豪华七对：有两个四个相同的牌当做四个对子使用
        """
        tileCountArr = [0 for _ in range(MTile.TILE_MAX_VALUE)]
        jiangCount = 0
        for p in pattern:
            if len(p) == 2:
                jiangCount += 1
                for tile in p:
                    tileCountArr[tile] += 1

        fourCount = 0
        if jiangCount == 7:
            for tileCount in tileCountArr:
                if tileCount == 4:
                    fourCount += 1
            if fourCount == 2:
                ftlog.debug('MKawuxingOneResult.isQiduiChaoHao result: True')
                return True
        ftlog.debug('MKawuxingOneResult.isQiduiChaoHao result: False')
        return False

    def isQiduiChaoChaoHao(self, pattern):
        """
        超超豪华七对：有三个四个相同的牌当做六个对子使用
        """
        tileCountArr = [0 for _ in range(MTile.TILE_MAX_VALUE)]
        jiangCount = 0
        for p in pattern:
            if len(p) == 2:
                jiangCount += 1
                for tile in p:
                    tileCountArr[tile] += 1

        fourCount = 0
        if jiangCount == 7:
            for tileCount in tileCountArr:
                if tileCount == 4:
                    fourCount += 1
            if fourCount == 3:
                ftlog.debug('MKawuxingOneResult.isQiduiChaoChaoHao result: True')
                return True
        ftlog.debug('MKawuxingOneResult.isQiduiChaoChaoHao result: False')
        return False

    def isXiaosanyuan(self):
        """
        小三元：胡牌时 如果牌面上有中、发、白中的任意2种（每种牌3张，碰杠都算），并且牌面中还有其余1对
        中发白胡牌时，只能时按照将，刻，杠，不可能按照顺子来胡牌，所以不用看胡牌牌型
        """
        tileCountArr = [0 for _ in range(MTile.TILE_MAX_VALUE)]
        for tile in self.__player_all_tiles_arr[self.winSeatId]:
            tileCountArr[tile] += 1
        kegangCount = 0
        jiangCount = 0
        for tileCheck in [MTile.TILE_HONG_ZHONG, MTile.TILE_FA_CAI, MTile.TILE_BAI_BAN]:
            if tileCountArr[tileCheck] >= 3:
                kegangCount += 1
            elif tileCountArr[tileCheck] == 2:
                jiangCount += 1
        if kegangCount == 2 and jiangCount == 1:
            ftlog.debug('MKawuxingOneResult.isXiaosanyuan result: True')
            return True
        ftlog.debug('MKawuxingOneResult.isXiaosanyuan result: False')
        return False

    def isDasanyuan(self):
        """
        大三元：胡牌时 如果牌面上有中、发、白每种3张（碰杠都算），称为大三元
        """
        tileCountArr = [0 for _ in range(MTile.TILE_MAX_VALUE)]
        for tile in self.__player_all_tiles_arr[self.winSeatId]:
            tileCountArr[tile] += 1
        if tileCountArr[MTile.TILE_HONG_ZHONG] >= 3 and tileCountArr[MTile.TILE_FA_CAI] >= 3 and tileCountArr[
            MTile.TILE_BAI_BAN] >= 3:
            ftlog.debug('MKawuxingOneResult.isDasanyuan result: True')
            return True
        ftlog.debug('MKawuxingOneResult.isDasanyuan result: False')
        return False

    def isMingsigui(self):
        """
        明四归：默认为半频道
        半频道：碰了的牌，必须胡第四张牌，才算明四归
        全频道：碰了的牌，第四张此牌也在同一玩家手上组成其他的句子，即算明四归
        """
        # 默认为半频道
        pinDao = self.tableConfig.get(MTDefine.PIN_DAO, 2)

        tileCountArr = [0 for _ in range(MTile.TILE_MAX_VALUE)]
        for tile in self.__player_all_tiles_arr[self.winSeatId]:
            tileCountArr[tile] += 1

        for pengPattern in self.__player_all_tiles[self.winSeatId][MHand.TYPE_PENG]:
            for tile in pengPattern:
                if tileCountArr[tile] == 4:
                    if pinDao == 1:
                        # 全频道
                        ftlog.debug('MKawuxingOneResult.isMingsigui result: True')
                        return True
                    elif pinDao == 2 and tile == self.winTile:
                        # 半频道
                        ftlog.debug('MKawuxingOneResult.isMingsigui result: True')
                        return True
        ftlog.debug('MKawuxingOneResult.isMingsigui result: False')
        return False

    def isAnsigui(self):
        """
        暗四归：默认为半频道
        半频道：手上有三张一样的字，这三张字必须是只能在手上，胡第四张，胡的牌型不是七对
        全频道：手里有四张一样的字，或者有三张一样在手上胡第四张，胡的牌型不是七对，都算暗四归
        """
        # 默认为半频道
        pinDao = self.tableConfig.get(MTDefine.PIN_DAO, 2)

        handTileCountArr = [0 for _ in range(MTile.TILE_MAX_VALUE)]
        for tile in self.__player_hand_tiles_with_hu[self.winSeatId]:
            handTileCountArr[tile] += 1

        if pinDao == 1:
            for handTileCount in handTileCountArr:
                if handTileCount == 4:
                    ftlog.debug('MKawuxingOneResult.isAnsigui result: True')
                    return True
        elif pinDao == 2 and handTileCountArr[self.winTile] == 4:
            ftlog.debug('MKawuxingOneResult.isAnsigui result: True')
            return True

        ftlog.debug('MKawuxingOneResult.isAnsigui result: False')
        return False

    def isPaoqiaomobaPao(self):
        """
        跑恰摸八中的跑：指和牌就加一分。就是说只要和牌，就有跑1，也仅有跑1
        """
        if self.tableConfig.get(MTDefine.PAOQIAMOBA, 0):
            # 必有人胡牌
            ftlog.debug('MKawuxingOneResult.isPaoqiaomobaPao result: True')
            return True
        ftlog.debug('MKawuxingOneResult.isPaoqiaomobaPao result: False')
        return False

    def isPaoqiaomobaMo(self):
        """
        跑恰摸八中的摸：指自摸就加一分。只要自摸，就有摸1，也仅有摸1
        """
        if self.tableConfig.get(MTDefine.PAOQIAMOBA, 0):
            if self.lastSeatId == self.winSeatId:
                ftlog.debug('MKawuxingOneResult.isPaoqiaomobaMo result: True')
                return True
        ftlog.debug('MKawuxingOneResult.isPaoqiaomobaMo result: False')
        return False

    def getPaoqiaomobaQiaCount(self):
        """
        恰摸八中的恰：指玩家手上自己有一坎牌（三张一样）
        1. 碰的牌不算恰，碰完牌后摸到再杠牌的算恰。
        2. 有几恰加几分。只有杠和手里的3张，算恰
        3. 如三张牌有一张与其它牌成型了 一句话 那么此时状态不算恰，必须是单独的 3张牌。
        4. 对倒胡（听牌为两个对子，胡的碰不管是自摸还是别人放炮，也都算恰）
        """
        qiaCount = 0
        if self.tableConfig.get(MTDefine.PAOQIAMOBA, 0):
            qiaCount += len(self.__player_all_tiles[self.winSeatId][MHand.TYPE_GANG])
            tileCountArr = [0 for _ in range(MTile.TILE_MAX_VALUE)]
            for tile in self.__player_hand_tiles_with_hu[self.winSeatId]:
                tileCountArr[tile] += 1
            for tileCount in tileCountArr:
                if tileCount >= 3:
                    qiaCount += 1
        ftlog.debug('MKawuxingOneResult.getPaoqiaomobaQiaCount qiaCount: ', qiaCount)
        return qiaCount

    def getPaoqiaomobaBaCount(self):
        """
        跑恰摸八中的八：筒、条、风这三门牌里面，和牌时，有几门达到8张
        每种花色，8张加1分，9张加2分，以此类推
        """
        baCount = 0
        if self.tableConfig.get(MTDefine.PAOQIAMOBA, 0):
            colorCountArr = [0, 0, 0, 0]
            for tile in self.__player_all_tiles_arr[self.winSeatId]:
                color = MTile.getColor(tile)
                colorCountArr[color] += 1

            for colorCount in colorCountArr:
                if colorCount >= 8:
                    baCount += colorCount - 7
        ftlog.debug('MKawuxingOneResult.getPaoqiaomobaBaCount baCount: ', baCount)
        return baCount

    def getKanCount(self):
        """
        数坎：胡牌时手上有三张一样的牌，就算一坎（一坎一分，两个就算两坎），手里有坎
        """
        kanCount = 0
        if self.tableConfig.get(MTDefine.SHU_KAN, 0):
            tileCountArr = [0 for _ in range(MTile.TILE_MAX_VALUE)]
            for tile in self.__player_hand_tiles_with_hu[self.winSeatId]:
                tileCountArr[tile] += 1
            for tileCount in tileCountArr:
                if tileCount >= 3:
                    kanCount += 1
        ftlog.debug('MKawuxingOneResult.getKanCount kanCount: ', kanCount)
        return kanCount

    def getMaScore(self):
        lstInfo = self.tableTileMgr.getLastSpecialTiles()
        maScore = 0
        if lstInfo and lstInfo['ma_tile']:
            if lstInfo['ma_tile'] in [MTile.TILE_HONG_ZHONG, MTile.TILE_FA_CAI, MTile.TILE_BAI_BAN]:
                maScore = 10
            elif lstInfo['ma_tile'] > 10 and lstInfo['ma_tile'] < 30:
                # 马牌仅能出现筒、条
                maScore = lstInfo['ma_tile'] % 10
        ftlog.debug('MKawuxingOneResult.getMaScoreCount maScoreCount: ', maScore)
        return maScore

    def isHaidipao(self):
        """
        海底炮：最后一张打出去的牌 放炮
        """
        if self.lastSeatId != self.winSeatId:
            if self.tableTileMgr and self.tableTileMgr.getTilesLeftCount() == 0:
                ftlog.debug('MKawuxingOneResult.isHaidipao result: True')
                return True
        ftlog.debug('MKawuxingOneResult.isHaidipao result: False')
        return False

    def isGangshangpao(self):
        """
        杠上炮：杠后打出的牌被别人胡，杠钱照算
        """
        lastGangActionID = 0
        ftlog.debug(self.lastSeatId, self.winSeatId, self.playerGangTiles)
        if self.lastSeatId != self.winSeatId:
            for gangArr in self.playerGangTiles[self.lastSeatId]:
                ftlog.debug(gangArr)
                if gangArr['actionID'] >= lastGangActionID:
                    lastGangActionID = gangArr['actionID']
            if lastGangActionID > 0:
                # 杠牌后抓牌1步，出牌一步，如果放炮，actionID差值应为2
                if (self.actionID - lastGangActionID) == 2:
                    ftlog.debug('MKawuxingOneResult.isGangShangPao result: True, actionID:', self.actionID,
                                'lastGangActionID:', lastGangActionID)
                    return True
        ftlog.debug('MKawuxingOneResult.isGangShangPao result: False, actionID:', self.actionID, 'lastGangActionID:',
                    lastGangActionID)
        return False

    def isMinghu(self):
        """
        明牌胡：亮倒后和牌
        """
        if self.__player_ting_liang[self.winSeatId] == True:
            ftlog.debug('MKawuxingOneResult.isMinghu result: True')
            return True
        ftlog.debug('MKawuxingOneResult.isMinghu result: False')
        return False

    def isMingshu(self, seatId):
        """
        明牌输：亮倒后输牌
        """
        if self.isMinghu() == False and self.__player_ting_liang[seatId] == True:
            # 当赢家是明牌的情况下，输家即使也明牌了，不再额外罚分
            ftlog.debug('MKawuxingOneResult.isMingshu result: True')
            return True
        ftlog.debug('MKawuxingOneResult.isMingshu result: False')
        return False

    def setPlayerAllTiles4Test(self, tiles):
        # 仅用于测试
        self.__player_all_tiles = tiles

    def setPlayerAllTilesArr4Test(self, tiles):
        # 仅用于测试
        self.__player_all_tiles_arr = tiles

    def setPlayerHandTilesWithHu4Test(self, tiles):
        # 仅用于测试
        self.__player_hand_tiles_with_hu = tiles

    def setPlayerTingLiang4Test(self, tingLiangState):
        # 仅用于测试
        self.__player_ting_liang = tingLiangState

    def setWinPatterns4Test(self, winPatterns):
        # 仅用于测试
        self.__win_patterns = winPatterns


if __name__ == "__main__":
    result = MKawuxingOneResult()
    result.setTableConfig({})
    result.setWinSeatId(1)
    result.setMingState([0, 0, 0])
    tableTileMgr = MTableTileFactory.getTableTileMgr(3, 'kawuxing', 1)

    """只设置所有牌list"""
    result.setPlayerAllTilesArr4Test([[], [16, 16, 15, 16, 17, 14, 15, 16, 11, 12, 13], []])
    assert True == result.isQingyise()
    result.setPlayerAllTilesArr4Test([[], [16, 16, 15, 16, 17, 14, 15, 16, 21, 22, 23], []])
    assert False == result.isQingyise()
    result.setPlayerAllTilesArr4Test([[], [37, 37, 35, 35, 35, 36, 36, 36, 15, 16, 17], []])
    assert True == result.isXiaosanyuan()
    assert False == result.isDasanyuan()
    result.setPlayerAllTilesArr4Test([[], [15, 15, 35, 35, 35, 36, 36, 36, 37, 37, 37], []])
    assert False == result.isXiaosanyuan()
    assert True == result.isDasanyuan()
    # 开启跑恰摸八
    result.setTableConfig({MTDefine.PAOQIAMOBA: 1})
    result.setPlayerAllTilesArr4Test([[], [15, 15, 15, 16, 16, 16, 17, 17, 17, 20, 20], []])
    assert 2 == result.getPaoqiaomobaBaCount()
    result.setPlayerAllTilesArr4Test([[], [15, 15, 15, 15, 16, 16, 16, 16, 21, 22, 23, 25, 26, 27, 21, 21], []])
    assert 2 == result.getPaoqiaomobaBaCount()
    # 关闭跑恰摸八
    result.setTableConfig({MTDefine.PAOQIAMOBA: 0})
    result.setPlayerAllTilesArr4Test([[], [15, 15, 15, 16, 16, 16, 17, 17, 17, 20, 20], []])
    assert 0 == result.getPaoqiaomobaBaCount()

    """清空所有的牌，只设置手牌"""
    result.setPlayerAllTilesArr4Test([[], [], []])
    result.setPlayerHandTilesWithHu4Test([[], [11, 11], []])
    assert True == result.isShouzhuayi()
    result.setPlayerHandTilesWithHu4Test([[], [11, 12, 13, 22, 22], []])
    assert False == result.isShouzhuayi()
    # 开启全频道
    result.setTableConfig({MTDefine.PIN_DAO: 1})
    result.setWinTile(15)
    result.setPlayerHandTilesWithHu4Test([[], [14, 14, 15, 15, 15, 15], []])
    assert True == result.isAnsigui()
    result.setWinTile(14)
    result.setPlayerHandTilesWithHu4Test([[], [14, 14, 15, 15, 15, 15], []])
    assert True == result.isAnsigui()
    # 开启半频道
    result.setTableConfig({MTDefine.PIN_DAO: 2})
    result.setWinTile(15)
    result.setPlayerHandTilesWithHu4Test([[], [14, 14, 15, 15, 15, 15], []])
    assert True == result.isAnsigui()
    result.setWinTile(14)
    result.setPlayerHandTilesWithHu4Test([[], [14, 14, 15, 15, 15, 15], []])
    assert False == result.isAnsigui()
    # 关闭频道
    result.setTableConfig({MTDefine.PIN_DAO: 0})
    result.setWinTile(15)
    result.setPlayerHandTilesWithHu4Test([[], [14, 14, 15, 15, 15, 15], []])
    assert False == result.isAnsigui()
    result.setWinTile(14)
    result.setPlayerHandTilesWithHu4Test([[], [14, 14, 15, 15, 15, 15], []])
    assert False == result.isAnsigui()
    # 开启数坎
    result.setTableConfig({MTDefine.SHU_KAN: 1})
    result.setPlayerHandTilesWithHu4Test([[], [14, 14, 15, 15, 15, 15], []])
    assert 1 == result.getKanCount()

    """清空所有的牌，只设置所有牌的详细情况、和手牌"""
    # 开启跑恰摸八
    result.setTableConfig({MTDefine.PAOQIAMOBA: 1})
    result.setPlayerHandTilesWithHu4Test([[], [], []])
    result.setPlayerAllTiles4Test([[], {MHand.TYPE_GANG: [{'pattern': [11, 11, 11, 11]}]}, []])
    result.setPlayerHandTilesWithHu4Test([[], [14, 14, 15, 15, 15, 15], []])
    assert 2 == result.getPaoqiaomobaQiaCount()
    result.setPlayerAllTiles4Test([[], {MHand.TYPE_GANG: []}, []])
    result.setPlayerHandTilesWithHu4Test([[], [14, 14, 15, 15, 15, 15], []])
    assert 1 == result.getPaoqiaomobaQiaCount()
    result.setTableConfig({MTDefine.PAOQIAMOBA: 0})
    assert 0 == result.getPaoqiaomobaQiaCount()

    # 开启全频道
    result.setTableConfig({MTDefine.PIN_DAO: 1})
    result.setWinTile(15)
    result.setPlayerAllTiles4Test([[], {MHand.TYPE_PENG: [[15, 15, 15]]}, []])
    result.setPlayerAllTilesArr4Test([[], [15, 15, 15, 14, 15, 16, 21, 21, 21, 25, 25], []])
    assert True == result.isMingsigui()
    result.setWinTile(14)
    result.setPlayerAllTilesArr4Test([[], [15, 15, 15, 14, 15, 16, 21, 21, 21, 25, 25], []])
    assert True == result.isMingsigui()
    # 开启半频道
    result.setTableConfig({MTDefine.PIN_DAO: 2})
    result.setWinTile(15)
    result.setPlayerAllTiles4Test([[], {MHand.TYPE_PENG: [[15, 15, 15]]}, []])
    result.setPlayerAllTilesArr4Test([[], [15, 15, 15, 14, 15, 16, 21, 21, 21, 25, 25], []])
    assert True == result.isMingsigui()
    result.setWinTile(14)
    result.setPlayerAllTilesArr4Test([[], [15, 15, 15, 14, 15, 16, 21, 21, 21, 25, 25], []])
    assert False == result.isMingsigui()
    # 关闭频道
    result.setTableConfig({MTDefine.PIN_DAO: 0})
    result.setWinTile(15)
    result.setPlayerAllTiles4Test([[], {MHand.TYPE_PENG: [[15, 15, 15]]}, []])
    result.setPlayerAllTilesArr4Test([[], [15, 15, 15, 14, 15, 16, 21, 21, 21, 25, 25], []])
    assert False == result.isMingsigui()

    """清空所有的牌，只设置winNode"""
    result.setPlayerAllTiles4Test([[], [], []])
    result.setPlayerAllTilesArr4Test([[], [], []])
    assert True == result.isQidui([[16, 16], [17, 17], [18, 18], [19, 19], [13, 13], [14, 14], [15, 15]])
    assert False == result.isQidui([[16, 16], [17, 17], [18, 18], [19, 19], [13, 13], [14, 14], [14, 14]])
    assert True == result.isQiduiHao([[16, 16], [17, 17], [18, 18], [19, 19], [13, 13], [14, 14], [14, 14]])
    assert False == result.isQiduiChaoHao([[16, 16], [17, 17], [18, 18], [19, 19], [13, 13], [14, 14], [14, 14]])
    assert True == result.isQiduiChaoHao([[16, 16], [17, 17], [18, 18], [13, 13], [13, 13], [14, 14], [14, 14]])

    result.setWinTile(29)
    result.setPlayerAllTiles4Test([[], {MHand.TYPE_PENG: [[22, 22, 22]],
                                        MHand.TYPE_GANG: [{'pattern': [15, 15, 15, 15], 'style': 0, 'actionID': 15},
                                                          {'pattern': [35, 35, 35, 35], 'style': True,
                                                           'actionID': 40}]}, []])
    # winNode的patten计算有问题，上述用例是实际的情况，先兼容这中错误情况
    assert True == result.isPengpenghu([[24, 24], [29, 29, 29], [35, 35, 35]])

    # 杠上炮
    result.setLastSeatId(2)
    result.setWinSeatId(1)
    result.setActionID(22)
    result.setPlayerGangTiles([[], [], [{'actionID': 1}, {'actionID': 20}], []])
    assert True == result.isGangshangpao()

    # 清一色海底捞，8分, 0号明牌输
    result.setWinPatterns4Test([[[16, 16], [15, 16, 17], [14, 15, 16], [11, 12, 13]]])
    result.setLastSeatId(1)
    result.setWinSeatId(1)
    result.setPlayerCount(3)
    result.setMingState([0, 0, 0])
    result.setWinTile(11)
    result.setPlayerHandTilesWithHu4Test([[], [16, 16, 15, 16, 17, 14, 15, 16, 11, 12, 13], []])
    result.setPlayerAllTiles4Test([{}, {MHand.TYPE_PENG: [], MHand.TYPE_GANG: []}, {}])
    result.setPlayerAllTilesArr4Test([[], [16, 16, 15, 16, 17, 14, 15, 16, 11, 12, 13], []])
    result.setPlayerTingLiang4Test([True, False, False])
    result.setTableConfig({'fan_list': [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]})
    tableTileMgr = MTableTileFactory.getTableTileMgr(3, 'kawuxing', 1)
    tableTileMgr.tileTestMgr.setTiles([])
    result.setTableTileMgr(tableTileMgr.tileTestMgr)
    assert 8 == result.getScoreByResults(result.getWinnerResults())
    result.calcWin()
    ftlog.debug(result.results)
    assert result.results[result.KEY_SCORE] == [-16, 24, -8]

    # 清一色手抓一，16分
    result.setWinPatterns4Test([[[11, 11], [13, 13, 13], [14, 14, 14], [15, 15, 15]]])
    result.setLastSeatId(1)
    result.setWinSeatId(1)
    result.setPlayerCount(3)
    result.setWinTile(11)
    result.setMingState([0, 0, 0])
    result.setPlayerHandTilesWithHu4Test([[], [11, 11], []])
    result.setPlayerAllTiles4Test([{}, {MHand.TYPE_PENG: [], MHand.TYPE_GANG: []}, {}])
    result.setPlayerAllTilesArr4Test([[], [16, 16, 15, 16, 17, 14, 15, 16, 11, 12, 13], []])
    result.setPlayerTingLiang4Test([False, False, False])
    result.setTableConfig({'fan_list': [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]})
    tableTileMgr = MTableTileFactory.getTableTileMgr(3, 'kawuxing', 1)
    tableTileMgr.tileTestMgr.setTiles([20, 21, 22])
    result.setTableTileMgr(tableTileMgr.tileTestMgr)
    assert 16 == result.getScoreByResults(result.getWinnerResults())
    result.calcWin()
    ftlog.debug(result.results)
    assert result.results[result.KEY_SCORE] == [-16, 32, -16]
    assert result.results[result.KEY_WIN_MODE] == [-2, 0, -2]

    # 放杠2倍
    result.setLastSeatId(2)
    result.setWinSeatId(1)
    result.setPlayerCount(3)
    result.setStyle(MPlayerTileGang.MING_GANG)
    result.calcGang()
    ftlog.debug(result.results)
    assert result.results[result.KEY_SCORE] == [0, 2, -2]

    # 蓄杠2倍
    result.setLastSeatId(1)
    result.setWinSeatId(1)
    result.setPlayerCount(3)
    result.setStyle(MPlayerTileGang.MING_GANG)
    result.calcGang()
    ftlog.debug(result.results)
    assert result.results[result.KEY_SCORE] == [-1, 2, -1]
