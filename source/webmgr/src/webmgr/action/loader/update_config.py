# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from tyserver.tyutils import strutil, tydb, fsutils
from webmgr.action import actlog


def action(options):
    '''
    装载并检测服务启动配置文件
    '''
    alldata = options.alldata
    alldata['freetime:db'] = options.dbdict
    alldata['freetime:global'] = options.globaldict
    alldata['freetime:server'] = options.serverlist
    alldata['poker:cmd'] = options.cmddict
    alldata['poker:machine'] = options.machinedict
    alldata['poker:project'] = options.projectlist
    alldata['poker:global'] = options.pokerdict
    alldata['poker:oldcmd'] = fsutils.readJsonFile(options.poker_path + '/poker/oldcmd.json')

    config_redis = options.pokerdict['config_redis']
    changekeys, changelen = _update_redis_file_by_diff(config_redis, alldata)
    setattr(options, 'changekeys', changekeys)
    setattr(options, 'changelen', changelen)

    return 1


def _load_old_datas(redisaddr):
    actlog.log('Load Redis Old Datas :', redisaddr)
    # 取得当前的数据库数据
    rconn = tydb.get_redis_conn(redisaddr)
    oldkeys = []
    olddatas = {}

    def get_old_datas(ckeys_):
        oldkeys.extend(ckeys_)
        oldvalues = rconn.mget(ckeys_)
        for x in xrange(len(ckeys_)):
            #             actlog.log('old->', ckeys_[x], '=[', oldvalues[x], ']')
            olddatas[ckeys_[x]] = oldvalues[x]

    get_old_datas(["freetime:server", "freetime:db", "freetime:global"])
    get_old_datas(["poker:cmd", "poker:oldcmd", "poker:machine", "poker:project", "poker:global"])
    get_old_datas(["poker:map.productid"])
    get_old_datas(["poker:map.bieventid"])
    get_old_datas(["poker:map.clientid"])
    get_old_datas(["poker:map.giftid"])
    get_old_datas(["poker:map.activityid"])

    cur = 0
    while cur >= 0:
        datas = rconn.scan(cur, 'game:*', 999)
        cur = datas[0]
        ckeys = datas[1]
        if ckeys:
            get_old_datas(ckeys)
        if cur <= 0:
            break
    return oldkeys, olddatas


def _update_redis_file_by_diff(redisaddr, newdatas):
    oldkeys, olddatas = _load_old_datas(redisaddr)
    # REDIS中有, 配置文件中没有, 为要删除的键值
    delkeys = set(oldkeys) - set(newdatas.keys())
    for k in delkeys:
        if k.find(':map.') > 0:
            continue
        actlog.log('del->', k)

    # 检查要更新的键值
    updatas = {}
    for key, newvalue in newdatas.items():
        oldvalue = olddatas.get(key, None)
        if not isinstance(newvalue, (str, unicode)):
            newvalue = strutil.dumps(newvalue)
        if newvalue != oldvalue:
            updatas[key] = newvalue
        #             actlog.log('update->', key, 'new=[', newvalue, '] old=[', oldvalue, ']')

    actlog.log('redis update begin !!')
    rpipe = tydb.get_redis_pipe(redisaddr)
    changelen = 0
    for k in delkeys:
        if k.find(':map.') > 0:
            continue
        rpipe.delete(k)
        changelen += 1

    for k, v in updatas.items():
        rpipe.set(k, v)
        changelen += len(v)

    rpipe.execute()
    actlog.log('redis update done !!')

    changekeys = set(delkeys)
    changekeys.update(set(updatas.keys()))
    changekeys = list(changekeys)
    actlog.log('TY_REDIS_CHANGE_LIST=', strutil.dumps(changekeys))
    actlog.log('+++++++++++++++++++++')
    for k in changekeys:
        #         rpipe.rpush('configure.changed', k)
        actlog.log('CHANGED', k)
    #     rpipe.execute()
    actlog.log('+++++++++++++++++++++')
    return changekeys, changelen
