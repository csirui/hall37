# -*- coding=utf-8 -*-
'''
Created on 2015年6月29日

@author: zhaojiangang
'''
import random
import struct
from sre_compile import isstring

import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from poker.entity.biz.confobj import TYConfable, TYConfableRegister
from poker.entity.biz.content import TYContentRegister
from poker.entity.biz.exceptions import TYBizBadDataException
from poker.entity.biz.task.dao import TYTaskDataDao
from poker.entity.biz.task.exceptions import TYTaskConfException
from poker.entity.configure import gdata
from poker.util import strutil


class TYTaskInspector(TYConfable):
    def __init__(self, interestEventMap):
        self._conditionList = None
        self._interestEventMap = interestEventMap

    @property
    def interestEventMap(self):
        return self._interestEventMap

    def processEvent(self, task, event):
        eventType = type(event)
        if eventType not in self._interestEventMap:
            return False, 0
        if self._conditionList:
            for condition in self._conditionList:
                if not condition.check(task, event):
                    return False, 0
        if 0 < task.taskKind.totalLimit <= task.finishCount:
            return False, 0

        changed, finishCount = self._processEventImpl(task, event)
        if changed:
            task.updateTime = pktimestamp.getCurrentTimestamp()
        return changed, finishCount

    def decodeFromDict(self, d):
        conditions = d.get('conditions', [])
        self._conditionList = TYTaskConditionRegister.decodeList(conditions)
        self._decodeFromDictImpl(d)
        return self

    def _decodeFromDictImpl(self, d):
        pass

    def _processEventImpl(self, task, event):
        raise NotImplementedError

    def on_task_created(self, task):
        pass


class TYTaskInspectorRegister(TYConfableRegister):
    _typeid_clz_map = {}


class TYTaskKind(TYConfable):
    """
    任务种类
    """

    def __init__(self):
        # 属于哪个任务池
        self.taskKindPool = None
        # 配置
        self.conf = None
        # 种类ID
        self.kindId = None
        # 名称
        self.name = None
        # 需要完成的数量
        self.count = None
        # 最大能完成几次
        self.totalLimit = None
        # 说明
        self.desc = None
        # 图片
        self.pic = None
        # 完成任务后给的奖励内容TYContent
        self.rewardContent = None
        self.rewardMail = None
        # 是否自动领取奖励
        self.autoSendReward = None
        # 监控者们
        self.inspectors = []
        # 是否继承上一个任务的进度
        self.inheritPrevTaskProgress = None
        # 下一个任务
        self.nextTaskKind = None
        # 星级
        self.star = None
        self.shareUrl = None
        self.resetProgressWhenFinish = False

    @property
    def taskUnit(self):
        return self.taskKindPool.taskUnit

    def decodeFromDict(self, d):
        self.conf = d
        self.kindId = d.get('kindId')
        if not isinstance(self.kindId, int):
            raise TYTaskConfException(d, 'task.kindId must be int')
        self.name = d.get('name')
        if not isstring(self.name):
            raise TYTaskConfException(d, 'task.name must be string')
        self.count = d.get('count')
        if not isinstance(self.count, int):
            raise TYTaskConfException(d, 'task.count must be int')

        self.totalLimit = d.get('totalLimit', 0)
        if not isinstance(self.totalLimit, int):
            raise TYTaskConfException(d, 'task.totalLimit must be int')

        self.desc = d.get('desc', '')
        if not isstring(self.desc):
            raise TYTaskConfException(d, 'task.desc must be string')

        self.pic = d.get('pic', '')
        if not isstring(self.pic):
            raise TYTaskConfException(d, 'task.pic must be string')

        self.inheritPrevTaskProgress = d.get('inheritPrevTaskProgress', 0)
        if self.inheritPrevTaskProgress not in (0, 1):
            raise TYTaskConfException(d, 'task.inheritPrevTaskProgress must be int in (0, 1)')

        self.star = d.get('star', 0)
        if not isinstance(self.star, int):
            raise TYTaskConfException(d, 'task.star must be int')
        self.shareUrl = d.get('shareUrl', 0)
        if self.shareUrl not in (0, 1):
            raise TYTaskConfException(d, 'task.shareUrl must be in (0,1)')

        rewardContent = d.get('rewardContent')
        if rewardContent:
            self.rewardContent = TYContentRegister.decodeFromDict(rewardContent)
            self.autoSendReward = d.get('autoSendReward', 0)
            if self.autoSendReward not in (0, 1):
                raise TYTaskConfException(d, 'task.n must be int int (0, 1)')

            self.rewardMail = d.get('rewardMail', '')
            if not isstring(self.rewardMail):
                raise TYTaskConfException(d, 'task.rewardMail must be string')

        if 'inspector' in d:
            inspector = TYTaskInspectorRegister.decodeFromDict(d.get('inspector'))
            self.inspectors.append(inspector)
        elif 'inspectors' in d:
            self.inspectors = TYTaskInspectorRegister.decodeList(d.get('inspectors'))

        self._decodeFromDictImpl(d)
        return self

    def newTaskData(self):
        raise NotImplementedError

    def newTaskForDecode(self):
        raise NotImplementedError

    def newTask(self, prevTask, timestamp):
        raise NotImplementedError

    def _decodeFromDictImpl(self, d):
        pass

    def processEvent(self, task, event):
        for inspector in self.inspectors:
            reProcess, count = inspector.processEvent(task, event)
            if reProcess:
                return reProcess, count
        return False, 0


class TYTaskData(object):
    BASE_STRUCT_FMT = '4iB'
    BASE_STRUCT_LEN = struct.calcsize(BASE_STRUCT_FMT)

    def __init__(self):
        self.progress = None
        self.finishCount = None
        self.finishTime = None
        self.updateTime = None
        self.gotReward = None

    @classmethod
    def encodeToBytes(cls, taskData):
        dataBytes = struct.pack(TYTaskData.BASE_STRUCT_FMT, taskData.progress, taskData.finishCount,
                                taskData.finishTime, taskData.updateTime, taskData.gotReward)
        structFormat = taskData._getStructFormat()
        if structFormat:
            fieldValues = []
            fieldNames = taskData._getFieldNames()
            for fieldName in fieldNames:
                fieldValues.append(getattr(taskData, fieldName))
            dataBytes = dataBytes + struct.pack(structFormat, *fieldValues)
        return dataBytes

    @classmethod
    def decodeFromBytes(cls, taskData, dataBytes):
        dataBytes = strutil.unicode2Ascii(dataBytes)
        taskData.progress, taskData.finishCount, taskData.finishTime, taskData.updateTime, taskData.gotReward = \
            struct.unpack(TYTaskData.BASE_STRUCT_FMT, dataBytes[0:TYTaskData.BASE_STRUCT_LEN])

        structFormat = taskData._getStructFormat()
        if structFormat:
            formatLen = struct.calcsize(structFormat)
            fieldValues = struct.unpack(structFormat,
                                        dataBytes[TYTaskData.BASE_STRUCT_LEN:TYTaskData.BASE_STRUCT_LEN + formatLen])
            fieldNames = taskData._getFieldNames()
            if len(fieldValues) != len(fieldNames):
                raise TYBizBadDataException('Failed to decode task data')
            for i, fieldName in enumerate(fieldNames):
                setattr(taskData, fieldName, fieldValues[i])
        return taskData

    def _getStructFormat(self):
        return None

    def _getFieldNames(self):
        return None


class TYTask(object):
    def __init__(self, taskKind):
        # 哪种任务
        self.taskKind = taskKind
        # 本此任务进度
        self.progress = 0
        # 总共完成该任务多少次
        self.finishCount = 0
        # 完成任务时间
        self.finishTime = 0
        # 是否领取了奖励
        self.gotReward = 0
        # 最后更新时间
        self.updateTime = 0
        # 用户tasking
        self._userTaskUnit = None

    @property
    def kindId(self):
        return self.taskKind.kindId

    @property
    def taskUnit(self):
        return self.taskKind.taskUnit

    @property
    def taskUnitId(self):
        return self.taskUnit.taskUnitId

    @property
    def userId(self):
        return self._userTaskUnit.userId

    @property
    def userTaskUnit(self):
        return self._userTaskUnit

    @userTaskUnit.setter
    def userTaskUnit(self, userTaskUnit):
        self._userTaskUnit = userTaskUnit
        for inspector in self.taskKind.inspectors:
            inspector.on_task_created(self)

    @property
    def isFinished(self):
        return self.finishCount > 0

    def setProgress(self, progress, timestamp):
        if 0 < self.taskKind.totalLimit <= self.finishCount:
            return False, 0
        if progress == self.progress:
            return False, 0

        self.updateTime = timestamp
        if progress < self.taskKind.count:
            self.progress = progress
            return True, 0

        if self.taskKind.resetProgressWhenFinish:
            self.progress = 0
        else:
            self.progress = self.taskKind.count
            # self.progress = progress
        self.finishCount += 1
        self.finishTime = timestamp
        return True, 1

    def encodeToTaskData(self):
        taskData = self.taskKind.newTaskData()
        taskData.kindId = self.kindId
        taskData.progress = self.progress
        taskData.finishCount = self.finishCount
        taskData.finishTime = self.finishTime
        taskData.gotReward = self.gotReward
        taskData.updateTime = self.updateTime
        self._encodeToTaskData(taskData)
        return taskData

    def decodeFromTaskData(self, taskData):
        self.progress = taskData.progress
        self.finishCount = taskData.finishCount
        self.finishTime = taskData.finishTime
        self.gotReward = taskData.gotReward
        self.updateTime = taskData.updateTime
        self._decodeFromTaskData(taskData)
        return self

    def _encodeToTaskData(self, taskData):
        pass

    def _decodeFromTaskData(self, taskData):
        pass


class TYTaskCondition(TYConfable):
    def check(self, task, event):
        '''
        判断是否符合条件
        @return: True/False
        '''
        raise NotImplementedError

    def decodeFromDict(self, d):
        self._decodeFromDictImpl(d)
        return self

    def _decodeFromDictImpl(self, d):
        pass


class TYTaskConditionRegister(TYConfableRegister):
    _typeid_clz_map = {}


class TYTaskKindRegister(TYConfableRegister):
    _typeid_clz_map = {}


class TYTaskKindPool(object):
    def __init__(self, taskUnit):
        self.conf = None
        # 属于哪个任务单元
        self._taskUnit = taskUnit
        # 任务列表
        self._taskKindList = None
        # 任务key=kindId, value=taskKind
        self._taskKindMap = None
        # 如何获取下一个任务
        self._nextType = None
        # 索引值
        self._index = None
        # v3.9扩展,显示指定任务顺序
        self._task_order = None

    @property
    def taskUnit(self):
        return self._taskUnit

    @property
    def taskKindList(self):
        return self._taskKindList

    @property
    def nextType(self):
        return self._nextType

    @property
    def index(self):
        return self._index

    @property
    def taskKindMap(self):
        return self._taskKindMap

    @property
    def task_order(self):
        return self._task_order

    def findTaskKind(self, kindId):
        return self._taskKindMap.get(kindId)

    def nextTaskKind(self, prevTaskKind=None, task_order=0):
        if not self.taskKindList:
            return None

        if self.nextType == 'next':
            if prevTaskKind and prevTaskKind.nextTaskKind:
                return prevTaskKind.nextTaskKind
            return self.taskKindList[0]
        elif self.nextType == 'nextByOrder':
            return self.findTaskKind(self.task_order[task_order]) if len(self.task_order) > task_order else None
        return self.taskKindList[random.randint(0, len(self.taskKindList) - 1)]

    def decodeFromDict(self, d):
        self.conf = d
        task_kind_map = {}
        task_kind_list = []
        task_kind_dict_list = d.get('tasks', [])
        for taskKindDict in task_kind_dict_list:
            task_kind = TYTaskKindRegister.decodeFromDict(taskKindDict)
            if task_kind.kindId in task_kind_map:
                raise TYTaskConfException(taskKindDict, 'Duplicate taskKind %s' % task_kind.kindId)
            task_kind_map[task_kind.kindId] = task_kind
            task_kind_list.append(task_kind)
            task_kind.taskKindPool = self

        next_type = d.get('nextType', 'random')
        if next_type not in ('next', 'nextByOrder', 'random'):
            raise TYTaskConfException(d, 'nextType must int ("next", "nextByOrder", "random")')

        if next_type == 'next':
            for i in xrange(len(task_kind_list) - 1):
                task_kind_list[i].nextTaskKind = task_kind_list[i + 1]
        elif next_type == 'nextByOrder':  # v3.9扩展,显示指定任务顺序
            self._task_order = d.get('taskOrder')
            if not self._task_order:
                raise TYTaskConfException(d, 'nextByOrder must define taskOrder')
            for task_kind_id in self._task_order:
                if task_kind_id not in task_kind_map:
                    raise TYTaskConfException(self._task_order, 'taskKind %s not in pool' % task_kind_id)

        self._nextType = next_type
        self._taskKindMap = task_kind_map
        self._taskKindList = task_kind_list
        return self


class TYTaskUnit(TYConfable):
    '''
    一个任务单元，包含n个任务池
    '''

    def __init__(self, _task_kind_pool_cls=None):
        self.conf = None
        # 任务单元ID
        self._taskUnitId = None
        # 该任务单元包含的所有任务类型
        self._taskKindMap = None
        # 任务池
        self._poolList = None
        # 发奖时
        self._taskSystem = None
        # 绑定的子任务系统
        self._subTaskSystem = None
        self._task_kind_pool_cls = _task_kind_pool_cls if _task_kind_pool_cls else TYTaskKindPool
        self._type_id = None  # 3.9扩展,支持模板任务

    @property
    def gameId(self):
        return self._taskSystem.gameId

    @property
    def taskUnitId(self):
        return self._taskUnitId

    @property
    def taskSystem(self):
        return self._taskSystem

    @property
    def subTaskSystem(self):
        return self._subTaskSystem

    @property
    def taskKindMap(self):
        return self._taskKindMap

    @property
    def poolList(self):
        return self._poolList

    @property
    def typeid(self):
        return self._type_id if self._type_id else self.taskUnitId

    def findTaskKind(self, kindId):
        '''
        根据kindId查找taskKind
        '''
        return self._taskKindMap.get(kindId)

    def decodeFromDict(self, d):
        self.conf = d
        self._taskUnitId = d.get('taskUnitId')
        if not self._taskUnitId:
            raise TYTaskConfException(d, 'Bad unitId %s' % (self._taskUnitId))

        self._type_id = d.get('typeId')
        poolDictList = d.get('pools', [])
        if not isinstance(poolDictList, list):
            raise TYTaskConfException(d, 'pools must be list')

        poolList = []
        for i, poolDict in enumerate(poolDictList):
            taskKindPool = self._task_kind_pool_cls(self).decodeFromDict(poolDict)
            taskKindPool._index = i
            poolList.append(taskKindPool)

        taskKindMap = {}
        for pool in poolList:
            for taskKind in pool.taskKindList:
                if taskKind.kindId in taskKindMap:
                    raise TYTaskConfException(taskKind.conf, 'Duplicate taskKind %s' % (taskKind.kindId))
                taskKindMap[taskKind.kindId] = taskKind
        self._poolList = poolList
        self._taskKindMap = taskKindMap
        return self


class TYUserTaskUnit(object):
    def __init__(self, userId, taskUnit):
        self._userId = userId
        self._taskUnit = taskUnit
        self._taskMap = {}

    @property
    def userId(self):
        return self._userId

    @property
    def taskUnit(self):
        return self._taskUnit

    @property
    def taskUnitId(self):
        return self._taskUnit.taskUnitId

    @property
    def taskSystem(self):
        return self._taskUnit.taskSystem

    @property
    def taskList(self):
        return self._taskMap.values()

    @property
    def taskMap(self):
        return self._taskMap

    def findTask(self, kindId):
        return self._taskMap.get(kindId)

    def addTask(self, task):
        assert (task.taskUnit == self._taskUnit)
        assert (task.userTaskUnit is None)
        self._addTaskToMap(task)
        self.taskSystem._saveTask(self.userId, task)

    def removeAllTask(self):
        taskMap = self._taskMap
        self._taskMap = {}
        for task in taskMap.values():
            self.taskSystem._removeTask(self.userId, task)

    def removeTask(self, task):
        assert (task.userTaskUnit == self)
        self._removeFromMap(task)
        self.taskSystem._removeTask(self.userId, task)

    def updateTask(self, task):
        assert (task.userTaskUnit == self)
        self.taskSystem._saveTask(self.userId, task)

    def _addTaskToMap(self, task):
        self._taskMap[task.kindId] = task
        task.userTaskUnit = self

    def _removeFromMap(self, task):
        del self._taskMap[task.kindId]
        task._userTaskUnit = None


# class TYTaskDao(object):
#     def __init__(self, taskSystem, dataDao):
#         self._dataDao = dataDao
#         self._taskSystem = taskSystem
#
#     def loadAll(self, gameId, userId):
#         ret = []
#         taskDataBytesList = self._dataDao.loadAll(gameId, userId)
#         unknownKindIdList = []
#         for kindId, taskDataBytes in taskDataBytesList:
#             task = self._decodeTask(gameId, userId, kindId, taskDataBytes)
#             if not task:
#                 unknownKindIdList.append(kindId)
#             else:
#                 ret.append(task)
#         return ret, unknownKindIdList
#
#     def saveTask(self, gameId, userId, task):
#         taskDataBytes = TYTaskData.encodeToBytes(task.encodeToTaskData())
#         self._dataDao.saveTask(gameId, userId, task.kindId, taskDataBytes)
#
#     def removeTask(self, gameId, userId, task):
#         self._dataDao.removeTask(gameId, userId, task.kindId)
#
#     def _decodeTask(self, gameId, userId, kindId, taskDataBytes):
#         try:
#             taskKind = self._taskSystem.findTaskKind(kindId)
#             if not taskKind:
#                 ftlog.info('TYTaskDao._decodeTask gameId=', gameId,
#                            'userId=', userId,
#                            'kindId=', kindId,
#                            'err=', 'NotFoundTaskKind')
#                 return None
#             taskData = taskKind.newTaskData()
#             TYTaskData.decodeFromBytes(taskData, taskDataBytes)
#             task = taskKind.newTaskForDecode()
#             task.decodeFromTaskData(taskData)
#             return task
#         except:
#             ftlog.info('TYTaskDao._decodeTask gameId=', gameId,
#                        'userId=', userId,
#                        'kindId=', kindId,
#                        'taskData=', taskData,
#                        'err=', 'DecodeData')
#         return None

# class TYUserTasking(object):
#     def __init__(self, userId, taskSystem):
#         self._userId = userId
#         self._userTaskUnitMap = {}
#     
#     @property
#     def userId(self):
#         return self._userId
#             
#     @property
#     def userTaskUnitMap(self):
#         return self._userTaskUnitMap
# 
#     def addUserTaskUnit(self, userTaskUnit):
#         self._userTaskUnitMap[userTaskUnit.taskUnitId] = userTaskUnit
#         
#     def getUserTaskUnit(self, taskUnitId):
#         return self._userTaskUnitMap.get(taskUnitId)


class TYSubTaskSystem(object):
    @property
    def gameId(self):
        raise NotImplementedError

    def onTaskUnitLoaded(self, taskUnit):
        '''
        当taskUnit加载完成时回调
        '''
        pass

    def processEvent(self, userTaskUnit, event):
        '''
        事件处理
        '''
        pass

    def decodeFromDict(self, d):
        pass


class TYTaskSystem(object):
    def getAllTaskUnit(self):
        '''
        获取所有任务单元
        '''
        raise NotImplementedError

    def findTaskKind(self, kindId):
        '''
        根据kindId查找taskKind
        '''
        raise NotImplementedError

    def findTaskUnit(self, taskUnitId):
        '''
        根据taskUnitId查找taskUnit
        @return: TYTaskUnit
        '''
        raise NotImplementedError


#
#     def loadUserTasking(self, userId):
#         '''
#         加载用户执行的任务单元
#         '''
#         raise NotImplementedError

# class TYTaskSystemDelegate(object):
#     pass


class TYTaskSystemImpl(TYTaskSystem):
    def __init__(self, gameId, taskDataDao, _task_kind_pool_cls=None):
        assert (isinstance(taskDataDao, TYTaskDataDao))
        self._gameId = gameId
        self._dataDao = taskDataDao
        # 所有taskUnit
        self._taskUnitMap = {}
        # 所有taskKind
        self._taskKindMap = {}
        # key=eventType, value=set(gameId)
        self._interestEventMap = {}
        # key=taskUnitId, value=subTaskSystem
        self._subTaskSystemMap = {}
        self._loaded = False
        self._task_kind_pool_cls = _task_kind_pool_cls if _task_kind_pool_cls else TYTaskKindPool

    def reloadConf(self, conf):
        taskUnitMap = {}
        task_unit_types = set()
        taskKindMap = {}
        taskUnitDictList = conf.get('taskUnits', [])
        if len(taskUnitDictList) == 0:
            return

        for taskUnitDict in taskUnitDictList:
            taskUnit = TYTaskUnit(self._task_kind_pool_cls).decodeFromDict(taskUnitDict)
            if taskUnit.taskUnitId in taskUnitMap:
                raise TYTaskConfException(taskUnitDict,
                                          'Duplicate taskUnit gameId=%s %s' % (self.gameId, taskUnit.taskUnitId))
            for taskKind in taskUnit.taskKindMap.values():
                if taskKind.kindId in taskKindMap:
                    raise TYTaskConfException(taskUnitDict,
                                              'Duplicate taskKind gameId=%s %s' % (self.gameId, taskKind.kindId))
                taskKindMap[taskKind.kindId] = taskKind
            taskUnitMap[taskUnit.taskUnitId] = taskUnit
            task_unit_types.add(taskUnit.typeid)
            taskUnit._taskSystem = self
            taskUnit._subTaskSystem = self._subTaskSystemMap.get(taskUnit.typeid)

        for task_unit_type in self._subTaskSystemMap.iterkeys():
            # 检查所有的子任务系统是否配置了taskUnit
            if task_unit_type not in task_unit_types:
                raise TYTaskConfException(conf, 'Not found task_unit_type %s' % task_unit_type)

        self._unregisterEvents()
        self._taskUnitMap = taskUnitMap
        self._taskKindMap = taskKindMap
        for taskunit in taskUnitMap.itervalues():
            sub_sys = self._subTaskSystemMap.get(taskunit.typeid)
            if sub_sys:
                sub_sys.onTaskUnitLoaded(taskunit)
        self._registerEvents()
        self._loaded = True
        if ftlog.is_debug():
            ftlog.debug('TYTaskSystemImpl.reloadConf successed units=', self._taskUnitMap.keys(),
                        'kindIds=', self._taskKindMap.keys(),
                        'subTaskSystem=', self._subTaskSystemMap.keys())

    @property
    def gameId(self):
        return self._gameId

    def registerSubTaskSystem(self, taskUnitId, subTaskSystem):
        assert (not self._loaded)
        assert (taskUnitId not in self._subTaskSystemMap)
        self._subTaskSystemMap[taskUnitId] = subTaskSystem

    def getAllTaskUnit(self):
        '''
        获取所有任务单元
        '''
        return self._taskUnitMap.values()

    def findTaskKind(self, kindId):
        '''
        根据kindId查找taskKind
        '''
        return self._taskKindMap.get(kindId)

    def findTaskUnit(self, taskUnitId):
        '''
        根据taskUnitId查找taskUnit
        @return: TYTaskUnit
        '''
        return self._taskUnitMap.get(taskUnitId)

    def loadUserTaskUnit(self, userId, taskUnit, timestamp):
        """
        加载用户执行的某个任务单元
        """
        return self.loadUserTaskUnits(userId, [taskUnit], timestamp)[0]

    def loadUserTaskUnits(self, userId, taskUnitList, timestamp):
        """
        加载用户执行的某些任务单元
        """
        unknownKindIdList = []
        userTaskUnitMap = {taskUnit.taskUnitId: TYUserTaskUnit(userId, taskUnit) for taskUnit in taskUnitList}
        taskDataBytesList = self._dataDao.loadAll(self.gameId, userId)

        # 删除不能识别的任务
        for kindId, taskDataBytes in taskDataBytesList:
            task_kind = self.findTaskKind(kindId)
            if not task_kind:
                unknownKindIdList.append(kindId)
            else:
                userTaskUnit = userTaskUnitMap.get(task_kind.taskUnit.taskUnitId)
                if userTaskUnit:
                    task = self._decodeTask(userId, kindId, taskDataBytes)
                    userTaskUnit._addTaskToMap(task)

        for kindId in unknownKindIdList:
            self._dataDao.removeTask(self.gameId, userId, kindId)
        return userTaskUnitMap.values()

    def _registerEvents(self):
        for taskKind in self._taskKindMap.values():
            for inspector in taskKind.inspectors:
                for eventType, gameIds in inspector.interestEventMap.iteritems():
                    gameIds = gameIds or gdata.gameIds()
                    for gameId in gameIds:
                        game = gdata.games().get(gameId)
                        if game:
                            game.getEventBus().subscribe(eventType, self._handleEvent)
                            self._addInterestEventType(eventType, gameId)
                            if ftlog.is_debug():
                                ftlog.debug('TYTaskSystemImpl._registerEvents eventType=', eventType,
                                            'gameId=', gameId,
                                            'taskUnitId=', taskKind.taskUnit.taskUnitId)
                        else:
                            ftlog.warn('TYTaskSystemImpl._registerEvents gameId=', gameId,
                                       'err=', 'Not find game')

    def _unregisterEvents(self):
        for eventType, gameIds in self._interestEventMap.iteritems():
            for gameId in gameIds:
                game = gdata.games().get(gameId)
                if game:
                    game.getEventBus().unsubscribe(eventType, self._handleEvent)
                else:
                    ftlog.warn('TYTaskSystemImpl._registerEvents gameId=', gameId,
                               'err=', 'Not find game')
        self._interestEventMap = {}

    def _addInterestEventType(self, eventType, gameId):
        gameIdSet = self._interestEventMap.get(eventType)
        if gameIdSet is None:
            gameIdSet = set()
            self._interestEventMap[eventType] = gameIdSet
        gameIdSet.add(gameId)

    def _handleEvent(self, event):
        if ftlog.is_debug():
            ftlog.debug('TYTaskSystemImpl._handleEvent gameId=', event.gameId,
                        'userId=', event.userId,
                        'event=', event,
                        'needHandle=', type(event) in self._interestEventMap)

        if type(event) not in self._interestEventMap:
            return

        userTaskUnitList = self.loadUserTaskUnits(event.userId, self._taskUnitMap.values(), event.timestamp)

        for userTaskUnit in userTaskUnitList:
            if userTaskUnit.taskUnit.subTaskSystem:
                userTaskUnit.taskUnit.subTaskSystem.processEvent(userTaskUnit, event)

    def _saveTask(self, userId, task):
        taskDataBytes = TYTaskData.encodeToBytes(task.encodeToTaskData())
        self._dataDao.saveTask(self.gameId, userId, task.kindId, taskDataBytes)

    def _removeTask(self, userId, task):
        self._dataDao.removeTask(self.gameId, userId, task.kindId)

    def _decodeTask(self, userId, kindId, taskDataBytes):
        try:
            taskKind = self.findTaskKind(kindId)
            if not taskKind:
                ftlog.info('TYTaskSystemImpl._decodeTask gameId=', self.gameId,
                           'userId=', userId,
                           'kindId=', kindId,
                           'err=', 'NotFoundTaskKind')
                return None
            taskData = taskKind.newTaskData()
            TYTaskData.decodeFromBytes(taskData, taskDataBytes)
            task = taskKind.newTaskForDecode()
            task.decodeFromTaskData(taskData)
            return task
        except:
            ftlog.error('TYTaskSystemImpl._decodeTask gameId=', self.gameId,
                        'userId=', userId,
                        'kindId=', kindId,
                        'taskData=', taskData,
                        'err=', 'DecodeData')
        return None
