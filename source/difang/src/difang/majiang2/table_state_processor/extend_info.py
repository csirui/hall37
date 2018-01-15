# -*- coding=utf-8
'''
Created on 2016年9月23日

用户在某个状态时的选择内容
extend
    chi        []
    peng       []
    gang       []
    ting       []
    win        []
    chiTing    []
    pengTing   []
    gangTing   []
    
@author: zhaol

'''

from difang.majiang2.table_state.state import MTableState
from freetime.util import log as ftlog


class MTableStateExtendInfo(object):
    CHI = 'chi'
    PENG = 'peng'
    GANG = 'gang'
    TING = 'ting'
    GRAB_CHI_TING = 'chiTing'
    GRAB_PENG_TING = 'pengTing'
    GRAB_GANG_TING = 'gangTing'
    GRAB_ZHAN_TING = 'zhanTing'
    WIN = 'win'
    QIANG_GANG_HU = 'qiangGangHu'

    def __init__(self):
        super(MTableStateExtendInfo, self).__init__()
        self.__extend = {}

    @property
    def extend(self):
        return self.__extend

    def setExtend(self, extend):
        """设置扩展信息"""
        self.__extend = extend

    def appendInfo(self, state, info):
        ftlog.debug('MTableStateExtendInfo appendInfo state:', state, ' info:', info)
        if (state & MTableState.TABLE_STATE_CHI) and (state & MTableState.TABLE_STATE_GRABTING):
            if self.GRAB_CHI_TING not in self.__extend:
                self.__extend[self.GRAB_CHI_TING] = []
            self.__extend[self.GRAB_CHI_TING].append(info)
            return

        if (state & MTableState.TABLE_STATE_PENG) and (state & MTableState.TABLE_STATE_GRABTING):
            if self.GRAB_PENG_TING not in self.__extend:
                self.__extend[self.GRAB_PENG_TING] = []
            self.__extend[self.GRAB_PENG_TING].append(info)
            return

        if (state & MTableState.TABLE_STATE_GANG) and (state & MTableState.TABLE_STATE_GRABTING):
            if self.GRAB_GANG_TING not in self.__extend:
                self.__extend[self.GRAB_GANG_TING] = []
            self.__extend[self.GRAB_GANG_TING].append(info)
            return

        if (state & MTableState.TABLE_STATE_ZHAN) and (state & MTableState.TABLE_STATE_GRABTING):
            if self.GRAB_ZHAN_TING not in self.__extend:
                self.__extend[self.GRAB_ZHAN_TING] = []
            self.__extend[self.GRAB_ZHAN_TING].append(info)
            return

        if state & MTableState.TABLE_STATE_HU:
            if self.WIN not in self.__extend:
                self.__extend[self.WIN] = []
            self.__extend[self.WIN].append(info)
            return

        if state & MTableState.TABLE_STATE_QIANGGANG:
            if self.QIANG_GANG_HU not in self.__extend:
                self.__extend[self.QIANG_GANG_HU] = []
            self.__extend[self.QIANG_GANG_HU].append(info)
            return

        if state & MTableState.TABLE_STATE_TING:
            if self.TING not in self.__extend:
                self.__extend[self.TING] = []
            self.__extend[self.TING].extend(info)
            return

        if state & MTableState.TABLE_STATE_GANG:
            if self.GANG not in self.__extend:
                self.__extend[self.GANG] = []
            self.__extend[self.GANG].append(info)
            ftlog.debug('MTableStateExtendInfo.appendInfo append gang node:', info, ' after add:',
                        self.__extend[self.GANG])
            return

        if state & MTableState.TABLE_STATE_PENG:
            if self.PENG not in self.__extend:
                self.__extend[self.PENG] = []
            self.__extend[self.PENG].append(info)
            return

        if state & MTableState.TABLE_STATE_CHI:
            if self.CHI not in self.__extend:
                self.__extend[self.CHI] = []
            self.__extend[self.CHI].append(info)
            return

        if state & MTableState.TABLE_STATE_FANPIGU:
            if 'pigus' not in self.__extend:
                self.__extend['pigus'] = []
            self.__extend['pigus'] = info
            return

    def setInfo(self, state, info):
        if (state & MTableState.TABLE_STATE_CHI) and (state & MTableState.TABLE_STATE_GRABTING):
            self.__extend[self.GRAB_CHI_TING] = info
            return

        if (state & MTableState.TABLE_STATE_PENG) and (state & MTableState.TABLE_STATE_GRABTING):
            self.__extend[self.GRAB_PENG_TING] = info
            return

        if (state & MTableState.TABLE_STATE_GANG) and (state & MTableState.TABLE_STATE_GRABTING):
            self.__extend[self.GRAB_GANG_TING] = info
            return

        if (state & MTableState.TABLE_STATE_ZHAN) and (state & MTableState.TABLE_STATE_GRABTING):
            self.__extend[self.GRAB_ZHAN_TING] = info
            return

        if state & MTableState.TABLE_STATE_HU:
            self.__extend[self.WIN] = info
            return

        if state & MTableState.TABLE_STATE_TING:
            self.__extend[self.TING] = info
            return

        if state & MTableState.TABLE_STATE_GANG:
            self.__extend[self.GANG] = info
            return

        if state & MTableState.TABLE_STATE_PENG:
            self.__extend[self.PENG] = info
            return

        if state & MTableState.TABLE_STATE_CHI:
            self.__extend[self.CHI] = info
            return

    def getChoosedInfo(self, state):
        if not state:
            ftlog.error('MTableStateExtendInfo.getChoosedInfo state error!')

        if (state & MTableState.TABLE_STATE_CHI) and (state & MTableState.TABLE_STATE_GRABTING):
            return self.__extend[self.GRAB_CHI_TING][0]

        if (state & MTableState.TABLE_STATE_PENG) and (state & MTableState.TABLE_STATE_GRABTING):
            return self.__extend[self.GRAB_PENG_TING][0]

        if (state & MTableState.TABLE_STATE_GANG) and (state & MTableState.TABLE_STATE_GRABTING):
            return self.__extend[self.GRAB_GANG_TING][0]

        if (state & MTableState.TABLE_STATE_ZHAN) and (state & MTableState.TABLE_STATE_GRABTING):
            return self.__extend[self.GRAB_ZHAN_TING][0]

        if state & MTableState.TABLE_STATE_HU:
            return self.__extend[self.WIN][0]

        if state & MTableState.TABLE_STATE_TING:
            return self.__extend[self.TING][0]

        if state & MTableState.TABLE_STATE_GANG:
            ftlog.debug('MTableStateExtendInfo.getChoosedInfo gangs:', self.__extend[self.GANG]
                        , ' choosed:', self.__extend[self.GANG][0])
            return self.__extend[self.GANG][0]

        if state & MTableState.TABLE_STATE_PENG:
            return self.__extend[self.PENG][0]

        if state & MTableState.TABLE_STATE_CHI:
            return self.__extend[self.CHI][0]

        if state & MTableState.TABLE_STATE_QIANGGANG:
            return self.__extend[self.QIANG_GANG_HU][0]

    def updateInfo(self, state):
        extend = {}
        if (state & MTableState.TABLE_STATE_CHI) and (state & MTableState.TABLE_STATE_GRABTING):
            extend[self.GRAB_CHI_TING] = self.__extend[self.GRAB_CHI_TING]
            self.__extend = extend
            return

        if (state & MTableState.TABLE_STATE_PENG) and (state & MTableState.TABLE_STATE_GRABTING):
            extend[self.GRAB_PENG_TING] = self.__extend[self.GRAB_PENG_TING]
            self.__extend = extend
            return

        if (state & MTableState.TABLE_STATE_GANG) and (state & MTableState.TABLE_STATE_GRABTING):
            extend[self.GRAB_GANG_TING] = self.__extend[self.GRAB_GANG_TING]
            self.__extend = extend
            return

        if (state & MTableState.TABLE_STATE_ZHAN) and (state & MTableState.TABLE_STATE_GRABTING):
            extend[self.GRAB_ZHAN_TING] = self.__extend[self.GRAB_ZHAN_TING]
            self.__extend = extend
            return

        if state & MTableState.TABLE_STATE_HU:
            extend[self.WIN] = self.__extend[self.WIN]
            self.__extend = extend
            return

        if state & MTableState.TABLE_STATE_TING:
            ftlog.debug('old:', self.__extend)
            extend[self.TING] = self.__extend[self.TING]
            self.__extend = extend
            ftlog.debug('new:', self.__extend)

            return

        if state & MTableState.TABLE_STATE_GANG:
            extend[self.GANG] = self.__extend[self.GANG]
            self.__extend = extend
            return

        if state & MTableState.TABLE_STATE_PENG:
            extend[self.PENG] = self.__extend[self.PENG]
            self.__extend = extend
            return

        if state & MTableState.TABLE_STATE_CHI:
            extend[self.CHI] = self.__extend[self.CHI]
            self.__extend = extend
            return

    def getAllDropTilesInTing(self):
        """获取所有的听牌解"""
        dropTiles = []
        if self.TING not in self.__extend:
            return dropTiles

        tingReArr = self.__extend[self.TING]
        for tingSolution in tingReArr:
            dropTile = tingSolution['dropTile']
            dropTiles.append(dropTile)

        ftlog.debug('MTableStateExtendInfo.getAllDropTilesInTing dropTiles:', dropTiles)
        return dropTiles

    def getWinNodesByDropTile(self, dropTile):
        tingInfos = None
        if self.TING in self.__extend:
            tingInfos = self.__extend[self.TING]

        if self.GRAB_CHI_TING in self.__extend:
            tingInfos = self.__extend[self.GRAB_CHI_TING][0][self.TING]

        if self.GRAB_PENG_TING in self.__extend:
            tingInfos = self.__extend[self.GRAB_PENG_TING][0][self.TING]

        if self.GRAB_GANG_TING in self.__extend:
            tingInfos = self.__extend[self.GRAB_GANG_TING][0][self.TING]

        if self.GRAB_ZHAN_TING in self.__extend:
            tingInfos = self.__extend[self.GRAB_ZHAN_TING][0][self.TING]

        if not tingInfos:
            ftlog.error('getWinNodesByDropTile tingInfos is None, need check:', self.__extend)
            return None

        ftlog.debug('getWinNodesByDropTile tingInfos:', tingInfos)
        for tingSolution in tingInfos:
            if tingSolution['dropTile'] == dropTile:
                return tingSolution['winNodes']

        return None

    def getTingResult(self, tableTileMgr, seatId):
        """获取新的吃牌扩展信息"""
        tings = self.__extend.get(self.TING, None)
        if not tings:
            return None

        tingsSolution = []
        for tingNode in tings:
            tingSolution = []
            tingSolution.append(tingNode['dropTile'])
            winsSolution = []
            winNodes = tingNode['winNodes']
            for winNode in winNodes:
                winSolution = []
                winSolution.append(winNode['winTile'])
                winSolution.append(1)
                dropCount = 0
                # 宝牌中的也算
                magicTiles = tableTileMgr.getMagicTiles(True)
                abandoneMagicTiles = tableTileMgr.getAbandonedMagics()
                if (winNode['winTile'] in magicTiles) or (winNode['winTile'] in abandoneMagicTiles):
                    dropCount += 1
                dropCount += tableTileMgr.getVisibleTilesCount(winNode['winTile'], True, seatId)
                ftlog.debug('MTableStateExtendInfo.getTingResult dropCount', dropCount)
                winSolution.append(4 - dropCount)
                winsSolution.append(winSolution)
            tingSolution.append(winsSolution)
            tingsSolution.append(tingSolution)

        ftlog.debug('MTableStateExtendInfo.getTingResult', tingsSolution)
        return tingsSolution

    def getTingLiangResult(self, tableTileMgr):
        """获取新的吃牌扩展信息，亮牌的信息"""
        # 卡五星中，听牌就是亮牌
        # 听牌逻辑太复杂，所以服务端不在额外增加状态，仅在发消息时，在听牌基础上修改数据
        mode = tableTileMgr.getTingLiangMode()
        if mode:
            return {"mode": mode}
        return None

    def getChiPengGangResult(self, state):
        if state & MTableState.TABLE_STATE_CHI:
            chis = self.__extend.get(self.CHI, None)
            return chis

        if state & MTableState.TABLE_STATE_PENG:
            pengs = self.__extend.get(self.PENG, None)
            return pengs

        if state & MTableState.TABLE_STATE_GANG:
            gangs = self.__extend.get(self.GANG, None)
            return gangs

        if state & MTableState.TABLE_STATE_HU:
            wins = self.__extend.get(self.WIN, None)
            return wins

    def getChiPengGangTingResult(self, state):
        if state & MTableState.TABLE_STATE_CHI:
            chiTings = self.__extend.get(self.GRAB_CHI_TING, None)
            if not chiTings:
                return None

            ces = []
            for ct in chiTings:
                ces.append(ct['pattern'])
            return ces

        if state & MTableState.TABLE_STATE_PENG:
            pengTings = self.__extend.get(self.GRAB_PENG_TING, None)
            if not pengTings:
                return None

            pes = []
            for pt in pengTings:
                pes.append(pt['pattern'])
            return pes

        if state & MTableState.TABLE_STATE_GANG:
            gangTings = self.__extend.get(self.GRAB_GANG_TING, None)
            if not gangTings:
                return None

            ges = []
            for gt in gangTings:
                ges.append({"tile": gt['tile'], "pattern": gt['pattern'], "style": gt['style']})
            return ges

        if state & MTableState.TABLE_STATE_ZHAN:
            zhanTings = self.__extend.get(self.GRAB_ZHAN_TING, None)
            if not zhanTings:
                return None

            ges = []
            for gt in zhanTings:
                ges.append({"tile": gt['tile'], "pattern": gt['pattern']})
            return ges

    def updateState(self, state, pattern):
        """用户做出了选择，更新"""
        if state & MTableState.TABLE_STATE_CHI:
            if state & MTableState.TABLE_STATE_GRABTING:
                chiTing = self.getChoiceByPattern(pattern, self.__extend[self.GRAB_CHI_TING])
                if not chiTing:
                    ftlog.error('MTableStateExtendInfo.updateState error, pattern:', pattern
                                , ' extend:', self.__extend)
                    return False

                self.__extend[self.GRAB_CHI_TING] = [chiTing]
            else:
                if pattern not in self.__extend[self.CHI]:
                    ftlog.error('MTableStateExtendInfo.updateState error, pattern:', pattern
                                , ' extend:', self.__extend)
                    return False

                self.__extend[self.CHI] = [pattern]

            self.updateInfo(state)
            return True

        if state & MTableState.TABLE_STATE_PENG:
            if state & MTableState.TABLE_STATE_GRABTING:
                pengTing = self.getChoiceByPattern(pattern, self.__extend[self.GRAB_PENG_TING])
                if not pengTing:
                    ftlog.error('MTableStateExtendInfo.updateState error, pattern:', pattern
                                , ' extend:', self.__extend)
                    return False

                self.__extend[self.GRAB_PENG_TING] = [pengTing]
            else:
                if pattern not in self.__extend[self.PENG]:
                    ftlog.error('MTableStateExtendInfo.updateState error, pattern:', pattern
                                , ' extend:', self.__extend)
                    return False

                self.__extend[self.PENG] = [pattern]

            self.updateInfo(state)
            return True

        if state & MTableState.TABLE_STATE_GANG:
            if state & MTableState.TABLE_STATE_GRABTING:
                ftlog.debug('MTableStateExtendInfo.updateState try gangTing, pattern:', pattern, ' extend:',
                            self.__extend)
                gangTing = self.getChoiceByPattern(pattern, self.__extend[self.GRAB_GANG_TING])
                if not gangTing:
                    ftlog.error('MTableStateExtendInfo.updateState error, pattern:', pattern
                                , ' extend:', self.__extend)
                    return False

                self.__extend[self.GRAB_GANG_TING] = [gangTing]
            else:
                ftlog.debug('MTableStateExtendInfo.updateState pattern:', pattern, ' extend:', self.__extend)
                gang = self.getChoiceByPattern(pattern['pattern'], self.__extend[self.GANG])
                if not gang:
                    ftlog.error('MTableStateExtendInfo.updateState error, pattern:', pattern
                                , ' extend:', self.__extend)
                    return False

                self.__extend[self.GANG] = [pattern]

            self.updateInfo(state)
            return True

        if state & MTableState.TABLE_STATE_ZHAN:
            if state & MTableState.TABLE_STATE_GRABTING:
                ftlog.debug('MTableStateExtendInfo.updateState try zhanTing, pattern:', pattern, ' extend:',
                            self.__extend)
                zhanTing = self.getChoiceByPattern(pattern, self.__extend[self.GRAB_ZHAN_TING])
                if not zhanTing:
                    ftlog.error('MTableStateExtendInfo.updateState error, pattern:', pattern
                                , ' extend:', self.__extend)
                    return False

                self.__extend[self.GRAB_ZHAN_TING] = [zhanTing]

            self.updateInfo(state)
            return True

        if state & MTableState.TABLE_STATE_HU:
            return True

        ftlog.error('MTableStateExtendInfo.updateState error state:', state, ' pattern:', pattern)
        return False

    def getFirstPattern(self, state, magicTiles):
        """获取默认解"""
        ftlog.debug('MTableStateExtendInfo.getFirstPattern in state:', state)

        if (state & MTableState.TABLE_STATE_GRABTING) or (state & MTableState.TABLE_STATE_TING):
            gangTing = self.__extend.get(self.GRAB_GANG_TING, None)
            if gangTing:
                state = MTableState.TABLE_STATE_GRABTING | MTableState.TABLE_STATE_GANG
                return gangTing[0]['pattern'], state

            pengTing = self.__extend.get(self.GRAB_PENG_TING, None)
            if pengTing:
                state = MTableState.TABLE_STATE_GRABTING | MTableState.TABLE_STATE_PENG
                return pengTing[0]['pattern'], state

            chiTings = self.__extend.get(self.GRAB_CHI_TING, None)
            if chiTings:
                state = MTableState.TABLE_STATE_GRABTING | MTableState.TABLE_STATE_CHI
                return chiTings[0]['pattern'], state

            zhanTings = self.__extend.get(self.GRAB_ZHAN_TING, None)
            if zhanTings:
                state = MTableState.TABLE_STATE_GRABTING | MTableState.TABLE_STATE_ZHAN
                return zhanTings[0]['pattern'], state

            ting = self.__extend.get(self.TING, None)
            if not ting:
                return None, state
            return ting[0], state

            ftlog.debug('MTableStateExtendInfo.getFirstPattern out state:', state)
            return None, state

        if state & MTableState.TABLE_STATE_HU:
            win = self.__extend.get(self.WIN, None)
            if not win:
                return None, state
            return win[0], state

        if state & MTableState.TABLE_STATE_GANG:
            gang = self.__extend.get(self.GANG, None)
            if not gang:
                return None, state
            return gang[0], state

        if state & MTableState.TABLE_STATE_PENG:
            peng = self.__extend.get(self.PENG, None)
            if not peng:
                return None, state
            # 碰牌,优先选择不带癞子的
            for temp in peng:
                for magicTile in magicTiles:
                    if magicTile not in temp:
                        return temp, state
            return peng[0], state

        if state & MTableState.TABLE_STATE_CHI:
            chi = self.__extend.get(self.CHI, None)
            if not chi:
                return None, state
            return chi[0], state

    def getChoiceByPattern(self, pattern, datas):
        """根据pattern从目标数据中获取内容"""
        if not pattern:
            return None

        if not datas:
            return None

        for node in datas:
            if pattern == node['pattern']:
                return node

        return None

    def getWinNodeByTile(self, tile):
        """根据和牌手牌获取和牌内容"""
        if self.WIN not in self.__extend:
            return None

        wins = self.__extend[self.WIN]
        for winNode in wins:
            if winNode['tile'] == tile:
                return winNode

        return None

    def getPigus(self, state):
        """云南曲靖麻将获取屁股牌"""
        if state & MTableState.TABLE_STATE_FANPIGU:
            if 'pigus' in self.__extend:
                return self.__extend['pigus']
        return None
