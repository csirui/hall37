# -*- coding=utf-8
'''
Created on 2017年3月2日

@author: nick.kai.lee
'''
import poker.util.timestamp as pktimestamp
from difang.majiang2.msg_handler.msg_longnet import MMsgLongNet
from difang.majiang2.player.player import MPlayer
from difang.majiang2.table_state.state import MTableState
from freetime.entity.msg import MsgPack
from poker.protocol import router


def send_msg_only(msg, targets, seat_id):
    '''
    targets中仅仅向seat_id玩家发送消息
    @param targets 玩家players对象
    @param seat_id 发送消息的玩家的座位号
    '''
    router.sendToUsers(msg, [targets[seat_id].userId])


def send_msg_except(msg, targets, seat_id=-1):
    '''
    向其他玩家广播"当前玩家"的消息
    @param targets 玩家players对象
    @param seat_id 当前玩家的座位号
    '''
    others = []
    for i in range(0, len(targets)):
        if i != seat_id and targets[i]:
            others.append(targets[i].userId)
    router.sendToUsers(msg, others)


class HYMsgLongNet(MMsgLongNet):
    def __init__(self):
        super(HYMsgLongNet, self).__init__()

    def __init_basic_msg(self, cmd, action=None):
        """
        初始化消息基础 (private api)
        @param cmd: 协议command
        @param action: 协议子command名

        {cmd:"command", result:{ action:"sub command"}}
        """
        mp = MsgPack()
        mp.setCmd(cmd)
        if action:
            mp.setResult('action', action)
        mp.setResult('gameId', self.gameId)
        mp.setResult('roomId', self.roomId)
        mp.setResult('tableId', self.tableId)
        return mp

    def table_call_table_info(self, targets, seat_id, banker_seat_id, seats_count, player_info, play_mode,
                              remained_count, action_id, is_reconnect, extend_info):
        """
        拉玩家入桌 (public api)
        参数说明：
        @param targets, 协议发送的目标玩家对象players
        @param seat_id, 给谁(seat_id)发 start from 0
        @param banker_seat_id 庄家座位号
        @param seats_count 牌桌max人数
        @param player_info 玩家信息
        @param play_mode, 玩法,eg:"hengyang"
        @param remained_count, 剩余牌张数
        @param action_id
        @param is_reconnect, boolean 是否断线重连
        @param extend_info, 自建桌扩展数据

        table_info消息
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
                    },...
                ],
                "tableId": 750410010200
            }
        }
        """
        message = self.__init_basic_msg('table_info')
        message.setResult('userId', targets[seat_id].userId)
        message.setResult('seatId', seat_id)
        message.setResult('header_seat_id', banker_seat_id)
        message.setResult('maxSeatN', seats_count)
        message.setResult('play_mode', play_mode)
        message.setResult('action_id', action_id)
        message.setResult('tableType', "create")
        message.setResult('reconnect', is_reconnect)
        message.setResult('timeout', 9)
        message.setResult('remained_count', remained_count)
        if extend_info:
            message.setResult('create_table_extend_info', extend_info)

        # 缓存消息机制 有缺陷
        backup_message = self.latestMsg[seat_id]
        if is_reconnect and backup_message and action_id == backup_message.getResult('action_id', 0):
            backup_seat_id = backup_message.getResult('seatId', -1)
            backup_tile = backup_message.getResult('tile', 0)
            if backup_seat_id == seat_id and backup_message.getCmd() == 'send_tile':
                # 如果缓存的是当前玩家的摸牌,add_tile就没有内容
                player_info[seat_id]['add_tile'] = []
                pass

            # 如果上一条缓存的是出牌消息, 需要在对应玩家的手牌里加一张0,如果是自己的牌则不用
            if backup_seat_id != seat_id and backup_message.getCmd() == 'play':
                player_info[backup_seat_id]['standup_tiles'].append(0)
                if backup_tile in player_info[backup_seat_id]['drop_tiles']:
                    player_info[backup_seat_id]['drop_tiles'].remove(backup_tile)

        message.setResult('players', player_info)

        self.addUserStep(message, targets[seat_id].userId)
        send_msg_only(message, targets, seat_id)
        if not is_reconnect:
            self.addMsgRecord(message, targets[seat_id].userId)

    def table_call_init_tiles(self, targets, seat_id, tiles, banker_seat_id):
        """
        给玩家起手发牌 (public api)
        参数说明：
        @param targets, 协议发送的目标玩家对象players, 只有seat_id是当前玩家, 其他玩家都只广播
        @param seat_id, 给谁(seat_id)发 start from 0
        @param tiles 发牌花色数组
        @param banker_seat_id 庄家的服务端座位号

        协议示例
        {"cmd":"init_tiles","result":{"header_seat_id":0, "seatId":1, "tiles":[34,27,28,26,26,33,21,29,27,28,26,27,34],"gameId":7201}}

        PS:
        1.给本家发送该协议
        """
        host = targets[seat_id]
        message = self.__init_basic_msg('init_tiles')
        message.setResult('tiles', tiles)
        message.setResult('header_seat_id', banker_seat_id)
        message.setResult('seatId', seat_id)
        self.addUserStep(message, host.userId)
        send_msg_only(message, targets, seat_id)
        self.addMsgRecord(message, host.userId)

    def table_call_send_tile(self, targets, tile, seat_id, time_out, action_id, actions):
        """
        给玩家发牌，只给收到摸牌的玩家发这条消息 (public api)
        参数说明：
        @param targets, 协议发送的目标玩家对象players, 只有seat_id是当前玩家, 其他玩家都只广播
        @param tile 发牌花色
        @param seat_id 摸牌玩家的服务端座位号 start from 0
        @param time_out 超时时间(等待玩家操作)
        @param action_id
        @param actions

        协议示例
        {"cmd":"send_tile","result":{"seatId":0, "tile":2, "gang_action":[], "timeout":30,"remained_count":83, "action_id":1, "gameId":7201}};

        PS:
        1.给本家发送的协议中携带玩家当前手牌信息
        standup_tiles:[], peng_tiles:[[]], chi_tiles:[[]], gang_tiles:[[]]

        2.非亮牌情况下, tile字段只有本家才可以收到

        3.协议里可能携带各种操作action(gang_action, chi_action, peng_action, win_action..., etc.)
        gang_action, win_action
        """
        message = self.__init_basic_msg("send_tile")
        host = targets[seat_id]

        message.setResult('seatId', seat_id)
        message.setResult('timeout', time_out)
        message.setResult('action_id', action_id)
        message.setResult('remained_count', self.tableTileMgr.getTilesLeftCount())

        # 给其他玩家广播消息
        send_msg_except(message, targets, seat_id)

        # AI运算需要，这时已经把牌加到手牌中了，消息中挪出新增的牌
        hand_tiles = host.copyHandTiles()
        hand_tiles.remove(tile)
        message.setResult('tile', tile)
        message.setResult('standup_tiles', hand_tiles)
        message.setResult('gang_tiles', host.copyGangArray())
        message.setResult('peng_tiles', host.copyPengArray())
        message.setResult('chi_tiles', host.copyChiArray())

        # acitons
        kongs = actions.getChiPengGangResult(MTableState.TABLE_STATE_GANG)
        if kongs:  # 是否能杠
            message.setResult('gang_action', kongs)

        wins = actions.getChiPengGangResult(MTableState.TABLE_STATE_HU)
        if wins and len(wins) > 0:  # 是否能胡
            message.setResult('win_tile', wins[0]['tile'])  # 胡牌的花色
            message.setResult('win_degree', 1)  # 地方麻将不需要番数

        # 缓存消息
        self.latestMsg[host.curSeatId] = message
        self.addUserStep(message, host.userId)  # 记录每个玩家在当前牌局中的步骤数,以供客户端检测是否漏消息!
        send_msg_only(message, targets, seat_id)  # 给当前玩家发送消息
        self.addMsgRecord(message, host.userId)  # 牌局记录

    def table_call_play(self, active_seat_id, tile, targets, passive_seat_id, time_out, state, action_id, actions):
        """
        玩家打牌，(public api)
        参数说明：
        @param active_seat_id 打牌者座位号(主动) start from 0
        @param tile 打牌花色
        @param targets, 玩家对象players集合
        @param passive_seat_id 受体玩家座位号(被动) start from 0
        @param time_out 超时时间(等待玩家操作)
        @param state 状态值(标记targets玩家可以就seat_id对应的打牌玩家打出的牌所进行的行为)
        @param action_id
        @param actions (行为,eg:chi_action,peng_action...,etc)

        协议示例
        {"cmd":"play","result":{"seatId":1,"tile":26, "chi_action":[ [26, 27, 28] ], "timeout":9, "gameId":7201}};

        PS:
        1.协议里可能携带各种操作action(gang_action, chi_action, peng_action, win_action..., etc.)
        gang_action, chi_action, peng_action, win_action
        """
        message = self.__init_basic_msg("play")
        message.setResult("tile", tile)
        message.setResult('seatId', active_seat_id)
        message.setResult('timeout', time_out)
        message.setResult('action_id', action_id)
        message.setResult('remained_count', self.tableTileMgr.getTilesLeftCount())

        count = 0
        passive = targets[passive_seat_id]  # 收协议方
        if passive.state != MPlayer.PLAYER_STATE_WON:
            if state & MTableState.TABLE_STATE_CHI:
                message.setResult('chi_action', actions.getChiPengGangResult(MTableState.TABLE_STATE_CHI))
                count += 1
            if state & MTableState.TABLE_STATE_PENG:
                message.setResult('peng_action', actions.getChiPengGangResult(MTableState.TABLE_STATE_PENG))
                count += 1
            if state & MTableState.TABLE_STATE_GANG:
                message.setResult('gang_action', actions.getChiPengGangResult(MTableState.TABLE_STATE_GANG))
                count += 1
            if state & MTableState.TABLE_STATE_HU:
                message.setResult('win_degree', 1)
                message.setResult('win_action', 1)
                count += 1

        # 保存最新的消息
        if count > 0:
            self.latestMsg[passive_seat_id] = message
        self.addUserStep(message, passive.userId)
        send_msg_only(message, targets, passive_seat_id)
        self.addMsgRecord(message, passive.userId)

    def table_call_chow(self, targets, seat_id, active_seat_id, passive_seat_id, tile, pattern, \
                        time_out, action_id, actions):
        """
        玩家吃牌，(public api)
        参数说明：
        @param targets, 玩家对象players集合
        @param seat_id, 协议接收方的座位号
        @param active_seat_id 吃牌者座位号(主动) start from 0
        @param passive_seat_id 被吃牌玩家座位号(被动) start from 0
        @param tile 吃牌花色
        @param pattern 吃牌牌型数组
        @param time_out 超时时间(等待玩家操作)
        @param action_id
        @param actions (行为,eg:gang_action,peng_action...,etc)

        协议示例
        {"cmd":"chi","result":{"tile":15,"pattern":[15,16,17], "seatId":1, "player_seat_id":2,"timeout":9,"action_id":2,"gameId":7201}};

        PS:
        1.协议里可能携带各种操作action(gang_action, chi_action, peng_action, win_action..., etc.)
        gang_action
        """
        message = self.__init_basic_msg("chi")
        message.setResult('seatId', active_seat_id)
        message.setResult('player_seat_id', passive_seat_id)
        message.setResult('tile', tile)
        message.setResult('pattern', pattern)
        message.setResult('timeout', time_out)
        message.setResult('action_id', action_id)

        if 'gang_action' in actions:
            kong_action = actions.get('gang_action', None)
            if kong_action:
                message.setResult('gang_action', kong_action)

        self.addUserStep(message, targets[seat_id].userId)
        send_msg_only(message, targets, seat_id)
        self.addMsgRecord(message, targets[seat_id].userId)

    def table_call_pong(self, targets, seat_id, active_seat_id, passive_seat_id, tile, pattern, time_out, action_id,
                        actions={}):
        """
        玩家碰牌，(public api)
        参数说明：
        @param targets, 玩家对象players集合
        @param seat_id, 协议接收方的座位号
        @param active_seat_id 碰牌者座位号(主动) start from 0
        @param passive_seat_id 被碰牌玩家座位号(被动) start from 0
        @param tile 碰牌花色
        @param pattern 碰牌牌型数组
        @param time_out 超时时间(等待玩家操作)
        @param action_id
        @param actions (行为,eg:gang_action,peng_action...,etc)

        协议示例
        {"cmd":"peng","result":{"tile":15,"pattern":[15,16,17], "seatId":1, "player_seat_id":2,"timeout":9,"action_id":2,"gameId":7201}};

        PS:
        1.协议里可能携带各种操作action(gang_action, chi_action, peng_action, win_action..., etc.)
        gang_action
        """
        message = self.__init_basic_msg("peng")
        message.setResult('seatId', active_seat_id)
        message.setResult('player_seat_id', passive_seat_id)
        message.setResult('tile', tile)
        message.setResult('pattern', pattern)
        message.setResult('timeout', time_out)
        message.setResult('action_id', action_id)

        if 'gang_action' in actions:
            kong_action = actions.get('gang_action', None)
            if kong_action:
                message.setResult('gang_action', kong_action)

        self.addUserStep(message, targets[seat_id].userId)
        send_msg_only(message, targets, seat_id)
        self.addMsgRecord(message, targets[seat_id].userId)

    def table_call_kong(self, targets, seat_id, active_seat_id, passive_seat_id, tile, pattern, style, loser_seat_ids,
                        time_out, action_id, actions={}):
        """
        玩家杠牌，(public api)
        参数说明：
        @param targets, 玩家对象players集合
        @param seat_id, 协议接收方的座位号
        @param active_seat_id 杠牌者座位号(主动) start from 0
        @param passive_seat_id 被杠牌玩家座位号(被动) start from 0
        @param tile 杠牌花色
        @param pattern 杠牌牌型数组
        @param style: 0暗杠, 1明杠
        @param loser_seat_ids: 放杠输家数组
        @param time_out 超时时间(等待玩家操作)
        @param action_id
        @param actions (行为,eg:gang_action,peng_action...,etc)

        协议示例
        {"cmd":"gang","result":{ "gang":{"tile":36, "pattern":[1,1,1,1], "style":1},
            "seatId":0,"player_seat_id":3,"loser_seat_ids":[3], "loser_coins":[16000],"gameId":7201}};

        PS:
        1.协议里可能携带各种操作action(gang_action, chi_action, peng_action, win_action..., etc.)
        gang_action
        """
        message = self.__init_basic_msg("gang")
        message.setResult('tile', tile)
        message.setResult('gang', {"tile": tile, "pattern": pattern, "style": style})
        message.setResult('seatId', active_seat_id)
        message.setResult('player_seat_id', passive_seat_id)
        message.setResult('action_id', action_id)
        message.setResult('timeout', time_out)
        message.setResult('loser_seat_ids', loser_seat_ids)

        self.addUserStep(message, targets[seat_id].userId)
        send_msg_only(message, targets, seat_id)
        self.addMsgRecord(message, targets[seat_id].userId)

    def table_call_score(self, targets, score, delta):
        """
        玩家积分刷新，(public api)
        参数说明：
        @param targets, 玩家对象players集合
        @param score
        @param delta

        协议示例
        {"cmd":"score","result":{ "score":[1,2,3,4], "delta":[-1,3,-1,-1], "gameId":7201}}
        """
        message = self.__init_basic_msg('score')
        message.setResult('score', score)
        message.setResult('delta', delta)

        user_ids = []
        for i in range(0, len(targets)):
            if targets[i]:
                user_ids.append(targets[i].userId)

        self.addUserStep(message, user_ids)
        send_msg_except(message, targets)
        self.addMsgRecord(message, user_ids)

    def table_call_budget(self, cmd, targets, active_seat_id, passive_seat_ids, win_mode, tile, score_base, total_score,
                          delta_score, patterns, game_flow, is_final, extend_info):
        """
        玩家结算，(public api)
        参数说明：
        @param cmd, "win" or "lose"
        @param targets, 玩家对象players集合
        @param active_seat_id, 结算者者座位号(主动) start from 0
        @param passive_seat_ids, 输家座位号列表(不一定有) start from 0
        @param tile 胡牌花色, 不一定有
        @param win_mode -1输,0自摸,1胡牌
        @param score_base, 基础加分
        @param total_score, 总分(不含基础加分)
        @param delta_score, #该局分数变化
        @param patterns, #胡牌番型

        协议示例

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
                "tile": 18 # 胡牌
            }
        }
        """
        message = self.__init_basic_msg(cmd)

        target = targets[active_seat_id]
        message.setResult('userId', target.userId)  # 结算玩家userId
        message.setResult('seatId', active_seat_id)  # 结算玩家座位号
        message.setResult('loserSeatIds', passive_seat_ids)  # 输家座位号

        message.setResult('gameFlow', game_flow)  # 是否流局(1 流局, 0 不流局)
        message.setResult('winMode', win_mode)  # 该局赢的类型，基本值: 0是自摸，1是放炮 -1输了(可扩展)

        message.setResult('timestamp', pktimestamp.getCurrentTimestamp())  # 和牌时间戳
        message.setResult('final', is_final)  # boolean 标记牌局是否结束

        message.setResult('create_table_extend_info', extend_info)

        # 结算分数发在detail里面
        message.setResult('detail', {
            "score": score_base + total_score,  # 总分(含基础加分)
            "total_delta_score": total_score,  # 总分(不含基础加分)
            "delta_score": delta_score,  # 该局分数变化
            "patterns": patterns  # "番型" eg: ["清一色"]
        })

        if is_final:  # 牌局结束了 才允许下发玩家手牌信息
            message.setResult('tilesInfo', {
                "tiles": target.copyHandTiles(),  # [1,2,3,4,5]
                "chi": target.copyChiArray(),  # [[2,3,4],[5,6,7]]
                "peng": target.copyPengArray(),  # [1,1,1]
                "gang": target.copyGangArray(),  # {"pattern":[5,5,5,5],"style":0,"actionID":45}
                "tile": tile,  # 7 胡七万
            })

        user_ids = []
        for i in range(0, len(targets)):
            if targets[i]:
                user_ids.append(targets[i].userId)
        self.addUserStep(message, user_ids)
        send_msg_except(message, targets)
        self.addMsgRecord(message, user_ids)

    def upload_game_record_to_cdn(self, name, urls):
        """
        服务器上传牌局记录到CDN，(public api)(非客户端通讯协议)
        参数说明：
        @param name, 记录名
        @param urls, 地址
        """
        self.saveRecord(name, urls)
