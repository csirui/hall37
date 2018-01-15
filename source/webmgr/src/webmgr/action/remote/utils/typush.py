# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import os

from tyserver.tyutils import fsutils
from webmgr.action import actlog
from webmgr.action.remote.utils import tyssh as tyssh
from webmgr.action.remote.utils import tythread as mythread


def push_tar_to_all_server(options, tarfile, taroutpath, tarsubpath, rmLeft):

    machines = options.machinedict.values()
    if len(machines) == 1 :
        if machines[0].get('localhost', 0) == 1:
            return 1
    
    params = {
              'options' : options,
              'tarfile' : tarfile,
              'taroutpath' : taroutpath,
              'tarsubpath' : tarsubpath,
              'rmLeft' : rmLeft,
              }
    haserror = mythread.mutil_thread_machine_action(params, _thread_action_push)
    if haserror :
        actlog.error('push tar file error !', tarfile)
        return 0
    return 1


def _thread_action_push(controls):
    '''
    这个方法运行再多线程当中
    '''
    machine = controls['machine']
    result = 0
    outputs = ''
    try:
        if machine.get('localhost', 0) == 1 :
            controls['percent'] = '++++'
            result = 1
        else:
            result, outputs = _thread_action_push_ssh(controls)
    except:
        result = 2  # 代码异常
        actlog.error()

    controls['done'] = 1
    controls['result'] = result
    controls['outputs'] = outputs

def _thread_action_push_ssh(controls):
    
    controls['percent'] = '---%'
    
    params = controls['params']
    machine = controls['machine']
    tarfile = params['tarfile']
    taroutpath = params['taroutpath']
    tarsubpath = params['tarsubpath']
    rmLeft = params['rmLeft']
    options = params['options']
    tarpath = fsutils.getParentDir(tarfile)

    host = machine['host']
    tyssh.connect(host, machine['user'], machine['pwd'], machine['ssh'])
    
    controls['percent'] = '--+%'
    tyssh.mkdirs(host, options.env['output_path'])
    tyssh.mkdirs(host, options.env['log_path'])
    tyssh.mkdirs(host, options.env['webroot_path'])
    tyssh.mkdirs(host, options.env['bin_path'])
    tyssh.mkdirs(host, options.env['backup_path'])
    tyssh.mkdirs(host, tarpath)

    controls['percent'] = '000%'
    localfilesize = os.path.getsize(tarfile)

    def update_send_size(sendsize_, allsize_):
        if sendsize_ == allsize_ :
            p = 100
        else:
            p = int((float(sendsize_) / float(allsize_)) * 100)
        controls['percent'] = '% 3d' % (p) + '%'

    putsize = tyssh.put_file(host, tarfile, tarfile, update_send_size)
    if int(putsize) != localfilesize :
        return 2, 'SSH Push ERROR ' + tarfile

    controls['percent'] = '110%'
    
    bin_path = options.env['bin_path']
    remotepy = fsutils.appendPath(bin_path, 'remote.py')
    remotetarpy = fsutils.appendPath(tarpath, 'remote.py')
    putsize = tyssh.put_file(host, remotepy, remotetarpy, None)
    localfilesize = os.path.getsize(remotepy)
    if int(putsize) != localfilesize :
        return 2, 'SSH Push ERROR ' + remotetarpy

    controls['percent'] = '120%'
    cmdline = 'pypy %s %s %s %s %s %s' % (remotetarpy, 'xvf', tarfile, taroutpath, tarsubpath, rmLeft)
    outputs = tyssh.executecmd(host, cmdline)
    status = tyssh.parse_remote_datas_int(outputs)
    if status != 0 :
        for l in outputs.split('\n'):
            actlog.log('REMOTE ERROR', l)
        return 2, 'SSH Push remote tar xvf ERROR'

    controls['percent'] = '++++'
    return 1, ''

