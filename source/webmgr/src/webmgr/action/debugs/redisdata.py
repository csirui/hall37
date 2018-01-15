# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
from tyserver.tyutils import fsutils, tydb, tylog, strutil
import time
import json

ONLINES = ['10.3.0.8', '10.3.0.34', '10.3.0.9', '10.3.0.32']
ISONLINE = 0

def _getLastOkDefines(options):
    p = getattr(options, 'poker_path', None)
    if not p :
        p = getattr(options, 'pokerpath', None)
    lastfile = p + '/._service_.json'
    datas = fsutils.readJsonFile(lastfile)
    return datas


def _getRedisDefCluster(rdbs, groupBy, head='user'):
    count = 0
    for k in rdbs :
        if k.find(head) == 0 :
            count += 1
    x = groupBy % count
    k = head + str(x)
    if rdbs[k][0] in ONLINES :
        global ISONLINE
        ISONLINE = 1
    return rdbs[k]


def _execute_scan(conn, matchstr, callback, *params):
    if ISONLINE :
        raise Exception('Its ONLINE !!, do not use normal test commands !!!')
    cur = 0
    scount = 0
    while cur >= 0 :
        datas = conn.scan(cur, matchstr, 600)
        cur = datas[0]
        if datas[1] :
            for rkey in datas[1] :
                scount += 1
                callback(conn, rkey, *params)
        if cur == 0 :
            break
    return scount


def redis_clear_all(options):
    datas = _getLastOkDefines(options)
    rdbs = datas['dbdict']['redis']
    for rdb in rdbs.values() :
        tydb.execute_redis_cmd_safe(rdb, 'flushdb')
    return 1

def _repr_(v):
    v = repr(v)
    if len(v) > 1 :
        if v[0] == "'" and v[-1] == "'" :
            v = v[1:-1]
    return v
    
def _warp_redis_fetch(data):
    if isinstance(data, (list, set, tuple)) :
        ndata = []
        for x in data :
            try:
                json.dumps(x)
                ndata.append(x)
            except:
                ndata.append(_repr_(x))
        return ndata
    
    if isinstance(data, dict) :
        ndata = {}
        for k, v in data.items() :
            try:
                json.dumps(k)
            except:
                k = _repr_(k)
            try:
                json.dumps(v)
            except:
                v = _repr_(v)
            ndata[k] = v
        return ndata
    
    try:
        json.dumps(data)
        return data
    except:
        return _repr_(data)


def _execute_redis_fetch(conn, rkey):
    dtype = conn.type(rkey)
    if dtype == 'hash' :
        data = conn.hgetall(rkey)
    elif dtype == 'list' :
        data = conn.lrange(rkey, 0, -1)
    elif dtype == 'string' :
        data = conn.get(rkey)
    elif dtype == 'set' :
        data = conn.smembers(rkey)
    elif dtype == 'zset' :
        data = conn.zrange(rkey, 0, -1, withscores=True)
    else:
        data = None

    return _warp_redis_fetch(data)


def redis_search_all_userdata(options, userId):
    if userId <= 0 :
        return 'param userId ERROR !!'
    datas = _getLastOkDefines(options)
    rdbs = datas['dbdict']['redis']
    rdb = _getRedisDefCluster(rdbs, userId)
    conn = tydb.get_redis_conn(rdb)
    datas = {}
    def get_data(conn, rkey):
        tylog.debug('find key->', rkey)
        datas[rkey] = _execute_redis_fetch(conn, rkey)

    _execute_scan(conn, '*:' + str(userId), get_data)
    del conn
    return datas


def redis_get_userdata(options, userId):
    return redis_search_all_userdata(options, userId)


def redis_set_userdata(options, userId, key, value):
    if userId <= 0 :
        return 'param userId ERROR !!'
    if not key :
        return 'param key ERROR !!'
    datas = _getLastOkDefines(options)
    rdbs = datas['dbdict']['redis']
    rdb = _getRedisDefCluster(rdbs, userId)
    conn = tydb.get_redis_conn(rdb)
    conn.hset('user:' + str(userId), key, value)
    data = conn.hget('user:' + str(userId), key)
    del conn
    return {'key' : key, 'value' : data}


def redis_get_gamedata(options, userId, gameId):
    if userId <= 0 :
        return 'param userId ERROR !!'
    if gameId <= 0 :
        return 'param gameId ERROR !!'
    datas = _getLastOkDefines(options)
    rdbs = datas['dbdict']['redis']
    rdb = _getRedisDefCluster(rdbs, userId)
    conn = tydb.get_redis_conn(rdb)
    datas = {}
    def get_data(conn, rkey):
        tylog.debug('find key->', rkey)
        datas[rkey] = _execute_redis_fetch(conn, rkey)
    _execute_scan(conn, '*:' + str(gameId)  +':' + str(userId), get_data)
    del conn
    return datas


def redis_set_gamedata(options, userId, gameId, key, value):
    if userId <= 0 :
        return 'param userId ERROR !!'
    if gameId <= 0 :
        return 'param gameId ERROR !!'
    if not key :
        return 'param key ERROR !!'
    datas = _getLastOkDefines(options)
    rdbs = datas['dbdict']['redis']
    rdb = _getRedisDefCluster(rdbs, userId)
    conn = tydb.get_redis_conn(rdb)
    conn.hset('gamedata:' + str(gameId) + ':' + str(userId), key, value)
    data = conn.hget('gamedata:' + str(gameId) + ':' + str(userId), key)
    del conn
    return {'key' : key, 'value' : data}


def redis_get_config(options, rkey):
    datas = _getLastOkDefines(options)
    rdb = datas['pokerdict']['config_redis']
    conn = tydb.get_redis_conn(rdb)
    data = conn.get(rkey)
    del conn
    return strutil.loads(data)


def redis_del_userdata(options, userId):
    if userId <= 0 :
        return 'param userId ERROR !!'
    datas = _getLastOkDefines(options)
    rdbs = datas['dbdict']['redis']
    rdb = _getRedisDefCluster(rdbs, userId)
    conn_datas = tydb.get_redis_conn(rdb)
    conn_mix = tydb.get_redis_conn(rdbs['mix'])
    conn_userkeys = tydb.get_redis_conn(rdbs['keymap'])

    acc, mobile1, snsid, email, devid, mobile2, mobile3, mobile4, devid2 = \
    conn_datas.hmget('user:%d' % (userId), 'userAccount', 'mobile', 'snsId', 'email', \
                                 'mdevid', 'bindMobile', 'phonenumber', 'detect_phonenumber', 'sessionDevId')
    
    delkeys = []
    def delete_redis_key(conn, rkey):
        conn.delete(rkey)
        delkeys.append(rkey)
        tylog.debug('REDIS DELETE-->[', rkey, ']')
    
    _execute_scan(conn_datas, '*:' + str(userId), delete_redis_key)
    _execute_scan(conn_mix, '*:' + str(userId), delete_redis_key)
    conn_userkeys.delete('devidmap:%s' % (devid))
    conn_userkeys.delete('newdevidmap:%s' % (devid))
    conn_userkeys.delete('devidmap3:%s' % (devid))
    conn_userkeys.delete('devidmap:%s' % (devid2))
    conn_userkeys.delete('newdevidmap:%s' % (devid2))
    conn_userkeys.delete('devidmap3:%s' % (devid2))
    conn_userkeys.delete('snsidmap:%s' % (snsid))
    conn_userkeys.delete('mailmap:%s' % (email))
    conn_userkeys.delete('accountmap:%s' % (acc))
    conn_userkeys.delete('mobilemap:%s' % (mobile1))
    conn_userkeys.delete('mobilemap:%s' % (mobile2))
    conn_userkeys.delete('mobilemap:%s' % (mobile3))
    conn_userkeys.delete('mobilemap:%s' % (mobile4))
    del conn_datas
    del conn_userkeys
    del conn_mix

    return delkeys


def redis_del_gamedata(options, userId, gameId):
    if userId <= 0 :
        return 'param userId ERROR !!'
    if gameId <= 0 :
        return 'param gameId ERROR !!'

    datas = _getLastOkDefines(options)
    rdbs = datas['dbdict']['redis']
    rdb = _getRedisDefCluster(rdbs, userId)
    conn_datas = tydb.get_redis_conn(rdb)

    delkeys = []
    def delete_redis_key(conn, rkey):
        conn.delete(rkey)
        delkeys.append(rkey)
        tylog.debug('REDIS DELETE-->[', rkey, ']')
    
    _execute_scan(conn_datas, '*:' + str(gameId) + ':' + str(userId), delete_redis_key)
    del conn_datas

    return delkeys


def redis_del_weakdata(options, userId, resetCheckIn):
    if userId <= 0 :
        return 'param userId ERROR !!'

    datas = _getLastOkDefines(options)
    rdbs = datas['dbdict']['redis']
    rdb = _getRedisDefCluster(rdbs, userId)
    conn_datas = tydb.get_redis_conn(rdb)

    delkeys = []
    def delete_redis_key(conn, rkey):
        conn.delete(rkey)
        delkeys.append(rkey)
        tylog.debug('REDIS DELETE-->[', rkey, ']')

    def delete_nslogin(conn, rkey):
        conn.hdel(rkey, 'newnslogin.lastlogin')
        conn.hdel(rkey, 'newnslogin.nslogin')
        tylog.debug('REDIS HDEL-->[', rkey, 'newnslogin.nslogin, newnslogin.lastlogin]')
        delkeys.append(rkey + ' newnslogin.nslogin, newnslogin.lastlogin')

    _execute_scan(conn_datas, 'weak:*:' + str(userId), delete_redis_key)
    _execute_scan(conn_datas, 'gamedata*:' + str(userId), delete_nslogin)
    
    if resetCheckIn :
        now = int(time.time())
        sec_of_1day = 24 * 60 * 60
        conn_datas.hset('user:' + str(userId), 'firstDailyCheckin', now - (2 * sec_of_1day))
        conn_datas.hset('user:' + str(userId), 'lastDailyCheckin', now - sec_of_1day)

    del conn_datas

    return delkeys

def redis_get_usertime(options, userId):
    if userId <= 0 :
        return 'param userId ERROR !!'

    datas = _getLastOkDefines(options)
    rdbs = datas['dbdict']['redis']
    rdb = _getRedisDefCluster(rdbs, userId)
    conn_datas = tydb.get_redis_conn(rdb)

    infos = []
    datas = conn_datas.hmget('user:' + str(userId), 'createTime', 'authorTime')
    infos.append('user:' + str(userId) + ' -> createTime :' + str(datas[0]))
    infos.append('user:' + str(userId) + ' -> authorTime :' + str(datas[1]))

    def get_game_time(conn, rkey):
        datas = conn.hmget(rkey, 'createTime', 'authorTime', 'lastlogin')
        infos.append(rkey + ' -> createTime :' + str(datas[0]))
        infos.append(rkey + ' -> authorTime :' + str(datas[1]))
        infos.append(rkey + ' -> lastlogin :' + str(datas[2]))

    _execute_scan(conn_datas, 'gamedata*:' + str(userId), get_game_time)
    
    return infos

def _decode_x(v):
    if v.find('\\x') >= 0:
        gg = {}
        exec('gvv="' + v +'"', gg, gg)
        return gg['gvv']
    return v

def redis_do_command(options, userId, roomId, ralias, cmdline):
    
    datas = _getLastOkDefines(options)
    rdbs = datas['dbdict']['redis']
    if ralias == 'config' :
        rdb = datas['pokerdict']['config_redis']
    elif ralias == 'user' :
        if userId <= 0 :
            return 'param userId ERROR !!'
        rdb = _getRedisDefCluster(rdbs, userId)
    elif ralias == 'table' :
        if roomId <= 0 :
            return 'param roomId ERROR !!'
        rdb = _getRedisDefCluster(rdbs, roomId, 'table')
    else:
        rdb = rdbs[ralias]

    conn = tydb.get_redis_conn(rdb)
    tylog.debug('redis_do_command->', cmdline)
    for x in xrange(len(cmdline)) :
        c = cmdline[x]
        cmdline[x] = _decode_x(c)
    try:
        data = conn.execute_command(*cmdline)
    except Exception, ex:
        data = str(ex)
        tylog.error(cmdline)
    del conn
    return _warp_redis_fetch(data)

