# -*- coding=utf-8 -*-

'''
Created on 2014年2月20日

@author: zjgzzz@126.com
'''
import time

from freetime.core.tasklet import FTTasklet
from freetime.util import log as ftlog
from poker.entity.configure import gdata
from poker.entity.events.tyevent import TYEvent


class TYEventBus(object):
    def __init__(self):
        # key=eventName, value=set<TYEventHandler>
        self._handlersMap = {}
        # value=TYEventHandler
        self._allEventHandlers = set()

    def subscribe(self, eventType, handler):
        '''订阅eventType的event, 由handler处理, 如果channel为None则表示订阅所有频道'''
        assert (callable(handler))
        if eventType is None:
            self._allEventHandlers.add(handler)
        else:
            if eventType in self._handlersMap:
                self._handlersMap[eventType].add(handler)
            else:
                self._handlersMap[eventType] = set([handler])

    def unsubscribe(self, eventType, handler):
        '''取消订阅eventType的event, 由handler处理, 如果channel为None则表示订阅所有频道'''
        assert (callable(handler))
        if eventType is None:
            self._allEventHandlers.discard(handler)
        elif eventType in self._handlersMap:
            self._handlersMap[eventType].discard(handler)

    def publishEvent(self, event, handleDelay=0, eventErrors=None, **argd):
        '''
        发布一个event, 同一个event不允许重复
        '''
        ftlog.debug('publishEvent ', str(self), 'handleDelay=', handleDelay, 'event=', event)
        assert (isinstance(event, TYEvent))
        if event.timestamp is None:
            event.timestamp = time.time()

        session = gdata.getTaskSession()
        _eventdata = session.get(str(self), None)
        if not _eventdata:
            _eventdata = {'events': [], 'processing': 0}
            session[str(self)] = _eventdata

        _events = _eventdata['events']
        if event not in _events:
            _events.append(event)
            if _eventdata['processing'] != 1:
                _eventdata['processing'] = 1
                while (len(_events) > 0):
                    curEvent = _events[0]
                    del _events[0]
                    self._processEvent(curEvent, handleDelay, eventErrors, **argd)
                _eventdata['processing'] = 0
        return

    def _sleepnb(self, handleDelay):
        if handleDelay > 0:
            FTTasklet.getCurrentFTTasklet().sleepNb(handleDelay)

    def _processEvent(self, event, handleDelay=0, eventErrors=None, **argd):
        try:
            eventType = type(event)
            handlers = set(self._allEventHandlers)
            for handler in handlers:
                try:
                    handler(event)
                    self._sleepnb(handleDelay)
                except:
                    ftlog.error(**argd)
                    if eventErrors != None:
                        eventErrors.append(ftlog.errorInfo(**argd))

            if eventType in self._handlersMap:
                handlers = set(self._handlersMap[eventType])
                for handler in handlers:
                    try:
                        handler(event)
                        self._sleepnb(handleDelay)
                    except:
                        ftlog.error(**argd)
                        if eventErrors != None:
                            eventErrors.append(ftlog.errorInfo(**argd))
        except:
            ftlog.error(**argd)
            if eventErrors != None:
                eventErrors.append(ftlog.errorInfo(**argd))


globalEventBus = TYEventBus()  # 全局事件的注册和监听, 目前有系统心跳, 配置变化
