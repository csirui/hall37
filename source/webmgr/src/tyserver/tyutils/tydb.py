# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
from redis.client import StrictRedis


###############################################################################
# logger for make, compiler, remote control
###############################################################################
def get_redis_conn(redisdef):
    if isinstance(redisdef, dict) :
        host = redisdef['host']
        port = int(redisdef['port'])
        dbid = int(redisdef['dbid'])
    elif isinstance(redisdef, (list, tuple)) :
        host = redisdef[0]
        port = int(redisdef[1])
        dbid = int(redisdef[2])
    else:
        datas = redisdef.split(':')
        host = datas[0]
        port = int(datas[1])
        dbid = int(datas[2])
    for x in (6, 5, 4, 3, 2, 1) :
        try:
            rconn = StrictRedis(host=host, port=port, db=dbid)
            return rconn
        except Exception, e:
            if x == 1 :
                raise e


def execute_redis_cmd_safe(redisdef, cmd, *params):
    for x in (6, 5, 4, 3, 2, 1) :
        try:
            conn = get_redis_conn(redisdef)
            fun = getattr(conn, cmd)
            datas = fun(*params)
            del conn
            return datas
        except Exception, e:
            if x == 1 :
                raise e


def get_redis_pipe(redisdef):
    return get_redis_conn(redisdef).pipeline()

