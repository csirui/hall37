# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''
import copy
import json
import random

import poker.util.timestamp as pktimestamp
from difang.majiang2.ai.play_mode import MPlayMode
from difang.majiang2.entity import uploader, majiang_conf
from difang.majiang2.msg_handler.msg import MMsg
from difang.majiang2.player.player import MPlayer
from difang.majiang2.table_state.state import MTableState
from freetime.core.tasklet import FTTasklet
from freetime.entity.msg import MsgPack
from freetime.util import log as ftlog
from poker.entity.dao import sessiondata
from poker.entity.game.tables.table_player import TYPlayer
from poker.protocol import router


class MMsgLongNet(MMsg):
    def __init__(self):
        super(MMsgLongNet, self).__init__()

    def table_call_add_card(self, player, tile, state, seatId, timeOut, actionId, extendInfo, changeInfo=None):
        """给玩家发牌，只给收到摸牌的玩家发这条消息
        参数说明：
        seatId - 发牌玩家的座位号
        {
            "cmd": "send_tile",
            "result": {
                "gameId": 7,
                "gang_tiles": [],
                "peng_tiles": [],
                "chi_tiles": [],
                "timeout": 9,
                "tile": 6,
                "remained_count": 53,
                "seatId": 0,
                "trustee": 0,
                "standup_tiles": [
                    2,
                    3,
                    4,
                    8,
                    12,
                    12,
                    14,
                    19,
                    19,
                    22,
                    23,
                    24,
                    35
                ],
                "action_id": 1
            }
        }
        
        "ting_action": [
            [
                8,
                [
                    [
                        12,
                        1,
                        1
                    ]
                ]
            ],
            [
                2,
                [
                    [
                        12,
                        1,
                        1
                    ]
                ]
            ],
            [
                12,
                [
                    [
                        2,
                        1,
                        3
                    ],
                    [
                        5,
                        1,
                        0
                    ],
                    [
                        8,
                        1,
                        1
                    ]
                ]
            ],
            [
                5,
                [
                    [
                        12,
                        1,
                        1
                    ]
                ]
            ]
        ]
        """
        message = self.createMsgPackResult('send_tile')
        message.setResult('gang_tiles', player.copyGangArray())
        message.setResult('peng_tiles', player.copyPengArray())
        message.setResult('chi_tiles', player.copyChiArray())
        message.setResult('zhan_tiles', player.zhanTiles)

        # AI运算需要，这时已经把牌加到手牌中了，消息中挪出新增的牌
        handTiles = player.copyHandTiles()
        handTiles.remove(tile)
        ftlog.debug("add_card handTiles = ", handTiles)
        ftlog.debug("add_card tile = ", tile)
        zhanTiles = player.zhanTiles
        if zhanTiles and zhanTiles in handTiles:
            handTiles.remove(zhanTiles)
        message.setResult('standup_tiles', handTiles)

        message.setResult('timeout', timeOut)
        message.setResult('tile', tile)

        message.setResult('remained_count', self.tableTileMgr.getTilesLeftCount())
        message.setResult('seatId', seatId)
        message.setResult('trustee', 1 if player.autoDecide else 0)
        message.setResult('action_id', actionId)

        if changeInfo:
            message.setResult('exchange_action', changeInfo)
        gang = extendInfo.getChiPengGangResult(MTableState.TABLE_STATE_GANG)

        if gang:
            #             normalGang = []
            #             imlicitGang = []
            #             for tempGang in gang:
            #                 if not tempGang.has_key('style'):
            #                     continue
            #                 if tempGang['style'] == 1:
            #                     normalGang.append(tempGang)
            #                 elif tempGang['style'] == 0:
            #                     imlicitGang.append(tempGang)
            #             if len(normalGang) > 0:
            #                 message.setResult('gang_action', normalGang)
            #             if len(imlicitGang) > 0:
            # 摸牌一定不是吃杠
            message.setResult('implicit_gang_action', gang)
            pigus = extendInfo.getPigus(MTableState.TABLE_STATE_FANPIGU)
            if pigus:
                message.setResult('fanpigu_action', pigus)
            else:
                ftlog.debug('table_call_add_card gang_action not find pigus')
        else:
            message.setResult('implicit_gang_action', [])

        ting_action = extendInfo.getTingResult(self.tableTileMgr, seatId)
        if ting_action:
            tingliang_action = extendInfo.getTingLiangResult(self.tableTileMgr)
            if tingliang_action:
                message.setResult('tingliang_action', tingliang_action)
            message.setResult('ting_action', ting_action)
        wins = extendInfo.getChiPengGangResult(MTableState.TABLE_STATE_HU)
        if wins and len(wins) > 0:
            ftlog.debug('table_call_add_card wins: ', wins)
            message.setResult('win_tile', wins[0]['tile'])
            message.setResult('win_degree', 1)

        # 缓存消息    
        self.latestMsg[player.curSeatId] = message
        self.addUserStep(message, player.userId)
        send_msg(message, player.userId)
        self.addMsgRecord(message, player.userId)

    def table_call_add_card_broadcast(self, seatId, timeOut, actionId, userId, tile, changeInfo=None):
        """通知其他人给某个人发牌
        参数说明：
        seatId 发牌玩家的座位号
        {
            "cmd": "send_tile",
            "result": {
                "remained_count": 54,
                "seatId": 3,
                "gameId": 7,
                "timeout": 9
            }
        }
        """
        message = self.createMsgPackResult('send_tile')
        message.setResult('seatId', seatId)
        message.setResult('remained_count', self.tableTileMgr.getTilesLeftCount())
        message.setResult('timeout', timeOut)
        message.setResult('action_id', actionId)
        #         if changeInfo:
        #             message.setResult('exchange_action', changeInfo)
        #         if self.players[seatId].isTingLiang():
        #             # 亮牌时，输出当前用户抓到的牌，否则不要输出用户抓到的牌
        #             message.setResult('tile', tile)

        ftlog.debug('MMsgLongNet.table_call_add_card_broadcast broadcast add card msg to user:', userId, ' message:',
                    message)
        self.addUserStep(message, userId)
        send_msg(message, userId)

    def table_call_drop(self, seatId, player, tile, state, extendInfo, actionId, timeOut):
        """通知玩家出牌
        参数：
            seatId - 出牌玩家的ID
            player - 针对出牌做出牌操作的玩家
            tile - 本次出牌
            state - 通知玩家可以做出的选择
            extendInfo - 扩展信息
            actionId - 当前的操作ID
            
        eg:
        {'ting': {'chiTing': []}, 'chi': [[12, 13, 14]]}
        """
        ftlog.debug('table_call_drop longnet player drop tile = ', tile)
        message = self.createMsgPackResult('play')
        message.setResult('tile', tile)
        message.setResult('seatId', seatId)
        message.setResult('remained_count', self.tableTileMgr.getTilesLeftCount())
        hasAction = False
        isPlayerHu = (player.state == MPlayer.PLAYER_STATE_WON)
        ftlog.debug('table_call_drop longnet tile:', tile, 'seatId:', seatId, 'isPlayerHu', isPlayerHu, 'player.state',
                    player.state)
        # 吃
        if state & MTableState.TABLE_STATE_CHI and not isPlayerHu:
            hasAction = True
            patterns = extendInfo.getChiPengGangResult(MTableState.TABLE_STATE_CHI)
            message.setResult('chi_action', patterns)

        # 碰
        if state & MTableState.TABLE_STATE_PENG and not isPlayerHu:
            hasAction = True
            patterns = extendInfo.getChiPengGangResult(MTableState.TABLE_STATE_PENG)
            message.setResult('peng_action', patterns)

        # 杠
        if state & MTableState.TABLE_STATE_GANG and not isPlayerHu:
            hasAction = True
            pattern = extendInfo.getChiPengGangResult(MTableState.TABLE_STATE_GANG)
            message.setResult('gang_action', pattern)
            pigus = extendInfo.getPigus(MTableState.TABLE_STATE_FANPIGU)
            if pigus:
                message.setResult('fanpigu_action', pigus)
            else:
                ftlog.debug('table_call_drop gang_action not find pigus')

        # 听
        if state & MTableState.TABLE_STATE_GRABTING and not isPlayerHu:
            # "grabTing_action":{"chi_action":[2],"peng_action":27}
            hasAction = True
            grabTingAction = {}
            ces = extendInfo.getChiPengGangTingResult(MTableState.TABLE_STATE_CHI)
            if ces:
                grabTingAction['chi_action'] = ces

            pes = extendInfo.getChiPengGangTingResult(MTableState.TABLE_STATE_PENG)
            if pes:
                grabTingAction['peng_action'] = pes

            ges = extendInfo.getChiPengGangTingResult(MTableState.TABLE_STATE_GANG)
            if ges:
                grabTingAction['gang_action'] = ges

            ges = extendInfo.getChiPengGangTingResult(MTableState.TABLE_STATE_ZHAN)
            if ges:
                grabTingAction['zhan_action'] = ges
            message.setResult('grabTing_action', grabTingAction)

        # 和
        if state & MTableState.TABLE_STATE_HU and not isPlayerHu:
            hasAction = True
            message.setResult('win_degree', 1)
            message.setResult('win_action', 1)

        if hasAction:
            message.setResult('player_seat_id', player.curSeatId)
            message.setResult('timeout', timeOut)
            message.setResult('action_id', actionId)

        #         tingliang_action = {}
        #         if extendInfo and self.players[seatId].isTing():
        #             # 客户端听亮和听
        #             tingliang_action = extendInfo.getTingLiangResult(self.tableTileMgr)
        #             message.setResult('tingliang_action', tingliang_action)
        #         if self.players[seatId].isTing() and not tingliang_action:
        #             message.setResult('ting', 1)

        # 保存最新的消息
        if hasAction:
            self.latestMsg[player.curSeatId] = message
        self.addUserStep(message, player.userId)
        send_msg(message, player.userId)
        self.addMsgRecord(message, player.userId)

    def sendTableEvent(self, count, userId, seatId, broadcastTargets=[]):
        """发送table_event消息，实时更新牌桌人数"""
        msg = self.createMsgPackResult('table_event')
        msg.setResult('count', count)
        msg.setResult('players', self.getPlayersInMsg(seatId, False))
        self.addUserStep(msg, broadcastTargets)
        send_msg(msg, broadcastTargets)
        self.addMsgRecord(msg, broadcastTargets)

    def broadcastUserSit(self, seatId, userId, is_reconnect, is_host=False, broadcastTargets=[]):
        """广播用户坐下消息"""
        message = self.createMsgPackResult('sit')
        message.setResult('isTableHost', 1 if is_host else 0)
        message.setResult('seatId', seatId)
        message.setResult('userId', userId)
        message.setResult('ip', sessiondata.getClientIp(userId))
        message.setResult('name', self.players[seatId].name)
        message.setResult('pic', self.players[seatId].purl)
        message.setResult('sex', self.players[seatId].sex)
        message.setResult('state', self.players[seatId].state)
        #         message.setResult('score', 0)
        self.addUserStep(message, broadcastTargets)
        send_msg(message, broadcastTargets)
        self.addMsgRecord(message, broadcastTargets)

    def send_location_message(self, seatId, userId):
        '''
        通知用户的location
        {
            "cmd": "location",
            "result": {
                "gameId": 7,
                "maxSeatN": 4,
                "play_mode": "harbin",
                "players": [
                    {
                        "master_point_level_diff": [
                            26,
                            100
                        ],
                        "name": "MI 3C",
                        "pic": "http://ddz.image.tuyoo.com/avatar/head_coffee.png",
                        "userId": 10788,
                        "master_point": 126,
                        "sex": 0,
                        "week_master_point": 126,
                        "charm": 0,
                        "max_win_sequence_count": 12,
                        "win_sequence_count": 0,
                        "seatId": 0,
                        "coin": 0,
                        "master_point_level": 5,
                        "max_degree": 4,
                        "new_win_sequence_count": 0
                    }
                ],
                "tableId": 750410010200,
                "seatId": 0,
                "roomId": 75041001,
                "tableType": "create"
            }
        }
        
        TODO:
        补充master_point_level等信息
        '''
        message = self.createMsgPackResult('location')
        message.setResult('seatId', seatId)
        message.setResult('maxSeatN', self.playerCount)
        message.setResult('play_mode', self.playMode)
        message.setResult('tableType', self.tableType)

        players = self.getPlayersInMsg(seatId, False)
        message.setResult('players', players)
        self.addUserStep(message, userId)
        send_msg(message, userId)
        # 录入牌局记录
        self.addMsgRecord(message, userId)

    def getPlayersInMsg(self, mySeatId, isReconnect=False, hasHuData=None):
        players = []
        needRemove = False
        removeSeatId = -1
        removeOtherTile = 0
        hasRemoved = False
        for i in range(self.playerCount):
            if not self.players[i]:
                continue

            player = {}
            player['ip'] = sessiondata.getClientIp(self.players[i].userId)
            player['userId'] = self.players[i].userId;
            player['name'] = self.players[i].name;
            player['pic'] = self.players[i].purl;
            player['sex'] = self.players[i].sex;
            player['coin'] = self.players[i].coin
            player['seatId'] = i
            player['state'] = self.players[i].state
            player['ting'] = self.players[i].isTing()

            if isReconnect:
                ftlog.debug("getPlayersInMsg mySeatId:", mySeatId, "nowSeat:", i)
                player['trustee'] = self.players[i].autoDecide
                userHands = self.players[i].copyHandTiles()
                zhanTiles = self.players[i].zhanTiles
                if zhanTiles and zhanTiles in userHands:
                    userHands.remove(zhanTiles)
                player['standup_tiles'] = userHands
                player['add_tile'] = []
                # 如果胡了,add_tile一定是显示胡的牌
                if self.players[i].hasHu:
                    #                     huTiles = self.players[i].copyHuArray()
                    #                     if len(huTiles) > 0:
                    #                         player['add_tile'] = huTiles
                    if hasHuData:
                        playerData = hasHuData.get(i, {})
                        if playerData:
                            player['won_tiles'] = [playerData.get('winTile', 0)]
                            player['winMode'] = playerData.get('winMode', 1)
                if self.players[i].curTile and not self.players[i].hasHu:
                    player['add_tile'] = [self.players[i].curTile]
                if i != mySeatId:
                    #                     if self.players[i].isTingLiang():
                    #                         # 亮牌时，输出当前用户手牌
                    #                         player['tingLiang'] = True
                    #                     else:
                    # 未亮牌情况下，当前用户手牌保密
                    if not self.players[i].hasHu:
                        player['standup_tiles'] = [0 for _ in range(len(userHands))]
                        if len(player['add_tile']) > 0:
                            player['add_tile'] = [0]
                if len(player['add_tile']) > 0 and len(player['standup_tiles']) % 3 == 2:
                    for temp in player['add_tile']:
                        if temp in player['standup_tiles']:
                            player['standup_tiles'].remove(temp)
                player['gang_tiles'] = self.players[i].copyGangArray()
                player['peng_tiles'] = self.players[i].copyPengArray()
                player['chi_tiles'] = self.players[i].copyChiArray()
                player['ting_tiles'] = self.players[i].copyTingArray()
                player['drop_tiles'] = copy.deepcopy(self.tableTileMgr.menTiles[self.players[i].curSeatId])
                player['zhan_tiles'] = self.players[i].zhanTiles
                # 临时解决这个问题,手牌吃碰完除3余2,才给恢复杠牌按钮
                if self.playMode == MPlayMode.YUNNAN or self.playMode == MPlayMode.ZHAOTONG:
                    if len(player['standup_tiles']) % 3 == 2 and i == mySeatId:
                        gang = self.gangRuleMgr.hasGang(self.players[i].copyTiles(), 0, 0)
                        if gang:
                            player['implicit_gang_action'] = gang
                        pigus = self.tableTileMgr.getPigus()
                        if pigus:
                            player['fanpigu_action'] = pigus
                        if self.playMode == MPlayMode.ZHAOTONG:
                            magicTiles = self.tableTileMgr.getMagicTiles()
                            needExchange, exchangeInfo = self.players[i].canExchangeMagic(magicTiles)
                            if needExchange:
                                player['exchange_action'] = exchangeInfo
                message = self.latestMsg[self.players[i].curSeatId]
                if message and self.actionId == message.getResult('action_id',
                                                                  0) and message.getCmd() == 'send_tile' and message.getResult(
                        'seatId', -1) == mySeatId:
                    # 如果缓存的是自己的摸牌,add_tile就没有内容
                    player['add_tile'] = []
                #                     # 发送快照中的手牌
                #                     ftlog.debug("getPlayersInMsg sendCacheMsg seat:", mySeatId, "player['standup_tiles']:", player['standup_tiles'])
                #                     player['standup_tiles'] = message.getResult('standup_tiles', [])
                #                     if message.getResult('seatId', -1) != mySeatId:
                #                         lenth = len(player['standup_tiles'])
                #                         player['standup_tiles'] = [0 for _ range(lenth)]
                # 如果上一条缓存的是出牌消息, 需要在对应玩家的手牌里加一张0,如果是自己的牌则不用
                ftlog.debug("getPlayersInMsg message:", message, "self.actionId:", self.actionId)
                if not hasRemoved:
                    if message and self.actionId == message.getResult('action_id', 0) \
                            and message.getCmd() == 'play':
                        needRemove = True
                        hasRemoved = True
                        removeSeatId = message.getResult('seatId', -1)
                        removeOtherTile = message.getResult('tile', 0)
                    #                     player['standup_tiles'].append(0)
                    #                     if len(player['drop_tiles']) > 0:
                    #                         player['drop_tiles'].pop(-1)
            players.append(player)
        if needRemove:
            if mySeatId != removeSeatId:
                for player in players:
                    if player['seatId'] == removeSeatId:
                        player['standup_tiles'].append(0)
                        if removeOtherTile in player['drop_tiles']:
                            player['drop_tiles'].remove(removeOtherTile)
        return players

    def sendMsgInitTils(self, tiles, banker, userId, seatId):
        """发牌
        {
            "cmd": "init_tiles",
            "result": {
                "tiles": [
                    22,
                    24,
                    29,
                    8,
                    14,
                    3,
                    12,
                    12,
                    4,
                    23,
                    2,
                    19,
                    35
                ],
                "gameId": 7,
                "header_seat_id": 0
            }
        }
        """

        message = self.createMsgPackResult('init_tiles')
        message.setResult('tiles', tiles)
        message.setResult('header_seat_id', banker)
        message.setResult('seatId', seatId)
        self.addUserStep(message, userId)
        send_msg(message, userId)
        self.addMsgRecord(message, userId)

    def createMsgPackRequest(self, cmd, action=None):
        """消息里面的公共信息"""
        mp = MsgPack()
        mp.setCmd(cmd)
        if action:
            mp.setParam('action', action)
        mp.setParam('gameId', self.gameId)
        mp.setParam('roomId', self.roomId)
        mp.setParam('tableId', self.tableId)
        return mp

    def createMsgPackResult(self, cmd, action=None):
        """消息里面的公共信息"""
        mp = MsgPack()
        mp.setCmd(cmd)
        if action:
            mp.setResult('action', action)
        mp.setResult('gameId', self.gameId)
        mp.setResult('roomId', self.roomId)
        mp.setResult('tableId', self.tableId)
        return mp

    def getMsgDispatchRobot(self, playerCount):
        """获取加机器人的上行消息"""
        message = self.createMsgPackRequest('table_call', 'dispatch_virtual_player')
        message.setParam('player_count', playerCount)
        return message

    def getMsgReadyTimeOut(self):
        """自建桌的准备超时"""
        message = self.createMsgPackRequest('table_call', 'friend_table_ready_time_out')
        return message

    def table_call_latest_msg(self, seatId):
        """补发最新的消息"""
        message = self.latestMsg[seatId]
        if not message:
            return

        if self.actionId == message.getResult('action_id', 0):
            message.setResult('reconnect', True)
            self.addUserStep(message, self.players[seatId].userId)
            send_msg(message, self.players[seatId].userId)
        else:
            ftlog.debug('table_call_latest_msg actionId not match, no need to send latest msg ......self.actionId =',
                        self.actionId, "getActionId= ", message.getResult('action_id', 0))

    def table_call_table_info(self, userId, banker, seatId, isReconnect, quanMenFeng, curSeat, tableState,
                              customInfo=None):
        """
        table_info消息
        参数
        1）userId - 发送table_info的用户
        2）banker - 庄家
        3）isReconnect - 是否断线重连
        例子：
        {
            "cmd": "table_info",
            "result": {
                "room_level": "master",
                "maxSeatN": 4,
                "room_coefficient": 6,
                "userId": 10788,
                "header_seat_id": 0,
                "table_product": [
                    {
                        "name": "36\\u4e07\\u91d1\\u5e01",
                        "price": "30",
                        "tip": "36\\u4e07\\u91d1\\u5e01",
                        "buy_type": "direct",
                        "needChip": 0,
                        "addchip": 360000,
                        "picurl": "http://111.203.187.150:8040/hall/pdt/imgs/goods_t300k_2.png",
                        "price_diamond": "300",
                        "type": 1,
                        "id": "TY9999D0030001",
                        "desc": "1\\u5143=12000\\u91d1\\u5e01"
                    }
                ],
                "table_raffle": 1,
                "base_chip": 1200,
                "reconnect": false,
                "seatId": 0,
                "roomId": 75041001,
                "quan_men_feng": 11,
                "tableType": "create",
                "gameId": 7,
                "gameRule": "classic",
                "interactive_expression_config": {
                    "0": {
                        "charm": 120,
                        "cost": 1200,
                        "chip_limit": 1320,
                        "ta_charm": -120
                    },
                    "1": {
                        "charm": 240,
                        "cost": 1200,
                        "chip_limit": 1320,
                        "ta_charm": 240
                    },
                    "2": {
                        "charm": 60,
                        "cost": 600,
                        "chip_limit": 1320,
                        "ta_charm": -60
                    },
                    "3": {
                        "charm": 120,
                        "cost": 600,
                        "chip_limit": 1320,
                        "ta_charm": 120
                    }
                },
                "play_mode": "harbin",
                "taskUnreward": true,
                "room_name": "\\u5927\\u5e08\\u573a",
                "current_player_seat_id": 0,
                "good_tile_chance": 1.5,
                "service_fee": 800,
                "min_coin": 10000,
                "play_timeout": 9,
                "max_coin": -1,
                "table_state": "play",
                "players": [
                    {
                        "ip": "111.203.187.129",
                        "pic": "http://ddz.image.tuyoo.com/avatar/head_coffee.png",
                        "userId": 10788,
                        "sex": 0,
                        "week_master_point": 126,
                        "max_win_sequence_count": 12,
                        "win_sequence_count": 0,
                        "seatId": 0,
                        "master_point_level": 5,
                        "vipInfo": {
                            "vipExp": 0,
                            "vipLevel": {
                                "level": 0
                            }
                        },
                        "ting": 0,
                        "new_win_sequence_count": 0,
                        "max_degree": 4,
                        "member": {
                            "flag": 0
                        },
                        "rank_name": "\\u5168\\u56fd\\u96c0\\u795e\\u699c",
                        "rank_index": 2,
                        "master_point_level_diff": [
                            26,
                            100
                        ],
                        "stat": "playing",
                        "charm": 0,
                        "coin": 21004366,
                        "name": "MI 3C",
                        "master_point": 126
                    },
                    {
                        "stat": "playing",
                        "name": "\\u6211\\u662f\\u738b",
                        "ip": "192.168.10.76",
                        "pic": "http://ddz.image.tuyoo.com/avatar/head_male_1.png",
                        "userId": 1057,
                        "sex": 1,
                        "ting": 0,
                        "seatId": 1,
                        "coin": 703440,
                        "vipInfo": {
                            "vipExp": 0,
                            "vipLevel": {
                                "level": 0
                            }
                        }
                    },
                    {
                        "stat": "playing",
                        "name": "\\u53c1\\u5343\\u5757\\u4e0a\\u4f60",
                        "ip": "192.168.10.76",
                        "pic": "http://ddz.image.tuyoo.com/avatar/head_lotus.png",
                        "userId": 1145,
                        "sex": 1,
                        "ting": 0,
                        "seatId": 2,
                        "coin": 811200,
                        "vipInfo": {
                            "vipExp": 0,
                            "vipLevel": {
                                "level": 0
                            }
                        }
                    },
                    {
                        "stat": "playing",
                        "name": "\\u5c0fEVA",
                        "ip": "192.168.10.76",
                        "pic": "http://ddz.image.tuyoo.com/avatar/head_feimao.png",
                        "userId": 1107,
                        "sex": 0,
                        "ting": 0,
                        "seatId": 3,
                        "coin": 637250,
                        "vipInfo": {
                            "vipExp": 0,
                            "vipLevel": {
                                "level": 0
                            }
                        }
                    }
                ],
                "tableId": 750410010200,
                "big_degree_fee": [
                    30,
                    0.1,
                    200
                ]
            }
        }
        """
        ftlog.debug('MMsgLongNet.table_call_table_info actionId:', self.actionId)
        message = self.createMsgPackResult('table_info')
        message.setResult('action_id', self.actionId)
        message.setResult('maxSeatN', self.playerCount)
        message.setResult('header_seat_id', banker)
        message.setResult('room_level', self.roomConf.get('level', ''))
        message.setResult('room_coefficient', self.tableConf.get('room_coefficient', 1))
        message.setResult('base_chip', self.tableConf.get('base_chip', 0))
        message.setResult('reconnect', isReconnect)
        message.setResult('seatId', seatId)
        message.setResult('quan_men_feng', quanMenFeng)
        message.setResult('tableType', self.tableType)
        message.setResult('gameRule', self.roomConf.get('gameRule', ''))
        message.setResult('play_mode', self.playMode)
        message.setResult('room_name', self.roomConf.get('name', ''))
        message.setResult('current_player_seat_id', curSeat)
        message.setResult('min_coin', self.roomConf.get('minCoin', 0))
        message.setResult('play_timeout', 9)
        message.setResult('max_coin', self.roomConf.get("maxCoin", 0))
        message.setResult('table_state', tableState)
        message.setResult('big_degree_fee', self.tableConf.get('big_degree_fee', []))
        message.setResult('remained_count', self.tableTileMgr.getTilesLeftCount())

        pigus = self.tableTileMgr.getPigus()
        if pigus:
            message.setResult('pigus', pigus)

        if customInfo:
            message.setResult('create_table_extend_info', customInfo.get('ctInfo', {}))
        if customInfo.has_key('btInfo'):
            btInfo = customInfo.get('btInfo', {})
            if self.playMode == MPlayMode.HAERBIN:
                message.setResult('baopai', btInfo)
            elif self.playMode == MPlayMode.YUNNAN:
                message.setResult('laizi', btInfo)
            elif self.playMode == MPlayMode.ZHAOTONG:
                if isReconnect:
                    message.setResult('laizi', btInfo)
        hasHuData = customInfo.get('hasHuData', {})
        players = self.getPlayersInMsg(seatId, isReconnect, hasHuData)
        message.setResult('players', players)
        ftlog.debug('MMsgLongNet.table_call_table_info: ', message)

        if TYPlayer.isHuman(userId):
            message.setResult('userId', userId)
            self.addUserStep(message, userId)
            send_msg(message, userId)
            if not isReconnect:
                self.addMsgRecord(message, userId)
        else:
            return

    def table_call_after_chi(self, lastSeatId, seatId, tile, pattern, timeOut, actionId, player, actionInfo=None):
        """吃/碰后的广播
        1）吃
        {
            "cmd": "chi",
            "result": {
                "tile": 22,
                "pattern": [22, 23, 24],
                "seatId": 1,
                "player_seat_id": 0,
                "timeout": 12,
                "action_id": 17,
                "gameId": 7
            }
        }
        """
        ftlog.debug('MsgLongnet.table_call_after_chi seatId', seatId)
        message = self.createMsgPackResult('chi')
        message.setResult('tile', tile)
        message.setResult('pattern', pattern)
        message.setResult('seatId', seatId)
        message.setResult('player_seat_id', lastSeatId)
        message.setResult('timeout', timeOut)
        message.setResult('action_id', actionId)
        if (player.curSeatId == seatId):
            if actionInfo.has_key('ting_action'):
                ting_action = actionInfo.get('ting_action', None)
                if ting_action:
                    message.setResult('grabTing', ting_action)
            if actionInfo.has_key('gang_action'):
                gang_action = actionInfo.get('gang_action', None)
                # 吃碰以后一定不是吃杠
                if gang_action:
                    message.setResult('implicit_gang_action', gang_action)
                fanpigu_action = actionInfo.get('fanpigu_action', None)
                if fanpigu_action:
                    message.setResult('fanpigu_action', fanpigu_action)
            else:
                message.setResult('implicit_gang_action', [])
        ftlog.debug('table_call_after_chi message:', message)
        self.addUserStep(message, player.userId)
        send_msg(message, player.userId)
        self.addMsgRecord(message, player.userId)

    def table_call_after_peng(self, lastSeatId, seatId, tile, timeOut, actionId, player, pattern, actionInfo=None,
                              exInfo=None):
        """吃/碰后的广播
        1）碰
        {
            "cmd": "peng",
            "result": {
                "tile": 19,
                "seatId": 1,
                "player_seat_id": 0,
                "timeout": 12,
                "action_id": 12,
                "gameId": 7
            }
        }
        """
        ftlog.debug('MsgLongnet.table_call_after_peng')
        message = self.createMsgPackResult('peng')
        message.setResult('tile', tile)
        message.setResult('seatId', seatId)
        message.setResult('player_seat_id', lastSeatId)
        message.setResult('timeout', timeOut)
        message.setResult('action_id', actionId)
        if pattern is None:
            pattern = [tile, tile, tile]
        message.setResult('pattern', pattern)
        if (player.curSeatId == seatId):
            if actionInfo.has_key('ting_action'):
                ting_action = actionInfo.get('ting_action', None)
                if ting_action and exInfo:
                    # 获取是否亮牌
                    tingliang_action = exInfo.getTingLiangResult(self.tableTileMgr)
                if ting_action and tingliang_action and tingliang_action['mode']:
                    message.setResult('tingliang_action', tingliang_action)
                elif ting_action:
                    message.setResult('grabTing', ting_action)
            if actionInfo.has_key('gang_action'):
                gang_action = actionInfo.get('gang_action', None)
                if gang_action:
                    # 吃碰以后一定不是吃杠
                    message.setResult('implicit_gang_action', gang_action)
                fanpigu_action = actionInfo.get('fanpigu_action', None)
                if fanpigu_action:
                    message.setResult('fanpigu_action', fanpigu_action)
            else:
                message.setResult('implicit_gang_action', [])
            #             magicTiles = self.tableTileMgr.getMagicTiles()
            #             needExchange, exchangeInfo = player.canExchangeMagic(magicTiles)
            #             if needExchange:
            #                 message.setResult('exchange_action', exchangeInfo)
        self.addUserStep(message, player.userId)
        send_msg(message, player.userId)
        self.addMsgRecord(message, player.userId)

    def table_call_after_gang(self, lastSeatId, seatId, tile, loser_seat_ids, actionId, player, gang, exInfo=None):
        """杠牌广播消息
        {
            "cmd": "gang",
            "result": {
                "tile": 21,
                "pattern": [21, 21, 21, 21]
                "seatId": 3,
                "player_seat_id": 0,
                "loser_seat_ids": [
                    0
                ],
                "gameId": 7
            }
        }
        """
        message = self.createMsgPackResult('gang')
        message.setResult('tile', tile)
        message.setResult('gang', gang)
        message.setResult('seatId', seatId)
        message.setResult('player_seat_id', lastSeatId)
        message.setResult('action_id', actionId)
        message.setResult('loser_seat_ids', loser_seat_ids)
        isPlayerHu = (player.state == MPlayer.PLAYER_STATE_WON)
        if exInfo and not isPlayerHu:
            choose = exInfo.getChoosedInfo(MTableState.TABLE_STATE_QIANGGANG)
            message.setResult("win_tile", choose['tile'])
            message.setResult('win_degree', 1)
        self.addUserStep(message, player.userId)
        send_msg(message, player.userId)
        if exInfo:
            # 抢杠和消息缓存
            self.latestMsg[player.curSeatId] = message
        self.addMsgRecord(message, player.userId)

    def table_call_after_zhan(self, lastSeatId, seatId, tile, timeOut, actionId, player, pattern, actionInfo=None):
        """粘牌广播消息
        {
            "cmd": "zhan",
            "result": {
                "tile": 21,
                "pattern": [21, 21]
                "seatId": 3,
                "player_seat_id": 0,
                "gameId": 7
            }
        }
        """
        ftlog.debug('MsgLongnet.table_call_after_peng')
        message = self.createMsgPackResult('zhan')
        message.setResult('tile', tile)
        message.setResult('seatId', seatId)
        message.setResult('player_seat_id', lastSeatId)
        message.setResult('timeout', timeOut)
        message.setResult('action_id', actionId)
        if pattern is None:
            pattern = [tile, tile]
        message.setResult('pattern', pattern)
        if (player.curSeatId == seatId):
            if actionInfo.has_key('ting_action'):
                ting_action = actionInfo.get('ting_action', None)
                if ting_action:
                    message.setResult('grabTing', ting_action)
        self.addUserStep(message, player.userId)
        send_msg(message, player.userId)
        self.addMsgRecord(message, player.userId)

    def table_call_after_ting(self, player, actionId, userId, allWinTiles):
        """听牌消息"""
        message = self.createMsgPackResult('ting')
        message.setResult('gang_tiles', player.copyGangArray())
        message.setResult('peng_tiles', player.copyPengArray())
        message.setResult('chi_tiles', player.copyChiArray())
        # 兼容其他客户端standup_tiles，all_win_tiles，不亮牌的情况下都传空
        message.setResult('standup_tiles', player.tingLiangTiles)
        message.setResult('all_win_tiles', allWinTiles)
        message.setResult('seatId', player.curSeatId)
        self.addUserStep(message, userId)
        send_msg(message, userId)
        self.addMsgRecord(message, userId)

    def table_call_game_win_loose(self
                                  , uids
                                  , wins
                                  , looses
                                  , observers
                                  , winMode
                                  , tile
                                  , totalScore
                                  , deltaScore
                                  , scoreBase
                                  , fanPattern
                                  , customInfo=None
                                  ):
        """
        结算
        -1 点炮
        -2 不输不赢
        
        score - 当前积分
        total_score - 目前为止总的输赢积分
        delta_score - 当前局的输赢积分
        customInfo 包含之前的ctInfo btInfo lstInfo
        """
        gameFlow = 0
        if customInfo:
            if customInfo.get('gameFlow', 0) == 1:
                gameFlow = 1
        for winPlayer in wins:
            self.table_call_game_win(self.players[winPlayer]
                                     , winMode[winPlayer]
                                     , tile
                                     , uids
                                     , totalScore[winPlayer]
                                     , deltaScore[winPlayer]
                                     , scoreBase
                                     , fanPattern[winPlayer]
                                     , gameFlow
                                     , customInfo)

        for loosePlayer in looses:
            self.table_call_game_loose(self.players[loosePlayer]
                                       , winMode[loosePlayer]
                                       , uids
                                       , totalScore[loosePlayer]
                                       , deltaScore[loosePlayer]
                                       , scoreBase
                                       , fanPattern[loosePlayer]
                                       , gameFlow
                                       , customInfo)

        for ob in observers:
            self.table_call_game_loose(self.players[ob]
                                       , winMode[ob]
                                       , uids
                                       , totalScore[ob]
                                       , deltaScore[ob]
                                       , scoreBase
                                       , fanPattern[ob]
                                       , gameFlow
                                       , customInfo)

    def table_call_game_win(self, winPlayer, winMode, tile, uids, totalScore, deltaScore, scoreBase, fanPatternInfo,
                            gameFlow, customInfo):
        """
        注：给赢家发送和牌消息
        
        params：
        1）winType：0是自摸和，1是放炮和
        
        例子：
        {
        "cmd": "win",
        "result": {
            "gameId": 710,
            "roomId": 7105021001,
            "tableId": 71050210010199,
            "seatId": 2,
            "userId": 9597,
            "timestamp": 1479255694,
     
            //分数相关， 总分，这把的分变化，目前为止的分数变化
            "score": 4,
            "delta_score": 5,
            "total_delta_score": 5,
     
            //当前座位的玩家，宝牌信息[牌花，牌数]
            "baopai":[{
                "tile":1
            }],
            //结算界面不需要看，遗弃过的宝牌
             
            //胡牌的模式，cmd>=0 为自己胡
            "winMode": 1,
     
            //当前这把，是否是流局
            "gameFlow": 0,
            //番型 是个 二维数组 [番型名称，番数]
            "patternInfo": [],
            //自建桌信息 是个 对象
            create_table_extend_info : {
                //房间号
                "create_table_no":123456,
                //游戏时长
                "time":123123,
                //是否最后一把
                "create_final":0,
                //当前剩余房卡
                "create_now_cardcount":2,
                //起始时，使用房卡
                "create_total_cardcount":5
            },
            
            //牌面信息
            "tilesInfo": {
                "tiles": [
                    5,
                    5,
                    6,
                    6,
                    6,
                    22,
                    23,
                    18
                ],
                "chi": [
                    [
                        24,
                        25,
                        26
                    ]
                ],
                "peng": [],
                "gang": [
                    {
                        "pattern": [
                            5,
                            5,
                            5,
                            5
                        ],
                        "style": 0
                    }
                ],
                "tile": 18
            }
        }

        """
        message = self.createMsgPackResult('win')
        message.setResult('score', scoreBase + totalScore)
        message.setResult('total_delta_score', totalScore)
        message.setResult('delta_score', deltaScore)
        message.setResult('seatId', winPlayer.curSeatId)  # 赢家座位号
        message.setResult('userId', winPlayer.userId)  # 赢家userId
        message.setResult('tile', tile)  # 和牌的牌
        message.setResult('timestamp', pktimestamp.getCurrentTimestamp())  # 和牌时间戳
        # message.setResult('balance', 20000) #赢家金币总额
        # message.setResult('totalCharges', 1000) #该局赢家总钱数(赢了也可能输钱哦)
        message.setResult('gameFlow', gameFlow)  # 是否流局(1 流局, 0 不流局)
        # message.setResult('score',  4) #番数, 输了不需要番数
        message.setResult('winMode', winMode)  # 该局赢的类型，0是自摸，1是放炮 -1输了
        if customInfo.has_key('ctInfo'):
            ctInfo = customInfo.get('ctInfo', None)
            if ctInfo:
                message.setResult('create_table_extend_info', ctInfo)
        if customInfo.has_key('btInfo'):
            btInfo = customInfo.get('btInfo', None)
            if btInfo:
                message.setResult('baopai', btInfo)
        if customInfo.has_key('lstInfo'):
            lstInfo = customInfo.get('lstInfo', None)
            if lstInfo:
                message.setResult('lastSpeicalTilesInfo', lstInfo)
        if customInfo.has_key('awardInfo'):
            awardInfo = customInfo.get('awardInfo', None)
            if awardInfo:
                message.setResult('awardInfo', awardInfo)
        winTiles = []
        if customInfo.has_key('winFinal'):
            winFinal = customInfo.get('winFinal', True)
            message.setResult('final', winFinal)
            if winFinal == True:
                if customInfo.has_key('winTiles'):
                    winTiles = customInfo.get('winTiles', [])
                    # 结算分数发在detail里面
        detailData = {
            "delta_score": deltaScore,
            "total_delta_score": totalScore,
            "score": scoreBase + totalScore,
            "patterns": fanPatternInfo
        }
        message.setResult('detail', detailData)

        # 如果是曲靖的十风或者十三幺等特殊牌型,胡牌牌面显示打出的牌
        winHandTiles = winPlayer.copyHandTiles()
        if customInfo.has_key('dropTiles'):
            dropTiles = customInfo.get('dropTiles', None)
            if dropTiles:
                winHandTiles = dropTiles

        if len(winTiles) > winPlayer.curSeatId:
            tile = winTiles[winPlayer.curSeatId]
        # 手牌信息
        tilesInfo = {
            "tiles": winHandTiles,  # [1,2,3,4,5]
            "gang": winPlayer.copyGangArray(),  # [[1,1,1,1],[9,9,9,9]] 明1&暗杠0, 花色
            "chi": winPlayer.copyChiArray(),  # [[2,3,4]]代表吃(1,2,3),(5,6,7)
            "peng": winPlayer.copyPengArray(),  # [1,2]代表吃(1,1,1),(2,2,2)
            "tile": tile,  # 7 胡七万
            "zhan": winPlayer.zhanTiles
            # "win_tiles": winPlayer.copyHuArray()
        }
        message.setResult('tilesInfo', tilesInfo)
        # 番数信息 patternInfo = [ ["连六", "1番"], ["连六", "1番"] ]
        # message.setResult('patternInfo', fanPatternInfo) #流局没有番型数据, 输了不需要番型数据
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    def table_call_game_loose(self, loosePlayer, winMode, uids, totalScore, deltaScore, scoreBase, fanPattern, gameFlow,
                              customInfo):
        """失败消息
        {
            "cmd": "lose",
            "result": {
                "userId": 1008,
                "seatId": 1,
                "timestamp": 1473782986.013167,
                "gameFlow": true,
                "balance": 937780,
                "totalCharges": -27000,
                "continuous": 0,
                "score": 0,
                "masterPoint": 0,
                "basePoint": 0,
                "roomPoint": 0,
                "memberPoint": 0,
                "winMode": -1,
                "final": true,
                "tilesInfo": {
                    "tiles": [
                        5,
                        5,
                        22,
                        22,
                        22,
                        26,
                        26,
                        27,
                        28,
                        28
                    ],
                    "kong": [],
                    "chow": [
                        15
                    ],
                    "pong": [],
                    "tile": null
                },
                "patternInfo": [],
                "loserInfo": [],
                "gameId": 7
            }
        }
        """
        message = self.createMsgPackResult('lose')
        message.setResult('score', scoreBase + totalScore)
        message.setResult('total_delta_score', totalScore)
        message.setResult('delta_score', deltaScore)
        message.setResult('userId', loosePlayer.userId)
        message.setResult('seatId', loosePlayer.curSeatId)
        message.setResult('timestamp', pktimestamp.getCurrentTimestamp())
        message.setResult('gameFlow', gameFlow)  # 是否流局(1 流局, 0 不流局)
        message.setResult('winMode', winMode)

        # 曲靖结算分数发在detail里面
        detailData = {
            "delta_score": deltaScore,
            "total_delta_score": totalScore,
            "score": scoreBase + totalScore,
            "patterns": fanPattern
        }
        if gameFlow == 1:
            # 流局才处理isPigs
            if customInfo.has_key('pigs'):
                pigs = customInfo.get('pigs', None)
                if loosePlayer.curSeatId in pigs:
                    detailData['isPig'] = 1
                else:
                    detailData['isPig'] = 0
        message.setResult('detail', detailData)

        # message.setResult('patternInfo', fanPattern)

        if customInfo.has_key('ctInfo'):
            ctInfo = customInfo.get('ctInfo', None)
            if ctInfo:
                message.setResult('create_table_extend_info', ctInfo)
        if customInfo.has_key('btInfo'):
            btInfo = customInfo.get('btInfo', None)
            if btInfo:
                message.setResult('baopai', btInfo)
        if customInfo.has_key('lstInfo'):
            lstInfo = customInfo.get('lstInfo', None)
            if lstInfo:
                message.setResult('lastSpeicalTilesInfo', lstInfo)
        if customInfo.has_key('awardInfo'):
            awardInfo = customInfo.get('awardInfo', None)
            if awardInfo:
                message.setResult('awardInfo', awardInfo)
        loseFinal = True
        if customInfo.has_key('loseFinal'):
            loseFinal = customInfo.get('loseFinal', True)
            message.setResult('final', loseFinal)

        # 根据
        tilesInfo = {}
        if loseFinal:
            tilesInfo = {
                "tiles": loosePlayer.copyHandTiles(),
                "gang": loosePlayer.copyGangArray(),
                "chi": loosePlayer.copyChiArray(),
                "peng": loosePlayer.copyPengArray(),
                "zhan": loosePlayer.zhanTiles
                # "win_tiles": loosePlayer.copyHuArray()
            }
        else:
            tilesInfo = {
                "tiles": [0 for _ in range(len(loosePlayer.copyHandTiles()))],
                "gang": loosePlayer.copyGangArray(),
                "chi": loosePlayer.copyChiArray(),
                "peng": loosePlayer.copyPengArray(),
                "zhan": 0}

        message.setResult('tilesInfo', tilesInfo)
        uids = []
        for player in self.players:
            uids.append(player.userId)
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    def table_call_game_all_stat(self, terminate, extendBudgets, ctInfo):
        """
        {
        "cmd":"gaming_leave_display_budget",
        "result":
        {
            "create_table_extend_info":
            {
                "create_final":1,
                "create_table_no":"000936",
                "create_now_cardcount":1,
                "create_total_cardcount":2,
                "time":1478278335
            },
            "roomId":78131001,
            "terminate":0 
            "detail":
            [
                {
                    "sid":1,
                    "total_delta_score":-2,
                    "statistics":[
                        {"desc":"自摸","value":0},
                        {"desc":"点炮","value":1},
                        {"desc":"明杠","value":0},
                        {"desc":"暗杠","value":0}
                        {"desc":"最大番数","value":2}
                    ],
                    "head_mark":"dianpao_most"
                },
                {
                    "sid":0,
                    "total_delta_score":2,
                    "statistics":[
                        {"desc":"自摸","value":0},
                        {"desc":"点炮","value":0},
                        {"desc":"明杠","value":0},
                        {"desc":"暗杠","value":0},
                        {"desc":"最大番数","value":2}
                    ],"head_mark":""
                }
            ],
            "gameId":7
        }
        }
            
        """
        message = self.createMsgPackResult('gaming_leave_display_budget')
        message.setResult('create_table_extend_info', ctInfo)
        message.setResult('terminate', terminate)
        message.setResult('detail', extendBudgets)

        uids = []
        for player in self.players:
            uids.append(player.userId)
        ftlog.debug(message)
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    def table_leave(self, userId, seatId, uids):
        message = self.createMsgPackResult('leave')
        message.setResult('seatId', seatId)
        message.setResult('userId', userId)
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    def table_call_baopai(self, player, baopai, abandones):
        """通知宝牌
        
        实例：
        {
            "cmd": "baopai",
            "result": {
                "gameId": 7,
                "userId": 10788,
                "tableId": 750410010200,
                "seatId": 0,
                "roomId": 75041001,
                "baopai": [
                    [
                        9,    花色
                        2,    倍数
                        3     剩余张数
                    ]
                ]
            }
        }
        """
        message = self.createMsgPackResult('baopai')
        message.setResult('userId', player.userId)
        message.setResult('seatId', player.curSeatId)
        if baopai:
            message.setResult('baopai', baopai)
        if abandones:
            message.setResult('abandoned', abandones)

        ftlog.debug(message)
        self.addUserStep(message, player.userId)
        send_msg(message, player.userId)
        self.addMsgRecord(message, player.userId)

    def table_chat_broadcast(self, uid, gameId, voiceIdx, msg, users):
        """广播聊天"""
        mo = self.createMsgPackResult('table_chat')
        mo.setResult('userId', uid)
        mo.setResult('gameId', gameId)
        mo.setResult('isFace', 0)
        if voiceIdx != -1:
            mo.setResult('voiceIdx', voiceIdx)
        mo.setResult('msg', msg)
        router.sendToUsers(mo, users)

    def table_chat_to_face(self, uid, gameId, voiceIdx, msg, player):
        """定向发消息"""
        mo = self.createMsgPackResult('table_chat')
        mo.setResult('userId', uid)
        mo.setResult('gameId', gameId)
        mo.setResult('isFace', 1)
        if voiceIdx != -1:
            mo.setResult('voiceIdx', voiceIdx)
        mo.setResult('msg', msg)
        mo.setResult('userName', player.name)
        router.sendToUser(mo, player.userId)

    def create_table_succ_response(self, userId, seatId, action, tableHost, uids):
        """
        {
            "cmd": "create_table",
            "result": {
                "isTableHost": 1,
                "action": "ready",
                "seatId": 0,
                "gameId": 7
            }
        }
        """
        message = self.createMsgPackResult('create_table', action)
        message.setResult('isTableHost', tableHost)
        message.setResult('seatId', seatId)
        message.setResult('userId', userId)
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    def create_table_dissolve(self, userId, seatId, state, uids):
        """
        {
            "cmd": "create_table",
            "result": {
                "action": "leave",
                "seatId": 0,
                "state": "win",
                "gameId": 7
            }
        }
        """
        message = self.createMsgPackResult('create_table', 'leave')
        message.setResult('seatId', seatId)
        message.setResult('state', state)
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    def create_table_dissolve_vote(self, userId, seatId, seatNum, vote_info, vote_detail, vote_name, vote_timeOut,
                                   uids):
        message = self.createMsgPackResult('create_table_dissolution')
        message.setResult('seatId', seatId)
        message.setResult('userId', userId)
        message.setResult('seatNum', seatNum)
        message.setResult('vote_info', vote_info)
        message.setResult('vote_info_detail', vote_detail)
        message.setResult('name', vote_name)
        message.setResult('vote_cd', vote_timeOut)
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    # 兼容客户端投票窗口关闭的协议，之后要优化合并 add by taoxc
    def create_table_dissolve_close_vote(self, userId, seatId):
        message = self.createMsgPackResult('user_leave_vote')
        message.setResult('seatId', seatId)
        message.setResult('userId', userId)
        message.setResult('vote_info_detail', [])
        message.setResult('close_vote_cd', 2)
        message.setResult('close_vote', 1)
        self.addUserStep(message, userId)
        send_msg(message, userId)
        self.addMsgRecord(message, userId)

    def table_call_fanpigu(self, pigus, uids):
        """发送翻屁股消息"""
        message = self.createMsgPackResult('fanpigu')
        message.setResult('pigus', pigus)
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    def table_call_QGH_wait(self, userId, implicitFlag=False):
        """发送翻屁股消息"""
        message = self.createMsgPackResult('qianggang_wait')
        if implicitFlag:
            message.setResult('implicit_gang_action', [])
            message.setResult('exchange_action', [])
        self.addUserStep(message, userId)
        send_msg(message, userId)
        self.addMsgRecord(message, userId)

    def table_call_exchange(self, seatId, tile, exchangedInfo, exchangInfo, extendInfo, userId, actionId):
        """换牌消息,发给要换牌的人"""
        message = self.createMsgPackResult('exchange')
        message.setResult('seatId', seatId)
        message.setResult('actionId', actionId)
        message.setResult('tile', tile)
        message.setResult('new_tile', exchangedInfo['newTile'])
        message.setResult('exchanged_action', exchangedInfo)
        message.setResult('exchange_action', exchangInfo)
        gang = extendInfo.getChiPengGangResult(MTableState.TABLE_STATE_GANG)
        if gang:
            message.setResult('implicit_gang_action', gang)
        else:
            message.setResult('implicit_gang_action', [])
        wins = extendInfo.getChiPengGangResult(MTableState.TABLE_STATE_HU)
        if wins and len(wins) > 0:
            ftlog.debug('table_call_exchange wins: ', wins)
            message.setResult('win_tile', wins[0]['tile'])
            message.setResult('win_degree', 1)
        self.addUserStep(message, userId)
        send_msg(message, userId)
        self.addMsgRecord(message, userId)

    def table_call_exchange_broadcast(self, seatId, tile, exchangedInfo, uids, actionId):
        """换牌消息广播,发给桌上其他人"""
        message = self.createMsgPackResult('exchange')
        message.setResult('seatId', seatId)
        message.setResult('actionId', actionId)
        message.setResult('tile', tile)
        message.setResult('exchanged_action', exchangedInfo)
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    def table_call_score(self, uids, score, delta):
        """牌桌积分变化"""
        message = self.createMsgPackResult('score')
        message.setResult('score', score)
        message.setResult('delta', delta)
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    def table_call_laizi(self, uids, magicTiles=[], magicFactors=[]):
        """向所有人发送赖子"""
        message = self.createMsgPackResult('show_laizi_tiles')
        message.setResult('dice_points', [])
        if magicTiles:
            message.setResult('table_laizi_tiles', magicTiles)
        if magicFactors:
            message.setResult('table_laizi_factors', magicFactors)
        self.addUserStep(message, uids)
        send_msg(message, uids)
        self.addMsgRecord(message, uids)

    def table_call_online_state(self, uids, onlineInfo):
        """下发玩家在线状态"""
        """{"cmd":"user_online_info",
                "result":{"roomId":7200041001
                            ,"gameId":720
                            ,"tableId":72000410010200
                            ,"online_info":[{"seatId":0
                                            ,"online":1
                                            },
                                            {"seatId":1
                                            ,"online":0
                                            },
                                            ]
                        }
            };
        online字段1为在线,0为离线
        """
        message = self.createMsgPackResult('user_online_info')
        message.setResult('online_info', onlineInfo)
        send_msg(message, uids)

    def table_call_ping(self, userId, pingInfo, timeStamp):
        """下发玩家网络状况
             {"cmd":"ping",
                "result":{"roomId":7200041001
                            ,"gameId":720
                            ,"tableId":72000410010200
                            ,"net_state":[-1,100,20,-1]  －1为不存在,100,20为延迟差
                                    }
                        }
            };
        """
        message = self.createMsgPackResult("table_call")
        message.setResult('action', 'ping')
        message.setResult('time', timeStamp)
        message.setResult('net_state', pingInfo)
        send_msg(message, userId)

    def quick_start_err(self, userId):
        messsage = self.createMsgPackResult('quick_start')
        messsage.setError(1, '对不起,该房间已满员')
        send_msg(messsage, userId)

    def saveRecord(self, recordName, urls):
        """
        保存牌局记录
        """
        trConfig = majiang_conf.getTableRecordConfig()
        uploadKey = trConfig.get('trUploadKey', '')
        uploadUrls = trConfig.get('trUploadUrls', [])
        if len(uploadUrls) == 0:
            return

        uploadUrl = random.choice(uploadUrls)
        uploadPath = trConfig.get('trFilePath', 'cdn37/tablerecord/')
        gamePath = self.playMode + '/'
        uploadPath = uploadPath + gamePath
        cdn = trConfig.get('trDownloadPath', 'http://df.dl.shediao.com/')
        recordString = json.dumps(self.msgRecords)
        cdn = cdn + uploadPath + recordName
        saveUrl = uploadUrl + uploadPath + recordName
        urls.append(cdn)
        self.reset()

        def runUpload():
            ec, info = uploader.uploadVideo(uploadUrl, uploadKey, uploadPath + recordName, recordString)
            ftlog.debug('runupload ec=', ec, 'info=', info)
            if ec == 0:
                ftlog.info('Majiang2.saveRecord ok, recordName:', recordName, ' CDNPath:', cdn)
            else:
                ftlog.error('Majiang2.saveRecord error, code:', ec, ' info:', info)

        argd = {'handler': runUpload}
        FTTasklet.create([], argd)

    def addUserStep(self, msg, uidList):
        """在给客户端关于牌桌逻辑的消息里加入user_step字段"""
        if not isinstance(uidList, list):
            uidList = [uidList]
        for uid in uidList:
            self.addPlayerStepByUserId(uid)
        msg.setResult("user_step", self.playerSteps)


def send_msg(msg, uidList):
    '''向客户端发消息'''
    if not isinstance(uidList, list):
        uidList = [uidList]
    newList = []
    for uid in uidList:
        if TYPlayer.isHuman(uid):
            newList.append(uid)

    router.sendToUsers(msg, uidList)
