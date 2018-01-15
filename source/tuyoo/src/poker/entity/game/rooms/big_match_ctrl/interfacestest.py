# -*- coding:utf-8 -*-
'''
Created on 2014年9月24日

@author: zjgzzz@126.com
'''

import freetime.util.log as ftlog

from poker.entity.game.rooms.big_match_ctrl.exceptions import MatchException
from poker.entity.game.rooms.big_match_ctrl.interfaces import TableController, PlayerNotifier, \
    SigninRecordDao, MatchStatusDao, SigninFee, MatchRewards, UserInfoLoader, \
    PlayerLocation


class User(object):
    def __init__(self, userId, name):
        # key=string value=count
        self.userId = userId
        self.name = name
        self.items = {}
        self.matchInstId = None
        self.location = None

    def addItem(self, name, count):
        if name in self.items:
            self.items[name] += count
        else:
            self.items[name] = count
        return self.items[name]


class UserDatabase(object):
    def __init__(self):
        self.users = {}

    def addUser(self, userId, name):
        assert (userId not in self.users)
        self.users[userId] = User(userId, name)

    def findUser(self, userId):
        return self.users.get(userId)


class PlayerLocationTest(PlayerLocation):
    def __init__(self, userdb):
        self.userdb = userdb

    def getLocation(self, userId):
        '''
        获取用户的location
        '''
        user = self.userdb.findUser(userId)
        assert (user)
        if user.location:
            parts = user.location.split('.', 3)
            return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
        return 0, 0, 0, 0

    def setLocationForce(self, userId, gameId, roomId, tableId, seatId):
        '''
        设置location
        '''
        user = self.userdb.findUser(userId)
        assert (user)
        location = '%s.%s.%s.%s' % (gameId, roomId, tableId, seatId)
        user.location = location
        ftlog.info('PlayerLocation.setLocationForce userId=', userId, 'location=', location)

    def clearLocationForce(self, userId, gameId, roomId):
        '''
        清除location
        '''
        ftlog.info('PlayerLocation.clearLocationForce userId=', userId,
                   'gameId=', gameId, 'roomId=', roomId)

    def redictToLocation(self, userId):
        '''
        重定向用户
        '''
        ftlog.info('PlayerLocation.clearLocationForce userId=', userId)


class TableControllerTest(TableController):
    def __init__(self, userdb):
        self.userdb = userdb

    def startTable(self, table):
        '''
        让player在具体的游戏中坐到seat上
        '''
        playerList = table.getPlayerList()
        ftlog.debug('TableControllerTest.quickStart group=', table.group.groupId,
                    'tableId=', table.tableId, 'userIds=', [p.userId for p in playerList])

    def clearTable(self, table):
        '''
        '''
        playerList = table.getPlayerList()
        ftlog.debug('TableControllerTest.clearTable group=', table.group.groupId,
                    'tableId=', table.tableId, 'userIds=', [p.userId for p in playerList])


class PlayerNotifierTest(PlayerNotifier):
    def notifyMatchCancelled(self, player, inst, reason):
        '''
        通知用户比赛由于reason取消了
        '''
        ftlog.debug('PlayerNotifierTest.notifyMatchCancelled userId=', player.userId,
                    'matchInst=', inst.instId, 'reason=', reason)

    def notifyMatchOver(self, player, group, reason, rankRewards):
        '''
        通知用户比赛结束了
        '''
        ftlog.debug('PlayerNotifierTest.notifyMatchOver userId=', player.userId,
                    'group=', group.groupId, 'reason=', reason, 'rewards=',
                    rankRewards.rewards if rankRewards else None)

    def notifyMatchIncrNote(self, group, table):
        '''
        通知比赛更新
        '''
        userIds = table.getUserIdList()
        ftlog.debug('PlayerNotifierTest.notifyMatchIncrNote userIds=', userIds,
                    'group=', group.groupId, 'table=', table.tableId)

    def notifyMatchUpdate(self, player):
        '''
        通知比赛更新
        '''
        ftlog.debug('PlayerNotifierTest.notifyMatchUpdate userId=', player.userId)

    def notifyMatchWait(self, players, group, step=None):
        '''
        通知用户等待
        '''
        if not isinstance(players, list):
            players = [players]
        userIds = [p.userId for p in players]
        ftlog.debug('PlayerNotifierTest.notifyMatchWait userIds=', userIds,
                    'group=', group.groupId, 'step=', step)


class SigninDatabase(object):
    def __init__(self):
        # key = instId, value = dict<userId, signinTime>
        self.records = {}

    def set(self, instId, userId, signinTime):
        subRecords = self.records.get(instId)
        if subRecords is None:
            subRecords = {}
            self.records[instId] = subRecords
        subRecords[userId] = signinTime

    def remove(self, instId, userId):
        subRecords = self.records.get(instId)
        if subRecords and userId in subRecords:
            del subRecords[userId]

    def removeAll(self, instId):
        if instId in self.records:
            del self.records[instId]


class SigninRecordDaoTest(SigninRecordDao):
    def __init__(self, signindb):
        self.signindb = signindb

    def load(self, matchId, instId):
        '''
        加载所有报名记录
        @return: list((userId, signinTime))
        '''
        records = self.signindb.records.get(instId)
        if records:
            return [(userId, signinTime) for userId, signinTime in records.items()]
        return []

    def recordSignin(self, matchId, instId, userId, timestamp):
        '''
        记录报名信息
        '''
        self.signindb.set(instId, userId, timestamp)

    def removeSignin(self, matchId, instId, userId):
        '''
        删除报名信息
        '''
        self.signindb.remove(instId, userId)

    def removeAll(self, matchId, instId):
        '''
        '''
        self.signindb.removeAll(instId)


class MatchStatus(object):
    def __init__(self):
        self.matchId = None
        self.matchInstId = None
        self.matchStartTime = None


class MatchStatusDaoTest(MatchStatusDao):
    def __init__(self):
        # key=matchId, value=MatchStatus
        self.statuses = {}

    def load(self, matchId):
        '''
        加载比赛信息
        @return: MatchStatus
        '''
        return self.statuses.get(matchId, None)

    def save(self, status):
        '''
        保存比赛信息
        '''
        self.statuses[status.matchId] = status


class SigninFeeTest(SigninFee):
    def __init__(self, userdb):
        self.userdb = userdb

    def collectFees(self, inst, userId, fees):
        '''
        收取用户报名费
        '''
        user = self.userdb.findUser(userId)
        assert (user)
        # 查看是否够
        for fee in fees:
            if fee['count'] <= 0:
                continue
            if (fee['name'] not in user.items
                or user.items[fee['name']] < fee['count']):
                raise MatchException(-1, '报名费不足')
        for fee in fees:
            if fee['count'] > 0:
                user.items[fee['name']] -= fee['count']
        return True

    def returnFees(self, inst, userId, fees):
        '''
        退还报名费
        '''
        user = self.userdb.findUser(userId)
        assert (user)
        # 查看是否够
        for fee in fees:
            if fee['count'] <= 0:
                continue
            user.addItem(fee)


class MatchRewardsTest(MatchRewards):
    def __init__(self, userdb):
        self.userdb = userdb

    def sendRewards(self, player, group, rankRewards):
        '''给用户发送奖励'''
        user = self.userdb.findUser(player.userId)
        assert (user)

        for reward in rankRewards.rewards:
            user.addItem(reward['name'], reward['count'])
        ftlog.debug('MatchRewardsTest.sendRewards userId=', player.userId,
                    'group=', group.groupId, 'rewards=', rankRewards.rewards)


class UserInfoLoaderTest(UserInfoLoader):
    def __init__(self, userdb):
        self.userdb = userdb

    def loadUserName(self, userId):
        '''
        获取用户名称
        '''
        user = self.userdb.findUser(userId)
        assert (user)
        return user.name

    def loadUserAttrs(self, userId, attrs):
        '''
        '''
        user = self.userdb.findUser(userId)
        assert (user)
        return user.name, ""
