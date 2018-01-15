# -*- coding:utf-8 -*-
'''
Created on 2016年1月17日

@author: zhaojiangang
'''
import random

import stackless

import freetime.util.log as ftlog
from freetime.core.reactor import mainloop
from poker.entity.game.rooms.group_match_ctrl.config import MatchConfig
from poker.entity.game.rooms.group_match_ctrl.interfacetest import \
    MatchStatusDaoMem, SignIFMem, TableControllerTest, PlayerNotifierTest, \
    MatchRewardsTest, UserInfoLoaderTest
from poker.entity.game.rooms.group_match_ctrl.match import MatchMaster, \
    MatchArea, MatchMasterStubLocal, MatchAreaStubLocal
from poker.entity.game.rooms.group_match_ctrl.models import TableManager
from poker.entity.game.rooms.group_match_ctrl.testbase import MyRoom, match_conf
from poker.entity.game.rooms.group_match_ctrl.utils import HeartbeatAble, \
    Heartbeat


def buildMatchMaster(roomId, matchId, matchConf):
    room = MyRoom(roomId)
    tableManager = TableManager(6, 3)
    tableManager.addTables(60571, 1, 100)
    match = MatchMaster(room, 6057, matchConf)
    match.matchStatusDao = MatchStatusDaoMem()
    return match


def buildMatchArea(roomId, matchId, matchConf, master):
    room = MyRoom(roomId)
    tableManager = TableManager(6, 3)
    tableManager.addTables(roomId, 1, 100)
    match = MatchArea(room, matchId, matchConf, MatchMasterStubLocal(master))
    match.signIF = SignIFMem()
    match.tableManager = tableManager
    match.tableController = TableControllerTest(match)
    match.playerNotifier = PlayerNotifierTest()
    match.matchRewards = MatchRewardsTest()
    return match


CLIENT_IDS = [
    'Android_3.372_tuyoo.weakChinaMobile.0-hall7.ydmm.happyxinchun',
    'Winpc_3.70_360.360.0-hall8.360.texas',
    'Android_3.72_tyOneKey,tyAccount,tyGuest.tuyoo.0-hall8.duokunew.day',
    'Android_3.363_pps.pps,weakChinaMobile,woStore,aigame.0-hall6.pps.dj'
]


class MatchChecker(HeartbeatAble):
    def __init__(self, master, areas, userInfoLoader):
        self._heartbeat = Heartbeat(1, self._doHeartbeat)
        self._master = master
        self._areaMap = {area.roomId: area for area in areas}
        self._userId = 1040000001
        self._signerCountPerArea = 30
        self.userInfoLoader = userInfoLoader
        self.userIds = [self._userId + i for i in xrange(len(self._areaMap) * self._signerCountPerArea)]
        for userId in self.userIds:
            clientId = CLIENT_IDS[random.randint(0, len(CLIENT_IDS) - 1)]
            self.userInfoLoader.setUserAttrs(i + 1, {'name': 'user%s' % (userId),
                                                     'sessionClientId': clientId,
                                                     'snsId': 'sns%s' % (userId)})

    def start(self):
        self._heartbeat.start()

    def _doHeartbeat(self):
        isAllReady = self._isAllReady()
        ftlog.info('MatchChecker._doHeartbeat isAllReady=', isAllReady)
        if isAllReady:
            # 报名到master
            for i, area in enumerate(self._areaMap.values()):
                self._signinToMatch(area, self.userIds[
                                          i * self._signerCountPerArea:i * self._signerCountPerArea + self._signerCountPerArea])
            self._heartbeat.stop()

    def _isAllReady(self):
        if not self._master.instCtrl:
            return False
        for area in self._areaMap.values():
            if not area.curInst:
                return False
        return True

    def _signinToMatch(self, area, userIds):
        for userId in userIds:
            area.curInst.signin(userId)


if __name__ == '__main__':
    ftlog.initLog('groupmatch.log', './logs/')
    # ftlog.LOG_LEVEL_DEBUG = 0
    matchId = 6057
    masterRoomId = 60571
    areaRoomIds = [60571, 60572, 60573]
    matchConf = MatchConfig.parse(6, 60571, 6057, '满3人开赛', match_conf['matchConf'])
    areas = []
    userInfoLoader = UserInfoLoaderTest()
    master = buildMatchMaster(masterRoomId, matchId, matchConf)
    for areaRoomId in areaRoomIds:
        area = buildMatchArea(areaRoomId, matchId, matchConf, master)
        areas.append(area)
        area.userInfoLoader = userInfoLoader
        master.addAreaStub(MatchAreaStubLocal(master, area))

    master.start()
    for area in areas:
        area.start()

    MatchChecker(master, areas, userInfoLoader).start()
    stackless.tasklet(mainloop)()
    stackless.run()
