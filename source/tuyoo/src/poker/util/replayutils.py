# -*- coding:utf-8 -*-
'''
Created on 2016年2月18日

@author: hanjiajun
'''

import struct

import freetime.util.log as ftlog

OPTYPE_RECODE_INFO = 0  # 0 记录的信息 游戏id:int,记录版本号(如果以后记录协议变更,就增加这个):int.
OPTYPE_GAME_READY = 1  # 1 系统发牌 len[74] 不与一局牌相关的信息 玩家 userid:3int 基数: 1int ,费用: 1int  一局牌开始的初始信息 内容为54个 byte 前17*3个分别是123玩家的手牌,最后3个是底牌
OPTYPE_GAME_START = 2  # 2 系统定地主 len[1] 1byte 定地主 值域 0|1|2
OPTYPE_GAME_WIN = 3  # 3 系统结算 len[29]  3个结束筹码或积分:6int 4种翻倍:4byte, 胜利玩家: 1byte
OPTYPE_CALL = 4  # 4 叫地主/抢地主 len[1] 1byte 倍数
OPTYPE_PASS = 5  # 5 过牌/不叫地主 len[0]
OPTYPE_CARD = 6  # 6 出牌 len[1~20] 牌 id 列表,最长: AAKKQQJJ10109988776655


# #读一遍log文件,挨个编码再解析
# def parseLogFile(filePath):
#     f = open(filePath, "r")
#     count = 2
#     while True:
#         line = f.readline()
#         count = count - 1
#         if line and count > 0:
#             report = line.split(' ')[-2].replace("\\\\","\\") # 倒数第二段替换\\为\后是正确的 json 数据
#             jsonInfo = json.loads(report)
#             jsonString = jsonInfo[-2] #最后一段是牌局流程的json 数据字符串
#             gameJson = json.loads(jsonString)
# 
#             #先编码
#             print "-------encode--------"
#             data = encodeOps(gameJson['ops'])
#             print "final length:" + str(len(data))
#             #再解析
#             print "-------decode--------"
#             decodeStr = decodeOps(data)
#             print "final decode:" , json.dumps(decodeStr, ensure_ascii = False,sort_keys=False,indent=4).replace('¨','{').replace('¼','}').replace('ÿ','[').replace('¦',']')
#         else:
#             break
#     f.close()



def encodeOps(ops):
    strs = []
    data = encodeRecodeInfo(strs)

    encoderMap = {}
    encoderMap['game_ready'] = encodeGameReady
    encoderMap['game_start'] = encodeGameStart
    encoderMap['game_win'] = encodeGameWin
    encoderMap['call'] = encodeCall
    encoderMap['card'] = encodeCard
    encoderMap['next'] = encodeNext

    # 遍历 ops,挨个编码
    for index in range(len(ops)):
        op = ops[index]
        action = op['action']
        if encoderMap.has_key(action):
            encoderMap[action](op, strs)
        else:
            print '发现了不认识的 action:', action

    return ''.join(strs)


# 记录基本信息
def encodeRecodeInfo(strs):
    # print "encodeRecodeInfo"
    strs.append(struct.pack('B', OPTYPE_RECODE_INFO))
    strs.append(struct.pack('II', 6, 0))  # 游戏 id:6,编码版本:0
    pass


# 发牌+牌局基本信息
def encodeGameReady(op, strs):
    # print "encodeGameReady:" , op
    strs.append(struct.pack('B', OPTYPE_GAME_READY))
    strs.append(struct.pack('I', op['seats'][0]['userId']))
    strs.append(struct.pack('I', op['seats'][1]['userId']))
    strs.append(struct.pack('I', op['seats'][2]['userId']))
    strs.append(struct.pack('I', op['baseMulti']))
    strs.append(struct.pack('I', op['roomFee']))
    # 记录手牌
    for seatIndex in range(len(op['seats'])):
        seat = op['seats'][seatIndex]
        for cardIndex in range(len(seat['cards'])):
            card = seat['cards'][cardIndex]
            strs.append(struct.pack('B', card))
    # 记录底牌
    for cardIndex in range(len(op['baseCards'])):
        card = op['baseCards'][cardIndex]
        strs.append(struct.pack('B', card))
    pass


# 开打
def encodeGameStart(op, strs):
    # print "encodeGameStart:" , op
    strs.append(struct.pack('B', OPTYPE_GAME_START))
    strs.append(struct.pack('B', op['dizhuseatIndex']))
    pass


# 结算
def encodeGameWin(op, strs):
    # print "encodeGameWin:" , op
    strs.append(struct.pack('B', OPTYPE_GAME_WIN))
    for index in range(len(op['winlose']['winloses'])):
        strs.append(struct.pack('i', op['winlose']['winloses'][index]['deltaChip']))
        strs.append(struct.pack('i', op['winlose']['winloses'][index]['finalChip']))
    strs.append(struct.pack('B', op['winlose']['zhadanMulti']))
    strs.append(struct.pack('B', op['winlose']['chuntianMulti']))
    strs.append(struct.pack('B', op['winlose']['mingpaiMulti']))
    strs.append(struct.pack('B', op['winlose']['baseCardMulti']))
    pass


# 叫地主
def encodeCall(op, strs):
    # print "encodeCall:" , op
    if op['call'] == 0:
        strs.append(struct.pack('B', OPTYPE_PASS))
    else:
        strs.append(struct.pack('B', OPTYPE_CALL))

    strs.append(struct.pack('B', op['seatIndex']))

    if op['call'] != 0:
        strs.append(struct.pack('B', op['call']))
    pass


# 出牌
def encodeCard(op, strs):
    # print "encodeCard:" , op
    outCards = op['outCards']
    if len(outCards) == 0:
        strs.append(struct.pack('B', OPTYPE_PASS))
    else:
        strs.append(struct.pack('B', OPTYPE_CARD))

    strs.append(struct.pack('B', op['seatIndex']))
    if len(outCards) != 0:
        strs.append(struct.pack('B', len(outCards)))
        for index in range(len(outCards)):
            strs.append(struct.pack('B', outCards[index]))

    pass


# 该谁出牌了
def encodeNext(op, strs):
    # print "encodeNext:" , op
    # next就不编码了,等需要做复盘时再编码
    pass


# 解码操作列表
def decodeOps(strData):
    # print "decodeOps:" , strData
    pointer = 0  # 读取数据的偏移指针
    ops = []  # 保存解析后数据的数组
    strLen = len(strData)  # 编码数据长度

    decoderMap = {}
    decoderMap[OPTYPE_RECODE_INFO] = decodeRecodeInfo
    decoderMap[OPTYPE_GAME_READY] = decodeGameReady
    decoderMap[OPTYPE_GAME_START] = decodeGameStart
    decoderMap[OPTYPE_GAME_WIN] = decodeGameWin
    decoderMap[OPTYPE_CALL] = decodeCall
    decoderMap[OPTYPE_CARD] = decodeCard
    decoderMap[OPTYPE_PASS] = decodePass

    while pointer < strLen:
        ftlog.info("pointer:", pointer, " strLen:", strLen)
        opType = struct.unpack_from('B', strData, pointer)[0]
        ftlog.info("opType", opType)
        if decoderMap.has_key(opType):
            operation, nextPointer = decoderMap[opType](strData, pointer + 1)
            ops.append(operation)
            ftlog.info("operation:", operation)
            pointer = nextPointer
            # print "nextPointer:" , nextPointer , " pointer:" , pointer
        else:
            print '发现了不认识的 opType:', str(opType)
            break

    ftlog.info("ops len:", len(ops))
    return ops


# 解码基本信息
def decodeRecodeInfo(strData, pointer):
    operation = {}
    nextPointer = pointer
    operation["action"] = "record_info"

    operation['gameId'] = struct.unpack_from('I', strData, nextPointer)[0]
    nextPointer += 4
    operation['version'] = struct.unpack_from('I', strData, nextPointer)[0]
    nextPointer += 4

    return operation, nextPointer


# 游戏初始信息
def decodeGameReady(strData, pointer):
    operation = {}
    nextPointer = pointer
    operation["action"] = "game_ready"

    operation['userIds'] = []
    operation['userIds'].append(struct.unpack_from('I', strData, nextPointer)[0])
    nextPointer += 4
    operation['userIds'].append(struct.unpack_from('I', strData, nextPointer)[0])
    nextPointer += 4
    operation['userIds'].append(struct.unpack_from('I', strData, nextPointer)[0])
    nextPointer += 4

    operation['baseMulti'] = struct.unpack_from('I', strData, nextPointer)[0]
    nextPointer += 4
    operation['roomFee'] = struct.unpack_from('I', strData, nextPointer)[0]
    nextPointer += 4

    operation['cards'] = []
    for userIndex in range(3):
        operation['cards'].append([])
        for cardIbdex in range(17):
            operation['cards'][userIndex].append(struct.unpack_from('B', strData, nextPointer)[0])
            nextPointer += 1

    operation['baseCards'] = []
    for cardIndex in range(3):
        operation['baseCards'].append(struct.unpack_from('B', strData, nextPointer)[0])
        nextPointer += 1

    return operation, nextPointer


# 解码牌局开始
def decodeGameStart(strData, pointer):
    operation = {}
    nextPointer = pointer
    operation["action"] = "game_start"
    operation['dizhuseatIndex'] = struct.unpack_from('B', strData, nextPointer)[0]
    nextPointer += 1

    return operation, nextPointer


# 解码牌局结束
def decodeGameWin(strData, pointer):
    operation = {}
    nextPointer = pointer
    operation["action"] = "game_win"

    operation['winloses'] = []

    for userIndex in range(3):
        operation['winloses'].append({})
        operation['winloses'][userIndex]["deltaChip"] = struct.unpack_from('i', strData, nextPointer)[0]
        nextPointer += 4
        operation['winloses'][userIndex]["finalChip"] = struct.unpack_from('i', strData, nextPointer)[0]
        nextPointer += 4
    operation["zhadanMulti"] = struct.unpack_from('B', strData, nextPointer)[0]
    nextPointer += 1
    operation["chuntianMulti"] = struct.unpack_from('B', strData, nextPointer)[0]
    nextPointer += 1
    operation["mingpaiMulti"] = struct.unpack_from('B', strData, nextPointer)[0]
    nextPointer += 1
    operation["baseCardMulti"] = struct.unpack_from('B', strData, nextPointer)[0]
    nextPointer += 1

    return operation, nextPointer


# 解码基本信息
def decodeCall(strData, pointer):
    operation = {}
    nextPointer = pointer
    operation["action"] = "call"
    operation["seatIndex"] = struct.unpack_from('B', strData, nextPointer)[0]
    nextPointer += 1
    operation["call"] = struct.unpack_from('B', strData, nextPointer)[0]
    nextPointer += 1

    return operation, nextPointer


# 解码基本信息
def decodeCard(strData, pointer):
    operation = {}
    nextPointer = pointer
    operation["action"] = "card"
    operation["seatIndex"] = struct.unpack_from('B', strData, nextPointer)[0]
    nextPointer += 1
    cardCount = struct.unpack_from('B', strData, nextPointer)[0]
    nextPointer += 1
    operation["outCards"] = []
    for userIndex in range(cardCount):
        operation["outCards"].append(struct.unpack_from('B', strData, nextPointer)[0])
        nextPointer += 1

    return operation, nextPointer


# 解码基本信息
def decodePass(strData, pointer):
    operation = {}
    nextPointer = pointer
    operation["action"] = "pass"
    operation["seatIndex"] = struct.unpack_from('B', strData, nextPointer)[0]
    nextPointer += 1

    return operation, nextPointer


# 二进制字符串转16进制字符串
def binToHex(binStr):
    length = len(binStr)
    array = []
    pointer = 0
    while length > pointer:
        array.append("%02x" % (struct.unpack_from('B', binStr, pointer)[0]))
        pointer += 1
    return ''.join(array)


# 16进制字符串转二进制字符串
def hexToBin(hexStr):
    length = len(hexStr)
    pointer = 0
    array = []
    while length > pointer:
        array.append(struct.pack('B', int(hexStr[pointer:pointer + 2], 16)))
        pointer += 2
    return ''.join(array)
