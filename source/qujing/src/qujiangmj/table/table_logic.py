# -*- coding=utf-8
'''
Created on 2016年9月23日
麻将的逻辑类，只关心麻将的核心玩法
@author: zhaol
'''
import copy

import poker.util.timestamp as pktimestamp
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.banker.banker_factory import BankerFactory
from difang.majiang2.chi_rule.chi_rule import MChiRule
from difang.majiang2.gang_rule.gang_rule import MGangRule
from difang.majiang2.msg_handler.msg_factory import MsgFactory
from difang.majiang2.peng_rule.peng_rule import MPengRule
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.player.player import MPlayer, MPlayerTileGang
from difang.majiang2.table.friend_table_define import MFTDefine
from difang.majiang2.table.run_mode import MRunMode
from difang.majiang2.table.table_config_define import MTDefine
from difang.majiang2.table.table_logic_style import AbstractMajiangTableLogic
from difang.majiang2.table_state.state import MTableState
from difang.majiang2.table_state.state_factory import TableStateFactory
from difang.majiang2.table_state_processor.add_card_processor import MAddCardProcessor
from difang.majiang2.table_state_processor.drop_card_processor import MDropCardProcessor
from difang.majiang2.table_state_processor.extend_info import MTableStateExtendInfo
from difang.majiang2.table_state_processor.qiang_gang_hu_processor import MQiangGangHuProcessor
from difang.majiang2.table_statistic.statistic import MTableStatistic
from difang.majiang2.table_tile.table_tile_factory import MTableTileFactory
from difang.majiang2.tile.tile import MTile
from difang.majiang2.win_loose_result.one_result import MOneResult
from difang.majiang2.win_loose_result.one_result_factory import MOneResultFactory
from difang.majiang2.win_loose_result.round_results import MRoundResults
from difang.majiang2.win_loose_result.table_results import MTableResults
from difang.majiang2.win_rule.win_rule import MWinRule
from difang.majiang2.win_rule.win_rule_factory import MWinRuleFactory
from freetime.util import log as ftlog


class QJMajiangTableLogic(AbstractMajiangTableLogic):
    def __init__(self, playerCount, playMode, runMode):
        super(QJMajiangTableLogic, self).__init__()
        # 用户数量
        self.__playerCount = playerCount
        # 玩法
        self.__playMode = playMode
        # 运行方式
        self.__run_mode = runMode
        # 牌桌配置
        self.__table_config = {}
        # 根据玩法获取发牌器
        self.__table_tile_mgr = MTableTileFactory.getTableTileMgr(self.__playerCount, self.__playMode, runMode)
        # 本局玩家
        self.__players = [None for _ in range(self.playerCount)]
        # 手牌张数
        self.__hand_card_count = 13
        # 庄家
        self.__banker_mgr = BankerFactory.getBankerAI(self.playMode)
        # 当前操作座位号
        self.__cur_seat = 0
        # 上牌状态
        self.__add_card_processor = MAddCardProcessor()
        # 出牌状态
        self.__drop_card_processor = MDropCardProcessor(self.playerCount, playMode)
        self.__drop_card_processor.setTableTileMgr(self.tableTileMgr)
        # 抢杠和状态
        self.__qiang_gang_hu_processor = MQiangGangHuProcessor(self.playerCount)
        # 和牌状态
        self.__table_win_state = MTableState.TABLE_STATE_NONE
        # 吃牌AI
        self.__chi_rule_mgr = MChiRule()
        self.__chi_rule_mgr.setTableTileMgr(self.__table_tile_mgr)
        # 碰牌AI
        self.__peng_rule_mgr = MPengRule()
        self.__peng_rule_mgr.setTableTileMgr(self.__table_tile_mgr)
        # 杠牌AI
        self.__gang_rule_mgr = MGangRule()
        self.__gang_rule_mgr.setTableTileMgr(self.__table_tile_mgr)
        # 消息处理者
        self.__msg_processor = MsgFactory.getMsgProcessor(runMode)
        self.__msg_processor.setTableTileMgr(self.tableTileMgr)
        self.__msg_processor.setGangRuleMgr(self.__gang_rule_mgr)
        # 和牌管理器
        self.__win_rule_mgr = MWinRuleFactory.getWinRule(self.playMode)
        self.__win_rule_mgr.setTableTileMgr(self.__table_tile_mgr)
        # 牌桌状态机
        self.__table_stater = TableStateFactory.getTableStates(self.playMode)
        # 听牌管理器
        self.__ting_rule_mgr = None

        # 牌桌最新操作标记，摸牌actionID加1，出牌actionID加1
        self.__action_id = 0
        # 圈/风
        self.__quan_men_feng = 0
        # 算分结果
        self.__round_result = None
        # 牌桌结果
        self.__table_result = MTableResults()
        # 记录上一局的结果
        self.__win_loose = 0
        # 记录上一局的胜利者
        self.__last_win_seatId = 0
        # 杠牌记录,用来判定杠上花和杠上炮,每次成功杠牌后设置,每次出牌后或者抢杠胡后清空,设置值为座位号,默认值-1
        self.__latest_gang_state = -1
        # 牌桌观察者
        self.__table_observer = None
        # 一炮多响时用于存储胡牌人位置的数组
        self.__win_seats = []
        # 漏胡时用于存储出牌时能胡的人的数组
        self.__pass_hu_seats = []
        # 用于存储本局牌局上传地址的数组
        self.__record_urls = []
        # 用于存储每人网络状况的字典
        self.__player_ping = {}
        ftlog.debug('qujingLogicTableInit')

    @property
    def recordUrls(self):
        return self.__record_urls

    def setLatestGangState(self, state):
        self.__latest_gang_state = state

    @property
    def latestGangState(self):
        return self.__latest_gang_state

    @property
    def tableResult(self):
        return self.__table_result

    def nextRound(self):
        """下一把"""
        self.__cur_seat = 0
        self.__add_card_processor.reset()
        self.__drop_card_processor.reset()
        self.__qiang_gang_hu_processor.reset()
        self.__table_win_state = MTableState.TABLE_STATE_NONE
        ftlog.debug("kazhuocheck1", self.__table_win_state)
        self.__action_id = 0
        self.__quan_men_feng = 0
        self.__win_seats = []
        self.__pass_hu_seats = []
        self.__table_tile_mgr.reset()

        for player in self.player:
            if player:
                player.reset()

    @property
    def tableObserver(self):
        return self.__table_observer

    def setTableObserver(self, observer):
        self.__table_observer = observer

    @property
    def roundResult(self):
        return self.__round_result

    @property
    def runMode(self):
        return self.__run_mode

    def resetGame(self, winLoose):
        """重置游戏"""
        self.__win_loose = winLoose
        self.__last_win_seatId = self.curSeat
        # 当前游戏信息备忘
        nowBanker = self.queryBanker()
        userIds = self.getBroadCastUIDs()
        # 确定下一局的庄家
        curRoundCount = self.tableConfig.get(MFTDefine.CUR_ROUND_COUNT, 0)
        banker, remains, noresults = self.__banker_mgr.getBanker(self.__playerCount
                                                                 , (curRoundCount == 0)
                                                                 , self.__win_loose
                                                                 , self.__last_win_seatId)
        ftlog.debug('Remains:', remains, 'Banker:', banker, 'Noresults:', noresults, ' OldBanker:', nowBanker)
        if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
            for player in self.player:
                player.setHasHu(False)
        # 标记游戏结束状态
        self.__table_win_state = MTableState.TABLE_STATE_GAME_OVER

        # 调整到gameover状态之后
        recordName = self.getCreateTableRecordName()
        self.msgProcessor.saveRecord(recordName, self.__record_urls)
        # 游戏结束后，记录牌局事件
        if self.tableObserver:
            # 游戏事件记录
            self.tableObserver.onBeginGame(userIds, nowBanker)
        # self.tableObserver.onGameEvent(MTableStatistic.TABLE_WIN, self.player)
        # 清空__round_result 否则在一局结束下局未开始时断线重连会取到错误的积分数据
        self.__round_result = MRoundResults()
        # 清空上一局胜者数据
        self.__win_seats = []
        # 清空出牌时漏胡者数据
        self.__pass_hu_seats = []

    def reset(self):
        """重置"""
        self.nextRound()
        self.__banker_mgr.reset()
        self.__players = [None for _ in range(self.playerCount)]
        self.__round_result = None
        self.__table_result.reset()
        self.__record_urls = []
        ftlog.debug('MajiangTableLogic.reset call.....')

    @property
    def tingRule(self):
        """听牌规则管理器"""
        return self.__ting_rule_mgr

    @property
    def addCardProcessor(self):
        """摸牌管理器"""
        return self.__add_card_processor

    @property
    def dropCardProcessor(self):
        """出牌管理器"""
        return self.__drop_card_processor

    @property
    def qiangGangHuProcessor(self):
        return self.__qiang_gang_hu_processor

    @property
    def playerCount(self):
        """获取本局玩家数量"""
        return self.__playerCount

    @property
    def msgProcessor(self):
        """获取消息处理对象"""
        return self.__msg_processor

    @property
    def actionID(self):
        """获取当前的操作标记"""
        return self.__action_id

    @property
    def playMode(self):
        """获取本局玩法"""
        return self.__playMode

    @property
    def player(self):
        """获取玩家"""
        return self.__players

    @property
    def quanMenFeng(self):
        """获取圈/风设置"""
        return self.__quan_men_feng

    @property
    def handCardCount(self):
        """获取初始手牌张数
        """
        return self.__hand_card_count

    @property
    def curSeat(self):
        """当前操作座位号
        """
        return self.__cur_seat

    @property
    def tableTileMgr(self):
        return self.__table_tile_mgr

    def isFriendTablePlaying(self):
        if self.getTableConfig(MFTDefine.IS_CREATE, 0):
            curCount = self.getTableConfig(MFTDefine.CUR_ROUND_COUNT, 0)
            ftlog.debug('MajiangTableLogic.isPlaying friendTable curCount:', curCount
                        , ' totalCount:', self.getTableConfig(MFTDefine.ROUND_COUNT, 0))
            return (curCount > 0) and (curCount != self.getTableConfig(MFTDefine.ROUND_COUNT, 0))

        return self.isPlaying()

    def isPlaying(self):
        """游戏是否开始"""
        ftlog.debug('tableLogic.isPlaying... self.__table_win_state:', self.__table_win_state)
        if self.__table_win_state == MTableState.TABLE_STATE_NEXT:
            return True
        return False

    def curState(self):
        """当前状态
        """
        return self.__add_card_processor.getState() \
               + self.__drop_card_processor.getState() \
               + self.__table_win_state \
               + self.__qiang_gang_hu_processor.getState()

    def nowPlayerCount(self):
        """座位上的人数
        """
        return len(self.__players)

    def setCurSeat(self, seat):
        """设置当前操作座位号
        """
        self.__cur_seat = seat

    def setHandCardCount(self, count):
        """设置初始手牌张数
        """
        self.__hand_card_count = count

    def setTableConfig(self, config):
        """设置牌桌配置"""
        self.__table_config = config
        ftlog.info('MajiangTableLogic.setTableConfig:', config)

        # 将TableConfig传递到tableTileMgr，方便各种特殊操作的判断
        self.tableTileMgr.setTableConfig(config)

        cardCount = self.getTableConfig(MTDefine.HAND_COUNT, MTDefine.HAND_COUNT_DEFAULT)
        self.setHandCardCount(cardCount)

        if MFTDefine.ROUND_COUNT not in self.__table_config:
            self.__table_config[MFTDefine.ROUND_COUNT] = 0

        if MFTDefine.CUR_ROUND_COUNT not in self.__table_config:
            self.__table_config[MFTDefine.CUR_ROUND_COUNT] = 0

        if MFTDefine.CARD_COUNT not in self.__table_config:
            self.__table_config[MFTDefine.CARD_COUNT] = 0

        if MFTDefine.LEFT_CARD_COUNT not in self.__table_config:
            self.__table_config[MFTDefine.LEFT_CARD_COUNT] = 0

        if MTDefine.TRUSTTEE_TIMEOUT not in self.__table_config:
            self.__table_config[MTDefine.TRUSTTEE_TIMEOUT] = 1

        if self.checkTableState(MTableState.TABLE_STATE_TING):
            self.__ting_rule_mgr.setTableConfig(config)

    def getTableConfig(self, key, default):
        """获取牌桌配置"""
        value = self.__table_config.get(key, default)
        ftlog.info('MajiangTableLogic.getTableConfig key:', key, ' value:', value)
        return value

    @property
    def tableConfig(self):
        return self.__table_config

    def queryBanker(self):
        """查询庄家
        """
        return self.__banker_mgr.queryBanker()

    def getPlayerState(self, seatId):
        """获取用户状态"""
        if seatId >= self.__playerCount:
            return None

        return self.__players[seatId].state

    def getPlayer(self, seatId):
        """获取用户名称"""
        return self.__players[seatId]

    def addPlayer(self, player, seatId, isReady=True, isAutoDecide=False):
        """添加玩家"""
        if player in self.__players:
            ftlog.debug('already in table...')
            return
        if seatId >= self.__playerCount:
            ftlog.debug('no seat any more...')
            return

        ftlog.debug('MajiangTableLogic.addPlayer name:', player.name, ' seatId:', seatId, ' isReady:', isReady,
                    ' isAutoDecide:', isAutoDecide)

        self.__players[seatId] = player
        self.__msg_processor.setPlayers(self.player)
        self.__add_card_processor.setPlayers(self.player)
        self.__drop_card_processor.setPlayers(self.player)
        self.__qiang_gang_hu_processor.setPlayers(self.player)
        player.setSeatId(seatId)
        player.setAutoDecide(isAutoDecide)
        self.playerReady(seatId, isReady)

    def removePlayer(self, seatId):
        """删除玩家"""
        self.__players[seatId] = None
        self.__msg_processor.setPlayers(self.__players)
        if self.isEmpty():
            self.reset()

    def isEmpty(self):
        """是否空桌"""
        for player in self.__players:
            if player:
                return False
        return True

    def setAutoDecideValue(self, seatId, adValue):
        """设置玩家的托管状态"""
        if self.__players[seatId]:
            if not self.getTableConfig(MFTDefine.IS_CREATE, 0):
                ftlog.debug('MajiangTableLogic.setAutoDecideValue not in createTable Mode')
                self.__players[seatId].setAutoDecide(adValue)

    def getBroadCastUIDs(self, filter_id=-1):
        """获取待广播的UID集合，不包括filter_id及机器人
        不需要向机器人发送消息
        """
        uids = []
        for player in self.__players:
            if player and (not player.isRobot()) and (player.userId != filter_id):
                uids.append(player.userId)
        return uids

    def getSeats(self):
        seats = [0 for _ in range(self.playerCount)]
        for index, _ in enumerate(seats):
            if self.__players[index]:
                seats[index] = self.__players[index].userId
        return seats

    def isGameOver(self):
        """是否已结束"""
        return self.__table_win_state == MTableState.TABLE_STATE_GAME_OVER

    def shuffle(self):
        """洗牌
        """
        if len(self.__players) != self.__playerCount:
            ftlog.debug('seats error...')
            return

        banker = self.__banker_mgr.queryBanker()

        # 根据需要与规则计算好牌点和初始张数
        # 好牌点1，放在发牌的最前面，table负责将好牌派发给正确的人
        # 手牌张数13
        self.__table_tile_mgr.shuffle(1, self.__hand_card_count)
        ftlog.debug('Round Tiles:', self.__table_tile_mgr.getTiles(), "len of round",
                    len(self.__table_tile_mgr.getTiles()))

        # 发牌
        self.setCurSeat(banker)
        cur_seat = self.curSeat

        # 下发赖子
        magicFactors = []
        magicTiles = self.tableTileMgr.getMagicTiles()
        for magicTile in magicTiles:
            if magicTile >= MTile.TILE_DONG_FENG:
                continue
            if magicTile % 10 == 1:
                magicFactors.append(magicTile + 8)
            else:
                magicFactors.append(magicTile - 1)
        if len(magicTiles) > 0:
            self.msgProcessor.table_call_laizi(self.getBroadCastUIDs(), magicTiles, magicFactors)

        for _ in range(self.__playerCount):
            self.tableTileMgr.clearPassHuBySeatId(cur_seat)
            handCards = self.__table_tile_mgr.popTile(self.__hand_card_count)
            curPlayer = self.__players[cur_seat]
            curPlayer.actionBegin(handCards)
            # 发送发牌的消息
            self.__msg_processor.sendMsgInitTils(curPlayer.copyHandTiles()
                                                 , self.__banker_mgr.queryBanker()
                                                 , curPlayer.userId
                                                 , curPlayer.curSeatId)
            cur_seat = (cur_seat + 1) % self.__playerCount
        pigus = self.tableTileMgr.getPigus()
        if pigus and len(pigus) > 0:
            uids = self.getBroadCastUIDs()
            self.msgProcessor.table_call_fanpigu(pigus, uids)

    def checkTableState(self, state):
        """校验牌桌状态机
        """
        return state & self.__table_stater.states

    def popOneTile(self, seatId):
        """获取后面的length张牌"""
        tiles = self.tableTileMgr.popTile(1)
        if len(tiles) == 0:
            return None
        else:
            self.tableTileMgr.setAddTileInfo(tiles[0], seatId)
        return tiles[0]

    def haveRestTile(self):
        """检查牌堆剩余的牌"""
        restTilesCount = self.tableTileMgr.getCheckFlowCount()
        if restTilesCount <= 0:
            ftlog.debug("haveRestTile no tile left")
            return False
        else:
            return True

    def processAddTile(self, cp, state, special_tile=None):
        """上一张牌并处理
        参数：
            cp - 当前玩家
            tile - 当前上牌
        """
        isAfterGang = state == MTableState.TABLE_STATE_GANG
        # 从抢杠听转过来听牌的处理需求
        mustTing = state & MTableState.TABLE_STATE_GRABTING

        tile = 0
        if self.checkTableState(MTableState.TABLE_STATE_FANPIGU) and special_tile:
            tile = special_tile
            self.tableTileMgr.updatePigu(special_tile)
            pigus = self.tableTileMgr.getPigus()
            self.msgProcessor.table_call_fanpigu(pigus, self.getBroadCastUIDs())
        else:
            if self.haveRestTile():
                tile = self.popOneTile(cp.curSeatId)
            else:
                # 处理流局
                self.gameFlow(cp.curSeatId)

        if not tile:
            return

        cp.actionAdd(tile)
        changeInfo = {}
        change = False
        # 换牌要在摸牌加入手牌之后,昭通现在特殊处理下,只在碰牌和杠牌里找
        if self.tableTileMgr.needChangeMagic():
            # 已经确认了摸的牌,判断下是否需要换赖子
            magicTiles = self.tableTileMgr.getMagicTiles()
            playerTiles = cp.copyTiles()
            changeType = ""
            patternInfo = []
            if tile not in magicTiles and tile in playerTiles[MHand.TYPE_HAND]:
                if not change:
                    for peng in playerTiles[MHand.TYPE_PENG]:
                        if tile in peng:
                            resultPeng, newPengPattern = cp.updateTile(tile, self.tableTileMgr)
                            if resultPeng:
                                change = True
                                changeType = 'peng'
                                patternInfo.append(peng)
                                patternInfo.append(newPengPattern['new'])
                                break;
                if not change:
                    for gang in playerTiles[MHand.TYPE_GANG]:
                        if tile in gang['pattern']:
                            resultGang, newGangPattern = cp.updateTile(tile, self.tableTileMgr)
                            if resultGang:
                                change = True
                                changeType = 'gang'
                                patternInfo.append(gang['pattern'])
                                patternInfo.append(newGangPattern['new']['pattern'])
                                break;

            if change and len(magicTiles) > 0:
                tile = magicTiles[0]
                if changeType == 'gang':
                    changeInfo = {
                        'gang': {"pattern": patternInfo, "style": 1}
                    }
                elif changeType == 'peng':
                    changeInfo = {
                        'peng': patternInfo
                    }
                    # 判断是不是第一次摸牌,是的话置一下状态
        if self.tableTileMgr.firstAdd[cp.curSeatId] == 0:
            self.tableTileMgr.setFirstAddBySeatId(cp.curSeatId)

        # 设置上一手杠状态
        if self.latestGangState != cp.curSeatId:
            ftlog.debug("gangTileclearLatestGangStatebefore = ", self.latestGangState)
            self.setLatestGangState(-1)
            self.__win_rule_mgr.setLastGangSeat(-1)
            ftlog.debug("gangTileclearLatestGangStateafter = ", self.latestGangState)

        if self.__win_rule_mgr.isPassHu:
            # 清空之前漏胡的牌
            ftlog.debug("passHuClear", cp.curSeatId)
            self.tableTileMgr.clearPassHuBySeatId(cp.curSeatId)

        self.__action_id += 1

        # 曲靖麻将判断四幺鸡,注意在上一步tile加到cp手上以后再调用
        if self.__win_rule_mgr.isAddHu(cp, tile):
            state = MTableState.TABLE_STATE_HU
            exInfo = MTableStateExtendInfo()
            timeOut = self.__table_stater.getTimeOutByState(state)
            self.addCardProcessor.initProcessor(self.actionID, state, cp.curSeatId, tile, exInfo, timeOut)
            # 直接胡牌
            self.gameWin(cp.curSeatId, tile)
            return

        # 扩展数据
        exInfo = MTableStateExtendInfo()
        # 判断和之外的状态，是否可听，可杠
        state = MTableState.TABLE_STATE_NEXT

        # 牌桌变为等待出牌状态
        if (not mustTing) and self.checkTableState(MTableState.TABLE_STATE_DROP):
            state = MTableState.TABLE_STATE_DROP

        # 自己上的牌，判断杠/胡，不需要判断吃。判断暗杠
        if (not mustTing) and (not cp.isTing()) and self.checkTableState(MTableState.TABLE_STATE_GANG):
            tiles = cp.copyTiles()
            gangs = self.__gang_rule_mgr.hasGang(tiles, tile, MTableState.TABLE_STATE_NEXT)

            if self.checkTableState(MTableState.TABLE_STATE_FANPIGU):
                pigus = self.tableTileMgr.getPigus()
                exInfo.appendInfo(MTableState.TABLE_STATE_FANPIGU, pigus)

            for gang in gangs:
                # 可以暗杠，给用户杠的选择，听牌后，是否开暗杠要看是否影响听牌结果。
                if cp.canGang(gang, True):
                    state = state | MTableState.TABLE_STATE_GANG
                    exInfo.appendInfo(MTableState.TABLE_STATE_GANG, gang)

        # 判断是否自摸和牌
        magics = self.tableTileMgr.getMagicTiles(cp.isTing())
        # 给winMgr传入当前杠牌的座位号
        self.__win_rule_mgr.setLastGangSeat(self.latestGangState)
        winResult, winPattern = self.__win_rule_mgr.isHu(cp.copyTiles(), tile, cp.isTing(), MWinRule.WIN_BY_MYSELF,
                                                         magics, cp.winNodes)
        ftlog.debug('MajiangTable.processAddTile winResult:', winResult, ' winPattern:', winPattern)

        if winResult and self.checkTableState(MTableState.TABLE_STATE_HU):
            # 可以和，给用户和的选择
            state = state | MTableState.TABLE_STATE_HU
            winInfo = {}
            winInfo['tile'] = tile
            if isAfterGang:
                winInfo['gangKai'] = 1
            exInfo.appendInfo(MTableState.TABLE_STATE_HU, winInfo)
            # 摸牌只有一个人胡,添加前重置
            self.__pass_hu_seats = []
            if cp.curSeatId not in self.__pass_hu_seats:
                self.__pass_hu_seats.append(cp.curSeatId)

        # 发牌处理
        ftlog.debug('MajiangTableLogic.processAddTile cp = :', cp.copyHandTiles())
        ftlog.debug('MajiangTableLogic.processAddTile tile:', tile)
        ftlog.debug('MajiangTableLogic.processAddTile extendInfo:', exInfo)
        timeOut = self.__table_stater.getTimeOutByState(state)
        self.addCardProcessor.initProcessor(self.actionID, state, cp.curSeatId, tile, exInfo, timeOut)
        self.__drop_card_processor.reset()
        for index in range(self.__playerCount):
            ftlog.debug('MajiangTableLogic.gangTileErrorCheck self.__cur_seat=:', (self.__cur_seat), "index = ", index)
            if self.__cur_seat == index:
                if change:
                    self.__msg_processor.table_call_add_card(self.__players[index]
                                                             , tile, state, index
                                                             , timeOut
                                                             , self.actionID
                                                             , exInfo
                                                             , changeInfo)
                else:
                    self.__msg_processor.table_call_add_card(self.__players[index]
                                                             , tile, state, index
                                                             , timeOut
                                                             , self.actionID
                                                             , exInfo)
            else:
                if change:
                    self.__msg_processor.table_call_add_card_broadcast(self.curSeat
                                                                       , timeOut
                                                                       , self.actionID
                                                                       , self.__players[index].userId
                                                                       , tile
                                                                       , changeInfo)
                else:
                    self.__msg_processor.table_call_add_card_broadcast(self.curSeat
                                                                       , timeOut
                                                                       , self.actionID
                                                                       , self.__players[index].userId
                                                                       , tile)

    def getCreateTableInfo(self, isTableInfo=False):
        """获取自建桌信息"""
        ctInfo = None
        cFinal = 0
        curCount = self.tableConfig[MFTDefine.CUR_ROUND_COUNT]
        if isTableInfo and (self.__table_win_state != MTableState.TABLE_STATE_NEXT):
            curCount += 1
        totalCount = self.tableConfig[MFTDefine.ROUND_COUNT]
        if curCount >= totalCount:
            curCount = totalCount

        if totalCount == curCount:
            cFinal = 1

        if self.tableConfig.get(MFTDefine.IS_CREATE, 0):
            ctInfo = {"create_table_no": self.tableConfig[MFTDefine.FTID],
                      "time": pktimestamp.getCurrentTimestamp(),
                      "create_final": cFinal,
                      "create_now_cardcount": curCount,
                      "create_total_cardcount": self.tableConfig[MFTDefine.ROUND_COUNT],
                      "itemParams": self.getTableConfig(MFTDefine.ITEMPARAMS, {}),
                      "hostUserId": self.getTableConfig(MFTDefine.FTOWNER, 0),
                      'create_table_desc_list': self.getTableConfig(MFTDefine.CREATE_TABLE_DESCS, []),
                      'create_table_play_desc_list': self.getTableConfig(MFTDefine.CREATE_TABLE_PLAY_DESCS, []),
                      }
        return ctInfo

    def getCreateTableRecordName(self):
        """获取牌桌记录信息"""
        if self.runMode == MRunMode.CONSOLE:
            return 'console.json'

        curCount = self.tableConfig[MFTDefine.CUR_ROUND_COUNT]
        totalCount = self.tableConfig[MFTDefine.ROUND_COUNT]
        recordName = '%s-%s-%d-%d-%d' % (
            self.playMode, self.tableConfig[MFTDefine.FTID], curCount, totalCount, pktimestamp.getCurrentTimestamp())
        ftlog.debug('MajiangTableLogic.getCreateTableRecordName recordName:', recordName)
        return recordName

    # 大结算时需要返回给客户端的统计信息
    def getCreateExtendBudgets(self, score):
        createExtendBudgets = [{} for _ in range(self.playerCount)]
        # roundResult 列表
        allResults = []
        tableResults = self.__table_result.results
        ftlog.debug('MajiangTableLogic.getCreateExtendBudgets roundResult count', len(tableResults))
        for roundResult in self.__table_result.results:
            ftlog.debug('MajiangTableLogic.getCreateExtendBudgets roundResult ...')
            for oneResult in roundResult.roundResults:
                allResults.append(oneResult)
                if MOneResult.KEY_SCORE in oneResult.results:
                    score.append(oneResult.results[MOneResult.KEY_SCORE])
                ftlog.debug('MajiangTableLogic.getCreateExtendBudgets oneResult ...score:', score)

        ziMoMaxValue = 0
        ziMoMaxSeatId = -1
        dianPaoMaxValue = 0
        dianPaoMaxSeatId = -1
        for seatId in range(self.playerCount):
            extendBudget = {}
            extendBudget["sid"] = seatId
            ziMoValue = 0
            dianPaoValue = 0
            mingGangValue = 0
            anGangValue = 0
            zuidaFanValue = 0
            # statistics
            statisticInfo = []
            # one result
            for oneResult in allResults:
                ftlog.debug('MajiangTableLogic.getCreateExtendBudgets seatId:', seatId)
                # statScore = oneResult.results[MOneResult.KEY_SCORE]
                # totalDeltaScore += statScore[seatId]
                stats = [[] for _ in range(self.__playerCount)]
                if MOneResult.KEY_STAT in oneResult.results:
                    stats = oneResult.results[MOneResult.KEY_STAT]
                    playerStats = stats[seatId]
                for stat in playerStats:
                    if MOneResult.STAT_ZIMO in stat:
                        ziMoValue += stat[MOneResult.STAT_ZIMO]

                    if MOneResult.STAT_DIANPAO in stat:
                        dianPaoValue += stat[MOneResult.STAT_DIANPAO]

                    if self.playMode == MPlayMode.HAERBIN:
                        if MOneResult.STAT_MINGGANG in stat:
                            mingGangValue += stat[MOneResult.STAT_MINGGANG]

                        if MOneResult.STAT_ANGANG in stat:
                            anGangValue += stat[MOneResult.STAT_ANGANG]

                    if MOneResult.STAT_ZUIDAFAN in stat:
                        if stat[MOneResult.STAT_ZUIDAFAN] > zuidaFanValue:
                            zuidaFanValue = stat[MOneResult.STAT_ZUIDAFAN]

            oneResultForName = MOneResult()
            statisticInfo.append({"desc": oneResultForName.statType[MOneResult.STAT_ZIMO]["name"], "value": ziMoValue})
            ftlog.debug('MTableLogic.createExtendBudgets seatId', seatId, ' ziMoValue:', ziMoValue)
            statisticInfo.append(
                {"desc": oneResultForName.statType[MOneResult.STAT_DIANPAO]["name"], "value": dianPaoValue})
            ftlog.debug('MTableLogic.createExtendBudgets seatId', seatId, ' dianPaoValue:', dianPaoValue)
            # extendBudget["total_delta_score"] = totalDeltaScore
            if self.__table_result.score and (len(self.__table_result.score) > seatId):
                extendBudget["total_delta_score"] = self.__table_result.score[seatId]
            else:
                extendBudget["total_delta_score"] = 0
            extendBudget["statistics"] = statisticInfo
            # dianpao_most zimo_most
            extendBudget["head_mark"] = ""
            createExtendBudgets[seatId] = extendBudget
            if ziMoValue > ziMoMaxValue:
                ziMoMaxValue = ziMoValue
                ziMoMaxSeatId = seatId
            if dianPaoValue > dianPaoMaxValue:
                dianPaoMaxValue = dianPaoValue
                dianPaoMaxSeatId = seatId
        if ziMoMaxSeatId >= 0:
            createExtendBudgets[ziMoMaxSeatId]["head_mark"] = "zimo_most"
            ftlog.debug('MTableLogic.createExtendBudgets zimo_most seat:', ziMoMaxSeatId)
        if dianPaoMaxSeatId >= 0:
            createExtendBudgets[dianPaoMaxSeatId]["head_mark"] = "dianpao_most"
            ftlog.debug('MTableLogic.createExtendBudgets dianpao_most seat:', dianPaoMaxSeatId)
        return createExtendBudgets

    def sendCreateExtendBudgetsInfo(self, terminate, score):
        # add by taoxc 本桌牌局结束进行大结算
        cebInfo = self.getCreateExtendBudgets(score)
        # 结算，局数不加1
        ctInfo = self.getCreateTableInfo(False)
        self.__msg_processor.table_call_game_all_stat(terminate, cebInfo, ctInfo)

    def sendMsgTableInfo(self, seatId, isReconnect=False):
        """重连"""
        ftlog.debug('MajiangTableLogic.sendMsgTableInfo seatId:', seatId, ' isReconnect:', isReconnect)
        if not self.__players[seatId]:
            ftlog.error('MajiangTableLogic.sendMsgTableInfo player info err:', self.__players)
        hasHuData = None
        if isReconnect:
            self.msgProcessor.setActionId(self.actionID)
            # 刷新一次当前分数
            deltaScore = [0 for _ in range(self.playerCount)]
            tableScore = [0 for _ in range(self.playerCount)]
            if self.tableResult and self.tableResult.score:
                tableScore = self.tableResult.score
            roundScore = [0 for _ in range(self.playerCount)]
            if self.roundResult and self.roundResult.score:
                roundScore = self.roundResult.score
            allScore = [0 for _ in range(self.playerCount)]
            for i in range(self.playerCount):
                allScore[i] = tableScore[i] + roundScore[i]
            # self.__msg_processor.table_call_score(self.getBroadCastUIDs(), allScore, deltaScore)
            # 如果是重连,在血战模式下需要取到已胡牌人的信息
            if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
                hasHuData = self.__win_rule_mgr.getHasHuData()

        ctInfo = self.getCreateTableInfo(True)
        btInfo, atInfo = self.getBaoPaiInfo()
        if self.checkTableState(MTableState.TABLE_STATE_TING):
            # 有听牌状态的产品，玩家没有听牌时，不显示宝牌
            if not self.player[seatId].isTing():
                btInfo = None

        customInfo = {
            'ctInfo': ctInfo,
            'btInfo': btInfo,
        }
        if hasHuData:
            customInfo['hasHuData'] = hasHuData
        self.__msg_processor.table_call_table_info(self.__players[seatId].userId
                                                   , self.__banker_mgr.queryBanker()
                                                   , seatId
                                                   , isReconnect
                                                   , 1
                                                   , self.curSeat
                                                   , 'play'
                                                   , customInfo)
        if isReconnect:
            self.__msg_processor.table_call_score(self.getBroadCastUIDs(), allScore, deltaScore)
            # 如果正在抢杠胡并且这个玩家是杠牌的人,给他补发抢杠胡等待
            if self.qiangGangHuProcessor.getState() != 0:
                if self.qiangGangHuProcessor.curSeatId == seatId:
                    if self.player and self.player[seatId]:
                        self.__msg_processor.table_call_QGH_wait(self.player[seatId].userId, True)
        # 补发宝牌消息
        if ((not btInfo) or (len(btInfo) == 0)) and ((not atInfo) or (len(atInfo) == 0)):
            return
        self.msgProcessor.table_call_baopai(self.player[seatId], btInfo, atInfo)

    def playerReady(self, seatId, isReady):
        """玩家准备"""
        ftlog.debug('MajiangTableLogic.playerReady seatId:', seatId, ' isReady:', isReady, ' tableState:',
                    self.__table_win_state)
        if seatId < 0:
            return False

        if seatId == 0:
            self.refixTableStateByConfig()
            self.refixTableMultipleByConfig()
            self.refixTableZimoBonusByConfig()
            self.reloadTableConfig()

        if self.__table_win_state == MTableState.TABLE_STATE_NONE or self.__table_win_state == MTableState.TABLE_STATE_GAME_OVER:
            if isReady:
                self.player[seatId].ready()
            else:
                self.player[seatId].wait()

            return self.beginGame()

    def beginGame(self):
        """开始游戏
        """
        already = True
        for seat in range(self.__playerCount):
            if (self.__players[seat] == None) or (self.__players[seat].state != MPlayer.PLAYER_STATE_READY):
                ftlog.debug('Seat:', seat, ' nor ready....')
                already = False
                break

        if not already:
            ftlog.debug('MajiangTableLogic.beginGame, all players not ready, begin game later....')
            return False

        # 初始化本局结果
        self.__round_result = MRoundResults()
        self.tableConfig[MFTDefine.CUR_ROUND_COUNT] += 1
        if self.tableConfig[MFTDefine.CUR_ROUND_COUNT] % 8 == 1 and self.tableConfig[MFTDefine.LEFT_CARD_COUNT] > 0:
            self.tableConfig[MFTDefine.LEFT_CARD_COUNT] -= 1
            ftlog.debug('MajiangTableLogic.beginGame consum card left card count:',
                        self.tableConfig[MFTDefine.LEFT_CARD_COUNT])
        self.__round_result.setRoundIndex(self.tableConfig.get(MFTDefine.CUR_ROUND_COUNT, 0))

        for seatId in range(self.playerCount):
            self.player[seatId].play()
        self.__table_tile_mgr.setPlayers(self.player)
        # 发牌
        self.shuffle()
        # 给庄家发一张牌，等待庄家出牌
        cp = self.player[self.__cur_seat]
        self.processAddTile(cp, MTableState.TABLE_STATE_NEXT)
        # 修改牌桌状态
        self.__table_win_state = MTableState.TABLE_STATE_NEXT
        ftlog.debug("kazhuocheck3.self.__table_win_state:", self.__table_win_state)
        if self.tableObserver:
            self.tableObserver.onGameEvent(MTableStatistic.TABLE_START, self.player)
        return True

    def gameNext(self):
        """下一步，游戏的主循环
        """
        ftlog.debug('table.gameNext...')
        changeMagicConfig = self.tableConfig.get(MTDefine.CHANGE_MAGIC, 0)
        canChangeMagic = True
        if changeMagicConfig and canChangeMagic:
            bChanged = False
            magics = self.tableTileMgr.getMagicTiles(True)
            for magic in magics:
                mCount = self.tableTileMgr.getVisibleTilesCount(magic)
                if mCount == 3 and self.tableTileMgr.getTilesLeftCount() > 0:
                    while True:
                        newMagic = self.tableTileMgr.updateMagicTile()
                        newMagicCount = self.tableTileMgr.getVisibleTilesCount(newMagic)
                        ftlog.info('MajiangTableLogic.changeMagic:', newMagic, ' newMagicCount:', newMagicCount)
                        if newMagicCount < 3:
                            bChanged = True
                            break
            if bChanged:
                # 发送换宝通知
                self.updateBao()

        if self.curState() == MTableState.TABLE_STATE_NEXT:
            self.__cur_seat = self.nextSeatId(self.__cur_seat)
            cp = self.player[self.__cur_seat]
            self.processAddTile(cp, MTableState.TABLE_STATE_NEXT)

    def nextSeatId(self, seatId):
        """
        计算下一个seatId
        """
        ftlog.debug("nextSeatId.seatId:", seatId)
        seatId = (seatId + 1) % self.__playerCount
        return seatId

    def preSeatId(self, seatId):
        """
        计算上家seatId
        """
        seatId = seatId - 1
        if seatId < 0:
            seatId += self.__playerCount
        return seatId

    def dropTile(self, seatId, dropTile):
        ftlog.debug('table.dropTile seatId:', seatId, ' dropTile:', dropTile, '__table_win_state:',
                    self.__table_win_state)
        self.__table_win_state = MTableState.TABLE_STATE_DROP
        """玩家出牌"""
        if self.__cur_seat != seatId:
            self.__table_win_state = MTableState.TABLE_STATE_NEXT
            ftlog.debug('table.dropTile wrong seatId...')
            return

        # 当前玩家
        cp = self.__players[seatId]
        if not cp.actionDrop(dropTile):
            self.__table_win_state = MTableState.TABLE_STATE_NEXT
            ftlog.debug('table.dropTile please re-drop')
            return

        # 设置出牌信息
        self.tableTileMgr.setDropTileInfo(dropTile, seatId)
        nowSeat = self.curSeat

        # 判断dropHu,必须在上一步设置出牌信息之后,因为取的是上一步dropTile加到已出牌组里后的数据
        winResultDrop, _ = self.__win_rule_mgr.isDropHu(cp)
        if winResultDrop:
            self.__add_card_processor.reset()
            self.__drop_card_processor.reset()
            self.__qiang_gang_hu_processor.reset()
            # 修改操作标记
            self.__action_id += 1
            # 向玩家发送出牌结果
            self.__msg_processor.table_call_drop(nowSeat, cp, dropTile, 0, {}, self.actionID, 0)
            self.__table_win_state = MTableState.TABLE_STATE_NEXT
            self.gameWin(seatId, dropTile)
            return

        # 设置出牌
        self.__add_card_processor.reset()
        self.__drop_card_processor.reset()
        self.__qiang_gang_hu_processor.reset()
        self.__drop_card_processor.initTile(dropTile, self.curSeat)

        # 修改操作标记
        self.__action_id += 1

        # 测试其他玩家对于这张牌的处理
        # 清空上一轮能胡牌的人的数组
        self.__pass_hu_seats = []
        for seat in range(self.__playerCount):
            if seat != seatId:
                rState = self.processDropTile(self.__players[seat], dropTile)
                #                 import os
                #                 data = json.dumps(self.__msg_processor.msgRecords)
                #                 data2 = copy.deepcopy(data)
                #                 path = "../client_msg_records/"
                #                 if False == os.path.exists(path):
                #                     os.makedirs(path)
                #                 fileRecord = open(path+"11111", 'w')
                #                 for i in range(100):
                #                     data = data + data2
                #                 fileRecord.write(data)
                #                 fileRecord.close()
                if self.playMode == MPlayMode.JIXI and rState & MTableState.TABLE_STATE_HU:
                    return

                    #         # 如果大家都对这张出牌没有反应，加入门前牌堆
                    #         if self.dropCardProcessor.getState() == 0:
                    #             ftlog.debug('dropTile, no user wants tile:', dropTile, ' put to men tiles. seatId:', seatId)
                    #             self.tableTileMgr.setMenTileInfo(dropTile, seatId)
        # 先加入门前牌堆,如果有其它处理再从牌堆里拿掉
        self.tableTileMgr.setMenTileInfo(dropTile, seatId)

        # 向玩家发送出牌结果
        self.__msg_processor.table_call_drop(nowSeat, cp, dropTile, 0, {}, self.actionID, 0)

        self.__table_win_state = MTableState.TABLE_STATE_NEXT

    def processDropTile(self, cp, tile):
        ftlog.debug('MajiangTable.processDropTile...')

        nowSeat = self.curSeat
        # 如果该玩家已经是胡的状态,不进行下面的处理
        if cp.state == MPlayer.PLAYER_STATE_WON:
            self.__msg_processor.table_call_drop(nowSeat, cp, tile, 0, {}, self.actionID, 0)
            ftlog.debug('MajiangTable.processDropTile...player:', cp.curSeatId, 'has won')
            return cp.state

        NotSkipChi = True
        NotSkipPeng = True
        NotSkipGang = True
        NotSkipHu = True
        if self.__playMode == MPlayMode.ZHAOTONG:
            if tile in self.tableTileMgr.getMagicTiles():
                NotSkipChi = False
                NotSkipPeng = False
                NotSkipGang = False
                NotSkipHu = False
        # 取出手牌
        tiles = cp.copyTiles()
        tiles[MHand.TYPE_HAND].append(tile)
        oriTiles = cp.copyTiles()
        oriTiles[MHand.TYPE_HAND].append(tile)

        nextSeatId = self.nextSeatId(self.__cur_seat)
        ftlog.debug("nextSeatId.seatId:", self.__cur_seat)
        state = 0

        exInfo = MTableStateExtendInfo()
        # 听牌了不可以吃
        chiResults = []
        if (not cp.isTing()) and self.checkTableState(MTableState.TABLE_STATE_CHI) and NotSkipChi:
            # 检测是否可吃
            chiResults = self.__chi_rule_mgr.hasChi(tiles, tile)
            if len(chiResults) != 0 and \
                    self.__win_rule_mgr.canWinAfterChiPengGang(tiles):
                if nextSeatId == cp.curSeatId:
                    state |= MTableState.TABLE_STATE_CHI
                    ftlog.debug('MajiangTable.processDropTile seatId:', cp.curSeatId, ' can chi:', chiResults)
                    exInfo.setInfo(MTableState.TABLE_STATE_CHI, chiResults)

                # 判断吃牌里面的吃听
                if self.checkTableState(MTableState.TABLE_STATE_GRABTING):
                    for chiResult in chiResults:
                        for _tile in chiResult:
                            tiles[MHand.TYPE_HAND].remove(_tile)
                        tiles[MHand.TYPE_CHI].append(chiResult)

                        # 判断吃听 吃之后加听
                        tingResult, tingArr = self.__ting_rule_mgr.canTing(tiles, self.tableTileMgr.tiles, tile,
                                                                           self.tableTileMgr.getMagicTiles(cp.isTing()))
                        if tingResult:
                            state |= MTableState.TABLE_STATE_GRABTING
                            chiTing = {}
                            chiTing['tile'] = tile
                            chiTing['pattern'] = chiResult
                            chiTing['ting'] = tingArr
                            exInfo.appendInfo(MTableState.TABLE_STATE_CHI | MTableState.TABLE_STATE_GRABTING, chiTing)
                            ftlog.debug('MajiangTable.processDropTile seatId:', cp.curSeatId,
                                        ' can ting with chi patter:', chiResult)
                        # 还原手牌    
                        tiles[MHand.TYPE_CHI].pop(-1)
                        tiles[MHand.TYPE_HAND].extend(chiResult)

        # 碰
        if (not cp.isTing()) and self.checkTableState(MTableState.TABLE_STATE_PENG) and NotSkipPeng:
            pengSolutions = self.__peng_rule_mgr.hasPeng(tiles, tile)
            ftlog.debug('MajiangTable.processDropTile hasPeng pengSolution:', pengSolutions)

            if len(pengSolutions) > 0 and self.__win_rule_mgr.canWinAfterChiPengGang(tiles):
                # 可以碰，给用户碰的选择
                state = state | MTableState.TABLE_STATE_PENG
                ftlog.debug('MajiangTable.processDropTile seatId:', cp.curSeatId, ' can peng')
                exInfo.setInfo(MTableState.TABLE_STATE_PENG, pengSolutions)

                for pengSolution in pengSolutions:
                    ftlog.debug('MajiangTable.processDropTile check pengSolution:', pengSolution, ' canTingOrNot')
                    if self.checkTableState(MTableState.TABLE_STATE_GRABTING):
                        for _tile in pengSolution:
                            tiles[MHand.TYPE_HAND].remove(_tile)
                        tiles[MHand.TYPE_PENG].append(pengSolution)

                        # 判断碰听，碰加听
                        tingResult, tingArr = self.__ting_rule_mgr.canTing(tiles, self.tableTileMgr.tiles, tile,
                                                                           self.tableTileMgr.getMagicTiles(cp.isTing()))
                        if tingResult:
                            state |= MTableState.TABLE_STATE_GRABTING
                            ftlog.debug('MajiangTable.processDropTile seatId:', cp.curSeatId, ' can ting with peng')
                            pengTing = {}
                            pengTing['tile'] = tile
                            pengTing['ting'] = tingArr
                            pengTing['pattern'] = pengSolution
                            exInfo.appendInfo(MTableState.TABLE_STATE_PENG | MTableState.TABLE_STATE_GRABTING, pengTing)
                        # 还原手牌    
                        tiles[MHand.TYPE_PENG].pop(-1)
                        tiles[MHand.TYPE_HAND].extend(pengSolution)

        # 粘
        if (not cp.isTing()) and self.checkTableState(MTableState.TABLE_STATE_ZHAN):
            # 判断粘听，粘加听
            tingResult, tingArr = self.__ting_rule_mgr.canTing(oriTiles, self.tableTileMgr.tiles, tile,
                                                               self.tableTileMgr.getMagicTiles(cp.isTing()))
            if tingResult and len(tingArr) > 0 and 'isQiDui' in tingArr[0]:
                # ting QiDui
                zhanSolution = [tile, tile]
                ftlog.debug('MajiangTable.processDropTile hasPeng zhanSolution:', zhanSolution)
                state |= MTableState.TABLE_STATE_ZHAN
                state |= MTableState.TABLE_STATE_GRABTING
                ftlog.debug('MajiangTable.processDropTile seatId:', cp.curSeatId, ' can ting with zhan')
                zhanTing = {}
                zhanTing['tile'] = tile
                zhanTing['ting'] = tingArr
                zhanTing['pattern'] = zhanSolution
                exInfo.appendInfo(MTableState.TABLE_STATE_ZHAN | MTableState.TABLE_STATE_GRABTING, zhanTing)
                tiles[MHand.TYPE_HAND].remove(tile)
                tiles[MHand.TYPE_HAND].extend(zhanSolution)

        # 杠，出牌时，只判断手牌能否组成杠
        if self.checkTableState(MTableState.TABLE_STATE_GANG) and (
                not (state & MTableState.TABLE_STATE_ZHAN)) and NotSkipGang:
            gangs = self.__gang_rule_mgr.hasGang(tiles, tile, MTableState.TABLE_STATE_DROP)
            if len(gangs) > 0 and self.__win_rule_mgr.canWinAfterChiPengGang(tiles):
                for gang in gangs:
                    if gang['style'] != MPlayerTileGang.MING_GANG:
                        continue

                    # 可以杠，给用户杠的选择，听牌后，不改变听牌的听口
                    if cp.canGang(gang, True):
                        state = state | MTableState.TABLE_STATE_GANG
                        ftlog.debug('MajiangTable.processDropTile seatId:', cp.curSeatId, ' can gang: ', gang)
                        exInfo.appendInfo(MTableState.TABLE_STATE_GANG, gang)
                        if self.checkTableState(MTableState.TABLE_STATE_FANPIGU):
                            pigus = self.tableTileMgr.getPigus()
                            exInfo.appendInfo(MTableState.TABLE_STATE_FANPIGU, pigus)

                    # 如果杠完，上任何一张牌，都可以听，则可以有杠听。此时确定不了听牌的听口，需杠牌上牌后确定听口
                    if (not cp.isTing()) and self.checkTableState(MTableState.TABLE_STATE_GRABTING):
                        ftlog.debug('handTile:', tiles[MHand.TYPE_HAND])
                        for _tile in gang['pattern']:
                            tiles[MHand.TYPE_HAND].remove(_tile)
                        tiles[MHand.TYPE_GANG].append(gang)

                        leftTiles = copy.deepcopy(self.tableTileMgr.tiles)
                        newTile = leftTiles.pop(0)
                        tiles[MHand.TYPE_HAND].append(newTile)

                        # 判断杠听，杠加听
                        tingResult, tingArr = self.__ting_rule_mgr.canTing(tiles, leftTiles, tile,
                                                                           self.tableTileMgr.getMagicTiles(cp.isTing()))
                        if tingResult:
                            state |= MTableState.TABLE_STATE_GRABTING
                            ftlog.debug('MajiangTable.processDropTile seatId:', cp.curSeatId, ' can ting with gang')
                            gangTing = {}
                            gangTing['tile'] = tile
                            gangTing['ting'] = tingArr
                            gangTing['pattern'] = gang['pattern']
                            gangTing['style'] = gang['style']
                            exInfo.appendInfo(MTableState.TABLE_STATE_GANG | MTableState.TABLE_STATE_TING, gangTing)

                        # 还原手牌
                        tiles[MHand.TYPE_GANG].pop(-1)
                        tiles[MHand.TYPE_HAND].extend(gang)
                        tiles[MHand.TYPE_HAND].remove(newTile)

        # 和
        tilesNoPao = self.tableConfig.get(MTDefine.TILES_NO_PAO, 0)
        winResult = False
        # 牌池数少于某个设置时，不和点炮
        if self.tableTileMgr.getTilesLeftCount() >= tilesNoPao and NotSkipHu:
            magics = self.tableTileMgr.getMagicTiles(cp.isTing())
            if self.tableConfig.get(MTDefine.HONG_ZHONG_BAO, 0) and MTile.TILE_HONG_ZHONG not in magics:
                magics.append(MTile.TILE_HONG_ZHONG)
            # 给winMgr传入当前杠牌的座位号
            self.__win_rule_mgr.setLastGangSeat(self.latestGangState)
            self.__win_rule_mgr.setCurSeatId(self.__cur_seat)
            winResult, winPattern = self.__win_rule_mgr.isHu(tiles, tile, cp.isTing(), MWinRule.WIN_BY_OTHERS,
                                                             self.tableTileMgr.getMagicTiles(cp.isTing()), cp.winNodes)
            self.__win_rule_mgr.setCurSeatId(-1)
            ftlog.debug('MajiangTable.processDropTile, winResutl:', winResult, ' winPattern:', winPattern)

        # 判断是否漏胡
        passHu = False
        if self.__win_rule_mgr.isPassHu:
            ftlog.debug("passHuJudge2", cp.curSeatId)
            passHu = self.tableTileMgr.isPassHuTileBySeatId(cp.curSeatId, tile)

        if self.checkTableState(MTableState.TABLE_STATE_HU) and winResult and not passHu:
            # 可以和，给用户和的选择
            state = state | MTableState.TABLE_STATE_HU
            ftlog.debug('MajiangTable.processDropTile seatId:', cp.curSeatId, ' can win')
            if cp.curSeatId not in self.__pass_hu_seats:
                self.__pass_hu_seats.append(cp.curSeatId)
            if self.playMode == MPlayMode.JIXI:
                timeOut = self.__table_stater.getTimeOutByState(state)
                self.__drop_card_processor.initProcessor(self.actionID, cp.curSeatId, state, exInfo, timeOut)
                # 直接和牌
                self.gameWin(cp.curSeatId, tile)
                return state

        timeOut = self.__table_stater.getTimeOutByState(state)
        self.__drop_card_processor.initProcessor(self.actionID, cp.curSeatId, state, exInfo, timeOut)
        ftlog.debug("processDropTile:self.curSeat", self.curSeat)
        self.__msg_processor.table_call_drop(nowSeat, cp, tile, state, exInfo, self.actionID, timeOut)
        # 返回结果
        return state

    def getBaoPaiInfo(self):
        """获取宝牌的协议信息"""
        bNodes = []
        magics = self.tableTileMgr.getMagicTiles(True)
        for magic in magics:
            bNode = {}
            magicFactor = 0
            if self.playMode == MPlayMode.ZHAOTONG:
                if magic % 10 == 1:
                    magicFactor = magic + 8
                else:
                    magicFactor = magic - 1
                bNode['tile'] = magic
                bNode['factor'] = magicFactor
            else:
                bNode['tile'] = magic
            bNodes.append(bNode)

        abandones = self.tableTileMgr.getAbandonedMagics()
        aNodes = []
        for ab in abandones:
            aNode = {}
            aNode['tile'] = ab
            aNodes.append(aNode)

        ftlog.debug('MajiangTable.getBaoPaiInfo baopaiInfo:', bNodes, ' abandonesInfo:', aNodes)
        return bNodes, aNodes

    def updateBao(self):
        """通知已听牌玩家宝牌"""
        bNodes, aNodes = self.getBaoPaiInfo()
        ftlog.debug('MajiangTable.updateBao bNodes:', bNodes, ' aNodes:', aNodes)
        if len(bNodes) == 0 and len(aNodes) == 0:
            return

        for player in self.player:
            if player.isTing():
                self.msgProcessor.table_call_baopai(player, bNodes, aNodes)
            else:
                self.msgProcessor.table_call_baopai(player, None, aNodes)

    def ting(self, seatId, dropTile, exInfo):
        """听牌状态"""
        winNodes = exInfo.getWinNodesByDropTile(dropTile)
        ftlog.info('ting, winNodes:', winNodes)

        self.__players[seatId].actionTing(winNodes)
        self.__cur_seat = seatId

        if self.playMode == MPlayMode.JIXI:
            # 检查宝牌 如果没有宝牌则生成宝牌
            magicTiles = self.tableTileMgr.getMagicTiles(True)
            if len(magicTiles) == 0:
                self.tableTileMgr.updateMagicTile()
            self.updateBao()

        # 哈尔滨玩法，听牌后通知宝牌
        if self.playMode == MPlayMode.HAERBIN:
            self.updateBao()

        # actionTingLiang当中会根据听亮模式，来决定是否亮牌，默认不亮牌
        self.__players[seatId].actionTingLiang(self.tableTileMgr, dropTile, self.actionID)

        allWinTiles = []
        for player in self.__players:
            if player.tingLiangWinTiles:
                allWinTiles.append(player.tingLiangWinTiles)
            else:
                allWinTiles.append(None)

        # 重置状态机
        self.addCardProcessor.reset()
        self.dropCardProcessor.reset()
        self.qiangGangHuProcessor.reset()

        for player in self.__players:
            if player.curSeatId != seatId:
                # 把听牌信息发送给其他玩家
                self.msgProcessor.table_call_after_ting(self.__players[seatId]
                                                        , self.actionID
                                                        , player.userId
                                                        , allWinTiles)
        # 出牌
        self.dropTile(seatId, dropTile)

    def getTingAction(self, tingInfo, seatId, withHandTiles=False):
        """获取消息中需要的听牌通知"""
        ting_action = []
        tings = tingInfo.get('ting', [])
        for tingNode in tings:
            ting = []
            ting.append(tingNode['dropTile'])
            tips = []
            winNodes = tingNode['winNodes']
            for node in winNodes:
                tip = []
                tip.append(node['winTile'])
                tip.append(1)  # 番数 TODO
                dropCount = 0
                # 宝牌中的也算
                magicTiles = self.tableTileMgr.getMagicTiles(True)
                abandoneMagicTiles = self.tableTileMgr.getAbandonedMagics()
                if (node['winTile'] in magicTiles) or (node['winTile'] in abandoneMagicTiles):
                    dropCount += 1
                dropCount += self.tableTileMgr.getVisibleTilesCount(node['winTile'], withHandTiles, seatId)
                tip.append(4 - dropCount)  # 数量
                tips.append(tip)
            ting.append(tips)
            ting_action.append(ting)
        ftlog.debug('MajiangTable.getTingAction seatId:', seatId, ' return ting_action:', ting_action)
        return ting_action

    """
    以下四种情况为别人打出的牌，其他人可以有的行为
    分别是
        吃
        碰
        杠
        胡
    同一人或者多个人有不同的选择，状态机的大小代表优先级。
    响应的规则是：
    优先响应最高优先级的操作，最高优先级的操作取消，响应次高优先级的操作。
    一人放弃响应，此人的状态机重置
    
    特殊说明：
        此时当前座位还是出牌的人
        获取出牌之外的人的状态进行比较
    """

    def chiTile(self, seatId, chiTile, chiPattern, state=MTableState.TABLE_STATE_CHI):
        """吃别人的牌
        只有一个人，且只判断__drop_card_processor
        """
        cp = self.__players[seatId]
        # 只传吃牌的组合，如果在听牌吃牌中，自动听牌，暂时做的是这样
        if self.__drop_card_processor.updateProcessor(self.actionID, seatId, state, chiTile, chiPattern):
            if self.__drop_card_processor.allResponsed():
                exInfo = self.__drop_card_processor.getExtendResultBySeatId(seatId)
                self.__drop_card_processor.reset()
                cp.actionAdd(chiTile)
                cp.actionChi(chiPattern, chiTile, self.actionID)
                lastSeatId = self.curSeat
                self.tableTileMgr.removeMenTile(chiTile, lastSeatId)
                self.__cur_seat = cp.curSeatId
                self.__action_id += 1

                timeOut = self.__table_stater.getTimeOutByState(state)
                self.addCardProcessor.initProcessor(self.actionID, MTableState.TABLE_STATE_DROP, cp.curSeatId, chiTile,
                                                    exInfo, timeOut)
                ftlog.debug('chiTile init addCardProcessor state:', state
                            , ' chiTile:', chiTile
                            , ' exInfo.extend:', exInfo.extend)

                actionInfo = {}

                # 吃碰完能补杠,现在只有曲靖有需求,暂时加上playMode判断
                if self.playMode == MPlayMode.YUNNAN or self.playMode == MPlayMode.ZHAOTONG:
                    gang = self.__gang_rule_mgr.hasGang(cp.copyTiles(), 0, state)
                    if gang:
                        actionInfo['gang_action'] = gang
                    pigus = self.tableTileMgr.getPigus()
                    if pigus:
                        actionInfo['fanpigu_action'] = pigus
                ftlog.debug("chiTileAfterActionInfo", actionInfo)

                # 吃完出牌，广播吃牌，如果吃听，通知用户出牌听牌
                for player in self.player:
                    self.__msg_processor.table_call_after_chi(lastSeatId
                                                              , self.curSeat
                                                              , chiTile
                                                              , chiPattern
                                                              , timeOut
                                                              , self.actionID
                                                              , player
                                                              , actionInfo)

    def pengTile(self, seatId, tile, pengPattern, state):
        """碰别人的牌
        只有一个人，且只判断__drop_card_processor
        """
        cp = self.__players[seatId]
        if self.__drop_card_processor.updateProcessor(self.actionID, seatId, state, tile, pengPattern):
            if self.__drop_card_processor.allResponsed():
                exInfo = self.__drop_card_processor.getExtendResultBySeatId(seatId)
                self.__drop_card_processor.reset()
                cp.actionAdd(tile)
                cp.actionPeng(tile, pengPattern, self.actionID)
                lastSeatId = self.curSeat
                self.tableTileMgr.removeMenTile(tile, lastSeatId)
                self.__cur_seat = cp.curSeatId
                self.__action_id += 1

                timeOut = self.__table_stater.getTimeOutByState(state)
                self.addCardProcessor.initProcessor(self.actionID, MTableState.TABLE_STATE_DROP, cp.curSeatId, tile,
                                                    exInfo, timeOut)
                ftlog.debug('after pengTile init addCardProcessor state:', state
                            , ' curSeatId:', cp.curSeatId
                            , ' exInfo.extend:', exInfo.extend)

                actionInfo = {}
                # 吃碰完能补杠,现在只有曲靖有需求,暂时加上playMode判断
                if self.playMode == MPlayMode.YUNNAN or self.playMode == MPlayMode.ZHAOTONG:
                    gang = self.__gang_rule_mgr.hasGang(cp.copyTiles(), 0, state)
                    if gang:
                        actionInfo['gang_action'] = gang
                    pigus = self.tableTileMgr.getPigus()
                    if pigus:
                        actionInfo['fanpigu_action'] = pigus
                ftlog.debug("pengTileAfterActionInfo", actionInfo)

                # 碰消息广播
                for player in self.player:
                    self.__msg_processor.table_call_after_peng(lastSeatId
                                                               , self.curSeat
                                                               , tile
                                                               , timeOut
                                                               , self.actionID
                                                               , player
                                                               , pengPattern
                                                               , actionInfo
                                                               , exInfo)

        else:
            ftlog.debug('pengTile error, need check....')

    def zhanTile(self, seatId, tile, zhanPattern, state, special_tile):
        """粘别人的牌
        只有一个人，且只判断__drop_card_processor
        """
        cp = self.__players[seatId]
        if self.__drop_card_processor.updateProcessor(self.actionID, seatId, state, tile, zhanPattern):
            exInfo = self.__drop_card_processor.getExtendResultBySeatId(seatId)
            self.__drop_card_processor.reset()
            cp.actionAdd(tile)
            cp.setZhanTiles(zhanPattern)
            lastSeatId = self.curSeat
            self.__cur_seat = cp.curSeatId
            self.__action_id += 1

            timeOut = self.__table_stater.getTimeOutByState(state)
            self.addCardProcessor.initProcessor(self.actionID, MTableState.TABLE_STATE_DROP, cp.curSeatId, tile, exInfo,
                                                timeOut)
            ftlog.debug('after zhanTile init addCardProcessor state:', state
                        , ' curSeatId:', cp.curSeatId
                        , ' exInfo.extend:', exInfo.extend)

            actionInfo = {}
            ting_action = None
            if state & MTableState.TABLE_STATE_GRABTING:
                tingInfo = exInfo.extend['zhanTing'][0]
                ftlog.debug('zhanTile grabTing tingInfo:', tingInfo)
                ting_action = self.getTingAction(tingInfo, seatId, True)
                actionInfo['ting_action'] = ting_action

            # 粘消息广播
            for player in self.player:
                self.__msg_processor.table_call_after_zhan(lastSeatId
                                                           , self.curSeat
                                                           , tile
                                                           , timeOut
                                                           , self.actionID
                                                           , player
                                                           , zhanPattern
                                                           , actionInfo)

        else:
            ftlog.debug('zhanTile error, need check....')

    def grabHuGang(self, seatId, tile):
        if self.qiangGangHuProcessor.getState() == 0:
            return

        if self.qiangGangHuProcessor.updateProcessor(self.actionID, seatId, MTableState.TABLE_STATE_QIANGGANG, tile,
                                                     None):
            # 不用客户端传过来的这张牌
            winTile = self.qiangGangHuProcessor.tile
            showTile = self.qiangGangHuProcessor.magicTile
            if showTile == 0:
                showTile = winTile
            cp = self.player[seatId]
            if self.playMode == MPlayMode.YUNNAN or self.playMode == MPlayMode.ZHAOTONG:
                if not self.qiangGangHuProcessor.allResponsed():
                    # 不是所有全响应完了 先等待
                    cp.actionHuFromOthers(winTile)
                    if seatId not in self.__win_seats:
                        self.__win_seats.append(seatId)
                else:
                    cp.actionHuFromOthers(winTile)
                    if seatId not in self.__win_seats:
                        self.__win_seats.append(seatId)
                    self.qiangGangHuProcessor.reset()
                    # 和牌后，获取最后的特殊牌
                    self.tableTileMgr.drawLastSpecialTiles(self.curSeat, seatId)
                    # 当前的座位号胡牌，胡牌类型为抢杠
                    winBase = self.getTableConfig(MTDefine.WIN_BASE, 1)
                    ftlog.debug('MajiangTableLogic.gameWin winBase: ', winBase)
                    winMode = [MOneResult.WIN_MODE_LOSS for _ in range(self.playerCount)]
                    winTiles = [0 for _ in range(len(self.__players))]
                    fanPattern = [[] for _ in range(self.playerCount)]
                    awardInfo = []
                    if winBase > 0:
                        result = MOneResultFactory.getOneResult(self.playMode)
                        result.setResultType(MOneResult.RESULT_WIN)
                        result.setLastSeatId(self.curSeat)
                        result.setWinSeatId(seatId)
                        result.setWinSeats(self.__win_seats)
                        result.setQiangGang(True)
                        result.setTableConfig(self.tableConfig)
                        result.setBankerSeatId(self.queryBanker())
                        result.setPlayerCount(self.playerCount)
                        if self.checkTableState(MTableState.TABLE_STATE_TING):
                            result.setWinNodes(cp.winNodes)

                        tingState = [0 for _ in range(self.playerCount)]
                        colorState = [0 for _ in range(self.playerCount)]
                        menState = [0 for _ in range(self.playerCount)]
                        ziState = [[0, 0, 0, 0, 0, 0, 0] for _ in range(self.playerCount)]
                        playerGangTiles = [0 for _ in range(self.playerCount)]
                        for player in self.player:
                            # 听牌状态
                            if player.isTing():
                                tingState[player.curSeatId] = 1
                            # 花色状态    
                            pTiles = player.copyTiles()
                            tileArr = MTile.changeTilesToValueArr(MHand.copyAllTilesToList(pTiles))
                            colorState[player.curSeatId] = MTile.getColorCount(tileArr)
                            tempTiles = MTile.traverseTile(MTile.TILE_FENG)
                            ziState[player.curSeatId] = tileArr[tempTiles[0]:tempTiles[len(tempTiles) - 1] + 1]
                            # 玩家牌的情况
                            playerGangTiles[player.curSeatId] = player.copyGangArray()
                            # 门清状态
                            handTiles = player.copyHandTiles()
                            if len(handTiles) == self.handCardCount:
                                menState[player.curSeatId] = 1

                        result.setMenState(menState)
                        result.setTingState(tingState)
                        result.setColorState(colorState)
                        result.setZiState(ziState)
                        result.setPlayerGangTiles(playerGangTiles)
                        ftlog.debug("grabGangHuWinTile =", winTile)
                        result.setWinTile(winTile)
                        result.setShowTile(showTile)
                        result.setTableTileMgr(self.tableTileMgr)
                        result.setWinRuleMgr(self.__win_rule_mgr)
                        result.setMultiple(self.__win_rule_mgr.multiple)
                        result.calcScore()
                        self.roundResult.addRoundResult(result)
                        # 加上牌桌上局数总分
                        tableScore = [0 for _ in range(self.playerCount)]
                        if self.tableResult.score:
                            tableScore = self.tableResult.score
                        currentScore = [0 for _ in range(self.playerCount)]
                        for i in range(self.playerCount):
                            currentScore[i] = tableScore[i] + self.roundResult.score[i]
                        self.msgProcessor.table_call_score(self.getBroadCastUIDs(), currentScore,
                                                           self.roundResult.delta)
                        if MOneResult.KEY_WIN_MODE in result.results:
                            winMode = result.results[MOneResult.KEY_WIN_MODE]
                        if MOneResult.KEY_WIN_TILE in result.results:
                            winTiles = result.results[MOneResult.KEY_WIN_TILE]
                        if MPlayMode().isSubPlayMode(self.playMode, MPlayMode.KAWUXING):
                            fanPattern = self.roundResult.fanPatterns
                        else:
                            if MOneResult.KEY_FAN_PATTERN in result.results:
                                fanPattern = result.results[MOneResult.KEY_FAN_PATTERN]
                            # 带上明杠暗杠oneResult中的番型信息
                            fanPattern = self.appendGangFanPattern(fanPattern)
                        if MOneResult.KEY_AWARD_INFO in result.results:
                            awardInfo = result.results[MOneResult.KEY_AWARD_INFO]

                    # 清空之前的杠牌记录    
                    self.setLatestGangState(-1)
                    self.__win_rule_mgr.setLastGangSeat(-1)
                    ftlog.debug("gangTileclearLatestGangState = ", self.latestGangState)
                    # 点炮和，一个人和，一个人输
                    if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
                        hasHuCount = 0
                        for player in self.player:
                            if player.hasHu:
                                hasHuCount += 1
                        if hasHuCount + 2 >= self.playerCount:
                            self.__table_result.addResult(self.roundResult)
                    else:
                        self.__table_result.addResult(self.roundResult)
                    scoreBase = self.getTableConfig(MTDefine.SCORE_BASE, 0)
                    uids = self.getBroadCastUIDs()
                    wins = [seatId]
                    looses = [self.curSeat]
                    observers = []
                    for player in self.player:
                        if (player.curSeatId not in self.__win_seats) and (
                                    player.curSeatId not in looses) and not player.hasHu:
                            observers.append(player.curSeatId)

                    # 抢杠和，局数不加1 
                    ctInfo = self.getCreateTableInfo()
                    btInfo, _ = self.getBaoPaiInfo()
                    # 获取最后特殊牌的协议信息
                    lstInfo = self.tableTileMgr.getLastSpecialTiles()
                    winFinal = True
                    loseFinal = True
                    sendWinSeat = self.__win_seats
                    if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
                        if self.getWinPlayerCount() < self.playerCount - 1:
                            loseFinal = False
                            winFinal = False
                        else:
                            for player in self.player:
                                if player.hasHu:
                                    sendWinSeat.append(player.curSeatId)
                                    #                         # 已经胡了就不广播胡牌消息了
                                    #                         for player in self.player:
                                    #                             if player.userId in uids and player.hasHu:
                                    #                                 uids.remove(player.userId)
                    customInfo = {
                        'ctInfo': ctInfo,
                        'btInfo': btInfo,
                        'lstInfo': lstInfo,
                        'awardInfo': awardInfo,
                        'winFinal': winFinal,
                        'loseFinal': loseFinal,
                        'winTiles': winTiles
                    }
                    sendTableScore = [0 for _ in range(self.playerCount)]
                    if self.__table_result.score:
                        sendTableScore = self.__table_result.score
                    self.msgProcessor.table_call_game_win_loose(uids
                                                                , sendWinSeat
                                                                , looses
                                                                , observers
                                                                , winMode
                                                                , showTile
                                                                , sendTableScore
                                                                , self.__round_result.score
                                                                , scoreBase
                                                                , fanPattern
                                                                , customInfo)
                    # 判断和牌是否结束
                    self.processHu(cp)

    # 不用检查抢杠和 直接杠牌 包含明杠和暗杠
    def __gangTile(self, lastSeatId, seatId, gangTile, gangPattern, style, state, afterAdd, special_tile=None,
                   qiangGangSeats=[]):
        ftlog.debug('MTableLogic.__gangTile lastSeatId', lastSeatId,
                    'seatId:', seatId, ' gangTile:', gangTile,
                    'gangPattern:', gangPattern, 'style:', style, ' state:', state)

        # 发送给客户端的结构
        gang = {}
        gang['tile'] = gangTile
        gang['pattern'] = gangPattern
        gang['style'] = style

        cp = self.__players[seatId]
        # after add
        if afterAdd:
            # 加入带赖子的补杠
            magicTiles = self.tableTileMgr.getMagicTiles()
            isAddOK = cp.actionGangByAddCard(gangTile, gangPattern, style, self.actionID, magicTiles)
            if not isAddOK:
                return
        # after drop
        else:
            cp.actionAdd(gangTile)
            self.tableTileMgr.removeMenTile(gangTile, lastSeatId)
            # 明杠
            isAddOK = cp.actionGangByDropCard(gangTile, gangPattern, self.actionID)
            if not isAddOK:
                return

        # 设置本次杠牌状态
        self.setLatestGangState(seatId)
        self.__win_rule_mgr.setLastGangSeat(seatId)
        ftlog.debug("gangTilesetLatestGangState = ", seatId)
        self.__action_id += 1
        self.__drop_card_processor.reset()

        # 给所有人发送杠牌结果(只有结果 没有抢杠和信息)
        # 曲靖麻将不给抢杠的人发
        ftlog.debug('table_call_after_gang seatId = ', seatId, 'qiangGangSeats= ', qiangGangSeats)
        for player in self.player:
            if self.playMode == MPlayMode.YUNNAN or self.playMode == MPlayMode.ZHAOTONG:
                if player.curSeatId not in qiangGangSeats:
                    self.msgProcessor.table_call_after_gang(lastSeatId
                                                            , seatId
                                                            , gangTile
                                                            , [lastSeatId]
                                                            , self.actionID
                                                            , player
                                                            , gang)
            else:
                self.msgProcessor.table_call_after_gang(lastSeatId
                                                        , seatId
                                                        , gangTile
                                                        , [lastSeatId]
                                                        , self.actionID
                                                        , player
                                                        , gang)
                # 杠牌之后设置当前位置为杠牌人的位置
        self.__cur_seat = cp.curSeatId
        # 杠完上牌
        self.processAddTile(cp, state, special_tile)

        # 记录杠牌得分
        gangBase = self.getTableConfig(MTDefine.GANG_BASE, 0)
        ftlog.debug('MajiangTableLogic.__gangTile gangBase: ', gangBase)

        if gangBase > 0:
            result = MOneResultFactory.getOneResult(self.playMode)
            result.setResultType(MOneResult.RESULT_GANG)
            result.setLastSeatId(lastSeatId)
            result.setWinSeatId(self.curSeat)
            result.setTableConfig(self.tableConfig)
            result.setPlayerCount(self.playerCount)
            result.setStyle(style)
            result.setMultiple(self.__win_rule_mgr.multiple)
            result.calcScore()
            # 设置牌局过程中的明杠和暗杠番型信息
            self.roundResult.addRoundResult(result)
            # 加上牌桌上局数总分
            tableScore = [0 for _ in range(self.playerCount)]
            if self.tableResult.score:
                tableScore = self.tableResult.score
            currentScore = [0 for _ in range(self.playerCount)]
            for i in range(self.playerCount):
                currentScore[i] = tableScore[i] + self.roundResult.score[i]
            self.msgProcessor.table_call_score(self.getBroadCastUIDs(), currentScore, self.roundResult.delta)

    def gangTile(self, seatId, tile, gangPattern, style, state, special_tile=None):
        """杠别人的牌
        只有一个人
        """
        ftlog.debug('MTableLogic.gangTile seatId:', seatId, ' tile:', tile, 'gangPattern:', gangPattern, ' style:',
                    style)
        lastSeatId = self.curSeat
        # 发送给客户端的结构
        gang = {}
        gang['tile'] = tile
        gang['pattern'] = gangPattern
        gang['style'] = style

        if self.__add_card_processor.getState() != 0:
            # 如果是明杠，判断其他玩家是否可以抢杠和
            # 如果没有玩家抢杠和，给当前玩家发牌
            # 如果有玩家抢杠和，等待该玩家的抢杠和结果
            # 检测抢杠和
            qiangGangWin = False
            winSeats = [-1 for _ in range(self.playerCount)]
            canQiangGang = False
            if style == MPlayerTileGang.MING_GANG:
                canQiangGang = True
            else:
                if self.playMode == MPlayMode.JIXI:
                    canQiangGang = True

            if canQiangGang and self.checkTableState(MTableState.TABLE_STATE_QIANGGANG) and self.checkTableState(
                    MTableState.TABLE_STATE_HU):
                rulePass = False
                rule = self.tableTileMgr.qiangGangRule
                if rule != 0b111:
                    if lastSeatId == seatId:
                        # 自己摸牌自己杠
                        # 暗杠0x001
                        # 补杠0x010
                        if style == 0:
                            if rule & 0b001:
                                rulePass = True
                        elif style == 1:
                            if rule & 0b010:
                                rulePass = True

                    else:
                        if rule & 0b100 and style == 1:
                            # 杠别人的牌0x100
                            rulePass = True

                # 判断一下这张牌,如果是赖子,并且剩下3张也都是赖子,才作为赖子传入qiangGangHuProcessor
                # 否则传入gangPattern里面其它的牌                            
                checkTile = gangPattern[-1]
                magicTiles = self.tableTileMgr.getMagicTiles()
                #                赖子补杠抢杠胡抢的牌要显示为赖子
                showWinTile = checkTile
                for tile in gangPattern:
                    if tile in magicTiles:
                        showWinTile = tile
                if gangPattern[-1] in magicTiles:
                    for temp in gangPattern:
                        if temp not in magicTiles:
                            checkTile = temp
                self.__pass_hu_seats = []
                for index in range(1, self.playerCount):
                    newSeatId = (seatId + index) % self.playerCount
                    # 判断是否抢杠和牌
                    player = self.player[newSeatId]
                    magics = self.tableTileMgr.getMagicTiles(player.isTing())

                    pTiles = player.copyTiles()
                    pTiles[MHand.TYPE_HAND].append(checkTile)
                    winResult, winPattern = self.__win_rule_mgr.isHu(pTiles, checkTile, player.isTing(),
                                                                     MWinRule.WIN_BY_QIANGGANGHU, magics,
                                                                     player.winNodes)
                    ftlog.debug('MajiangTable.gangTile after gang, check qiangGangHu winResult:', winResult,
                                ' winPattern:', winPattern)

                    if winResult and rulePass:
                        # 可以和，给用户和的选择
                        state = MTableState.TABLE_STATE_QIANGGANG
                        winInfo = {}
                        winInfo['tile'] = tile
                        winInfo['qiangGang'] = 1
                        winInfo['gangSeatId'] = self.curSeat
                        exInfo = MTableStateExtendInfo()
                        exInfo.appendInfo(state, winInfo)
                        ftlog.debug('MajiangTableLogic.gangTile after gang, qiangGangHu extendInfo:', exInfo)
                        timeOut = self.__table_stater.getTimeOutByState(state)
                        qiangGangWin = True
                        if player.curSeatId not in self.__pass_hu_seats:
                            self.__pass_hu_seats.append(player.curSeatId)
                        winSeats[player.curSeatId] = player.curSeatId
                        self.qiangGangHuProcessor.initProcessor(self.actionID
                                                                , player.curSeatId
                                                                , state
                                                                , exInfo
                                                                , timeOut)

            if qiangGangWin:
                if showWinTile in magicTiles:
                    self.qiangGangHuProcessor.initTile(checkTile, self.curSeat, state, gangPattern, style, special_tile,
                                                       showWinTile)
                else:
                    self.qiangGangHuProcessor.initTile(checkTile, self.curSeat, state, gangPattern, style, special_tile)
                # 摸牌处理器初始化
                self.__add_card_processor.reset()

                for player in self.player:
                    # 给抢杠的人发送杠牌消息
                    if player.curSeatId in winSeats:
                        self.msgProcessor.table_call_after_gang(lastSeatId
                                                                , self.curSeat
                                                                , tile
                                                                , [lastSeatId]
                                                                , self.actionID
                                                                , player
                                                                , gang
                                                                , self.qiangGangHuProcessor.getExtendResultBySeatId(
                                player.curSeatId))
                    # 给杠牌的人发送抢杠胡等待消息
                    if player.curSeatId == self.curSeat:
                        self.msgProcessor.table_call_QGH_wait(player.userId, True)
                        #                 # 如果抢杠胡,需要给客户端发送屁股牌消息,让客户端关闭界面,并且清空客户端的implict_gang_action
                        #                 pigus = self.tableTileMgr.getPigus()
                        #                 self.msgProcessor.table_call_fanpigu(pigus, self.getBroadCastUIDs(), True)
                return
            else:
                # 摸牌处理器初始化
                self.__add_card_processor.reset()
                # 直接杠牌
                self.__gangTile(lastSeatId, seatId, tile, gangPattern, style, state, True, special_tile)

        elif self.__drop_card_processor.getState() != 0:
            # 自己打牌后,自己不能杠牌,从后端逻辑上限制
            if seatId == lastSeatId:
                ftlog.debug("MTableLogic.gangTile gang after self drop error", seatId, "lastSeatId:", lastSeatId)
                return
            # 抢杠胡的过程中不能让自动处理逻辑帮自己杠牌,必须要靠系统触发
            if self.__qiang_gang_hu_processor.getState() != 0:
                ftlog.debug("MTableLogic.gangTile gang after self drop error __qiang_gang_hu_processor is on seatId:",
                            seatId, "lastSeatId:", lastSeatId)
                return
            if self.__drop_card_processor.updateProcessor(self.actionID, seatId, state, tile, gang):
                if self.__drop_card_processor.allResponsed():
                    # 直接杠牌
                    self.__gangTile(lastSeatId, seatId, tile, gangPattern, style, state, False, special_tile)
            else:
                if self.playMode == MPlayMode.YUNNAN or self.playMode == MPlayMode.ZHAOTONG:
                    cp = self.player[seatId]
                    if cp:
                        self.msgProcessor.table_call_QGH_wait(cp.userId, True)
                        #                     # 曲靖如果杠不能立即成功,客户端需要等待,就发送翻屁股消息到客户端,让客户端关闭翻屁股界面
                        #                     pigus = self.tableTileMgr.getPigus()
                        #                     self.msgProcessor.table_call_fanpigu(pigus, self.getBroadCastUIDs(), True)

    def changeToTingState(self, player, tile):
        # self.__action_id += 1
        # 判断停牌
        allTiles = player.copyTiles()
        if not player.isTing():
            """切换到听牌状态，这个时候，获取听牌方案，是一定可以取到的，取不到就有问题"""
            tingResult, tingReArr = self.tingRule.canTing(allTiles, self.tableTileMgr.tiles, tile,
                                                          self.tableTileMgr.getMagicTiles(player.isTing()), \
                                                          self.__cur_seat, player.curSeatId, self.actionID)
            if tingResult and len(tingReArr) > 0:
                # 可以听牌
                ftlog.debug('MajiangTableLogic.changeToTingState canTing result value: ', tingResult, ' result array: ',
                            tingReArr)
                exInfo = MTableStateExtendInfo()
                exInfo.setInfo(MTableState.TABLE_STATE_TING, tingReArr)
                return True, exInfo
            else:
                ftlog.debug('error, player can not ting!!!!! seatId:', player.curSeatId)
        else:
            ftlog.debug('error, player already ting! seatId:', player.curSeatId)

        return False, None

    def gameWin(self, seatId, tile):
        """
        胡牌
        1）出牌时 可以有多个人和牌
        2）摸牌时，只有摸牌的人和牌
        """
        lastSeatId = self.curSeat
        cp = self.__players[seatId]
        ftlog.debug('MajiangTableLogic.gameWin seatId:', seatId, ' lastSeatId:', lastSeatId)

        # 和牌后，获取最后的特殊牌
        self.tableTileMgr.drawLastSpecialTiles(lastSeatId, seatId)

        # 结算的类型
        # 1 吃和
        # 0 自摸
        # -1 输牌
        wins = [seatId]
        looses = []
        observers = []
        gangKai = False
        daFeng = False
        baoZhongBao = False
        magicAfertTing = False
        tianHu = False
        wuDuiHu = False
        if self.__add_card_processor.getState() != 0:
            exInfo = self.__add_card_processor.extendInfo
            winNode = exInfo.getWinNodeByTile(tile)
            if winNode and ('gangKai' in winNode) and winNode['gangKai']:
                gangKai = True
            if winNode and ('daFeng' in winNode) and winNode['daFeng']:
                daFeng = True
            if winNode and ('baoZhongBao' in winNode) and winNode['baoZhongBao']:
                baoZhongBao = True
            if winNode and ('magicAfertTing' in winNode) and winNode['magicAfertTing']:
                magicAfertTing = True
            if winNode and ('tianHu' in winNode) and winNode['tianHu']:
                tianHu = True
            if winNode and ('wuDuiHu' in winNode) and winNode['wuDuiHu']:
                wuDuiHu = True

            self.__add_card_processor.updateProcessor(self.actionID, MTableState.TABLE_STATE_HU, seatId)
            cp.actionHuByMyself(tile, not (baoZhongBao or magicAfertTing or tianHu or wuDuiHu))
            # 自摸，一个人和，其他人都输
            for player in self.player:
                if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
                    if player.curSeatId != seatId and not player.hasHu:
                        looses.append(player.curSeatId)
                else:
                    if player.curSeatId != seatId:
                        looses.append(player.curSeatId)
        elif self.__drop_card_processor.getState() != 0:
            if self.__drop_card_processor.updateProcessor(self.actionID, seatId, MTableState.TABLE_STATE_HU, tile,
                                                          None):
                self.__drop_card_processor.reset()
                ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang updateProcessor True seatId = ', seatId, 'tile =',
                            tile)
                cp.actionHuFromOthers(tile)
                self.tableTileMgr.removeMenTile(tile, lastSeatId)
                looses.append(lastSeatId)
                for player in self.player:
                    if (player.curSeatId not in wins) and (player.curSeatId not in looses) and not player.hasHu:
                        observers.append(player.curSeatId)
            else:
                if self.playMode == MPlayMode.YUNNAN or self.playMode == MPlayMode.ZHAOTONG:
                    # 曲靖一炮多响,等所有能胡的人确认完了再开始处理流程
                    ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang')
                    if not self.__drop_card_processor.allResponsed():
                        # 还有人没有确认完
                        ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang,need more response seatId = ', seatId)
                        if seatId not in self.__win_seats:
                            ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang,append seatId = ', seatId,
                                        'self.__win_seats', self.__win_seats)
                            self.__win_seats.append(seatId)
                            cp.actionHuFromOthers(tile)
                            self.tableTileMgr.removeMenTile(tile, lastSeatId)
                        return
                    else:
                        ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang,calcResult self.__win_seats=',
                                    self.__win_seats)
                        # 所有人都确认完了
                        cp.actionHuFromOthers(tile)
                        self.tableTileMgr.removeMenTile(tile, lastSeatId)
                        if seatId not in self.__win_seats:
                            ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang,append seatId = ', seatId,
                                        'self.__win_seats', self.__win_seats)
                            self.__win_seats.append(seatId)
                        # 点炮输家只有一个
                        looses.append(self.__drop_card_processor.curSeatId)
                        # 如果是胡牌时有人可以杠并且选择了,就把这个杠存下来,等处理完胡之后再补发
                        if self.playMode == MPlayMode.ZHAOTONG:
                            turns = []
                            for offset in range(self.playerCount - 1):
                                turns.append((self.__drop_card_processor.curSeatId + offset + 1) % self.playerCount)
                            for index in turns:
                                if index in self.__win_seats:
                                    continue
                                state = self.dropCardProcessor.getStateBySeatId(index)
                                exInfo = self.dropCardProcessor.getExtendResultBySeatId(index)
                        if self.playMode == MPlayMode.ZHAOTONG:
                            self.__drop_card_processor.resetSeatId(seatId)
                        else:
                            self.__drop_card_processor.reset()
                        for player in self.player:
                            if (player.curSeatId not in self.__win_seats) and (
                                        player.curSeatId not in looses) and not player.hasHu:
                                observers.append(player.curSeatId)
                        changeSeat = True
                        # 昭通胡的时候判断有没有已经选择的碰和杠，如果有的话 不转换座位号
                        if self.playMode == MPlayMode.ZHAOTONG:
                            for i in range(self.playerCount):
                                state = self.dropCardProcessor.getStateBySeatId(i)
                                if state == MTableState.TABLE_STATE_PENG or state == MTableState.TABLE_STATE_GANG:
                                    changeSeat = False
                        if changeSeat:
                            self.__cur_seat = seatId
                        # 计算胡牌得分
                        winBase = self.getTableConfig(MTDefine.WIN_BASE, 1)
                        winMode = [MOneResult.WIN_MODE_LOSS for _ in range(len(self.__players))]
                        winTiles = [0 for _ in range(len(self.__players))]
                        fanPattern = [[] for _ in range(len(self.__players))]
                        awardInfo = []
                        if winBase > 0:
                            ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang calcResult1')
                            result = MOneResultFactory.getOneResult(self.playMode)
                            result.setResultType(MOneResult.RESULT_WIN)
                            result.setLastSeatId(lastSeatId)
                            result.setWinSeatId(self.curSeat)
                            result.setWinSeats(self.__win_seats)
                            result.setLatestGangState(self.latestGangState)
                            result.setTableConfig(self.tableConfig)
                            result.setBankerSeatId(self.queryBanker())
                            result.setGangKai(gangKai)
                            result.setBaoZhongBao(baoZhongBao)
                            result.setMagicAfertTing(magicAfertTing)
                            result.setTianHu(tianHu)
                            result.setWuDuiHu(wuDuiHu)
                            result.setPlayerCount(self.playerCount)
                            if self.checkTableState(MTableState.TABLE_STATE_TING):
                                result.setWinNodes(cp.winNodes)

                            tingState = [0 for _ in range(self.playerCount)]
                            colorState = [0 for _ in range(self.playerCount)]
                            menState = [0 for _ in range(self.playerCount)]
                            ziState = [[0, 0, 0, 0, 0, 0, 0] for _ in range(self.playerCount)]
                            mingState = [0 for _ in range(self.playerCount)]
                            playerAllTiles = [0 for _ in range(self.playerCount)]
                            playerHandTiles = [0 for _ in range(self.playerCount)]
                            playerGangTiles = [0 for _ in range(self.playerCount)]
                            for player in self.player:
                                # 听牌状态
                                if player.isTing():
                                    tingState[player.curSeatId] = 1
                                # 花色状态    
                                pTiles = player.copyTiles()
                                tileArr = MTile.changeTilesToValueArr(MHand.copyAllTilesToList(pTiles))
                                colorState[player.curSeatId] = MTile.getColorCount(tileArr)
                                tempTiles = MTile.traverseTile(MTile.TILE_FENG)
                                ziState[player.curSeatId] = tileArr[tempTiles[0]:tempTiles[len(tempTiles) - 1] + 1]
                                # 玩家牌的情况
                                playerAllTiles[player.curSeatId] = player.copyTiles()
                                playerHandTiles[player.curSeatId] = player.copyHandTiles()
                                playerGangTiles[player.curSeatId] = player.copyGangArray()
                                # 门清状态
                                if len(playerHandTiles[player.curSeatId]) == self.handCardCount:
                                    menState[player.curSeatId] = 1
                                # 明牌状态
                                if player.isMing():
                                    mingState[player.curSeatId] = 1

                            result.setMenState(menState)
                            result.setTingState(tingState)
                            result.setColorState(colorState)
                            result.setZiState(ziState)
                            result.setMingState(mingState)
                            result.setPlayerAllTiles(playerAllTiles)
                            result.setPlayerGangTiles(playerGangTiles)
                            result.setWinTile(tile)
                            # 抽奖牌
                            if self.playMode == MPlayMode.JIXI:
                                awardTileCount = self.tableConfig.get(MTDefine.AWARD_TILE_COUNT, 1)
                                awardTiles = self.tableTileMgr.popTile(awardTileCount)
                                result.setAwardTiles(awardTiles)
                            result.setActionID(self.actionID)
                            result.setDaFeng(daFeng)
                            result.setTableTileMgr(self.tableTileMgr)
                            result.setWinRuleMgr(self.__win_rule_mgr)
                            result.setMultiple(self.__win_rule_mgr.multiple)
                            ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang calcResult2 winTile'
                                        , tile
                                        , 'lastSeatId', lastSeatId
                                        , 'winSeatId', self.curSeat
                                        , 'self.__win_seats', self.__win_seats
                                        , 'self.actionID', self.actionID
                                        )
                            result.calcScore()
                            ftlog.debug('MajiangTableLogic.gameWin.yipaoduoxiang calcResult3 result.results'
                                        , result.results
                                        , 'lastSeatId', lastSeatId
                                        , 'winSeatId', self.curSeat
                                        , 'self.__win_seats', self.__win_seats
                                        , 'self.actionID', self.actionID
                                        )
                            self.setLatestGangState(-1)
                            self.__win_rule_mgr.setLastGangSeat(-1)
                            ftlog.debug("gangTileclearLatestGangState = ", self.latestGangState)
                            self.roundResult.addRoundResult(result)
                            # 加上牌桌上局数总分
                            tableScore = [0 for _ in range(self.playerCount)]
                            if self.tableResult.score:
                                tableScore = self.tableResult.score
                            currentScore = [0 for _ in range(self.playerCount)]
                            for i in range(self.playerCount):
                                currentScore[i] = tableScore[i] + self.roundResult.score[i]
                            self.msgProcessor.table_call_score(self.getBroadCastUIDs(), currentScore,
                                                               self.roundResult.delta)
                            if MOneResult.KEY_WIN_MODE in result.results:
                                winMode = result.results[MOneResult.KEY_WIN_MODE]
                            if MOneResult.KEY_WIN_TILE in result.results:
                                winTiles = result.results[MOneResult.KEY_WIN_TILE]
                            if MPlayMode().isSubPlayMode(self.playMode, MPlayMode.KAWUXING):
                                fanPattern = self.roundResult.fanPatterns
                            else:
                                if MOneResult.KEY_FAN_PATTERN in result.results:
                                    fanPattern = result.results[MOneResult.KEY_FAN_PATTERN]
                                # 带上明杠暗杠oneResult中的番型信息
                                fanPattern = self.appendGangFanPattern(fanPattern)
                            if MOneResult.KEY_AWARD_INFO in result.results:
                                awardInfo = result.results[MOneResult.KEY_AWARD_INFO]

                        # 点炮和，一个人和，一个人输
                        if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
                            hasHuCount = 0
                            for player in self.player:
                                if player.hasHu:
                                    hasHuCount += 1
                            if hasHuCount + 2 >= self.playerCount:
                                self.__table_result.addResult(self.roundResult)
                        else:
                            self.__table_result.addResult(self.roundResult)
                        scoreBase = self.getTableConfig(MTDefine.SCORE_BASE, 0)
                        uids = self.getBroadCastUIDs()
                        # 胡牌，局数不加1
                        ctInfo = self.getCreateTableInfo()
                        btInfo, _ = self.getBaoPaiInfo()
                        # 获取最后特殊牌的协议信息
                        lstInfo = self.tableTileMgr.getLastSpecialTiles()
                        # 血战情况下检查是不是最后结算
                        winFinal = True
                        loseFinal = True
                        sendWinSeat = self.__win_seats
                        if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
                            if self.getWinPlayerCount() < self.playerCount - 1:
                                loseFinal = False
                                winFinal = False
                            else:
                                for player in self.player:
                                    if player.hasHu:
                                        sendWinSeat.append(player.curSeatId)
                                        #                             # 已经胡了就不广播胡牌消息了
                                        #                             for player in self.player:
                                        #                                 if player.userId in uids and player.hasHu:
                                        #                                     uids.remove(player.userId)
                        customInfo = {
                            'ctInfo': ctInfo,
                            'btInfo': btInfo,
                            'lstInfo': lstInfo,
                            'awardInfo': awardInfo,
                            'winFinal': winFinal,
                            'loseFinal': loseFinal,
                            'winTiles': winTiles
                        }
                        sendTableScore = [0 for _ in range(self.playerCount)]
                        if self.__table_result.score:
                            sendTableScore = self.__table_result.score
                        self.msgProcessor.table_call_game_win_loose(uids
                                                                    , sendWinSeat
                                                                    , looses
                                                                    , observers
                                                                    , winMode
                                                                    , tile
                                                                    , sendTableScore
                                                                    , self.__round_result.score
                                                                    , scoreBase
                                                                    , fanPattern
                                                                    , customInfo)
                        # 处理胡牌，判断游戏是否结束，没结束继续游戏
                        self.processHu(cp)
                        return
                else:
                    # 有上家同时和牌 那么当前玩家不给予响应 除非上家过牌
                    return
        else:
            cp.actionHuByDrop(tile)
            # 自摸，一个人和，其他人都输
            for player in self.player:
                if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
                    if player.curSeatId != seatId and not player.hasHu:
                        looses.append(player.curSeatId)
                else:
                    if player.curSeatId != seatId:
                        looses.append(player.curSeatId)

        self.__cur_seat = seatId
        # 记录杠牌得分
        winBase = self.getTableConfig(MTDefine.WIN_BASE, 1)
        ftlog.debug('MajiangTableLogic.gameWin winBase: ', winBase)

        winMode = [MOneResult.WIN_MODE_LOSS for _ in range(len(self.__players))]
        winTiles = [0 for _ in range(len(self.__players))]
        fanPattern = [[] for _ in range(len(self.__players))]
        awardInfo = []
        NeedDropTiles = False
        if winBase > 0:
            result = MOneResultFactory.getOneResult(self.playMode)
            result.setResultType(MOneResult.RESULT_WIN)
            result.setLastSeatId(lastSeatId)
            result.setWinSeatId(self.curSeat)
            if self.curSeat not in self.__win_seats:
                self.__win_seats.append(self.curSeat)
            result.setWinSeats(self.__win_seats)
            result.setLatestGangState(self.latestGangState)
            result.setTableConfig(self.tableConfig)
            result.setBankerSeatId(self.queryBanker())
            result.setGangKai(gangKai)
            result.setBaoZhongBao(baoZhongBao)
            result.setMagicAfertTing(magicAfertTing)
            result.setTianHu(tianHu)
            result.setWuDuiHu(wuDuiHu)
            result.setPlayerCount(self.playerCount)
            if self.checkTableState(MTableState.TABLE_STATE_TING):
                result.setWinNodes(cp.winNodes)

            tingState = [0 for _ in range(self.playerCount)]
            colorState = [0 for _ in range(self.playerCount)]
            menState = [0 for _ in range(self.playerCount)]
            ziState = [[0, 0, 0, 0, 0, 0, 0] for _ in range(self.playerCount)]
            mingState = [0 for _ in range(self.playerCount)]
            playerAllTiles = [0 for _ in range(self.playerCount)]
            playerHandTiles = [0 for _ in range(self.playerCount)]
            playerGangTiles = [0 for _ in range(self.playerCount)]
            for player in self.player:
                # 听牌状态
                if player.isTing():
                    tingState[player.curSeatId] = 1
                # 花色状态    
                pTiles = player.copyTiles()
                tileArr = MTile.changeTilesToValueArr(MHand.copyAllTilesToList(pTiles))
                colorState[player.curSeatId] = MTile.getColorCount(tileArr)
                tempTiles = MTile.traverseTile(MTile.TILE_FENG)
                ziState[player.curSeatId] = tileArr[tempTiles[0]:tempTiles[len(tempTiles) - 1] + 1]
                # 玩家牌的情况
                playerAllTiles[player.curSeatId] = player.copyTiles()
                playerHandTiles[player.curSeatId] = player.copyHandTiles()
                playerGangTiles[player.curSeatId] = player.copyGangArray()
                # 门清状态
                if len(playerHandTiles[player.curSeatId]) == self.handCardCount:
                    menState[player.curSeatId] = 1
                # 明牌状态
                if player.isMing():
                    mingState[player.curSeatId] = 1

            result.setMenState(menState)
            result.setTingState(tingState)
            result.setColorState(colorState)
            result.setZiState(ziState)
            result.setMingState(mingState)
            result.setPlayerAllTiles(playerAllTiles)
            result.setPlayerGangTiles(playerGangTiles)
            result.setWinTile(tile)
            # 抽奖牌
            if self.playMode == MPlayMode.JIXI:
                awardTileCount = self.tableConfig.get(MTDefine.AWARD_TILE_COUNT, 1)
                awardTiles = self.tableTileMgr.popTile(awardTileCount)
                result.setAwardTiles(awardTiles)
            result.setActionID(self.actionID)
            result.setDaFeng(daFeng)
            result.setTableTileMgr(self.tableTileMgr)
            result.setWinRuleMgr(self.__win_rule_mgr)
            result.setMultiple(self.__win_rule_mgr.multiple)
            result.calcScore()
            self.setLatestGangState(-1)
            self.__win_rule_mgr.setLastGangSeat(-1)
            ftlog.debug("gangTileclearLatestGangState = ", self.latestGangState)
            if result.dropHuFlag == 1:
                NeedDropTiles = True
            self.roundResult.addRoundResult(result)
            # 加上牌桌上局数总分
            tableScore = [0 for _ in range(self.playerCount)]
            if self.tableResult.score:
                tableScore = self.tableResult.score
            currentScore = [0 for _ in range(self.playerCount)]
            for i in range(self.playerCount):
                currentScore[i] = tableScore[i] + self.roundResult.score[i]
            self.msgProcessor.table_call_score(self.getBroadCastUIDs(), currentScore, self.roundResult.delta)
            if MOneResult.KEY_WIN_MODE in result.results:
                winMode = result.results[MOneResult.KEY_WIN_MODE]
            if MOneResult.KEY_WIN_TILE in result.results:
                winTiles = result.results[MOneResult.KEY_WIN_TILE]
            if MPlayMode().isSubPlayMode(self.playMode, MPlayMode.KAWUXING):
                fanPattern = self.roundResult.fanPatterns
            else:
                if MOneResult.KEY_FAN_PATTERN in result.results:
                    fanPattern = result.results[MOneResult.KEY_FAN_PATTERN]
                # 带上明杠暗杠oneResult中的番型信息
                fanPattern = self.appendGangFanPattern(fanPattern)
            if MOneResult.KEY_AWARD_INFO in result.results:
                awardInfo = result.results[MOneResult.KEY_AWARD_INFO]

        # 点炮和，一个人和，一个人输
        if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
            hasHuCount = 0
            for player in self.player:
                if player.hasHu:
                    hasHuCount += 1
            if hasHuCount + 2 >= self.playerCount:
                self.__table_result.addResult(self.roundResult)
        else:
            self.__table_result.addResult(self.roundResult)
        scoreBase = self.getTableConfig(MTDefine.SCORE_BASE, 0)
        uids = self.getBroadCastUIDs()
        # 胡牌，局数不加1
        ctInfo = self.getCreateTableInfo()
        btInfo, _ = self.getBaoPaiInfo()
        # 获取最后特殊牌的协议信息
        lstInfo = self.tableTileMgr.getLastSpecialTiles()
        winFinal = True
        loseFinal = True
        if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
            if self.getWinPlayerCount() < self.playerCount - 1:
                loseFinal = False
                winFinal = False
            else:
                for player in self.player:
                    if player.hasHu:
                        wins.append(player.curSeatId)
                        #             # 已经胡了就不广播胡牌消息了
                        #             for player in self.player:
                        #                 if player.userId in uids and player.hasHu:
                        #                     uids.remove(player.userId)
        customInfo = {
            'ctInfo': ctInfo,
            'btInfo': btInfo,
            'lstInfo': lstInfo,
            'awardInfo': awardInfo,
            'winFinal': winFinal,
            'loseFinal': loseFinal,
            'winTiles': winTiles
        }
        # 十风或者十三幺时显示打出的牌
        dropTiles = self.tableTileMgr.dropTiles[seatId]
        if NeedDropTiles:
            customInfo['dropTiles'] = dropTiles
        sendTableScore = [0 for _ in range(self.playerCount)]
        if self.__table_result.score:
            sendTableScore = self.__table_result.score
        self.msgProcessor.table_call_game_win_loose(uids
                                                    , wins
                                                    , looses
                                                    , observers
                                                    , winMode
                                                    , tile
                                                    , sendTableScore
                                                    , self.__round_result.score
                                                    , scoreBase
                                                    , fanPattern
                                                    , customInfo)
        # 处理胡牌，判断游戏是否结束，没结束继续游戏
        self.processHu(cp)

    def gameFlow(self, seatId):
        """流局,所有人都是lose,gameflow字段为1"""
        ftlog.debug('MajiangTableLogic.gameFlow seatId:', seatId)

        # 结算的类型
        # 1 吃和
        # 0 自摸
        # -1 输牌
        tile = 0
        wins = []
        looses = []
        observers = []
        # cp = self.__players[seatId]
        # 流局所有人都是loose
        for player in self.player:
            if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
                if not player.hasHu:
                    looses.append(player.curSeatId)
            else:
                looses.append(player.curSeatId)
        if self.__add_card_processor.getState() != 0:
            exInfo = self.__add_card_processor.extendInfo
        elif self.__drop_card_processor.getState() != 0:
            self.__drop_card_processor.updateProcessor(self.actionID, seatId, MTableState.TABLE_STATE_HU, tile, None)
            self.__drop_card_processor.reset()

        # 记录杠牌得分
        winBase = self.getTableConfig(MTDefine.WIN_BASE, 1)
        ftlog.debug('MajiangTableLogic.gameWin winBase: ', winBase)
        pigs = []
        noTings = []
        winMode = [MOneResult.WIN_MODE_LOSS for _ in range(len(self.__players))]
        winTiles = [0 for _ in range(len(self.__players))]
        fanPattern = [[] for _ in range(len(self.__players))]
        if winBase > 0:
            result = MOneResultFactory.getOneResult(self.playMode)
            result.setResultType(MOneResult.RESULT_FLOW)
            result.setLastSeatId(seatId)
            result.setWinSeatId(-1)
            self.__win_seats = []
            result.setWinSeats(self.__win_seats)
            result.setTableConfig(self.tableConfig)
            result.setBankerSeatId(self.queryBanker())
            result.setPlayerCount(self.playerCount)
            tingState = [0 for _ in range(self.playerCount)]
            colorState = [0 for _ in range(self.playerCount)]
            menState = [0 for _ in range(self.playerCount)]
            ziState = [[0, 0, 0, 0, 0, 0, 0] for _ in range(self.playerCount)]

            for player in self.player:
                # 听牌状态
                if player.isTing():
                    tingState[player.curSeatId] = 1
                # 花色状态    
                pTiles = player.copyTiles()
                tileArr = MTile.changeTilesToValueArr(MHand.copyAllTilesToList(pTiles))
                colorState[player.curSeatId] = MTile.getColorCount(tileArr)
                tempTiles = MTile.traverseTile(MTile.TILE_FENG)
                ziState[player.curSeatId] = tileArr[tempTiles[0]:tempTiles[len(tempTiles) - 1] + 1]
                # 门清状态
                handTiles = player.copyHandTiles()
                if len(handTiles) == self.handCardCount:
                    menState[player.curSeatId] = 1

            result.setMenState(menState)
            result.setTingState(tingState)
            result.setColorState(colorState)
            result.setZiState(ziState)

            result.setWinTile(-1)
            result.setTableTileMgr(self.tableTileMgr)
            result.setWinRuleMgr(self.__win_rule_mgr)
            result.setMultiple(self.__win_rule_mgr.multiple)
            result.calcScore()
            self.setLatestGangState(-1)
            self.__win_rule_mgr.setLastGangSeat(-1)
            pigs = result.pigs
            noTings = result.noTings
            ftlog.debug("gangTileclearLatestGangState = ", self.latestGangState)
            self.roundResult.addRoundResult(result)
            # 加上牌桌上局数总分
            tableScore = [0 for _ in range(self.playerCount)]
            if self.tableResult.score:
                tableScore = self.tableResult.score
            currentScore = [0 for _ in range(self.playerCount)]
            for i in range(self.playerCount):
                currentScore[i] = tableScore[i] + self.roundResult.score[i]
            self.msgProcessor.table_call_score(self.getBroadCastUIDs(), currentScore, self.roundResult.delta)
            if MOneResult.KEY_WIN_MODE in result.results:
                winMode = result.results[MOneResult.KEY_WIN_MODE]
            if MOneResult.KEY_WIN_TILE in result.results:
                winTiles = result.results[MOneResult.KEY_WIN_TILE]
            if MPlayMode().isSubPlayMode(self.playMode, MPlayMode.KAWUXING):
                fanPattern = self.roundResult.fanPatterns
            else:
                if MOneResult.KEY_FAN_PATTERN in result.results:
                    fanPattern = result.results[MOneResult.KEY_FAN_PATTERN]
                # 带上明杠暗杠oneResult中的番型信息
                fanPattern = self.appendGangFanPattern(fanPattern)

        # 处理流局
        scoreBase = self.getTableConfig(MTDefine.SCORE_BASE, 0)
        # 目前玩法的流局都是真正的结束
        self.__table_result.addResult(self.roundResult)
        uids = self.getBroadCastUIDs()
        # 流局，局数不加1
        ctInfo = self.getCreateTableInfo()
        btInfo, _ = self.getBaoPaiInfo()
        #         if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
        #             # 已经胡了就不广播胡牌消息了
        #             for player in self.player:
        #                 if player.userId in uids and player.hasHu:
        #                     uids.remove(player.userId)
        for player in self.player:
            if player.hasHu:
                wins.append(player.curSeatId)
        customInfo = {
            'ctInfo': ctInfo,
            'btInfo': btInfo,
            'winFinal': True,
            'loseFinal': True,
            'pigs': pigs,
            'noTings': noTings,
            'winTiles': winTiles,
            'gameFlow': 1
        }
        self.msgProcessor.table_call_game_win_loose(uids
                                                    , wins
                                                    , looses
                                                    , observers
                                                    , winMode
                                                    , -1
                                                    , self.__table_result.score
                                                    , self.__round_result.score
                                                    , scoreBase
                                                    , fanPattern
                                                    , customInfo)
        # 处理流局,判断游戏是否结束
        self.processFlow()

    def getWinPlayerCount(self):
        count = 0
        for player in self.__players:
            if player.state == MPlayer.PLAYER_STATE_WON:
                count += 1
        return count

    def processHu(self, player):
        # 根据玩法需要是继续还是游戏结束
        ftlog.debug('MajiangTableLogic.processHu...')
        if self.checkTableState(MTableState.TABLE_STATE_XUEZHAN):
            player.setHasHu(True)
            ftlog.debug('MajiangTableLogic.processHu xuezhan...setHasHu:', player.hasHu)
            # 有三个人和了，游戏结束
            if self.getWinPlayerCount() >= self.playerCount - 1:
                self.resetGame(1)
                return True
            else:
                self.__win_seats = []
                self.__cur_seat = player.curSeatId
        elif self.checkTableState(MTableState.TABLE_STATE_XUELIU):
            ftlog.debug('MajiangTableLogic.processHu xueliu...')
            self.__cur_seat = player.curSeatId
        else:
            ftlog.debug('MajiangTableLogic.processHu normal gameover...')
            self.resetGame(1)
            return True

        return False

    def processFlow(self):
        # 流局游戏结束
        ftlog.debug('MajiangTableLogic.processFlow...')
        self.resetGame(0)
        return True

    def playerCancel(self, seatId):
        """用户选择放弃
        """
        tile = 0
        if self.__drop_card_processor.getState() != 0:
            ftlog.debug("playerCancel Drop", seatId)
            tile = self.__drop_card_processor.getTile()
            self.__drop_card_processor.resetSeatId(seatId)
        elif self.__add_card_processor.getState() != 0:
            ftlog.debug("playerCancel Add", seatId)
            tile = copy.deepcopy(self.__add_card_processor.getTile())
            addState = copy.deepcopy(self.__add_card_processor.state)
            cancelPlayer = self.player[seatId]
            # 成功取消才继续
            if self.__add_card_processor.updateProcessor(self.actionID, 0, seatId):
                ftlog.debug('MajiangTableLogic.playerCancel tile:', tile, ' addState:', addState)
                if cancelPlayer.isTing() and addState & MTableState.TABLE_STATE_HU:
                    ftlog.debug('MajiangTableLogic.playerCancel, user pass win, drop tile directly....')
                    self.dropTile(seatId, tile)
        elif self.__qiang_gang_hu_processor.getState() != 0:
            ftlog.debug("playerCancel QiangGangHu", seatId)
            tile = self.__qiang_gang_hu_processor.tile
            self.__qiang_gang_hu_processor.resetSeatId(seatId)
            if self.__qiang_gang_hu_processor.getState() == 0:
                ftlog.debug('__qiang_gang_hu_processor all player check')
                # 恢复挂起的杠牌状态 允许原来杠牌的玩家继续杠牌
                gangSeatId = self.__qiang_gang_hu_processor.curSeatId
                gangState = self.__qiang_gang_hu_processor.gangState
                gangSpecialTile = self.__qiang_gang_hu_processor.specialTile
                gangTile = self.__qiang_gang_hu_processor.tile
                gangPattern = self.__qiang_gang_hu_processor.gangPattern
                gangStyle = self.__qiang_gang_hu_processor.style
                self.__gangTile(self.curSeat, gangSeatId, gangTile, gangPattern, gangStyle, gangState, True,
                                gangSpecialTile, self.__qiang_gang_hu_processor.qiangGangSeats)
                ftlog.debug('__qiang_gang_hu_processor.qiangGangSeats = ',
                            self.__qiang_gang_hu_processor.qiangGangSeats)
                self.__qiang_gang_hu_processor.clearQiangGangSeats()
            if self.curState() == 0:
                self.__cur_seat = (self.__cur_seat - 1) % self.playerCount

        if self.__win_rule_mgr.isPassHu:
            # 别人出牌检查漏胡
            if self.checkTableState(MTableState.TABLE_STATE_HU) and seatId in self.__pass_hu_seats:
                # pass后将漏胡的牌加入漏胡牌数组,下次轮到自己回合时清空
                ftlog.debug("addPassHuTileByDrop", seatId, tile)
                self.tableTileMgr.addPassHuBySeatId(seatId, tile)

    def appendGangFanPattern(self, fanPattern):
        for ri in range(0, len(self.roundResult.roundResults) - 1)[::-1]:
            if self.roundResult.roundResults[ri].results[MOneResult.KEY_TYPE] == MOneResult.KEY_TYPE_NAME_HU:
                # 倒序统计杠牌信息
                break
            else:
                # 本局的杠牌记录
                if MOneResult.KEY_STAT in self.roundResult.roundResults[ri].results:
                    roundStat = self.roundResult.roundResults[ri].results[MOneResult.KEY_STAT]
                    for rsi in range(len(roundStat)):
                        for statItems in roundStat[rsi]:
                            for oneStatItemKey in statItems.keys():
                                if oneStatItemKey == MOneResult.STAT_MINGGANG:
                                    mingGangName = self.roundResult.roundResults[ri].statType[MOneResult.STAT_MINGGANG][
                                        "name"]
                                    mingGangFanPattern = [mingGangName, str(1) + "番"]
                                    if mingGangFanPattern not in fanPattern[rsi]:
                                        fanPattern[rsi].append(mingGangFanPattern)

                                if oneStatItemKey == MOneResult.STAT_ANGANG:
                                    anGangName = self.roundResult.roundResults[ri].statType[MOneResult.STAT_ANGANG][
                                        "name"]
                                    anGangFanPattern = [anGangName, str(1) + "番"]
                                    if anGangFanPattern not in fanPattern[rsi]:
                                        fanPattern[rsi].append(anGangFanPattern)
        return fanPattern

    def printTableTiles(self):
        """打印牌桌的所有手牌信息"""
        for player in self.player:
            player.printTiles()
        self.tableTileMgr.printTiles()

    def refixTableStateByConfig(self):
        """根据自建房配置调整牌桌状态"""
        itemParams = self.getTableConfig(MFTDefine.ITEMPARAMS, {})
        chipengSetting = itemParams.get('chipengsetting', 0)
        if chipengSetting == 2:
            if self.checkTableState(self.__table_stater.TABLE_STATE_CHI):
                self.__table_stater.clearState(self.__table_stater.TABLE_STATE_CHI)
                ftlog.debug("refixTableStateByConfig remove TABLE_STATE_CHI, now chi state =",
                            self.checkTableState(self.__table_stater.TABLE_STATE_CHI))
        elif chipengSetting == 1:
            if not self.checkTableState(self.__table_stater.TABLE_STATE_CHI):
                self.__table_stater.setState(self.__table_stater.TABLE_STATE_CHI)
                ftlog.debug("refixTableStateByConfig add TABLE_STATE_CHI, now chi state =",
                            self.checkTableState(self.__table_stater.TABLE_STATE_CHI))
                # 默认不改动吃的状态

    def refixTableMultipleByConfig(self):
        """根据传入配置调整输赢倍数"""
        itemParams = self.getTableConfig(MFTDefine.ITEMPARAMS, {})
        multiple = itemParams.get('multiple', 1)
        if multiple >= 1 and multiple <= 8:
            self.__win_rule_mgr.setMultiple(multiple)

    def refixTableZimoBonusByConfig(self):
        """根据传入配置调整自摸加番"""
        itemParams = self.getTableConfig(MFTDefine.ITEMPARAMS, {})
        zimoBonus = itemParams.get('zimoBonus', 1)
        if zimoBonus >= 1 and zimoBonus <= 2:
            self.__win_rule_mgr.setZimoBonus(zimoBonus)

    def reloadTableConfig(self):
        """根据传入配置调整参数"""
        itemParams = self.getTableConfig(MFTDefine.ITEMPARAMS, {})
        ftlog.info("loadTableConfig itemParams=", itemParams)
        if itemParams:
            self.__win_rule_mgr.setItemParams(itemParams)

    def sendLeaveMessage(self, userId):
        """userId:离线者的userId"""
        onlineInfo = []
        if self.player:
            for index in range(len(self.player)):
                onlineInfoTemp = {}
                onlineInfoTemp['seatId'] = index
                if self.player[index]:
                    if self.player[index].userId == userId:
                        onlineInfoTemp["online"] = 0
                    else:
                        if self.player[index].playerLeave:
                            onlineInfoTemp["online"] = 0
                        else:
                            onlineInfoTemp["online"] = 1
                else:
                    onlineInfoTemp["online"] = 0
                onlineInfo.append(onlineInfoTemp)
        uids = self.getBroadCastUIDs(userId)
        ftlog.info("sendLeaveMessage onlineInfo:", onlineInfo)
        self.__msg_processor.table_call_online_state(uids, onlineInfo)

    def sendEnterMessage(self):
        """userId:离线者的userId"""
        onlineInfo = []
        if self.player:
            for index in range(len(self.player)):
                onlineInfoTemp = {}
                onlineInfoTemp['seatId'] = index
                if self.player[index]:
                    ftlog.info("sendLeaveMessage self.player[index].playerLeave:", self.player[index].playerLeave)
                    if self.player[index].playerLeave:
                        onlineInfoTemp["online"] = 0
                    else:
                        onlineInfoTemp["online"] = 1
                else:
                    ftlog.info("sendLeaveMessage self.player:", self.player)
                    onlineInfoTemp["online"] = 0
                onlineInfo.append(onlineInfoTemp)
        uids = self.getBroadCastUIDs()
        ftlog.info("sendLeaveMessage onlineInfo:", onlineInfo)
        self.__msg_processor.table_call_online_state(uids, onlineInfo)

    def setPlayerLeave(self, seatId, leave):
        """设置某个玩家的离开状态"""
        if seatId < 0 or seatId > self.playerCount - 1:
            return
        if self.player:
            if self.player[seatId]:
                if leave:
                    self.player[seatId].setPlayerLeave(True)
                    ftlog.debug("table_logic.setPlayerLeaveTrue:", self.player[seatId].playerLeave)
                else:
                    self.player[seatId].setPlayerLeave(False)
                    ftlog.debug("table_logic.setPlayerLeaveFalse:", self.player[seatId].playerLeave)

    def sendNetStateToUser(self, userId, seatId, timeStamp, delta):
        """处理玩家网络状态并发送"""
        if self.__player_ping.has_key(userId):
            userData = self.__player_ping.get(userId, {})
            userData = {
                "lastTs": timeStamp,
                "delta": delta
            }
            self.__player_ping[userId] = userData
            ftlog.debug("curTimestemp:", timeStamp
                        , "delta", delta)
        else:
            self.__player_ping[userId] = {
                "lastTs": timeStamp,
                "delta": delta
            }

        pingArr = []
        for index in range(self.playerCount):
            if self.player[index]:
                if self.__player_ping.has_key(self.player[index].userId):
                    pingArr.append(self.__player_ping[self.player[index].userId].get("delta", 0))
                else:
                    pingArr.append(0)
            else:
                pingArr.append(-1)
        self.__msg_processor.table_call_ping(userId, pingArr, timeStamp)

    def exchangeMagicTilePeng(self, userId, pengInfo):
        """
        昭通换碰牌中的癞子
        """
        pass

    def exchangeMagicTileGang(self, userId, gangInfo):
        """昭通换杠牌中的癞子"""
        pass

    def isStart(self):
        if self.__table_win_state != MTableState.TABLE_STATE_NONE and self.__table_win_state != MTableState.TABLE_STATE_GAME_OVER:
            return True
        return False
