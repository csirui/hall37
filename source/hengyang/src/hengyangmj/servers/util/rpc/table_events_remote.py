# -*- coding=utf-8 -*-
'''
Created on 2015年10月22日

@author: liaoxx
'''
import freetime.util.log as ftlog
from difang.majiang2.entity.events.events import UserTablePlayEvent
from poker.entity.dao import gamedata
from poker.protocol.rpccore import markRpcCall


@markRpcCall(groupName="userId", lockName="", syncCall=1)
def gamePlay(userId, gameId, roomId, tableId, banker):
    ftlog.debug('table_events_remote trigger event UserTablePlayEvent...')
    from hengyangmj.game import TGhengyangmj
    TGhengyangmj.getEventBus().publishEvent(UserTablePlayEvent(gameId
                                                               , userId
                                                               , roomId
                                                               , tableId
                                                               , banker))
    gamedata.incrGameAttr(userId, gameId, 'play_game_count', 1)
