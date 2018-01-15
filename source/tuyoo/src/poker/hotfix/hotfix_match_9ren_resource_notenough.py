# -*- coding:utf-8 -*-
'''
Created on 2016年8月11日

@author: zhaojiangang
'''
import time

from poker.entity.biz import bireport
from poker.entity.game.rooms.group_match_ctrl.const import MatchFinishReason
from poker.entity.game.rooms.group_match_ctrl.match import MatchInst
from poker.entity.game.rooms.group_match_ctrl.utils import PlayerSort


def _doStart(self):
    assert (self._state < MatchInst.ST_STARTING)
    self._logger.info('MatchInst._doStart ...',
                      'state=', self._state,
                      'signerCount=', self.signerCount)
    self._state = MatchInst.ST_STARTING
    startTime = time.time()
    totalSignerCount = self.signerCount
    self._lockSigners()
    toKickSigners = []

    if self.matchConf.start.isTimingType():
        # 删除不能处理的（达到最大人数）玩家
        signers = sorted(self._signerMap.values(), cmp=PlayerSort.cmpBySigninTime)
        toKickSigners = signers[self.matchConf.start.userMaxCountPerMatch:]
        for signer in toKickSigners:
            del self._signerMap[signer.userId]
            self.area.playerNotifier.notifyMatchCancelled(signer,
                                                          MatchFinishReason.RESOURCE_NOT_ENOUGH,
                                                          MatchFinishReason.toString(
                                                              MatchFinishReason.RESOURCE_NOT_ENOUGH))
    bireport.matchLockUser(self.area.gameId, self.area.roomId,
                           self.matchId, self.area.matchName,
                           instId=self.instId,
                           signinUserCount=totalSignerCount,
                           lockedUserCount=self.signerCount,
                           lockedUserIds=self._signerMap.keys())
    self._logger.info('MatchInst._doStart lockOk',
                      'state=', self._state,
                      'signerCount=', self.signerCount,
                      'kickCount=', len(toKickSigners),
                      'usedTime=', time.time() - startTime)
    if not self.matchConf.start.isUserCountType():
        self.area.playerNotifier.notifyMatchStart(self.instId, self._signerMap.values())
    self.area.signIF.removeAllUsers(self.matchId, self.roomId, self.instId)
    self.area.onInstStarted(self)
    self._state = MatchInst.ST_START
    self._logger.info('MatchInst._doStart ok',
                      'state=', self._state,
                      'signerCount=', self.signerCount,
                      'usedTime=', time.time() - startTime)


MatchInst._doStartOld = MatchInst._doStart
MatchInst._doStart = _doStart
