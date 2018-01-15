# -*- coding=utf-8 -*-
'''
Created on 2015年9月30日
麻将陌生人桌的牌桌
@author: zhaol
'''
import copy
import random

from difang.majiang2.action_handler.action_handler_factory import ActionHandlerFactory
from difang.majiang2.entity import majiang_conf
from difang.majiang2.entity.create_table_record import MJCreateTableRecord
from difang.majiang2.entity.majiang_timer import MajiangTableTimer
from difang.majiang2.entity.util import sendPopTipMsg
from difang.majiang2.player.player import MPlayer
from difang.majiang2.table.friend_table_define import MFTDefine
from difang.majiang2.table.run_mode import MRunMode
from difang.majiang2.table.table_config_define import MTDefine
from difang.majiang2.table.table_expression import MTableExpression
from freetime.core.lock import locked
from freetime.core.timer import FTLoopTimer
from freetime.util import log as ftlog
from poker.entity.dao import onlinedata
from poker.entity.dao import userdata
from poker.entity.game.rooms.room import TYRoom
from poker.entity.game.tables.table import TYTable
from poker.entity.game.tables.table_player import TYPlayer
from poker.entity.game.tables.table_seat import TYSeat
from poker.protocol import runcmd
from poker.util import keywords


class MajiangQuickTable(TYTable):
    """
    1）负责框架桌子资源的管理，对接赛制/自建桌
    2）负责处理用户的上行消息处理
    3）麻将的具体逻辑，在逻辑类中处理
    4）负责联网玩法用户准备情况的管理，条件合适的时候开始游戏
    5）MajiangTable就是核心玩法里联网的action_handler
    """

    def __init__(self, tableId, room):
        super(MajiangQuickTable, self).__init__(room, tableId)
        self._owner = room
        self._players = []
        self.__actionHandler = ActionHandlerFactory.getActionHandler(MRunMode.LONGNET)

        # 初始化seat
        for seat in range(self.maxSeatN):
            self.seats[seat] = TYSeat(self)

        # 牌桌配置
        self._roomConf = self.room.roomConf
        ftlog.debug('MajiangQuickTable.init roomConf->', self._roomConf)

        self._tableConf = copy.deepcopy(self._roomConf.get('tableConf', {}))
        self._tableConf[MFTDefine.IS_CREATE] = self.getRoomConfig(MFTDefine.IS_CREATE, 0)
        ftlog.debug('MajiangQuickTable.init tableConf->', self._tableConf)

        # 创建逻辑配桌类
        self.__tableType = self.getRoomConfig('tableType', 'normal')
        self.__playMode = self.getRoomConfig('playMode', 'guobiao')
        ftlog.debug('MajiangQuickTable.init playMode:', self.playMode)
        # 逻辑牌桌
        self.__table_observer = None
        # 下面这部分代码改为在具体的麻将工程里执行,以实现不同牌桌逻辑的拆分
        # self.logic_table = MajiangTableLogic(self.maxSeatN, self.playMode, MRunMode.LONGNET)
        # self.logic_table.setTableConfig(self._tableConf)
        # # 设置牌桌公共信息，tableId & roomId
        # self.logic_table.msgProcessor.setInfo(self.gameId, self.roomId, self.tableId, self.playMode, self.tableType, self.maxSeatN)
        # self.logic_table.msgProcessor.setRoomInfo(self._roomConf, self._tableConf)

        # # 给action handler设置table
        # self.__actionHandler.setTable(self.logic_table)

        # 初始化定时器，个数是座位数加1
        self.__timer = MajiangTableTimer(self.maxSeatN + 1, self)
        # 循环定时器，用于处理牌桌托管状态
        self.__looper_timer = None

        ftlog.debug('MajiangQuickTable create ok, roomId:', self.roomId, ' tableId:', self.tableId)

    @property
    def tableObserver(self):
        return self.__table_observer

    def setTableObserver(self, observer):
        """设置牌桌观察者"""
        self.__table_observer = observer
        self.logic_table.setTableObserver(self.tableObserver)

    @property
    def tableTimer(self):
        return self.__timer

    @property
    def tableLooperTimer(self):
        return self.__looper_timer

    @property
    def actionHander(self):
        """行为解析处理器"""
        return self.__actionHandler

    @property
    def playMode(self):
        """玩法"""
        return self.__playMode

    @property
    def tableType(self):
        """牌桌类型"""
        return self.__tableType

    def changeFrameSeatToMJSeatId(self, frameSeat):
        """将框架的seatId转化为麻将的座位号
        获取座位号时，框架返回的是1，2，3，内部存储的索引是0，1，2
        麻将的座位号是0，1，2
        """
        return frameSeat - 1

    def changeMJSeatToFrameSeat(self, mjSeat):
        """将麻将的座位号转化为框架的座位号"""
        return mjSeat + 1

    def getRoomConfig(self, name, defaultValue):
        """获取房间配置"""
        return self._roomConf.get(name, defaultValue)

    def getTableConfig(self, name, defaultValue):
        """获取table配置"""
        return self._tableConf.get(name, defaultValue)

    def CheckSeatId(self, seatId, userId=None):
        """校验座位号"""
        seatValid = (seatId >= 0) and (seatId < self.maxSeatN)
        if not seatValid:
            return False

        if not userId:
            return seatValid

        if self.seats[seatId][TYSeat.INDEX_SEATE_USERID] != userId:
            return False

        return True

    def doTableChat(self, userId, seatId, isFace, voiceIdx, chatMsg):
        """doTableChat非父类的接口，可以抽象至麻将的table基类中"""
        ftlog.debug('MajiangQuickTable.doTableChat userId:', userId,
                    ' seatId:', seatId,
                    ' ifFace:', isFace if isFace else "1",
                    ' voiceIdx:', voiceIdx if voiceIdx else "1",
                    ' chatMsg:', chatMsg if chatMsg else "1")

        if 'type' in chatMsg and chatMsg['type'] == 2:
            # 表情
            if not self.process_interactive_expression(userId, seatId, chatMsg):
                return
        # 语音/文字
        self._doTableChat(userId, seatId, isFace, voiceIdx, chatMsg)

    def _doTableChat(self, userId, seatId, isFace, voiceIdx, chatMsg):
        """
        聊天的逻辑
        1）文字聊天
        {
            "cmd": "table_chat",
            "params": {
                "roomId": 7108021001,
                "tableId": 71080210010100,
                "seatId": 1,
                "isFace": 0,
                "msg": {
                    "seatId": 1,
                    "type": 0,
                    "content": "abc"
                },
                "gameId": 710,
                "userId": 10856,
                "clientId": "IOS_3.91_tuyoo.appStore,weixinPay,alipay.0-hall6.appStore.huanle"
            }
        }
        
        2）语音聊天
        {
            "cmd": "table_chat",
            "params": {
                "roomId": 7108021001,
                "tableId": 71080210010100,
                "seatId": 1,
                "isFace": 0,
                "msg": {
                    "seatId": 1,
                    "type": 2,
                    "emoId": 1,
                    "targetSeatId": 0
                },
                "gameId": 710,
                "userId": 10856,
                "clientId": "      IOS_3.91_tuyoo.appStore,weixinPay,alipay.0-hall6.appStore.huanle"
            }
        }
        """
        if not chatMsg:
            return

        if isFace == 0 and 'type' in chatMsg and chatMsg['type'] == 0:  # 麻将文字聊天消息
            content = chatMsg['content']
            filterContent = keywords.replace(content)
            chatMsg['content'] = filterContent

        if isFace == 0:
            users = self.logic_table.getBroadCastUIDs()
            self.logic_table.msgProcessor.table_chat_broadcast(userId, self.gameId, voiceIdx, chatMsg, users)
        else:
            for seat in self.maxSeatN:
                player = self.logic_table.getPlayer(seat)
                self.logic_table.msgProcessor.table_chat_to_face(userId, self.gameId, voiceIdx, chatMsg, player)

    def process_interactive_expression(self, uid, seatId, chat_msg):
        """处理消费金币的表情"""
        targetSeatId = chat_msg.get('targetSeatId', -1)
        if not self.CheckSeatId(targetSeatId, None):
            return False

        target_player_uid = self.seats[targetSeatId][TYSeat.INDEX_SEATE_USERID]
        return MTableExpression.process_interactive_expression(uid
                                                               , self.gameId
                                                               , seatId
                                                               , chat_msg
                                                               , target_player_uid
                                                               , self.getTableConfig('base_chip', 0))

    def _doSit(self, msg, userId, seatId, clientId):
        '''玩家操作, 尝试再当前的某个座位上坐下'''
        ftlog.debug('==_doSit=msg=', msg, ' seatId:', seatId, 'tableId:', self.tableId)
        seatId = self.changeFrameSeatToMJSeatId(seatId)
        self.doSitDown(userId, seatId, msg, clientId)

    def doSitDown(self, userId, seatId, msg, clientId):
        """
        用户坐到某个桌子上，逻辑处理：如果是非重连用户，将用户坐下的消息广播给
        其它已经坐下的用户，然后将当前的桌子信息发送给新来用户
        继承自table类
        这是的seatId为游戏的座位号
        
        返回值：
        1）是否做下
        2）是否断线重连
        """
        ftlog.debug('>>MajiangQuickTable.doSitDown seatId =', seatId, ', userId = ', userId, ' tableId:', self.tableId)

        if (seatId != -1) and (userId != self.seats[seatId][TYSeat.INDEX_SEATE_USERID]):
            onlinedata.removeOnlineLoc(userId, self.roomId, self.tableId)
            ftlog.warn('reconnecting user id is not matched', 'seats =', self.seats, ' tableId:', self.tableId)
            return False

        frameSeatId = self.findIdleSeat(userId)
        ftlog.debug('MajiangQuickTable.doSitDown userId:', userId, ' findSeatId:', frameSeatId)

        sitRe = True
        if 0 == frameSeatId:
            ftlog.debug('MajiangQuickTable.doSitDown now seats:', self.seats)
            sendPopTipMsg(userId, '对不起,该房间已满员')
            self.logic_table.msgProcessor.quick_start_err(userId)
            sitRe = False
        elif 0 > frameSeatId:
            # 补发tableInfo
            seatId = self.getSeatIdByUserId(userId)
            if seatId < 0:
                onlinedata.removeOnlineLoc(userId, self.roomId, self.tableId)
            else:
                self.sendMsgTableInfo(msg, userId, seatId, True)
        elif frameSeatId > 0:
            isReady = self.getTableConfig(MTDefine.READY_AFTER_SIT, 0)
            gameSeatId = self.changeFrameSeatToMJSeatId(frameSeatId)
            # 设置座位的状态
            self.seats[gameSeatId][TYSeat.INDEX_SEATE_USERID] = userId
            # 快速桌用户坐下就是准备状态
            self.seats[gameSeatId][
                TYSeat.INDEX_SEATE_STATE] = TYSeat.SEAT_STATE_READY if isReady else TYSeat.SEAT_STATE_WAIT
            # 添加玩家
            tPlayer = TYPlayer(self, gameSeatId)
            self.players[gameSeatId] = tPlayer
            ftlog.debug('MajiangQuickTable.doSitDown user:', userId
                        , ' seat in:', gameSeatId
                        , ' now seats:', self.seats
                        , ' now playersNum:', self.playersNum)

            # 向牌桌添加用户：联网/机器人
            if TYPlayer.isHuman(userId):
                locResult = onlinedata.addOnlineLoc(userId, self.roomId, self.tableId, frameSeatId)
                ftlog.info('MajiangQuickTable.doSitDown, add online loc userId:', userId
                           , ' roomId:', self.roomId
                           , ' tableId:', self.tableId
                           , ' frameSeatId:', frameSeatId
                           , ' locResult:', locResult)

                _name, _purl, _sex, _coin = userdata.getAttrs(userId, ['name', 'purl', 'sex', 'coin'])
                player = MPlayer(_name, _sex, userId, 0, _purl, _coin, clientId)
                # 快速桌 默认坐下就是准备状态 默认非托管状态
                self.logic_table.addPlayer(player, gameSeatId, isReady, False)
                # 发送location消息
                self.logic_table.msgProcessor.send_location_message(gameSeatId, userId)
            else:
                from difang.majiang2.resource import resource
                robot = resource.getRobotByUserId(userId)
                if robot:
                    player = MPlayer(robot['name'], robot['sex'], userId, 0, robot['purl'], robot['coin'])
                    # 机器人默认准备 默认托管状态
                    self.logic_table.addPlayer(player, gameSeatId, True, True)

            # 座位号调整，框架返回时进行了加1的操作，调整还原
            self.room.updateTableScore(self.getTableScore(), self.tableId)
            self.sendMsgTableInfo(msg, userId, self.getSeatIdByUserId(userId), False)
            if self.playersNum != self.maxSeatN:
                # 一次召唤一个机器人
                self.setTimerOfDispatchRobot()
                uids = self.logic_table.getBroadCastUIDs()
                self.logic_table.msgProcessor.sendTableEvent(self.playersNum, userId, gameSeatId, uids)
            else:
                # 人满了，启动定时器
                self.setTimerHandleAutoDecideAction()

        return sitRe

    def sendMsgTableInfo(self, message, userId, seatId, isReconnect, isHost=False):
        """玩家坐下后，给玩家发送table_info，拉进游戏"""
        self.logic_table.sendMsgTableInfo(seatId, isReconnect)
        if isReconnect:
            self.logic_table.msgProcessor.table_call_latest_msg(seatId)
        self.logic_table.setPlayerLeave(seatId, False)
        self.logic_table.sendEnterMessage()
        self.logic_table.msgProcessor.broadcastUserSit(seatId, userId, isReconnect, isHost,
                                                       self.logic_table.getBroadCastUIDs())

    def setTimerHandleAutoDecideAction(self):
        """定时器，处理托管的行为"""
        ftlog.debug('MajiangQuickTable.setTimerHandleAutoDecideAction tableId:', self.tableId)
        if not self.__looper_timer:
            self.__looper_timer = FTLoopTimer(1, -1, self.handle_auto_decide_action)
        self.__looper_timer.start()

    def setTimerOfDispatchRobot(self):
        """设置定时器加派机器人"""
        ftlog.debug('MajiangQuickTable.setTimerOfDispatchRobot tableId:', self.tableId)
        robotMode = self.getRoomConfig('hasrobot', 1)
        if robotMode != 1:
            return

        message = self.logic_table.msgProcessor.getMsgDispatchRobot(self.playersNum)
        robot_interval = majiang_conf.getRobotInterval(self.gameId)

        self.__timer.setupTimer(self.maxSeatN  # 调用的定时器编号
                                , robot_interval  # 定时时间
                                , message)  # 定时回调的消息

    def _handle_dispatch_virtual_player(self):
        """处理分派机器人"""
        self.__timer.cancelTimer(self.maxSeatN)

        playerCount = runcmd.getMsgPack().getParam('player_count')
        if (self.playersNum == playerCount):
            ftlog.debug("dispatch_virtual_player", playerCount)
            robotRandom = random.randint(1, 9999)
            from difang.majiang2.resource import resource
            robot = resource.getRobot(robotRandom)
            self.doSitDown(robot['userId'], -1, None, 'robot_3.7_-hall6-robot')
        else:
            ftlog.debug('player_count is changed, no need to dispacth virtual player')

    @locked
    def handle_auto_decide_action(self):
        """处理托管"""
        ftlog.debug('$$$$$$$$$$$$$$$$$MajiangQuickTable.handle_auto_decide_action')
        if self.logic_table.isGameOver():
            """游戏结束，通知玩家离开，站起，重置牌桌"""
            ftlog.debug('MajiangQuickTable.handle_auto_decide_action gameOver, clearTable... tableId:', self.tableId)
            self.clearTable(True)
            return

        self.actionHander.updateTimeOut(-1)
        self.actionHander.doAutoAction()

    def _doTableCall(self, msg, userId, seatId, action, clientId):
        """
        继承父类，处理table_call消息
        """
        try:
            ftlog.debug('MajiangQuickTable handle table_call message, tableId:', self.tableId, ' seatId:', seatId,
                        ' action:', action)
            if not self.CheckSeatId(seatId, userId):
                ftlog.warn("handle table_call, seatId is invalid,", action, seatId)
                return

            if action == 'play':
                # 出牌
                self.actionHander.handleTableCallPlay(userId, seatId, msg)
            elif action == 'chi':
                # 吃牌
                self.actionHander.handleTableCallChi(userId, seatId, msg)
            elif action == 'peng':
                # 碰牌
                self.actionHander.handleTableCallPeng(userId, seatId, msg)
            elif action == 'gang':
                # 杠牌
                self.actionHander.handleTableCallGang(userId, seatId, msg)
            elif action == 'grabTing':
                # 抢听
                self.actionHander.handleTableCallGrabTing(userId, seatId, msg)
            elif action == 'win':
                # 和牌
                self.actionHander.handleTableCallWin(userId, seatId, msg)
            elif action == 'pass':
                # 过牌
                self.actionHander.handleTableCallpass(userId, seatId, msg)
            elif action == 'dispatch_virtual_player':
                # 分配机器人
                self._handle_dispatch_virtual_player()
            elif action == 'grabHuGang':
                # 抢杠和
                self.actionHander.handleTableCallGrabHuGang(userId, seatId, msg)
            elif action == 'fanpigu':
                self.actionHander.handleTableCallFanpigu(userId, seatId, msg)
            elif action == 'ping':
                # 获取网速
                self.actionHander.handleTableCallPing(userId, seatId, msg)
            elif action == 'exchange':
                # 换牌
                self.actionHander.handleTableCallExchange(userId, seatId, msg)
            else:
                ftlog.debug('MajiangQuickTable._doTableCall unprocessed message:', msg)
        except:
            ftlog.error("_doTableCall error clear table")
            self.clearTable(True)

    def kickOffUser(self, userId, seatId, sendLeave):
        """让一个玩家leave"""
        ftlog.debug('MajiangQuickTable.kickOffUser userId:', userId, ' seatId:', seatId)
        onlinedata.removeOnlineLoc(userId, self.roomId, self.tableId)
        # uids = self.logic_table.getBroadCastUIDs()
        # 临时注释掉 待整体确认 taoxc
        # self.logic_table.msgProcessor.table_leave(userId, seatId, uids)
        # 游戏开始之后的退出，客户端不需要再收到退出消息 客户端的退出由其自身控制 sendLeave = False
        # 游戏未开始时房主解散了房间才需要向客户端发消息 sendLeave = True
        if sendLeave:
            uids = self.logic_table.getBroadCastUIDs()
            self.logic_table.msgProcessor.create_table_dissolve(userId, seatId, 'dissolve', uids)
        self.logic_table.removePlayer(seatId)
        self.seats[seatId] = TYSeat(self)
        self.players[seatId] = None

    def _doLeave(self, msg, userId, clientId):
        reason = msg.getParam("reason", TYRoom.LEAVE_ROOM_REASON_ACTIVE)
        ftlog.debug("majiang_quick_table_doLeave msg:", msg)
        if reason == TYRoom.LEAVE_ROOM_REASON_LOST_CONNECTION:
            self.logic_table.sendLeaveMessage(userId)
            return {"isOK": False, "reason": reason}

    def _doStandUp(self, msg, userId, seatId, reason, clientId):
        '''
        玩家操作, 尝试离开当前的座位
        子类需要自行判定userId和seatId是否吻合
        快速麻将桌的站起比较简单
        牌局没开始，站起
        牌局已开始，不处理，超时托管
        '''
        if self.logic_table.isPlaying():
            # 用户托管
            ftlog.debug('MajiangQuickTable.standup, user stand up, set trustTee...')
            self.logic_table.setAutoDecideValue(seatId, True)
        else:
            ftlog.info('MajiangQuickTable.standup removeOnlineLoc userId:', userId
                       , ' roomId:', self.roomId
                       , ' tableId:', self.tableId
                       , ' seatId:', seatId
                       , ' reason:', reason)
            self.kickOffUser(userId, seatId, True)

    def _doTableManage(self, msg, action):
        '''桌子内部处理所有的table_manage命令'''
        ftlog.debug("majiang_quick_table_doTableManage msg:", msg, "action", action)
        result = {'isOK': True}
        if action == 'leave':
            userId = msg.getParam('userId')
            self.logic_table.sendLeaveMessage(userId)
            seatId = self.getSeatIdByUserId(userId)
            if seatId >= 0:
                self.logic_table.setPlayerLeave(seatId, True)
                self._doStandUp(None, userId, seatId, -1, '')
        elif action == 'clear_table':
            self.clearTable(True)
        elif action == 'tableTiles':
            if self.logic_table.isPlaying():
                self.logic_table.printTableTiles()
        return result

    def getSeatIdByUserId(self, userId):
        """根据userId获取座位号"""
        for index in range(self.maxSeatN):
            if self.seats[index][TYSeat.INDEX_SEATE_USERID] == userId:
                return index
        return -1

    def clearTable(self, sendLeave):
        """清理桌子"""
        ftlog.debug('MajiangQuickTable.clearTable tableId:', self.tableId
                    , ' now seats: ', self.seats)
        self.__timer.cancelTimerAll()
        if self.__looper_timer:
            self.__looper_timer.cancel()
            self.__looper_timer = None
        # 清理用户座位
        for seatId in range(self.maxSeatN):
            if self.seats[seatId][TYSeat.INDEX_SEATE_USERID] != 0:
                self.kickOffUser(self.seats[seatId][TYSeat.INDEX_SEATE_USERID], seatId, sendLeave)
        # 结束游戏
        self.logic_table.reset()

        # 释放桌子
        self.room.updateTableScore(self.getTableScore(), self.tableId)

    def saveRecordAfterClear(self, score):
        """score为每盘的分的数组,形如[[-1,0,1,0],[2,1,1,0]]"""
        scoreInfo = {}

        ftlog.debug("saveRecordAfterClear score:", score)
        playerCount = self.logic_table.playerCount
        sendScore = [[] for _ in range(playerCount)]
        for roundScore in score:
            for i in range(0, playerCount):
                sendScore[i].append(roundScore[i])
        ftlog.debug("saveRecordAfterClear sendScore:", sendScore)
        ftId = self.logic_table.tableConfig[MFTDefine.FTID]
        for i in range(0, playerCount):
            cp = self.logic_table.player[i]
            if cp:
                if 'budget' not in scoreInfo:
                    scoreInfo['budget'] = {}
                import time
                if 'time' not in scoreInfo:
                    scoreInfo['time'] = int(time.time())
                if 'playMode' not in scoreInfo:
                    scoreInfo['playMode'] = self.playMode
                if 'tableId' not in scoreInfo:
                    scoreInfo['tableId'] = self.tableId
                if 'tableNo' not in scoreInfo:
                    scoreInfo['tableNo'] = ftId
                if 'defaultScore' not in scoreInfo:
                    scoreInfo['defaultScore'] = 1
                if 'recordUrls' not in scoreInfo:
                    scoreInfo['recordUrls'] = self.logic_table.recordUrls
                if cp.userId not in scoreInfo['budget']:
                    scoreInfo['budget'][cp.userId] = {}
                scoreInfo['budget'][cp.userId]['uid'] = cp.userId
                scoreInfo['budget'][cp.userId]['name'] = cp.name
                scoreInfo['budget'][cp.userId]['score'] = sendScore[i]
                if self.logic_table.tableResult:
                    if self.logic_table.tableResult.score:
                        scoreInfo['budget'][cp.userId]['deltaScoreList'] = \
                            self.logic_table.tableResult.score[i]
                    else:
                        scoreInfo['budget'][cp.userId]['deltaScoreList'] = 0
                else:
                    scoreInfo['budget'][cp.userId]['deltaScoreList'] = 0
        MJCreateTableRecord.saveRecord(scoreInfo, ftId, self.gameId)
