# -*- coding=utf-8 -*-
import time

import freetime.entity.config as ftcon
import freetime.util.log as ftlog
from freetime.core.lock import locked
from freetime.core.tasklet import FTTasklet
from freetime.core.timer import FTLoopTimer
from poker.entity.configure import gdata
from poker.util import strutil, webpage

_DEBUG = 0
debug = ftlog.info
_REPORT_OK = 0


def doSyncData(event):
    _doReportStatus(event)
    _doCheckReloadConfig(event)


def _doReportStatus(event):
    global _REPORT_OK
    if (event.count % 600 == 1 or _REPORT_OK == 0) \
            and gdata.isControlProcess() \
            and len(gdata.serverTypeMap().get(gdata.SRV_TYPE_HTTP, [])) > 0:
        '''
        每10分钟, 汇报一次, 服务在线, 且 只有当控制进程时才汇报, 否者视为非游戏大厅服务
        只需要第一个进程进行汇报即可
        '''
        try:
            _reportOnlineToSdk(_lockobj)
        except:
            ftlog.error()


class _lockobj():
    pass


_lockobj = _lockobj()


@locked
def _reportOnlineToSdk(_lockobj):
    '''
    向当前的SDK服务汇报自己的运行状态
    '''
    posturl = '%s/_game_server_online_?' % (gdata.httpSdkInner())
    datas = {'http_game': gdata.httpGame(),
             'conns': gdata.getUserConnIpPortList(),
             'mode': gdata.mode(),
             'name': gdata.name(),
             'time': int(time.time())
             }
    datas = strutil.dumpsbase64(datas)
    ret, _ = webpage.webgetJson(posturl, {'params': datas}, None, 10)
    if isinstance(ret, dict):
        result = ret.get('result', {})
        ok = result.get('ok', False)
        if ok == True:
            global _REPORT_OK
            _REPORT_OK = True
            ftlog.debug('_reportOnlineToSdk-> OK !', ret)
            return
    ftlog.debug('_reportOnlineToSdk-> ERROR !', ret)


def _doCheckReloadConfig(event):
    # 每15秒检查一次数据同步, event为None即为手工进行执行推送
    if event == None or (event.count > 0 and event.count % 15 == 0):
        FTLoopTimer(0.01, 0, _syncConfigure, _lockobj).start()


_CHANGE_INDEX = -1
_CHANGE_KEYS_NAME = 'configitems.changekey.list'
_LAST_ERRORS = None


def _initialize():
    global _CHANGE_INDEX
    if _CHANGE_INDEX < 0:
        _CHANGE_INDEX = ftcon.getConfNoCache('LLEN', _CHANGE_KEYS_NAME)


@locked
def _syncConfigure(_lockobj):
    global _CHANGE_INDEX, _LAST_ERRORS
    changindex = ftcon.getConfNoCache('LLEN', _CHANGE_KEYS_NAME)
    keys = []
    ftlog.debug('_syncConfigure _CHANGE_INDEX=', _CHANGE_INDEX, 'changindex=', changindex)
    if changindex > _CHANGE_INDEX:
        keys = ftcon.getConfNoCache('LRANGE', _CHANGE_KEYS_NAME, _CHANGE_INDEX, changindex)
        if keys != None and len(keys) > 0:
            for x in xrange(len(keys)):
                keys[x] = str(keys[x])
            errors = _reloadConfigLocked(keys, 0.1)
            _LAST_ERRORS = errors  # 记录上次的失败信息，在获取更新状态时返回
            if not errors:
                _CHANGE_INDEX = changindex
            else:
                # 发送报警邮件
                ftlog.sendException(errors)
    elif changindex < _CHANGE_INDEX:
        _CHANGE_INDEX = changindex


def _sleepnb(sleepTime=0.01):
    if sleepTime > 0:
        FTTasklet.getCurrentFTTasklet().sleepNb(sleepTime)


def _reloadConfigLocked(keylist, sleepTime=0.01):
    from poker.entity.configure import configure
    from poker.entity.events.tyevent import EventConfigure
    from poker.entity.events.tyeventbus import globalEventBus

    ftlog.info('_syncConfigure._reloadConfig keylist=', keylist)
    if 'all' in keylist:
        keylist = ['all']
    configure.reloadKeys(keylist)
    _sleepnb(sleepTime)

    eventErrors = []
    datas = {'errorLogGroup': 'configure',
             'errorLogParams': keylist
             }
    try:
        _updateRoomDefine(keylist, sleepTime)
    except:
        ftlog.error(**datas)
        eventErrors.append(ftlog.errorInfo())
        return eventErrors

    ftlog.info('_syncConfigure._triggerCnfigureChangedEvent in')
    globalEventBus.publishEvent(EventConfigure(keylist, []), sleepTime, eventErrors, **datas)
    ftlog.info('_syncConfigure._triggerCnfigureChangedEvent out')

    ftlog.info('_syncConfigure finis erros len=', len(eventErrors))
    return eventErrors


def _updateRoomDefine(keylist, sleepTime):
    import json
    from poker.entity.game import quick_start
    isall = 1 if len(keylist) == 1 and keylist[0] == 'all' else 0
    if _DEBUG:
        debug('_syncConfigure._updateRoomDefine-> in', keylist)
    _sleepnb(sleepTime)
    keylist = set(keylist)
    changedGameIds = []
    changedBigRoomIds = []
    for gid, bigRoomIds in gdata.gameIdBigRoomidsMap().items():
        rkey = 'game:' + str(gid) + ':room:0'
        if isall or rkey in keylist:
            changedGameIds.append([rkey, gid])
        for bigRoomId in bigRoomIds:
            rkey = 'game:' + str(gid) + ':room:' + str(bigRoomId)
            if isall or rkey in keylist:
                changedBigRoomIds.append([rkey, bigRoomId])

    changeRoomIds = set([])
    for changed in changedGameIds:
        rkey = changed[0]
        gid = changed[1]
        if _DEBUG:
            debug('_syncConfigure._updateRoomDefine-> reload roomdef', rkey)
        roomdict = ftcon.getConfNoCache('GET', rkey)
        if roomdict:
            roomdict = json.loads(roomdict)
        if not isinstance(roomdict, dict):
            continue
        for roomIdStr, configure in roomdict.items():
            bigRoomId = int(roomIdStr)
            # 所有BIGROOMID下的configure是同一个对象，update第一个即可
            roomid0 = gdata.bigRoomidsMap()[bigRoomId][0]
            room0 = gdata.roomIdDefineMap()[roomid0]
            room0.configure.update(configure)
            changeRoomIds.add(bigRoomId)
            if _DEBUG:
                debug('_syncConfigure._updateRoomDefine-> reload roomdef by 0.json', bigRoomId)
            _sleepnb(sleepTime)

    for changed in changedBigRoomIds:
        rkey = changed[0]
        bigRoomId = changed[1]
        if _DEBUG:
            debug('_syncConfigure._updateRoomDefine-> reload roomdef', rkey)
        extdict = ftcon.getConfNoCache('GET', rkey)
        if extdict:
            extdict = json.loads(extdict)
        if not isinstance(extdict, dict):
            continue
            # 所有BIGROOMID下的configure是同一个对象，update第一个即可
        roomid0 = gdata.bigRoomidsMap()[bigRoomId][0]
        room0 = gdata.roomIdDefineMap()[roomid0]
        room0.configure.update(extdict)
        changeRoomIds.add(bigRoomId)
        if _DEBUG:
            debug('_syncConfigure._updateRoomDefine-> reload roomdef by ' + str(bigRoomId) + '.json', bigRoomId)
        _sleepnb(sleepTime)

    if changeRoomIds:
        for _, roomIns in gdata.rooms().items():
            if roomIns.bigRoomId in changeRoomIds:
                if _DEBUG:
                    debug('_syncConfigure._updateRoomDefine-> reload roomins', roomIns.roomId)
                rdef = gdata.roomIdDefineMap().get(roomIns.roomId)
                roomIns.doReloadConf(rdef)
                _sleepnb(sleepTime)

        quick_start._CANDIDATE_ROOM_IDS = {}

    _sleepnb(sleepTime)
    if _DEBUG:
        debug('_syncConfigure._updateRoomDefine-> out')
