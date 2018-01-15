# coding: utf-8

'''
配置辅助
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import freetime.util.log as ftlog
from hall.entity import hallshare
from poker.entity.configure import configure

GAME_ID = 9993


# httpApiGameNames = {8: "texas", 30: "t3card", 38: "t3cardhundred", 39: "t3flush"}


def getPublicConf(gameId, key):
    return configure.getGameJson(gameId, 'public', {}).get(key, {})


def getCustomRoomConf(gameId, key):
    return configure.getGameJson(gameId, 'custom_room', {}).get(key, {})


def getShareInfo(userId, gameId, shareKey):
    shareId = hallshare.getShareId(shareKey, userId, gameId)
    share = hallshare.findShare(shareId)
    if share:
        return share.getUrl(userId, gameId), share.getTitle(userId, gameId)
    else:
        return None, None


def getTableRecordUploadConf(gameId):
    conf = configure.getGameJson(GAME_ID, 'table_record', {})
    uploadUrls = conf.get("trUploadUrls", [])
    token = conf.get("trUploadKey", "")
    path = conf.get("trFilePath", "") + r"%d/" % gameId
    if ftlog.is_debug():
        ftlog.debug("|gameId, uploadUrls, token, path:", gameId, uploadUrls, token, path)
    return uploadUrls, token, path


def getTableRecordDownloadConf(gameId):
    conf = configure.getGameJson(GAME_ID, 'table_record', {})
    downloadUrl = conf.get("trDownloadPath", "")
    token = conf.get("trUploadKey", "")
    path = conf.get("trFilePath", "") + r"%d/" % gameId
    if ftlog.is_debug():
        ftlog.debug("|gameId, downloadUrl, token, path:", gameId, downloadUrl, token, path)
    return downloadUrl, token, path


def isEnableLogChatMsg(gameId):
    return configure.getGameJson(gameId, 'table_chat', {}).get('enableLogChatMsg', 1)


def getTableSmiliesConf(gameId, bigRoomId):
    conf = {
        "bomb": {
            "other_charm": 0,
            "price": 0,
            "self_charm": 0
        },
        "diamond": {
            "other_charm": 0,
            "price": 0,
            "self_charm": 0
        },
        "egg": {
            "other_charm": 0,
            "price": 0,
            "self_charm": 0
        },
        "flower": {
            "other_charm": 0,
            "price": 0,
            "self_charm": 0
        }
    }
    return conf
