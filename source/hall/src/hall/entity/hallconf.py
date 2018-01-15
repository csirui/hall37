# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
每个配置项必须是JSON格式
'''

import json

import freetime.util.log as ftlog
from hall.entity import hallmoduledefault
from poker.entity.configure import configure, pokerconf
from poker.util import strutil

HALL_GAMEID = 9999
SDK_GAMEID = 9998

_assetKindId2OldMap = {
    'user:chip': 'CHIP',
    'user:coupon': 'COUPON',
    'item:1007': 'CARDMATCH',
    'item:2003': 'COUPON',
    'item:3001': 'MOONKEY',
    'item:3002': 'MOONBOX',
}


def tempsort(datas):
    for v in datas.values():
        if isinstance(v, list):
            try:
                v.sort(key=lambda x: x['name'])
            except:
                try:
                    v.sort(key=lambda x: x['id'])
                except:
                    pass
    return json.dumps(datas, sort_keys=True)


def getAllTcDatas(moduleName):
    datas = {}
    for gid in pokerconf.getConfigGameIds():
        subdata = configure.getGameJson(gid, moduleName, {}, configure.CLIENT_ID_TEMPLATE)
        #         ftlog.debug('getAllTcDatas', gid, moduleName, subdata)
        for k, d in subdata.items():
            if not k in datas:
                if isinstance(d, dict):
                    datas[k] = {}
                else:
                    datas[k] = []

            if isinstance(d, dict):
                # check dict config
                for k1, d1 in d.items():
                    if k1 in datas[k]:
                        ftlog.debug('Notice ModuleName:', moduleName
                                    , ' Duplicated key:', k1
                                    , ' gameId:', gid
                                    , ' content:', d1)
                datas[k].update(d)
            elif isinstance(d, list):
                datas[k].extend(d)
            # try:
            #                     datas[k].sort(key=lambda x: x['name'])
            #                 except:
            #                     try:
            #                         datas[k].sort(key=lambda x: x['id'])
            #                     except:
            #                         pass
            else:
                datas[k] = d
                #     ftlog.debug('getAllTcDatas', 'all', moduleName, datas)
    return datas


def getVcTemplateConf(clientId, moduleName, tempKeyName=None, needDict=0):
    """根据clientId获取虚配置"""
    tname1 = configure.getVcTemplate(moduleName, clientId)
    ftlog.debug('getVcTemplateConf->', clientId, moduleName, tname1)
    return tname1


def translateAssetKindIdToOld(assetKindId):
    return _assetKindId2OldMap.get(assetKindId, assetKindId)


def getPopWndConf():
    return getAllTcDatas('popwnd')


def getClientPopWndTemplateName(clientId):
    return getVcTemplateConf(clientId, 'popwnd')


def getRenameConf():
    return configure.getGameJson(HALL_GAMEID, 'rename', {}, configure.DEFAULT_CLIENT_ID)


def getClientRenameConf(clientId):
    intClientId = pokerconf.clientIdToNumber(clientId)
    if intClientId == 0:
        return {}
    return configure.getGameJson(HALL_GAMEID, 'rename', {}, intClientId)


def getFlipCardLuckConf():
    return configure.getGameJson(HALL_GAMEID, 'flipcardluck', {}, configure.DEFAULT_CLIENT_ID)


def getAppKeyInfo(appId):
    keys = configure.getGameJson(SDK_GAMEID, 'appkeys', {}, 0)
    return keys.get(str(appId), {})


def getDailyCheckinConf():
    return configure.getGameJson(HALL_GAMEID, 'dailycheckin', {}, configure.DEFAULT_CLIENT_ID)


def getClientDailyCheckinConf(clientId):
    intClientId = pokerconf.clientIdToNumber(clientId)
    if intClientId == 0:
        return {}
    return configure.getGameJson(HALL_GAMEID, 'dailycheckin', {}, intClientId)


def getMonthCheckinConf():
    return configure.getGameJson(HALL_GAMEID, 'monthcheckin', {}, configure.DEFAULT_CLIENT_ID)


def getStartFlowConf():
    return configure.getGameJson(HALL_GAMEID, 'startflow', {}, configure.DEFAULT_CLIENT_ID)


def getMonthDailyCheckinConf(clientId):
    intClientId = pokerconf.clientIdToNumber(clientId)
    if intClientId == 0:
        return {}
    return configure.getGameJson(HALL_GAMEID, 'monthcheckin', {}, intClientId)


def getModuleTipConf():
    return configure.getGameJson(HALL_GAMEID, 'moduletip', {}, configure.DEFAULT_CLIENT_ID)


def getShareConf():
    return configure.getGameJson(HALL_GAMEID, 'share', {}, configure.DEFAULT_CLIENT_ID)


def getShareTCConf():
    return configure.getGameJson(HALL_GAMEID, 'share', {}, configure.CLIENT_ID_TEMPLATE)


def getFreeConf():
    return configure.getGameJson(HALL_GAMEID, 'free', {}, configure.CLIENT_ID_TEMPLATE)


def getReplayConf():
    return configure.getGameJson(HALL_GAMEID, 'replay', {}, configure.DEFAULT_CLIENT_ID)


def getPromoteConf():
    datas = getAllTcDatas('promote')
    return datas


def getPromoteTemplateName(clientId):
    return getVcTemplateConf(clientId, 'promote')


def getFreeTemplateName(clientId, defaultName='default'):
    tname = configure.getVcTemplate('free', clientId, HALL_GAMEID)
    if tname:
        return tname
    template = hallmoduledefault.getClientModuleDefaultConf(clientId, 'free')
    if template is None:
        template = {}
    return template.get('template', defaultName)


def getGameListConf():
    return configure.getGameJson(HALL_GAMEID, 'gamelist', {}, configure.DEFAULT_CLIENT_ID)


def getGameListTemplateName(clientId):
    intClientId = pokerconf.clientIdToNumber(clientId)
    ftlog.debug("intClientId:", intClientId)
    if intClientId == 0:
        return 'hall_game_default'
    template = configure.getGameJson(HALL_GAMEID, 'gamelist', {}, intClientId)
    return template.get('template', 'hall_game_default')


def getGameList2Conf():
    return getAllTcDatas('gamelist2')


def getGameUpdateConf():
    return getAllTcDatas('update')


def getGameList2TemplateName(clientId):
    return getVcTemplateConf(clientId, 'gamelist2')


def getItemConf():
    return configure.getGameJson(HALL_GAMEID, 'item', {}, configure.DEFAULT_CLIENT_ID)


def getClientItemConf(clientId):
    intClientId = pokerconf.clientIdToNumber(clientId)
    if intClientId == 0:
        return None
    return configure.getGameJson(HALL_GAMEID, 'item', {}, intClientId)


def getVipConf():
    return configure.getGameJson(HALL_GAMEID, 'vip', {}, configure.DEFAULT_CLIENT_ID)


def getRankingConf():
    return configure.getGameJson(HALL_GAMEID, 'ranking', {}, configure.DEFAULT_CLIENT_ID)


def getStoreBuyLimitConf():
    return configure.getGameJson(HALL_GAMEID, 'store.buylimit', {}, configure.DEFAULT_CLIENT_ID)


def getClientRankTemplateName(rankingKey, clientId):
    intClientId = pokerconf.clientIdToNumber(clientId)
    if intClientId == 0:
        return None

    rankingKeys = configure.getGameJson(HALL_GAMEID, 'ranking', {}, intClientId).get('rankingKeys')
    if not rankingKeys:
        return None

    return rankingKeys.get(rankingKey)


def getBenefitsConf():
    return configure.getGameJson(HALL_GAMEID, 'benefits', {}, configure.DEFAULT_CLIENT_ID)


def getLocalNotificationConf():
    return configure.getGameJson(HALL_GAMEID, 'local_notification', {}, configure.DEFAULT_CLIENT_ID)


def getAdsConf():
    return getAllTcDatas('ads')


def getFangKaBuyConf():
    return getAllTcDatas('fangka_buy_info')


def getExitRemindConf():
    return configure.getGameJson(HALL_GAMEID, 'exit_remind', {}, configure.DEFAULT_CLIENT_ID)


def getExitRemindVCConf():
    return configure.getGameJson(HALL_GAMEID, 'exit_remind', {}, configure.CLIENT_ID_MATCHER)


def getLedConf():
    return configure.getGameJson(HALL_GAMEID, 'led', {}, configure.DEFAULT_CLIENT_ID)


def getRedEnvelope():
    return configure.getGameJson(HALL_GAMEID, 'red_envelope', {}, configure.DEFAULT_CLIENT_ID)


def getClientAdsConf(clientId):
    return getVcTemplateConf(clientId, 'ads')


def getFangKaBuyInfoCliengConf(clientId):
    return getVcTemplateConf(clientId, 'fangka_buy_info')


def getClientFangKaConf(clientId):
    """获取房卡道具配置"""
    return getVcTemplateConf(clientId, 'fangka')


def getWXAppidConf(clientId):
    """获取微信红包对应的微信appid"""
    return getVcTemplateConf(clientId, 'wxappid', HALL_GAMEID)


def getLotteryConf():
    return configure.getGameJson(HALL_GAMEID, 'lottery', {}, configure.DEFAULT_CLIENT_ID)


def getClientLotteryConf(clientId):
    intClientId = pokerconf.clientIdToNumber(clientId)
    if intClientId == 0:
        return {}
    return configure.getGameJson(HALL_GAMEID, 'lottery', {}, intClientId)


def getRouletteConf():
    return configure.getGameJson(HALL_GAMEID, 'roulette', {}, configure.DEFAULT_CLIENT_ID)


def getClientRouletteConf(clientId):
    intClientId = pokerconf.clientIdToNumber(clientId)
    if intClientId == 0:
        return {}
    return configure.getGameJson(HALL_GAMEID, 'roulette', {}, intClientId)


def getCustomSkinsConf():
    return configure.getGameJson(HALL_GAMEID, 'customskins', {}, configure.DEFAULT_CLIENT_ID)


def getClientCustomSkinsConf(clientId):
    intClientId = pokerconf.clientIdToNumber(clientId)
    if intClientId == 0:
        return {}
    return configure.getGameJson(HALL_GAMEID, 'customskins', {}, intClientId)


def getActivityConf():
    return getAllTcDatas('activity')


def getClientActivityConf(clientId):
    return getVcTemplateConf(clientId, 'activity')


def getMenuListDefaultConf():
    return getAllTcDatas('menulist')


def getMenuListClientConf(clientId):
    return getVcTemplateConf(clientId, 'menulist')


def getStoreTemplates():
    datas = getAllTcDatas('store')
    return datas


def getClientStoreConf(clientId):
    return getVcTemplateConf(clientId, 'store')


def getStoreCloseLastTemplates():
    datas = getAllTcDatas('storebuy').get('templates', {})
    return datas


def getClientStoreCloseLastConf(clientId):
    return getVcTemplateConf(clientId, 'storebuy')


def getProductsConf():
    return configure.getGameJson(HALL_GAMEID, 'products', {}, configure.DEFAULT_CLIENT_ID)


def getHallPublic():
    return configure.getGameJson(HALL_GAMEID, 'public')


def getPublicConf(key, defVal):
    d = configure.getGameJson(HALL_GAMEID, 'public', {})
    return d.get(key, defVal)


def _getHallPublic(key):
    return getHallPublic().get(key, None)


def getOnlineUserCountRate(clientId):
    gameId = strutil.getGameIdFromHallClientId(clientId)
    intClientidNum = pokerconf.clientIdToNumber(clientId)
    infos = configure.getGameJson(gameId, 'online.info', {}, intClientidNum)
    rate = infos.get('rate', None)
    if rate:
        return rate
    infos = configure.getGameJson(gameId, 'online.info', {}, 0)
    rate = infos.get('rate', None)
    if rate:
        return rate
    return 1


def _adjustHallSessionInfo(redisfullkey, alldata):
    if not alldata:
        return
    redisfullkey = redisfullkey.replace(':hall.info', ':table.tbbox')
    tbbox = configure.getJson(redisfullkey, {}, 0)
    tbboxrooms = tbbox.get('rooms', {})
    for _, si in alldata['session_items'].items():
        rooms = si['rooms']
        for x in xrange(len(rooms)):
            rooms[x] = alldata['room_items'][rooms[x]]
            rid = rooms[x]['id']
            roomtbbox = tbboxrooms.get(str(rid))
            if roomtbbox and roomtbbox.get('playCount', 0) > 1:
                items = roomtbbox.get('reward', {}).get('items', {})
                items = strutil.cloneData(items)
                for item in items:
                    item['name'] = translateAssetKindIdToOld(item['itemId'])
                rooms[x]['tbbox'] = {'pt': roomtbbox.get('playCount', 0),
                                     'rewards': items}
    for _, ss in alldata['templates'].items():
        for x in xrange(len(ss)):
            ss[x] = alldata['session_items'][ss[x]]


def getHallSessionInfo(gameId, clientId):
    if not gameId or gameId == HALL_GAMEID:
        gameId = strutil.getGameIdFromHallClientId(clientId)
    intClientId = pokerconf.clientIdToNumber(clientId)
    return configure.getGameTemplateInfo(gameId, 'hall.info', intClientId, _adjustHallSessionInfo)


def _adjustHallHtmlsInfo(redisfullkey, alldata):
    if alldata:
        hitems = alldata.get('html_items', {})
        for _, ss in alldata.get('templates', {}).items():
            for x in ss.keys():
                ss[x] = hitems[x]
            ss['keys'] = ss.keys()


def getHallHtmlsInfo(clientId):
    try:
        gameId = strutil.getGameIdFromHallClientId(clientId)
        intClientId = pokerconf.clientIdToNumber(clientId)
        return configure.getGameTemplateInfo(gameId, 'htmls.info', intClientId, _adjustHallHtmlsInfo)
    except:
        ftlog.error('ERROR getHallHtmlsInfo clientId=', clientId)


def getDaShiFenFilter(clientId):
    info = configure.getTcContentByClientId('dashifen.filter', None, clientId, [])
    return info


def getModulesSwitch(clientId):
    info = configure.getTcContentByGameId('modules.switch', None, HALL_GAMEID, clientId, [])
    return info


def _adjustMoreGameTemplates(key, alldata):
    templates = alldata['templates']
    plugs = alldata['plugins']
    for ts in templates.values():
        for x in xrange(len(ts)):
            ts[x] = plugs[ts[x]]


def getMoreGames(clientId):
    gameId = strutil.getGameIdFromHallClientId(clientId)
    intClientId = pokerconf.clientIdToNumber(clientId)
    templates = configure.getGameTemplates(HALL_GAMEID, 'more.games', _adjustMoreGameTemplates)
    template = configure.getGameJson(gameId, 'more.games', {}, intClientId)
    template = template.get('template', 'default')
    info = templates.get(template)
    ftlog.debug('hallconf.getMoreGames clientId=', clientId,
                'gameId=', gameId,
                'intClientId=', intClientId,
                'template=', template,
                'info=', info)
    if info:
        return info
    return templates.get('default')


def getMoreGamesDesc(clientId):
    return configure.getGameJson(HALL_GAMEID, 'more.games.desc', None, configure.DEFAULT_CLIENT_ID)


def getMoreGamesUpdateApks(clientId):
    try:
        gameId = strutil.getGameIdFromHallClientId(clientId)
        intClientId = pokerconf.clientIdToNumber(clientId)
        apks = configure.getGameTemplateInfo(gameId, 'more.games.apks', intClientId, None)
        if not apks:
            ftlog.error('ERROR, getMoreGamesUpdateApks clientId=', clientId)
        return apks
    except:
        ftlog.error('ERROR, getMoreGamesUpdateApks clientId=', clientId)
        return None


def getUserHeadPics(clientId):
    heads = configure.getTcContentByClientId('headpics', None, clientId, None)
    if not heads:
        heads = configure.getTcContentByGameId('headpics', None, HALL_GAMEID, clientId)
    return heads


def getChargeLeadTemplate(templateName):
    conf = configure.getGameJson(HALL_GAMEID, 'chargelead', None, configure.DEFAULT_CLIENT_ID)
    if conf:
        return conf.get('templates', {}).get(templateName)
    return None


def getNeiTuiGuangConf(clientId):
    templates = configure.getGameJson(HALL_GAMEID, 'neituiguang', {}, configure.DEFAULT_CLIENT_ID).get('templates', {})
    intClientId = pokerconf.clientIdToNumber(clientId)
    templateName = configure.getGameJson(HALL_GAMEID, 'neituiguang', {}, intClientId).get('template', '')
    if templateName:
        return templates.get(templateName, {})
    else:
        _, clientVer, _ = strutil.parseClientId(clientId)
        if clientVer >= 3.372:
            return templates.get('default_neituiguang_new', {})
        else:
            return templates.get('default_neituiguang_3_37', {})


def getRoomLevelName(gameId, bigRoomId):
    conf = configure.getGameJson(gameId, 'chargelead', None, configure.DEFAULT_CLIENT_ID)
    if conf:
        return conf.get(str(bigRoomId))
    return None


def getFiveStarConf():
    return configure.getGameJson(HALL_GAMEID, 'fivestar', {}, configure.DEFAULT_CLIENT_ID)


def getFiveStarClientConf(clientId):
    intClientId = pokerconf.clientIdToNumber(clientId)
    if intClientId == 0:
        return {}
    return configure.getGameJson(HALL_GAMEID, 'fivestar', {}, intClientId)


def getUpgradeFullConf(gameId, clientId):
    return configure.getTcContentByGameId('upgrade_full', None, gameId, clientId, None)


def getUpgradeDiffConf(gameId, clientId):
    return configure.getTcContentByGameId('upgrade_diff', None, gameId, clientId, None)


def getUpgradeIncConf(gameId, clientId):
    return configure.getTcContentByGameId('upgrade_inc', None, gameId, clientId, None)


def getUpgradeStaticConf():
    conf = configure.getGameJson(HALL_GAMEID, 'upgrade_client_static')
    return conf


def getModuleDefaultConf():
    conf = configure.getGameJson(HALL_GAMEID, 'module_default')
    return conf


def getFristRechargeConf():
    conf = configure.getGameJson(HALL_GAMEID, 'first_recharge')
    return conf


def getFristRechargeVCConf():
    conf = configure.getGameJson(HALL_GAMEID, "first_recharge", {}, configure.CLIENT_ID_MATCHER)
    return conf


def getThirdSDKSwitchConf():
    conf = configure.getGameJson(HALL_GAMEID, 'third_sdk_switch', {}, configure.DEFAULT_CLIENT_ID)
    return conf


def getDomainTCConf():
    conf = configure.getGameJson(HALL_GAMEID, "domain", [], configure.CLIENT_ID_TEMPLATE)
    return conf


def getLoginRewardConf():
    conf = configure.getGameJson(HALL_GAMEID, 'login_reward', {}, configure.CLIENT_ID_TEMPLATE)
    return conf


def getItemExchangeConf():
    conf = configure.getGameJson(HALL_GAMEID, 'item_exchange', {}, configure.CLIENT_ID_TEMPLATE)
    return conf
