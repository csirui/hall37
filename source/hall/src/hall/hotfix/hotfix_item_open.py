# -*- coding=utf-8
'''
Created on 2015年10月15日

@author: zhaojiangang
'''
import freetime.util.log as ftlog
from hall.entity import hallitem
from poker.entity.biz.item.item import TYItemActionCondition
from poker.entity.dao import sessiondata


class ItemActionConditionGameDashifenLevel(TYItemActionCondition):
    '''
    大师分等级
    '''
    TYPE_ID = 'item.action.cond.game.dashifen.level'

    def __init__(self):
        super(ItemActionConditionGameDashifenLevel, self).__init__()
        self.minLevel = None
        self.maxLevel = None
        self.gameId = None

    def _conform(self, gameId, userAssets, item, timestamp, params):
        userId = userAssets.userId
        clientId = sessiondata.getClientId(userId)
        from hall.entity import hallaccount
        info = hallaccount.getGameInfo(userId, clientId)

        if ftlog.is_debug():
            ftlog.debug('ItemActionConditionGameDashifenLevel.check gameInfo:', info)

        dashifen = info.get('dashifen', {})

        level = 0
        if gameId in dashifen:
            level = dashifen[gameId].get('level', 0)
            if ftlog.is_debug():
                ftlog.debug('ItemActionConditionGameDashifenLevel.check level:', info)
        else:
            return False

        return (self.minLevel == -1 or level >= self.minLevel) \
               and (self.maxLevel == -1 or level < self.maxLevel)


hallitem.ItemActionConditionGameDashifenLevel._conform = ItemActionConditionGameDashifenLevel._conform
