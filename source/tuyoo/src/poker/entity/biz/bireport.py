# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import struct
import time

import freetime.util.log as ftlog
from poker.entity.biz import integrate
from poker.entity.configure import gdata, pokerconf
from poker.entity.dao import bidata, sessiondata
from poker.entity.dao.daoconst import CHIP_TYPE_ALL, CHIP_TYPE_ITEM
from poker.util import timestamp, strutil

_ENABLE_BIFILE = 0
_BILOGER = None


def _report(arglist, argdict, isHinfo=0):
    if _ENABLE_BIFILE:
        global _BILOGER
        if _BILOGER is None:
            log_file_fullpath = gdata.globalConfig()['log_path']
            log_file_fullpath = log_file_fullpath + '/bi.' + gdata.serverId() + '.log'
            _BILOGER = ftlog.openNormalLogfile(log_file_fullpath)
        jsondata = [timestamp.formatTimeMs(), gdata.serverId()]
        jsondata.extend(arglist)
        jsondata.append(argdict)
        msg = strutil.dumps(jsondata)
        _BILOGER.info(msg)
    else:
        jsondata = ['BIREPORT', gdata.serverId()]
        jsondata.extend(arglist)
        jsondata.append(argdict)
        msg = strutil.dumps(jsondata)
        if isHinfo:
            ftlog.hinfo(msg)
        else:
            ftlog.info(msg)


def report(moduleName, *arglist, **argdict):
    alist = [moduleName]
    alist.extend(arglist)
    _report(alist, argdict)


def _getCurrentDay():
    return timestamp.formatTimeDayShort()


def itemUpdate(gameId, userId, kindId, detalCount, finalCount, eventId, intEventParam, *arglist, **argdict):
    '''
    道具变化的标准本地日志文件汇报
    '''
    _, clientIdInt = sessiondata.getClientIdNum(userId)
    reportBiChip(userId, detalCount, detalCount, finalCount, eventId, clientIdInt, gameId, gameId, intEventParam,
                 CHIP_TYPE_ITEM, kindId, arglist=arglist, argdict=argdict, logtag='item_update')


def tableStart(gameId, roomId, tableId, cardId, userIdList, *arglist, **argdict):
    '''
    桌子游戏开始的标准本地日志文件汇报
    '''
    alist = ['table_start', gameId, roomId, tableId, cardId, userIdList]
    alist.extend(arglist)
    _report(alist, argdict)


def tableWinLose(gameId, roomId, tableId, cardId, userIdList, *arglist, **argdict):
    '''
    桌子游戏结束的标准本地日志文件汇报
    '''
    alist = ['table_winlose', gameId, roomId, tableId, cardId, userIdList]
    alist.extend(arglist)
    _report(alist, argdict, 1)


def tcpUserOnline(userCount, *arglist, **argdict):
    '''
    用户TCP连接在线数量的标准本地日志文件汇报和REDIS实时数据汇报
    '''
    bidata.setConnOnLineInfo(gdata.serverId(), userCount)
    alist = ['tcp_user_online', 0, userCount]
    alist.extend(arglist)
    _report(alist, argdict)


def getConnOnlineUserCount():
    '''
    重BI数据库取得当前所有CONN进程的在线人数合计
    '''
    return bidata.getConnOnlineUserCount()


def roomUserOnline(gameId, roomId, userCount, playTableCount, observerCount, *arglist, **argdict):
    '''
    房间内在线用户数量的标准本地日志文件汇报和REDIS实时数据汇报
    '''
    bidata.setRoomOnLineInfo(gameId, roomId, userCount, playTableCount, observerCount)
    alist = ['room_user_online', 0, roomId, userCount, playTableCount, observerCount]
    alist.extend(arglist)
    _report(alist, argdict)


def getRoomOnLineUserCount(gameId, withShadowRoomInfo=0):
    '''
    重BI数据库中取得当前的游戏的所有的在线人数信息
    return allcount, counts, details
    allcount int，游戏内所有房间的人数的总和
    counts 字典dict，key为大房间ID（bigRoomId)，value为该大房间内的人数总和
    details 字典dict，key为房间实例ID（roomId），value为该放假内的人数
    此数据由每个GR，GT进程每10秒钟向BI数据库进行汇报一次
    '''
    allcount, counts, details, _, _, _ = bidata.getRoomOnLineUserCount(gameId, withShadowRoomInfo)
    return allcount, counts, details


def getRoomOnLineUserCount2(gameId, withShadowRoomInfo=0):
    '''
    重BI数据库中取得当前的游戏的所有的在线人数信息, 与getRoomOnLineUserCount功能一致，仅多出一个返回值ocount
    return allcount, counts, details, allobcount, obcounts, obdetails
    allobcount, obcounts, obdetails 观察者数量，需要table类实现observersNum属性
    '''
    return bidata.getRoomOnLineUserCount(gameId, withShadowRoomInfo)


def gcoin(coinKey, gameId, detalCount, *arglist, **argdict):
    '''
    一类货币数量变化的标准本地日志文件汇报和REDIS实时数据汇报
    '''
    rkey = str(gameId) + ':' + _getCurrentDay()
    assert (isinstance(coinKey, (str, unicode)))
    assert (isinstance(detalCount, int))
    leftCount = bidata.incrGcoin(rkey, coinKey, detalCount)
    alist = ['gcoin', gameId, detalCount, leftCount, rkey, coinKey]
    alist.extend(arglist)
    _report(alist, argdict)


def creatGameData(gameId, userId, clientId, dataKeys, dataValues, *arglist, **argdict):
    '''
    创建用户游戏数据的标准本地日志文件汇报
    '''
    alist = ['creat_game_data', gameId, userId, clientId, dataKeys, dataValues]
    alist.extend(arglist)
    _report(alist, argdict)


def tableRoomFee(gameId, fees, *arglist, **argdict):
    '''
    房间费用的标准本地日志文件汇报
    '''
    alist = ['table_room_fee', gameId, fees]
    alist.extend(arglist)
    _report(alist, argdict)


def userGameEnter(gameId, userId, clientId, *arglist, **argdict):
    '''
    用户进入游戏的标准本地日志文件汇报
    '''
    alist = ['game_enter', gameId, userId, clientId]
    alist.extend(arglist)
    _report(alist, argdict)


def userGameLeave(gameId, userId, clientId, *arglist, **argdict):
    '''
    用户离开游戏的标准本地日志文件汇报
    '''
    alist = ['game_leave', gameId, userId, clientId]
    alist.extend(arglist)
    _report(alist, argdict)


def userBindUser(gameId, userId, clientId, *arglist, **argdict):
    '''
    用户进入大厅的标准本地日志文件汇报
    '''
    alist = ['bind_user', gameId, userId, clientId]
    alist.extend(arglist)
    _report(alist, argdict)


def tableEvent(gameId, roomId, tableId, event, *arglist, **argdict):
    '''
    桌子事件的标准本地日志文件汇报
    '''
    alist = ['table_event', gameId, roomId, tableId, event]
    alist.extend(arglist)
    _report(alist, argdict)


def playerEvent(gameId, userId, roomId, tableId, event, *arglist, **argdict):
    '''
    桌子玩家的标准本地日志文件汇报
    '''
    alist = ['player_event', gameId, userId, roomId, tableId, event]
    alist.extend(arglist)
    _report(alist, argdict)


def matchStart(gameId, roomId, matchId, matchName, *arglist, **argdict):
    '''
    比赛开始的标准本地日志文件汇报
    '''
    alist = ['match_start', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict, 1)


def matchFinish(gameId, roomId, matchId, matchName, *arglist, **argdict):
    '''
    比赛结束大厅的标准本地日志文件汇报
    '''
    alist = ['match_finish', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict, 1)


def matchStartTable(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_start_table', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict, 1)


def matchLockUser(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_lock_user', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict, 1)


def matchStageStart(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_stage_start', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict, 1)


def matchStageFinish(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_stage_finish', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict, 1)


def matchGroupStart(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_group_start', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict, 1)


def matchGroupFinish(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_group_finish', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict, 1)


def matchUserGameOver(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_user_game_over', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict, 1)


def matchUserSignin(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_user_signin', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict)


def matchUserSignout(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_user_signout', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict)


def matchUserKickout(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_user_kickout', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict)


def matchUserEnter(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_user_enter', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict)


def matchUserLeave(gameId, roomId, matchId, matchName, *arglist, **argdict):
    alist = ['match_user_leave', gameId, roomId, matchId, matchName]
    alist.extend(arglist)
    _report(alist, argdict)


def reportHttpBi1(user_id, log_type, struct_fmt, *struct_args):
    if _ENABLE_BIFILE:
        return 1
    '''
    发送BI消息到BI日志收集服务
    user_id 消息产生的用户ID, 必须是有效的正整数
    log_type 消息的基本大类型, 再poker/global.json中定义的bireportgroup的键值
    struct_fmt 消息的具体格式, struct的格式化格式
    struct_args 消息的参数, 即:struct.pack使用的参数
    注意: 本函数自动会在struct_fmt之前添加基本消息头"<I", 即: 使用little字节序, 添加当前的时间戳
    '''
    try:
        ftlog.debug('reportHttpBi->', user_id, log_type, struct_args)
        struct_fmt = '<I' + struct_fmt
        log_record = struct.pack(struct_fmt, int(time.time()), *struct_args)
        groupinfos = pokerconf.getIntegrate().get('bireport', {}).get('groups', {})
        groupinfo = groupinfos[log_type]
        group = groupinfo['name']
        gcount = groupinfo['count']
        if gcount > 0:
            group = group + str(user_id % gcount)
        ftlog.sendHttpLog(group, log_type, log_record)
    except:
        ftlog.error()


def reportHttpBi2(user_id, log_type, struct_fmt, *struct_args):
    if _ENABLE_BIFILE:
        return 1
    '''
    发送BI消息到BI日志收集服务
    user_id 消息产生的用户ID, 必须是有效的正整数
    log_type 消息的基本大类型, 再poker/global.json中定义的bireportgroup的键值
    struct_fmt 消息的具体格式, struct的格式化格式
    struct_args 消息的参数, 即:struct.pack使用的参数
    注意: 本函数自动会在struct_fmt之前添加基本消息头"<I", 即: 使用little字节序, 添加当前的时间戳
    '''
    if integrate.isEnabled('bireport'):
        try:
            ftlog.debug('reportHttpBi->', user_id, log_type, struct_args)
            struct_fmt = '<I' + struct_fmt
            log_record = struct.pack(struct_fmt, int(time.time()), *struct_args)
            groupinfos = pokerconf.getIntegrate().get('bireport', {}).get('groups', {})
            if groupinfos:
                groupinfo = groupinfos[log_type]
                group = groupinfo['name']
                gcount = groupinfo['count']
                if gcount > 0:
                    group = group + str(user_id % gcount)
                header = {"log-type": log_type, "log-group": group}
                integrate.sendTo('bireport', log_record, header)
        except:
            ftlog.error()


reportHttpBi = reportHttpBi2


def reportBiChip(user_id, delta, trueDelta, final, eventId,
                 clientId, gameId, appId, eventParam, chipType, extentId=0,
                 arglist=[], argdict={}, logtag='chip_update'):
    '''
    用户货币变化的HTTP远程BI汇报
    '''
    # fmt = "I q q q I I H H I B I"
    #        | | | | | | | | | | └-- extentId 扩展类型类型, 目前当为道具的时候为道具的kindId
    #        | | | | | | | | | └-- chipType 金币类型, 参考: CHIP_TYPE_ALL
    #        | | | | | | | | └-- eventParam 事件的参数
    #        | | | | | | | └- appId 客户端登录时产生的appId
    #        | | | | | | └- gameId 后端服务操作时使用的gameId
    #        | | | | | └- clientId 客户端终端的ID
    #        | | | | └- eventId 事件ID
    #        | | | └- final 最终的数量
    #        | | └- trueDelta 实际变化的数量
    #        | └- delta 期望发生的数量
    #        └- userId 事件产生的用户
    eventId = pokerconf.biEventIdToNumber(eventId)
    assert (isinstance(user_id, (int, long)))
    assert (isinstance(delta, (int, long)))
    assert (isinstance(trueDelta, (int, long)))
    assert (isinstance(final, (int, long)))
    assert (isinstance(eventId, (int, long)))
    assert (isinstance(clientId, (int, long)))
    assert (isinstance(gameId, (int, long)))
    assert (isinstance(appId, (int, long)))
    assert (isinstance(eventParam, (int, long)))
    assert (chipType in CHIP_TYPE_ALL)
    assert (isinstance(extentId, (int, long)))
    # 本地日志
    alist = [logtag, user_id, delta, trueDelta, final, eventId, clientId, gameId, appId, eventParam, chipType, extentId]
    alist.extend(arglist)
    _report(alist, argdict)
    if _ENABLE_BIFILE:
        return 1
    # 远程日志
    return reportHttpBi(user_id, 'chip', 'IqqqIIHHIBI',
                        user_id, delta, trueDelta, final, eventId,
                        clientId, gameId, appId, eventParam, chipType, extentId)


def reportGameEvent(eventId, user_id, gameId, roomId, tableId, roundId, detalChip, state1, state2, cardlist, clientId,
                    finalTableChip=0, finalUserChip=0,
                    arglist=[], argdict={}, logtag='game_event'):
    '''
    游戏牌桌阶段事件的HTTP远程BI汇报
    '''
    # fmt = "I I H I Q Q I q q q B B 20B"
    #        | | | | | | | | | | | | └- cardlist 当前事件操作的牌, 数字(0~54), 0xFF为无效
    #        | | | | | | | | | | | └- state2 当前事件操作的状态2(例如:托管,超时)
    #        | | | | | | | | | | └- state1 当前事件操作的状态1(例如:托管,超时)
    #        | | | | | | | | | └- finalUserChip 当前事件用户的最终所有金币数量
    #        | | | | | | | | └- finalTableChip 当前事件用户的最终桌子金币数量
    #        | | | | | | | └- detalChip 当前事件操作涉及的金币数量
    #        | | | | | | └- roundId 当前事件的游戏局ID(如果为比赛事件,即为比赛的ID, 如果为普通牌桌,即为牌局ID或时间戳)
    #        | | | | | └- tableId 游戏事件发生的房间桌子ID
    #        | | | | └- roomId 游戏事件发生的房间
    #        | | | └- clientId 客户端的clientId
    #        | | └- gameId 后端服务操作时使用的gameId
    #        | └- userId 事件产生的用户
    #        └- eventId 事件ID
    eventId = pokerconf.biEventIdToNumber(eventId)
    user_id = int(user_id)
    gameId = int(gameId)
    _, clientId = sessiondata.getClientIdNum(user_id, clientId)
    assert (isinstance(eventId, (int, long)))
    assert (isinstance(user_id, (int, long)))
    assert (isinstance(gameId, (int, long)))
    assert (isinstance(roomId, (int, long)))
    assert (isinstance(tableId, (int, long)))
    assert (isinstance(roundId, (int, long)))
    assert (isinstance(detalChip, (int, long)))
    assert (isinstance(state1, (int, long)))
    assert (isinstance(state2, (int, long)))
    assert (isinstance(clientId, (int, long)))
    assert (isinstance(finalUserChip, (int, long)))
    assert (isinstance(finalTableChip, (int, long)))

    cards = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
             0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
             0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
             0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    if cardlist:
        for x in xrange(min(20, len(cardlist))):
            cards[x] = int(cardlist[x])

    # 本地日志
    alist = [logtag, eventId, user_id, gameId, roomId, tableId, roundId, detalChip, state1, state2, cardlist, clientId,
             finalTableChip, finalUserChip]
    alist.extend(arglist)
    _report(alist, argdict)
    if _ENABLE_BIFILE:
        return 1
    # 远程日志
    return reportHttpBi(user_id, 'game', 'IIHIQQIqqq22B', eventId,
                        user_id, gameId, clientId, roomId,
                        tableId, roundId, detalChip, finalTableChip, finalUserChip, state1, state2,
                        cards[0], cards[1], cards[2], cards[3], cards[4], cards[5], cards[6], cards[7], cards[8],
                        cards[9],
                        cards[10], cards[11], cards[12], cards[13], cards[14], cards[15], cards[16], cards[17],
                        cards[18], cards[19]
                        )


def reportCardEvent(eventId, user_id, gameId, roomId, tableId, roundId, detalChip, state1, state2, cardlist, clientId,
                    finalTableChip=0, finalUserChip=0,
                    arglist=[], argdict={}, logtag='card_event'):
    '''
    游戏出牌事件的HTTP远程BI汇报
    '''
    # fmt = "I I H I Q Q I q q q B B 20B"
    #        | | | | | | | | | | | | |
    #        | | | | | | | | | | | | └- cardlist 当前事件操作的牌, 数字(0~54), 0xFF为无效
    #        | | | | | | | | | | | └- state2 当前事件操作的状态2(例如:托管,超时)
    #        | | | | | | | | | | └- state1 当前事件操作的状态1(例如:托管,超时)
    #        | | | | | | | | | └- finalUserChip 当前事件用户的最终所有金币数量
    #        | | | | | | | | └- finalTableChip 当前事件用户的最终桌子金币数量
    #        | | | | | | | └- detalChip 当前事件操作涉及的金币数量
    #        | | | | | | └- roundId 当前事件的游戏局ID(如果为比赛事件,即为比赛的ID, 如果为普通牌桌,即为牌局ID或时间戳)
    #        | | | | | └- tableId 游戏事件发生的房间桌子ID
    #        | | | | └- roomId 游戏事件发生的房间
    #        | | | └- clientId 客户端的clientId
    #        | | └- gameId 后端服务操作时使用的gameId
    #        | └- userId 事件产生的用户
    #        └- eventId 事件ID
    eventId = pokerconf.biEventIdToNumber(eventId)
    user_id = int(user_id)
    gameId = int(gameId)
    _, clientId = sessiondata.getClientIdNum(user_id, clientId)
    assert (isinstance(eventId, (int, long)))
    assert (isinstance(user_id, (int, long)))
    assert (isinstance(gameId, (int, long)))
    assert (isinstance(roomId, (int, long)))
    assert (isinstance(tableId, (int, long)))
    assert (isinstance(roundId, (int, long)))
    assert (isinstance(detalChip, (int, long)))
    assert (isinstance(state1, (int, long)))
    assert (isinstance(state2, (int, long)))
    assert (isinstance(clientId, (int, long)))
    assert (isinstance(finalUserChip, (int, long)))
    assert (isinstance(finalTableChip, (int, long)))
    cards = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
             0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
             0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
             0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    if cardlist:
        for x in xrange(min(20, len(cardlist))):
            cards[x] = int(cardlist[x])
    # 本地日志
    alist = [logtag, eventId, user_id, gameId, roomId, tableId, roundId, detalChip, state1, state2, cardlist, clientId,
             finalTableChip, finalUserChip]
    alist.extend(arglist)
    _report(alist, argdict)
    if _ENABLE_BIFILE:
        return 1
        # 远程日志 目前BI服务无法接收此消息的数据量，暂时不发送远程数据

#     return reportHttpBi(user_id, 'card', 'IIHIQQIqqq22B', eventId,
#                           user_id, gameId, clientId, roomId,
#                           tableId, roundId, detalChip, finalTableChip, finalUserChip, state1, state2, *cards)
