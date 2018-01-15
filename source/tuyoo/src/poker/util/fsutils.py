# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import json
import os
import platform
import re
import shutil
import socket
import subprocess

from poker.util import strutil

__cur_machine_ip_list = None


def makeDirs(mpath, clear=False):
    '''
    创建一个物理路径, 若相关联的上下级路径不存在,也会同时创建
    当clear为False时, 路径已经存在, 则不进行任何操作
    当clear为True时, 若路径已经存在, 那么清空改路径下的所有内容
    '''
    if not os.path.isdir(mpath):
        os.makedirs(mpath)
    else:
        if clear:
            shutil.rmtree(mpath)
            os.makedirs(mpath)


def deletePath(mpath):
    '''
    强制删除一个物理路径
    '''
    if os.path.exists(mpath):
        shutil.rmtree(mpath)


def normpath(apath):
    '''
    驳接os.path.normpath方法
    '''
    return os.path.normpath(apath)


def abspath(apath):
    '''
    驳接os.path.abspath方法
    '''
    return os.path.abspath(apath)


def appendPath(parent, *path):
    '''
    驳接os.path.join方法
    '''
    return os.path.join(parent, *path)


def getParentDir(apath, level=1):
    '''
    取得apath向上跳level级的目录
    '''
    for _ in xrange(level):
        apath = os.path.dirname(apath)
    return os.path.abspath(apath)


def getLastPathName(apath):
    '''
    驳接os.path.basename方法, 取得路径的最后一个名称
    '''
    return os.path.basename(apath)


def makeAsbpath(mpath, relpath=None):
    '''
    获得mpath的绝对路径
    若relpath为None,那么获得当前(PWD)的绝对路径
    否则以relpath为基础,取得绝对路径
    '''
    if os.path.isabs(mpath):
        return os.path.abspath(mpath)
    if relpath == None:
        relpath = os.getcwd()
    if os.path.isfile(relpath):
        relpath = os.path.dirname(relpath)
    mpath = os.path.abspath(relpath + os.path.sep + mpath)
    return mpath


def fileExists(afile):
    '''
    驳接os.path.isfile方法
    '''
    return os.path.isfile(afile)


def dirExists(afile):
    '''
    驳接os.path.isdir方法
    '''
    return os.path.isdir(afile)


def writeFile(fpath, fname, content):
    '''
    将内容content写入到 fpath/fname中
    若content为list, tuple, dict, set则进行JSON的序列化后在写入文件
    '''
    if isinstance(content, (list, tuple, dict, set)):
        content = json.dumps(content, sort_keys=True, indent=4, separators=(',', ':'))
    if (fpath != None and len(fpath) > 0):
        fullpath = fpath + os.path.sep + fname
    else:
        fullpath = fname
    rfile = open(fullpath, 'w')
    rfile.write(content)
    rfile.close()


def readFile(fpath):
    '''
    读取fpath指定文件的全部内容, 若文件不存在或出错,返回None
    '''
    try:
        if os.path.isfile(fpath):
            f = open(fpath, 'rb')
            c = f.read()
            f.close()
            return c
    except:
        pass
    return None


def readJsonFile(fpath, needdecodeutf8=False):
    '''
    读取fpath指定文件的JSON内容, 返回JSON对象
    若needdecodeutf8为真, 则进行UTF8的编码转换处理
    '''
    fp = open(fpath, 'r')
    datas = json.load(fp)
    if needdecodeutf8:
        datas = strutil.decodeObjUtf8(datas)
    fp.close()
    return datas


def copyFile(fromFile, toFile):
    '''
    拷贝文件fromFile -> toFile
    '''
    shutil.copyfile(fromFile, toFile)


def deleteFile(fromFile):
    '''
    删除一个文件
    '''
    os.remove(fromFile)


def findTreeFiles(fpath, include, exclude):
    '''
    查找一个路劲下的所有文件
    include为包含文件的正则表示列表
    exclude为剔除文件的正则表示列表
    先判定是否要剔除,再判定是否要包含
    注意: 判定是否剔除时,是以fpath为基础的文件路径
        例如: fpath下有 <fpath>/a/1.txt <fpath>/2/b.txt
        判定时的文件路径为: "/a/1.txt" "/2/b.txt"
    '''
    fpath = os.path.abspath(fpath)
    incs = []
    if include:
        for x in xrange(len(include)):
            incs.append(re.compile(include[x]))
    excs = []
    if exclude:
        for x in xrange(len(exclude)):
            excs.append(re.compile(exclude[x]))

    def is_excs(fn):
        for regx in excs:
            if regx.match(filename):
                return 1
        return 0

    def is_incs(fn):
        if not incs:
            return 1
        for regx in incs:
            if regx.match(filename):
                return 1
        return 0

    floders = set()
    ffiles = []
    cutlen = len(fpath)
    for p, _, filenames in os.walk(fpath):
        for filename in filenames:
            filename = p + os.path.sep + filename
            filename = filename[cutlen:]
            if is_excs(filename) == 0 and is_incs(filename) == 1:
                ffiles.append(filename)
                floders.add(os.path.dirname(filename))
    floders = list(floders)
    floders.sort()
    return floders, ffiles


def copyTree(pathlist, outpath, cuthead=0, logfun=None):
    '''
    拷贝文件目录树
    pathlist为一个list列表, 每个列表中为一个拷贝源的定义
        {'path' : '/test/', 'include' : [], 'exclude' : []}
            path为拷贝的源, 
            include为拷贝包含的文件的正则表达式列表
            exclude为拷贝剔除的文件的正则表达式列表
    若cuthead不为0, 那么再拷贝目标时, 将丢弃源文件的cuthead个父级目录
    若logfun为一个函数, 则拷贝时, 调用此函数进行拷贝进度的输出提示
    '''
    folders = set()
    ffiles = {}
    for proj in pathlist:
        projpath = proj['path']
        include = proj.get('include', [])
        exclude = proj.get('exclude', [])
        ds, fs = findTreeFiles(projpath, include, exclude)
        folders.update(ds)
        ffiles[projpath] = fs

    folders = list(folders)
    folders.sort()

    for f in folders:
        if cuthead > 0:
            f = os.path.sep + os.path.sep.join(f.split(os.path.sep)[cuthead:])
        if logfun:
            logfun('copyTree, mkdir: %s\n' % (outpath + f))
        makeDirs(outpath + f)

    copyfiles = []
    fcount = 0
    for projpath, fs in ffiles.items():
        for f in fs:
            fcount += 1
            src = projpath + f
            if cuthead > 0:
                f = os.path.sep + os.path.sep.join(f.split(os.path.sep)[cuthead:])
            copyfiles.append(f)
            dst = outpath + f
            if logfun:
                logfun('copytree file : %s -> %s\n' % (src, dst))
            shutil.copyfile(src, dst)
    if logfun:
        logfun('copyTree copy %d folders, %d files -> %s' % (len(folders), fcount, outpath))
    return outpath, copyfiles


def checkMachinePort(host, port=22, timeout=3):
    '''
    检查一个机器的某个端口是否可以连接
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close();
    except:
        return False
    return True


def getLocalMachineIp():
    '''
    取得当前机器的IP地址列表
    '''
    global __cur_machine_ip_list
    if __cur_machine_ip_list != None:
        return __cur_machine_ip_list

    # LINUX MAC WIN32
    curplatform = platform.system()
    ipstr = '([0-9]{1,3}\.){3}[0-9]{1,3}'
    if curplatform == "Darwin" or curplatform == "Linux":
        ipconfig_process = subprocess.Popen("ifconfig", stdout=subprocess.PIPE)
        output = ipconfig_process.stdout.read()
        ip_pattern = re.compile('(inet %s)' % ipstr)
        if curplatform == "Linux":
            ip_pattern = re.compile('(inet addr:%s)' % ipstr)
        pattern = re.compile(ipstr)
        iplist = []
        for ipaddr in re.finditer(ip_pattern, str(output)):
            ip = pattern.search(ipaddr.group())
            if ip.group() != "127.0.0.1":
                iplist.append(ip.group())
        __cur_machine_ip_list = iplist
    elif curplatform == "Windows":
        ipconfig_process = subprocess.Popen("ipconfig", stdout=subprocess.PIPE)
        output = ipconfig_process.stdout.read()
        ip_pattern = re.compile("IPv4.*: %s" % ipstr)
        pattern = re.compile(ipstr)
        iplist = []
        for ipaddr in re.finditer(ip_pattern, str(output)):
            ip = pattern.search(ipaddr.group())
            if ip.group() != "127.0.0.1":
                iplist.append(ip.group())
        __cur_machine_ip_list = iplist
    return __cur_machine_ip_list


def getHostIp(host):
    '''
    取得host对应的IP地址
    '''
    results = socket.getaddrinfo(host, None)
    return results[0][4][0]


def isLocalMachine(host):
    '''
    判定给出的host是否是当前代码运行的本机
    '''
    ip = getHostIp(host)
    ips = getLocalMachineIp()
    if ip in ips:
        return True
    return False
