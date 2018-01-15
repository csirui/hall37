# -*- coding:utf-8 -*-
'''
Created on 2014年9月24日

@author: zjgzzz@126.com, zhouhao@tuyoogame.com
'''

import stackless

from freetime.core.reactor import mainloop
from freetime.core.timer import FTTimer
from poker.entity.game.rooms.big_match_ctrl.config import MatchConfig
from poker.entity.game.rooms.big_match_ctrl.interfacestest import UserDatabase, SigninDatabase, \
    TableControllerTest, PlayerNotifierTest, SigninRecordDaoTest, MatchStatusDaoTest, \
    SigninFeeTest, UserInfoLoaderTest, MatchRewardsTest, PlayerLocationTest
from poker.entity.game.rooms.big_match_ctrl.match import TableManager, Match

userdb = UserDatabase()
signindb = SigninDatabase()
tableController = TableControllerTest(userdb)
playerLocation = PlayerLocationTest(userdb)
playerNotifier = PlayerNotifierTest()
signinRecordDao = SigninRecordDaoTest(signindb)
matchStatusDao = MatchStatusDaoTest()
signinFee = SigninFeeTest(userdb)
userInfoLoader = UserInfoLoaderTest(userdb)
matchRewards = MatchRewardsTest(userdb)


def initUsers():
    for i in xrange(3):
        userdb.addUser(i + 1, 'user%s' % (i + 1))


def buildMatch(conf):
    tableManager = TableManager(conf.gameId, conf.tableSeatCount)
    tableManager.addTables(61101, 1, 10)
    tableManager.addTables(61102, 1, 10)
    match = Match(conf)
    match.tableManager = tableManager
    match.matchStatusDao = matchStatusDao
    match.signinFee = signinFee
    match.playerLocation = playerLocation
    match.tableController = tableController
    match.playerNotifier = playerNotifier
    match.userInfoLoader = userInfoLoader
    match.signinRecordDao = signinRecordDao
    match.matchRewards = matchRewards
    return match


matchTips = {
    "infos": [
        "当积分相同时，按报名先后顺序确定名次。",
        "除海选赛阶段，只有力争第一才可以晋级！",
        "天生我材必有用，有用就得斗地主！",
        "忽如一夜春风来，千人万人牌桌开！",
        "普通场获得勋章时，记得领取相应奖励哦。",
        "万人比赛火热上线，记得要关注哦。",
        "海选阶段要稳打，低于基础分会被淘汰哟！",
    ],
    "interval": 5
}

match_conf_612 = {
    "desc": "开赛时间：满3人开赛\n赛制：定局淘汰(共1局,每局2副牌)\n报名费用：5000金币",
    "table.seat.count": 3,
    "tips": matchTips,
    # 比赛开始条件定义
    "start": {
        "type": 1,  # 人满开赛
        "user.size": 3,  # 人满开赛的人数
        "maxplaytime": 60 * 60,  # 预订的比赛的最大时间，用于终止无法结束的比赛
        "fee.type": 1,  # 比赛开赛时，如果用户不在线，是否返还用户参赛费， 1--返还 0--不返还
    },
    # 报名费定义
    "fees": [
        {"name": "CHIP", "count": 5000}
    ],
    "stages": [
        {
            "type": 2,  # 淘汰 赛制
            "name": "决赛",  #
            "animation.type": 3,  # 0 海选赛; 1 N强赛; 2 决赛; 3 vs动画; 4 配桌动画
            "seat.principles": 1,  # 1-随机 2-蛇型 3-种子 4-进入时间
            "card.count": 2,  # 固定打多少副牌
            "rise.user.count": 1,  # 晋级人数
            "chip.user": 1000,  # 当前阶段用户的初始游戏基数, 0-无变化 1-平方根 2-百分比 3-开方放大发 >10-重置当前所有用户的游戏基数
            "chip.user.3.base": 0,  # 开方放大发时的计算基准值
            "chip.base": 100,  # 当前阶段游戏基数,如果<=0则继承上一个阶段的值，否则重置
            "chip.times": 60 * 60,  # 游戏基数增长时间，单位秒,如果<=0则继承上一个阶段的值，否则重置
            "chip.grow": 0.5,  # 当前阶段游戏基数增长的比率0.25意味25%增长，如果是大于99的整数，则为固定的增长, 如果<=0则继承上一个阶段的值，否则重置
        }
    ],
    "rank.rewards": [
        {
            "ranking": {"start": 1, "end": 1},
            "rewards": [
                {"name": "CHIP", "count": 10000},
                {"name": "EXP", "count": 200},
                {"name": "1012", "count": 1}
            ],
            "desc": u"10000金币+特惠礼包"
        },
        {
            "ranking": {"start": 2, "end": 2},
            "rewards": [
                {"name": "CHIP", "count": 3500},
                {"name": "EXP", "count": 60},
                {"name": "1012", "count": 1}
            ],
            "desc": u"3500金币+特惠礼包"
        },
        {
            "ranking": {"start": 3, "end": 3},
            "rewards": [
                {"name": "1012", "count": 1}
            ],
            "desc": u"特惠礼包"
        },
    ]
}


def matchStart():
    initUsers()
    conf = MatchConfig.parse(6, 612, '满3人开赛', match_conf_612)
    conf.tableId = 1
    conf.seatId = 1
    match = buildMatch(conf)
    match.load()
    #     match.doHeartbeat()
    match.signin(1)
    #     match.doHeartbeat()
    match.signin(2)
    #     match.doHeartbeat()
    match.signin(3)


if __name__ == '__main__':
    FTTimer(1, matchStart)
    stackless.tasklet(mainloop)()
    stackless.run()

    #     match.doHeartbeat()
    #     match.doHeartbeat()
    #     match.doHeartbeat()
    #     Utils.currentTimestamp = time.time() + 160
    #     match.doHeartbeat()
    #     player = match.findMatchingPlayer(1)
    #     match.winlose(player.seat.table.tableId, player.seat.table.ccrc, player.seat.seatId, 1, 20, True)
    #     match.winlose(2, 10, False)
    #     match.winlose(3, 10, False)
    #     Utils.currentTimestamp = time.time() + 160
    #     match.doHeartbeat()
    #     Utils.currentTimestamp = time.time() + 160
    #     match.doHeartbeat()
    #     Utils.currentTimestamp = time.time() + 160
    #     player = match.findMatchingPlayer(1)
    #     match.winlose(player.seat.table.tableId, player.seat.table.ccrc, player.seat.seatId, 1, 20, True)
    #     match.winlose(2, -10, False)
    #     match.winlose(3, -10, False)
    #     match.doHeartbeat()
    #     match.winlose(1, 20, True)
    #     match.winlose(2, -10, False)
    #     match.winlose(3, -10, False)
    #     match.doHeartbeat()
    #     match.winlose(1, 20, True)
    #     match.winlose(2, -10, False)
    #     match.winlose(3, -10, False)
    #     match.doHeartbeat()
    #     match.winlose(1, 20, True)
    #     match.winlose(2, -10, False)
    #     match.winlose(3, -10, False)
    #     match.doHeartbeat()
    #     match.doHeartbeat()
    #     match.doHeartbeat()
    #     match.doHeartbeat()
    #     match.doHeartbeat()
    #     match.doHeartbeat()
    for user in userdb.users.values():
        print 'userId=', user.userId, 'location=', user.location
    print 'ok'
