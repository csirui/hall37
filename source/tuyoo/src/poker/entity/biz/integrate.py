# -*- coding=utf-8
'''
Created on 2015年6月3日

@author: zhaoqh
'''
import freetime.util.log as ftlog
from freetime.entity import clients
from poker.entity.configure import pokerconf, gdata

_DEBUG = 0
debug = ftlog.info

_inited = 0


def _initialize():
    if _DEBUG:
        debug('poker.integrate._initialize begin')
    global _inited
    if not _inited:
        _inited = True
        _reloadConf()
        from poker.entity.events.tyevent import EventConfigure
        import poker.entity.events.tyeventbus as pkeventbus
        pkeventbus.globalEventBus.subscribe(EventConfigure, _onConfChanged)
    if _DEBUG:
        debug('poker.integrate._initialize end')


def _onConfChanged(event):
    if _inited and event.isChanged('poker:global'):
        if _DEBUG:
            debug('poker.integrate._onConfChanged')
        _reloadConf()


def _reloadConf():
    integrates = pokerconf.getIntegrate()
    if _DEBUG:
        debug('poker.integrate._reloadConf', integrates)
    _resetIntegrate('logcenter', integrates)
    _resetIntegrate('chatlog', integrates)
    _resetIntegrate('pushserver', integrates)
    _resetIntegrate('bireport', integrates)


def _resetIntegrate(adapterKey, integrates):
    conf = integrates.get(adapterKey, {})  # 配置为空，不启动集成
    if conf:
        if '*' in conf['serverTypes']:
            pass  # 所有类型的进程全部启动集成
        else:
            if gdata.serverType() in conf['serverTypes']:
                pass  # 当前类型的进程全部启动集成
            else:
                conf = {}  # 不启动集成
    clients.resetAdapters(adapterKey, conf)


def sendTo(adapterKey, dictData, headerDict=None):
    clients.sendToAdapter(adapterKey, dictData, headerDict)


def isEnabled(adapterKey):
    return clients.isEnabled(adapterKey)
