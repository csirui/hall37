# coding=UTF-8
'''贵宾房间类
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
    'WangTao'
]

import math
from random import choice

from freetime.core.lock import locked
from freetime.core.tasklet import FTTasklet
from freetime.entity.msg import MsgPack
from freetime.util import log as ftlog
from freetime.util.log import catchedmethod, getMethodName
from poker.entity.configure import gdata, configure
from poker.entity.dao import sessiondata
from poker.entity.dao import userchip
from poker.entity.game.plugin import TYPluginUtils, TYPluginCenter
from poker.entity.game.rooms.normal_room import TYNormalRoom
from poker.entity.game.rooms.player_room_dao import PlayerRoomDao
from poker.entity.game.rooms.room import TYRoom
from poker.protocol import router


class TYVipRoom(TYNormalRoom):
    '''贵宾房间类'''

    VIP_ROOM_LIST_REVERSE_CHIPS = 10000000

    def __init__(self, roomdefine):
        super(TYVipRoom, self).__init__(roomdefine)

        self.lastActiveTableId = 0
        self._activeTables = {}
        self._hidenTables = {}

        self._waitingPlayerMap = {}  # 玩家在哪张桌子排队

    @catchedmethod
    @locked
    def doQuickStart(self, msg):
        ''' 
        Note:
            1> 由于不同游戏评分机制不同，例如德州会根据游戏阶段评分，所以把桌子评分存到redis里，方便各游戏服务器自由刷新。
            2> 为了防止同一张桌子同时被选出来分配座位，选桌时会把tableScore里选出的桌子删除，玩家坐下成功后再添加回去，添回去之前无需刷新该桌子的评分。 
            3> 玩家自选桌时，可能选中一张正在分配座位的桌子，此时需要休眠后重试，只到该桌子完成分配或者等待超时。
            4> 贵宾室为了凑桌，当一张桌子被取走需要等待返回，这样需要锁一下房间对象。
        '''
        assert self.roomId == msg.getParam("roomId")

        userId = msg.getParam("userId")
        shadowRoomId = msg.getParam("shadowRoomId")
        tableId = msg.getParam("tableId")
        clientId = msg.getParam("clientId")
        ftlog.hinfo("doQuickStart <<", "|userId, clientId, roomId, shadowRoomId, tableId:", userId, clientId,
                    self.roomId, shadowRoomId, tableId, caller=self)

        #         if tableId and tableId not in self._activeTables: #此方法不可行，GR的_activeTables是空的，实际数据在GT里
        #             ftlog.warn("tableId not in self._activeTables, tableId:", tableId)
        #             tableId = 0

        if tableId == 0:  # 服务器为玩家选择桌子并坐下
            shadowRoomId = choice(self.roomDefine.shadowRoomIds)
            tableId = self.getBestTableId(userId, shadowRoomId)
        # else:  # 玩家自选桌子坐下
        #             assert isinstance(shadowRoomId, int) and gdata.roomIdDefineMap()[shadowRoomId].bigRoomId == self.roomDefine.bigRoomId
        #             tableId = self.enterOneTable(userId, shadowRoomId, tableId)

        if not tableId:
            ftlog.error(getMethodName(), "getFreeTableId timeout", "|userId, roomId, tableId:", userId, self.roomId,
                        tableId)
            return

        if ftlog.is_debug():
            ftlog.info("after choose table", "|userId, shadowRoomId, tableId:", userId, shadowRoomId, tableId,
                       caller=self)
        extParams = msg.getKey('params')
        self.doEnter(userId)
        self.querySitReq(userId, shadowRoomId, tableId, clientId, extParams)

    def _enter(self, userId):
        if ftlog.is_debug():
            ftlog.debug("<< |roomId, userId:", self.roomId, userId, caller=self)

        PlayerRoomDao.clear(userId, self.bigRoomId)

        return True, TYRoom.ENTER_ROOM_REASON_OK

    def _leave(self, userId, reason, needSendRes):
        ftlog.hinfo("_leave << |roomId, userId, reason:", self.roomId, userId, reason, caller=self)

        if reason == TYRoom.LEAVE_ROOM_REASON_LOST_CONNECTION:
            return False

        if not self._remoteTableLeave(userId, reason):
            return False

        PlayerRoomDao.clear(userId, self.bigRoomId)

        return True

    def _initActiveTables(self):
        # 在贵宾桌列表中显示的桌子：
        if self.isAutoQueueRoom():
            minTableCount = 1
        else:
            minTableCount = self.roomConf.get("minTableCount", 1)
        self._activeTables = dict([(tid, t) for tid, t in
                                   sorted(self.maptable.items())[:minTableCount]])

        for activeTable in self._activeTables.values():
            self.updateTableScore(activeTable.getTableScore(),
                                  activeTable.tableId, force=True)  # 确保快速开始时优选选择activeTables

        if self.isAutoQueueRoom():
            self.lastActiveTableId = self._activeTables.keys()[0]

        if ftlog.is_debug():
            ftlog.debug("|roomId, self.room._activeTables, lastActiveTableId:", self.roomId,
                        self._activeTables.keys(), self.lastActiveTableId, caller=self)

        # 不在贵宾桌列表中显示的桌子：
        self._hidenTables = dict([(tid, t) for tid, t in
                                  self.maptable.items() if tid not in self._activeTables])

    def sortedActiveTablesWithId(self):
        return [(tid, t) for tid, t in sorted(self._activeTables.items())]

    def sortedActiveTables(self):
        return [t for tid, t in sorted(self._activeTables.items())]

    def isActiveTable(self, table):
        return table.tableId in self._activeTables

    def hotTablesWithId(self, hotTablePlayersCount):
        return [(tid, t) for tid, t in self.sortedActiveTablesWithId()
                if t.playersNum >= hotTablePlayersCount]

    def hotTables(self, hotTablePlayersCount):
        return [t for tid, t in self.hotTablesWithId(hotTablePlayersCount)]

    def checkAddTable(self, hotTablePlayersCount):
        """ 检查是否要在贵宾桌列表里增加显示牌桌项 """
        hot_tables = self.hotTables(hotTablePlayersCount)
        if len(hot_tables) >= len(self._activeTables) and self._hidenTables:
            tid = sorted(self._hidenTables.keys())[0]
            if ftlog.is_debug():
                ftlog.debug("add table", tid, 'room:', self.roomId, 'len(hot_tables)',
                            len(hot_tables), 'active:', len(self._activeTables),
                            'hiden:', len(self._hidenTables), 'all:', len(self.maptable),
                            caller=self)

            self._activeTables[tid] = self._hidenTables[tid]
            self.updateTableScore(self._activeTables[tid].getTableScore(), tid, force=True)

            del self._hidenTables[tid]

    @catchedmethod
    def checkHideTable(self, table, hotTablePlayersCount):
        """ 检查是否要在贵宾桌列表里隐藏牌桌项 """
        if ftlog.is_debug():
            ftlog.debug("<< |", self.roomId, caller=self)

        if len(self._activeTables) <= self.roomConf.get("minTableCount", 1):
            if ftlog.is_debug():
                ftlog.debug("len(self._activeTables) <= minTableCount",
                            len(self._activeTables), self.roomConf.get("minTableCount", 1), caller=self)
            return

        if self.isLiveShowRoom() and table.creatorId > 0:
            if ftlog.is_debug():
                ftlog.debug("table.creatorId > 0", table.creatorId, caller=self)
            return

        if self.isAutoQueueRoom() and table.tableId != self.lastActiveTableId:
            ftlog.warn("checkHideTable table.tableId != self.lastActiveTableId", "|roomId, tableId, lastActiveTableId:",
                       self.roomId, table.tableId, self.lastActiveTableId,
                       "|table.waitPlayers, table.playersNum:", table.waitPlayers, table.playersNum,
                       "|nextTable.playersNum:", self._activeTables[table.tableId + 1].playersNum)
            return

        if table.playersNum == 0:
            hot_tables = self.hotTables(hotTablePlayersCount)
            if len(hot_tables) < (len(self._activeTables) - 1) or self.isLiveShowRoom():
                if ftlog.is_debug():
                    ftlog.debug("hide table", table.tableId, 'room:', self.roomId, 'len(hot_tables)',
                                len(hot_tables), 'active:', len(self._activeTables),
                                'hiden:', len(self._hidenTables), 'all:', len(self.maptable),
                                caller=self)
                self._hidenTables[table.tableId] = table
                try:
                    del self._activeTables[table.tableId]
                except:
                    ftlog.warn('del table', table.tableId, 'from self._activeTables', self._activeTables, 'error',
                               caller=self)
                self.updateTableScore(0, table.tableId, force=True)
                if self.isAutoQueueRoom():
                    self.lastActiveTableId -= 1
                # self.lastActiveTableId = self.sortedActiveTablesWithId()[-1][0]
                if ftlog.is_debug():
                    ftlog.debug(">>|roomId, self.lastActiveTableId:", self.roomId, self.lastActiveTableId, caller=self)

    # --- 排队桌功能
    def appendOneActiveTable(self):
        if ftlog.is_debug():
            ftlog.debug(">>|roomId, self.lastActiveTableId:", self.roomId, self.lastActiveTableId, caller=self)
        self.lastActiveTableId += 1
        self._activeTables[self.lastActiveTableId] = self._hidenTables[self.lastActiveTableId]
        self.updateTableScore(self.lastActiveTableId % 10000, self.lastActiveTableId, force=True)
        # 确保最后一个activeTable评分最高
        del self._hidenTables[self.lastActiveTableId]
        if ftlog.is_debug():
            ftlog.info("addNewActiveTable <<|roomId, self.lastActiveTableId:",
                       self.roomId, self.lastActiveTableId, caller=self)

    def getLastActiveTable(self):
        return self._activeTables[self.lastActiveTableId]

    # --- 房间类型
    def isSecretRoom(self):
        return self.roomConf.get("secretConf") != None

    def isAutoQueueRoom(self):
        return bool(self.roomConf.get("autoQueue")) and not self.isSecretRoom()

    def isLiveShowRoom(self):
        return bool(self.roomConf.get("isLiveShowRoom"))

    # --- 牌桌列表
    def doGetVipTableList(self, userId, clientId):
        '''为了效率，贵宾室所有桌子放在一个GT进程里， 在此进程中通过遍历来获取每张桌子的状态
        '''
        msgRes = MsgPack()
        msgRes.setCmd("game")
        msgRes.setResult("action", "vip_table_list")

        clientVer = sessiondata.getClientIdVer(userId)
        if clientVer < 5.0:
            if self.gameId == 8:
                msgRes.setCmd("texas_room_list_response")
            if self.gameId == 30:
                msgRes.setCmd("room")
                msgRes.setResult("action", "vipTableList")

        msg = FTTasklet.getCurrentFTTasklet().pack
        tag = msg.getParam("tag", "")

        msgRes.updateResult(self._getVipTableList(userId, clientId, tag))
        router.sendToUser(msgRes, userId)

    def doGetMasterTableList(self, userId, clientId):
        '''为了效率，贵宾室所有桌子放在一个GT进程里， 在此进程中通过遍历来获取每张桌子的状态
        '''
        msgRes = MsgPack()
        msgRes.setCmd("game")
        msgRes.setResult("action", "master_table_list")
        msgRes.updateResult(self._getVipTableList(userId, clientId, tag="", isMasterRoom=True))
        router.sendToUser(msgRes, userId)

    def doGetLiveShowTableList(self, userId, clientId):
        '''为了效率，贵宾室所有桌子放在一个GT进程里， 在此进程中通过遍历来获取每张桌子的状态
        '''
        msgRes = MsgPack()
        msgRes.setCmd("game")
        msgRes.setResult("action", "live_show_table_list")
        msgRes.updateResult(self._getVipTableList(userId, clientId, tag="", isLiveShowRoom=True))
        router.sendToUser(msgRes, userId)

    def _getVipTableList(self, userId, clientId, tag="", isMasterRoom=False, isLiveShowRoom=False):
        '''获取vip房间和游轮赛房间的桌子列表'''
        roomList = []
        vip_tableList = []
        chip = userchip.getChip(userId)

        if ftlog.is_debug():
            ftlog.debug("|roomIds:", gdata.rooms().keys(), caller=self)
        for room in gdata.rooms().values():
            if not isinstance(room, TYVipRoom):
                continue

            ftlog.debug("|roomId:", room.roomId, caller=self)
            if not room.roomConf.get('visible', True):
                if ftlog.is_debug():
                    ftlog.debug("not visible", caller=self)
                continue

            if isMasterRoom != bool(room.roomConf.get("isMasterRoom")):
                if ftlog.is_debug():
                    ftlog.debug("isMasterRoom not match", caller=self)
                continue

            if isLiveShowRoom != bool(room.roomConf.get("isLiveShowRoom")):
                if ftlog.is_debug():
                    ftlog.debug("isLiveShowRoom not match", caller=self)
                continue

            if tag != room.roomConf.get("tag", ""):
                if ftlog.is_debug():
                    ftlog.debug("tag not match", caller=self)
                continue

            roomSortId = room.roomConf.get("sortId", 0)
            roomIndex = room.bigRoomId % 1000
            if roomSortId > 0 and roomSortId < 1000:
                if chip >= self.VIP_ROOM_LIST_REVERSE_CHIPS:
                    roomSortId = roomIndex
                else:
                    roomSortId = 1000 - roomIndex
            roomInfo = {"roomId": room.bigRoomId, "roomSortId": roomSortId}
            roomList.append(roomInfo)

            if ftlog.is_debug():
                ftlog.debug("|roomId, secretConf:", room.roomId, room.roomConf.get("secretConf"), caller=self)
            if room.isSecretRoom():

                if len(self.maptable) < 1:
                    continue

                table = room.maptable.values()[0]
                if not table.checkSecretCondition(userId, clientId):
                    continue

                tableinfo = {}
                tableinfo["maxPlayerNum"] = table.maxSeatN
                tableinfo["playerNum"] = 0
                tableinfo["tableId"] = 0
                tableinfo["roomId"] = room.roomId
                tableinfo["type"] = room.roomConf["typeName"]
                tableinfo["sortId"] = room.roomConf.get("sortId", 0)
                tableinfo["isSecrect"] = True
                table.updateTableListInfo(tableinfo, clientId)
                vip_tableList.append(tableinfo)
                continue

            if not room._activeTables:
                room._initActiveTables()

            for tableId, table in room.sortedActiveTablesWithId():
                tableinfo = {}
                tableinfo["maxPlayerNum"] = table.maxSeatN
                tableinfo["playerNum"] = table.playersNum
                tableinfo["tableId"] = tableId
                tableinfo["roomId"] = table.room.roomId
                tableinfo["type"] = table.room.roomConf["typeName"]
                tableinfo["sortId"] = table.room.roomConf.get("sortId", 0)
                tableinfo["listBG"] = room.roomConf.get("listBG", "normal")
                table.updateTableListInfo(tableinfo, clientId)
                if self.isLiveShowRoom() and not tableinfo.get("creatorId"):
                    continue
                vip_tableList.append(tableinfo)

                #         def tableListComparer(x, y):
                #             if x["playerNum"] == x["maxPlayerNum"] :
                #                 if y["playerNum"] == y["maxPlayerNum"] :
                #                     return y["sortId"] - x["sortId"]
                #                 else :
                #                     return 1
                #
                #             if y["playerNum"] == y["maxPlayerNum"] :
                #                 return -1
                #
                #             return x["sortId"] - y["sortId"]

                #         vip_tableList = sorted(vip_tableList, cmp=lambda x, y : tableListComparer(x, y))

        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_GET_VIP_TABLE_LIST', params={
            'table': self, 'vip_tableList': vip_tableList}), self.gameId)

        for t in vip_tableList:
            del t['sortId']

        results = {"gameId": self.gameId}
        results['tables'] = vip_tableList
        results['roomList'] = roomList

        return results

    def doGetPlayingTableList(self):
        if self._activeTables:
            return {"tables": [t.tableId for t in self._activeTables.values() if t.playersNum > 0]}
        return {"tables": []}

    def doChooseRoom(self, userId, clientId):
        if self.gameId == 38:
            chooseRoomRatio = configure.getGameJson(self.gameId, "misc", {}).get("choose_room_ratio", 1.0)
            baseN = gdata.rooms().values()[0].tableConf["maxSeatN"] * chooseRoomRatio
            candidateRooms = []
            if ftlog.is_debug():
                ftlog.debug("|roomIds:", gdata.rooms().keys(), caller=self)
            allPlayersN = 1
            for room in gdata.rooms().values():
                if not isinstance(room, TYVipRoom):
                    continue
                playersN = room.maptable.values()[0].playersNum
                allPlayersN += playersN
                candidateRooms.append([room.roomId, playersN])

            candidateRooms.sort(key=lambda x: x[0])  # 所有房间按roomId排序
            maxRoomIndex = int(math.ceil(allPlayersN / baseN))
            sortedCandidateRooms = sorted(candidateRooms[0:maxRoomIndex], key=lambda x: x[1])  # 前几个房间按人数排序
            if ftlog.is_debug():
                ftlog.info("doChooseRoom |allPlayersN, baseN, candidateRooms:", allPlayersN, baseN, candidateRooms,
                           "|maxRoomIndex, sortedCandidateRooms:",
                           maxRoomIndex, sortedCandidateRooms, caller=self)
            return sortedCandidateRooms[0][0]
