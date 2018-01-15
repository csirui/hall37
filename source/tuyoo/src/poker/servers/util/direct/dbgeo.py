# -*- coding=utf-8

import time

from poker.entity.dao import daobase
from poker.entity.dao.daoconst import GameGeoSchema


def _setUserGeoOffline(userId, gameId):
    return daobase._sendGeoCmd('ZADD', GameGeoSchema.mkey(gameId), int(time.time() + 3600 * 4), userId)
