# -*- coding:utf-8 -*-
'''
Created on 2016年2月4日

@author: zhaojiangang
'''
from poker.entity.game.rooms.big_match_ctrl.matchrecord import MatchRecord


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


MatchRecord.Record.fromDict = fromDict

if __name__ == '__main__':
    pass
