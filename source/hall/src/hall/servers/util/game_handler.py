# -*- coding: utf-8 -*-
'''
Created on 2015年5月20日

@author: zqh
'''

import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from hall.entity import hall_exit_remind
from hall.entity import halluser, hallitem, datachangenotify, hall_game_update, \
    hall_friend_table, hall_fangka, hall_fangka_buy_info
from hall.entity.hallevent import UserBindPhoneEvent
from hall.entity.todotask import TodoTaskHelper, TodoTaskGoldRain
from hall.game import TGHall
from hall.servers.common.base_checker import BaseMsgPackChecker
from hall.servers.util.util_helper import UtilHelper
from poker.entity.biz import bireport
from poker.entity.dao import gamedata
from poker.entity.events.tyevent import OnLineGameChangedEvent
from poker.protocol.decorator import markCmdActionHandler, markCmdActionMethod


@markCmdActionHandler
class GameTcpHandler(BaseMsgPackChecker):
    def __init__(self):
        self.helper = UtilHelper()

    @markCmdActionMethod(cmd='game', action="data", clientIdVer=0)
    def doGameData(self, userId, gameId, clientId):
        self.helper.sendUserInfoResponse(userId, gameId, clientId, '', 0, 1)

    @markCmdActionMethod(cmd='game', action="bindPhone", clientIdVer=0)
    def dosendChipToUser(self, userId, gameId, clientId):
        # 添加绑定
        nowBindPone = gamedata.getGameAttr(userId, gameId, 'bindReward1')
        if not nowBindPone or nowBindPone < 1:
            gamedata.setGameAttr(userId, gameId, 'bindReward1', 1)
        else:
            from poker.entity.biz.exceptions import TYBizException
            raise TYBizException(-1, '重复绑定')
        # 发金币
        ftlog.info('cmd game action bindPhone userId =', userId)
        from poker.entity.dao import userchip, daoconst
        userchip.incrChip(userId, gameId, 10000, daoconst.CHIP_NOT_ENOUGH_OP_MODE_CLEAR_ZERO, 'BIND_PHONE', 0, clientId)
        datachangenotify.sendDataChangeNotify(gameId, userId, 'chip')
        # 消息推送
        from poker.entity.biz.message import message
        msg = '恭喜您绑定手机成功，赠送您10000金币'
        message.send(gameId, message.MESSAGE_TYPE_PRIVATE, userId, msg)
        # 更新小红点
        datachangenotify.sendDataChangeNotify(gameId, userId, ['free', 'promotion_loc'])
        TGHall.getEventBus().publishEvent(UserBindPhoneEvent(userId, gameId))

    @markCmdActionMethod(cmd='game', action="enter", clientIdVer=0)
    def doGameEnter(self, userId, gameId, clientId):
        isdayfirst, iscreate = halluser.loginGame(userId, gameId, clientId)
        self.helper.sendUserInfoResponse(userId, gameId, clientId, '', 0, 1)
        self.helper.sendTodoTaskResponse(userId, gameId, clientId, isdayfirst)
        # BI日志统计
        bireport.userGameEnter(gameId, userId, clientId)
        bireport.reportGameEvent('BIND_GAME',
                                 userId, gameId, 0, 0, 0, 0, 0, 0, [], clientId, iscreate)
        evt = OnLineGameChangedEvent(userId, gameId, 1, clientId)
        TGHall.getEventBus().publishEvent(evt)

    @markCmdActionMethod(cmd='game', action="leave", clientIdVer=0)
    def doGameLeave(self, userId, gameId, clientId):
        evt = OnLineGameChangedEvent(userId, gameId, 0, clientId)
        TGHall.getEventBus().publishEvent(evt)

    @markCmdActionMethod(cmd='game', action='get_member_reward', clientIdVer=0)
    def doGameGetMemberReward(self, userId, gameId, clientId):
        userAssets = hallitem.itemSystem.loadUserAssets(userId)
        userBag = userAssets.getUserBag()
        memberCardItem = userBag.getItemByKindId(hallitem.ITEM_MEMBER_NEW_KIND_ID)
        timestamp = pktimestamp.getCurrentTimestamp()
        if memberCardItem and memberCardItem.canCheckin(timestamp):
            checkinAction = memberCardItem.itemKind.findActionByName('checkin')
            checkinAction.doAction(gameId, userAssets, memberCardItem, timestamp, {})
            datachangenotify.sendDataChangeNotify(gameId, userId, 'free')
            TodoTaskHelper.sendTodoTask(gameId, userId, TodoTaskGoldRain('恭喜您领取了今天的会员福利'))

    @markCmdActionMethod(cmd='game', action='get_exit_remind', clientIdVer=0)
    def doGameGetExitRemind(self, userId, gameId, clientId):
        hall_exit_remind.queryExitRemind(gameId, userId, clientId)

    @markCmdActionMethod(cmd='game', action='get_fangka_item', clientIdVer=0)
    def doGetFangKaItem(self, userId, gameId, clientId):
        hall_fangka.sendFangKaItemToClient(gameId, userId, clientId)

    @markCmdActionMethod(cmd='game', action='require_fangka_buy_info', clientIdVer=0)
    def doRequireFangBuyInfo(self, userId, gameId, clientId):
        hall_fangka_buy_info.queryFangKaBuyInfo(gameId, userId, clientId)

    @markCmdActionMethod(cmd='game', action='get_game_update_info', clientIdVer=0)
    def doGameGetUpdateInfo(self, userId, gameId, clientId, version, updateVersion):
        hall_game_update.getUpdateInfo(gameId, userId, clientId, version, updateVersion)

    @markCmdActionMethod(cmd='game', action='update_notify', clientIdVer=0)
    def doGameUpdateNotify(self, userId, gameId, clientId, module):
        '''
        通知前端更新消息
        '''
        from hall.entity.hallconf import HALL_GAMEID
        datachangenotify.sendDataChangeNotify(HALL_GAMEID, userId, module)

    @markCmdActionMethod(cmd='game', action='enter_friend_table', clientIdVer=0)
    def doEnterFriendTable(self, userId, gameId, clientId, ftId):
        '''
        通知前端更新消息
        '''
        hall_friend_table.enterFriendTable(userId, gameId, clientId, ftId)
