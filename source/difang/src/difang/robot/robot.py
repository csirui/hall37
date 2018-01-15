# -*- coding=utf-8 -*-
from difang.resource import loadResource
from freetime.util import log as ftlog
from poker.entity.configure import gdata
from poker.entity.robot import robot
from poker.entity.robot.robot import TYRobotManager, MAX_ROBOT_UID
from poker.util import strutil

robot.TEST_ROBOT = True  # 允许机器人坐一桌


class DiFangRobotManager(TYRobotManager):
    def __init__(self, gameId):
        super(DiFangRobotManager, self).__init__()
        res = loadResource('robot_info.json')
        rinfo = strutil.loads(res)
        baseSnsId = rinfo['basesnsid'] + gdata.serverId()
        users = []
        names = ["rb_" + str(gameId) + "_" + str(uid) for uid in xrange(MAX_ROBOT_UID)]
        # names = ["rb_" + str(uid + 1) for uid in xrange(MAX_ROBOT_UID)]
        #         names = rinfo["names"]
        for x in xrange(len(names)):
            name = names[x]
            snsId = baseSnsId + '_' + str(gameId) + "_" + str(x)
            users.append(gdata.games()[gameId].RobotUserClass(None, snsId, name))
        self.freeRobotUsers = users

        ftlog.info('>> |gameId, robot user count:', gameId, len(users), caller=self)
