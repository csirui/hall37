# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import json

import freetime.util.log as ftlog
from poker.util import keywords


def DATA_TYPE_INT(field, value, defaultVal, recovers):
    '''
    整形数字, 缺省为0
    '''
    try:
        if value != None:
            return int(value)
    except:
        if ftlog.is_debug():
            ftlog.error()
    if recovers != None:
        recovers.append(field)
        recovers.append(defaultVal)
    assert (isinstance(defaultVal, int)), 'DATA_TYPE_INT type, defaultVal must be int, field=' + str(field)
    return defaultVal


def DATA_TYPE_INT_ATOMIC(field, value, defaultVal, recovers):
    '''
    整形数字, 缺省为0, 必须使用单独方法进行原子操作
    '''
    try:
        if value != None:
            return int(value)
    except:
        if ftlog.is_debug():
            ftlog.error()
    if recovers != None:
        recovers.append(field)
        recovers.append(defaultVal)
    assert (isinstance(defaultVal, int)), 'DATA_TYPE_INT_ATOMIC type, defaultVal must be int, field=' + str(field)
    return defaultVal


def DATA_TYPE_FLOAT(field, value, defaultVal, recovers):
    '''
    浮点数字, 缺省为0.0
    '''
    try:
        if value != None:
            return float(value)
    except:
        if ftlog.is_debug():
            ftlog.error()
    if recovers != None:
        recovers.append(field)
        recovers.append(defaultVal)
    assert (isinstance(defaultVal, float)), 'DATA_TYPE_FLOAT type, defaultVal must be float, field=' + str(field)
    return defaultVal


def DATA_TYPE_FLOAT_ATOMIC(field, value, defaultVal, recovers):
    '''
    浮点数字, 缺省为0.0, 必须使用单独方法进行原子操作  
    '''
    try:
        if value != None:
            return float(value)
    except:
        if ftlog.is_debug():
            ftlog.error()
    if recovers != None:
        recovers.append(field)
        recovers.append(defaultVal)
    assert (isinstance(defaultVal, float)), 'DATA_TYPE_FLOAT_ATOMIC type, defaultVal must be float, field=' + str(field)
    return defaultVal


def DATA_TYPE_STR(field, value, defaultVal, recovers):
    '''
    字符串, 缺省为空串  
    '''
    try:
        if value != None:
            return unicode(value)
    except:
        if ftlog.is_debug():
            ftlog.error()
    if recovers != None:
        recovers.append(field)
        recovers.append(defaultVal)
    assert (
        isinstance(defaultVal, (str, unicode))), 'DATA_TYPE_STR type, defaultVal must be str or unicode, field=' + str(
        field)
    return defaultVal


def DATA_TYPE_STR_FILTER(field, value, defaultVal, recovers):
    '''
    字符串, 缺省为空串, 如果有值则进行关键字过滤
    '''
    try:
        if value != None:
            return keywords.replace(unicode(value))
    except:
        if ftlog.is_debug():
            ftlog.error()
    if recovers != None:
        recovers.append(field)
        recovers.append(defaultVal)
    assert (isinstance(defaultVal,
                       (str, unicode))), 'DATA_TYPE_STR_FILTER type, defaultVal must be str or unicode, field=' + str(
        field)
    return defaultVal


def DATA_TYPE_LIST(field, value, defaultVal, recovers):
    '''
    JSON格式的数组, 缺省为[] 
    '''
    try:
        if value != None:
            vl = json.loads(value)
            if isinstance(vl, list):
                return vl
    except:
        if ftlog.is_debug():
            ftlog.error()
    if recovers != None:
        recovers.append(field)
        recovers.append(defaultVal)
    assert (isinstance(defaultVal, list)), 'DATA_TYPE_LIST type, defaultVal must be dict, field=' + str(field)
    return defaultVal


def DATA_TYPE_DICT(field, value, defaultVal, recovers):
    '''
    JSON格式的字典, 缺省的{}
    '''
    try:
        if value != None:
            vl = json.loads(value)
            if isinstance(vl, dict):
                return vl
    except:
        if ftlog.is_debug():
            ftlog.error()
    if recovers != None:
        recovers.append(field)
        recovers.append(defaultVal)
    assert (isinstance(defaultVal, dict)), 'DATA_TYPE_DICT type, defaultVal must be dict, field=' + str(field)
    return defaultVal


def DATA_TYPE_BOOLEAN(field, value, defaultVal, recovers):
    '''
    真假值, 缺省为假 False  
    '''
    if value == 1 or value == 'true' or value == 'True':
        return 1
    if recovers != None:
        if value == 0 or value == 'false' or value == 'False':
            return 0
        else:
            recovers.append(field)
            recovers.append(defaultVal)
    assert (defaultVal == 0 or defaultVal == 1), 'DATA_TYPE_BOOLEAN type, defaultVal must be 0 or 1, field=' + str(
        field)
    return defaultVal


def redisDataSchema(cls):
    _VCODE = '''
        if field == '%s' :
            return %s(field, value, %s, recovers)
'''
    _VFIELD = '''
    %s = '%s'
'''
    _VGROUP = '''
    %s = ("%s",)
'''
    _VCLASS = '''
class %s(DataSchema):
    
    def __init__(self, *argl, **argd):
        raise Exception('Scheame Class, can not instance !!')

    @staticmethod
    def checkData(field, value, recovers=None):
        %s
        return value;

    @staticmethod
    def mkey(%s) :
        return '%s' %s (%s)

    %s

    REDIS_KEY = '%s'

    FIELDS_ALL = (%s)

    READ_ONLY_FIELDS = set([%s])

    FIELDS_ALL_SET = set(FIELDS_ALL)

    WRITES_FIELDS = FIELDS_ALL_SET - READ_ONLY_FIELDS

'''
    fieldsall = []
    vcode = ''
    fields = ''
    mkey = ''
    readonlys = []
    for att in dir(cls):
        v = getattr(cls, att)
        if att == 'REDIS_KEY':
            assert (isinstance(v, (str, unicode))), 'the redis key must be str, unicode !' + str(cls) + ' att=' + str(
                att) + ' val=' + str(v) + ' ' + type(v)
            mkey = v
        if att.find('FIELD_GROUP_') < 0 and isinstance(v, tuple) and len(v) == 3:
            field, fundtype, defaultVal = v
            assert (isinstance(field, (str, unicode))), 'the filed type must be str, unicode' + str(
                cls) + ' field=' + str(field) + ' ' + type(field)
            assert (defaultVal != None), 'the default value can not be None !' + str(cls) + ' field=' + str(field)
            assert (field not in fieldsall), 'the field already defined !' + str(cls) + ' field=' + str(field)
            fieldsall.append(field)
            if isinstance(defaultVal, (int, float)):
                defaultVal = str(defaultVal)
            elif isinstance(defaultVal, (str, unicode)):
                defaultVal = '"' + defaultVal + '"'
            elif isinstance(defaultVal, (list, dict)):
                defaultVal = json.dumps(defaultVal)
            else:
                raise Exception(
                    'the default value is error !' + str(cls) + ' field=' + str(field) + ' defaultVal=' + str(
                        defaultVal) + ' ' + type(defaultVal))
            fields += _VFIELD % (att, field)
            vcode += _VCODE % (field, fundtype.__name__, defaultVal)
            if fundtype.__name__.endswith('_ATOMIC'):
                readonlys.append(field)
        elif att.find('FIELD_GROUP_') == 0 and isinstance(v, (list, tuple)):
            gcode = []
            for x in v:
                gcode.append(x[0])
            gcode = '","'.join(gcode)
            fields += _VGROUP % (att, gcode)

    kas = []
    for x in xrange(len(mkey)):
        if mkey[x] == '%':
            kas.append('d%d' % (x))
    kas = ','.join(kas)

    readonlys.sort()
    fieldsall.sort()
    readonlys = '"' + '","'.join(readonlys) + '"'
    fieldsall = '"' + '","'.join(fieldsall) + '"'
    vclass = _VCLASS % (cls.__name__, vcode, kas, mkey, '%', kas, fields, mkey, fieldsall, readonlys)

    #     print vclass

    mylocals = {}
    co = compile(vclass, cls.__module__ + '.' + cls.__name__, 'exec')
    exec co in globals(), mylocals
    vclass = mylocals[mylocals.keys()[0]]
    return vclass


class DataSchema():
    FIELDS_ALL = ()  # 字段集合, 由redisDataSchema修饰符自动赋值
    FIELDS_ALL_SET = set()
    WRITES_FIELDS = set()
    READ_ONLY_FIELDS = ()  # 只读字段集合, 由redisDataSchema修饰符自动赋值, 即 检测方法名称以_ATOMIC为结尾的字段集合

    @staticmethod
    def checkData(field, value, recovers=None):
        '''
        检测对应的字段的数据格式, 此方法由redisDataSchema修饰符自动生成
        '''

    @staticmethod
    def mkey(*argl):
        '''
        返回数据中的主键的值, 此方法由redisDataSchema修饰符自动生成
        '''

    @classmethod
    def checkDataList(cls, fields, values, recovers=None):
        for x in xrange(len(fields)):
            values[x] = cls.checkData(fields[x], values[x], recovers)
        return values

    @classmethod
    def checkDataDict(cls, fields, values, recovers=None):
        datas = {}
        for x in xrange(len(fields)):
            f = fields[x]
            datas[f] = cls.checkData(f, values[x], recovers)
        return datas

    @classmethod
    def paramsDict2List(cls, datas, check=1):
        gdkv = []
        for k, v in datas.items():
            if check:
                assert (k in cls.WRITES_FIELDS), 'the key [' + str(k) + '] not in WRITES_FIELDS ' + str(
                    cls.WRITES_FIELDS)
            if isinstance(v, (list, dict)):
                v = json.dumps(v, separators=(',', ':'))
            else:
                assert (
                    isinstance(v, (
                    int, float, str, unicode))), 'the value type must be int, float, str, unicode, k=' + str(
                    k) + ' v=' + type(v)
            gdkv.append(k)
            gdkv.append(v)
        return gdkv

    @classmethod
    def paramsDict2Dict(cls, datas, check=1):
        gdkv = {}
        for k, v in datas.items():
            if check:
                assert (k in cls.WRITES_FIELDS), 'the key [' + str(k) + '] not in WRITES_FIELDS ' + str(
                    cls.WRITES_FIELDS)
            if isinstance(v, (list, dict)):
                v = json.dumps(v, separators=(',', ':'))
            else:
                assert (
                    isinstance(v, (
                    int, float, str, unicode))), 'the value type must be int, float, str, unicode, k=' + str(
                    k) + ' v=' + type(v)
            gdkv[k] = v
        return gdkv

    @classmethod
    def assertParamDictFields(cls, dataDict):
        for k, v in dataDict.items():
            assert (k in cls.WRITES_FIELDS), 'the key [' + str(k) + '] not in WRITES_FIELDS' + str(cls.WRITES_FIELDS)
            assert (isinstance(v, (int, float, str, unicode, list,
                                   dict))), 'the value type must be int, float, str, unicode, list, dict k=' + str(
                k) + ' v=' + type(v)

    @classmethod
    def assertParamListFields(cls, dataList):
        for x in xrange(len(dataList) / 2):
            assert (dataList[x << 1] in cls.WRITES_FIELDS), 'the key [' + str(
                dataList[x << 1]) + '] not in WRITES_FIELDS' + str(cls.WRITES_FIELDS)
