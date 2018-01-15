# -*- coding: utf-8 -*-
"""
Created on 2015-5-12
@author: zqh
"""
import os

from freetime.style import ide_debug
from tyserver.tyutils import fsutils
from webmgr.action import actlog


def action(options):
    """
    拷贝源代码工程的etc、src、src-robot、webroot到编译输出目录，按照配置文件的工程列表进行顺序覆盖拷贝
    """
    # 创建所有的路径
    allpaths = [
        options.env['log_path'],
        options.env['webroot_path'],
        options.env['backup_path'],
    ]
    for mp in allpaths:
        fsutils.makePath(mp, False)
    allpaths = [
        options.env['bin_path']
    ]
    for mp in allpaths:
        fsutils.makePath(mp, True)

    if os.environ.get('RUN_IN_DOCKER', 0):
        # 在开发docker模式下，webroot为link模式，无需拷贝
        copySourceInDocker(options)
        actlog.log('docker mode use original project src path !')
        return 1

    paths = []
    for proj in options.projectlist:
        src = fsutils.appendPath(proj['path'], 'src')
        if fsutils.dirExists(src):
            paths.append({'path': src, 'include': [], 'exclude': [".*\\.svn\\.*", ".*pyc"]})
        else:  # freetime project
            paths.append({'path': proj['path'],
                          "include": ["^/freetime/.*"],
                          "exclude": [".*\\.svn\\.*",
                                      ".*pyc",
                                      ".*\\logserver\\.*",
                                      ".*\\cold-data-server\\.*"]})

    if ide_debug():
        _, copy_files = fsutils.linkTree(paths, options.env['bin_path'], logfun=actlog.log)
    else:
        _, copy_files = fsutils.copyTree(paths, options.env['bin_path'], logfun=actlog.log)
    setattr(options, '_pyfiles', copy_files)

    return 1


def copySourceInDocker(options):
    for proj in options.projectlist:
        runpy = fsutils.appendPath(proj['path'], 'src/run.py')
        if fsutils.fileExists(runpy):
            fsutils.copyFile(runpy, options.env['bin_path'] + '/run.py')
