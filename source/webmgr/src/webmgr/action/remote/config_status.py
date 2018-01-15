# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from tyserver.tyutils import strutil, tydb
from webmgr.action import actlog
from webmgr.action.remote import hotfix


HOTCODE = '''code://
from poker.entity.configure import synccenter
global results
results['CINDEX'] = synccenter._CHANGE_INDEX
results['ERRORS'] = synccenter._LAST_ERRORS 
'''

_CHANGE_KEYS_NAME = 'configitems.changekey.list'

def action(options, integrate=0):
    '''
    装载并检测服务启动配置文件
    '''
    serverlist = options.serverlist
    setattr(options, 'hotfixpy', HOTCODE)
    setattr(options, 'hotfixwait', 1)
    x = 0
    serverIds = []
    for srv in serverlist :
        x += 1
        serverIds.append(srv['type'] + srv['id'])
    serverIds = ','.join(serverIds)
    setattr(options, 'serverIds', serverIds)
    if integrate == 0 :
        actlog.log('get configure status->', serverIds)
    ret = hotfix.action(options, 0)

    config_redis = options.pokerdict['config_redis']
    rconn = tydb.get_redis_conn(config_redis)
    clen = rconn.llen(_CHANGE_KEYS_NAME)
    try:
        datas = strutil.loads(ret)
    except:
        actlog.log('ERROR !!', ret)
        if integrate == 0 :
            return 0
        return 0, 0
    
    confOks = []
    confNgs = []
    errors = []
    errorids = []
    for sid in datas :
        if isinstance(datas[sid], dict):
            cidx = datas[sid].get('CINDEX', None)
            cerrs = datas[sid].get('ERRORS', [])
        else:
            cidx = ''
            cerrs = []
            actlog.log('ERROR !!!! ', sid, datas[sid])
        if cerrs :
            errorids.append(sid)
            for cerr in cerrs :
                erritem = [cerr.get('exception', None), cerr.get('tarceback', None)]
                if not erritem in errors :
                    errors.append(erritem)

        if isinstance(cidx, int) :
            if cidx >= clen :
                confOks.append(sid)
            else:
                confNgs.append(sid)
        else:
            actlog.error('ERROR !!', sid, 'GET STATUS ERROR !!', datas[sid])
    
    if errors :
        actlog.log('ERROR IDS =', ','.join(errorids))
        actlog.log('========== ERROR !!!! BEGINE ========')
        for x in errors :
            actlog.log('========== Exception ========')
            for l in x[0] :
                for m in l.split('\n') :
                    if m :
                        actlog.log(m)
            actlog.log('========== Traceback ========')
            for l in x[1] :
                for m in l.split('\n') :
                    if m :
                        actlog.log(m)
        actlog.log('========== ERROR !!!! END ========')
        raise Exception('Remote Exception')
        if integrate == 0 :
            return 0
        else:
            return 0, 0

    if integrate == 0 :    
        actlog.log('THE CONFIGURE KEY INDEX =', clen)
        actlog.log('TOTAL_COUNT =', len(serverlist) , 'OK_COUNT =', len(confOks), 'DELAY_COUNT =', len(confNgs))
        actlog.log('CONFIGURE_STATUS = %0.2d' % (int(float(len(confOks)) / len(datas) * 100)) + '%')
    if integrate == 0 :
        return 1
    else:
        return len(confOks), len(serverlist)


