# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
每个配置项必须是JSON格式
'''

from datetime import datetime

import freetime.entity.config as ftcon
import freetime.util.log as ftlog
from freetime.core.lock import FTLock, lock
from poker.util import strutil

UNKNOW_ID = 0  # 未知的或错误的clientId, 未知的或错误的商品定义, 未知的或错误的商品定义
DEFAULT_CLIENT_ID = 0  # 缺省的clientid的数值
CLIENT_ID_TEMPLATE = 'tc'
CLIENT_ID_MATCHER = 'vc'
CLIENTID_RPC = 'Android_3.7_-hall6-RPC'
CLIENTID_SYSCMD = 'Android_3.7_-hall6-SYSCMD'
CLIENTID_ROBOT = 'robot_3.7_-hall6-robot'

_CONFIG_CMD_PPS_ = 0
_CONFIG_CMDS_ = {}
_CONFIG_COUNT_ = 0
_CONFIG_COUNT_TIME_ = datetime.now()


def _configCmdPps(ckey):
    global _CONFIG_CMDS_, _CONFIG_COUNT_, _CONFIG_COUNT_TIME_
    try:
        i = ckey.rfind(':')
        if i > 0:
            ckey = ckey[0:i]

        if not ckey in _CONFIG_CMDS_:
            _CONFIG_CMDS_[ckey] = 1
        else:
            _CONFIG_CMDS_[ckey] += 1

        _CONFIG_COUNT_ += 1
    # if _CONFIG_COUNT_ % _CONFIG_COUNT_BLOCK_ == 0:
    #             ct = datetime.now()
    #             dt = ct - _CONFIG_COUNT_TIME_
    #             dt = dt.seconds + dt.microseconds / 1000000.0
    #             pps = '%0.2f' % (_CONFIG_COUNT_BLOCK_ / dt)
    #             _CONFIG_COUNT_TIME_ = ct
    #             ftlog.info("CONFIG_PPS", pps, 'CMDCOUNT', _CONFIG_COUNT_, 'DT %0.2f' % (dt), 'CMDS', strutil.dumps(_CONFIG_CMDS_))
    #             _CONFIG_CMDS_ = {}
    except:
        ftlog.error()


def ppsCountConfigCmds():
    global _CONFIG_CMDS_, _CONFIG_COUNT_, _CONFIG_COUNT_TIME_
    ct = datetime.now()
    dt = ct - _CONFIG_COUNT_TIME_
    dt = dt.seconds + dt.microseconds / 1000000.0
    pps = '%0.2f' % (_CONFIG_COUNT_ / dt)
    ftlog.hinfo("CONFIG_PPS", pps, 'CMDCOUNT', _CONFIG_COUNT_, 'DT %0.2f' % (dt), 'CMDS', strutil.dumps(_CONFIG_CMDS_))
    _CONFIG_COUNT_TIME_ = ct
    _CONFIG_CMDS_ = {}
    _CONFIG_COUNT_ = 0


def reloadKeys(keylist):
    if len(keylist) == 1 and keylist[0] == 'all':
        ftcon.getConf.clear()
    else:
        ftcon.getConf.clear_keys(keylist)
    _templatesCache.clear()


def _get(redisfullkey, defaultvalue=None, intClientidNum=None):
    if intClientidNum == None:
        rkey = redisfullkey
    else:
        rkey = redisfullkey + ':' + str(intClientidNum)

    if _CONFIG_CMD_PPS_:
        _configCmdPps(rkey)

    value = ftcon.getConf(rkey)
    if value == None:
        ftlog.debug('get configer->', rkey, 'is None !!')
        value = defaultvalue
    if value:
        if not isinstance(value, (list, dict)):
            raise Exception('the configer content is not list or dict !' + rkey)
    return value


def getUuid():
    '''
    取得配置内容的更新的标记, 即配置内容每发生一次变化(由配置脚本或配置界面更新), 此标记变化一次
    其值为一个UUID字符串
    '''
    return _get('configitems:uuid', 'none')


def getJson(redisfullkey, defaultVal=None, intClientidNum=None):
    '''
    取得配置系统的一个键值的json对象值(list或dict类型)
    '''
    return _get(redisfullkey, defaultVal, intClientidNum)


def getGameJson(gameId, key, defaultVal=None, intClientidNum=0):
    '''
    取得配置系统的一个游戏相关的键值的json对象值(list或dict类型)
    '''
    return _get('game:' + str(gameId) + ':' + key, defaultVal, intClientidNum)


def stringIdToNumber(datakey, stringid):
    if stringid == 'UNKNOWN':
        return UNKNOW_ID
    if isinstance(stringid, int):
        return stringid
    # PATCH: 不知道client_id的配置在哪里
    if stringid == "Android_3.901_weixin,tyGuest.alipay.0-hall712.qile.ztmj":
        return 17499
    if stringid.find("hall711") > 0 and stringid.find("qjmj") > 0:
        return 17489

    numDict = _get(datakey, {})
    if not numDict:
        ftlog.warn('configure.stringIdToNumber', datakey, 'NotConfig')
        return UNKNOW_ID
    num = numDict.get(stringid, UNKNOW_ID)
    if num == UNKNOW_ID:
        if stringid.find('robot') < 0:  # 机器人的clientid忽略
            ftlog.warn('configure.stringIdToNumber ', datakey, ' stringid=', stringid, 'Unknown')
        return num
    assert (num > 0)
    return num


_numDictRevertd = {}


def numberToStringId(datakey, numberId):
    rinfo = _numDictRevertd.get(datakey, None)
    ndict = _get(datakey, {})
    if not rinfo or rinfo.get('ndictKey', None) != id(ndict):
        datas = {}
        for k, v in ndict.items():
            datas[v] = k
        rinfo = {'ndictKey': id(ndict),
                 'datas': datas}
        _numDictRevertd[datakey] = rinfo
    else:
        datas = rinfo['datas']

    return datas.get(numberId, '')


def getTemplateInfo(redisfullkey, intClientId, funconvert=None):
    # 0.json 保存的是模板的集合
    # n.json 保存的是对模板ID的引用, 若引用不存在,那么返回模板中的default内容
    alldata = getJson(redisfullkey, {}, DEFAULT_CLIENT_ID)
    if alldata and funconvert:
        convert = getattr(alldata, 'convert', None)
        if convert == None:
            funconvert(redisfullkey, alldata)
            setattr(alldata, 'convert', 1)
    templates = alldata.get('templates', {})

    update = getJson(redisfullkey, {}, intClientId)
    if templates and update:
        key = update.get('template')
        return templates.get(key, templates.get('default', None))
    return templates.get('default', None)


def getGameTemplateInfo(gameId, key, intClientId, funconvert=None):
    # 0.json 保存的是模板的集合
    # n.json 保存的是对模板ID的引用, 若引用不存在,那么返回模板中的default内容
    return getTemplateInfo('game:' + str(gameId) + ':' + key, intClientId, funconvert)


def getTemplates(key, funconvert=None):
    # 0.json 保存的是模板的集合
    # n.json 保存的是对模板ID的引用, 若引用不存在,那么返回模板中的default内容
    alldata = getJson(key, {}, DEFAULT_CLIENT_ID)
    if funconvert:
        convert = getattr(alldata, 'convert', None)
        if convert == None:
            funconvert(key, alldata)
            setattr(alldata, 'convert', 1)
    return alldata.get('templates', {})


def getGameTemplates(gameId, key, funconvert=None):
    return getTemplates('game:' + str(gameId) + ':' + key, funconvert)


def getConfigGameIds():
    return getJson('poker:global', {}).get('config.game.ids', {})


def clientIdToNumber(clientId):
    """
    转换clientID的字符串定义至INTEGER_ID的定义
    """
    if clientId == CLIENTID_RPC or clientId == CLIENTID_SYSCMD or clientId == CLIENTID_ROBOT:
        return 10000
    return stringIdToNumber('poker:map.clientid', clientId)


def numberToClientId(numberId):
    """
    转换clientID的字符串定义至INTEGER_ID的定义
    """
    if numberId == 10000:
        return CLIENTID_ROBOT
    # PATCH: 不知道client_id的配置在哪里
    if numberId == 17499:
        return "Android_3.901_weixin,tyGuest.alipay.0-hall712.qile.ztmj"
    if numberId == 17489:
        return "Android_3.90_weixin,tyGuest.alipay.0-hall711.qiangqiang.qjmj"
    return numberToStringId('poker:map.clientid', numberId)


_templatesCache = {}
_templatesLockers = {}


def getTcTemplates(moduleKey, funDecode):
    '''
    取得配置系统的一个游戏相关的键值的json对象值(list或dict类型)
    '''
    # 若有缓存，直接返回缓存内容， 其缓存内容为funAdjust的返回值，而非原始数据
    datas = _templatesCache.get(moduleKey, None)
    if datas:
        return datas
    else:
        locker = _templatesLockers.get(moduleKey, None)
        if not locker:
            locker = FTLock(moduleKey)
            _templatesLockers[moduleKey] = locker
        with lock(locker):
            return _getTcTemplates(moduleKey, funDecode)


def _getTcTemplates(moduleKey, funDecode):
    # 取得redis中的所有原始数据
    datas = {}
    xkey = 'game:%s:' + moduleKey + ':' + CLIENT_ID_TEMPLATE
    for gid in getConfigGameIds():
        subdata = ftcon.getConfNoCache('GET', xkey % (gid))
        if subdata:
            subdata = strutil.loads(subdata)
            for k, d in subdata.items():
                if not k in datas:
                    if isinstance(d, dict):
                        datas[k] = {}
                    else:
                        datas[k] = []
                if isinstance(d, dict):
                    datas[k].update(d)
                elif isinstance(d, list):
                    datas[k].extend(d)
                else:
                    datas[k] = d
    datas = strutil.replaceObjRefValue(datas)
    if funDecode:
        cachedata = funDecode(moduleKey, datas)
        assert (isinstance(cachedata, dict)), 'the cache templates data must be a dict !' + str(
            moduleKey) + ' funDecode=' + str(funDecode)
    else:
        cachedata = datas['templates']
    _templatesCache[moduleKey] = cachedata

    return cachedata


def getVcTemplate(moduleKey, clientId, gameId=None):
    """
    http://192.168.10.93:8090/pages/viewpage.action?pageId=1868148
    """
    if isinstance(clientId, int):
        strClientId = numberToClientId(clientId)
        numClientId = clientIdToNumber(strClientId)
    else:
        numClientId = clientIdToNumber(clientId)
        strClientId = numberToClientId(numClientId)

    assert (numClientId > 0), 'the clientId int value error, input=' + str(clientId) + ' convert=' + str(
        numClientId) + ' ' + str(strClientId)
    assert (strClientId != ''), 'the clientId str value error, input=' + str(clientId) + ' convert=' + str(
        numClientId) + ' ' + str(strClientId)

    if not gameId:
        gameId = strutil.getGameIdFromHallClientId(strClientId)
        assert (gameId > 0), 'the gameId error, input=' + str(strClientId) + ' convert=' + str(gameId) + ' ' + str(
            numClientId) + ' ' + str(strClientId)

    xkey = 'game:' + str(gameId) + ':' + moduleKey + ':' + CLIENT_ID_MATCHER
    datas = _get(xkey, {})
    if not '_cache' in datas:
        strutil.replaceObjRefValue(datas)
        datas['_cache'] = {}

    _cache = datas['_cache']
    tname = _cache.get(numClientId, None)
    if tname == None:
        # 先判定1：1真实映射
        actual = datas.get('actual', {})
        tname = actual.get(strClientId, None)
        if tname == None:
            tname = actual.get(str(numClientId), None)

        # 第二优先级判定主次渠道，主次渠道可覆盖大部分的批量配置需求，比正则表达式配置难度低
        if tname == None:
            channel = strutil.getChannelFromHallClientId(clientId)
            tname = actual.get(channel, None)

        # 再判定正则表达式映射
        if tname == None:
            for vm in datas.get('virtual', []):
                if strutil.regMatch(vm[0], strClientId):
                    tname = vm[1]
                    break
        # 最后取缺省值
        if tname == None:
            clientSys, _, _ = strutil.parseClientId(strClientId)
            tname = datas.get('default_' + str(clientSys).lower(), None)
        # 最后取缺省值
        if tname == None:
            tname = datas.get('default', None)
        if tname == None:
            ftlog.warn('the clientId can not find template name ' + str(moduleKey) + ' ' + str(
                numClientId) + ' ' + strClientId)
        _cache[numClientId] = tname
    return tname


def getTcTemplatesByClientId(moduleKey, funDecode, clientId):
    '''
    取得配置系统的一个游戏相关的键值的json对象值(list或dict类型)
    '''
    if isinstance(clientId, int):
        strClientId = numberToClientId(clientId)
        numClientId = clientIdToNumber(strClientId)
    else:
        numClientId = clientIdToNumber(clientId)
        strClientId = numberToClientId(numClientId)
    gameId = strutil.getGameIdFromHallClientId(strClientId)
    return getTcTemplatesByGameId(moduleKey, funDecode, gameId)


def getTcTemplatesByGameId(moduleKey, funDecode, gameId):
    '''
    取得配置系统的一个游戏相关的键值的json对象值(list或dict类型)
    '''
    moduleKey = str(gameId) + ':' + str(moduleKey)

    # 若有缓存，直接返回缓存内容， 其缓存内容为funAdjust的返回值，而非原始数据
    datas = _templatesCache.get(moduleKey, None)
    if datas:
        return datas
    else:
        locker = _templatesLockers.get(moduleKey, None)
        if not locker:
            locker = FTLock(moduleKey)
            _templatesLockers[moduleKey] = locker
        with lock(locker):
            return _getTcTemplatesByModuleKey(moduleKey, funDecode)


def _getTcTemplatesByModuleKey(moduleKey, funDecode):
    # 取得redis中的所有原始数据
    xkey = 'game:' + moduleKey + ':' + CLIENT_ID_TEMPLATE
    datas = ftcon.getConfNoCache('GET', xkey)
    if datas:
        datas = strutil.loads(datas)
        datas = strutil.replaceObjRefValue(datas)
    else:
        datas = {'templates': {}}
    if funDecode:
        cachedata = funDecode(moduleKey, datas)
        assert (isinstance(cachedata, dict)), 'the cache templates data must be a dict !' + str(
            moduleKey) + ' funDecode=' + str(funDecode)
    else:
        cachedata = datas['templates']
    _templatesCache[moduleKey] = cachedata

    return cachedata


def getTcContent(moduleKey, funDecode, clientId):
    if isinstance(clientId, int):
        strClientId = numberToClientId(clientId)
        numClientId = clientIdToNumber(strClientId)
    else:
        numClientId = clientIdToNumber(clientId)
        strClientId = numberToClientId(numClientId)
    gameId = strutil.getGameIdFromHallClientId(strClientId)
    moduleKey = str(gameId) + ':' + str(moduleKey)
    templates = getTcTemplates(moduleKey, funDecode)
    tname = getVcTemplate(moduleKey, clientId)
    try:
        return templates[tname]
    except:
        ftlog.error('getTcContent', moduleKey, funDecode, clientId)
        return None


def getTcContentByClientId(moduleKey, funDecode, clientId, defaultVal=None):
    '''
    使用clientId中指向的gameId，进行数据查询
    '''
    templates = getTcTemplatesByClientId(moduleKey, funDecode, clientId)
    if not templates:
        ftlog.warn('getTcContentByClientId', moduleKey, funDecode, clientId, 'templates is None')
        return defaultVal
    tname = getVcTemplate(moduleKey, clientId)
    ftlog.debug('getTcContentByClientId', moduleKey, tname, clientId, templates.get(tname, None))
    try:
        return templates[tname]
    except:
        ftlog.error('getTcContentByClientId', tname, moduleKey, funDecode, clientId)
        return defaultVal


def getTcContentByGameId(moduleKey, funDecode, gameId, clientId, defaultVal=None):
    '''
    忽律clientId中指向的gameId，直接使用参数中的gameId进行数据查询
    '''
    templates = getTcTemplatesByGameId(moduleKey, funDecode, gameId)
    if not templates:
        ftlog.warn('getTcContentByGameId', moduleKey, funDecode, clientId, 'templates is None')
        return defaultVal
    tname = getVcTemplate(moduleKey, clientId, gameId)
    ftlog.debug('getTcContentByGameId', moduleKey, tname, clientId, templates.get(tname, None))
    conf = templates.get(tname, None)
    if conf == None:
        ftlog.warn('getTcContentByGameId', tname, moduleKey, funDecode, clientId, tname, 'conf is none')
        return defaultVal
    return conf
