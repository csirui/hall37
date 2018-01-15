# -*- coding=utf-8 -*-
'''
Created on 2015年9月30日
麻将好友桌的牌桌，负责好友桌号的管理和好友桌赛制的调度。
@author: 赵良
'''
from difang.majiang2.entity import majiang_conf
from difang.majiang2.entity import util
from difang.majiang2.entity.create_table import CreateTableData
from difang.majiang2.table.friend_table_define import MFTDefine
from difang.majiang2.table.majiang_quick_table import MajiangQuickTable
from difang.majiang2.table.table_config_define import MTDefine
from difang.servers.util.rpc import user_remote
from freetime.core.lock import locked
from freetime.util import log as ftlog
from hall.entity import hall_friend_table
from poker.entity.configure import gdata
from poker.entity.game.tables.table_player import TYPlayer


class MajiangFriendTable(MajiangQuickTable):
    # 解散同意
    DISSOLVE_AGREE = 1
    # 解散拒绝
    DISSOLVE_REFUSE = 0

    """
    好友桌的牌桌管理类，继承自MajiangQuickTable
    与MajiangQuickTable相比，有几个地方不同。
    1）角色区分房主非房主
    2）准备阶段，房主退出，房间解散，归还全部房卡
    3）牌局开始后，退出走投票机制
    4）自建桌有局数设置，所有的局数打完，散桌。没打完时，继续准备开始下一局
    """

    def __init__(self, tableId, room):
        super(MajiangFriendTable, self).__init__(tableId, room)
        self.__init_params = None
        self.__ftId = None
        self.__table_owner = 0
        self.__vote_info = [None for _ in range(self.maxSeatN)]
        self.__vote_host = MTDefine.INVALID_SEAT
        self.__vote_time_out = 0
        self.__params_desc = None
        self.__params_play_desc = None
        self.__table_owner_seatId = MTDefine.INVALID_SEAT
        self.__ready_time_out_timer = False

    @property
    def tableOwnerSeatId(self):
        return self.__table_owner_seatId

    @property
    def initParams(self):
        return self.__init_params

    @property
    def ftId(self):
        return self.__ftId

    @property
    def voteInfo(self):
        return self.__vote_info

    @property
    def voteHost(self):
        return self.__vote_host

    @property
    def voteTimeOut(self):
        return self.__vote_time_out

    def sendMsgTableInfo(self, msg, userId, seatId, isReconnect, isHost=False):
        """用户坐下后给用户发送table_info"""
        if msg and msg.getParam('itemParams', None):
            self.__init_params = msg.getParam('itemParams', None)
            self.__params_desc = self.get_select_create_config_items()
            self.__params_play_desc = self.get_select_create_config_items(True)
            ftlog.debug('MajiangFriendTable.sendMsgTableInfo userId:', userId
                        , ' seatId:', seatId
                        , ' message:', msg
                        , ' itemParams:', self.__init_params
                        )
            ftId = msg.getParam('ftId', None)
            if ftId:
                self.processCreateTableSetting()
                self.__ftId = ftId
                # 保存自建桌对应关系
                CreateTableData.addCreateTableNo(self.tableId, self.roomId, gdata.serverId(), self.ftId)

                self.__table_owner = userId
                self.__table_owner_seatId = seatId
                self.logic_table.tableConfig[MFTDefine.FTID] = self.__ftId
                self.logic_table.tableConfig[MFTDefine.FTOWNER] = userId
                self.logic_table.tableConfig[MFTDefine.ITEMPARAMS] = self.__init_params
                self.logic_table.tableConfig[MFTDefine.CREATE_TABLE_DESCS] = self.__params_desc
                self.logic_table.tableConfig[MFTDefine.CREATE_TABLE_PLAY_DESCS] = self.__params_play_desc
                # 返回房主建房成功消息，准备状态
                self.logic_table.playerReady(self.getSeatIdByUserId(userId), True)
                self.logic_table.msgProcessor.create_table_succ_response(userId
                                                                         , self.getSeatIdByUserId(userId)
                                                                         , 'ready'
                                                                         , 1
                                                                         , self.logic_table.getBroadCastUIDs())

                # 房主启动准备定时器，超时解散牌桌
                message = self.logic_table.msgProcessor.getMsgReadyTimeOut()
                readyTimeOut = self.getTableConfig(MFTDefine.READY_TIMEOUT, 3600)
                ftlog.debug('MajiangFriendTable.sendMsgTableInfo begin to check ready timeout, message:', message
                            , ' readyTimeOut:', readyTimeOut
                            , ' tableOwnerSeatId:', self.tableOwnerSeatId)
                self.tableTimer.setupTimer(self.tableOwnerSeatId, readyTimeOut, message)
                self.__ready_time_out_timer = True
        # 发送table_info
        super(MajiangFriendTable, self).sendMsgTableInfo(msg, userId, seatId, isReconnect, userId == self.__table_owner)
        # 如果正在投票解散，给用户补发投票解散的消息
        if self.logic_table.isFriendTablePlaying() and self.voteHost != MTDefine.INVALID_SEAT:
            # 补发投票解散信息
            self.logic_table.msgProcessor.create_table_dissolve_vote(self.players[self.voteHost].userId
                                                                     , self.voteHost
                                                                     , self.maxSeatN
                                                                     , self.get_leave_vote_info()
                                                                     , self.get_leave_vote_info_detail()
                                                                     , self.logic_table.player[self.voteHost].name
                                                                     , self.__vote_time_out
                                                                     , self.logic_table.getBroadCastUIDs())

    def get_select_create_config_items(self, playDesc=False):
        """获取自建桌创建的选项描述
        """
        ret = []
        create_table_config = majiang_conf.getCreateTableTotalConfig(self.gameId)
        playmode_config = {}
        if create_table_config:
            playmode_config = create_table_config.get(self.playMode, {})

        # 通过id直接获取自建桌配置的key数组
        for key, value in self.__init_params.iteritems():
            if key not in playmode_config:
                continue

            if playDesc and (key == 'cardCount' or key == 'playerType'):
                continue

            items = playmode_config[key]
            for item in items:
                if item['id'] == value:
                    ret.append(item['desc'])

        ftlog.debug('get_select_create_config_items descs:', ret)
        return ret

    def processCreateTableSetting(self):
        """解析处理自建桌参数"""
        # 配置1 轮数
        cardCountId = self.initParams.get(MFTDefine.CARD_COUNT, 0)
        cardCountConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, MFTDefine.CARD_COUNT,
                                                            cardCountId)
        if cardCountConfig:
            round_count = cardCountConfig.get('value', 1)
            card_count = cardCountConfig.get('fangka_count', 1)
            self.logic_table.tableConfig[MFTDefine.ROUND_COUNT] = round_count
            self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT] = 0
            self.logic_table.tableConfig[MFTDefine.CARD_COUNT] = card_count
            self.logic_table.tableConfig[MFTDefine.LEFT_CARD_COUNT] = card_count
            ftlog.debug('MajiangFriendTable.processCreateTableSetting roundCount:', round_count, 'cardCount',
                        card_count)

        # 配置2 纯夹
        chunJiaId = self.initParams.get('chunJia', 0)
        chunJiaConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'chunJia', chunJiaId)
        if chunJiaConfig:
            self.logic_table.tableConfig[MTDefine.MIN_MULTI] = chunJiaConfig.get(MTDefine.MIN_MULTI, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting chunJia:',
                        self.logic_table.tableConfig[MTDefine.MIN_MULTI])

        # 配置3 红中宝
        hzbId = self.initParams.get('hongZhongBao', 0)
        hzbConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'hongZhongBao', hzbId)
        if hzbConfig:
            self.logic_table.tableConfig[MTDefine.HONG_ZHONG_BAO] = hzbConfig.get(MTDefine.HONG_ZHONG_BAO, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting hongZhongBao:',
                        self.logic_table.tableConfig[MTDefine.HONG_ZHONG_BAO])

        # 配置4 三七边
        sqbId = self.initParams.get('sanQiBian', 0)
        sqbConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'sanQiBian', sqbId)
        if sqbConfig:
            self.logic_table.tableConfig[MTDefine.BIAN_MULTI] = sqbConfig.get(MTDefine.BIAN_MULTI, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting sanQiBian:',
                        self.logic_table.tableConfig[MTDefine.BIAN_MULTI])

        # 配置5 刮大风
        fengId = self.initParams.get('guaDaFeng', 0)
        fengConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'guaDaFeng', fengId)
        if fengConfig:
            self.logic_table.tableConfig[MTDefine.GUA_DA_FENG] = fengConfig.get(MTDefine.GUA_DA_FENG, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting guaDaFeng:',
                        self.logic_table.tableConfig[MTDefine.GUA_DA_FENG])

        # 配置6 频道
        pinDaoId = self.initParams.get('pinDao', 0)
        pinDaoConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'pinDao', pinDaoId)
        if pinDaoConfig:
            self.logic_table.tableConfig[MTDefine.PIN_DAO] = pinDaoConfig.get(MTDefine.PIN_DAO, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting pinDao:',
                        self.logic_table.tableConfig[MTDefine.PIN_DAO])

        # 配置7 跑恰摸八
        paoqiamobaId = self.initParams.get('paoqiamoba', 0)
        paoqiamobaConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'paoqiamoba', paoqiamobaId)
        if paoqiamobaConfig:
            self.logic_table.tableConfig[MTDefine.PAOQIAMOBA] = paoqiamobaConfig.get(MTDefine.PAOQIAMOBA, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting paoqiamoba:',
                        self.logic_table.tableConfig[MTDefine.PAOQIAMOBA])

        # 配置8 定漂
        dingPiaoId = self.initParams.get('dingPiao', 0)
        dingPiaoConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'dingPiao', dingPiaoId)
        if dingPiaoConfig:
            self.logic_table.tableConfig[MTDefine.DING_PIAO] = dingPiaoConfig.get(MTDefine.DING_PIAO, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting dingPiao:',
                        self.logic_table.tableConfig[MTDefine.DING_PIAO])

        # 配置9 买马
        maiMaId = self.initParams.get('maiMa', 0)
        maiMaConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'maiMa', maiMaId)
        if maiMaConfig:
            self.logic_table.tableConfig[MTDefine.MAI_MA] = maiMaConfig.get(MTDefine.MAI_MA, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting maiMa:',
                        self.logic_table.tableConfig[MTDefine.MAI_MA])

        # 配置10 数坎
        shuKanId = self.initParams.get('shuKan', 0)
        shuKanConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'shuKan', shuKanId)
        if shuKanConfig:
            self.logic_table.tableConfig[MTDefine.SHU_KAN] = shuKanConfig.get(MTDefine.SHU_KAN, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting shuKan:',
                        self.logic_table.tableConfig[MTDefine.SHU_KAN])

        # 配置11 听牌时亮牌规则
        liangPaiId = self.initParams.get('liangPai', 0)
        liangPaiConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'liangPai', liangPaiId)
        if liangPaiConfig:
            self.logic_table.tableConfig[MTDefine.LIANG_PAI] = liangPaiConfig.get(MTDefine.LIANG_PAI, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting liangPai:',
                        self.logic_table.tableConfig[MTDefine.LIANG_PAI])

        # 配置12 最大番数
        maxFanId = self.initParams.get('maxFan', 0)
        maxFanConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'maxFan', maxFanId)
        if maxFanConfig:
            self.logic_table.tableConfig[MTDefine.MAX_FAN] = maxFanConfig.get(MTDefine.MAX_FAN, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting maxFan:',
                        self.logic_table.tableConfig[MTDefine.MAX_FAN])

        # 配置13 卡五星番数
        kawuxingFanId = self.initParams.get('kawuxingFan', 0)
        kawuxingFanConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'kawuxingFan', kawuxingFanId)
        if kawuxingFanConfig:
            self.logic_table.tableConfig[MTDefine.KAWUXING_FAN] = kawuxingFanConfig.get(MTDefine.KAWUXING_FAN, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting kawuxingFan:',
                        self.logic_table.tableConfig[MTDefine.KAWUXING_FAN])

        # 配置14 碰碰胡番数
        pengpenghuFanId = self.initParams.get('pengpenghuFan', 0)
        pengpenghuFanConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'pengpenghuFan',
                                                                pengpenghuFanId)
        if pengpenghuFanConfig:
            self.logic_table.tableConfig[MTDefine.PENGPENGHU_FAN] = pengpenghuFanConfig.get(MTDefine.PENGPENGHU_FAN, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting pengpenghuFan:',
                        self.logic_table.tableConfig[MTDefine.PENGPENGHU_FAN])

        # 配置15 杠上花番数
        gangshanghuaFanId = self.initParams.get('gangshanghuaFan', 0)
        gangshanghuaFanConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'gangshanghuaFan',
                                                                  gangshanghuaFanId)
        if gangshanghuaFanConfig:
            self.logic_table.tableConfig[MTDefine.GANGSHANGHUA_FAN] = gangshanghuaFanConfig.get(
                MTDefine.GANGSHANGHUA_FAN, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting gangshanghuaFan:',
                        self.logic_table.tableConfig[MTDefine.GANGSHANGHUA_FAN])

        # 配置16 闭门算番(鸡西)
        biMenFanId = self.initParams.get('biMenFan', 0)
        biMenFanConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'biMenFan', biMenFanId)
        if biMenFanConfig:
            self.logic_table.tableConfig[MTDefine.BI_MEN_FAN] = biMenFanConfig.get(MTDefine.BI_MEN_FAN, 0)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting biMenFan:',
                        self.logic_table.tableConfig[MTDefine.BI_MEN_FAN])

        # 配置17 抽奖牌数量(鸡西)
        awordTileCountId = self.initParams.get('awordTileCount', 0)
        awordTileCountConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'awordTileCount',
                                                                 awordTileCountId)
        if awordTileCountConfig:
            self.logic_table.tableConfig[MTDefine.AWARD_TILE_COUNT] = awordTileCountConfig.get(
                MTDefine.AWARD_TILE_COUNT, 1)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting awordTileCount:',
                        self.logic_table.tableConfig[MTDefine.AWARD_TILE_COUNT])

        # 配置18 宝牌隐藏(鸡西 默认暗宝)
        magicHideId = self.initParams.get('magicHide', 0)
        magicHideConfig = majiang_conf.getCreateTableConfig(self.gameId, self.playMode, 'magicHide', magicHideId)
        if magicHideConfig:
            self.logic_table.tableConfig[MTDefine.MAGIC_HIDE] = awordTileCountConfig.get(MTDefine.MAGIC_HIDE, 1)
            ftlog.debug('MajiangFriendTable.processCreateTableSetting magicHide:',
                        self.logic_table.tableConfig[MTDefine.MAGIC_HIDE])

    def _doTableCall(self, msg, userId, seatId, action, clientId):
        """
        继承父类，处理table_call消息
        单独处理自建桌的分享/解散
        """
        if not self.CheckSeatId(seatId, userId):
            ftlog.warn("MajiangFriendTable.doTableCall, delay msg action:", action
                       , ' seatId:', seatId
                       , ' messange:', msg)
            return

        if action == 'next_round':
            if self.logic_table.isStart():
                return
            self.logic_table.sendMsgTableInfo(seatId)
            beginGame = self.logic_table.playerReady(seatId, True)
            self.logic_table.msgProcessor.create_table_succ_response(userId, seatId, 'ready',
                                                                     1 if (userId == self.__table_owner) else 0,
                                                                     self.logic_table.getBroadCastUIDs())
            for player in self.logic_table.player:
                if not player:
                    continue

                if not TYPlayer.isHuman(player.userId):
                    beginGame = self.logic_table.playerReady(player.curSeatId, True)

            if beginGame:
                # 纪录上一局的日志 给GM使用
                # addOneResult(tableNo, seats, deltaScore, totalScore, curRound, totalRound, gameId, roomId, tableId)
                if self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT] > 1:
                    roundResult = self.logic_table.tableResult.results[-1]
                    deltaScore = roundResult.score
                    totalScore = self.logic_table.tableResult.score
                    curRound = self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT] - 1
                    totalRound = self.logic_table.tableConfig[MFTDefine.ROUND_COUNT]
                    seats = self.logic_table.getSeats()
                    ftlog.debug('MajiangFriendTable.doTableCall nextRound stat tableNo', self.ftId, 'seats', seats,
                                'deltaScore:',
                                deltaScore, 'totalScore:', totalScore, 'gameId:', self.gameId, 'roomId:', self.roomId,
                                'tableId', self.tableId)
                    hall_friend_table.addOneResult(self.ftId, seats, deltaScore, totalScore, curRound, totalRound,
                                                   self.gameId, self.roomId, self.tableId)
                else:
                    ftlog.debug('MajiangFriendTable.doTableCall nextRound stat log error')
            else:
                ftlog.debug('MajiangFriendTable.doTableCall nextRound stat log error not begin')
        elif action == 'ready':
            # 返回房主建房成功消息，准备状态
            # 玩家准备结束 游戏正式开始
            beginGame = self.logic_table.playerReady(seatId, True)
            self.logic_table.msgProcessor.create_table_succ_response(userId, seatId, 'ready',
                                                                     1 if (userId == self.__table_owner) else 0,
                                                                     self.logic_table.getBroadCastUIDs())
            if beginGame and self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT] > 0:
                # 纪录开局日志 gameBegin(tableNo, seats, gameId, roomId, tableId)
                seats = self.logic_table.getSeats()
                ftlog.debug('MajiangFriendTable._doTableCall log game begin tableNo:', self.__ftId, 'seats:', seats,
                            'gameId:', self.gameId, 'roomId:', self.roomId, 'tableId', self.tableId)
                hall_friend_table.gameBegin(self.__ftId, seats, self.gameId, self.gameId, self.tableId)
            else:
                ftlog.debug('MajiangFriendTable._doTableCall log game begin not ready cur round:',
                            self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT])
        elif action == 'create_table_user_leave':
            if (self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT] > 0):
                util.sendPopTipMsg(userId, "游戏已开始，不能解散")
                return

            # 房主解散，由前端主动发送，存在隐患，后续修改。房主建房后，掉线，房主的房间状态将不对，TODO
            if userId == self.__table_owner:
                ftlog.debug('MajiangFriendTable.create_table_user_leave owner leave...')
                # 解散时，给大家提示
                for player in self.logic_table.player:
                    if not player:
                        continue
                    # 通知
                    util.sendPopTipMsg(player.userId, "房主解散房间")

                # 归还剩余房卡道具
                ftlog.debug('MajiangFriendTable.doTableCall leftCardCount:',
                            self.logic_table.tableConfig[MFTDefine.LEFT_CARD_COUNT]
                            , ' tableOwner:', self.__table_owner)
                if self.logic_table.tableConfig[MFTDefine.LEFT_CARD_COUNT] > 0:
                    itemId = self.room.roomConf.get('create_item', None)
                    if itemId:
                        user_remote.resumeItemFromTable(self.__table_owner
                                                        , self.gameId
                                                        , itemId
                                                        , self.logic_table.tableConfig[MFTDefine.LEFT_CARD_COUNT]
                                                        , self.roomId
                                                        , self.tableId)
                # 解散牌桌
                self.clearTable(True)
            else:
                ftlog.debug('MajiangFriendTable.create_table_user_leave player leave...')
                util.sendPopTipMsg(userId, "您已退出房间")
                self.kickOffUser(userId, seatId, True)
        elif action == 'create_table_dissolution':
            if self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT] == 0:
                ftlog.debug(
                    'MajiangFriendTable._doTableCall create_table_dissolution game not start, can not dissolved...')
                return

            # 投票解散牌桌
            if self.voteHost != MTDefine.INVALID_SEAT:
                ftlog.debug('MajiangFriendTable._doTableCall create_table_dissolution ', self.voteHost,
                            ' already dissolved...')
                return

            self.__vote_host = seatId
            self.__vote_info[seatId] = {'userId': userId, 'seatId': seatId, 'vote': self.DISSOLVE_AGREE}
            self.__vote_time_out = self.getTableConfig('dissolve_vote_time_out', 60)
            ftlog.debug('MajiangFriendTable.create_table_dissolution voteInfo:', self.voteInfo)

            # 广播解散投票消息
            self.logic_table.msgProcessor.create_table_dissolve_vote(userId
                                                                     , seatId
                                                                     , self.maxSeatN
                                                                     , self.get_leave_vote_info()
                                                                     , self.get_leave_vote_info_detail()
                                                                     , self.logic_table.player[seatId].name
                                                                     , self.__vote_time_out
                                                                     , self.logic_table.getBroadCastUIDs())
        elif action == 'user_leave_vote':
            ftlog.debug('MajiangFriendTable._doTableCall voteInfo:', self.voteInfo)
            if self.voteHost == MTDefine.INVALID_SEAT:
                ftlog.debug(
                    'MajiangFriendTable._doTableCall user_leave_vote, voteHost is invalid, no need process this message...')
                return

            vote = msg.getParam('vote', 0)
            self.__vote_info[seatId] = {'userId': userId, 'seatId': seatId, 'vote': vote}
            self.logic_table.msgProcessor.create_table_dissolve_vote(userId
                                                                     , seatId
                                                                     , self.maxSeatN
                                                                     , self.get_leave_vote_info()
                                                                     , self.get_leave_vote_info_detail()
                                                                     , self.logic_table.player[self.voteHost].name
                                                                     , self.__vote_time_out
                                                                     , self.logic_table.getBroadCastUIDs())
            # 计算投票结果
            self.dissolveDecision()

        elif action == 'create_friend_invite':  # 微信邀请todotask下发
            contentStr = ','.join(self.__params_desc)
            util.sendTableInviteShareTodoTask(userId
                                              , self.gameId
                                              , self.ftId
                                              , self.playMode
                                              , self.logic_table.tableConfig[MFTDefine.CARD_COUNT]
                                              , contentStr)
        elif action == 'friend_table_ready_time_out':
            # 准备超时，回收牌桌
            self.clearTable(True)
        else:
            super(MajiangFriendTable, self)._doTableCall(msg, userId, seatId, action, clientId)

    """
    def kickOffUser(self, userId, seatId, sendLeave = False):
        # 拉出牌桌
        #游戏开始之后的退出，客户端不需要再收到退出消息 客户端的退出由其自身控制
        #游戏未开始时房主解散了房间才需要向客户端发消息
        if sendLeave:
            uids = self.logic_table.getBroadCastUIDs()
            self.logic_table.msgProcessor.create_table_dissolve(userId, seatId, 'dissolve', uids)
        super(MajiangFriendTable, self).kickOffUser(userId, seatId)
    """

    def _doStandUp(self, msg, userId, seatId, reason, clientId):
        '''
        自建桌这里的逻辑退出，不自动站起/退出
        '''
        pass

    @locked
    def handle_auto_decide_action(self):
        # ftlog.debug('@@@@@@@@@@@@@@@@@@MajiangFriendTable.handle_auto_decide_action',str(self.logic_table.__class__))
        """牌桌定时器"""
        if self.__ready_time_out_timer and self.logic_table.isFriendTablePlaying():
            self.__ready_time_out_timer = False
            self.tableTimer.cancelTimer(self.tableOwnerSeatId)

        if self.voteHost != MTDefine.INVALID_SEAT:
            ftlog.debug('MajiangFriendTable.handle_auto_decide_action voteTimeOut--')
            self.__vote_time_out -= 1
            if self.voteTimeOut == 0:
                self.processVoteDissolveTimeOut()

        if self.logic_table.isGameOver():
            """游戏结束，通知玩家离开，站起，重置牌桌"""
            ftlog.debug('MajiangFriendTable.handle_auto_decide_action gameOver... tableId:', self.tableId
                        , ' totalRoundCount:', self.logic_table.tableConfig[MFTDefine.ROUND_COUNT]
                        , ' now RoundCount:', self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT])

            if self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT] == self.logic_table.tableConfig[
                MFTDefine.ROUND_COUNT]:
                # TODO 自建桌最终结算
                score = []
                self.logic_table.sendCreateExtendBudgetsInfo(0, score)
                self.saveRecordAfterClear(score)
                self.clearTable(False)
                return

            self.logic_table.nextRound()
            return

        self.actionHander.updateTimeOut(-1)
        self.actionHander.doAutoAction()

    def processVoteDissolveTimeOut(self):
        """超时自动处理解散投票"""
        ftlog.debug('MajiangFriendTable.processVoteDissolveTimeOut...')
        for player in self.logic_table.player:
            if not player:
                continue

            if not self.voteInfo[player.curSeatId]:
                self.__vote_info[player.curSeatId] = {'userId': player.userId, 'seatId': player.curSeatId,
                                                      'vote': self.DISSOLVE_AGREE}
        self.dissolveDecision()

    def resetVoteInfo(self):
        self.__vote_host = MTDefine.INVALID_SEAT
        self.__vote_info = [None for _ in range(self.maxSeatN)]
        self.__vote_time_out = 0

    def dissolveDecision(self):
        """计算投票结果"""
        ftlog.debug('MajiangFriendTable.dissolveDecision voteInfo:', self.voteInfo)

        agree = 0
        refuse = 0
        for info in self.voteInfo:
            if not info:
                continue

            if info['vote']:
                agree += 1
            else:
                refuse += 1

        ftlog.debug('MajiangFriendTable.dissolveDecision agree:', agree, ' refuse:', refuse)
        bClear = False
        # 投票规则现在为只要有一人投了反对,就不解散
        if (agree + refuse) == self.maxSeatN:
            self.resetVoteInfo()
            if refuse <= 0:
                bClear = True
            # if agree > refuse:
            #                 bClear = True
            else:
                for player in self.logic_table.player:
                    if not player:
                        continue
                    util.sendPopTipMsg(player.userId, "经投票，牌桌继续...")
                    self.logic_table.msgProcessor.create_table_dissolve_close_vote(player.userId, player.curSeatId)
        else:
            voteConfig = self.getTableConfig(MFTDefine.LEAVE_VOTE_NUM, {})
            ftlog.debug('MajiangFriendTable.dissolveDecision voteConfig:', voteConfig)
            strCount = str(self.logic_table.playerCount)
            count = voteConfig.get(strCount, 0)
            if count and agree >= count:
                bClear = True

        if bClear:
            self.resetVoteInfo()
            # 解散牌桌时发送大结算
            score = []
            self.logic_table.sendCreateExtendBudgetsInfo(0, score)
            self.saveRecordAfterClear(score)
            # 牌桌解散
            for player in self.logic_table.player:
                if not player:
                    continue

                util.sendPopTipMsg(player.userId, "经投票，牌桌已解散")
                self.logic_table.msgProcessor.create_table_dissolve_close_vote(player.userId, player.curSeatId)

            # 归还剩余房卡道具
            ftlog.debug('MajiangFriendTable.dissolveDecision leftCardCount:',
                        self.logic_table.tableConfig[MFTDefine.LEFT_CARD_COUNT]
                        , ' tableOwner:', self.__table_owner)
            if self.logic_table.tableConfig[MFTDefine.LEFT_CARD_COUNT] > 0:
                itemId = self.room.roomConf.get('create_item', None)
                if itemId:
                    user_remote.resumeItemFromTable(self.__table_owner
                                                    , self.gameId
                                                    , itemId
                                                    , self.logic_table.tableConfig[MFTDefine.LEFT_CARD_COUNT]
                                                    , self.roomId
                                                    , self.tableId)
            self.clearTable(False)

    def get_leave_vote_info(self):
        """获取投票简要信息"""
        agree = 0
        disagree = 0
        for info in self.voteInfo:
            if not info:
                continue

            if info['vote'] == self.DISSOLVE_AGREE:
                agree += 1
            elif info['vote'] == self.DISSOLVE_REFUSE:
                disagree += 1
        return {'disagree': disagree, 'agree': agree}

    def get_leave_vote_info_detail(self):
        '''20160909新需求添加，增加用户头像,用户名等信息'''
        retList = []
        for info in self.voteInfo:
            if not info:
                continue

            retData = {}
            seatId = info['seatId']
            retData['name'], retData['purl'] = self.logic_table.player[seatId].name, self.logic_table.player[
                seatId].purl
            retData['vote'] = info['vote']
            retData['userId'] = info['userId']
            retList.append(retData)
        return retList

    def clearTable(self, sendLeave):
        # 纪录最后一局日志和结束日志
        seats = self.logic_table.getSeats()
        if self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT] == self.logic_table.tableConfig[
            MFTDefine.ROUND_COUNT]:
            if len(self.logic_table.tableResult.results) > 0:
                roundResult = self.logic_table.tableResult.results[-1]
                deltaScore = roundResult.score
                totalScore = self.logic_table.tableResult.score
                curRound = self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT]
                totalRound = self.logic_table.tableConfig[MFTDefine.ROUND_COUNT]
                ftlog.debug('MajiangFriendTable.cleraTable stat tableNo', self.ftId, 'seats', seats, 'deltaScore:',
                            deltaScore, 'totalScore:', totalScore, 'gameId:', self.gameId, 'roomId:', self.roomId,
                            'tableId', self.tableId)
                hall_friend_table.addOneResult(self.ftId, seats, deltaScore, totalScore, curRound, totalRound,
                                               self.gameId, self.roomId, self.tableId)
            else:
                ftlog.debug('MajiangFriendTable.cleraTable CUR_ROUND_COUNT',
                            self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT],
                            'ROUND_COUNT',
                            self.logic_table.tableConfig[MFTDefine.ROUND_COUNT])

        # def gameEnd(tableNo, seats, totalScore, totalRound, gameId, roomId, tableId)
        if self.logic_table.tableConfig[MFTDefine.CUR_ROUND_COUNT] > 0:
            totalScore = self.logic_table.tableResult.score
            if not totalScore:
                totalScore = [0 for _ in range(self.logic_table.playerCount)]
            totalRound = self.logic_table.tableConfig[MFTDefine.ROUND_COUNT]
            ftlog.debug('MajiangFriendTable.cleraTable stat gameEnd tableNo:', self.ftId, 'seats:', seats,
                        'totalScore:', totalScore, 'totalRound:', totalRound,
                        'gameId:', self.gameId, 'roomId:', self.roomId,
                        'tableId:', self.tableId)
            hall_friend_table.gameEnd(self.ftId, seats, totalScore, totalRound, self.gameId, self.roomId, self.tableId)

        """清理桌子"""
        super(MajiangFriendTable, self).clearTable(sendLeave)
        # 释放大厅房间ID
        hall_friend_table.releaseFriendTable(self.gameId, self.ftId)
        CreateTableData.removeCreateTableNo(gdata.serverId(), self.ftId)

    def getTableScore(self):
        '''
        取得当前桌子的快速开始的评分
        越是最适合进入的桌子, 评分越高, 座位已满评分为0
        '''
        if self.maxSeatN <= 0:
            return 1

        # 自建桌逻辑特殊，有人坐下后，后续就不安排人坐下了
        if self.playersNum > 0:
            return 0

        return (self.playersNum + 1) * 100 / self.maxSeatN
