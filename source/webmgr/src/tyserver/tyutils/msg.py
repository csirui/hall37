# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import json


class MsgPack:

    def __init__(self):
        self._ht = {}


    def __str__(self):
        return str(self._ht)


    def __repr__(self):
        return self.__str__()


    def pack(self):
        return json.dumps(self._ht, separators=(',', ':'))


    def unpack(self, jstr):
        self._ht = json.loads(jstr)


    def setCmd(self, cmd):
        self._ht['cmd'] = cmd


    def getCmd(self):
        if self._ht.has_key('cmd'):
            return self._ht['cmd']
        return None


    def setKey(self, key, value):
        self._ht[key] = value


    def getKey(self, key):
        if self._ht.has_key(key):
            return self._ht[key]
        return None


    def rmKey(self, key):
        if self._ht.has_key(key):
            del self._ht[key]


    def setParam(self, pkey, pvalue):
        params = self._ht.get('params', None)
        if params == None:
            params = {}
            self._ht['params'] = params
        params[pkey] = pvalue


    def getParam(self, pkey):
        params = self._ht.get('params', None)
        if params :
            return params.get(pkey. None)
        return None


    def getParamAct(self):
        return self.getParamStr('action', '')


    def getParamStr(self, pkey, dValue=''):
        value = self.getParam(pkey)
        if value == None:
            value = str(dValue)
        return value


    def getParamInt(self, pkey, dValue=0):
        try:
            value = int(self.getParam(pkey))
        except:
            value = dValue
        return value


    def getParamFloat(self, pkey, dValue=0.0):
        try:
            value = float(self.getParam(pkey))
        except:
            value = dValue
        return value


    def setResult(self, pkey, pvalue):
        result = self._ht.get('result', None)
        if result == None:
            result = {}
            self._ht['result'] = result
        result[pkey] = pvalue

    def getResult(self, pkey):
        result = self._ht.get('result', None)
        if result :
            return result.get(pkey, None)
        return None


    def rmResult(self, *pkeys):
        result = self._ht.get('result', None)
        if result :
            for pkey in pkeys :
                if result.has_key(pkey) :
                    del result[pkey]


    def setResultActCmd(self, action, cmd='table_call'):
        self.setCmd(cmd)
        self.setResult('action', cmd)


    def getResultStr(self, pkey, dValue=''):
        value = self.getResult(pkey)
        if value == None:
            value = str(dValue)
        return value
    
    
    def getResultInt(self, pkey, dValue=0):
        try:
            value = int(self.getResult(pkey))
        except:
            value = dValue
        return value


    def getResultFloat(self, pkey, dValue=0.0):
        try:
            value = float(self.getResult(pkey))
        except:
            value = dValue
        return value


    def setError(self, code, info):
        self._ht['error'] = {'code':code, 'info':info}


    def isError(self):
        if 'error' in self._ht:
            return True
        else:
            return False


    def getErrorInfo(self):
        error = self._ht.get('error', None)
        if error :
            return error.get('info', None)
        return None


    def getErrorCode(self):
        error = self._ht.get('error', None)
        if error :
            return error.get('code', None)
        return None

