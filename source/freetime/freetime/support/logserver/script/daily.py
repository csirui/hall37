# -*- coding=utf-8 -*-

import json
import os
import shutil
import sys
import time
import traceback

import datetime
import redis

BI_RECORD_EXTRA_SIZE = 17  # 17字节数据包含：TUYO（4字节） 、recType（1字节）、recvTime（4字节）、logId（8字节）
BIN_PATH = '/home/bi/source/freetime/freetime/support/logserver/script'

# key:redis_pool name  value:redis_pool
# {"config":...,...}
redis_pool_map = {}

# key:log_type  value:log_type_struct
# {"format":...,record_size:...,single_file_record_count:...,index_field:[...]}
log_type_map = {}

# key:data key name, value:...
global_config = {}

today = time.strftime('%Y%m%d')


#
def run(**argd):
    global global_config
    global redis_pool_map
    global log_type_map
    _initFromRedis(argd["config_redis"])
    _initRedis(redis_pool_map)
    try:
        datadir_path = global_config["data_path"]
        datadir_backuppath = global_config["data_back_path"]
        move_and_create_file(datadir_path, datadir_backuppath, log_type_map, redis_pool_map)
    except:
        print "create file exception!!"
        traceback.print_exc()


def _initFromRedis(conf):
    global global_config
    global redis_pool_map
    global log_type_map
    print "init from redis:", conf[0], conf[1], conf[2]
    _rs = redis.StrictRedis(host=conf[0], port=conf[1], db=conf[2])
    rc, lc, glc = _rs.mget("freetime:db", "freetime:log_type", "freetime:global")
    redis_pool_map = json.loads(rc)
    global_config = json.loads(glc)
    log_type_map = json.loads(lc)


def move_old_file(datadir_path, datadir_backuppath, log_type, log_group, record_count, days_ago_move, redisHandler):
    print "move old file start!"
    logFileIndex = getNDaysAgoLogFileIndex(days_ago_move, redisHandler, log_type, log_group, record_count)
    if logFileIndex == None:
        return
    for index in range(0, logFileIndex):
        fileName = "bidata_%s_%s_%d.data" % (log_type, log_group, index)
        absPath = "%s/%s/%s/%s" % (datadir_path, log_type, log_group, fileName)
        movePath = "%s/%s/%s/%s" % (datadir_backuppath, log_type, log_group, fileName)
        moveDir = "%s/%s/%s" % (datadir_backuppath, log_type, log_group)
        if (not os.path.exists(moveDir)):
            os.makedirs(moveDir)
        print "move %s to %s" % (absPath, movePath)
        if not os.path.exists(absPath):
            print "move file %s error not exist" % absPath
            continue
        shutil.move(absPath, movePath)


def move_and_create_file(datadir_path, datadir_backuppath, log_type_map, redis_pool_map):
    print "create file start!"
    for log_type in log_type_map:
        try:
            record_size = log_type_map[log_type]["record_size"] + log_type_map[log_type][
                "reserved_size"] + BI_RECORD_EXTRA_SIZE
            record_count = int(log_type_map[log_type]["single_file_record_count"])
            days_ago_move = int(log_type_map[log_type]["days_ago_move"])
            pre_create_file_nums = int(log_type_map[log_type]["pre_create_file_nums"])
            groups = log_type_map[log_type]["group"]
            for n in groups:
                if n not in redis_pool_map:
                    print "group not exist !!", n
                    continue
                redisHandler = redis_pool_map[n]
                move_old_file(datadir_path, datadir_backuppath, log_type, n, record_count, days_ago_move, redisHandler)
                writeNewFiles(datadir_path, log_type, n, record_size, record_count, pre_create_file_nums, redisHandler)
        except:
            traceback.print_exc()
            print "parse log_type info error!", log_type


def writeFile(findex, absPath, record_size, record_count):
    startid = record_count * findex + 1
    mkcmd = BIN_PATH + '/mkbi ' + absPath + \
            ' ' + str(startid) + ' ' + str(record_count) + \
            ' ' + str(record_size)
    print "creat_bi_file cmd= %s" % mkcmd
    result = os.system(mkcmd)
    ret = result >> 8
    if ret != 0:
        print 'creat_bi_file ret= %d' % ret
    else:
        print 'creat_bi_file  %s successful' % absPath


def writeNewFiles(dir_path, log_type, group, record_size, record_count, pre_create_file_nums, redisHandler):
    logFileIndex = getNDaysAgoLogFileIndex(0, redisHandler, log_type, group, record_count)
    if None == logFileIndex:
        globalLogid = redisHandler.get("global:logid:%s:%s" % (group, log_type))
        if not globalLogid:
            logFileIndex = 0
        else:
            print "get %s logFileIndex error" % today
            return None
    if 0 == logFileIndex:
        for index in range(0, pre_create_file_nums):
            fileName = "bidata_%s_%s_%d.data" % (log_type, group, logFileIndex + index)
            absPath = "%s/%s/%s/%s" % (dir_path, log_type, group, fileName)
            if not os.path.isfile(absPath):
                writeFile(logFileIndex + index, absPath, record_size, record_count)
            else:
                print 'creat_bi_file  %s already exist' % absPath
    else:
        for index in range(1, pre_create_file_nums + 1):
            fileName = "bidata_%s_%s_%d.data" % (log_type, group, logFileIndex + index)
            print fileName
            absPath = "%s/%s/%s/%s" % (dir_path, log_type, group, fileName)
            if not os.path.isfile(absPath):
                writeFile(logFileIndex + index, absPath, record_size, record_count)
            else:
                print 'creat_bi_file  %s already exist' % absPath


def getNDaysAgoLogFileIndex(n, redisHandler, log_type, group, record_count):
    dateStr = getNDayAgo(n)
    redisKey = "day1st:%s:%s" % (group, log_type)
    firstLogId = redisHandler.hget(redisKey, dateStr)
    print "%s %s %s" % (redisKey, dateStr, firstLogId)
    if not firstLogId:
        if 0 == len(redisHandler.hgetall(redisKey)):
            print "day1st hashmap not exist!!!", redisKey
            firstLogId = 1
        else:
            print "get %s firstLogId not find" % dateStr
            return None
    logFileIndex = int(firstLogId) / record_count
    return logFileIndex


def getNDayAgo(n):
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=-n)
    n_days = now + delta
    return n_days.strftime('%Y%m%d')


def _initRedis(redis_pool_map):
    if "redis" in redis_pool_map:
        redisconf = redis_pool_map["redis"]
        for n in redisconf:
            try:
                c = redisconf[n]
                h, p, dbid = c[0], c[1], c[2]
                _rp = redis.StrictRedis(host=h, port=p, db=dbid)
                redis_pool_map[n] = _rp
                print n, _rp
            except:
                print "init redis error !! ", n, c
    else:
        print "redis conf not in db.json!!"


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Usage:pypy daily.py <config_redis_ip> <config_redis_port> <config_redis_dbid>"
        sys.exit(-1)

    _conf_ip = sys.argv[1]
    _conf_port = int(sys.argv[2])
    _conf_dbid = int(sys.argv[3])

    run(config_redis=(_conf_ip, _conf_port, _conf_dbid))

    sys.exit(0)
