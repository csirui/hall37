# -*- coding: utf-8 -*-
'''
Created on 2015年5月20日

@author: zqh
'''

import random
from string import strip

from datetime import datetime

from hall.entity import hallvip, hallconf
from poker.entity.biz import bireport
from poker.entity.biz.message import message
from poker.entity.configure import gdata
from poker.entity.dao import daobase, userdata, userchip, gamedata, \
    day1st
from poker.entity.events.tyevent import EventUserLogin
from poker.entity.game.game import TYGame
from poker.util import timestamp


def getRegisterDay(userId):
    """
    获取玩家注册的天数
    """
    registerTimeStr = userdata.getAttr(userId, 'createTime')
    nowTime = datetime.now()
    try:
        registerTime = datetime.strptime(registerTimeStr, '%Y-%m-%d %H:%M:%S.%f')
    except:
        registerTime = nowTime
    ct = nowTime.time()
    dt1 = datetime.combine(nowTime.date(), ct)
    dt2 = datetime.combine(registerTime.date(), ct)
    past = dt1 - dt2
    return int(past.days)


def isForceLogout(userId):
    '''
    检查该用户是否已经禁止登录
    '''
    isForbidden = daobase.executeForbiddenCmd('EXISTS', 'forbidden:uid:' + str(userId))
    if isForbidden:
        return 1
    return 0


def getUserInfo(userId, gameId, clientId):
    '''
    取得用户的基本账户的信息
    '''
    ukeys = ['email', 'pdevid', 'mdevid', 'isbind', 'snsId', 'name',
             'source', 'diamond', 'address', 'sex', 'state',
             'payCount', 'snsinfo', 'vip', 'dayang', 'idcardno',
             'phonenumber', 'truename', 'detect_phonenumber',
             'lang', 'country', "signature", "set_name_sum", "coupon",
             'purl', 'beauty', 'charm', 'password', 'bindMobile']

    udataDb = userdata.getAttrs(userId, ukeys)

    udata = dict(zip(ukeys, udataDb))
    udata['coin'] = udata['diamond']  # 数据补丁: 再把diamond转换到coin返回, 老版本用的是coin
    udata['chip'] = userchip.getChip(userId)

    # 头像相关
    purl, isbeauty = getUserHeadUrl(userId, clientId, udata['purl'], udata['beauty'])
    udata['purl'] = purl
    udata['isBeauty'] = isbeauty

    # vip信息
    udata['vipInfo'] = hallvip.userVipSystem.getVipInfo(userId)
    # 江湖救急次数
    udata['assistance'] = {
        'count': hallvip.userVipSystem.getAssistanceCount(gameId, userId),
        'limit': hallvip.vipSystem.getAssistanceChipUpperLimit()
    }
    userdata.updateUserGameDataAuthorTime(userId, gameId)
    return udata


def getGameInfo(userId, gameId, clientId):
    '''
    取得当前用户的游戏账户信息dict
    '''
    # 获取插件游戏的信息
    infos = TYGame(gameId).getGameInfo(userId, clientId)
    # 数据补丁, 避免客户端崩溃
    if 'headUrl' not in infos:
        infos['headUrl'] = ''
    return infos


def _filter360QihuImage(userId, clientId, headurl):
    '''
    过滤360SNS账户的恶心的头像图标
    '''
    headurl = unicode(headurl)
    if headurl.find('qhimg.com') > 0:
        heads = getUserHeadPics(clientId)
        purl = random.choice(heads)
        userdata.setAttr(userId, 'purl', purl)
        return purl
    return headurl


def getUserHeadUrl(userId, clientId, purl=None, beauty=None):
    '''
    取得当前的用户的头像
    取得当前的用户是否是美女认证账户
    '''
    # 自定义头像, 美女认证
    if purl == None:
        purl, beauty = userdata.getAttrs(userId, ['purl', 'beauty'])
        if purl:
            purl = unicode(purl)
        else:
            purl = ''
    purl = _filter360QihuImage(userId, clientId, purl)
    if isinstance(purl, (str, unicode)):
        if (purl.find('http://') < 0) and (purl.find('https://') < 0):
            purl = ''
    if purl == '' or purl == None:
        heads = getUserHeadPics(clientId)
        purl = random.choice(heads)
        userdata.setAttr(userId, 'purl', purl)

    isBeauty = False
    if beauty:
        isBeauty = True if (beauty & 1) != 0 else False

    return purl, isBeauty


def _getMsgParam(atts, values, msg, checkType, msgkey, attname=None):
    '''
    重MsgPack实例中取得一个参数的值, 并使用checkType进行检查
    将结果追加到atts和values中
    '''
    value = msg.getParam(msgkey)
    if value == None:
        return
    value = checkType(value)
    if value != None:
        if attname == None:
            atts.append(msgkey)
        else:
            atts.append(attname)
        values.append(value)


def _checkStr(val):
    '''
    检查用户的一个字符串属性的数据格式
    '''
    val = strip(unicode(val))
    if len(val) > 0:
        return val
    return None


def _checkSex(val):
    '''
    检查用户的性别的数据格式
    '''
    try:
        val = int(val)
        if val == 1 or val == 0:
            return val
    except:
        pass
    return None


def _checkHeadUrl(val):
    '''
    检查用户的头像的数据格式
    '''
    val = _checkStr(val)
    if val:
        if val.find('http://') < 0:
            val = gdata.httpAvatar() + '/' + val
    return None


def loginGame(userId, gameId, clientId):
    """
    用户登录一个游戏, 检查用户的游戏数据是否存在(创建用户数据)
    """
    # 确认用户的游戏数据是否存在
    iscreate = ensureGameDataExists(userId, gameId, clientId)
    # 游戏登录次数加1，每次bind_user都会加1，包括断线重连
    gamedata.incrGameAttr(userId, gameId, 'loginsum', 1)

    # 确认是否是今日第一次登录
    isdayfirst = False
    datas = day1st.getDay1stDatas(userId, gameId)
    if 'daylogin' not in datas:
        isdayfirst = True
        datas['daylogin'] = 1
        datas['iscreate'] = 1
    else:
        datas['daylogin'] += 1
        datas['iscreate'] = 0
    day1st.setDay1stDatas(userId, gameId, datas)

    if isdayfirst:
        # 消息的数据结构新旧转换
        message.convertOldData(gameId, userId)

    # 插件的登录补充处理
    TYGame(gameId).loginGame(userId, gameId, clientId, iscreate, isdayfirst)

    evt = EventUserLogin(userId, gameId, isdayfirst, iscreate, clientId)
    TYGame(gameId).getEventBus().publishEvent(evt)

    userdata.updateUserGameDataAuthorTime(userId, gameId)

    return isdayfirst, iscreate


def ensureGameDataExists(userId, gameId, clientId):
    '''
    判定用户游戏数据是否存在, 若不存在则初始化该游戏的所有的相关游戏数据
    包括: 主游戏数据gamedata, 道具, 勋章等
    '''
    isCreate = False
    gaccount = TYGame(gameId)
    # 以游戏主数据的前2个字段为判定条件
    ukeys = gaccount.getInitDataKeys()[0:2]
    d1, d2 = gamedata.getGameAttrs(userId, gameId, ukeys)
    if d1 is None or d2 is None:
        gdkeys, gdata = gaccount.createGameData(userId, gameId)
        gdkeys.append('createTime')
        gdata.append(timestamp.formatTimeMs())
        bireport.creatGameData(gameId, userId, clientId, gdkeys, gdata)
        bireport.reportGameEvent('CREATE_GAME_DATA',
                                 userId, gameId, 0, 0, 0, 0, 0, 0, [], clientId)
        isCreate = True
    return isCreate


# def updateHistoryClientIds(userId, gameId, clientId):
#     '''
#     更新当前游戏数据中, 客户端的历史版本记录
#     即详细记录当前用户再每个游戏中,使用过的客户端
#     '''
#     intClientId = pokerconf.clientIdToNumber(clientId)
#     if intClientId <= 0 :
#         ftlog.error('updateGameDataHistoryClientIds not know clientid ! [', clientId, ']')
#         return
# 
#     changed = False
#     found = False
#     clist = gamedata.getGameAttrJson(userId, gameId, 'history_clientids', [])
#     for x in xrange(len(clist)) :
#         c = clist[x]
#         if not isinstance(c, int) :  # 老数据的补丁, 转换字符格式到数字格式
#             c = pokerconf.clientIdToNumber(c)
#             if c <= 0 :
#                 ftlog.error('updateGameDataHistoryClientIds not know clientid ! [', clist[x], ']')
#             clist[x] = c
#             changed = True
#         if c == intClientId :
#             found = True
# 
#     if not found :
#         clist.append(intClientId)
#         changed = True
#     
#     if changed :
#         gamedata.setGameAttr(userId, gameId, 'history_clientids', strutil.dumps(clist))


# def getHistoryClientIds(userId, gameId):
#     return gamedata.getGameAttrJson(userId, gameId, 'history_clientids', [])


def getUserHeadPics(clientId):
    return hallconf.getUserHeadPics(clientId)
