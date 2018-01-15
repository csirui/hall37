# -*- coding=utf-8 -*-
'''
'''
from poker.util import strutil

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import time

import freetime.util.log as ftlog

from poker.entity.dao import gamedata
from poker.entity.game import plugin
from poker.entity.game.plugin import TYPluginUtils


# from hall.entity import hallstartchip, hallbenefits, hallranking



class DiFangAccount(object):
    # Redis 中 gamedata 的初始化数据，至少两个属性
    gamedata_init_values = {
        "lastlogin": 0,
        "nslogin": 0,
    }

    @classmethod
    def getInitDataKeys(cls):
        return cls.gamedata_init_values.keys()

    @classmethod
    def addGameData(cls, userId, gameId, clientId, gdata):
        pass

    @classmethod
    def getGameInfo(cls, userId, gameId, clientId):
        ''' 获取 gamedta，用来在 bind_game/user_info中返回给前端 '''

        if ftlog.is_debug():
            ftlog.debug('<<|gameId, userId, clientId:', gameId, userId, clientId, caller=cls)

        # matchScores = None
        # if gdata.games()[gameId].RANKING_ID_MTT:
        #     matchScores = hallranking.rankingSystem.getRankingUser(gdata.games()[gameId].RANKING_ID_MTT, userId).score
        # if matchScores == None:
        #     matchScores = 0
        #
        gameData = {
            #         'headUrl': userdata.getAttr(userId, 'purl'),
            #         'gameTime': 0, #TODO:
            #         'matchScores': matchScores,
        }

        # keys = ['photo', 'lastlogin', 'winChips', 'loginsum']
        # values = gamedata.getGameAttrs(userId, gameId, ['photo', 'lastlogin', 'accwinchips', 'loginsum'])
        # gameData.update(dict(zip(keys, values)))

        # cls.addGameData(userId, gameId, clientId, gameData)

        plugin.TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_GET_GAME_DATA',
                                                            params={'userId': userId, 'gamedata': gameData}), gameId)

        if ftlog.is_debug():
            ftlog.debug('>>|gameId, userId, clientId, gdata:', gameId, userId, clientId, gameData, caller=cls)

        return gameData

    @classmethod
    def getDaShiFen(cls, userId, gameId, clientId):
        if ftlog.is_debug():
            ftlog.debug('<< |gameId, userId, clientId:', gameId, userId, clientId, caller=cls)

            # ev_msg = plugin.TYPluginUtils.updateMsg(cmd='EV_GET_DA_SHI_FEN',
            #         params={'userId': userId},
            #         result={'dashifen': {}},
            #         )
            # plugin.TYPluginCenter.event(ev_msg, gameId)
            #
            # return ev_msg.getResult('dashifen')

    @classmethod
    def createGameData(cls, userId, gameId, clientId):
        '''初始化该游戏的所有的相关游戏数据'''
        if ftlog.is_debug():
            ftlog.debug('<< |gameId, userId, clientId:', gameId, userId, clientId, caller=cls)

        gdatas = strutil.cloneData(cls.gamedata_init_values)
        gdatas['createTime'] = int(time.time())

        # photo = random.choice(cls.CLIENT_PHONE_NAMES)
        # gdatas['photo'] = photo

        gdkeys = gdatas.keys()
        gvals = gdatas.values()

        gamedata.setGameAttrs(userId, gameId, gdkeys, gvals)

        return gdkeys, gvals

    @classmethod
    def loginGame(cls, userId, gameId, clientId, iscreate, isdayfirst):
        '''用户登录一个游戏, 游戏自己做一些其他的业务或数据处理'''
        if ftlog.is_debug():
            ftlog.debug("<< |userId, gameId, clientId, iscreate, isdayfirst:",
                        userId, gameId, clientId, iscreate, isdayfirst, caller=cls)
            # if not (iscreate or hallstartchip.needSendStartChip(userId, gameId)):
            #     hallbenefits.benefitsSystem.sendBenefits(gameId, userId, pktimestamp.getCurrentTimestamp())
