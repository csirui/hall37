# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.3.28

import json


class MsgPack:
    def __init__(self):
        self._ht = {}

    def __str__(self):
        return str(self._ht)

    def __repr__(self):
        return self.__str__()

    def clone(self):
        m = MsgPack()
        m.unpack(self.pack())
        return m

    def setCmd(self, cmd):
        self._ht['cmd'] = cmd

    def setAction(self, action):
        self.setParam('action', action)

    def getAction(self):
        return self.getParam('action')

    def setCmdAction(self, cmd, action):
        self.setCmd(cmd)
        self.setAction(action)

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

    def pack(self):
        return json.dumps(self._ht, separators=(',', ':'))

    def unpack(self, jstr):
        self._ht = json.loads(jstr)

    def setError(self, code, info):
        self._ht['error'] = {'code': code, 'info': info}

    def getParam(self, pkey, defValue=None):
        if self._ht.has_key('params'):
            reqht = self._ht['params']
            if reqht.has_key(pkey):
                return reqht[pkey]
        return defValue

    def setParam(self, pkey, pvalue):
        if not self._ht.has_key('params'):
            self._ht['params'] = {}
        reqht = self._ht['params']
        reqht[pkey] = pvalue

    def updateParam(self, moreParam):
        if not self._ht.has_key('params'):
            self._ht['params'] = {}
        reqht = self._ht['params']
        reqht.update(moreParam)

    def setResult(self, pkey, pvalue):
        if not self._ht.has_key('result'):
            self._ht['result'] = {}
        reqht = self._ht['result']
        reqht[pkey] = pvalue

    def updateResult(self, moreResult):
        if not self._ht.has_key('result'):
            self._ht['result'] = {}
        reqht = self._ht['result']
        reqht.update(moreResult)

    def getResult(self, pkey, defValue=None):
        if self._ht.has_key('result'):
            reqht = self._ht['result']
            if reqht.has_key(pkey):
                return reqht[pkey]
        return defValue

    def isError(self):
        return self._ht.has_key('error')

    def getErrorCode(self, defValue=None):
        err = self._ht.get('error')
        if err:
            return err.get('code')
        return defValue

    def getErrorInfo(self, defValue=None):
        err = self._ht.get('error')
        if err:
            return err.get('info')
        return defValue

    def getParams(self, *keys):
        return map(self._ht.get('params', {}).get, keys)

    def getResults(self, *keys):
        return map(self._ht.get('result', {}).get, keys)
