# -*- coding=utf-8
"""
Created on 2016年9月23日
上行行为处理

@author: zhaol
"""
from difang.majiang2.ai.tile_value import MTileValue
from difang.majiang2.table.table_config_define import MTDefine
from difang.majiang2.table_state.state import MTableState
from freetime.util import log as ftlog


class ActionHandler(object):
    # 出
    ACTION_DROP = 1
    # 吃
    ACTION_CHI = 2
    # 碰
    ACTION_PENG = 3
    # 杠
    ACTION_GANG = 4
    # 听
    ACTION_TING = 5
    # 和
    ACTION_HU = 6

    def __init__(self):
        super(ActionHandler, self).__init__()
        self.__table = None

    @property
    def table(self):
        """
        :rtype AbstractMajiangTableLogic
        """
        return self.__table

    def setTable(self, table):
        """设置牌桌"""
        self.__table = table

    def processAction(self, cmd):
        pass

    def updateTimeOut(self, delta):
        if self.table.addCardProcessor.getState() > 0:
            self.table.addCardProcessor.updateTimeOut(delta)

        if self.table.dropCardProcessor.getState() > 0:
            self.table.dropCardProcessor.updateTimeOut(delta)

    def doAutoAction(self):
        """自动行为，关注当前牌局是否正在开始"""
        ftlog.debug('ActionHandler.checkState...')
        if not self.table.isPlaying():
            return

        if self.table.curState() == MTableState.TABLE_STATE_NEXT:
            ftlog.debug('ActionHandler.gameNext...')
            self.table.gameNext()
            return True
        # ftlog.debug('ActionHandler.checkState.addCardProcessor...')   
        if MTDefine.INVALID_SEAT != self.table.addCardProcessor.hasAutoDecideAction(self.table.curSeat,
                                                                                    self.table.tableConfig[
                                                                                        MTDefine.TRUSTTEE_TIMEOUT]):
            ftlog.debug('ActionHandler.addCardProcessor.hasAutoDecideAction curSeat: ', self.table.curSeat
                        , ' trustTeeSet:', self.table.tableConfig[MTDefine.TRUSTTEE_TIMEOUT])
            self.autoProcessAddCard()
            return True
        ftlog.debug('ActionHandler.checkState.dropCardProcessor...')
        seatId = self.table.dropCardProcessor.hasAutoDecideAction(self.table.curSeat,
                                                                  self.table.tableConfig[MTDefine.TRUSTTEE_TIMEOUT])
        if seatId != MTDefine.INVALID_SEAT:
            ftlog.debug('ActionHandler.dropCardProcessor.hasAutoDecideAction seatId:', seatId)
            self.autoProcessDropCard(seatId)
            return True
        # ftlog.debug('ActionHandler.checkState.qiangGangHuProcessor...')
        seatId = self.table.qiangGangHuProcessor.hasAutoDecideAction(self.table.curSeat,
                                                                     self.table.tableConfig[MTDefine.TRUSTTEE_TIMEOUT])
        if seatId != MTDefine.INVALID_SEAT:
            ftlog.debug('ActionHandler.qiangGangHuProcessor.hasAutoDecideAction seatId:', seatId)
            self.autoProcessQiangGangHu(seatId)
            return True

        return False

    def autoProcessQiangGangHu(self, seatId):
        """自动处理抢杠和"""
        extend = self.table.qiangGangHuProcessor.getExtendResultBySeatId(seatId)
        #         choose = extend.getChoosedInfo(MTableState.TABLE_STATE_QIANGGANG)
        #         winInfo['tile'] = tile
        #         winInfo['qiangGang'] = 1
        #         winInfo['gangSeatId'] = self.curSeat
        gangTile = self.table.qiangGangHuProcessor.tile
        self.table.grabHuGang(seatId, gangTile)

    def autoProcessDropCard(self, seatId):
        """托管出牌操作
        简单点儿：
        1）能和就和
        2）能杠就杠
        3）能碰就碰
        4）能吃就吃
        """
        #         isResponsed = self.table.dropCardProcessor.getResponseBySeatId(seatId)
        seatState = self.table.dropCardProcessor.getStateBySeatId(seatId)
        if not self.table.dropCardProcessor.allResponsed():
            ftlog.debug("autoProcessDropCard player has responsed seatId=", seatId)
            return
        nowTile = self.table.dropCardProcessor.tile
        if seatState > 0:
            if seatState & MTableState.TABLE_STATE_HU:
                self.table.gameWin(seatId, nowTile)
                return

            extend = self.table.dropCardProcessor.getExtendResultBySeatId(seatId)
            choose = extend.getChoosedInfo(seatState)
            ftlog.debug('autoProcessDropCard gang choose:', choose)

            if seatState & MTableState.TABLE_STATE_GANG:
                special_tile = self.getPiguTile()
                # AI自动选择杠听
                if seatState & MTableState.TABLE_STATE_GRABTING:
                    self.table.gangTile(seatId
                                        , nowTile
                                        , choose['pattern']
                                        , choose['style']
                                        , MTableState.TABLE_STATE_GANG | MTableState.TABLE_STATE_GRABTING
                                        , special_tile)
                else:
                    self.table.gangTile(seatId
                                        , nowTile
                                        , choose['pattern']
                                        , choose['style']
                                        , MTableState.TABLE_STATE_GANG
                                        , special_tile)
                return

            if seatState & MTableState.TABLE_STATE_PENG:
                # AI自动选择碰听
                ftlog.debug('seatId:', seatId, ' nowTile:', nowTile, ' extend:', extend)
                if seatState & MTableState.TABLE_STATE_GRABTING:
                    self.table.pengTile(seatId, nowTile, choose['pattern'],
                                        MTableState.TABLE_STATE_PENG | MTableState.TABLE_STATE_GRABTING)
                else:
                    self.table.pengTile(seatId, nowTile, choose, MTableState.TABLE_STATE_PENG)
                return

            if seatState & MTableState.TABLE_STATE_CHI:
                # 这里的准确逻辑是，如果吃的牌在吃听里，继续转听。如果吃的牌不在听牌里，按普通的吃处理
                if seatState & MTableState.TABLE_STATE_GRABTING:
                    self.table.chiTile(seatId
                                       , nowTile
                                       , choose['pattern']
                                       , MTableState.TABLE_STATE_CHI | MTableState.TABLE_STATE_GRABTING)
                else:
                    self.table.chiTile(seatId, nowTile, choose, MTableState.TABLE_STATE_CHI)
                return

            # 未处理的状态，自动取消
            self.table.playerCancel(seatId)

    def autoProcessAddCard(self):
        player = self.table.addCardProcessor.getPlayer()
        nowTile = self.table.addCardProcessor.getTile()
        magicTiles = self.table.tableTileMgr.getMagicTiles()
        if self.table.addCardProcessor.getState() & MTableState.TABLE_STATE_HU:
            self.table.gameWin(player.curSeatId, nowTile)
            return

        exInfo = self.table.addCardProcessor.extendInfo
        if self.table.addCardProcessor.getState() & MTableState.TABLE_STATE_TING:
            _pattern, newState = exInfo.getFirstPattern(MTableState.TABLE_STATE_TING, magicTiles)
            tingInfo = exInfo.getChoosedInfo(newState)
            ftlog.debug('MajiangTable.autoProcessAddCard tingInfo:', tingInfo)
            if 'ting' in tingInfo:
                tingInfo = tingInfo['ting'][0]
            ftlog.debug('MajiangTable.autoProcessAddCard tingInfo:', tingInfo)
            # 选择打掉的牌，用剩下的牌听，自动选择可胡牌数最多的解
            self.table.ting(player.curSeatId, tingInfo['dropTile'], self.table.addCardProcessor.extendInfo)
            return

        if self.table.addCardProcessor.getState() & MTableState.TABLE_STATE_GANG:
            _pattern, newState = exInfo.getFirstPattern(MTableState.TABLE_STATE_GANG, magicTiles)
            ftlog.debug('MajiangTable.autoProcessAddCard getFirstGangPattern pattern:', _pattern
                        , ' newState:', newState)

            exInfo.updateState(newState, _pattern)
            gangInfo = exInfo.getChoosedInfo(newState)

            ftlog.debug('MajiangTable.autoProcessAddCard gangInfo:', gangInfo)
            style = gangInfo['style']
            pattern = gangInfo['pattern']
            special_tile = self.getPiguTile()
            self.table.gangTile(player.curSeatId, nowTile, pattern, style, MTableState.TABLE_STATE_GANG, special_tile)
            return

        ftlog.debug(player.copyTiles())
        ftlog.debug(player.isTing())
        minTile, minValue = MTileValue.getBestDropTile(player.copyTiles()
                                                       , self.table.tableTileMgr.getTiles()
                                                       , self.table.playMode
                                                       , nowTile
                                                       , player.isTing()
                                                       , self.table.tableTileMgr.getMagicTiles(player.isTing())
                                                       , self.table.tingRule)

        ftlog.debug('autoProcessAddCard.getBestDropTile minTile:', minTile, ' minValue:', minValue)

        # 最后，出价值最小的牌
        self.table.dropTile(player.curSeatId, minTile)

    def getPiguTile(self):
        """获取翻屁股"""
        if self.table.checkTableState(MTableState.TABLE_STATE_FANPIGU):
            pigus = self.table.tableTileMgr.getPigus()
            if pigus and len(pigus) > 0:
                return pigus[0]
        return None
