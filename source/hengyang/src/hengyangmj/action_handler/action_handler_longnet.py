# -*- coding=utf-8
'''
Created on 2017年3月1日

@author: nick.kai.lee
'''
from difang.majiang2.action_handler.action_handler_longnet import ActionHandlerLongNet
from hengyangmj.hengyang_log import HYLog


class HYActionHandlerLongNet(ActionHandlerLongNet):
    def __init__(self):
        super(HYActionHandlerLongNet, self).__init__()

    def handleTableCallChi(self, user_id, seat_id, message):
        """
        玩家吃牌上行消息 (框架调用)
        参数说明：
        @param user_id, 协议发送方的用户id
        @param seat_id, 协议发送方的座位号
        @param message 协议其他数据
        协议示例
        {"cmd":"table_call","params":{"action":"chi","action_id":24,"tile":4,"pattern":[2,3,4],"seatId":0,
            "roomId":72018031001,"tableId":720180310010200,"gameId":7201,"userId":10001,"clientId":"Android_3.901_weixin,tyGuest.alipay.0-hall7201.youle.hengyangmj"}
        """
        action_id = message.getParam('action_id')
        if action_id == self.table.actionID:
            tile = message.getParam('tile', None)
            pattern = message.getParam('pattern', None)
            pattern.sort()
            if not pattern or not tile:
                HYLog.error('handleTableCallChi: wrong pattern or tile word!', pattern, tile)
            self.table.do_chow_tile(seat_id, tile, pattern)
        else:
            HYLog.info('handleTableCallChi: wrong actionId:', action_id, ' ,now table actionId:', self.table.actionID,
                       ', message:', message)
        pass

    def handleTableCallPeng(self, user_id, seat_id, message):
        """
        玩家碰牌上行消息 (框架调用)
        参数说明：
        @param user_id, 协议发送方的用户id
        @param seat_id, 协议发送方的座位号
        @param message 协议其他数据
        协议示例
        {"cmd":"table_call","params":{"action":"peng","action_id":24,"tile":4,"pattern":[4,4,4],"seatId":0,
            "roomId":72018031001,"tableId":720180310010200,"gameId":7201,"userId":10001,"clientId":"Android_3.901_weixin,tyGuest.alipay.0-hall7201.youle.hengyangmj"}
        """
        action_id = message.getParam('action_id')
        if action_id == self.table.actionID:
            tile = message.getParam('tile', None)
            pattern = message.getParam('pattern', None)
            if not pattern or not tile:
                HYLog.error('handleTableCallPeng: wrong pattern or tile word!', pattern, tile)
            self.table.do_pong_tile(seat_id, tile, pattern)
        else:
            HYLog.info('handleTableCallPeng: wrong actionId:', action_id, ' ,now table actionId:', self.table.actionID,
                       ', message:', message)
        pass

    def handleTableCallGang(self, user_id, seat_id, message):
        """
        玩家杠牌上行消息 (框架调用)
        参数说明：
        @param user_id, 协议发送方的用户id
        @param seat_id, 协议发送方的座位号
        @param message 协议其他数据
        协议示例
        {"cmd":"table_call","params":{"action":"gang","action_id":24,"tile":4,"gang":{"style":1,"pattern":[4,4,4,4]},"seatId":0,
            "roomId":72018031001,"tableId":720180310010200,"gameId":7201,"userId":10001,"clientId":"Android_3.901_weixin,tyGuest.alipay.0-hall7201.youle.hengyangmj"}
        """
        action_id = message.getParam('action_id')
        if action_id == self.table.actionID:
            kong = message.getParam('gang', None)
            tile = message.getParam('tile', None)
            if not kong or not tile:
                HYLog.error('handleTableCallGang: wrong gang or tile word!', kong, tile)
                return

            style = kong.get('style')
            pattern = kong.get('pattern')
            pattern.sort()

            self.table.do_kong_tile(seat_id, tile, pattern, style)
        else:
            HYLog.info('handleTableCallGang: wrong actionId:', action_id, ' ,now table actionId:', self.table.actionID,
                       ', message:', message)
        pass

    def handleTableCallWin(self, user_id, seat_id, message):
        """
        玩家胡牌上行消息 (框架调用)
        参数说明：
        @param user_id, 协议发送方的用户id
        @param seat_id, 协议发送方的座位号
        @param message 协议其他数据
        协议示例
        {"cmd":"table_call","params":{"action":"win","action_id":24,"tile":4,"seatId":0,
            "roomId":72018031001,"tableId":720180310010200,"gameId":7201,"userId":10001,"clientId":"Android_3.901_weixin,tyGuest.alipay.0-hall7201.youle.hengyangmj"}
        """
        action_id = message.getParam('action_id')
        if action_id == self.table.actionID:
            tile = message.getParam('tile')
            if not tile:
                HYLog.error('handleTableCallWin: wrong tile word!', tile)
                return
            self.table.do_win_tile(seat_id, tile)
        else:
            HYLog.info('handleTableCallWin: wrong actionId:', action_id, ' ,now table actionId:', self.table.actionID,
                       ', message:', message)
