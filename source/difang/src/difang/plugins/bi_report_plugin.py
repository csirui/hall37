# coding: UTF-8
'''
BI统计插件
'''

__author__ = ['ZhouHao']

import time

import difang.entity.plugin_event_const as PluginEvent
import freetime.util.log as ftlog
from difang.gameplayer.players_helper import DiFangPlayersHelper
from poker.entity.biz import bireport
from poker.entity.configure import gdata
from poker.entity.dao import sessiondata


class DiFangBIReportPlugin(object):
    '''BI汇报类

        为了数据部能更好的进行统计, 需要大家添加以下游戏事件:
        1. create_game_data(新进用户数据源)  ---- 已经完成(赵庆辉)
        2. bind_user(游戏大厅登录用户数据源)  ---- 已经完成(赵庆辉)
        3. bind_game(游戏插件登录用户数据源)  ---- 已经完成(赵庆辉)

        4. 游戏每局开始  BiEventId.TABLE_START ---- 各个游戏后端主程
        5. 游戏每局出牌操作  BiEventId.TABLE_CARD   ---- 各个游戏后端主程
        6. 游戏每局结束  BiEventId.TABLE_WIN  ---- 各个游戏后端主程
        7. 比赛报名  BiEventId.MATCH_SIGN_UP   ---- 各个游戏后端主程
        8. 比赛退赛  BiEventId.MATCH_SIGN_OUT   ---- 各个游戏后端主程
        9. 比赛开始  BiEventId.MATCH_START   ---- 各个游戏后端主程
        10. 比赛结束  BiEventId.MATCH_FINISH   ---- 各个游戏后端主程

        各个后端主程需要再各自的代码当中调用BiReport.report_game_event方法进行事件的汇报(4~10)
        report_game_event的参数,请参考具体的代码实现
        注意: 每局每个人需要进行单独汇报, 每比赛每个人需要单独进行汇报
        注意: 需要更新trunk的tyframework和tyhall代码
    '''

    def event_handle(self, gameId):
        serverType = gdata.serverType()
        if serverType not in (gdata.SRV_TYPE_TABLE,
                              ):
            return {}

        common_handlers = {
            PluginEvent.EV_RELOAD_CONFIG: self.onEvReloadConfig,
        }

        handlers = {}

        if serverType == gdata.SRV_TYPE_TABLE:
            handlers = {
                PluginEvent.EV_TRANSIT_TO_STATE_START_GAME: self.onTableGameStart,
                PluginEvent.EV_TRANSIT_TO_STATE_FINAL: self.onTableGameWin,
            }

        handlers.update(common_handlers)
        return handlers

    def __init__(self, gameId):
        self.gameId = gameId

        self._initConf()

    def _initConf(self):
        '''初始化配置'''
        pass

    def onEvReloadConfig(self, gameId, msg):
        '''刷新配置'''
        # keyList = msg.getParam('keylist')
        # if self._configKey in keyList:
        #     self._initConf()

    def onTableGameStart(self, gameId, msg):
        if ftlog.is_debug():
            ftlog.debug("<< |msg", msg, caller=self)

        table = msg.getParam("table")

        bireport.tableStart(table.gameId, table.roomId, table.tableId,
                            table.gamePlay.gameSeq, DiFangPlayersHelper.getPlayingPlayersIds(table))

        for player in DiFangPlayersHelper.getPlayingPlayers(table):
            bireport.reportGameEvent('TABLE_START',
                                     player.userId, gameId, table.roomId, table.tableId,
                                     table.gamePlay.gameSeq,
                                     0, 0, 0, [],
                                     sessiondata.getClientId(player.userId),
                                     player.tableChips)

    def onTableGameWin(self, gameId, msg):
        if ftlog.is_debug():
            ftlog.debug("<< |msg", msg, caller=self)

        table = msg.getParam("table")

        bireport.tableWinLose(table.gameId, table.roomId, table.tableId,
                              table.gamePlay.gameSeq, DiFangPlayersHelper.getPlayingPlayersIds(table),
                              gameTime=time.time() - table.gamePlay.startTime)

        for player in DiFangPlayersHelper.getPlayingPlayers(table):
            bireport.reportGameEvent('TABLE_WIN',
                                     player.userId, gameId, table.roomId, table.tableId,
                                     table.gamePlay.gameSeq,
                                     0, 0, 0, [],
                                     sessiondata.getClientId(player.userId),
                                     player.tableChips)
