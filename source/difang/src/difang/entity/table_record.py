# -*- coding: utf-8 -*-
import copy
import functools
import json
import random
import time
import zlib

import difang.entity.conf as difangConf
from difang.entity import uploader
from freetime.core.timer import FTTimer
from freetime.util import log as ftlog

ALLUSERS = 0
UPLOAD_INTERVAL = 2


class DiFangTableRecord(object):
    '''牌局记录'''

    def __init__(self, table):
        super(DiFangTableRecord, self).__init__()
        self.table = table
        self.clear()

    def clear(self):
        self.resMsgs = []

    def addResMsg(self, mo, userId=ALLUSERS):
        res = self.processMsg(mo)
        if not res:
            return
        self.resMsgs.append((res, userId))
        if ftlog.is_debug():
            ftlog.debug("sizeof res", len(json.dumps(res)), caller=self)
            ftlog.debug("sizeof resMsgs", len(json.dumps(self.resMsgs)), caller=self)
            ftlog.debug("sizeof zlib resMsgs", len(zlib.compress(json.dumps(self.resMsgs))), caller=self)

    def processMsg(self, mo):
        copyHt = copy.deepcopy(mo._ht)
        result = copyHt.get("result")
        # 减少消息重复内容
        if "roomId" in result:
            del result["roomId"]
        if "gameId" in result:
            del result["gameId"]
        if "tableId" in result:
            del result["tableId"]

        # if mo.getResult("action") in ["ready", "chat"] or mo.getCmd() in ["table_chat"]:
        #     return None
        return copyHt

    def compress(self):
        # return "gzib" + zlib.compress(json.dumps(self.resMsgs))
        return json.dumps(self.resMsgs)

    def decompress(self, str_data):
        # return json.loads(zlib.decompress(str_data))
        return json.loads(str_data)

    def getKey(self):
        """获取recordKey
        """
        # return "record" + "_" + str(self.table.gameId) + "_" + str(self.table.ftId) + "_" + str(self.table.createTime)
        return "record" + "_" + str(self.table.gameId) + "_" + str(self.table.ftId) + "_" + str(int(time.time()))

    def getTimeStampFromKey(self, key):
        return key.split("_")[-1]

    def saveRecord(self):
        """保存当前局的纪录
        """
        if not self.resMsgs:
            return
        data = self.compress()
        fname = self.getKey() + "_" + str(self.table.gamePlay.gameSeq)
        func = functools.partial(self.uploadTableRecord, fname, data, 1)
        FTTimer(UPLOAD_INTERVAL, func)
        self.clear()

    def uploadTableRecord(self, fname, fdata, times):
        '''
        如果上传失败，每隔2*n的时间重试一次，重试4次
        '''
        uploadUrls, token, path = difangConf.getTableRecordUploadConf(self.table.gameId)
        # path = difangConf.getPublicConf(self.table.gameId, 'cloudUploadPath')
        if not uploadUrls or not token or not path:
            ftlog.error("DiFangTableRecord.uploadTableRecord conf error! |uploadUrl=", uploadUrls,
                        "token=", token,
                        "path=", path)
            return -1, ""
        uploadUrl = random.choice(uploadUrls)

        ret, message = uploader.uploadVideo(uploadUrl, token, path + fname, fdata)
        ftlog.info("DiFangTableRecord.uploadTableRecord ret=", ret,
                   "message=", message,
                   "fname=", fname,
                   "times=", times)
        # 失败重试
        if ret != 0 and times <= 16:
            times = times * 2
            func = functools.partial(self.upload, fname, fdata, times)
            FTTimer(UPLOAD_INTERVAL, func)
