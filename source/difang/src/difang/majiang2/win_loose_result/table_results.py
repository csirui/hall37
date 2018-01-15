# -*- coding=utf-8
'''
Created on 2016年9月23日

本桌的输赢结果
1）陌生人桌，打完后直接散桌，有一个round_results
2）自建桌，SNG，打几把，有几个round_results
@author: zhaol
'''
import copy

from freetime.util import log as ftlog


class MTableResults(object):
    def __init__(self):
        super(MTableResults, self).__init__()
        self.__results = []
        self.__score = None

    def reset(self):
        self.__results = []
        self.__score = None

    @property
    def score(self):
        return self.__score

    @property
    def results(self):
        return self.__results

    def addResult(self, result):
        self.__results.append(result)
        if self.__score is None:
            self.__score = copy.deepcopy(result.score)
        else:
            for index in range(len(self.__score)):
                self.__score[index] += result.score[index]

        ftlog.debug('MTableResults.addResult deltaScore:', result.score
                    , ' totalScore:', self.__score)
