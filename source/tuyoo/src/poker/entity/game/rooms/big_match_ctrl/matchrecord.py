'''
Created on 2015年3月11日

@author: zhaojiangang, zhouhao
'''
import json

import freetime.util.log as ftlog
from poker.entity.dao import gamedata
from poker.entity.events.tyevent import MatchWinloseEvent


class MatchRecord(object):
    class Record(object):
        def __init__(self, bestRank, crownCount, playCount):
            assert (isinstance(bestRank, (int, float)) and bestRank >= 0)
            assert (isinstance(crownCount, int) and crownCount >= 0)
            assert (isinstance(playCount, int) and playCount >= 0)
            self.bestRank = int(bestRank)
            self.crownCount = crownCount
            self.playCount = playCount

        def update(self, rank):
            if self.bestRank <= 0 or rank < self.bestRank:
                self.bestRank = int(rank)
            if rank == 1:
                self.crownCount += 1
            self.playCount += 1

        @classmethod
        def fromDict(cls, d):
            bestRank = d.get('bestRank', 0)
            crownCount = d.get('crownCount', 0)
            playCount = d.get('playCount', 0)
            if (not isinstance(bestRank, (int, float)) or
                    not isinstance(crownCount, int) or
                    not isinstance(playCount, int)):
                return None
            return MatchRecord.Record(int(bestRank), crownCount, playCount)

        def toDict(self):
            return {'bestRank': int(self.bestRank), 'crownCount': self.crownCount, 'playCount': self.playCount}

    @classmethod
    def initialize(cls, eventBus):
        eventBus.subscribe(MatchWinloseEvent, cls.onMatchWinlose)

    @classmethod
    def onMatchWinlose(cls, event):
        record = cls.loadRecord(event.gameId, event.userId, event.matchId)
        if record is None:
            record = MatchRecord.Record(0, 0, 0)
        record.update(event.rank)
        cls.saveRecord(event.gameId, event.userId, event.matchId, record)

    @classmethod
    def loadRecord(cls, gameId, userId, matchId):
        try:
            jstr = gamedata.getGameAttr(userId, gameId, cls.__buildField(matchId))

            if ftlog.is_debug():
                ftlog.debug('MatchRecord.loadRecord gameId=', gameId,
                            'userId=', userId,
                            'matchId=', matchId,
                            'data=', jstr,
                            caller=cls)
            if jstr:
                return MatchRecord.Record.fromDict(json.loads(jstr))
        except:
            ftlog.exception()
        return None

    @classmethod
    def saveRecord(cls, gameId, userId, matchId, record):
        gamedata.setGameAttr(userId, gameId, cls.__buildField(matchId), json.dumps(record.toDict()))

    @classmethod
    def __buildField(cls, matchId):
        return 'm.%s' % (matchId)

# if __name__ == '__main__':
#     from freetime.util.testbase import initContext
#     from freetime.games.dizhu.game import GameDizhu
#     initContext()
#     TyContext.RedisGame.execute(10001, 'del', 'gamedata:6:10001')
#     MatchRecord.initialize(GameDizhu)
#     record = MatchRecord.loadRecord(6, 10001, 610)
#     assert(record is None)
#     GameDizhu.eventBus.publishEvent(MatchWinloseEvent(6, 10001, 610, True, 10))
#     record = MatchRecord.loadRecord(6, 10001, 610)
#     assert(record.crownCount == 0)
#     assert(record.bestRank == 10)
#     assert(record.playCount == 1)
#     
#     GameDizhu.eventBus.publishEvent(MatchWinloseEvent(6, 10001, 610, True, 9))
#     record = MatchRecord.loadRecord(6, 10001, 610)
#     assert(record.crownCount == 0)
#     assert(record.bestRank == 9)
#     assert(record.playCount == 2)
#     
#     GameDizhu.eventBus.publishEvent(MatchWinloseEvent(6, 10001, 610, True, 1))
#     record = MatchRecord.loadRecord(6, 10001, 610)
#     assert(record.crownCount == 1)
#     assert(record.bestRank == 1)
#     assert(record.playCount == 3)
#     
#     GameDizhu.eventBus.publishEvent(MatchWinloseEvent(6, 10001, 610, True, 10))
#     record = MatchRecord.loadRecord(6, 10001, 610)
#     assert(record.crownCount == 1)
#     assert(record.bestRank == 1)
#     assert(record.playCount == 4)
#     
#     GameDizhu.eventBus.publishEvent(MatchWinloseEvent(6, 10001, 610, True, 1))
#     record = MatchRecord.loadRecord(6, 10001, 610)
#     assert(record.crownCount == 2)
#     assert(record.bestRank == 1)
#     assert(record.playCount == 5)
#     
#     GameDizhu.eventBus.publishEvent(MatchWinloseEvent(6, 10001, 610, True, 1))
#     record = MatchRecord.loadRecord(6, 10001, 610)
#     assert(record.crownCount == 3)
#     assert(record.bestRank == 1)
#     assert(record.playCount == 6)
# 
#     GameDizhu.eventBus.publishEvent(MatchWinloseEvent(6, 10001, 610, True, 100))
#     record = MatchRecord.loadRecord(6, 10001, 610)
#     assert(record.crownCount == 3)
#     assert(record.bestRank == 1)
#     assert(record.playCount == 7)
#     print 'test ok'
