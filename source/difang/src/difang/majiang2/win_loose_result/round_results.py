# -*- coding=utf-8
'''
Created on 2016年9月23日

本副牌局的和牌结果，可能有多个
1）普通麻将一个结果
2）血战到底N-1个结果，N为牌桌人数
3）血流成河有多个结果，直到本局牌全部发完
@author: zhaol
'''
import copy

from difang.majiang2.win_loose_result.one_result import MOneResult
from freetime.util import log as ftlog


class MRoundResults(object):
    def __init__(self):
        super(MRoundResults, self).__init__()
        self.__round_index = 0
        self.__round_results = []
        self.__fan_patterns = []
        self.__score = None
        self.__delta = None

    @property
    def delta(self):
        return self.__delta

    @property
    def score(self):
        return self.__score

    @property
    def fanPatterns(self):
        return self.__fan_patterns

    @property
    def roundIndex(self):
        return self.__round_index

    def setRoundIndex(self, index):
        self.__round_index = index

    @property
    def roundResults(self):
        return self.__round_results

    def addRoundResult(self, result):
        """添加轮次结果"""
        ftlog.debug('MRoundResults.addRoundResult : ', result.results
                    , ' now roundIndex:', self.__round_index)

        self.__round_results.append(result)
        self.__delta = result.results[MOneResult.KEY_SCORE]
        if result.results.has_key(MOneResult.KEY_FAN_PATTERN):
            if self.__fan_patterns == []:
                # 根据返回值的玩家人数，初始化
                self.__fan_patterns = [[] for _ in range(len(result.results[MOneResult.KEY_FAN_PATTERN]))]
            for index in range(len(result.results[MOneResult.KEY_FAN_PATTERN])):
                self.__fan_patterns[index].extend(result.results[MOneResult.KEY_FAN_PATTERN][index])
        if not self.__score:
            self.__score = copy.deepcopy(self.__delta)
        else:
            for index in range(len(self.__delta)):
                self.__score[index] += self.__delta[index]

        ftlog.debug('MRoundResults.addRoundResult type:', result.results[MOneResult.KEY_TYPE]
                    , ' name:', result.results[MOneResult.KEY_NAME]
                    , ' totalScore:', self.__score
                    , ' deltaScore:', self.__delta
                    , ' fanPatterns:', self.__fan_patterns)
