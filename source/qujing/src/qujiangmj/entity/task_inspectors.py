# -*- coding=utf-8 -*-
from difang.majiang2.entity.events.events import UserTablePlayEvent

from freetime.util import log as ftlog
from poker.entity.biz.task.task import TYTaskInspector, \
    TYTaskInspectorRegister
from qujiangmj.entity.configure.conf import GAMEID


class GameTaskInspectorPlay(TYTaskInspector):
    TYPE_ID = str(GAMEID) + '.play'
    EVENT_GAMEID_MAP = {UserTablePlayEvent: (GAMEID,)}

    def __init__(self):
        super(GameTaskInspectorPlay, self).__init__(self.EVENT_GAMEID_MAP)

    def _processEventImpl(self, task, event):
        if isinstance(event, UserTablePlayEvent) and (event.gameId == GAMEID):
            return task.setProgress(task.progress + 1, event.timestamp)
        return False, 0


def _registerClasses():
    ftlog.info('difang.majiang2_task._registerClasses')
    TYTaskInspectorRegister.registerClass(GameTaskInspectorPlay.TYPE_ID, GameTaskInspectorPlay)
