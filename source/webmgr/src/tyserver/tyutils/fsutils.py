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

from tyserver.tyutils import strutil

__cur_machine_ip_list = None


def makeDirs(checkdir):
    if os.path.exists(checkdir) == False:
        os.makedirs(checkdir)


def makePath(mpath, clear=False):
    if not os.path.isdir(mpath):
        os.makedirs(mpath)
    else:
        if clear:
            shutil.rmtree(mpath)
            os.makedirs(mpath)


def deletePath(mpath):
    if os.path.exists(mpath):
        shutil.rmtree(mpath)


def cleanPath(mpath):
    if os.path.exists(mpath):
        subs = os.listdir(mpath)
        for sub in subs:
            sf = appendPath(mpath, sub)
            if os.path.islink(sf):
                os.remove(sf)
            elif fileExists(sf):
                deleteFile(sf)
            elif dirExists(sf):
                deletePath(sf)


def normpath(apath):
    return os.path.normpath(apath)


def abspath(apath):
    return os.path.abspath(apath)


def appendPath(parent, *path):
    return os.path.join(parent, *path)


def getParentDir(apath, level=1):
    for _ in xrange(level):
        apath = os.path.dirname(apath)
    return os.path.abspath(apath)


def getLastPathName(apath):
    return os.path.basename(apath)


def makeAsbpath(mpath, relpath=None):
    if os.path.isabs(mpath):
        return os.path.abspath(mpath)
    if relpath == None:
        relpath = os.getcwd()
    if os.path.isfile(relpath):
        relpath = os.path.dirname(relpath)
    mpath = os.path.abspath(relpath + os.path.sep + mpath)
    return mpath


def fileExists(afile):
    return os.path.isfile(afile)


def dirExists(afile):
    return os.path.isdir(afile)


def writeFile(fpath, fname, content):
    if isinstance(content, (list, tuple, dict, set)):
        content = json.dumps(content, sort_keys=True, indent=4, separators=(', ', ' : '))
    if (fpath != None and len(fpath) > 0):
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


def readFile(fpath):
    f = None
    try:
        if os.path.isfile(fpath):
            f = open(fpath, 'rb')
            c = f.read()
            f.close()
            return c
    finally:
        try:
            f.close()
        except:
            pass
    return None


def readJsonFile(fpath, needdecode=False):
    fp = None
    try:
        fp = open(fpath, 'r')
        datas = json.load(fp)
        if needdecode:
            datas = strutil.decodeObjUtf8(datas)
        fp.close()
        return datas
    finally:
        try:
            fp.close()
        except:
            pass


def readJsoFileParseEnv(env, fpath, needdecode=False, _logger=None):
    fp = None
    try:
        fp = open(fpath, 'r')
        jstr = fp.read()
        fp.close()
        datas = json.loads(jstr)
        if needdecode:
            datas = strutil.decodeObjUtf8(datas)
        datas = strutil.replace_objevn_value(datas, env)
        return datas
    finally:
        try:
            fp.close()
        except:
            pass


def copyFile(fromFile, toFile):
    shutil.copyfile(fromFile, toFile)


def deleteFile(fromFile):
    os.remove(fromFile)


def findTreeFiles(fpath, include, exclude):
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


def linkTree(pathlist, outpath, cuthead=0, logfun=None):
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

    copyfiles = []
    for projpath, fs in ffiles.items():
        for f in set(map(lambda x: x.split(os.sep)[1], fs)):
            os.symlink(os.path.realpath(os.path.join(projpath, f)),
                       os.path.join(outpath, f))
        for f in fs:
            if cuthead > 0:
                f = os.path.sep + os.path.sep.join(f.split(os.path.sep)[cuthead:])
            copyfiles.append(f)
    return outpath, copyfiles


def copyTree(pathlist, outpath, cuthead=0, logfun=None):
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
        # if logfun :
        #             logfun('copyTree, mkdir: %s\n' % (outpath + f))
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
            #             if logfun :
            #                 logfun('copytree file : %s -> %s\n' % (src, dst))
            shutil.copyfile(src, dst)
    if logfun:
        logfun('copyTree copy %d folders, %d files -> %s' % (len(folders), fcount, outpath))
    return outpath, copyfiles


###############################################################################
# UTIL for local machine action
###############################################################################


def checkMachinePort(host, port=22, timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close();
    except:
        return False
    return True


def getLocalMachineIp():
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
    results = socket.getaddrinfo(host, None)
    return results[0][4][0]


def isLocalMachine(host):
    ip = getHostIp(host)
    if ip == "127.0.0.1":
        return True
    ips = getLocalMachineIp()
    if ip in ips:
        return True
    return False
