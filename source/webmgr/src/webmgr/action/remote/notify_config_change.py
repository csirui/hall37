# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from tyserver.tyutils import strutil, tydb
from webmgr.action import actlog
from webmgr.action.remote import hotfix, config_status
from datetime import datetime
import time


HOTCODE = '''code://
from poker.servers.rpc import srvmgr
from poker.entity.configure import gdata
global results
keylist = %s
reloadlist = %s
sleepTime = %f
serverIds = [gdata.serverId()]
rets = srvmgr.reloadConfig(serverIds, keylist, reloadlist, sleepTime)
results.update(rets)
'''

def action(options, extkeys=[]):
    '''
    装载并检测服务启动配置文件
    '''
    sleepTime = 0.001
#     reloadlist = []
    changekeys = options.changekeys
    serverlist = options.serverlist
    changelen = options.changelen
    if extkeys :
        changekeys.extend(extkeys)
    if options.reset:
        changekeys = ['all']
#     if options.reset:
#         reloadlist = ['all']
    actlog.log('changekeys=', changekeys)
    actlog.log('changelen =', changelen)
    actlog.log('sleep time=', sleepTime)
    
#     hotcode = HOTCODE % (strutil.dumps(changekeys),
#                          strutil.dumps(reloadlist),
#                          sleepTime)
    config_redis = options.pokerdict['config_redis']
    rconn = tydb.get_redis_conn(config_redis)
    _CHANGE_KEYS_NAME = 'configitems.changekey.list'
    rconn.rpush(_CHANGE_KEYS_NAME, 'CHANG_TIME %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')))
    for ckey in changekeys :
        rconn.rpush(_CHANGE_KEYS_NAME, ckey)

#     setattr(options, 'hotfixpy', hotcode)
#     setattr(options, 'hotfixwait', 1)
#     x = 0

#     ipgroups = {}
#     for srv in serverlist :
#         x += 1
#         ip = srv['ip']
#         if ip in ipgroups :
#             sids = ipgroups[ip]
#         else:
#             sids = []
#             ipgroups[ip] = sids
#         sids.append(srv['type'] + srv['id'])
#     
#     # 每次每个机器更新10个进程
#     while 1 :
#         sids = []
#         for ip in ipgroups.keys() :
#             mids = ipgroups[ip]
#             head = mids[0:10]
#             ipgroups[ip] = mids[10:]
#             sids.extend(head)
#         if not sids :
#             break
#         sids = ','.join(sids)
#         setattr(options, 'serverIds', sids)
#         actlog.log('notify config changed->', sids)
#         ret = hotfix.action(options, 0)
#         if ret.find('"error"') >= 0 :
#             actlog.log('ERROR !!!')
#             actlog.log(ret)
#             actlog.log('ERROR !!!')
#             return 0
#         time.sleep(2)

    actlog.log('Configure update wait :', 0, '/', len(serverlist))
    while 1 :
        okcounts, allcounts = config_status.action(options, 1)
        if allcounts <= 0 :  # 有异常发生
            actlog.log('Configure update ERROR !!')
            return 0
        elif okcounts == allcounts :  # 完成同步
            actlog.log('Configure update OK :', okcounts, '/', allcounts)
            return 1
        else :  # 没有同步完成
            actlog.log('Configure update WAIT :', okcounts, '/', allcounts)
            time.sleep(2)
    return 1

