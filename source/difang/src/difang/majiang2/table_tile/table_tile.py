# -*- coding=utf-8
'''
Created on 2016年9月23日
牌桌麻将牌的管理器
包括：
1）发牌
2）牌桌上的出牌
3）宝牌

发牌说明：
发牌涉及到好牌点
@author: zhaol
'''
import copy

from difang.majiang2.dealer.dealer_factory import DealerFactory
from difang.majiang2.table_tile.test.table_tile_test_factory import MTableTileTestFactory
from difang.majiang2.tile.tile import MTile
from freetime.util import log as ftlog


class MTableTile(object):
    # 不亮牌
    MODE_LIANG_NONE = 0
    # 亮牌，亮全部手牌
    MODE_LIANG_HAND = 1
    # 亮牌，只亮听口牌
    MODE_LIANG_TING = 2

    def __init__(self, playerCount, playMode, runMode):
        super(MTableTile, self).__init__()
        self.__player_count = playerCount
        self.__play_mode = playMode
        self.__run_mode = runMode
        # 本局剩余的牌
        self.__tiles = []
        # 每个玩家出过的牌
        self.__drop_tiles = [[] for _ in range(self.playCount)]
        # 每个玩家摸到的牌
        self.__add_tiles = [[] for _ in range(self.playCount)]
        # 每个玩家门前的牌
        self.__men_tiles = [[] for _ in range(self.playCount)]
        # 特殊用途的牌，比如宝牌，被选出后，不用于打牌
        self.__special_tiles = []
        # 发牌器
        self.__dealer = DealerFactory.getDealer(self.__play_mode, playerCount)
        # 摆牌器
        self.__tile_test_mgr = MTableTileTestFactory.getTableTileTestMgr(playerCount, playMode, runMode)
        # 玩家
        self.__players = None
        # 牌桌配置，方便自定义行为的操作
        self.__table_config = {}
        # 杠可以用的赖子数
        self.__magics_gang_max_count = 4
        # 碰可以用的癞子数
        self.__magics_peng_max_count = 3
        # 允许抢杠胡的类型用二进制表示,这个变量只在判断了抢杠胡状态下使用
        self.__qiang_gang_rule = 0b111
        # 首次摸牌数组,用于判断地胡
        self.__first_add = [0 for _ in range(0, playerCount)]

    def reset(self):
        """重置"""
        self.__tiles = []
        self.__drop_tiles = [[] for _ in range(self.__player_count)]
        self.__add_tiles = [[] for _ in range(self.playCount)]
        self.__men_tiles = [[] for _ in range(self.playCount)]
        self.__special_tiles = []
        self.__dealer.reset()
        self.__tile_test_mgr = MTableTileTestFactory.getTableTileTestMgr(self.playCount, self.playMode, self.runMode)
        self.__players = None
        self.__first_add = [0 for _ in range(0, self.playCount)]

    def printTiles(self):
        """打印牌桌手牌信息"""
        ftlog.debug('MTableTile.printTiles...')
        ftlog.debug('addTiles:', self.addTiles)
        ftlog.debug('dropTiles:', self.dropTiles)
        ftlog.debug('menTiles:', self.menTiles)
        ftlog.debug('specialTiles:', self.specialTiles)
        ftlog.debug('leftTiles:', self.tiles)

    @property
    def firstAdd(self):
        return self.__first_add

    def setFirstAddBySeatId(self, seatId):
        self.__first_add[seatId] = 1

    @property
    def qiangGangRule(self):
        return self.__qiang_gang_rule

    def setQiangGangRule(self, rule):
        self.__qiang_gang_rule = rule

    @property
    def magicGangMaxCount(self):
        return self.__magics_gang_max_count

    def setMagicGangMaxCount(self, magicGangCount):
        self.__magics_gang_max_count = magicGangCount

    @property
    def magicPengMaxCount(self):
        return self.__magics_peng_max_count

    def setMagicPengMaxCount(self, magicPengCount):
        self.__magics_peng_max_count = magicPengCount

    @property
    def players(self):
        return self.__players

    def setPlayers(self, players):
        self.__players = players

    @property
    def specialTiles(self):
        return self.__special_tiles

    @property
    def runMode(self):
        return self.__run_mode

    def addSpecialTile(self, tile):
        self.__special_tiles.append(tile)

    @property
    def tileTestMgr(self):
        return self.__tile_test_mgr

    @property
    def tiles(self):
        return self.__tiles

    @property
    def playCount(self):
        return self.__player_count

    @property
    def playMode(self):
        return self.__play_mode

    @property
    def dropTiles(self):
        return self.__drop_tiles

    @property
    def addTiles(self):
        return self.__add_tiles

    @property
    def menTiles(self):
        return self.__men_tiles

    @property
    def tableConfig(self):
        return self.__table_config

    def setTableConfig(self, config):
        """设置牌桌配置"""
        self.__table_config = config

    @property
    def dealer(self):
        return self.__dealer

    def setAddTileInfo(self, tile, seatId):
        """设置摸牌信息"""
        self.__add_tiles[seatId].append(tile)

    def setMenTileInfo(self, tile, seatId):
        """设置门前的牌"""
        self.__men_tiles[seatId].append(tile)

    def removeMenTile(self, tile, seatId):
        """移除某人的门前牌"""
        if tile in self.__men_tiles[seatId]:
            self.__men_tiles[seatId].remove(tile)

    def shuffle(self, goodPointCount, handTileCount, piguTrick=[]):
        """
        洗牌器 
        子类里可添加特殊逻辑，比如确定宝牌
        """
        if self.tileTestMgr.initTiles():
            # 检查手牌
            handTiles = self.tileTestMgr.handTiles
            poolTiles = self.tileTestMgr.tiles
            ftlog.debug("self.tiles len1 = ", len(self.__tiles), "poolTiles = ", poolTiles, "handTiles = ", handTiles)
            if self.__dealer.initTiles(handTiles, poolTiles):
                ftlog.debug("self.tiles len2 = ", len(self.__tiles), "poolTiles = ", poolTiles, "handTiles = ",
                            handTiles)
                self.__tiles = copy.deepcopy(self.__dealer.tiles)
            ftlog.debug("self.tiles len3 = ", len(self.__tiles), "poolTiles = ", poolTiles, "handTiles = ", handTiles)
        else:
            ftlog.debug("self.tiles len4 = ", len(self.__tiles))
            self.__tiles = self.__dealer.shuffle(goodPointCount, handTileCount)
            ftlog.debug("self.tiles len5 = ", len(self.__tiles))
        ftlog.debug('MTableTile.shuffle tiles:', self.__tiles)
        return self.__tiles

    def getTiles(self):
        """获取本局未发出的手牌，亦即剩余手牌
        """
        return self.__tiles

    def getTilesLeftCount(self):
        """获取剩余手牌数量"""
        return len(self.__tiles)

    def getCheckFlowCount(self):
        """获取用于流局判定的剩余牌数,用于某些提前判定流局的,例如云南曲靖,如需要由子类覆盖"""
        return len(self.__tiles)

    def getTileLeftCount(self, tile):
        """获取某个花色剩余数量"""
        tileArr = MTile.changeTilesToValueArr(self.__tiles)
        return tileArr[tile]

    def getVisibleTilesCount(self, tile, withHandTiles=False, seatId=-1):
        """从玩家的吃牌/碰牌/打出牌中获取某个花色的数量"""
        visibleTiles = []
        for men in self.__men_tiles:
            visibleTiles.extend(men)

        for player in self.players:
            cs = player.copyChiArray()
            for chi in cs:
                visibleTiles.extend(chi)

            ps = player.copyPengArray()
            for peng in ps:
                visibleTiles.extend(peng)

            if withHandTiles:
                if player.curSeatId == seatId:
                    hand = player.copyHandTiles()
                    visibleTiles.extend(hand)
                    ftlog.debug('TableTile.getVisibleTilesCountWithHandTiles tile:', tile
                                , ' count In Hand Tiles:', hand
                                , ' withHandTiles:', withHandTiles)
                else:
                    ftlog.debug('TableTile.getVisibleTilesCountWithHandTiles tile:', tile
                                , ' seatId:', seatId
                                , ' not hit player seatId:', player.curSeatId)

        count = 0
        for t in visibleTiles:
            if t == tile:
                count += 1

        ftlog.debug('TableTile.getVisibleTilesCount tile:', tile
                    , ' count In Visible Tiles:', count
                    , ' visibleTiles:', visibleTiles)

        return count

    def popTile(self, tileLen):
        """从前面弹出多少牌
        子类里可添加特殊逻辑，比如摸牌好牌点
        参数：
        1）len - 弹出牌的长度
        """
        if len(self.__tiles) < tileLen:
            return []

        pops = []
        for _ in range(tileLen):
            pops.append(self.__tiles.pop(0))

        #         ftlog.debug( 'MTableTile.popCard:', pops )
        return pops

    def setDropTileInfo(self, tile, seatId):
        """出牌
        记录出牌信息
        子类里可添加特殊逻辑，比如哈尔滨，底牌里有三张宝牌后，需更换宝牌
        """
        self.__drop_tiles[seatId].append(tile)

    def canUseMagicTile(self, state):
        """在状态state下是否使用癞子牌"""
        return False

    def getMagicTiles(self, isTing=False):
        """获取宝牌，采用数组，有的游戏有多个宝牌"""
        return []

    def getAbandonedMagics(self):
        """获取废弃的宝牌"""
        return []

    def exculeMagicTiles(self, tileArr, magics):
        """挑出癞子牌"""
        magicTiles = []
        if len(magics) != 0:
            for mTile in magics:
                for _ in range(0, tileArr[mTile]):
                    magicTiles.append(mTile)
                tileArr[mTile] = 0
        return tileArr, magicTiles

    def getLastSpecialTiles(self):
        """获取最后抓取的特殊牌"""
        return []

    def drawLastSpecialTiles(self, curSeatId, winSeatId):
        """抓取最后抓取的特殊牌"""
        pass

    def getPigus(self):
        """获取用于补杠的尾牌"""
        return None

    def updatePigu(self, tile):
        """更新屁股"""
        return None

    def updateMagicTile(self):
        """更新宝牌"""
        return None

    def addPassHuBySeatId(self, seatId, tile):
        pass

    def clearPassHuBySeatId(self, seatId):
        pass

    def isPassHuTileBySeatId(self, seatId, tile):
        return False

    def getTingLiangMode(self):
        """默认在听牌时，不会亮牌"""
        # mode 0表示，不亮牌
        return 0

    def needChangeMagic(self):
        """摸牌时是否需要换赖子"""
        return False

    def trick(self, trickTiles):
        """临时代码用来生成一手牌"""
        needTiles = trickTiles
        for tile in needTiles:
            if tile <= 0 or tile >= 40 or not isinstance(tile, int):
                ftlog.debug("TrickTiles Input Error")
                return
        ftlog.debug("trick self.tiles1 len= ", len(self.tiles))
        temptiles = []
        for tile in needTiles:
            if tile in self.tiles:
                self.tiles.remove(tile)
                temptiles.append(tile)
            else:
                ftlog.debug("trick tile not in self.tiles")
        ftlog.debug("trick self.tiles2 len= ", len(self.tiles))
        for tile in temptiles:
            self.tiles.append(tile)
        ftlog.debug("trick self.tiles3 len= ", len(self.tiles))
        self.tiles.reverse()

    @classmethod
    def getMagicTileCountInTiles(cls, tiles, magicTiles):
        """
        intro:
        计算一组牌中的赖子数目,不会改变传入牌组
        arg:
        tils:list:需要处理的一组牌
        """
        tempTiles = copy.deepcopy(tiles)
        magicCount = 0
        for magicTile in magicTiles:
            while magicTile in tempTiles:
                magicCount += 1
                tempTiles.remove(magicTile)
        return magicCount, tempTiles

    @classmethod
    def isMagicTile(cls, tile, magicTiles):
        """
        intro:
        判断是否赖子
        args:
        tile:需要判断的牌
        """
        if tile in magicTiles:
            return True
        return False
