# -*- coding:utf-8 -*-
'''
Created on 2016年6月16日

@author: zhaojiangang
'''
import random

from poker.entity.configure import gdata
from poker.entity.game.rooms.group_match_ctrl.config import MatchConfig
from poker.entity.game.rooms.group_match_ctrl.models import TableManager
from poker.entity.game.rooms.group_match_room import TYGroupMatchRoom


def initMatch(self):
    assert (self.matchPlugin.getMatch(self.roomId) is None)
    self._logger.info('TYGroupMatchRoom.initMatch ...')
    conf = MatchConfig.parse(self.gameId, self.roomId, self.bigmatchId,
                             self.roomConf['name'],
                             self.matchConf)
    conf.tableId = self.roomId * 10000  # 用来表示玩家在房间队列的特殊tableId
    conf.seatId = 1

    tableManager = TableManager(self, conf.tableSeatCount)
    shadowRoomIds = self.roomDefine.shadowRoomIds

    self._logger.info('TYGroupMatchRoom.initMatch',
                      'shadowRoomIds=', list(shadowRoomIds))

    for roomId in shadowRoomIds:
        count = self.roomDefine.configure['gameTableCount']
        baseid = roomId * 10000
        self._logger.info('TYGroupMatchRoom.initMatch addTables',
                          'shadowRoomId=', roomId,
                          'tableCount=', count,
                          'baseid=', baseid)
        tableManager.addTables(roomId, baseid, count)
    random.shuffle(tableManager._idleTables)
    match, master = self.matchPlugin.buildMatch(conf, self)
    match.tableManager = tableManager

    if gdata.mode() == gdata.RUN_MODE_ONLINE:
        playerCapacity = int(tableManager.allTableCount * tableManager.tableSeatCount * 0.9)
        userMaxCountPerMatch = conf.start.userMaxCountPerMatch
        if conf.stages and conf.stages[0].groupingType != 0:
            # 分组赛
            userMaxCountPerMatch *= 0.5
        if playerCapacity <= userMaxCountPerMatch:
            self._logger.error('TYGroupMatchRoom.initMatch',
                               'allTableCount=', tableManager.allTableCount,
                               'tableSeatCount=', tableManager.tableSeatCount,
                               'playerCapacity=', playerCapacity,
                               'userMaxCount=', conf.start.userMaxCount,
                               'confUserMaxCountPerMatch=', conf.start.userMaxCountPerMatch,
                               'userMaxCountPerMatch=', userMaxCountPerMatch,
                               'err=', 'NotEnoughTable')
        assert (playerCapacity > conf.start.userMaxCountPerMatch)

    self.match = match
    self.matchMaster = master
    self.matchPlugin.setMatch(self.roomId, match)
    if master:
        master.start()
    match.start()


TYGroupMatchRoom.initMatchOld = TYGroupMatchRoom.initMatch
TYGroupMatchRoom.initMatch = initMatch
