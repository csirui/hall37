# -*- coding=utf-8
'''
Created on 2017年3月7日

结算

@author: nick.kai.lee
'''
from difang.majiang2.player.player import MPlayerTileGang
from difang.majiang2.table.table_config_define import MTDefine
from hengyangmj.hengyang_log import HYLog


class HYOneBudget(object):
    # 杠牌，刮风下雨
    RESULT_GANG = 1
    # 和牌
    RESULT_WIN = 2
    # 流局
    RESULT_FLOW = 3

    TYPE = {"FINISH": 0, "TERMINATE": 3}

    # 杠牌和胡牌都会产生一个OneResult 在OneResult中存放winMode,番型,统计信息 每局输赢后提供数据给客户端，最后牌桌结束后一起将统计数据提供给客户端
    KEY_TYPE = 'type'  # 杠牌 和牌
    KEY_NAME = 'name'  # 明杠 暗杠
    KEY_SCORE = 'score'  # 每局的分数(变化部分)统计 [seatId] = value
    KEY_WIN_MODE = 'winMode'  # 输赢类型 [seatId] = value
    KEY_FAN_PATTERN = 'fanPattern'  # 番型统计 [seatId] = value
    KEY_STAT = 'stat'  # 最后大结算需要的统计数据 [seatId] = value {"desc":"自摸","value":0},{"desc":"点炮","value":0},{"desc":"明杠","value":0},{"desc":"暗杠","value":0},{"desc":"最大番数","value":2}
    KEY_AWARD_INFO = 'awardInfo'
    KEY_WIN_TILE = 'winTile'  # 胡的哪张牌,在血战的结算里需要

    KEY_TYPE_NAME_GANG = '杠牌'
    KEY_TYPE_NAME_HU = '和牌'
    KEY_TYPE_NAME_FLOW = '流局'

    # stat type
    STAT_ZIMO = 'ziMO'
    STAT_DIANPAO = 'dianPao'
    STAT_MINGGANG = 'mingGang'
    STAT_ANGANG = 'anGang'
    STAT_ZUIDAFAN = 'zuiDaFan'

    # winMode
    WIN_MODE_DIANPAO_BAOZHUANG = -3
    WIN_MODE_LOSS = -2
    WIN_MODE_DIANPAO = -1
    WIN_MODE_ZIMO = 0
    WIN_MODE_PINGHU = 1
    WIN_MODE_GANGKAI = 2
    WIN_MODE_QIANGGANGHU = 3
    WIN_MODE_WUDUIHU = 4
    WIN_MODE_TIANHU = 5

    def __init__(self):
        super(HYOneBudget, self).__init__()

        # 牌桌手牌管理器
        self.__table_tile_mgr = None
        # 牌桌胜负规则管理器
        self.__win_rule_mgr = None

        self.__table_config = None  # 牌桌配置
        self.__play_mode = None  # 玩法
        self.__player_count = 0  # 玩家个数
        self.__aciton_id = None  # 获胜时的aciton_id
        self.__banker_seat_id = None  # 庄家座位号

        self.__type = None  # 结算类型 胡牌 或者 流局

        """
        1）自摸 self.__win_seat_id == self.__last_seat_id
        2）点炮 self.__win_seat_id != self.__last_seat_id
        """
        self.__active_seat_id = None  # 获胜一方的座位号
        self.__passvie_seat_id = None  # 上一轮的桌子号

        """通过__table_tile_mgr获取__win_tile是否是宝牌，是否是宝中宝"""
        self.__win_tile = None  # 获胜牌

        self.__player_all_tiles = []  # 所有玩家的所有牌，按手牌格式的数组[[],[],[],[]]

        self.__stat_type = {
            self.STAT_ZIMO: {"name": "自摸"},
            self.STAT_DIANPAO: {"name": "点炮"},
            self.STAT_MINGGANG: {"name": "明杠"},
            self.STAT_ANGANG: {"name": "暗杠"},
            self.STAT_ZUIDAFAN: {"name": "最大番"},
        }

        # 倍数
        self.__multiple = 1

        self.__results = {
            "score": []  # 保存结算中玩家的积分 数组下标是座位号
        }  # 结果

    def serialize(self):
        """序列化"""
        obj = {}
        if self.__play_mode:
            obj['playMode'] = self.__play_mode
        if self.__banker_seat_id:
            obj['bankerSeatId'] = self.__banker_seat_id
        if self.__active_seat_id:
            obj['winSeatId'] = self.__active_seat_id
        if self.__passvie_seat_id:
            obj['lastSeatId'] = self.__passvie_seat_id
        if self.__win_tile:
            obj['winTile'] = self.__win_tile
        if self.__aciton_id:
            obj['actionID'] = self.__aciton_id
        if self.__player_count:
            obj['playCount'] = self.__player_count
        if self.__table_config:
            obj['tableConfig'] = self.__table_config
        HYLog.debug('HYWinLoseResult.serialize: ', obj)

    def unserialize(self, obj):
        """反序列化"""
        HYLog.debug('HYWinLoseResult.unSerialize: ', obj)
        self.__play_mode = obj.get('playMode', None)
        self.__banker_seat_id = obj.get('bankerSeatId', None)
        self.__active_seat_id = obj.get('winSeatId', None)
        self.__passvie_seat_id = obj.get('lastSeatId', None)
        self.__win_tile = obj.get('winTile', 0)
        self.__aciton_id = obj.get('actionID', 0)
        self.__player_count = obj.get('playCount', 4)
        self.__table_config = obj.get('tableConfig', None)

    def get_results(self):
        return self.__results

    def get_player_count(self):
        return self.__player_count

    def set_player_count(self, count):
        self.__player_count = count

    def set_all_players_tiles(self, tiles):
        """
        设置所有玩家的手牌信息
        @:param tiles 二维数组 [座位号][[手牌],[吃]...]
        """
        self.__player_all_tiles = tiles

    def get_all_players_tiles(self):
        return self.__player_all_tiles

    def set_type(self, rType):
        """设置结算类型"""
        self.__type = rType

    def get_type(self):
        return self.__type

    def set_action_id(self, action_id):
        self.__aciton_id = action_id

    def get_action_id(self):
        return self.__aciton_id

    def set_banker_seat_id(self, seat_id):
        """
        设置庄家座位号
        @:param seat_id
        """
        self.__banker_seat_id = seat_id

    def get_banker_seat_id(self):
        return self.__banker_seat_id

    def set_play_mode(self, mode):
        """
        设置玩法
        @:param mode eg: "hengyang"
        """
        self.__play_mode = mode

    def get_play_mode(self):
        return self.__play_mode

    def get_multiple(self):
        return self.__multiple

    def set_multiple(self, value):
        self.__multiple = value

    def set_active_seat_id(self, seat_id):
        """
        赢家座位号
        @:param seat_id
        """
        self.__active_seat_id = seat_id

    def get_active_seat_id(self):
        """ 获得赢家座位号 """
        return self.__active_seat_id

    def set_passvie_seat_id(self, seat_id):
        """
        导致胡牌结果的玩家座位号(流局则是上家座位号)
        @:param seat_id
        """
        self.__passvie_seat_id = seat_id

    def get_passvie_seat_id(self):
        return self.__passvie_seat_id

    def set_table_config(self, config):
        self.__table_config = config

    def set_win_tile(self, tile):
        """设置获胜手牌"""
        self.__win_tile = tile

    def get_win_tile(self):
        return self.__win_tile

    def set_table_tile_mgr(self, mgr):
        """设置手牌管理器"""
        self.__table_tile_mgr = mgr

    def get_table_tile_mgr(self):
        return self.__table_tile_mgr

    def set_win_rule_mgr(self, mgr):
        self.__win_rule_mgr = mgr

    def get_win_rule_mgr(self):
        return self.__win_rule_mgr

    def set_win_pattern(self, pattern):
        """设置赢牌手牌组合"""
        self.__win_pattern = pattern

    def get_win_pattern(self):
        return self.__win_pattern

    def get_score_by_seat_id(self, seat_id):
        """
        根据座位号获得玩家结算的积分
        @:param seat_id 玩家座位号
        """
        return self.__results.score[seat_id] or 0

    def calc_gang(self):
        """计算杠的输赢"""

        # 明杠暗杠统计
        resultStat = [[] for _ in range(self.__player_count)]

        self.__results[self.KEY_TYPE] = HYOneBudget.KEY_TYPE_NAME_GANG
        base = self.__table_config.get(MTDefine.GANG_BASE, 0)
        if self.style == MPlayerTileGang.AN_GANG:
            self.__results[self.KEY_NAME] = "暗杠"
            base *= 2
            resultStat[self.__active_seat_id].append({HYOneBudget.STAT_ANGANG: 1})
        else:
            self.__results[self.KEY_NAME] = "明杠"
            resultStat[self.__active_seat_id].append({HYOneBudget.STAT_MINGGANG: 1})

        if self.__passvie_seat_id != self.__active_seat_id:
            scores = [0 for _ in range(self.__player_count)]
            scores[self.__active_seat_id] = base
            scores[self.__passvie_seat_id] = -base
        else:
            scores = [-base for _ in range(self.__player_count)]
            scores[self.__active_seat_id] = (self.__player_count - 1) * base

        HYLog.debug('MOneResult.calcGang gangType:', self.__results[self.KEY_NAME], ' scores', scores)
        self.__results[self.KEY_SCORE] = scores
        self.__results[self.KEY_STAT] = resultStat

    def calc_win(self):
        """计算和牌的输赢"""
        pass

    def calc_score(self):
        """计算输赢数值"""
        # 放在这里补充环境数据，要么不方便单元测试
        self.__player_all_tiles

        for player in self.__table_tile_mgr.players:
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

        HYLog.info('MKawuxingOneResult.calcScore __player_all_tiles=', self.__player_all_tiles)
        HYLog.info('MKawuxingOneResult.calcScore __player_all_tiles_arr=', self.__player_all_tiles_arr)
        HYLog.info('MKawuxingOneResult.calcScore __player_hand_tiles_with_hu=', self.__player_hand_tiles_with_hu)
        HYLog.info('MKawuxingOneResult.calcScore __player_ting_liang=', self.__player_ting_liang)

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
        HYLog.info('MKawuxingOneResult.calcScore __win_patterns=', self.__win_patterns)

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
        HYLog.info('MKawuxingOneResult.calcWin score:', score)

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
        HYLog.debug('MYunnanOneResult calcScore:KEY_SCORE:', self.results[self.KEY_SCORE])
        HYLog.debug('MYunnanOneResult calcScore:KEY_NAME:', self.results[self.KEY_NAME])
        HYLog.debug('MYunnanOneResult calcScore:KEY_TYPE:', self.results[self.KEY_TYPE])
        HYLog.debug('MYunnanOneResult calcScore:KEY_WIN_MODE:', self.results[self.KEY_WIN_MODE])
        HYLog.debug('MYunnanOneResult calcScore:KEY_FAN_PATTERN:', self.results[self.KEY_FAN_PATTERN])
        HYLog.debug('MYunnanOneResult calcScore:KEY_STAT:', self.results[self.KEY_STAT])
