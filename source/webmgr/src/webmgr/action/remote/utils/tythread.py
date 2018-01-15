# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import threading
import time

from webmgr.action import actlog


def cread_thread(fun_run, *params):
    t = threading.Thread(target=fun_run, args=params)
    t.start()
    return t


def mutil_thread_machine_action(params, fun_thread_main):
    stime = time.time()
    threads = []
    machines = params['options'].machinedict.values()
    for machine in machines:
        # done 0 - 线程运行中 1 － 线程结束
        # result 0 - 操作进行中 1 － 正常结束 2 － 异常结束
        controls = {'params': params, 'machine': machine, 'done': 0, 'result': 0}
        t = cread_thread(fun_thread_main, controls)
        controls['thread'] = t
        threads.append(controls)

    # runchars = ['*', '-', '\\', '|', '/']
    isdoneall = 0
    resultall = 0
    #     wcount = 0

    while 1:
        ct = time.time()
        slines = []
        isdoneall = 0
        resultall = 0
        for worker in threads:
            isdone = worker.get('done', 0)
            result = worker.get('result', 0)
            percent = worker.get('percent', None)
            isdoneall += isdone
            resultall += result

            if result == 0:
                st = 'R'  # runchars[wcount % len(runchars)]
            elif result == 1:
                st = 'O'
            else:
                st = 'E'

            if percent is not None:
                if result == 0:
                    st = percent + st
                elif result == 1:
                    st = percent + st
                else:
                    st = percent + st

            slines.append(st + ' ')

        ptime = '%03d' % (time.time() - stime)
        lmsg = 'PROGRESS       : ' + ptime + ' ' + ''.join(slines)
        actlog.log(lmsg)
        if isdoneall == len(threads):
            break
        time.sleep(max(0.1, 1 - time.time() + ct))
    # wcount += 1

    haserror = 0
    for worker in threads:
        ip = worker['machine']['intranet']
        result = worker.get('result', 0)
        if result == 1:
            resultstr = 'OK'
        else:
            resultstr = 'ERROR'
            haserror = 1

        msg = 'REMOTE : %-16s : %s' % (ip, resultstr)
        if result == 1:
            actlog.log(msg)
        else:
            outputs = worker.get('outputs', '')
            for l in outputs.split('\n'):
                actlog.log(msg, l)

        finalstatus = worker.get('finalstatus', None)
        if finalstatus:
            for line in finalstatus:
                actlog.log(line)

    return haserror
