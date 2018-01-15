# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import json
import os
import subprocess
import traceback

import paramiko
import psutil

from tyserver.tyutils import fsutils

###############################################################################
# paramiko SSH util 
###############################################################################
_SSH_CLIENT = {}
_SFTP_CLIENT = {}


def get_ssh(ip):
    return _SSH_CLIENT[ip]


def get_sftp(ip):
    return _SFTP_CLIENT[ip]


def close_ip(ip):
    close_sftp(ip)
    close_ssh(ip)


def close_ssh(ip):
    global _SSH_CLIENT
    if ip in _SSH_CLIENT:
        try:
            _SSH_CLIENT[ip].close()
        except:
            pass
        del _SSH_CLIENT[ip]


def close_sftp(ip):
    global _SFTP_CLIENT
    if ip in _SFTP_CLIENT:
        try:
            _SFTP_CLIENT[ip].close()
        except:
            pass
        del _SFTP_CLIENT[ip]


def release_all():
    global _SSH_CLIENT, _SFTP_CLIENT
    for ip in _SFTP_CLIENT.keys():
        close_ssh(ip)

    for ip in _SSH_CLIENT.keys():
        close_sftp(ip)

    _SSH_CLIENT = {}
    _SFTP_CLIENT = {}


def connect(ip, user, password, port=22, reconnect=False):
    global _SSH_CLIENT, _SFTP_CLIENT
    try:
        if reconnect:
            close_ip(ip)

        if not ip in _SFTP_CLIENT:
            s = paramiko.SSHClient()

            if isinstance(password, (str, unicode)) and len(password) > 0:
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                s.connect(ip, port, user, password, timeout=15)
            else:
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                hpath = os.path.expanduser('~') + '/.ssh/id_rsa'
                #                 print 'load id_rsa->', hpath
                key = paramiko.RSAKey.from_private_key_file(hpath)
                s.load_system_host_keys()
                s.connect(ip, port, pkey=key)

            _SSH_CLIENT[ip] = s
            _SFTP_CLIENT[ip] = s.open_sftp()
            return s
    except:
        traceback.print_exc()
        raise Exception('can not connect to ' + str(ip))


def executecmd(ip, cmdline):
    sclient = get_ssh(ip)
    #     sftp = get_sftp(ip)
    _, stdouts_, stderrs_ = sclient.exec_command(cmdline, get_pty=True)
    lines = []
    for line in stdouts_:
        lines.append(line.strip())
    for line in stderrs_:
        lines.append(line.strip())

    outputs = None
    for line in lines:
        if line.find('TY_TASK_LOG_FILE') >= 0:
            resultfile = line.split('=')[1].strip()
            localfile = os.getcwd() + os.path.sep + 'actlog' + os.path.sep + os.path.basename(resultfile) + ip
            get_file(ip, resultfile, localfile, None)
            #             try:
            #                 sftp.remove(resultfile)
            #             except:
            #                 pass
            outputs = fsutils.readFile(localfile)
            fsutils.deleteFile(localfile)
            break

    if outputs == None:
        outputs = '\n'.join(lines)

    return outputs


def executecmd_local(cmdline):
    child1 = psutil.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    s1, s2 = child1.communicate()
    outputs = s1 + '\n' + s2
    lines = outputs.split('\n')
    for x in xrange(len(lines)):
        lines[x] = lines[x].strip()

    outputs = None
    for line in lines:
        if line.find('TY_TASK_LOG_FILE') >= 0:
            resultfile = line.split('=')[1].strip()
            outputs = fsutils.readFile(resultfile)
            fsutils.deleteFile(resultfile)
            break

    if outputs == None:
        outputs = '\n'.join(lines)

    return outputs


def parse_remote_datas_int(outputs):
    lines = outputs.split('\n')
    for line in lines:
        if line.find('TY_TASK_RESULT_INT') >= 0:
            result = line.split('=')[1].strip()
            return int(result)
    return -1


def parse_remote_datas_json(outputs, key):
    lines = outputs.split('\n')
    for line in lines:
        if line.find(key) >= 0:
            result = line.split('=')[1].strip()
            return json.loads(result)
    return -1


def mkdirs(ip, mpath):
    sftp = get_sftp(ip)
    mpath = os.path.abspath(mpath)
    tks = mpath.split(os.path.sep)
    for x in xrange(len(tks) + 1):
        p = os.path.sep.join(tks[0:x])
        if len(p) > 0:
            try:
                sftp.mkdir(p)
            except:
                pass
    attr = sftp.stat(mpath)
    if attr.st_mtime <= 0:
        raise Exception('Remote Folder make error ! ' + str(ip) + ':' + str(mpath))


def _dummy_file_callback(size, filesize):
    pass


def put_file(ip, localpath, remotepath, fun_callback):
    if not fun_callback:
        fun_callback = _dummy_file_callback
    sftp = get_sftp(ip)
    attrs = sftp.put(localpath, remotepath, callback=fun_callback)
    return attrs.st_size


def get_file(ip, remotepath, localpath, fun_callback):
    if not fun_callback:
        fun_callback = _dummy_file_callback
    sftp = get_sftp(ip)
    sftp.get(remotepath, localpath, callback=fun_callback)
