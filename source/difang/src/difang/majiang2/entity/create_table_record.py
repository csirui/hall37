# coding:utf-8
import json
import time

import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack
from poker.entity.dao import daobase
from poker.protocol import router
from poker.util.strutil import md5digest


class MJCreateTableRecord(object):
    """自建桌战绩
    """
    _user_record_count = 20  # 一个用户最多存储的数据

    @classmethod
    def initialize(cls):
        """初始化，加载lua脚本
        """
        pass

    @classmethod
    def _getRecordKey(cls, tableNo, gameId):
        """ 返回 所有战绩redis key
            tableNo 自建桌验证码 
        """
        if not tableNo or not tableNo.isdigit():
            return ''
        nowTime = int(time.time())
        return 'replay:%s:%s:%s' % (gameId, tableNo, nowTime)

    @classmethod
    def _getUserRecordKey(cls, userId, gameId):
        """ 返回 用户的战绩 redis key
        """
        return 'gamedata:%s:%s' % (gameId, userId)

    @classmethod
    def saveRecord(cls, budgets, tableNo, gameId):
        """
            1 在所有战绩中添加 战绩记录
            2 在所有用户的战绩中添加 战绩记录的 key
        """
        ftlog.debug('createTableRecordSaveRecord1')
        if 'tableNo' not in budgets or tableNo != budgets['tableNo']:
            ftlog.error('===budgets record===Trace==', tableNo, budgets)
            return
        ftlog.debug('createTableRecordSaveRecord2 tableNo=', tableNo)
        if isinstance(budgets, dict) and tableNo.isdigit() and int(tableNo) < 9999999:
            ftlog.debug('createTableRecordSaveRecord3 tableNo=', tableNo)
            replayKey = cls._getRecordKey(tableNo, gameId)
            ftlog.debug('createTableRecordSaveRecord3 mixKey=', replayKey)
            cls._saveRecordInAllList(budgets, replayKey, gameId)
            if 'budget' in budgets:
                for uid, _ in budgets['budget'].items():
                    userId = int(uid)
                    gameDataKey = cls._getUserRecordKey(userId, gameId)
                    cls.saveToGameData(userId, gameDataKey, replayKey, gameId)
        else:
            ftlog.error("==saveRecord==", budgets, tableNo, caller=cls)

    @classmethod
    def _saveRecordInAllList(cls, budgets, replayKey, gameId):
        """存储新的record到所有record列表中
        """
        replayDBKey = 'replay:%s' % (gameId)

        hasKey = daobase.executeRePlayCmd('HEXISTS', replayDBKey, replayKey)
        if not hasKey:
            daobase.executeRePlayCmd('HSET', replayDBKey, replayKey, json.dumps(budgets))

    @classmethod
    def saveToGameData(cls, userId, gameDataKey, replayKey, gameId):
        """
        往gamedata下添加数据
        """
        replayDBKey = 'replay:%s' % (gameId)
        ftlog.debug("MJCreateTableRecord_saveToGameData userId", userId
                    , "gameDataKey", gameDataKey
                    , "replayKey", replayKey
                    , "replayDBKey", replayDBKey)

        if daobase.executeUserCmd(userId, 'HEXISTS', gameDataKey, 'game_record'):
            ftlog.debug("MJCreateTableRecord_saveToGameData1")
            recordData = daobase.executeUserCmd(userId, 'HGET', gameDataKey, 'game_record')
            ftlog.debug("MJCreateTableRecord_saveToGameData2,recordData type = ", type(recordData), "content =",
                        recordData)
            recordList = json.loads(str(recordData))
            ftlog.debug("MJCreateTableRecord_saveToGameData2,recordList type = ", type(recordList), "content =",
                        recordList)
            if recordList and isinstance(recordList, dict):
                while len(recordList['recordIndex']) >= 20:
                    wastedReplayKey = recordList['recordIndex'].pop(0)
                    hasKey = daobase.executeRePlayCmd('HEXISTS', replayDBKey, wastedReplayKey)
                    if hasKey:
                        daobase.executeRePlayCmd('HDEL', replayDBKey, wastedReplayKey)
                recordList['recordIndex'].append(replayKey)
                ftlog.debug("MJCreateTableRecord_saveToGameData3")
            daobase.executeUserCmd(userId, 'HSET', gameDataKey, 'game_record', json.dumps(recordList))
        else:
            recordData = {"recordIndex": []}
            recordData['recordIndex'].append(replayKey)
            daobase.executeUserCmd(userId, 'HSET', gameDataKey, 'game_record', json.dumps(recordData))

    @classmethod
    def sendAllRecordToUser(cls, userId, gameId):
        """全量下发
        """
        gameDataKey = cls._getUserRecordKey(userId, gameId)
        replayDBKey = 'replay:%s' % (gameId)
        if daobase.executeUserCmd(userId, 'HEXISTS', gameDataKey, 'game_record'):
            gameRecord = daobase.executeUserCmd(userId, 'HGET', gameDataKey, 'game_record')
            ftlog.debug("sendAllRecordToUser.gameRecord = ", gameRecord)
            recordData = json.loads(gameRecord)
            if len(recordData['recordIndex']) > 0:
                records = []
                for temp in recordData['recordIndex']:
                    record = daobase.executeRePlayCmd('HGET', replayDBKey, temp)
                    if record:
                        records.append(record)
                ftlog.debug("sendAllRecordToUser.records = ", records)
                if isinstance(records, list) and len(records) > 0:
                    msg = MsgPack()
                    msg.setCmd('create_table')
                    msg.setResult('action', 'record')
                    msg.setResult('type', 'update')
                    msg.setResult('gameId', gameId)
                    retList = []
                    for recordStr in records:
                        if not recordStr:
                            continue
                        try:
                            ftlog.debug("sendAllRecordToUsersetRetData1")
                            record = json.loads(recordStr)
                            defaultScore = record.get('defaultScore', 0)
                            urls = record.get('recordUrls', [])
                            retData = {}
                            retData['recordTime'] = record.get('time', 0)
                            retData['createTableNo'] = record['tableNo']
                            # 客户端牌局回放key
                            retData['tableRecordKey'] = '%s.%s' % (
                            record.get('createTime', 0), retData['createTableNo'])
                            retData['record_download_info'] = []
                            retData['users'] = []
                            ftlog.debug("sendAllRecordToUsersetRetData2")
                            for uid, info in record['budget'].items():
                                deltaScoreList = info.get('deltaScoreList', 0)
                                score = info.get('score', [])
                                if isinstance(score, int):
                                    score = []
                                retData['users'].append({'name': info['name'], 'score': score, 'userId': info['uid'],
                                                         'deltaScore': deltaScoreList})
                                # 胜负结果字段
                                if int(uid) == userId:
                                    if deltaScoreList > 0:
                                        retData['winScore'] = 1
                                    elif deltaScoreList == 0:
                                        retData['winScore'] = 0
                                    elif deltaScoreList < 0:
                                        retData['winScore'] = -1
                                    else:
                                        retData['winScore'] = 0
                                if int(uid) == userId:
                                    retData['deltaScore'] = 0 - defaultScore
                                    for i in range(len(urls)):
                                        record_download_info_obj = {}
                                        record_download_info_obj['url'] = '%s' % (urls[i])
                                        record_download_info_obj['fileType'] = ''
                                        record_download_info_obj['MD5'] = md5digest(
                                            record_download_info_obj['url']).upper()
                                        retData['record_download_info'].append(record_download_info_obj)
                            ftlog.debug("sendAllRecordToUsersetRetData3", retData)
                            retList.append(retData)
                        except:
                            ftlog.error('==sendAllRecordToUser ===', records, ' keys:', recordData['recordIndex'])
                    msg.setResult('list', retList)
                    router.sendToUser(msg, userId)
        else:
            return
