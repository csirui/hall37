# -*- coding=utf-8 -*-
"""
Created on 2015年7月13日

@author: zhaojiangang
"""
import freetime.util.log as ftlog
import poker.util.timestamp as pktimestamp
from hall.entity import hallitem, datachangenotify, hallconf
from hall.entity import hallpopwnd
from hall.entity import hallvip
from hall.entity.hallconf import HALL_GAMEID
from hall.entity.hallitem import TYOpenItemEvent
from hall.entity.hallroulette import TYEventRouletteDiamond
from hall.entity.hallusercond import UserConditionRegister
from hall.entity.hallvip import TYUserVipLevelUpEvent
from poker.entity.biz.item.item import TYAssetUtils
from poker.entity.biz.message import message
from poker.entity.biz.task.dao import TYTaskDataDao
from poker.entity.biz.task.exceptions import TYTaskConfException, \
    TYTaskAlreayGetRewardException, TYTaskNotFinisheException
from poker.entity.biz.task.task import TYTaskInspector, TYTaskCondition, TYTask, \
    TYTaskKind, TYTaskConditionRegister, TYTaskInspectorRegister, TYTaskKindRegister, \
    TYSubTaskSystem, TYTaskData, TYTaskUnit, TYTaskSystem, TYTaskSystemImpl, TYTaskKindPool, TYUserTaskUnit
from poker.entity.configure import configure
from poker.entity.dao import taskdata
from poker.entity.events import tyeventbus
from poker.entity.events.tyevent import EventConfigure, ChargeNotifyEvent
from poker.util import strutil


class TYTaskDataDaoImpl(TYTaskDataDao):
    # @classmethod
    # def _buildKey(self, gameId, userId):
    #     return 'task2:%s:%s' % (gameId, userId)

    def loadAll(self, gameId, userId):
        '''
        加载用户所有任务
        @return: list(kindId, bytes)
        '''
        return taskdata.getTaskDataAll(userId, gameId)

    def saveTask(self, gameId, userId, kindId, taskDataBytes):
        '''
        保存一个用户的task
        @param kindId: kindId
        @param taskDataBytes: bytes
        '''
        return taskdata.setTaskData(userId, gameId, kindId, taskDataBytes)

    def removeTask(self, gameId, userId, kindId):
        '''
        删除一个用户的task
        @param kindId: kindId
        '''
        return taskdata.delTaskData(userId, gameId, kindId)


class TYItemOpenTaskInspector(TYTaskInspector):
    TYPE_ID = 'hall.item.open'
    EVENT_GAMEID_MAP = {TYOpenItemEvent: (HALL_GAMEID,)}

    def __init__(self):
        super(TYItemOpenTaskInspector, self).__init__(self.EVENT_GAMEID_MAP)

    def _processEventImpl(self, task, event):
        if isinstance(event, TYOpenItemEvent):
            return task.setProgress(task.progress + 1, event.timestamp)
        return False, 0


class TYTaskInspectorRouletteDiamond(TYTaskInspector):
    TYPE_ID = 'hall.roulette.diamond'
    EVENT_GAMEID_MAP = {TYEventRouletteDiamond: (HALL_GAMEID,)}

    def __init__(self):
        super(TYTaskInspectorRouletteDiamond, self).__init__(self.EVENT_GAMEID_MAP)

    def _processEventImpl(self, task, event):
        if isinstance(event, TYEventRouletteDiamond):
            return task.setProgress(task.progress + 1, event.timestamp)
        return False, 0


class TYTaskInspectorVipLevel(TYTaskInspector):
    TYPE_ID = 'hall.vip.level'
    EVENT_GAMEID_MAP = {TYUserVipLevelUpEvent: (HALL_GAMEID,)}

    def __init__(self):
        super(TYTaskInspectorVipLevel, self).__init__(self.EVENT_GAMEID_MAP)

    def _processEventImpl(self, task, event):
        if isinstance(event, TYUserVipLevelUpEvent):
            return task.setProgress(event.userVip.vipLevel.level, event.timestamp)
        return False, 0

    def on_task_created(self, task):
        user_vip = hallvip.userVipSystem.getUserVip(task.userId)
        level = user_vip.vipLevel.level
        if level > 0:
            task.setProgress(level, pktimestamp.getCurrentTimestamp())


class TYTaskInspectorChargeCumulation(TYTaskInspector):
    """
    累积充值任务
    """
    TYPE_ID = 'hall.charge.cumulation'
    EVENT_GAMEID_MAP = {ChargeNotifyEvent: ()}

    def __init__(self):
        super(TYTaskInspectorChargeCumulation, self).__init__(self.EVENT_GAMEID_MAP)

    def _processEventImpl(self, task, event):
        if isinstance(event, ChargeNotifyEvent):
            return task.setProgress(task.progress + event.rmbs, event.timestamp)
        return False, 0


class TYTaskInspectorChargeSingle(TYTaskInspector):
    """
    单次充值任务
    """
    TYPE_ID = 'hall.charge.single'
    EVENT_GAMEID_MAP = {ChargeNotifyEvent: ()}

    def __init__(self):
        super(TYTaskInspectorChargeSingle, self).__init__(self.EVENT_GAMEID_MAP)

    def _processEventImpl(self, task, event):
        if isinstance(event, ChargeNotifyEvent):
            if event.rmbs >= task.taskKind.count:
                return task.setProgress(event.rmbs, event.timestamp)
        return False, 0


class TYTaskConditionItemId(TYTaskCondition):
    TYPE_ID = 'hall.item.open.kindId'

    def __init__(self):
        self._kindIds = set()

    def check(self, task, event):
        if isinstance(event, TYOpenItemEvent):
            return event.item.kindId in self._kindIds
        return False

    def _decodeFromDictImpl(self, d):
        kindIds = d.get('kindIds', [])
        if not isinstance(kindIds, list):
            raise TYTaskConfException(d, 'TYTaskConditionItemId.kindIds must be list')
        for kindId in kindIds:
            if not isinstance(kindId, int):
                raise TYTaskConfException(d, 'TYTaskConditionItemId.kindIds.kindId must be int')
            self._kindIds.add(kindId)


class TYTaskSimple(TYTask):
    def __init__(self, taskKind):
        assert (isinstance(taskKind, TYTaskKindSimple))
        super(TYTaskSimple, self).__init__(taskKind)


class TYTaskSimpleData(TYTaskData):
    def __init__(self):
        super(TYTaskSimpleData, self).__init__()


class TYTaskKindSimple(TYTaskKind):
    TYPE_ID = 'hall.task.simple'

    def __init__(self):
        super(TYTaskKindSimple, self).__init__()
        self.freshTip = None  # 是否显示图片的角标
        # v3.9扩展,未完成时指引跳转
        self._todo_task_factory = None
        self.lblEnter = None  # 指引按钮文字

    def newTaskData(self):
        return TYTaskSimpleData()

    def newTaskForDecode(self):
        return TYTaskSimple(self)

    def newTask(self, prevTask, timestamp):
        task = TYTaskSimple(self)
        task.finishCount = 0
        task.finishTime = 0
        task.gotReward = 0
        task.updateTime = timestamp
        if prevTask and task.taskKind.inheritPrevTaskProgress:
            task.setProgress(prevTask.progress, timestamp)
        return task

    def _decodeFromDictImpl(self, d):
        self.freshTip = d.get('freshTip', False)
        dict_todo = d.get('todotask')
        if dict_todo:
            self._todo_task_factory = hallpopwnd.decodeTodotaskFactoryByDict(dict_todo)
            self.lblEnter = d.get('lblEnter')

    @property
    def todotask_factory(self):
        return self._todo_task_factory


class TYHallTaskModel(object):
    def __init__(self, subTaskSystem, userTaskUnit):
        assert (isinstance(subTaskSystem, TYSubTaskSystem))
        self._subTaskSystem = subTaskSystem
        self._userTaskUnit = userTaskUnit

    @property
    def userId(self):
        return self._userTaskUnit.userId

    @property
    def userTaskUnit(self):
        return self._userTaskUnit

    @property
    def subTaskSystem(self):
        return self._subTaskSystem


class TYHallSubTaskSystem(TYSubTaskSystem):
    NULL_TASK_UNIT = TYTaskUnit()

    def __init__(self, gameId):
        self._gameId = gameId
        self._taskUnit = TYHallSubTaskSystem.NULL_TASK_UNIT

    @property
    def gameId(self):
        return self._gameId

    @property
    def taskUnit(self):
        return self._taskUnit

    def taskUnitValid(self):
        return self._taskUnit and self._taskUnit != TYHallSubTaskSystem.NULL_TASK_UNIT

    def onTaskUnitLoaded(self, taskUnit):
        '''
        当taskUnit加载完成时回调
        '''
        self._taskUnit = taskUnit
        self._onTaskUnitLoadedImpl(taskUnit)

    def getTaskReward(self, task, timestamp, eventId, intEventParam):
        '''
        '''
        assert (task.userTaskUnit)

        if task.gotReward:
            raise TYTaskAlreayGetRewardException(task.kindId)
        if not task.isFinished:
            raise TYTaskNotFinisheException(task.kindId)

        task.gotReward = 1
        task.userTaskUnit.updateTask(task)

        assetList = self._sendTaskReward(task, timestamp, eventId, intEventParam)
        self._onGotTaskReward(task, assetList, timestamp)
        return assetList

    def processEvent(self, userTaskUnit, event):
        '''
        事件处理
        '''
        taskModel = self._loadTaskModel(userTaskUnit, event.timestamp)
        taskList = list(taskModel.userTaskUnit.taskList)
        for task in taskList:
            _changed, finishCount = task.taskKind.processEvent(task, event)
            if _changed:
                userTaskUnit.updateTask(task)
                self._onTaskUpdated(task)
            if finishCount > 0:
                assert (task.isFinished)
                self._onTaskFinished(task, event.timestamp)

    def loadTaskModel(self, userId, timestamp, clientId=None):
        userTaskUnit = self.taskUnit.taskSystem.loadUserTaskUnit(userId, self.taskUnit, timestamp)
        return self._loadTaskModel(userTaskUnit, timestamp)

    def _loadTaskModel(self, userTaskUnit, timestamp):
        pass

    def _onTaskUnitLoadedImpl(self, taskUnit):
        pass

    def _onTaskUpdated(self, task):
        pass

    def _onTaskFinished(self, task, timestamp):
        pass

    def _onGotTaskReward(self, task, assetList, timestamp):
        pass

    def _sendTaskReward(self, task, timestamp, eventId, intEventParam):
        if task.taskKind.rewardContent:
            userAssets = hallitem.itemSystem.loadUserAssets(task.userTaskUnit.userId)
            assetList = userAssets.sendContent(self.gameId, task.taskKind.rewardContent, 1, True,
                                               timestamp, eventId, intEventParam)
            changeNames = TYAssetUtils.getChangeDataNames(assetList)
            rewardMail = task.taskKind.rewardMail
            if rewardMail:
                contents = TYAssetUtils.buildContentsString(assetList)
                rewardMail = strutil.replaceParams(rewardMail,
                                                   {'rewardContent': contents, 'taskName': task.taskKind.name})
                message.send(self.gameId, message.MESSAGE_TYPE_SYSTEM, task.userId, rewardMail)
                changeNames.add('message')
            datachangenotify.sendDataChangeNotify(self.gameId, task.userId, changeNames)
            return assetList
        return []


class HallNewUserSubTaskSystem(TYHallSubTaskSystem):
    """
    福利任务的首次接取(任务池的第一个任务),是前端打开福利界面触发的
    而别的任务系统,只要调用_loadTaskModel,都会触发
    """
    TYPE_ID = 'hall.task.newuser'

    def __init__(self):
        super(HallNewUserSubTaskSystem, self).__init__(HALL_GAMEID)
        self._taskUnit = {}

    def onTaskUnitLoaded(self, taskUnit):
        self._taskUnit[taskUnit.taskUnitId] = taskUnit

    def loadTaskModel(self, userId, timestamp, clientId=None):
        template_name = configure.getVcTemplate('hall_tasks', clientId)
        template = _templates.get(template_name)
        if not template:
            return None
        task_unitid = template.get(self.TYPE_ID)
        if not task_unitid:
            return None
        # 玩家身上只能有一个本类型的taskunit
        task_units = self._taskUnit.values()
        user_task_units = task_units[0].taskSystem.loadUserTaskUnits(userId, task_units, timestamp)
        user_task_units = [temp for temp in user_task_units if temp.taskMap]
        if user_task_units:
            user_task_unit = user_task_units[0]
            if user_task_unit.taskUnitId != task_unitid:
                return None  # 已结取任务,且跟当前模板不一致,那么不显示
        else:
            user_task_unit = TYUserTaskUnit(userId, self._taskUnit.get(task_unitid))
        user_task_unit = self._fix_user_task_unit(user_task_unit, timestamp)
        return self._loadTaskModel(user_task_unit, timestamp)

    def _loadTaskModel(self, user_task_unit, timestamp):
        return TYHallTaskModel(self, user_task_unit)

    def _onTaskFinished(self, task, timestamp):
        datachangenotify.sendDataChangeNotify(HALL_GAMEID, task.userId, 'free')

    # 前一个任务领奖,后一个任务解锁(接取)
    # 但不走这个逻辑,刷任务列表的时候能保证接取
    # 那么为啥?考虑配置的任务后继可能会从无到有,而领奖事件只会触发一次
    # def _onGotTaskReward(self, task, assetList, timestamp):
    #     self._fix_user_task_unit(task.userTaskUnit, timestamp)

    def _fix_user_task_unit(self, user_task_unit, timestamp):
        task_pool = user_task_unit.taskUnit.poolList[0]
        assert isinstance(task_pool, HallTaskKindPoolWithCond)
        # 检查过期条件
        if task_pool.visible_cond and \
                not task_pool.visible_cond.check(self.gameId, user_task_unit.userId, None, timestamp):
            return TYUserTaskUnit(user_task_unit.userId, user_task_unit.taskUnit)
        tasklist = user_task_unit.taskList
        if tasklist:
            for task in tasklist:
                if not task.gotReward:
                    return user_task_unit  # 还有任务没领奖
        else:  # 身上没任务
            # 检查接取条件
            if task_pool.accepted_cond and not task_pool.accepted_cond.check(
                    self.gameId, user_task_unit.userId, None, timestamp):
                return user_task_unit

        # 接新任务
        task_kind = task_pool.nextTaskKind(task_order=len(tasklist))
        if task_kind:
            task = task_kind.newTask(None, timestamp)
            user_task_unit.addTask(task)
        return user_task_unit


class HallChargeSubTaskSystem(TYHallSubTaskSystem):
    """
    任务的首次接取(任务池的第一个任务),是前端打开福利界面触发的
    """
    TYPE_ID = 'hall.task.charge'

    def __init__(self):
        super(HallChargeSubTaskSystem, self).__init__(HALL_GAMEID)

    def loadTaskModel(self, userId, timestamp, clientId=None):
        user_task_unit = self.taskUnit.taskSystem.loadUserTaskUnit(userId, self.taskUnit, timestamp)
        user_task_unit = self._fix_user_task_unit(user_task_unit, timestamp)
        return self._loadTaskModel(user_task_unit, timestamp)

    def _loadTaskModel(self, user_task_unit, timestamp):
        return TYHallTaskModel(self, user_task_unit)

    def _onTaskUpdated(self, task):
        datachangenotify.sendDataChangeNotify(HALL_GAMEID, task.userId, 'free')

    def _fix_user_task_unit(self, user_task_unit, timestamp):
        tasklist = user_task_unit.taskList
        if not tasklist:  # 身上没任务,接第1个pool
            for task_pool in self.taskUnit.poolList:
                task_kind = self._taskpool_get_first(task_pool, user_task_unit.userId, timestamp)
                if not task_kind:
                    continue
                task = task_kind.newTask(None, timestamp)
                user_task_unit.addTask(task)
                break
            return user_task_unit

        task_pool = tasklist[0].taskKind.taskKindPool
        # 如果当前pool过期，找下一个pool；否则看当前pool的任务完成情况
        is_expire = self._taskpool_expire(task_pool, user_task_unit.userId, timestamp)
        if not is_expire:
            for task in tasklist:
                if not task.gotReward:
                    return user_task_unit  # 还有任务没领奖,do nothing

            # 还有后继任务,那么接取；否则找下一个pool
            task_kind = task_pool.nextTaskKind(task_order=len(tasklist))
            if task_kind:
                task = task_kind.newTask(None, timestamp)
                user_task_unit.addTask(task)
                return user_task_unit

        # 找下一个pool
        for task_pool in self.taskUnit.poolList[task_pool.index + 1:]:
            task_kind = self._taskpool_get_first(task_pool, user_task_unit.userId, timestamp)
            if not task_kind:
                continue
            # 同时只能存在一个pool,先删除身上任务
            user_task_unit.removeAllTask()
            task = task_kind.newTask(None, timestamp)
            user_task_unit.addTask(task)
            return user_task_unit

        # 没能找到下一个pool
        return TYUserTaskUnit(user_task_unit.userId, user_task_unit.taskUnit) if is_expire else user_task_unit

    def _taskpool_expire(self, task_pool, userId, curtime):
        return task_pool.visible_cond and not task_pool.visible_cond.check(self.gameId, userId, None, curtime)

    def _taskpool_get_first(self, task_pool, userId, curtime):
        assert isinstance(task_pool, HallTaskKindPoolWithCond)
        # 过期条件
        if self._taskpool_expire(task_pool, userId, curtime):
            return
        # 检查接取条件
        if task_pool.accepted_cond and not task_pool.accepted_cond.check(self.gameId, userId, None, curtime):
            return
        return task_pool.nextTaskKind()


class HallTaskKindPoolWithCond(TYTaskKindPool):
    def __init__(self, taskunit):
        super(HallTaskKindPoolWithCond, self).__init__(taskunit)
        self._accepted_cond = None
        self._visible_cond = None

    @property
    def accepted_cond(self):
        return self._accepted_cond

    @property
    def visible_cond(self):
        return self._visible_cond

    def decodeFromDict(self, d):
        super(HallTaskKindPoolWithCond, self).decodeFromDict(d)
        condition = d.get('acceptedCond')
        if condition:
            self._accepted_cond = UserConditionRegister.decodeFromDict(condition)
        condition = d.get('visibleCond')
        if condition:
            self._visible_cond = UserConditionRegister.decodeFromDict(condition)
        return self


def _registerClasses():
    # 任务条件注册
    TYTaskConditionRegister.registerClass(TYTaskConditionItemId.TYPE_ID, TYTaskConditionItemId)
    # 任务检查员注册
    TYTaskInspectorRegister.registerClass(TYItemOpenTaskInspector.TYPE_ID, TYItemOpenTaskInspector)
    TYTaskInspectorRegister.registerClass(TYTaskInspectorRouletteDiamond.TYPE_ID, TYTaskInspectorRouletteDiamond)
    TYTaskInspectorRegister.registerClass(TYTaskInspectorVipLevel.TYPE_ID, TYTaskInspectorVipLevel)
    TYTaskInspectorRegister.registerClass(TYTaskInspectorChargeCumulation.TYPE_ID, TYTaskInspectorChargeCumulation)
    TYTaskInspectorRegister.registerClass(TYTaskInspectorChargeSingle.TYPE_ID, TYTaskInspectorChargeSingle)
    # 任务种类注册
    TYTaskKindRegister.registerClass(TYTaskKindSimple.TYPE_ID, TYTaskKindSimple)


_taskSystem = TYTaskSystem()
_inited = False
_templates = {}
hall_new_user_task_sys = HallNewUserSubTaskSystem()
hall_charge_task_sys = HallChargeSubTaskSystem()


def _reload_conf():
    if _inited:
        conf = hallconf.getAllTcDatas('hall_tasks')
        _taskSystem.reloadConf(conf)

        conf_templates = conf.get('templates')
        if conf_templates:
            templates = {}
            for name, template in conf_templates.iteritems():
                templates[name] = template
            global _templates
            _templates = templates


def _on_conf_changed(event):
    if _inited and event.isModuleChanged(['hall_tasks']):
        ftlog.info('halltask._on_conf_changed')
        _reload_conf()


def initialize():
    global _inited
    global _taskSystem
    if not _inited:
        _inited = True
        _taskSystem = TYTaskSystemImpl(HALL_GAMEID, TYTaskDataDaoImpl(), HallTaskKindPoolWithCond)
        # 已经废弃了,保留内推广任务为了兼容
        from hall.entity.neituiguangtask import newUserTaskSystem
        _taskSystem.registerSubTaskSystem('hall.task.neituiguang.newUser', newUserTaskSystem)
        _taskSystem.registerSubTaskSystem(HallNewUserSubTaskSystem.TYPE_ID, hall_new_user_task_sys)
        _taskSystem.registerSubTaskSystem(HallChargeSubTaskSystem.TYPE_ID, hall_charge_task_sys)
        _reload_conf()
        tyeventbus.globalEventBus.subscribe(EventConfigure, _on_conf_changed)
