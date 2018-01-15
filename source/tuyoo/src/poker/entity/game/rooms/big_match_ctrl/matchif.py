# -*- coding:utf-8 -*-
'''
Created on 2014年9月29日

@author: zjgzzz@126.com， Zhouhao
'''


class MatchIF(object):
    @classmethod
    def getMatchInfo(cls, tasklet, room, uid, mo):
        mo.setError(1, 'not a match room')

    @classmethod
    def getMatchStates(cls, tasklet, room, uid, mo):
        mo.setError(1, 'not a match room')
