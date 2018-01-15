# -*- coding=utf-8 -*-
'''
'''
from difang.plugins.custom_room_plugin import DiFangCustomRoomPlugin

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

from datetime import datetime
import freetime.util.log as ftlog
from freetime.util.log import catchedmethod

from poker.entity.configure import gdata
from poker.entity.events.tyevent import EventHeartBeat, EventConfigure
from poker.entity.events.tyeventbus import globalEventBus
from poker.entity.game.game import TYGame
from poker.entity.game.plugin import TYPluginCenter, TYPluginUtils
from poker.entity.dao import gamedata
from poker.entity.game.rooms import tyRoomConst

from hall.entity.todotask import TodoTaskEnterGameNew, TodoTaskHelper

import difang.entity.plugin_event_const as PluginEvent
from difang.quick_start import DiFangQuickStartDispatcher
from difang.entity.account import DiFangAccount
from difang.robot.robot import DiFangRobotManager
from difang.servers.http.common import DiFangHTTPCommon
from difang.entity.conf import GAME_ID


class DiFangGame(TYGame):
    GAME_ID = GAME_ID
    RobotManagerClass = DiFangRobotManager
    AccountClass = DiFangAccount
    QuickStartDispatcherClass = DiFangQuickStartDispatcher
    CommonHttpHandlerClass = DiFangHTTPCommon

    def initGame(self):
        if ftlog.is_debug():
            ftlog.debug("<< |gameId:", self.GAME_ID, caller=self)

        self.gameInitTime = datetime.now()
        self._now = datetime.now()

        if self.GAME_ID == GAME_ID:
            return

        serverType = gdata.serverType()

        if serverType == gdata.SRV_TYPE_ROBOT:
            self.initRobotServerGame()
        elif serverType == gdata.SRV_TYPE_UTIL:
            self.initUtilServerGame()
        elif serverType == gdata.SRV_TYPE_TABLE:
            self.initGTServerGame()
        elif serverType == gdata.SRV_TYPE_HTTP:
            self.initHTServerGame()
        elif serverType == gdata.SRV_TYPE_ROOM:
            self.initGRServerGame()

        globalEventBus.subscribe(EventConfigure, self.onReloadConfig)
        globalEventBus.subscribe(EventHeartBeat, self.onEventHeartBeat)

    def initRobotServerGame(self):
        self._robotmgr = self.RobotManagerClass(self.GAME_ID)
        globalEventBus.subscribe(EventHeartBeat, self._robotmgr.onHeartBeat)

    def initUtilServerGame(self):
        pass

    def initGTServerGame(self):
        pass

    def initGRServerGame(self):
        pass

    def initHTServerGame(self):
        self.commonHttpHandler = self.CommonHttpHandlerClass()
        self.commonHttpHandler.GAME_ID = self.gameId()

    def getCommonHttpHandler(self):
        return self.commonHttpHandler

    def gameId(self):
        '''
        取得当前游戏的GAMEID, int值
        '''
        return self.GAME_ID

    def newTable(self, room, tableId):
        if room.roomConf['typeName'] == tyRoomConst.ROOM_TYPE_NAME_CUSTOM:
            return self.CustomTableClass(room, tableId)

        raise Exception("invalid typeName")

    def getInitDataKeys(self):
        '''
        取得游戏数据初始化的字段列表
        '''
        return self.AccountClass.getInitDataKeys()

    def getGameInfo(self, userId, clientId):
        '''
        取得当前用户的游戏账户信息dict
        '''
        return self.AccountClass.getGameInfo(userId, self.GAME_ID, clientId)

    def getDaShiFen(self, userId, clientId):
        '''
        取得当前用户的游戏账户的大师分信息
        '''
        return self.AccountClass.getDaShiFen(userId, self.GAME_ID, clientId)

    def getTodoTasksAfterLogin(self, userId, gameId, clientId, isdayfirst):
        '''
        获取登录后的todotasks列表
        '''
        if ftlog.is_debug():
            ftlog.debug('<< |userId=', userId,
                        'gameId=', gameId,
                        'clientId=', clientId,
                        'isdayfirst=', isdayfirst, caller=self)

    def createGameData(self, userId, clientId):
        '''
        初始化该游戏的所有的相关游戏数据
        包括: 主游戏数据gamedata, 道具item, 勋章medal等
        返回主数据的键值和值列表
        '''
        return self.AccountClass.createGameData(userId, self.GAME_ID, clientId)

    def loginGame(self, userId, gameId, clientId, iscreate, isdayfirst):
        '''
        用户登录一个游戏, 游戏自己做一些其他的业务或数据处理
        例如: 1. IOS大厅不发启动资金的补丁, 
             2. 麻将的记录首次登录时间
             3. 游戏插件道具合并至大厅道具
        '''
        ftlog.hinfo('loginGame <<|userId=', userId,
                    'gameId=', gameId,
                    'clientId=', clientId,
                    'isdayfirst=', isdayfirst, caller=self)
        self.AccountClass.loginGame(userId, gameId, clientId, iscreate, isdayfirst)

        # 获取前端代码版本号。以这个版本号判断前端功能
        # msg = runcmd.getMsgPack()
        # codeVer = msg.getParam('v', 0)
        # gamedata.setGameAttr(userId, gameId, 'codeVer', codeVer)

        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd='EV_USER_LOGIN', params={
            'userId': userId, 'isCreate': iscreate,
            'clientId': clientId, 'dayFirst': isdayfirst,
            # 'codeVer': codeVer,
        }), gameId)

    def onReloadConfig(self, event):
        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd=PluginEvent.EV_RELOAD_CONFIG, params={
            'keylist': event.keylist}), self.gameId())

    def onEventHeartBeat(self, event):
        self.onServerHeartBeat()
        TYPluginCenter.event(TYPluginUtils.updateMsg(cmd=PluginEvent.EV_SERVER_HEART_BEAT, params={
            'event': event}), self.gameId())

    def onServerHeartBeat(self):
        """
        处理 server heart beat, 并发出时间事件

        服务器心跳每秒一次, 这个函数会识别时间, 在每分钟、小时、天、星期(周一0:00)、月、年的开始, 发出一个事件
        """

        now = datetime.now()
        last = self._now
        self._now = now

        newTimePoints = []

        if last.minute != now.minute:
            newTimePoints.append('minute')
        if last.hour != now.hour:
            newTimePoints.append('hour')
        if last.day != now.day:
            newTimePoints.append('day')
        if last.weekday() != now.weekday() and now.weekday() == 0:  # 周一
            newTimePoints.append('week')
        if last.month != now.month:
            newTimePoints.append('month')
        if last.year != now.year:
            newTimePoints.append('year')

        if newTimePoints:
            msg = TYPluginUtils.updateMsg(cmd=PluginEvent.EV_NEW_TIME, params={
                'newTimePoints': newTimePoints, 'now': now, 'last': last})

            TYPluginCenter.event(msg, self.gameId())

    @catchedmethod
    def initGameAfter(self):
        serverType = gdata.serverType()
        if ftlog.is_debug():
            ftlog.debug("<< |gameId, serverType:", self.gameId(), serverType)

        if serverType in (gdata.SRV_TYPE_HTTP,
                          gdata.SRV_TYPE_UTIL,
                          gdata.SRV_TYPE_ROOM,
                          gdata.SRV_TYPE_TABLE,
                          gdata.SRV_TYPE_CENTER):
            TYPluginCenter.reload(self.GAME_ID)

        if serverType == gdata.SRV_TYPE_TABLE:
            for room in gdata.rooms().values():
                if room.gameId != self.gameId():
                    continue

                if ftlog.is_debug():
                    ftlog.debug("init tables"
                                "|gameId, serverType, roomId:",
                                self.gameId(), serverType, room.roomId)

                for table in room.maptable.values():
                    TYPluginCenter.evmsg(table.gameId,
                                         PluginEvent.EV_AFTER_TABLE_CHILD_INIT,
                                         {'table': table,
                                          'tableType': table.tableType})

    def enterFriendTable(self, userId, gameId, clientId, ftId):
        """进入自建桌，插件实现具体功能"""
        if ftlog.is_debug():
            ftlog.debug('|userId, gameId, clientId, ftId:', userId, gameId, clientId, ftId, caller=self)

        tableId = DiFangCustomRoomPlugin.getTableIdOfFtId(self.GAME_ID, ftId)

        if not tableId:
            ftlog.error("enterFriendTable not tableId |userId, gameId, clientId, ftId:", userId, gameId, clientId, ftId)
            return

        enterParams = {
            "type": "game",  # 需要前端统一
            "pluginParams": {
                "gameType": 11,  # 需要前端统一
                "ftId": ftId,
                "tableId": tableId,
                "roomId": tableId / 10000
            }
        }

        todotask = TodoTaskEnterGameNew(self.GAME_ID, enterParams)
        TodoTaskHelper.sendTodoTask(gameId, userId, todotask)

    def checkFriendTable(self, ftId):
        tableId = DiFangCustomRoomPlugin.getTableIdOfFtId(self.GAME_ID, ftId)
        return True if tableId else False

    def getPlayGameInfoByKey(self, userId, clientId, keyName):
        if keyName == TYGame.PLAY_COUNT:
            countStr = gamedata.getGameAttr(userId, self.GAME_ID, 'play_game_count')
            if not countStr:
                return 0
            return int(countStr)

        elif keyName == TYGame.WIN_COUNT:
            winStr = gamedata.getGameAttr(userId, self.GAME_ID, 'win_game_count')
            if not winStr:
                return 0
            return int(winStr)

        return None


def getInstance():
    return DiFangGame()
