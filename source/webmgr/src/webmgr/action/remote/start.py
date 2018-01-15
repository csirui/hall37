# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import time

from webmgr.action import actlog
from webmgr.action.remote import execute_remote_py, getMachinePids
from webmgr.action.remote.utils import tythread, tyssh


def action(options):
    """
    这个部分启动所有的远程进程, 取得所有进程的pid, pid需要在3秒内保持不变即可
    随后, 发送hotcmd命令到各个进程去查询其运行状态
    """
    actlog.log('server start on all machines !')
    params = {'options': options}
    filters = [['AG'], ['UT', 'PL', 'PG', 'CT', 'RB'], ['GR', 'GT'], ['HT', 'CO']]
    for f in filters:
        params['thread_filter'] = f
        haserror = tythread.mutil_thread_machine_action(params, _thread_action_start)
        if haserror:
            actlog.log('server start error !')
            return 0
    if haserror:
        actlog.log('server start error !')
        return 0
    return 1


def _thread_action_start(controls):
    """
    这个方法运行再多线程当中
    """
    params = controls['params']
    machine = controls['machine']
    options = params['options']
    pfilter = params['thread_filter']
    procids = getMachinePids(options, machine, pfilter)
    if not procids:
        controls['done'] = 1
        controls['result'] = 1
        controls['outputs'] = 'the procids is empty'
        return

    controls['percent'] = '++++'

    # 启动本机的所有进程
    rparams = ['start']
    rparams.extend(procids)
    result, outputs = execute_remote_py(options, machine, rparams)
    if result != 0:
        actlog.log('remote start false !')
        actlog.log('---------------------------------------------------------------')
        for l in outputs.split('\n'):
            actlog.log(l)
        actlog.log('---------------------------------------------------------------')
        controls['done'] = 1
        controls['result'] = 2
        controls['percent'] = 'done'
        controls['outputs'] = outputs
        return

    # 获得本机的所有进程基本信息
    thread_info = tyssh.parse_remote_datas_json(outputs, 'TY_THREAD_INFO')
    pypypids = {}
    for k, v in thread_info.items():
        pypypids[k] = v['pypy']['pid']
        actlog.log(machine['host'], 'sid=', k, 'pid=', pypypids[k])

    # 远程发送hotcmd, 取得进程的运行状态
    rparams = ['status']
    rparams.extend(procids)
    wst = time.time()
    while 1:
        isdone = 0
        result, outputs = execute_remote_py(options, machine, rparams)
        if result != 0:
            actlog.log('read remote status false retry !')
            actlog.log('---------------------------------------------------------------')
            for l in outputs.split('\n'):
                actlog.log(l)
            actlog.log('---------------------------------------------------------------')
        else:
            try:
                # 获得本机的所有进程基本信息
                thread_status = tyssh.parse_remote_datas_json(outputs, 'TY_THREAD_STATUS')
                ecount = 0.0
                scount = 0.0
                wcount = 0.0
                errpids = []
                for sid in pypypids:
                    status = thread_status.get(sid, {})
                    if pypypids[sid] != status.get('pid', pypypids[sid]):
                        ecount += 1
                        errpids.append(sid)
                    else:
                        st = status.get('status', 0)
                        if st == 500:
                            ecount += 1
                            errpids.append(sid)
                        elif st == 200:
                            scount += 1
                        else:
                            wcount += 1
                controls['percent'] = str(int(scount * 100.0 / float(len(pypypids)))) + '%'
                if int(scount) + int(ecount) == len(pypypids):
                    # 全部启动成功
                    if int(ecount) > 0:
                        # 有错误
                        controls['done'] = 1
                        controls['result'] = 2
                        controls['percent'] = 'done'
                        controls['outputs'] = 'remote process has Exception !'
                        for sid in errpids:
                            actlog.log(machine['host'], 'EXCEPTION !! ->', sid)
                        return
                    else:
                        # 没有错误
                        isdone = 1
                        break
            except:
                actlog.error()
        if isdone == 1:
            # 没有错误
            break
        elif time.time() - wst > 300:  # 5分钟启动超时
            actlog.log(machine['host'], 'time out !!!')
            actlog.log('remote status timeout false !' + str(errpids))
            controls['done'] = 1
            controls['result'] = 2
            controls['percent'] = 'done'
            controls['outputs'] = 'remote status timeout false !' + str(errpids)
            return
        time.sleep(1)

    controls['done'] = 1
    controls['result'] = 1
    controls['outputs'] = outputs
