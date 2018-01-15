# -*- coding=utf-8 -*-
import freetime.util.log as ftlog
from hall.entity import hallstore
from hall.entity.hallactivity.activity_type import TYActivityType
from hall.entity.todotask import TodoTaskFirstRechargeFactory, TodoTaskFirstRechargeRewardFactory
from hall.entity.todotask import TodoTaskPayOrder
from poker.entity.biz.activity.activity import TYActivity
from poker.entity.configure import gdata
from poker.entity.dao import day1st
from poker.util import strutil


class TYActivityFirstCharge(TYActivity):
    TYPE_ID = TYActivityType.ACTIVITY_FIRST_CHARGE

    def getConfigForClient(self, gameId, userId, clientId):
        if day1st.isDayFirstLogin(userId, gameId):
            return None
        clientConf = strutil.cloneData(self._clientConf)
        firstChargeHasSent = hallstore.isGetFirstRechargeReward(userId)
        if firstChargeHasSent:
            return None
        tyGame = gdata.getGame(gameId)
        if not tyGame:
            return None
        userGameInnings = tyGame.getPlayGameCount(userId, clientId)
        if userGameInnings < 5:
            return None
        isFirstRecharged = hallstore.isFirstRecharged(userId)
        try:
            if not isFirstRecharged:
                rechargeFactory = TodoTaskFirstRechargeFactory().decodeFromDict(
                    self._serverConf.get("firstCharge", {})
                )
                product = rechargeFactory._getProduct(gameId, userId)
                todoTask = TodoTaskPayOrder(product)
                clientConf["config"]["button"]["todoTask"] = todoTask.toDict()
            else:
                rewardFactory = TodoTaskFirstRechargeRewardFactory.decodeFromDict(
                    self._serverConf.get("firstChargeReward", {})
                )
                clientConf["config"]["button"]["todoTask"] = rewardFactory.newTodoTask(gameId, userId,
                                                                                       clientId).toDict()
        except:
            ftlog.exception("TYActivityFirstCharge.getConfigForClient error")
            return None

        return clientConf
