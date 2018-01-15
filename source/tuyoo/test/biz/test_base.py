# -*- coding=utf-8
'''
Created on 2015年6月12日

@author: zhaojiangang
'''
import time

import freetime.util.log as ftlog
from biz.mock import patch
from biz import mock
from poker.entity.dao import daoconst
from poker.entity.events.tyevent import TYEvent
import poker.util.strutil as pkstrutil


class ConfigDBTest(object):
    def __init__(self):
        self._confMap = {}
        
    def clear(self):
        self._confMap = {}
        
    def getConf(self, confname):
        value = self._confMap.get(confname)
        ftlog.debug('ConfigDBTest.getConf name=', confname, 'value=', value)
        return value
    
    def setConf(self, confname, value):
        self._confMap[confname] = value
        ftlog.debug('ConfigDBTest.setConf name=', confname, 'value=', value)
        
    def clearConf(self, confname):
        if confname in self._confMap:
            del self._confMap[confname]
    
class Configure(object):
    def __init__(self, configDB):
        self._configDB = configDB
        
    def _get(self, redisfullkey, defaultvalue=None, intClientidNum=None):
        if intClientidNum == None :
            rkey = redisfullkey
        else:
            assert(isinstance(intClientidNum, (int, long)))
            rkey = redisfullkey + ':' + str(intClientidNum)
        value = self._configDB.getConf(rkey)
        print '**********Configure._get redisfullkey=', redisfullkey, 'value=', value
        if value is None:
            value = defaultvalue
        if value :
            assert(isinstance(value, (list, dict)))
        return value

    def getGameJson(self, gameId, key, defaultVal=None, intClientidNum=0):
        return self._get('game:' + str(gameId) + ':' + key, defaultVal, intClientidNum)

    def setGameJson(self, gameId, key, value, intClientidNum=0):
        key = 'game:' + str(gameId) + ':' + key
        if intClientidNum is not None:
            key = key + ':' + str(intClientidNum)
        self._configDB.setConf(key, value)
        
    def getJson(self, redisfullkey, defaultVal=None, intClientidNum=None):
        return self._get(redisfullkey, defaultVal, intClientidNum)

    def setJson(self, redisfullkey, value, intClientidNum=None):
        if intClientidNum is not None:
            redisfullkey = redisfullkey + ':' + str(intClientidNum)
        self._configDB.setConf(redisfullkey, value)
        
class GameDBTest(object):
    def __init__(self):
        # key=gameId, value=UserDBTest
        self._gameUserDBMap = {}
        
    def clear(self):
        self._gameUserDBMap = {}
        
    def setnxGameAttr(self, userId, gameId, attrname, value):
        userDB = self._ensureUserDBExists(gameId)
        return userDB.setnxAttr(userId, attrname, value)
    
    def delGameAttr(self, userId, gameId, attrname):
        userDB = self._ensureUserDBExists(gameId)
        userDB.removeAttr(userId, attrname)
    
    def getGameAttr(self, userId, gameId, attrname, filterKeywords=True):
        userDB = self._ensureUserDBExists(gameId)
        return userDB.getAttr(userId, attrname, filterKeywords)
    
    def getGameAttrInt(self, userId, gameId, attrname):
        userDB = self._ensureUserDBExists(gameId)
        return userDB.getAttrInt(userId, attrname)
    
    def getGameAttrs(self, userId, gameId, attrlist, filterKeywords=True):
        userDB = self._ensureUserDBExists(gameId)
        return userDB.getAttrs(userId, attrlist, filterKeywords)
    
    def setGameAttr(self, userId, gameId, attrname, value):
        userDB = self._ensureUserDBExists(gameId)
        return userDB.setAttr(userId, attrname, value)
    
    def setGameAttrs(self, userId, gameId, attrlist, valuelist):
        userDB = self._ensureUserDBExists(gameId)
        userDB.setAttrs(userId, attrlist, valuelist)
    
    def incrGameAttr(self, userId, gameId, attrname, value):
        userDB = self._ensureUserDBExists(gameId)
        return userDB.incrAttr(userId, attrname, value)
    
    def incrGameAttrLimit(self, userId, gameId, attrname, deltaCount, lowLimit, highLimit,
                          chipNotEnoughOpMode):
        userDB = self._ensureUserDBExists(gameId)
        return userDB.incrAttrLimit(userId, attrname, deltaCount, lowLimit, highLimit,
                                    chipNotEnoughOpMode)
    
    def _ensureUserDBExists(self, gameId):
        userDB = self._gameUserDBMap.get(gameId)
        if userDB is None:
            userDB = UserDBTest()
            self._gameUserDBMap[gameId] = userDB
        return userDB

class UserDBTest(object):
    def __init__(self):
        # key=userId, value=map<attrname, attrvalue>
        self._userAttrMap = {}
        
    def clear(self):
        self._userAttrMap = {}
        
    def clearUser(self, userId):
        if userId in self._userAttrMap:
            del self._userAttrMap[userId]
            
    def setnxAttr(self, userId, attrname, value):
        attrMap = self._userAttrMap.get(userId)
        if attrMap and attrname in attrMap:
            return 0
        attrMap[attrname] = value
        return 1
    
    def removeAttr(self, userId, attrname):
        attrMap = self._userAttrMap.get(userId)
        if attrMap and attrname in attrMap:
            del attrMap[attrname]
            
    def getAllAttrs(self, userId):
        d = self._userAttrMap.get(userId)
        if not d:
            return None
        ret = []
        for k,v in d.iteritems():
            ret.append(k)
            ret.append(v)
        return ret
        
    def getAttr(self, userId, attrname, filterKeywords=True):
        attrMap = self._userAttrMap.get(userId)
        if attrMap:
            return attrMap.get(attrname)
        return None
    
    def getAttrs(self, userId, attrlist, filterKeywords=True):
        ret = []
        for attrname in attrlist:
            ret.append(self.getAttr(userId, attrname, filterKeywords))
        return ret
    
    def getAttrInt(self, userId, attrname):
        attrMap = self._userAttrMap.get(userId)
        if attrMap:
            value = attrMap.get(attrname, 0)
            if isinstance(value, int):
                return value
        return 0
    
    def setAttr(self, userId, attrname, value):
        attrMap = self._ensureUserExists(userId)
        ret = 0 if attrname in attrMap else 1
        attrMap[attrname] = value
        return ret

    def setAttrs(self, userId, attrlist, valuelist):
        assert(len(attrlist) <= len(valuelist))
        for i, attrname in enumerate(attrlist):
            self.setAttr(userId, attrname, valuelist[i])
            
    def incrAttr(self, userId, attrname, value):
        attrMap = self._ensureUserExists(userId)
        oldValue = attrMap.get(attrname, 0)
        if not isinstance(oldValue, int):
            raise ValueError('incrAttr %s must be int' % (attrname))
        attrMap[attrname] = value + oldValue
        return attrMap[attrname]

    def incrAttrLimit(self, userId, attrname, deltaCount, lowLimit, highLimit,
                      chipNotEnoughOpMode):
        '''
        @return: trueDelta, final, fixCount
        '''
        assert(chipNotEnoughOpMode == daoconst.CHIP_NOT_ENOUGH_OP_MODE_CLEAR_ZERO 
           or chipNotEnoughOpMode == daoconst.CHIP_NOT_ENOUGH_OP_MODE_NONE)
        
        attrMap = self._ensureUserExists(userId)
        oldValue = attrMap.get(attrname, 0)
        fixCount = 0
        if oldValue < 0:
            fixCount = -oldValue
            attrMap[attrname] = 0
            oldValue = 0
        
        final = oldValue + deltaCount
        if lowLimit >= 0 and final < lowLimit:
            return 0, oldValue, fixCount
        if highLimit >= 0 and final > highLimit:
            return 0, oldValue, fixCount
        
        if deltaCount > 0 or final >= 0:
            attrMap[attrname] = final
            return deltaCount, final, fixCount
        
        if (chipNotEnoughOpMode == daoconst.CHIP_NOT_ENOUGH_OP_MODE_NONE
            or oldValue == 0):
            return 0, oldValue, fixCount
        attrMap[attrname] = 0
        return -oldValue, 0, fixCount 
            
    def getExp(self, userId):
        return self.getAttrInt(userId, daoconst.ATT_EXP)
        
    def incrExp(self, userId, detalExp):
        _, final, _ = self.incrAttrLimit(userId, daoconst.ATT_EXP, detalExp, 0, -1,
                                              daoconst.CHIP_NOT_ENOUGH_OP_MODE_CLEAR_ZERO)
        return final

    def getCharm(self, userId):
        return self.getAttr(userId, daoconst.ATT_CHARM)

    def incrCharm(self, userId, detalCharm):
        _, final, _ = self.incrAttrLimit(userId, daoconst.ATT_CHARM, detalCharm, 0, -1,
                                        daoconst.CHIP_NOT_ENOUGH_OP_MODE_CLEAR_ZERO)
        return final

    def _ensureUserExists(self, userId):
        attrMap = self._userAttrMap.get(userId)
        if attrMap is None:
            attrMap = {}
            self._userAttrMap[userId] = attrMap
        return attrMap
    
class UserChip(object):
    _isbuyin = 1
    def __init__(self, userDB, gameDB):
        self.userDB = userDB
        self.gameDB = gameDB
        
    def getUserChipAll(self, userId):
        return self.userDB.getAttrInt(userId, daoconst.ATT_CHIP)
    
    def incrUserChipField(self, userId, gameId, deltaCount, lowLimit, highLimit, chipNotEnoughOpMode,
                          eventId, chipType, intEventParam, clientId, tableId=0):
        assert(isinstance(userId, int))
        assert(isinstance(gameId, int))
        assert(isinstance(deltaCount, int))
        assert(isinstance(lowLimit, int))
        assert(isinstance(highLimit, int))
        assert(isinstance(chipNotEnoughOpMode, int))
        assert(isinstance(chipType, int))
        
#         def incrAttrLimit(self, userId, attrname, deltaCount, lowLimit, highLimit,
#                       chipNotEnoughOpMode):
#             
# def incrGameAttrLimit(self, userId, gameId, attrname, deltaCount, lowLimit, highLimit,
#                           chipNotEnoughOpMode):
        userChipTypeMap = {
            daoconst.CHIP_TYPE_CHIP:daoconst.ATT_CHIP,
            daoconst.CHIP_TYPE_COIN:daoconst.ATT_COIN,
            daoconst.CHIP_TYPE_DIAMOND:daoconst.ATT_DIAMOND,
            daoconst.CHIP_TYPE_COUPON:daoconst.ATT_COUPON,
        }
        field = userChipTypeMap.get(chipType)
        if field:
            trueDelta, finalCount, fixed = self.userDB.incrAttrLimit(userId, field, deltaCount, lowLimit, highLimit, chipNotEnoughOpMode)
        elif field == daoconst.CHIP_TYPE_TABLE_CHIP:
            trueDelta, finalCount, fixed = self.gameDB.incrGameAttrLimit(userId, gameId, field, deltaCount, lowLimit, highLimit, chipNotEnoughOpMode)
        else:
            raise ValueError('Unknown chipType %s' % (chipType))
    
        ftlog.debug('UserChip->incr_user_chip_filed', userId, gameId, deltaCount, lowLimit, highLimit,
                                 chipNotEnoughOpMode, eventId, chipType, field,
                                 'result->', trueDelta, finalCount, fixed)
        return trueDelta, finalCount

class TYEventBusSample(object):

    def __init__(self):
        # key=eventName, value=set<TYEventHandler>
        self.__handlersMap = {}
        # value=TYEventHandler
        self.__allEventHandlers = set()
        # 当前等待处理的events
        self.__events = []
        # 正在处理消息
        self.__processing = False

    def subscribe(self, eventType, handler):
        '''订阅eventType的event, 由handler处理, 如果channel为None则表示订阅所有频道'''
        assert(handler)
        if eventType is None:
            self.__allEventHandlers.add(handler)
        else:
            if eventType in self.__handlersMap:
                self.__handlersMap[eventType].add(handler)
            else:
                self.__handlersMap[eventType] = set([handler])
            
    def unsubscribe(self, eventType, handler):
        '''取消订阅eventType的event, 由handler处理, 如果channel为None则表示订阅所有频道'''
        assert(callable(handler))
        if eventType is None:
            self.__allEventHandlers.discard(handler)
        elif eventType in self.__handlersMap:
            self.__handlersMap[eventType].discard(handler)
        
    def publishEvent(self, event):
        '''发布一个event'''
        assert(isinstance(event, TYEvent))
        if event.timestamp is None:
            event.timestamp = time.time()
        self.__events.append(event)
        if not self.__processing:
            self.__processing = True
            while (len(self.__events) > 0):
                curEvent = self.__events[0]
                del self.__events[0]
                self._processEvent(curEvent)
            self.__processing = False
            
    def _processEvent(self, event):
        try:
            eventType = type(event)
            handlers = set(self.__allEventHandlers)
            for handler in handlers:
                try:
                    handler(event)
                except:
                    ftlog.error()
            if eventType in self.__handlersMap:
                handlers = set(self.__handlersMap[eventType])
                for handler in handlers:
                    try:
                        handler(event)
                    except:
                        ftlog.error()
        except:
            ftlog.error()


def _bireport(arglist, argdict):
    jsondata = ['BIREPORT', 'test']
    jsondata.extend(arglist)
    jsondata.append(argdict)
    msg = pkstrutil.dumps(jsondata)
    ftlog.info(msg)

class MessageTest(object):
    def __init__(self):
        pass
    
    def clear(self):
        pass
    
    def sendPrivate(self, gameId, toUid, fromUid, msg):
        ftlog.info('MessageTest.sendPrivate gameId=', gameId,
                   'toUid=', toUid,
                   'fromUid=', fromUid,
                   'msg=', msg)
    
class GdataTest(object):
    def __init__(self):
        self._gameMap = {}
        
    def setGame(self, game):
        self._gameMap[game.gameId()] = game
        
    def games(self):
        '''
        取得当前系统初始化后的TYGame的所有实例
        key为: int(gameId)
        value为: TYGame()
        注: 由poker系统initialize()方法进行初始化
        '''
        return self._gameMap


    def gameIds(self):
        '''
        取得当前系统初始化后的TYGame的ID列表
        注: 由poker系统initialize()方法进行初始化
        '''
        return self._gameMap.keys()
    
class TestRouter(object):
    def sendToUser(self, msgpack, userId):
        ftlog.info('TestRouter.sendToUser userId=', userId, 'msg=', msgpack)
        
class TestMockContext(object):
    def __init__(self):
        self.userDB = UserDBTest()
        self.gameDB = GameDBTest()
        self.confDB = ConfigDBTest()
        self.messageDB = MessageTest()
        self.configure = Configure(self.confDB)
        self.userChip = UserChip(self.userDB, self.gameDB)
        self.gdataTest = GdataTest()
        self.router = TestRouter()
        
        self.globalEventBus = TYEventBusSample()
        self.eventBusPatcher = patch('poker.entity.events.tyeventbus.globalEventBus', self.globalEventBus)
        self.gameDataPatcher = mock._patch_multiple('poker.entity.dao.gamedata',
                                                    getGameAttr=self.gameDB.getGameAttr,
                                                    getGameAttrs=self.gameDB.getGameAttrs,
                                                    setGameAttr=self.gameDB.setGameAttr,
                                                    setGameAttrs=self.gameDB.setGameAttrs,
                                                    incrGameAttr=self.gameDB.incrGameAttr,
                                                    setnxGameAttr=self.gameDB.setnxGameAttr,
                                                    incrGameAttrLimit=self.gameDB.incrGameAttrLimit,
                                                    delGameAttr=self.gameDB.delGameAttr)
        self.confPatcher = patch('freetime.entity.config.getConf', self.confDB.getConf)
        self.userChipPatcher = patch('poker.entity.dao.userchip._incrUserChipFiled', self.userChip.incrUserChipField)
        self.userAllChipPatcher = patch('poker.entity.dao.userchip.getUserChipAll', self.userChip.getUserChipAll)
        self.bireportPatcher = patch('poker.entity.biz.bireport._report', _bireport)
        self.userDataPatcher = mock._patch_multiple('poker.entity.dao.userdata',
                                                    getAttr=self.userDB.getAttr,
                                                    getAttrs=self.userDB.getAttrs,
                                                    getAttrInt=self.userDB.getAttrInt,
                                                    setAttr=self.userDB.setAttr,
                                                    setnxAttr=self.userDB.setnxAttr,
                                                    incrAttr=self.userDB.incrAttr,
                                                    incrAttrLimit=self.userDB.incrAttrLimit,
                                                    getExp=self.userDB.getExp,
                                                    incrExp=self.userDB.incrExp,
                                                    getCharm=self.userDB.getCharm,
                                                    incrCharm=self.userDB.incrCharm)
        self.messagePatcher = mock._patch_multiple('poker.entity.biz.message.message',
                                                    sendPrivate=self.messageDB.sendPrivate)
        self.gdataPatcher = mock._patch_multiple('poker.entity.configure.gdata',
                                                 games=self.gdataTest.games,
                                                 gameIds=self.gdataTest.gameIds)
        self.routerPatcher = mock._patch_multiple('poker.protocol.router',
                                                  sendToUser=self.router.sendToUser)
        
    def startMock(self):
        self.eventBusPatcher.start()
        self.userChipPatcher.start()
        self.userAllChipPatcher.start()
        self.confPatcher.start()
        self.gameDataPatcher.start()
        self.bireportPatcher.start()
        self.userDataPatcher.start()
        self.messagePatcher.start()
        self.gdataPatcher.start()
        self.routerPatcher.start()
        self._startMockImpl()
        
    def stopMock(self):
        self.confPatcher.stop()
        self.userChipPatcher.stop()
        self.userAllChipPatcher.stop()
        self.gameDataPatcher.stop()
        self.bireportPatcher.stop()
        self.userDataPatcher.stop()
        self.eventBusPatcher.stop()
        self.messagePatcher.stop()
        self.gdataPatcher.stop()
        self.routerPatcher.stop()
        
        self.userDB.clear()
        self.gameDB.clear()
        self.confDB.clear()
        self.itemDataDao.clear()
        self.messageDB.clear()
        self._stopMockImpl()
        
    def _startMockImpl(self):
        pass
    
    def _stopMockImpl(self):
        pass
    
    
    