# -*- coding:utf-8 -*-
'''
Created on 2016年5月13日

@author: zhaojiangang
'''
from poker.entity.events.tyevent import TYEvent


class MatchStartSigninEvent(TYEvent):
    def __init__(self, gameId, instId):
        super(MatchStartSigninEvent, self).__init__()
        self.gameId = gameId
        self.instId = instId


class MatchCancelEvent(TYEvent):
    def __init__(self, gameId, instId, reason):
        super(MatchCancelEvent, self).__init__()
        self.gameId = gameId
        self.instId = instId
        self.reason = reason


class MatchingEvent(TYEvent):
    def __init__(self, gameId, instId, matchingId):
        super(MatchingEvent, self).__init__()
        self.gameId = gameId
        self.instId = instId
        self.matchingId = matchingId


class MatchingStartEvent(MatchingEvent):
    def __init__(self, gameId, instId, matchingId):
        super(MatchingStartEvent, self).__init__(gameId, instId, matchingId)


class MatchingStageStartEvent(MatchingEvent):
    def __init__(self, gameId, instId, matchingId, stageIndex):
        super(MatchingStageStartEvent, self).__init__(gameId, instId, matchingId)
        self.stageIndex = stageIndex


class MatchingStageFinishEvent(MatchingEvent):
    def __init__(self, gameId, instId, matchingId, stageIndex):
        super(MatchingStageFinishEvent, self).__init__(gameId, instId, matchingId)
        self.stageIndex = stageIndex


class MatchingFinishEvent(MatchingEvent):
    def __init__(self, gameId, instId, matchingId):
        super(MatchingFinishEvent, self).__init__(gameId, instId, matchingId)
