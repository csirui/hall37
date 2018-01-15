import json

import freetime.util.log as ftlog
from difang.majiang2.entity.create_table_record import MJCreateTableRecord
from freetime.entity.msg import MsgPack
from poker.entity.dao import daobase
from poker.protocol import router
from poker.util.strutil import md5digest


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
                        retData['tableRecordKey'] = '%s.%s' % (record.get('createTime', 0), retData['createTableNo'])
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
                                    record_download_info_obj['MD5'] = md5digest(record_download_info_obj['url']).upper()
                                    retData['record_download_info'].append(record_download_info_obj)
                        ftlog.debug("sendAllRecordToUsersetRetData3", retData)
                        retList.append(retData)
                    except:
                        ftlog.error('==sendAllRecordToUser ===', records, ' keys:', recordData['recordIndex'])
                msg.setResult('list', retList)
                router.sendToUser(msg, userId)
    else:
        return


MJCreateTableRecord.sendAllRecordToUser = sendAllRecordToUser
