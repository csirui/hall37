# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import commands
import os
import platform
import stat

from datetime import datetime

from tyserver.tyutils import fsutils, strutil
from webmgr.action import actlog


def action(options):
    """
    预编译所有的py文件到pyc，以便发现语法错误
    """
    if os.environ.get('RUN_IN_DOCKER', 0):
        # 在开发docker模式下，webroot为link模式，无需拷贝
        if not makeSoInDocker(options):
            return 0
        actlog.log('docker mode skip compiler pyc !')
        return 1

    # 编译SO文件
    bin_path = options.env['bin_path']
    # LINUX WIN32
    if platform.system() == 'Darwin':
        makesosh = [
            os.path.join('freetime', 'core', 'cffi', 'makeso.sh'),
            os.path.join('poker', 'util', 'cffi', 'makeso.sh'),
        ]
    elif platform.system() == 'Windows':
        _, makesosh = fsutils.findTreeFiles(bin_path, ['.*' + os.path.sep + '(makeso.cmd)$'], ['.*\\.svn.*'])
    else:
        _, makesosh = fsutils.findTreeFiles(bin_path, ['.*' + os.path.sep + '(makeso.sh)$'], ['.*\\.svn.*'])

    if len(makesosh) == 0:
        actlog.log('run C/C++ compiler   : not found !!')

    for msh in makesosh:
        cmd = bin_path + os.path.sep + msh
        os.chmod(cmd, stat.S_IRWXU | stat.S_IRWXG)
        actlog.log('run C/C++ compiler   :', msh)
        status, output = commands.getstatusoutput(cmd)
        if status != 0:
            actlog.log('C/C++ compiler ERROR !!', cmd)
            actlog.log(output)
            return 0

    # 只有再Linux运行环境下才进行预编译
    if platform.system() != 'Linux':
        return 1

    # 生成编译文件
    pkgs = []
    pyfiles = options._pyfiles
    for pyf in pyfiles:
        if pyf.endswith('.py') and pyf.find('hotfix') < 0:
            pkg = '    import ' + '.'.join(pyf.split(os.path.sep)[1:])
            pkg = pkg[0:-3]
            if pkg.endswith('__init__'):
                pkg = pkg[0:-9]
            pkgs.append(pkg)
    content = '''
# -*- coding: utf-8 -*-
# author time : %s
import sys
from twisted.internet import reactor # 确保reactor第一时间初始化, 否则可能莫名其妙的crash
if sys.getdefaultencoding().lower() != 'utf-8' :
    reload(sys)
    sys.setdefaultencoding("utf-8")
try:
%s
except:
    print sys.path
    raise
''' % (str(datetime.now()), '\n'.join(pkgs))
    cfilepath = bin_path + os.path.sep + '_compiler.py'
    fsutils.writeFile('', cfilepath, content)

    actlog.log('run PYPY  compiler   :', cfilepath)
    pypy = strutil.getEnv('PYPY', 'pypy')
    cmd = '%s -tt %s' % (pypy, cfilepath)
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
        actlog.log('ERROR !!', 'compile py files false !', status, cfilepath)

        lines = output.split('\n')
        for line in lines:
            actlog.log(line)
        return 0
    else:
        # fsutils.deleteFile(cfilepath)
        for pyf in pyfiles:
            if pyf.endswith('.py'):
                f = bin_path + os.path.sep + pyf + 'c'
                if fsutils.fileExists(f):
                    fsutils.deleteFile(f)

    return 1


def makeSoInDocker(options):
    found = 0
    for proj in options.projectlist:
        srcPath = fsutils.appendPath(proj['path'], 'src')
        actlog.log('makeSoInDocker', srcPath)
        if platform.system() == 'Windows':
            _, makesosh = fsutils.findTreeFiles(srcPath, ['.*' + os.path.sep + '(makeso.cmd)$'], ['.*\\.svn.*'])
        else:
            _, makesosh = fsutils.findTreeFiles(srcPath, ['.*' + os.path.sep + '(makeso.sh)$'], ['.*\\.svn.*'])
        if makesosh:
            for msh in makesosh:
                found = 1
                cmd = srcPath + os.path.sep + msh
                os.chmod(cmd, stat.S_IRWXU | stat.S_IRWXG)
                actlog.log('run C/C++ compiler   :', msh)
                status, output = commands.getstatusoutput(cmd)
                if status != 0:
                    actlog.log('C/C++ compiler ERROR !!', cmd)
                    actlog.log(output)
                    return 0
    if not found:
        actlog.log('run C/C++ compiler   : not so found !!')
    return 1
