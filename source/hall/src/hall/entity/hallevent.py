# -*- coding:utf-8 -*-
'''
Created on 2016年5月31日

@author: zhaojiangang
'''
from poker.entity.events.tyevent import UserEvent


class UserBindPhoneEvent(UserEvent):
    def __init__(self, userId, gameId):
        super(UserBindPhoneEvent, self).__init__(userId, gameId)
