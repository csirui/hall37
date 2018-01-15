# -*- coding=utf-8 -*-
'''
Created on 2015年9月28日

@author: liaoxx
'''

import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from difang.majiang2.entity import majiang_conf
from difang.majiang2.entity.create_table import CreateTableData
from difang.majiang2.entity.create_table_record import MJCreateTableRecord
from difang.majiang2.entity.quick_start import MajiangQuickStartDispatcher, \
    MajiangCreateTable
from difang.majiang2.entity.util import sendPopTipMsg
from freetime.entity.msg import MsgPack
from hall.entity.todotask import TodoTaskEnterGameNew, TodoTaskHelper
from hall.servers.common.base_checker import BaseMsgPackChecker
from poker.entity.configure import gdata
from poker.entity.dao import onlinedata, gamedata
from poker.protocol import runcmd, router
from poker.util import strutil


class GameTcpHandler(BaseMsgPackChecker):
    def __init__(self):
        pass

    def _check_param_sessionIndex(self, msg, key, params):
        sessionIndex = msg.getParam(key)
        if isinstance(sessionIndex, int) and sessionIndex >= 0:
            return None, sessionIndex
        return None, -1

    def _check_param_match_id(self, msg, key, params):
        match_id = msg.getParam("match_id")
        if match_id and isinstance(match_id, (str, unicode)):
            return None, match_id
        return 'ERROR of match_id !' + str(match_id), None

    def doGameQuickStart(self, userId, gameId, clientId, roomId0, tableId0, playMode, sessionIndex):
        '''
        TCP 发送的至UTIL服务的quick_start暂时不能用lock userid的方式, 
        因为,消息流 CO->UT->GR->GT->UT会死锁
        '''
        msg = runcmd.getMsgPack()
        ftlog.debug('doGameQuickStart', userId, gameId, clientId, roomId0, tableId0, playMode, sessionIndex,
                    caller=self)
        if not playMode and roomId0 <= 0 and tableId0 <= 0:
            try:
                # 前端对于sessionIndex是写死的, 不会更具hall_info中的顺序改变而改变
                if sessionIndex == 0:
                    playMode = majiang_conf.PLAYMODE_GUOBIAO
                elif sessionIndex == 1:
                    playMode = majiang_conf.PLAYMODE_SICHUAN
                elif sessionIndex == 2:
                    playMode = majiang_conf.PLAYMODE_GUOBIAO_EREN
                elif sessionIndex == 3:
                    playMode = majiang_conf.PLAYMODE_HARBIN
                elif sessionIndex == 4:
                    playMode = majiang_conf.PLAYMODE_SICHUAN_DQ
                elif sessionIndex == 5:
                    playMode = majiang_conf.PLAYMODE_SICHUAN_XLCH
                elif sessionIndex == 6:
                    playMode = majiang_conf.PLAYMODE_GUOBIAO_VIP
                else:
                    playMode = majiang_conf.PLAYMODE_GUOBIAO
                msg.setParam('playMode', playMode)  # 透传playMode, 以便发送高倍房引导弹窗
            except:
                ftlog.error('doGameQuickStart', msg)
            ftlog.debug('doGameQuickStart sessionIndex=', sessionIndex, 'playMode=', playMode)

        if roomId0 < 1000:
            roomIdx = roomId0
            roomId0 = 0
            ftlog.info("quickstart roomID error, from %d change to %d" % (roomIdx, roomId0))

        MajiangQuickStartDispatcher.dispatchQuickStart(msg, userId, gameId, roomId0, tableId0, playMode, clientId)
        if router.isQuery():
            mo = runcmd.newOkMsgPack(1)
            router.responseQurery(mo, '', str(userId))

    def doAwardCertificate(self, userId, gameId, match_id, clientId):
        '''
        TCP 发送的至UTIL服务的quick_start暂时不能用lock userid的方式, 
        因为,消息流 CO->UT->GR->GT->UT会死锁
        '''
        msg = runcmd.getMsgPack()
        roomId = msg.getParam("roomId")
        ftlog.debug('doAwardCertificate', userId, gameId, roomId, match_id, caller=self)
        if len(str(roomId)) != 4 and len(str(roomId)) != 8 and len(str(roomId)) != 0:
            roomIdx = roomId
            roomId = roomId * 100
            ftlog.info("doAwardCertificate roomID error, from %d change to %d" % (roomIdx, roomId))

        allrooms = gdata.roomIdDefineMap()
        ctrlRoomId = roomId
        if roomId in allrooms:
            roomDef = allrooms[roomId]
            if roomDef.parentId > 0:  # this roomId is shadowRoomId
                ctrlRoomId = roomDef.parentId
        else:
            ftlog.warn("doAwardCertificate, error roomId", roomId)
            return

        ftlog.debug("ctrlRoomId:", ctrlRoomId)

        msg1 = MsgPack()
        msg1.setCmd('room')
        msg1.setParam('gameId', gameId)
        msg1.setParam('userId', userId)
        msg1.setParam('roomId', ctrlRoomId)
        msg1.setParam('action', "match_award_certificate")
        msg1.setParam('match_id', match_id)
        msg1.setParam('clientId', clientId)
        router.sendRoomServer(msg1, roomId)
        if router.isQuery():
            mo = runcmd.newOkMsgPack(1)
            router.responseQurery(mo, '', str(userId))

    def doGetCreatTableInfo(self, userId, gameId, clientId):
        """获取创建牌桌配置信息
        """
        ftlog.debug('doGetCreatTableInfo | userId gameId clientId:', userId, gameId, clientId)
        configList = []
        config = majiang_conf.getCreateTableTotalConfig(gameId)
        for playMode in config:
            ftlog.debug('doGetCreatTableInfo playMode:', playMode)
            pConfig = config.get(playMode)
            pConfig['playMode'] = playMode
            configList.append(pConfig)
        ftlog.debug('doGetCreatTableInfo configList:', configList)

        mo = MsgPack()
        mo.setCmd("create_table")
        mo.setResult('action', 'info')
        mo.setResult('gameId', gameId)
        mo.setResult('userId', userId)
        mo.setResult('list', configList)
        router.sendToUser(mo, userId)

    def _canEnterGame(self, userId, gameId):
        """是否可进入游戏"""
        gameTime = gamedata.getGameAttrInt(userId, gameId, 'createTableTime')
        nowTime = pktimestamp.getCurrentTimestamp()
        ftlog.debug('Majiang2 game_handler _canEnterGame gameTile:', gameTime
                    , ' nowTime:', nowTime)
        return (nowTime - gameTime) >= 5

    def doCreateTable(self, userId, gameId, clientId, roomId0, tableId0, playMode):
        """
        房主创建牌桌
        """
        if not playMode:
            ftlog.error('game_handler, cat not create table without playMode...')

        loc = onlinedata.checkUserLoc(userId, clientId, gameId)
        lgameId, lroomId, ltableId, lseatId = loc.split('.')
        lgameId, lroomId, ltableId, lseatId = strutil.parseInts(lgameId, lroomId, ltableId, lseatId)
        if lgameId > 0 and lroomId > 0 and ltableId > 0 and lseatId >= 0:
            ftlog.warn('create_table error, user in table', lgameId, lroomId, ltableId, lseatId)
            sendPopTipMsg(userId, "请稍候,正在进桌...")
            config = {
                "type": "quickstart",
                "pluginParams": {
                    "roomId": lroomId,
                    "tableId": ltableId,
                    "seatId": lseatId
                }
            }
            todotask = TodoTaskEnterGameNew(lgameId, config)
            mo = MsgPack()
            mo.setCmd('todo_tasks')
            mo.setResult('gameId', gameId)
            mo.setResult('pluginId', lgameId)
            mo.setResult('userId', userId)
            mo.setResult('tasks', TodoTaskHelper.encodeTodoTasks(todotask))
            router.sendToUser(mo, userId)
        elif self._canEnterGame(userId, gameId):
            # 保存建桌时间戳
            gamedata.setGameAttr(userId, gameId, 'createTableTime', pktimestamp.getCurrentTimestamp())

            msg = runcmd.getMsgPack()
            itemParams = msg.getParam("itemParams")
            # cardCount为总局数
            if "cardCount" in itemParams:
                cardCountId = itemParams.get('cardCount', 0)
                cardCountConfig = majiang_conf.getCreateTableConfig(gameId, playMode, 'cardCount', cardCountId)
                fangka_count = cardCountConfig.get('fangka_count', 1)
                ftlog.debug('MajiangCreateTable.create_table fangka_count:', fangka_count)

                playerCount = 4
                playerTypeId = itemParams.get('playerType', 1)
                if playerTypeId:
                    playerTypeConfig = majiang_conf.getCreateTableConfig(gameId, playMode, 'playerType', playerTypeId)
                    playerCount = playerTypeConfig.get('count', 4)
                    ftlog.debug('MajiangCreateTable.create_table playerCount:', playerCount)

                msg.setParam('isCreateTable', 1)  # 标记创建的桌子是 自建桌
                from poker.entity.game.rooms.room import TYRoom
                roomId, checkResult = MajiangCreateTable._chooseCreateRoom(userId, gameId, playMode, playerCount)
                ftlog.debug('MajiangCreateTable._chooseCreateRoom roomId:', roomId, ' checkResult:', checkResult)

                if checkResult == TYRoom.ENTER_ROOM_REASON_OK:
                    msg = runcmd.getMsgPack()
                    msg.setCmdAction("room", "create_table")
                    msg.setParam("roomId", roomId)
                    msg.setParam("itemParams", itemParams)
                    msg.setParam('needFangka', fangka_count)
                    ftlog.debug('MajiangCreateTable._chooseCreateRoom send message to room:', msg)

                    router.sendRoomServer(msg, roomId)
                else:
                    sendPopTipMsg(userId, "暂时无法创建请稍后重试")
            else:
                sendPopTipMsg(userId, "暂时无法创建请稍后重试")

            if router.isQuery():
                mo = runcmd.newOkMsgPack(1)
                router.responseQurery(mo, '', str(userId))
        else:
            ftlog.info('majiang2 game_handler, ignore enter game request...')

    def doJoinCreateTable(self, userId, gameId, clientId, roomId0, tableId0, playMode):
        """用户加入自建牌桌
        """
        loc = onlinedata.checkUserLoc(userId, clientId, gameId)
        lgameId, lroomId, ltableId, lseatId = loc.split('.')
        lgameId, lroomId, ltableId, lseatId = strutil.parseInts(lgameId, lroomId, ltableId, lseatId)
        if lgameId > 0 and lroomId > 0 and ltableId > 0 and lseatId >= 0:
            ftlog.warn('create_table error, user in table')
            sendPopTipMsg(userId, "请稍候,正在进桌...")
            config = {
                "type": "quickstart",
                "pluginParams": {
                    "roomId": lroomId,
                    "tableId": ltableId,
                    "seatId": lseatId
                }
            }
            todotask = TodoTaskEnterGameNew(lgameId, config)
            mo = MsgPack()
            mo.setCmd('todo_tasks')
            mo.setResult('gameId', gameId)
            mo.setResult('pluginId', lgameId)
            mo.setResult('userId', userId)
            mo.setResult('tasks', TodoTaskHelper.encodeTodoTasks(todotask))
            router.sendToUser(mo, userId)
        else:
            msg = runcmd.getMsgPack()
            createTableNo = msg.getParam('createTableNo', 0)
            if not createTableNo:
                return
            tableId0, roomId0 = CreateTableData.getTableIdByCreateTableNo(createTableNo)
            if not tableId0 or not roomId0:
                sendPopTipMsg(userId, "找不到您输入的房间号")
                return
            msg = runcmd.getMsgPack()
            msg.setParam("shadowRoomId", roomId0)
            msg.setParam("roomId", roomId0)
            msg.setParam("tableId", tableId0)
            msg.setCmdAction("room", "join_create_table")
            router.sendRoomServer(msg, roomId0)

            if router.isQuery():
                mo = runcmd.newOkMsgPack(1)
                router.responseQurery(mo, '', str(userId))

    def doGetCreateTableRecord(self, userId, gameId, clientId):
        """全量请求牌桌记录
        """
        MJCreateTableRecord.sendAllRecordToUser(userId, gameId)
        if router.isQuery():
            mo = runcmd.newOkMsgPack(1)
            router.responseQurery(mo, '', str(userId))
