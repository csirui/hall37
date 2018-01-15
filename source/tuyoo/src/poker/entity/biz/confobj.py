# -*- coding=utf-8
'''
Created on 2015年6月3日

@author: zhaojiangang
'''
import freetime.util.log as ftlog
from poker.entity.biz.exceptions import TYBizConfException
from poker.util.reflection import TYClassRegister


class TYConfable(object):
    TYPE_ID = 'unknown'

    def __init__(self):
        pass

    def decodeFromDict(self, d):
        raise NotImplementedError


class TYConfableRegister(TYClassRegister):
    @classmethod
    def decodeFromDict(cls, d):
        typeId = d.get('typeId')
        # ftlog.debug('typeId:', typeId, ' d:', d)

        clz = cls.findClass(typeId)
        if not clz:
            raise TYBizConfException(d, '%s unknown typeId %s' % (cls, typeId))

        try:
            confable = clz()
            confable.decodeFromDict(d)
        except Exception, e:
            ftlog.error(clz, d)
            raise e
        return confable

    @classmethod
    def decodeList(cls, dictList):
        ret = []
        for d in dictList:
            ret.append(cls.decodeFromDict(d))
        return ret
