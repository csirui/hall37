# -*- coding=utf-8 -*-
'''
Created on 2016年3月5日

@author: liaoxx
'''

import copy
import json
import struct

from freetime.entity.msg import MsgPack
from freetime.util import log as ftlog


class CmdObjBase(object):
    def __init__(self):
        self._formatStr = ""
        self._fieldsName = []

    def structMsg(self, msgPack):
        fieldsValue = msgPack.getResults(*(self._fieldsName))
        return struct.pack(self._formatStr, *fieldsValue)

    def _unstructMsg(self, binStr):
        fieldsValue = struct.unpack(self._formatStr, binStr)
        return dict(zip(self._fieldsName, fieldsValue))

    def _constructJson(self, msgMap):
        return ""

    def unstructMsg(self, binStr):
        msgMap = self._unstructMsg(binStr)
        ftlog.debug("unstructMsg msgMap:", msgMap)
        return self._constructJson(msgMap)


class FireVerify(CmdObjBase):
    def __init__(self):
        super(FireVerify, self).__init__()
        self._formatStr = "!QQBHffB"
        self._fieldsName = ["userId", "tableId", "seatId", "wpId", "fPosx", "fPosy", "fFlg"]

    def _constructJson(self, msgMap):
        msgJson = {}
        msgJson["cmd"] = "fish_table_call"
        msgJson["params"] = msgMap
        msgMap["gameId"] = 43
        from poker.protocol.conn import protocols
        tcpuser = protocols._ONLINE_USERS.get(msgMap.get("userId", -1))
        if tcpuser:
            msgMap["clientId"] = tcpuser.clientId
        else:
            msgMap["clientId"] = ""
        msgMap["roomId"] = msgMap.get("tableId") / 10000
        msgMap["action"] = "fire"
        return json.dumps(msgJson)


class FireVerifyRet(CmdObjBase):
    def __init__(self):
        super(FireVerifyRet, self).__init__()
        self._formatStr = "!BHBQ"
        self._fieldsName = ["fFlg", "wpId", "reason", "chip"]

    def _constructJson(self, msgMap):
        msgJson = {}
        msgJson["cmd"] = "fire"
        msgJson["result"] = msgMap
        return json.dumps(msgJson)


class FireBroadcast(CmdObjBase):
    def __init__(self):
        super(FireBroadcast, self).__init__()
        self._formatStr = "!BBHffQ"
        self._fieldsName = ["seatId", "fFlg", "wpId", "fPosx", "fPosy", "chip"]

    def _constructJson(self, msgMap):
        msgJson = {}
        msgJson["cmd"] = "fire"
        msgJson["result"] = msgMap
        return json.dumps(msgJson)


class CatchVerify(CmdObjBase):
    def __init__(self):
        super(CatchVerify, self).__init__()
        self._formatStr = "!QQBBHH"
        self._fieldsName = ["userId", "tableId", "seatId", "fFlg", "wpId", "fId"]

    def _constructJson(self, msgMap):
        msgJson = {}
        msgJson["cmd"] = "table_call"
        msgJson["params"] = msgMap
        msgMap["gameId"] = 43
        from poker.protocol.conn import protocols
        tcpuser = protocols._ONLINE_USERS.get(msgMap.get("userId", -1))
        if tcpuser:
            msgMap["clientId"] = tcpuser.clientId
        else:
            msgMap["clientId"] = ""
        msgMap["roomId"] = msgMap.get("tableId") / 10000
        msgMap["action"] = "catch"
        return json.dumps(msgJson)


class CatchVerifyRetOk(CmdObjBase):
    def __init__(self):
        super(CatchVerifyRetOk, self).__init__()
        self._formatStr = "!BBHB"  # HL
        self._fieldsName = ["seatId", "fFlg", "fId"]

    def structMsg(self, msgPack):
        gain = msgPack.getResult("gain")
        itemNum = len(gain)
        formatStr = copy.copy(self._formatStr)
        fieldsValue = msgPack.getResults(*(self._fieldsName))
        fieldsValue = list(fieldsValue)
        fieldsValue.append(itemNum)
        for i in xrange(itemNum):
            formatStr += "HL"
            fieldsValue.extend([gain[i]["name"], gain[i]["count"]])
        return struct.pack(formatStr, *fieldsValue)

    #     def _unstructMsg(self, binStr):
    #         subBinStr = binStr[0:5]
    #         _, _, _, itemNum = struct.unpack(self._formatStr, subBinStr)
    #         formatStr = copy.copy(self._formatStr)
    #         for i in xrange(itemNum):
    #             formatStr += "HL"
    #
    #         fieldsValue = struct.unpack(formatStr, binStr)
    #         return dict(zip(self._fieldsName, fieldsValue))


    def _constructJson(self, msgMap):
        msgJson = {}
        msgJson["cmd"] = "catch"
        msgJson["result"] = msgMap
        return json.dumps(msgJson)


class CatchVerifyRetFail(CmdObjBase):
    def __init__(self):
        super(CatchVerifyRetFail, self).__init__()
        self._formatStr = "!BHB"
        self._fieldsName = ["fFlg", "fId", "reason"]

    def _constructJson(self, msgMap):
        msgJson = {}
        msgJson["cmd"] = "catch"
        msgJson["result"] = msgMap
        return json.dumps(msgJson)


FireVerifyObj = FireVerify()
FireVerifyRetObj = FireVerifyRet()
FireBroadcastObj = FireBroadcast()
CatchVerifyObj = CatchVerify()
CatchVerifyRetOkObj = CatchVerifyRetOk()
CatchVerifyRetFailObj = CatchVerifyRetFail()


def _getCmdObj(cmdId):
    Obj = None
    if cmdId == 1:
        Obj = FireVerifyObj
    elif cmdId == 2:
        Obj = FireVerifyRetObj
    elif cmdId == 3:
        Obj = FireBroadcastObj
    elif cmdId == 4:
        Obj = CatchVerifyObj
    elif cmdId == 5:
        Obj = CatchVerifyRetOkObj
    elif cmdId == 6:
        Obj = CatchVerifyRetFailObj

    return Obj


# {} json str  -> cmdId:......
def encode(msgstr):
    if not msgstr:
        return msgstr
    if msgstr[0] != "{":
        return msgstr
    if msgstr.find('"cmdId"') < 0:
        return msgstr
    msgPack = MsgPack()
    msgPack.unpack(msgstr)
    cmdId = msgPack.getKey("cmdId")
    if not cmdId:
        return msgstr
    cmdObj = _getCmdObj(cmdId)
    if not cmdObj:
        return msgstr
    binStr = cmdObj.structMsg(msgPack)
    return struct.pack("!3sB", "$fs", cmdId) + binStr


# cmdId......\r\n json str
def decode(msgstr):
    if len(msgstr) < 4:
        return msgstr

    if msgstr[0] == "{":
        return msgstr

    prefix, cmdId = struct.unpack("!3sB", msgstr[0:4])
    if prefix != "$fs":
        return msgstr

    cmdObj = _getCmdObj(cmdId)
    if not cmdObj:
        return msgstr

    msg = msgstr[4:]  # 去掉 \r\n
    return cmdObj.unstructMsg(msg)
