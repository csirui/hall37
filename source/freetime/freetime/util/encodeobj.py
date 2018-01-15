# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.4.3

def decodeObjUtf8(datas):
    '''
    遍历datas(list,dict), 将遇到的所有的字符串进行encode utf-8处理
    '''
    if isinstance(datas, dict):
        ndatas = {}
        for key, val in datas.items():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            ndatas[key] = decodeObjUtf8(val)
        return ndatas
    if isinstance(datas, list):
        ndatas = []
        for val in datas:
            ndatas.append(decodeObjUtf8(val))
        return ndatas
    if isinstance(datas, unicode):
        return datas.encode('utf-8')
    return datas
