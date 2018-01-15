# -*- coding=utf-8
'''
Created on 2017年3月7日

结算

@author: nick.kai.lee
'''
from difang.majiang2.player.player import MPlayerTileGang
from difang.majiang2.table.table_config_define import MTDefine
from freetime.util import log as ftlog


class HYWinLoseResult(object):
    # 杠牌，刮风下雨
    RESULT_GANG = 1
    # 和牌
    RESULT_WIN = 2
    # 流局
    RESULT_FLOW = 3

    TYPE = {"WIN": 2, "FLOW": 3}

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
        super(HYWinLoseResult, self).__init__()

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

        """
        1）通过获胜手牌与获胜手牌组合判断是否是夹牌
        2）通过获胜手牌组合判断是否是大扣等
        """
        # 获胜的手牌组合
        self.__win_pattern = None
        # 仅由获胜牌组合定义的番型，比如九莲宝灯，金钩和，七对等
        self.__win_pattern_type = None

        self.__results = {}  # 结果

        self.__win_fan_pattern = []

        self.__player_hand_tiles = []  # 所有玩家手牌
        self.__player_all_tiles = []  # 所有玩家的所有牌，按手牌格式的数组
        self.__player_all_tiles_arr = []  # 所有玩家的所有牌，合到一个数组
        self.__player_gang_tiles = []  # 所有玩家杠牌情况

        self.__stat_type = {
            self.STAT_ZIMO: {"name": "自摸"},
            self.STAT_DIANPAO: {"name": "点炮"},
            self.STAT_MINGGANG: {"name": "明杠"},
            self.STAT_ANGANG: {"name": "暗杠"},
            self.STAT_ZUIDAFAN: {"name": "最大番"},
        }

        # 倍数
        self.__multiple = 1

    def get_multiple(self):
        return self.__multiple

    def set_multiple(self, value):
        self.__multiple = value

    @property
    def statType(self):
        return self.__stat_type

    def winFanPattern(self):
        return self.__win_fan_pattern

    def clearWinFanPattern(self):
        self.__win_fan_pattern = []

    def addWinFanPattern(self, name, index):
        self.__win_fan_pattern.append([name.strip(), str(index) + "番"])

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
        if self.__win_pattern:
            obj['winPattern'] = self.__win_pattern
        if self.__win_pattern_type:
            obj['winPatternType'] = self.__win_pattern_type
        if self.__player_count:
            obj['playCount'] = self.__player_count
        if self.style:
            obj['style'] = self.style
        if self.__table_config:
            obj['tableConfig'] = self.__table_config
        ftlog.debug('HYWinLoseResult.serialize: ', obj)

    def unserialize(self, obj):
        """反序列化"""
        ftlog.debug('HYWinLoseResult.unSerialize: ', obj)
        self.__play_mode = obj.get('playMode', None)
        self.__banker_seat_id = obj.get('bankerSeatId', None)
        self.__active_seat_id = obj.get('winSeatId', None)
        self.__passvie_seat_id = obj.get('lastSeatId', None)
        self.__win_tile = obj.get('winTile', 0)
        self.__aciton_id = obj.get('actionID', 0)
        self.__win_pattern = obj.get('winPattern', [])
        self.__win_pattern_type = obj.get('winPatternType', 0)
        self.__player_count = obj.get('playCount', 4)
        self.__table_config = obj.get('tableConfig', None)

    def get_player_count(self):
        return self.__player_count

    def set_player_count(self, count):
        self.__player_count = count

    @property
    def playerAllTiles(self):
        return self.__player_all_tiles

    def setPlayerAllTiles(self, playerAllTiles):
        self.__player_all_tiles = playerAllTiles

    @property
    def playerGangTiles(self):
        return self.__player_gang_tiles

    def setPlayerGangTiles(self, playerGangTiles):
        self.__player_gang_tiles = playerGangTiles

    def get_results(self):
        return self.__results

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

    def setWinPatternType(self, wType):
        """原始番型"""
        self.__win_pattern_type = wType

    @property
    def winPatternType(self):
        return self.__win_pattern_type

    def calcGang(self):
        """计算杠的输赢"""

        # 明杠暗杠统计
        resultStat = [[] for _ in range(self.__player_count)]

        self.__results[self.KEY_TYPE] = HYWinLoseResult.KEY_TYPE_NAME_GANG
        base = self.__table_config.get(MTDefine.GANG_BASE, 0)
        if self.style == MPlayerTileGang.AN_GANG:
            self.__results[self.KEY_NAME] = "暗杠"
            base *= 2
            resultStat[self.__active_seat_id].append({HYWinLoseResult.STAT_ANGANG: 1})
        else:
            self.__results[self.KEY_NAME] = "明杠"
            resultStat[self.__active_seat_id].append({HYWinLoseResult.STAT_MINGGANG: 1})

        if self.__passvie_seat_id != self.__active_seat_id:
            scores = [0 for _ in range(self.__player_count)]
            scores[self.__active_seat_id] = base
            scores[self.__passvie_seat_id] = -base
        else:
            scores = [-base for _ in range(self.__player_count)]
            scores[self.__active_seat_id] = (self.__player_count - 1) * base

        ftlog.debug('MOneResult.calcGang gangType:', self.__results[self.KEY_NAME], ' scores', scores)
        self.__results[self.KEY_SCORE] = scores
        self.__results[self.KEY_STAT] = resultStat

    def calcWin(self):
        """计算和牌的输赢"""
        pass

    def calcScore(self):
        """计算输赢数值"""
        pass
