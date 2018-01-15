# coding=UTF-8
'''处理quick_start请求
'''
import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack
from poker.entity.configure import gdata, pokerconf
from poker.entity.dao import onlinedata, userchip
from poker.entity.game.rooms.room import TYRoom
from poker.entity.game.rooms.room_mixin import TYRoomMixin
from poker.util import strutil

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

_CANDIDATE_ROOM_IDS = {}


class BaseQuickStartDispatcher(object):
    '''按clientId分发快速开始请求
    '''

    @classmethod
    def dispatchQuickStart(cls, msg, userId, gameId, roomId, tableId, playMode, clientId):
        return BaseQuickStart.onCmdQuickStart(msg, userId, gameId, roomId, tableId, playMode, clientId)


class BaseQuickStart(object):
    '''快速开始处理基类'''

    @classmethod
    def onCmdQuickStart(cls, msg, userId, gameId, roomId, tableId, playMode, clientId):
        '''UT server中处理来自客户端的quick_start请求  
        Args:
            msg
                cmd : quick_start
                if roomId == 0:
                    表示快速开始，服务器为玩家选择房间，然后将请求转给GR
                    
                if roomId > 0 and tableId == 0 : 
                    表示玩家选择了房间，将请求转给GR
                    
                if roomId > 0 and tableId == roomId * 10000 :
                    表示玩家在队列里断线重连，将请求转给GR
                    
                if roomId > 0 and tableId > 0:
                    if onlineSeatId > 0: 
                        表示玩家在牌桌里断线重连，将请求转给GT
                    else:
                        表示玩家选择了桌子，将请求转给GR
        '''
        assert isinstance(userId, int) and userId > 0
        assert isinstance(roomId, int) and roomId >= 0
        assert isinstance(tableId, int) and tableId >= 0

        if ftlog.is_debug():
            ftlog.debug("<< |clientId:", clientId,
                        "|userId, roomId, tableId:", userId, roomId, tableId,
                        "|gameId, playMode:", gameId, playMode, caller=cls)

        # 单开, 无论何时quick_start进入都检查loc
        if not pokerconf.isOpenMoreTable(clientId):
            loc = onlinedata.checkUserLoc(userId, clientId, gameId)
            if ftlog.is_debug():
                ftlog.debug('old client, checkUserLoc->', loc, caller=cls)
            if isinstance(loc, basestring):
                lgameId, lroomId, ltableId, lseatId = loc.split('.')
                lgameId, lroomId, ltableId, lseatId = strutil.parseInts(lgameId, lroomId, ltableId, lseatId)
                if lgameId == gameId and lroomId > 0:
                    ftlog.debug('onCmdQuickStart re-connected |userId, loc:', userId, loc,
                                '|roomId, tableId:', roomId, tableId, caller=cls)
                    roomId = lroomId
                    tableId = ltableId
                    msg.setParam('isReConnected', True)
                    if ftlog.is_debug():
                        ftlog.debug('old client, reset roomId, tableId->', roomId, tableId, caller=cls)

        if roomId == 0:  # 玩家点击快速开始
            chosenRoomId, checkResult = cls._chooseRoom(userId, gameId, playMode)
            ftlog.debug("after choose room", "|userId, chosenRoomId, checkResult:", userId, chosenRoomId, checkResult,
                        caller=cls)
            if checkResult == TYRoom.ENTER_ROOM_REASON_OK:
                TYRoomMixin.queryRoomQuickStartReq(msg, chosenRoomId, 0)  # 请求转给GR
            else:
                candidateRoomIds = cls._getCandidateRoomIds(gameId, playMode)
                if candidateRoomIds:
                    rid = candidateRoomIds[0]
                    msg.setParam('candidateRoomId', rid)
                cls._onEnterRoomFailed(msg, checkResult, userId, clientId, roomId)
            return

        bigRoomId = gdata.getBigRoomId(roomId)
        ftlog.debug('bigRoomId:', bigRoomId)
        if bigRoomId == 0:
            cls._onEnterRoomFailed(msg, TYRoom.ENTER_ROOM_REASON_ROOM_ID_ERROR, userId, clientId, roomId)
            return

        if strutil.getGameIdFromBigRoomId(bigRoomId) != gameId:
            cls._onEnterRoomFailed(msg, TYRoom.ENTER_ROOM_REASON_ROOM_ID_ERROR, userId, clientId, roomId)
            return

        if tableId == 0:  # 玩家只选择了房间
            if gameId == 6 and roomId != bigRoomId:
                ctrlRoomId = gdata.roomIdDefineMap()[roomId].parentId
                queryRoomId = roomId
            else:
                ctrRoomIds = gdata.bigRoomidsMap()[bigRoomId]
                ctrlRoomId = ctrRoomIds[userId % len(ctrRoomIds)]
                queryRoomId = ctrlRoomId
            reason = cls._canQuickEnterRoom(userId, gameId, ctrlRoomId, 1)
            if reason == TYRoom.ENTER_ROOM_REASON_OK:
                if gameId == 6:
                    TYRoomMixin.queryRoomQuickStartReq(msg, queryRoomId, 0)  # 请求转给GR或GT
                else:
                    TYRoomMixin.queryRoomQuickStartReq(msg, ctrlRoomId, 0)  # 请求转给GR或GT
            elif reason == TYRoom.ENTER_ROOM_REASON_LESS_MIN or reason == TYRoom.ENTER_ROOM_REASON_GREATER_MAX:
                if gameId == 6:
                    innerTable = msg.getParam("innerTable", 0)  # innerTable 区分不同版本弹窗
                    if innerTable == 1:
                        roomDef = gdata.roomIdDefineMap()[ctrlRoomId]
                        playMode = roomDef.configure.get('playMode', None)
                        if ftlog.is_debug():
                            ftlog.debug('enter_less_min userId=', userId, 'roomId=', ctrlRoomId, 'msg=', msg,
                                        'playmode=', playMode)
                        msgpack = MsgPack()
                        msgpack.setCmd("quick_start")
                        msgpack.setParam("userId", userId)
                        msgpack.setParam("gameId", gameId)
                        msgpack.setParam("clientId", clientId)
                        msgpack.setParam("innerTable", 1)
                        msgpack.setParam("apiver", msg.getParam("apiver", 3.7))
                        cls.onCmdQuickStart(msgpack, userId, gameId, 0, 0, playMode, clientId)
                        if ftlog.is_debug():
                            ftlog.debug('reenter_less_min userId=', userId, 'roomId=', ctrlRoomId, 'msgpack=',
                                        msgpack.pack())
                    else:
                        cls._onEnterRoomFailed(msg, reason, userId, clientId, roomId)
                else:
                    cls._onEnterRoomFailed(msg, reason, userId, clientId, roomId)
            else:
                cls._onEnterRoomFailed(msg, reason, userId, clientId, roomId)
            return

        if tableId == roomId * 10000:  # 玩家在队列里断线重连
            TYRoomMixin.queryRoomQuickStartReq(msg, roomId, tableId)  # 请求转给GR
            return

        onlineSeat = onlinedata.getOnlineLocSeatId(userId, roomId, tableId)

        if onlineSeat:
            if onlineSeat == gdata.roomIdDefineMap()[roomId].configure['tableConf']['maxSeatN'] + 1:
                # 牌桌里旁观的玩家断线重连，请求转给GT
                TYRoomMixin.sendTableCallObserveReq(userId, roomId, tableId, clientId)
            else:
                # 牌桌里坐着的玩家断线重连，请求转给GT
                # TYRoomMixin.querySitReq(userId, roomId, tableId, clientId) # GT人多时会有超时异常
                TYRoomMixin.sendSitReq(userId, roomId, tableId, clientId)
        else:  # 玩家选择了桌子, 
            shadowRoomId = tableId / 10000
            ctrRoomId = gdata.roomIdDefineMap()[shadowRoomId].parentId
            TYRoomMixin.queryRoomQuickStartReq(msg, ctrRoomId, tableId, shadowRoomId=shadowRoomId)  # 请求转给GR

            #         try :
            #         except AssertionError :
            #             ftlog.error(getMethodName(), "online loc error", "|clientId:", clientId,
            #                 "|userId, roomId, tableId:", userId, roomId, tableId,
            #                 "|onlineSeat:", onlineSeat)

    @classmethod
    def _chooseRoom(cls, userId, gameId, playMode):
        '''服务端为玩家选择房间'''
        candidateRoomIds = cls._getCandidateRoomIds(gameId, playMode)
        if ftlog.is_debug():
            ftlog.debug("<<|candidateRoomIds:", candidateRoomIds, 'playMode=', playMode, caller=cls)

        for roomId in candidateRoomIds:
            ret = cls._canQuickEnterRoom(userId, gameId, roomId, 0)
            if ftlog.is_debug():
                ftlog.debug("|roomId, ret:", roomId, ret, caller=cls)
            if ret == TYRoom.ENTER_ROOM_REASON_OK:
                return roomId, TYRoom.ENTER_ROOM_REASON_OK

        return 0, TYRoom.ENTER_ROOM_REASON_LESS_MIN

    @classmethod
    def _onEnterRoomFailed(cls, msg, checkResult, userId, clientId, roomId=0):
        '''进入房间失败回调函数'''
        ftlog.warn("|userId, reason:", userId, checkResult, caller=cls)  # 调用最小房间金币不够充值提醒的todotask

    @classmethod
    def _initCandidateRoomIdsByGameId(cls, gameId):

        roomids = {'': []}
        ctlRoomIds = [bigRoomId * 10000 + 1000 for bigRoomId in gdata.gameIdBigRoomidsMap().get(gameId, [])]
        for ctlRoomId in ctlRoomIds:
            roomDef = gdata.roomIdDefineMap()[ctlRoomId]
            playMode = roomDef.configure.get('playMode', '')
            ismatch = roomDef.configure.get('ismatch', 0)
            if ismatch == 0:
                sortVal = roomDef.configure.get('quickIndex', 0)
                if not playMode in roomids:
                    roomids[playMode] = []
                roomids[playMode].append([ctlRoomId, sortVal])

        croomids = {}
        allids = []
        for k, v in roomids.items():
            v.sort(key=lambda x: x[1])
            rids = [x[0] for x in v]
            croomids[k] = rids
            allids.extend(rids)
            ftlog.debug('_initCandidateRoomIds->', gameId, k, '=', croomids[k])

        allids.sort()
        croomids['_all_'] = allids
        ftlog.debug('_initCandidateRoomIds->', gameId, '_all_', '=', croomids['_all_'])

        return croomids

    @classmethod
    def _initCandidateRoomIds(cls):
        global _CANDIDATE_ROOM_IDS
        croomids = {}
        for gameId in gdata.gameIds():
            roomids = cls._initCandidateRoomIdsByGameId(gameId)
            croomids[gameId] = roomids
        _CANDIDATE_ROOM_IDS = croomids

    @classmethod
    def _getCandidateRoomIds(cls, gameId, playMode):
        global _CANDIDATE_ROOM_IDS
        if not _CANDIDATE_ROOM_IDS:
            cls._initCandidateRoomIds()

        gamePlays = _CANDIDATE_ROOM_IDS.get(gameId, {})
        ctlRoomIds = gamePlays.get(playMode, [])
        if not ctlRoomIds:
            ctlRoomIds = gamePlays.get('_all_', [])
        return ctlRoomIds

    @classmethod
    def _canQuickEnterRoom(cls, userId, gameId, roomId, isOnly):

        try:
            chip = userchip.getChip(userId)
            if ftlog.is_debug():
                ftlog.debug(gdata.roomIdDefineMap()[roomId].configure)
            roomConfig = gdata.roomIdDefineMap()[roomId].configure
            if ftlog.is_debug():
                ftlog.debug('userId =', userId,
                            'minCoin =', roomConfig.get('minCoin'),
                            'maxCoin =', roomConfig.get('maxCoin'),
                            'minCoinQS =', roomConfig.get('minCoinQS'),
                            'maxCoinQS =', roomConfig.get('maxCoinQS'),
                            'chip =', chip,
                            'isOnly =', isOnly)
            if isOnly:
                minCoinQs = roomConfig['minCoin']
                maxCoinQs = roomConfig['maxCoin']
            else:
                minCoinQs = roomConfig['minCoinQS']
                maxCoinQs = roomConfig['maxCoinQS']
            ismatch = roomConfig.get('ismatch')

            if ismatch or minCoinQs <= 0:
                return TYRoom.ENTER_ROOM_REASON_NOT_QUALIFIED

            if ftlog.is_debug():
                ftlog.debug('roomId =', roomId, 'minCoinQs =', minCoinQs,
                            'maxCoinQs =', maxCoinQs, 'chip =', chip,
                            caller=cls)

            if chip < minCoinQs:
                return TYRoom.ENTER_ROOM_REASON_LESS_MIN
            if maxCoinQs > 0 and chip >= maxCoinQs:
                return TYRoom.ENTER_ROOM_REASON_GREATER_MAX

            return TYRoom.ENTER_ROOM_REASON_OK

        except Exception as e:
            ftlog.error(e)
            return TYRoom.ENTER_ROOM_REASON_INNER_ERROR
