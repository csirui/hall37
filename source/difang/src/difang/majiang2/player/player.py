# -*- coding=utf-8
'''
Created on 2016年9月23日
麻将核心玩法中用到的玩家对象
@author: zhaol
'''
import copy

from difang.majiang2.ai.win import MWin
from difang.majiang2.player.hand.hand import MHand
from difang.majiang2.table_state.state import MTableState
from difang.majiang2.table_tile.table_tile import MTableTile
from difang.majiang2.tile.tile import MTile
from freetime.util import log as ftlog


class MPlayerTileChi(object):
    """玩家手牌的吃牌"""

    def __init__(self, tile, pattern, actionId):
        super(MPlayerTileChi, self).__init__()
        self.__tile = tile
        self.__pattern = pattern
        self.__actionId = actionId

    @property
    def tile(self):
        return self.__tile

    @property
    def pattern(self):
        return self.__pattern

    def setPattern(self, newPattern):
        """设置吃牌组"""
        self.__pattern = newPattern

    @property
    def actionID(self):
        return self.__actionId


class MPlayerTilePeng(object):
    """玩家手牌的吃牌"""

    def __init__(self, tile, pattern, actionId):
        super(MPlayerTilePeng, self).__init__()
        self.__tile = tile
        self.__pattern = pattern
        self.__actionId = actionId

    @property
    def tile(self):
        return self.__tile

    @property
    def pattern(self):
        return self.__pattern

    def setPattern(self, newPattern):
        """设置牌组"""
        self.__pattern = newPattern

    @property
    def actionID(self):
        return self.__actionId


class MPlayerTileGang(object):
    MING_GANG = 1
    AN_GANG = 0
    """玩家手牌的吃牌"""

    def __init__(self, tile, pattern, actionId, style):
        super(MPlayerTileGang, self).__init__()
        self.__tile = tile
        self.__pattern = pattern
        self.__actionId = actionId
        self.__gang_style = style

    def isMingGang(self):
        """是否明杠"""
        return self.__gang_style == self.MING_GANG

    @property
    def tile(self):
        return self.__tile

    @property
    def pattern(self):
        return self.__pattern

    def setPattern(self, pattern):
        """设置碰牌组"""
        self.__pattern = pattern

    @property
    def actionID(self):
        return self.__actionId

    @property
    def style(self):
        return self.__gang_style


class MPlayer(object):
    """
    麻将的玩家类
    本类主要描述一下几种信息
    1）玩家的个人信息，包括姓名，性别，userId，积分等等
    2）手牌，包括握在手里的牌，吃牌，碰牌，杠牌
    3）打牌行为的响应，是否吃牌，是否碰牌，是否杠牌，是否胡牌，是否过胡翻倍
    """

    """玩家游戏状态，只关心用户的游戏状态，用户的准备状态由继承框架TYTable的MajiangTable来处理
    """
    # 用户刚坐下，需要点击准备按钮
    PLAYER_STATE_NORMAL = 'sit'
    # 用户已准备
    PLAYER_STATE_READY = 'ready'
    # 用户在游戏中
    PLAYER_STATE_PLAYING = 'play'
    # 特殊的游戏状态，听牌状态
    PLAYER_STATE_TING = 'ting'
    # 特殊的游戏状态，明牌状态
    PLAYER_STATE_MING = 'ming'
    # 特殊的游戏状态，用户已经和牌
    PLAYER_STATE_WON = 'win'

    def __init__(self, name, sex, userId, score, purl='', coin=0, clientId=''):
        super(MPlayer, self).__init__()
        # 1 姓名
        self.__name = name
        # 2 性别
        self.__sex = sex
        self.__purl = purl
        self.__coin = coin
        # 3 用户ID
        self.__userId = userId
        self.__clientId = clientId
        # 5 手牌
        self.__hand_tiles = []
        # 6 吃牌
        self.__chi_tiles = []
        # 7 碰牌
        self.__peng_tiles = []
        # 8 杠牌
        self.__gang_tiles = []
        # 10 和牌，血流有多次胡牌的设计
        self.__hu_tiles = []
        # 粘牌 鸡西玩法 粘之后存储在player中 下发协议时用来塞选手牌
        self.__zhan_tiles = []
        # 听牌同时亮牌，亮牌列表
        self.__ting_liang_tiles = []
        # 11 状态
        self.__state = self.PLAYER_STATE_NORMAL
        # 12 当前手牌
        self.__cur_tile = 0
        # 13 座位号
        self.__cur_seat_id = -1
        # 14 定缺
        self.__absense_color = MTile.TILE_NONE
        # 15 托管
        self.__auto_decide = False
        # 听牌方案
        self.__win_nodes = []
        # 听牌同时亮牌，操作id
        self.__ting_liang_actionId = None
        # 听牌同时亮牌，要胡的牌，同时也是其他人不能打牌
        self.__ting_liang_winTiles = []
        # 已经胡牌的标记,用于血战
        self.__has_hu = False
        # 用户是否是离线
        self.__player_leave = False

    def reset(self):
        """重置
        """
        self.__hand_tiles = []
        self.__chi_tiles = []
        self.__peng_tiles = []
        self.__gang_tiles = []
        self.__hu_tiles = []
        self.__zhan_tiles = []
        self.__state = self.PLAYER_STATE_NORMAL
        self.__cur_tile = 0
        self.__win_nodes = []
        self.__ting_liang_tiles = []
        self.__ting_liang_actionId = None
        self.__ting_liang_winTiles = []
        self.__has_hu = False
        self.__player_leave = False

    @property
    def playerLeave(self):
        return self.__player_leave

    def setPlayerLeave(self, playerLeave):
        self.__player_leave = playerLeave

    @property
    def hasHu(self):
        return self.__has_hu

    def setHasHu(self, hasHu):
        self.__has_hu = hasHu

    @property
    def name(self):
        """获取名称"""
        return self.__name

    @property
    def clientId(self):
        return self.__clientId

    @property
    def winNodes(self):
        """获取听牌方案
        例子：
        [{'winTile': 1, 'winTileCount': 3, 'pattern': [[6, 6], [5, 6, 7], [4, 5, 6], [1, 2, 3]]}
        """
        return self.__win_nodes

    def setWinNodes(self, winNodes):
        """设置听牌信息"""
        self.__win_nodes = winNodes

    @property
    def sex(self):
        """获取用户性别"""
        return self.__sex

    @property
    def purl(self):
        """获取用户头像"""
        return self.__purl

    @property
    def coin(self):
        """获取用户金币"""
        return self.__coin

    @property
    def curTile(self):
        """当前摸到的牌"""
        return self.__cur_tile

    def setCurTile(self, curTile):
        """设置当前摸到的牌"""
        self.__cur_tile = curTile

    @property
    def curSeatId(self):
        """玩家当前座位号"""
        return self.__cur_seat_id

    def setSeatId(self, seat):
        """设置座位号"""
        self.__cur_seat_id = seat

    @property
    def userId(self):
        """获取用户ID"""
        return self.__userId

    @property
    def handTiles(self):
        """获取手牌"""
        return self.__hand_tiles

    @property
    def chiTiles(self):
        """获取吃牌"""
        return self.__chi_tiles

    @property
    def pengTiles(self):
        """获取听牌"""
        return self.__peng_tiles

    @property
    def gangTiles(self):
        """获取暗杠牌"""
        return self.__gang_tiles

    @property
    def huTiles(self):
        """胡牌"""
        return self.__hu_tiles

    @property
    def zhanTiles(self):
        """胡牌"""
        if self.__zhan_tiles:
            zhanTiles = []
            zhanTiles.append(self.__zhan_tiles)
            return zhanTiles
        else:
            return self.__zhan_tiles

    def setZhanTiles(self, zhanSolution):
        self.__zhan_tiles = zhanSolution

    @property
    def tingLiangTiles(self):
        """听牌亮牌的牌列表"""
        return self.__ting_liang_tiles

    @property
    def tingLiangActionID(self):
        """听牌亮牌时的actionId，后面用来确认谁先亮牌"""
        return self.__ting_liang_actionId

    @property
    def tingLiangWinTiles(self):
        """听牌亮牌要胡的牌列表，也是对方禁止打的牌的列表"""
        return self.__ting_liang_winTiles

    @property
    def state(self):
        """获取当前玩家状态"""
        return self.__state

    @property
    def absenseColor(self):
        """获取定缺花色"""
        return self.__absense_color

    @property
    def autoDecide(self):
        """是否托管"""
        return self.__auto_decide

    def setAutoDecide(self, value):
        """设置是否托管
        参数
        1）value，托管设置
        True 托管
        False 不托管
        """
        ftlog.debug('MPlayer.setAutoDecide value:', value
                    , ' player:', self.name
                    , ' userId:', self.userId)
        self.__auto_decide = value

    def ready(self):
        """设置准备状态"""
        self.__state = self.PLAYER_STATE_READY

    def play(self):
        """设置游戏状态"""
        self.__state = self.PLAYER_STATE_PLAYING

    def wait(self):
        """设置准备状态"""
        self.__state = self.PLAYER_STATE_NORMAL

    def isWon(self):
        """是否和牌"""
        return self.__state == self.PLAYER_STATE_WON

    def isTing(self):
        """是否听牌"""
        return self.__state == self.PLAYER_STATE_TING

    def isTingLiang(self):
        """是否听牌同时亮牌"""
        if self.__ting_liang_tiles:
            return True
        else:
            return False

    def isMing(self):
        """是否明牌"""
        return self.__state == self.PLAYER_STATE_MING

    def isRobot(self):
        """是否是机器人"""
        if self.__userId < 10000:
            return True
        return False

    def canGang(self, gang, hasGang):
        if not hasGang:
            return False

        if not self.isTing():
            return True

        # 当前听牌，检查杠牌是否影响听牌，先去掉手牌中的杠牌
        handTiles = self.copyHandTiles()
        if gang['style'] == MPlayerTileGang.AN_GANG:
            for tile in gang['pattern']:
                handTiles.remove(tile)

        if gang['style'] == MPlayerTileGang.MING_GANG:
            handTiles.remove(gang['pattern'][3])

        # 加入听口，如果都能和，不改变听口结果，继续杠牌；如果改变了听口，不能杠
        for node in self.winNodes:
            winTile = node['winTile']
            handTiles.append(winTile)
            if not MWin.isHu(handTiles):
                return False
            handTiles.remove(winTile)

        return True

    def copyHandTiles(self):
        """拷贝手牌
        返回值： 数组
        """
        return copy.deepcopy(self.__hand_tiles)

    def copyChiArray(self):
        """拷贝吃牌，二位数组"""
        allChi = []
        for chiObj in self.__chi_tiles:
            allChi.append(chiObj.pattern)
        return copy.deepcopy(allChi)

    def copyPengArray(self):
        """拷贝所有的碰牌"""
        allPeng = []
        for pengObj in self.__peng_tiles:
            allPeng.append(pengObj.pattern)
        return allPeng

    def copyTingArray(self):
        """拷贝听牌数组"""
        return []

    def copyGangArray(self):
        """拷贝杠牌"""
        allGangPattern = []
        for gangObj in self.__gang_tiles:
            gang = {}
            gang['pattern'] = gangObj.pattern
            gang['style'] = gangObj.style
            gang['actionID'] = gangObj.actionID
            allGangPattern.append(gang)
        return allGangPattern

    def copyHuArray(self):
        """拷贝和牌"""
        return copy.deepcopy(self.__hu_tiles)

    def printTiles(self):
        """打印玩家手牌"""
        ftlog.debug('MPayer.printTiles name:', self.name, ' seatId:', self.curSeatId)
        ftlog.debug('HandTiles:', self.copyHandTiles())
        ftlog.debug('ChiTiles:', self.copyChiArray())
        ftlog.debug('PengTiles:', self.copyPengArray())
        ftlog.debug('gangTiles::', self.copyGangArray())
        ftlog.debug('WinTiles:', self.copyHuArray())

    def copyTiles(self):
        """拷贝玩家所有的牌
        返回值，二维数组
        索引  说明    类型
        0    手牌    数组
        1    吃牌    数组
        2    碰牌    数组
        3    明杠牌  数组
        4    暗杠牌  数组
        """
        re = [[] for _ in range(MHand.TYPE_COUNT)]
        # 手牌
        handTiles = self.copyHandTiles()
        re[MHand.TYPE_HAND] = (handTiles)

        # 吃牌
        re[MHand.TYPE_CHI] = self.copyChiArray()

        # 碰牌
        re[MHand.TYPE_PENG] = self.copyPengArray()

        # 明杠牌
        re[MHand.TYPE_GANG] = self.copyGangArray()

        # 和牌
        re[MHand.TYPE_HU] = self.copyHuArray()

        # 最新手牌
        newestTiles = [self.__cur_tile]
        re[MHand.TYPE_CUR] = newestTiles

        return re

    """
    以下是玩家打牌的行为
    开始
    摸牌
    出牌
    明牌
    吃
    碰
    杠
    和
    """

    def actionBegin(self, handTiles):
        """开始
        参数
            handTiles - 初始手牌
        """
        self.__hand_tiles.extend(handTiles)
        self.__hand_tiles.sort()
        ftlog.debug('Player ', self.name, ' Seat:', self.curSeatId, ' actionBegin:', self.__hand_tiles)

    def updateTile(self, tile, tableTileMgr):
        """更新吃牌/碰/杠牌中的宝牌"""
        magicTiles = tableTileMgr.getMagicTiles(False)
        if len(magicTiles) == 0:
            return False, None

        if tableTileMgr.canUseMagicTile(MTableState.TABLE_STATE_CHI):
            chiRe, chiData = self.updateChiTile(tile, magicTiles)
            if chiRe:
                return chiRe, chiData

        if tableTileMgr.canUseMagicTile(MTableState.TABLE_STATE_PENG):
            pengRe, pengData = self.updatePengTile(tile, magicTiles)
            if pengRe:
                return pengRe, pengData

        if tableTileMgr.canUseMagicTile(MTableState.TABLE_STATE_GANG):
            gangRe, gangData = self.updateMingGangTile(tile, magicTiles)
            if gangRe:
                return gangRe, gangData

        return False, None

    def updateChiTile(self, tile, magicTiles):
        """更新吃牌中的宝牌"""
        for chiObj in self.__chi_tiles:
            if tile in chiObj.pattern:
                continue
            # 不含癞子无需换牌
            needChange = False
            for magicTile in magicTiles:
                if magicTile in chiObj.pattern:
                    needChange = True
            if not needChange:
                continue

            bChanged = False
            oldPattern = copy.deepcopy(chiObj.pattern)
            newPattern = copy.deepcopy(oldPattern)
            oldTile = 0
            newTile = 0

            for index in range(3):
                if oldPattern[index] in magicTiles:
                    if index == 0:
                        if (oldPattern[index + 1] == (tile + 1)) or (oldPattern[index + 2] == (tile + 2)):
                            bChanged = True
                            oldTile = oldPattern[index]
                            newTile = tile
                            newPattern[index] = tile
                            break

                    if index == 1:
                        if (oldPattern[index - 1] == (tile - 1)) or (oldPattern[index + 1] == (tile + 1)):
                            bChanged = True
                            oldTile = oldPattern[index]
                            newTile = tile
                            newPattern[index] = tile
                            break

                    if index == 2:
                        if (oldPattern[index - 1] == (tile - 1)) or (oldPattern[index - 2] == (tile - 2)):
                            bChanged = True
                            oldTile = oldPattern[index]
                            newTile = tile
                            newPattern[index] = tile
                            break

            if bChanged:
                chiObj.setPattern(newPattern)
                newData = {}
                newData['old'] = oldPattern
                newData['new'] = newPattern
                newData['type'] = 'chi'
                newData['oldTile'] = oldTile
                newData['newTile'] = newTile
                self.__hand_tiles.remove(tile)
                self.__hand_tiles.append(oldTile)
                if self.__cur_tile == tile:
                    self.__cur_tile = oldTile
                return True, newData
        return False, None

    def updatePengTile(self, tile, magicTiles):
        """更新碰牌中的宝牌"""
        for pengObj in self.__peng_tiles:
            if tile not in pengObj.pattern:
                continue
            # 不含癞子无需换牌
            needChange = False
            for magicTile in magicTiles:
                if magicTile in pengObj.pattern:
                    needChange = True
            if not needChange:
                continue
            oldTile = 0
            newTile = 0

            newPattern = copy.deepcopy(pengObj.pattern)
            for index in range(len(newPattern)):
                if newPattern[index] in magicTiles:
                    oldTile = newPattern[index]
                    newTile = tile
                    newPattern[index] = tile
                    break

            ftlog.debug('MPlayer.updatePengTile newPattern:', newPattern)
            oldPattern = copy.deepcopy(pengObj.pattern)
            newPattern.sort()
            pengObj.setPattern(newPattern)
            newData = {}
            newData['old'] = oldPattern
            newData['new'] = newPattern
            newData['type'] = 'peng'
            newData['newTile'] = newTile
            newData['oldTile'] = oldTile
            self.__hand_tiles.remove(tile)
            self.__hand_tiles.append(oldTile)
            if self.__cur_tile == tile:
                self.__cur_tile = oldTile
            return True, newData

        return False, None

    def updateMingGangTile(self, tile, magicTiles):
        """更新明杠牌中的宝牌"""
        for gangObj in self.__gang_tiles:
            # 不含癞子无需换牌
            needChange = False
            for magicTile in magicTiles:
                if magicTile in gangObj.pattern:
                    needChange = True
            if not needChange:
                continue

            if gangObj.isMingGang and (tile in gangObj.pattern):
                newPattern = copy.deepcopy(gangObj.pattern)
                oldPattern = copy.deepcopy(gangObj.pattern)

                oldTile = 0
                newTile = 0

                for index in range(4):
                    if oldPattern[index] in magicTiles:
                        newPattern[index] = tile
                        oldTile = oldPattern[index]
                        newTile = tile
                        break
                newPattern.sort()
                gangObj.setPattern(newPattern)
                newData = {}

                old = {}
                old['pattern'] = oldPattern
                old['style'] = gangObj.style
                newData['old'] = old

                new = {}
                new['pattern'] = newPattern
                new['style'] = gangObj.style
                newData['new'] = new

                newData['type'] = 'gang'
                newData['oldTile'] = oldTile
                newData['newTile'] = newTile

                self.__hand_tiles.remove(tile)
                self.__hand_tiles.append(oldTile)
                if self.__cur_tile == tile:
                    self.__cur_tile = oldTile
                return True, newData

        return False, None

    def actionAdd(self, tile):
        """摸牌
        加到最后，先不排序
        """
        self.__cur_tile = tile
        self.__hand_tiles.append(tile)
        self.__hand_tiles.sort()
        ftlog.debug('Player:', self.name
                    , ' HandTiles:', self.__hand_tiles
                    , ' Seat:', self.curSeatId
                    , ' actionAdd:', tile)

    def actionDrop(self, tile):
        """出牌
        """
        if tile not in self.__hand_tiles:
            ftlog.debug('drap error')
            return False
        else:
            self.__cur_tile = 0
            self.__hand_tiles.remove(tile)
            # 手牌排序
            self.__hand_tiles.sort()
        ftlog.debug('Player:', self.name, ' Seat:', self.curSeatId, ' actionDrop:', tile)
        return True

    def actionMing(self):
        """明牌
        明牌后，别人可看到此人的手牌
        """
        self.__state = self.PLAYER_STATE_MING
        ftlog.debug('Player:', self.name, ' Seat:', self.curSeatId, ' actionMing')

    def actionChi(self, handTiles, chiTile, actionId):
        """吃
        参数：
            handTiles - 自己的手牌，跟chiTile组成吃牌组
            chiTile - 被吃的牌，跟handTiles组成吃牌组
        """
        for tile in handTiles:
            if tile not in self.__hand_tiles:
                ftlog.debug('chi error tile:', tile)
                return False
            self.__hand_tiles.remove(tile)

        chiTileObj = MPlayerTileChi(tile, handTiles, actionId)
        self.__chi_tiles.append(chiTileObj)
        self.__cur_tile = 0
        self.__hand_tiles.sort()
        ftlog.debug('Player:', self.name, ' Seat:', self.curSeatId, ' actionChi:', chiTile)
        return True

    def actionPeng(self, pengTile, pengPattern, actionId):
        """碰别人
        """
        for _tile in pengPattern:
            self.__hand_tiles.remove(_tile)

        pengTileObj = MPlayerTilePeng(pengTile, pengPattern, actionId)
        self.__peng_tiles.append(pengTileObj)
        self.__cur_tile = 0
        self.__hand_tiles.sort()
        ftlog.debug('Player:', self.name, ' Seat:', self.curSeatId, ' actionPeng:', pengTile)
        return True

    def actionGangByDropCard(self, gangTile, gangPattern, actionId):
        """明杠，通过出牌杠牌，牌先加到手牌里，再加到杠牌里
        参数：
            gangTile - 被杠的牌，跟handTiles组成杠牌组
        """
        handTiles = self.copyHandTiles()
        for _tile in gangPattern:
            if _tile not in handTiles:
                ftlog.debug('gang error gangTile =', gangTile, "handtiles=", handTiles)
                return False
            else:
                handTiles.remove(_tile)

        self.__hand_tiles = handTiles
        gangTileObj = MPlayerTileGang(gangTile, gangPattern, actionId, True)
        self.__gang_tiles.append(gangTileObj)
        self.__cur_tile = 0
        ftlog.debug('Player:', self.name, ' Seat:', self.curSeatId, ' actionGangByDropCard:', gangTile)
        return True

    def actionGangByAddCard(self, gangTile, gangPattern, style, actionId, magicTiles):
        """暗杠/明杠都有可能
        1）杠牌在手牌里，暗杠
        2）杠牌在碰牌里，明杠
        参数：
            gangTile - 杠牌
        返回值：
        0 - 出错，不合法
        1 - 明杠
        2 - 暗杠
        """
        ftlog.debug('MPlayer.actionGangByAddCard, gangPattern = ', gangPattern, 'gangTile=', gangTile,
                    'self.__hand_tiles:', self.__hand_tiles)
        # 摸牌明杠,一定是补杠,只要有赖子realGangTile一定是赖子
        if style == MPlayerTileGang.MING_GANG:
            tempGangPattern = copy.deepcopy(gangPattern)
            tempGangPattern.remove(gangTile)
            pengPattern = tempGangPattern
            pengObj = None
            # 手牌里有一张该牌或者手牌里有赖子
            noTile = True
            if gangTile not in self.__hand_tiles:
                for magicTile in magicTiles:
                    if magicTile in self.__hand_tiles:
                        noTile = False
            else:
                noTile = False
            if noTile:
                ftlog.debug('MPlayer.actionGangByAddCard gang error, gangTile not in handTiles:', self.__hand_tiles)
                return False

            realGangTile = None
            for _tile in self.__hand_tiles:
                if _tile in pengPattern:
                    realGangTile = _tile
                    break

            # 补杠里面有赖子,赖子一定在手牌    
            if not realGangTile and (len(magicTiles) > 0):
                for _tile in gangPattern:
                    if _tile in magicTiles:
                        realGangTile = _tile

            if not realGangTile:
                ftlog.debug('MPlayer.actionGangByAddCard an gang error, not gangTile in handTiles:', self.__hand_tiles)
                return False

            for _pengObj in self.__peng_tiles:
                if _pengObj.pattern == pengPattern:
                    pengObj = _pengObj
                    break
            ftlog.debug('MPlayer.actionGangByAddCard,MINGGANG,gangPattern = ', gangPattern, 'gangTile=', gangTile)
            # 带赖子的补杠
            isLaiziBuGang = False
            laizi = None
            if len(magicTiles) > 0:
                ftlog.debug('MPlayer.actionGangByAddCard1,')
                for magicTile in magicTiles:
                    ftlog.debug('MPlayer.actionGangByAddCard2,')
                    newGangPattern = copy.deepcopy(gangPattern)
                    ftlog.debug('MPlayer.actionGangByAddCard3,')
                    if magicTile in newGangPattern:
                        ftlog.debug('MPlayer.actionGangByAddCard, newGangPattern = ', newGangPattern, 'magicTile=',
                                    magicTile)
                        newGangPattern.remove(magicTile)
                        newPengPattern = newGangPattern
                        ftlog.debug('MPlayer.actionGangByAddCard, newPengPattern = ', newPengPattern, 'gangTile=',
                                    gangTile)
                        for _pengObj in self.__peng_tiles:
                            if _pengObj.pattern == newPengPattern:
                                pengObj = _pengObj
                                isLaiziBuGang = True
                                laizi = magicTile
                                break

            if pengObj:
                self.__peng_tiles.remove(pengObj)
                if isLaiziBuGang and laizi:
                    self.__hand_tiles.remove(laizi)
                else:
                    self.__hand_tiles.remove(realGangTile)
                gangTileObj = MPlayerTileGang(gangTile, gangPattern, actionId, style)
                self.__gang_tiles.append(gangTileObj)
                self.__cur_tile = 0
            return True
        else:
            handTiles = self.copyHandTiles()
            for _tile in gangPattern:
                if _tile in handTiles:
                    handTiles.remove(_tile)
                else:
                    ftlog.debug('MPlayer.actionGangByAddCard an gang error, not 4 gangTiles in handTiles')
                    return False

            self.__hand_tiles = handTiles
            gangTileObj = MPlayerTileGang(gangTile, gangPattern, actionId, style)
            self.__gang_tiles.append(gangTileObj)
            self.__cur_tile = 0
            ftlog.debug('MPlayer.actionGangByAddCard,ANGANG,gangPattern = ', gangPattern, 'gangTile=', gangTile)
            return True

    def actionTing(self, winNodes):
        """听
        """
        self.__state = self.PLAYER_STATE_TING
        self.__win_nodes = winNodes
        ftlog.debug('MPlayer:', self.name, ' Seat:', self.curSeatId, ' actionTing winNodes:', winNodes)

    def actionTingLiang(self, tableTileMgr, dropTile, actionId):
        """听牌同时亮牌
        """
        # 听牌同时亮牌，必须要先听牌
        if not self.isTing():
            return None

        self.__ting_liang_tiles = []
        self.__ting_liang_winTiles = []
        mode = tableTileMgr.getTingLiangMode()
        ftlog.debug('actionTingLiang, mode:', mode, ' hand tiles:', self.__hand_tiles, ' drop tile:', dropTile)

        if mode == MTableTile.MODE_LIANG_NONE:
            # 当前不支持亮牌
            return None

        for wn in self.__win_nodes:
            self.__ting_liang_winTiles.append(wn['winTile'])
        self.__ting_liang_actionId = actionId

        if mode == MTableTile.MODE_LIANG_HAND:
            # 亮全部手牌
            ftlog.debug('actionTingLiang: in MTableTile.MODE_LIANG_HAND')
            # 此处一定要用deepcopy,否则会影响用户手牌
            self.__ting_liang_tiles = copy.deepcopy(self.__hand_tiles)
            self.__ting_liang_tiles.remove(dropTile)
        elif mode == MTableTile.MODE_LIANG_TING:
            # 亮全部听口的牌
            ftlog.debug('actionTingLiang: in MTableTile.MODE_LIANG_TING')
            liangTilesCount = [0 for _ in range(MTile.TILE_MAX_VALUE)]
            for wn in self.__win_nodes:
                liangTilesCountTemp = [0 for _ in range(MTile.TILE_MAX_VALUE)]
                for p in wn['pattern']:
                    if wn['winTile'] in p:
                        # 只要要和牌出现在牌型中，这3张牌就是听口牌
                        for tile in p:
                            liangTilesCountTemp[tile] += 1
                # 遍历过所有牌后，减去要胡的牌，剩下的是当前所有听口的牌
                liangTilesCountTemp[wn['winTile']] -= 1
                # 汇总各种牌型中听口的牌
                for i in range(MTile.TILE_MAX_VALUE):
                    if liangTilesCountTemp[i] > liangTilesCount[i]:
                        liangTilesCount[i] = liangTilesCountTemp[i]
            # 把听口的牌整理出来
            for i in range(MTile.TILE_MAX_VALUE):
                self.__ting_liang_tiles.extend([i for _ in range(liangTilesCount[i])])

        ftlog.debug('MPlayer:', self.name, ' Seat:', self.curSeatId, ' actionTingLiang, mode:', mode, ' tiles:',
                    self.__ting_liang_tiles, ' winTiles:', self.__ting_liang_winTiles)

    def actionHuFromOthers(self, tile):
        """吃和
        别分放炮
        """
        self.__state = self.PLAYER_STATE_WON
        self.__hu_tiles.append(tile)
        ftlog.debug('Player:', self.name, ' Seat:', self.curSeatId, ' actionHuFromOthers:', tile)

    def actionHuByMyself(self, tile, addRemove=True):
        """自摸和
        """
        self.__state = self.PLAYER_STATE_WON
        # 取最后一张牌放到和牌里
        if addRemove:
            self.__hu_tiles.append(tile)
            self.__hand_tiles.remove(tile)
        ftlog.debug('Player:', self.name, ' Seat:', self.curSeatId, ' actionHuByMyself:', tile)

    def actionHuByDrop(self, tile):
        """云南曲靖特殊玩法,自己出牌自己胡
        """
        self.__state = self.PLAYER_STATE_WON
        # 取最后一张牌放到和牌里
        self.__hu_tiles.append(tile)
        ftlog.debug('Player:', self.name, ' Seat:', self.curSeatId, ' actionHuByDrop:', tile)

    def resetWithScore(self):
        """带积分重置
        """
        self.reset()

    def exchangeMagicTilePeng(self, pengInfo, magicTiles):
        """实际换牌操作"""
        if len(magicTiles) <= 0:
            return False, 0, 0, {}
        changeOk = False
        keyTile = 0
        # 判断是否能换牌
        for tile in pengInfo:
            if tile in magicTiles:
                continue
            for handTile in self.handTiles:
                if handTile == tile:
                    keyTile = handTile
                    changeOk = True
            if changeOk:
                break
            else:
                continue

        # 开始换牌,只执行一次,执行完了就退出,一次只让换一张
        for pengObj in self.pengTiles:
            pengPattern = pengObj.pattern
            if pengInfo == pengPattern:
                for pengTile in pengPattern:
                    ftlog.debug("exchangeMagicTilePeng pengPattern:", pengPattern, "self.handTiles:", self.handTiles)
                    # 将找到的第一个癞子替换为母牌并重新排序
                    if pengTile in magicTiles:
                        pengPattern.remove(pengTile)
                        pengPattern.append(keyTile)
                        pengPattern.sort()
                        self.handTiles.remove(keyTile)
                        self.handTiles.append(pengTile)
                        self.handTiles.sort()
                        if self.curTile == keyTile:
                            self.__cur_tile = pengTile
                        ftlog.debug("exchangeMagicTilePeng pengPattern:", pengPattern, "self.handTiles:",
                                    self.handTiles)
                        return True, keyTile, pengTile, {"peng": [pengInfo, pengPattern]}
            else:
                continue
        return False, 0, 0, {}

    def exchangeMagicTileGang(self, gangInfo, magicTiles):
        """实际换牌操作"""
        if len(magicTiles) <= 0:
            return False, 0, 0, {}

        if not gangInfo.has_key('style') or not gangInfo.has_key('pattern'):
            return False, 0, 0, {}
        changeOk = False
        keyTile = 0
        # 判断是否能换牌
        for tile in gangInfo['pattern']:
            if tile in magicTiles:
                continue
            for handTile in self.handTiles:
                if handTile == tile:
                    keyTile = handTile
                    changeOk = True
            if changeOk:
                break
            else:
                continue

        # 开始换牌,只执行一次,执行完了就退出,一次只让换一张
        for gangObj in self.gangTiles:
            gangPattern = gangObj.pattern
            if gangInfo['pattern'] == gangPattern:
                for pengTile in gangPattern:
                    ftlog.debug("exchangeMagicTilePeng gangPattern:", gangPattern, "self.handTiles:", self.handTiles)
                    # 将找到的第一个癞子替换为母牌并重新排序
                    if pengTile in magicTiles:
                        gangPattern.remove(pengTile)
                        gangPattern.append(keyTile)
                        gangPattern.sort()
                        self.handTiles.remove(keyTile)
                        self.handTiles.append(pengTile)
                        self.handTiles.sort()
                        if self.curTile == keyTile:
                            self.__cur_tile = pengTile
                        ftlog.debug("exchangeMagicTilePeng gangPattern:", gangPattern, "self.handTiles:",
                                    self.handTiles)
                        return True, keyTile, pengTile, {
                            "gang": {"pattern": [gangInfo['pattern'], gangPattern], "style": gangObj.style}}
            else:
                continue
        return False, 0, 0, {}

    def canExchangeMagic(self, magicTiles):
        """
        查看是否能够换碰杠牌中的癞子
        遍历所有手牌，举出所有可能
        """
        if len(magicTiles) <= 0:
            return False, 0, {}
        exchangeInfo = {
            "peng": [],
            "gang": []
        }
        canExchange = False
        for tile in self.handTiles:
            if tile in magicTiles:
                continue
            for pengObj in self.__peng_tiles:
                if tile in pengObj.pattern:
                    for pengTile in pengObj.pattern:
                        if pengTile in magicTiles:
                            canExchange = True
                            exchangeInfo['peng'].append(copy.deepcopy(pengObj.pattern))
                            break
                else:
                    continue
            for gangObj in self.__gang_tiles:
                if tile in gangObj.pattern:
                    for gangTile in gangObj.pattern:
                        if gangTile in magicTiles:
                            canExchange = True
                            gangInfo = {
                                "tile": tile,
                                "pattern": copy.deepcopy(gangObj.pattern),
                                "style": gangObj.style
                            }
                            exchangeInfo['gang'].append(gangInfo)
                            break
                else:
                    continue
        ftlog.debug('canExchangeMagic canExchange:', canExchange, 'exchangeInfo', exchangeInfo)
        ftlog.debug('canExchangeMagic self.__hand_tiles:', self.__hand_tiles)
        # 在这里处理一下重复的pattern
        newGang = []
        newPeng = []
        for gang in exchangeInfo['gang']:
            if gang not in newGang:
                newGang.append(copy.deepcopy(gang))
        exchangeInfo['gang'] = newGang
        for peng in exchangeInfo['peng']:
            if peng not in newPeng:
                newPeng.append(copy.deepcopy(peng))
        exchangeInfo['peng'] = newPeng
        return canExchange, exchangeInfo
