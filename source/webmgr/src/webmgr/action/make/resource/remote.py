# -*- coding: utf-8 -*-
'''
Created on ${TIME}
@author: zqh
'''
import commands
from datetime import datetime
import platform
import traceback
import json
import getpass
import fcntl
import pty
import time
import subprocess
import psutil
import os
import sys
import re

if sys.getdefaultencoding().lower() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding("utf-8")
    sys.stderr = sys.stdout

bin_path = '${BIN_PATH}'
log_path = '${LOG_PATH}'
redis_config = '${REDIS_CONFIG}'

log_file = log_path + '/remote.out'
if not os.path.isdir(log_path):
    os.makedirs(log_path)
if not os.path.isfile(log_file):
    _logf = open(log_file, 'w')
else:
    _logf = open(log_file, 'a+')


def getLocalIps():
    try:
        ipstr = '([0-9]{1,3}\.){3}[0-9]{1,3}'
        cmd = '/bin/ifconfig'
        if not os.path.isfile(cmd) :
            cmd = '/sbin/ifconfig'
        if not os.path.isfile(cmd) :
            cmd = 'ifconfig'
        ipconfig_process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output = ipconfig_process.stdout.read()
        if output.find('inet addr:') >= 0:
            ip_pattern = re.compile('(inet addr:%s)' % ipstr)
        else:
            ip_pattern = re.compile('(inet %s)' % ipstr)
        pattern = re.compile(ipstr)
        iplist = []
        for ipaddr in re.finditer(ip_pattern, str(output)):
            ip = pattern.search(ipaddr.group())
            if ip.group() != "127.0.0.1":
                iplist.append(ip.group())
        return iplist
    except Exception, e:
        return [str(e)]


def mylog(*argl, **argd):
    fcntl.flock(_logf, fcntl.LOCK_EX)
    try:
        ct = datetime.now().strftime('%m-%d %H:%M:%S.%f ')
        print ct,
        _logf.write(ct)
        for l in argl:
            print l, ' ',
            _logf.write(str(l))
        for k, v in argd.items():
            print k, '=', v,
            _logf.write(str(k))
            _logf.write('=')
            _logf.write(str(v))
        print ''
        _logf.write('\n')
        _logf.flush()
    finally:
        fcntl.flock(_logf, fcntl.LOCK_UN)


def writeFile(fpath, fname, content):
    if isinstance(content, (list, tuple, dict, set)):
        content = json.dumps(content, sort_keys=True, indent=4, separators=(', ', ' : '))
    if(fpath != None and len(fpath) > 0):
        fullpath = fpath + os.path.sep + fname
    else:
        fullpath = fname
    rfile = None
    try:
        rfile = open(fullpath, 'w')
        rfile.write(content)
        rfile.close()
    finally:
        try:
            rfile.close()
        except:
            pass


def sendMail():
    import smtplib
    from email.MIMEText import MIMEText
    from email.Utils import formatdate
    from email.Header import Header

    def sendOut(toMail, subject, content):
        smtpHost = 'smtp.mxhichina.com'
        sslPort = '465'
        fromMail = 'monitor@tuyoogame.com'
        username = 'monitor@tuyoogame.com'
        password = 'jiankong!@#20140617'
        encoding = 'utf-8'
        mail = MIMEText(content.encode(encoding), 'plain', encoding)
        mail['Subject'] = Header(subject, encoding)
        mail['From'] = fromMail
        mail['To'] = toMail
        mail['Date'] = formatdate()
        try:
            smtp = smtplib.SMTP_SSL(smtpHost, sslPort)
            smtp.ehlo()
            smtp.login(username, password)
            smtp.sendmail(fromMail, toMail, mail.as_string())
            smtp.close()
        except Exception:
            raise

    iplist = json.dumps(getLocalIps())
    nowtime = str(datetime.now())
    if sys.argv[2] == 'crash':
        toAdd = 'pypro_monitor@tuyoogame.com'
        subject = '服务进程CRASH'
        message = ' '.join(sys.argv[3:])
        content = message + "\n" + nowtime + "\nSEND MAIL FROM " + iplist
    else:
        toAdd = sys.argv[2]
        subject = sys.argv[3]
        message = sys.argv[4]
        content = message + "\n" + nowtime + "\nSEND MAIL FROM " + iplist

    toAdds = toAdd.split(';')
    for toadd in toAdds:
        toadd = toadd.strip()
        if len(toadd) > 0:
            sendOut(toadd, subject, content)


def find_sub_files(fpath):
    ffiles = set()
    fpath = os.path.abspath(fpath)
    for p, _, filenames in os.walk(fpath):
        for filename in filenames:
            filename = os.path.join(p, filename)
            filename = os.path.abspath(filename)
            ffiles.add(filename)
    return ffiles


def tar_xvf(tarfilepath, out_dir, sub_dir, rmLeft):
    import tarfile
    tar = tarfile.open(tarfilepath)
    mylog('tar_xvf->', tarfilepath, out_dir)
    names = tar.getnames()
    newfiles = set()
    for name in names:
        newf = tar.extractfile(name)
        if newf:
            newdata = newf.read()
            newf.close()
            oldf = None
            olddata = None
            outfile = os.path.join(out_dir, name)
            outfile = os.path.abspath(outfile)
            try:
                oldf = open(outfile, 'r')
                olddata = oldf.read()
            except:
                try:
                    oldf.close()
                except:
                    pass
            newfiles.add(outfile)
            newfiles.add(outfile + 'c')
            mylog('tar_xvf->', olddata == newdata, outfile)
            if olddata != newdata:
                outf = open(outfile, 'w')
                outf.write(newdata)
                outf.close()
        else:
            print 'tar_xvf->', os.path.join(out_dir, name)
            tar.extract(name, path=out_dir)
    tar.close()
    if int(rmLeft) :
        subfiles = find_sub_files(os.path.join(out_dir, sub_dir))
        delfiles = list(subfiles - newfiles)
        delfiles.sort()
        mylog('tar_xvf del->', len(delfiles))
        for df in delfiles:
            commands.getoutput('rm -fr ' + df)
            mylog('tar_xvf del->', df)
    mylog('tar_xvf->', tarfilepath, out_dir, 'done.')


def statusProcess(procids):
    mylog('read all process status file !!')
    status = {}
    stfile = None
    stpath = ''
    try:
        for pid in procids:
            datas = {}
            stpath = log_path + '/status.' + pid
            if os.path.isfile(stpath):
                stfile = open(stpath, 'r')
                fcntl.flock(stfile, fcntl.LOCK_EX)
                try:
                    ds = json.load(stfile)
                    datas = {'pid': ds['pid'],
                             'status': ds['status']}
                except:
                    datas = {}
                fcntl.flock(stfile, fcntl.LOCK_UN)
                stfile.close()
            status[pid] = datas
    except Exception, e:
        raise e
    finally:
        try:
            if stfile:
                fcntl.flock(stfile, fcntl.LOCK_UN)
        except:
            pass
        try:
            if stfile:
                stfile.close()
        except:
            pass
    mylog('TY_THREAD_STATUS=' + json.dumps(status))
    return 1


def startProcess(procids):
    '''
    启动所有的while1进程
    '''
    mylog('reset all process status file !!')
    ct = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    for pid in procids:
        datas = {'creatTime': ct, 'serverId': pid}
        writeFile(log_path, 'status.' + pid, datas)

    mylog('all while1 start in !!')
    for pid in procids:
        _popen_process_while1(pid)
    mylog('all while1 start done !!')
    time.sleep(3)  # waiting for while1

    checktimes = 0
    runinfo = {}
    while checktimes < 10:
        checktimes += 1
        slowpids, runinfo = _get_process_info(procids)
        if not slowpids:
            break
        else:
            mylog('WAIT PROCESS INFO:', slowpids)
            time.sleep(10)

    for procid in runinfo:
        mylog('PROCESS INFO:', runinfo[procid])
    mylog('TY_THREAD_INFO=' + json.dumps(runinfo))
    return 1


def _popen_process_while1(pid):
    # TODO tasket's cpu ????
    #     mymachine = options.mymachine
    cpuindex = 0
#     if mymachine.get('taskset', 0) == 1:
#         syscpucount = 1
#         myservers = options.myservers
#         cpucount = psutil.cpu_count() - syscpucount  # 逻辑核数量, 刨除第一个核给系统调用
#         if cpucount > 0 :
#             i = myservers.index(pid)
#             cpuindex = (i % cpucount) + syscpucount

    redis_conf = redis_config.split(':')
    os.chmod(bin_path + '/while1.sh', 00777)
    cmdline = ['./while1.sh', pid, redis_conf[0], redis_conf[1],
               redis_conf[2], str(cpuindex), 'pypy']
    
    if pid.find('GT7') >= 0 and os.path.isfile('/bin/pypy24') :
        cmdline[-1] = '/bin/pypy24'

    # LINUX WIN32
    if platform.system() == 'Windows':
        raise Exception('WIN32 system start up not test !!')
    else:
        cmdline.insert(0, 'nohup')
        cmdline.append('&')

    mylog('cmd-->', bin_path, cmdline)
    cmdline = ' '.join(cmdline)
    _, slave = pty.openpty()
    psutil.Popen(cmdline, cwd=bin_path, stdin=subprocess.PIPE,
                 stdout=slave, stderr=slave, close_fds=True, shell=True)


def _get_process_info(pidlist):
    curuser = getpass.getuser()
    redis_conf = redis_config.split(':')
    rediskey = str(redis_conf[0]) + ' ' + str(redis_conf[1]) + ' ' + str(redis_conf[2])
    runinfo = {}
    for aid in pidlist:
        runinfo[aid] = {'pypy': {'pid': 0}, 'while1': {'pid': 0}}
    for p in psutil.process_iter():
        try:
            if p.username() == curuser:
                cmdline = p.cmdline()
            else:
                continue
        except:
            continue
        cmdline = ' '.join(cmdline)
        if cmdline.find(rediskey) > 0:
            procid = None
            for aid in pidlist:
                if cmdline.find(' ' + aid + ' ') > 0:
                    procid = aid
                    break
            if procid:
                if cmdline.find('while1') >= 0:
                    runinfo[procid]['while1']['pid'] = p.pid
                elif cmdline.find(' run.py ') >= 0:
                    runinfo[procid]['pypy']['pid'] = p.pid

    slowpids = []
    for procid in runinfo:
        rinfo = runinfo[procid]
        if rinfo['pypy']['pid'] == 0 or rinfo['while1']['pid'] == 0:
            slowpids.append(procid)
    return slowpids, runinfo


def stopProcess(procids):
    checktimes = 0
    runinfo = {}
    curuser = getpass.getuser()
    while checktimes < 10:
        checktimes += 1
        _, runinfo = _get_process_info(procids)
        if not runinfo:
            break
        else:
            pcount = 0
            for procid, info in runinfo.items():
                pid1 = info['while1']['pid']
                pid2 = info['pypy']['pid']
                mylog('KILL Process of :', procid, 'while1=', pid1, 'pypy=', pid2)
                try:
                    if pid1 > 0:
                        p = psutil.Process(pid1)
                        if p.username() == curuser:
                            pcount += 1
                            p.kill()
                    if pid2 > 0:
                        p = psutil.Process(pid2)
                        if p.username() == curuser:
                            pcount += 1
                            p.kill()
                except:
                    traceback.print_exc()
            if pcount == 0:
                break
            time.sleep(1)


def _get_process_pids():
    curuser = getpass.getuser()
    redis_conf = redis_config.split(':')
    rediskey = str(redis_conf[0]) + ' ' + str(redis_conf[1]) + ' ' + str(redis_conf[2])
    while1pids = []
    pypypids = []
    for p in psutil.process_iter():
        try:
            if p.username() == curuser:
                cmdline = p.cmdline()
                cmdline = ' '.join(cmdline)
            else:
                continue
        except:
            continue
        if cmdline.find(rediskey) > 0:
            if cmdline.find('while1.sh ') >= 0:
                while1pids.append(p.pid)
            elif cmdline.find(' run.py ') >= 0:
                pypypids.append(p.pid)
    return while1pids, pypypids


def stopProcessAll():
    checktimes = 0
    curuser = getpass.getuser()
    while checktimes < 10:
        checktimes += 1
        while1pids, pypypids = _get_process_pids()
        if not while1pids and not pypypids:
            break
        else:
            pcount = 0
            for pid1 in while1pids:
                mylog('KILL while1 Process of :', pid1)
                try:
                    p = psutil.Process(pid1)
                    if p.username() == curuser:
                        pcount += 1
                        p.kill()
                except:
                    traceback.print_exc()
            for pid1 in pypypids:
                mylog('KILL pypy Process of :', pid1)
                try:
                    p = psutil.Process(pid1)
                    if p.username() == curuser:
                        pcount += 1
                        p.kill()
                except:
                    traceback.print_exc()
            if pcount == 0:
                break
            time.sleep(1)


def main():
    mylog('remote.py bin_path=', bin_path)
    mylog('remote.py redis_config=', redis_config)
    mylog('remote.py args=', sys.argv)

    act = sys.argv[1]
    if act == 'sendmail':
        sendMail()

    elif act == 'xvf':
        tar_xvf(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

    elif act == 'start':
        procids = sys.argv[2:]
        stopProcess(procids)
        startProcess(procids)

    elif act == 'status':
        procids = sys.argv[2:]
        statusProcess(procids)

    elif act == 'stopall':
        stopProcessAll()

    elif act == 'rmlogs':
        commands.getoutput('rm -fr ' + log_path + '/*')

    mylog('TY_TASK_RESULT_INT=0')


if __name__ == '__main__':
    main()
    try:
        _logf.close()
    except:
        pass
