# -*- coding=utf-8
'''
Created on 2016年2月17日

@author: hanjiajun
'''

import os
import time

import freetime.util.log as ftlog
from hall.entity import hallconf
from hall.servers.common.base_http_checker import BaseHttpMsgChecker
from poker.protocol import runhttp
from poker.protocol.decorator import markHttpHandler, markHttpMethod
from poker.util.replayutils import decodeOps, hexToBin


@markHttpHandler
class ReplayHttpHandler(BaseHttpMsgChecker):
    def __init__(self):
        pass

    def isEnable(self):
        return True

    def makeErrorResponse(self, ec, message):
        return {'error': {'ec': ec, 'message': message}}

    def makeResponse(self, result):
        return {'result': result}

    def _check_param_roundId(self, key, params):
        roundId = runhttp.getParamStr(key, "")
        return None, roundId

    def _check_param_recordData(self, key, params):
        recordData = runhttp.getParamStr(key, "")
        return None, recordData

    def _check_param_timeStmp(self, key, params):
        time = runhttp.getParamStr(key, "")
        return None, time

    def _makeStoragePath(self, roundId, timeStmp):

        conf = hallconf.getReplayConf()
        basePath = conf.get("rep_storage_path", "/home/tyhall/hall37/run/replay/")  # 加个默认的,避免出问题
        timePath = time.strftime("%Y/%m/%d%H/%M/%S/", time.localtime(int(timeStmp)))
        fullDir = os.path.join(basePath, timePath)
        fullPath = os.path.join(fullDir, roundId + ".txt")
        if not os.path.exists(fullDir):
            os.makedirs(fullDir)
        return fullPath

    @markHttpMethod(httppath='/replay/record')
    def doReplayRecord(self, roundId, timeStmp, recordData):
        ftlog.info('TestHttpHandler.doReplayRecord roundId=', roundId)
        ftlog.info('TestHttpHandler.doReplayRecord timeStmp=', timeStmp)
        ftlog.info('TestHttpHandler.doReplayRecord recordData=', recordData)

        # TDOO 写本地
        path = self._makeStoragePath(roundId, timeStmp)
        record = open(path, 'w')
        record.write(hexToBin(recordData))
        record.close()

        return self.makeResponse({})

    @markHttpMethod(httppath='/replay/pick')
    def doReplayPick(self, roundId, timeStmp):
        ftlog.info('TestHttpHandler.doReplayRecord roundId=', roundId)
        ftlog.info('TestHttpHandler.doReplayRecord timeStmp=', timeStmp)

        # TDOO 写本地
        path = self._makeStoragePath(roundId, timeStmp)
        ftlog.info('path=', path)
        jsonData = ""
        if os.path.exists(path):
            record = open(path, 'r')
            fileData = record.read()
            jsonData = decodeOps(fileData)
            record.close()

        return self.makeResponse({'data': jsonData})

    @markHttpMethod(httppath='/replay/test')
    def doReplayTest(self):

        # TDOO 写本地
        path = "/home/tyhall/hall37/run/record+0.txt"
        ftlog.info('path=', path)
        jsonData = ""
        if os.path.exists(path):
            ftlog.info('exists ')
            record = open(path, 'r')
            fileData = record.read()
            ftlog.info('file=', fileData)
            ftlog.info('ops=', decodeOps(fileData))
            jsonData = decodeOps(fileData)
            record.close()

        return self.makeResponse({'data': jsonData})
