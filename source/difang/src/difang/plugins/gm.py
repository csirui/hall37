# coding=UTF-8


__author__ = ['WangTao']

import difang.entity.util as utils
import freetime.util.log as ftlog
from hall.entity import hallvip
from poker.entity.configure import gdata
from poker.entity.dao import daobase
from poker.entity.dao import daoconst
from poker.entity.dao import userdata
from poker.protocol import router
from poker.util import strutil


class GM(object):
    '''
    '''

    def __init__(self, gameId):
        self.gameId = gameId

    def event_handle(self, gameId):
        return {
            'EV_HTTP_COMMON_REQUEST': self.onEvHttpCommonRequest,
            ('EV_ROOM_GM', 'gm'): self.onEvRoomGm,
            # ('EV_TABLE_GM', 'gm'): self.onEvTableGm,
            ('table', 'gm'): self.onEvTableGm,
        }

    def onEvHttpCommonRequest(self, gameId, msg):
        ''' 处理 http 消息
        这个函数只运行在 HT 里。负责处理一些自己能处理的，其它的息转发给 GR, GT
        '''
        httpRequest, httpArgs = msg.getParams('httpRequest', 'httpArgs')
        httpResult = msg.getResult('httpResult')
        for k, v in httpArgs.items():
            if len(v) == 1:
                httpArgs[k] = v[0]
        if ftlog.is_debug():
            ftlog.debug('httpArgs', gameId, httpArgs, caller=self)

        action = httpArgs.get('a')
        if action != 'gm':
            return

        sa = httpArgs.get('sa')
        if not sa:
            if ftlog.is_debug():
                ftlog.debug('sa is None')
            return

        if sa == 'roomlist':
            self._do_http_gm_room_list(gameId, httpRequest, httpArgs, httpResult)
        elif sa == 'playingTableList':
            self._do_http_gm_playing_table_list(gameId, httpRequest, httpArgs, httpResult)
        elif sa == 'tableDetail':
            self._do_http_gm_table_detail(gameId, httpRequest, httpArgs, httpResult)

    def _do_http_gm_room_list(self, gameId, httpRequest, httpArgs, httpResult):
        '''获取房间列表'''

        roomOnlineInfos = daobase._executeBiCmd('HGETALL', daoconst.BI_KEY_ROOM_ONLINES % (gameId))
        roomOnlineInfos = dict(utils.pairwise(roomOnlineInfos))
        bigRoomOnlineInfos = {}
        for roomId, onlineInfo in roomOnlineInfos.items():
            bigRoomId = gdata.getBigRoomId(roomId)
            tcs = map(int, onlineInfo.split('|'))
            ucount, tcount = tcs[0], tcs[-1]
            if bigRoomId not in bigRoomOnlineInfos:
                bigRoomOnlineInfos[bigRoomId] = [0, 0]
            bigRoomOnlineInfos[bigRoomId][0] += ucount
            bigRoomOnlineInfos[bigRoomId][1] += tcount

        roomList = []

        for bigRoomId in gdata.gameIdBigRoomidsMap()[gameId]:
            ctrlRoomId = gdata.bigRoomidsMap()[bigRoomId][0]
            roomDefine = gdata.roomIdDefineMap()[ctrlRoomId]
            ucount, tcount = bigRoomOnlineInfos.get(roomDefine.bigRoomId, [0, 0])
            roomInfo = {
                'bigRoomId': bigRoomId,
                'tableCount': roomDefine.configure['gameServerCount'] * roomDefine.configure['gameTableCount'],
                'name': roomDefine.configure['tableConf'].get('tname', ''),
                'playingPlayers': ucount,
                'playingTables': tcount,
            }
            roomList.append(roomInfo)
        httpResult['roomList'] = roomList

    def _do_http_gm_playing_table_list(self, gameId, httpRequest, httpArgs, httpResult):
        '''获取某个房间正在玩的牌桌列表'''

        bigRoomId = int(httpArgs['bigRoomId'])
        ctrlRoomIds = gdata.bigRoomidsMap()[bigRoomId]
        playingTableList = []

        for ctrlRoomId in ctrlRoomIds:
            roomDef = gdata.roomIdDefineMap()[ctrlRoomId]
            for shadowRoomId in roomDef.shadowRoomIds:
                msg = utils.updateMsg(cmd='table', params={
                    'action': 'gm',
                    'sa': 'playingTableList',
                    'gameId': gameId,
                    'roomId': shadowRoomId,
                    'tableId': shadowRoomId * 10000 + 1,
                })
                ret = router.queryTableServer(msg, shadowRoomId)
                ftlog.debug('_do_http_gm_playing_table_list| shadowRoomId, ret:', shadowRoomId, ret)
                playingTableList += strutil.loads(ret)['result']['playingTableList']
        httpResult['playingTableList'] = playingTableList

    def _do_http_gm_table_detail(self, gameId, httpRequest, httpArgs, httpResult):
        '''获取某牌桌的详情'''

        roomId = int(httpArgs['roomId'])
        tableId = int(httpArgs['tableId'])
        username = httpArgs.get('username')
        password = httpArgs.get('password')
        if username and password:
            token = daobase.executeMixCmd('HGET', '8:gm:token', username) == password
        else:
            token = False

        ftlog.info('GM._do_http_gm_table_detail << |',
                   'roomId, tableId, username, token', roomId, tableId, username, token)

        msg = utils.updateMsg(cmd='table', params={
            'action': 'gm',
            'sa': 'tableDetail',
            'gameId': gameId,
            'roomId': roomId,
            'tableId': tableId,
            'token': token,
        })
        ret = strutil.loads(router.queryTableServer(msg, roomId))
        ftlog.debug('_do_http_gm_table_detail| roomId, tableId, ret:', roomId, tableId, ret)
        tableDetail = strutil.loads(router.queryTableServer(msg, roomId))['result']['tableDetail']
        httpResult['tableDetail'] = tableDetail

    def onEvRoomGm(self, gameId, msg):
        ftlog.info('onEvRoomGm', msg)

    def onEvTableGm(self, gameId, msg):
        ftlog.info('onEvTableGm', msg)
        cmd = msg.getParam('cmd')
        action = msg.getParam('sa')
        roomId = msg.getParam('roomId')
        tableId = msg.getParam('tableId')
        result = {}

        if action == 'playingTableList':
            tables = self._doTableGmGetPlayingTableList(gameId, roomId)
            # msg.setResult('playingTableList', tables)
            result['playingTableList'] = tables
        elif action == 'tableDetail':
            token = msg.getParam('token')
            tableDetail = self._doTableGmGetTableDetail(gameId, roomId, tableId, token)
            # msg.setResult('tableDetail', tableDetail)
            result['tableDetail'] = tableDetail

        if router.isQuery():
            mo = utils.updateMsg(cmd='table', result=result)
            router.responseQurery(mo)

    def _doTableGmGetPlayingTableList(self, gameId, roomId):
        '''获取正在玩的牌桌列表'''
        tables = []
        room = gdata.rooms()[roomId]  # shadow roomId
        for table in room.maptable.values():
            playersNum = table.playersNum
            if playersNum != 0 or table.observers:
                players = []
                for player in table.players:
                    if player.userId > 0:
                        players.append({
                            'name': player.name,
                            'userId': player.userId,
                            'seatId': player.seatId,
                        })
                tableInfo = {
                    'playersNum': playersNum,
                    'tableId': table.tableId,
                    'players': players,
                    'roomId': roomId,
                    'gameId': gameId,
                }
                tables.append(tableInfo)
        return tables

    def _doTableGmGetTableDetail(self, gameId, roomId, tableId, token):
        '''获取牌桌信息'''
        room = gdata.rooms()[roomId]  # shadow roomId
        table = room.maptable[tableId]
        ftlog.info('GM._doTableGmGetTableDetail << |', 'roomId, tableId, token:', roomId, tableId, token)

        players = []
        for player in table.players:
            if player.userId > 0:
                userVip = hallvip.userVipSystem.getUserVip(player.userId)
                vipLevel = (userVip and userVip.vipLevel and userVip.vipLevel.level) or 0
                createTime, chargeTotal, ip = userdata.getAttrs(player.userId,
                                                                ['createTime', 'chargeTotal', 'sessionClientIP'])
                playerInfo = {
                    'seatId': player.seatId,
                    'purl': player.purl,
                    'name': player.name,
                    'userId': player.userId,
                    'holeCards': player.holeCards,
                    'cardtype': player.cardtype,
                    'cardOrder': player.order,
                    'bet': player.bet,
                    'userChips': player.userChips,
                    'tableChips': player.tableChips,
                    'sharkLevel': player.sharkLevel,
                    'vipLevel': vipLevel,
                    'chargeTotal': chargeTotal,
                    'createTime': createTime,
                    'ip': ip,
                    'localPic': player.localPic,
                }
                if not token:
                    del playerInfo['holeCards']
                    del playerInfo['cardtype']
                    del playerInfo['cardOrder']
                players.append(playerInfo)

        obs = []
        for userId in table.observers.keys():
            userVip = hallvip.userVipSystem.getUserVip(userId)
            vipLevel = (userVip and userVip.vipLevel and userVip.vipLevel.level) or 0
            name, chip = userdata.getAttrs(userId, ['name', 'chip'])
            ob = {
                'userId': userId,
                'name': name,
                'chip': chip,
            }
            obs.append(ob)

        tableDetail = {
            'tableId': table.tableId,
            'cards': table.gamePlay.sharedCards,
            'players': players,
            'obs': obs,
        }
        if getattr(table, 'creatorId', 0):
            tableDetail['主播'] = userdata.getAttr(table.creatorId, 'name')
            tableDetail['主播id'] = table.creatorId

        if not token:
            del tableDetail['cards']
        return tableDetail
