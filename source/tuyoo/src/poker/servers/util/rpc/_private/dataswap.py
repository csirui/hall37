# -*- coding=utf-8 -*-
'''
Created on 2015-12-2
@author: zqh
'''

import freetime.util.log as ftlog
from freetime.entity import config
from poker.entity.configure import pokerconf, configure
from poker.entity.dao import daobase, daoconst
from poker.servers.util.rpc import dbmysql
from poker.servers.util.rpc._private import dataswap_scripts
from poker.util import strutil, timestamp

mysqlsize = -1


def getMysqlSize():
    global mysqlsize
    if mysqlsize < 0:
        msize = 0
        for k in config.global_config.get('freetime:db', {}).get('mysql', {}):
            if k.find('user') == 0:
                msize += 1
        mysqlsize = msize
        ftlog.info('getMysqlSize->', mysqlsize)
    return mysqlsize


def checkUserData(userId, clientId=None, appId=0):
    '''
    检查当前用户的数据是否是热数据(即存储在REDIS), 
    如果不是热数据, 那么重MYSQL中读取冷数据导入至热数据中
    同时更新当前用户的数据生命时间
    导入导出的用户数据包括user和个个游戏的所有数据
    返回:
        如果用户数据的最终状态为热数据,返回1
        如果用户数据不存在,返回0
    '''
    ftlog.debug('MySqlSwap checkUserData->userId=', userId, 'clientId=', clientId, 'appId=', appId)
    userId = int(userId)
    ctfull = timestamp.formatTimeMs()
    isok = daobase.executeUserLua(userId, dataswap_scripts.CHECK_USER_DATA_LUA_SCRIPT, 2, userId, ctfull)
    ftlog.debug('MySqlSwap checkUserData->userId=', userId, 'clientId=', clientId, 'appId=', appId, 'isok=', isok)
    if isok == 1:
        return 1
    if clientId:
        intClientId = pokerconf.clientIdToNumber(clientId)
    else:
        intClientId = configure.DEFAULT_CLIENT_ID
    appId = int(appId)
    return _tryReadDataFromMySql(userId, intClientId, appId, ctfull)


def _tryReadDataFromMySql(userId, intClientId, appId, ctfull):
    # 得到MySQL中的数据
    csize = getMysqlSize()
    dbname = 'user' + str(userId % csize)
    tablename = 't' + str(userId / csize % 200)
    sqlstr = 'select data from %s where userid=%d limit 1' % (tablename, userId)
    ftlog.info('_tryReadDataFromMySql', userId, intClientId, appId, dbname, sqlstr)
    jsonstr = dbmysql._queryMysql00(userId, dbname, sqlstr)
    ftlog.info('_tryReadDataFromMySql before', userId, jsonstr)
    if not jsonstr:
        ftlog.info('_tryReadDataFromMySql', userId, 'the user mysql data not found !')
        return 0
    loaddatas = strutil.loads(jsonstr)
    # 拆解执行数据装载，避免redis的slowlog, 避免挤压redis
    isok, chip, diamond, coin, coupon = 1, 0, 0, 0, 0
    rkeys = loaddatas.keys()
    while (len(rkeys)) > 0:
        subrkeys = rkeys[0:4]
        rkeys = rkeys[4:]
        subdata = {}
        for subkey in subrkeys:
            subdata[subkey] = loaddatas[subkey]
        jsonstr1 = strutil.dumps(subdata)
        isok1, chip1, diamond1, coin1, coupon1 = daobase.executeUserLua(userId,
                                                                        dataswap_scripts.DATA_SWAP_LUA_SCRIPT, 3,
                                                                        userId, ctfull, jsonstr1)
        ftlog.debug('_tryReadDataFromMySql save to redis->', userId, isok, jsonstr1)
        isok = min(isok, isok1)
        chip = max(chip, chip1)
        diamond = max(diamond, diamond1)
        coin = max(coin, coin1)
        coupon = max(coupon, coupon1)
    ftlog.info('_tryReadDataFromMySql save to redis->', userId,
               'isok=', isok, 'chip=', chip, 'diamond=', diamond,
               'coin=', coin, 'coupon=', coupon)
    chip, diamond, coin, coupon = strutil.parseInts(chip, diamond, coin, coupon)
    if isok == 1:
        from poker.entity.biz import bireport
        bireport.reportBiChip(userId, chip, chip, chip,
                              'DATA_FROM_MYSQL_2_REDIS_CHIP',
                              intClientId, appId, appId, 0,
                              daoconst.CHIP_TYPE_CHIP)
        bireport.reportBiChip(userId, coin, coin, coin,
                              'DATA_FROM_MYSQL_2_REDIS_COIN',
                              intClientId, appId, appId, 0,
                              daoconst.CHIP_TYPE_COIN)
        bireport.reportBiChip(userId, diamond, diamond, diamond,
                              'DATA_FROM_MYSQL_2_REDIS_DIAMOND',
                              intClientId, appId, appId, 0,
                              daoconst.CHIP_TYPE_DIAMOND)
        bireport.reportBiChip(userId, coupon, coupon, coupon,
                              'DATA_FROM_MYSQL_2_REDIS_COUPON',
                              intClientId, appId, appId, 0,
                              daoconst.CHIP_TYPE_COUPON)
        return 1
    return 0
