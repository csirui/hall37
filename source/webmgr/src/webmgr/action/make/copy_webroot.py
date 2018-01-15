# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import os

from tyserver.tyutils import fsutils
from webmgr.action import actlog


def action(options):
    '''
    拷贝源代码工程的webroot到编译输出目录，按照配置文件的工程列表进行顺序覆盖拷贝
    '''
    actlog.log('copy webroot to bin/webroot')

    if os.environ.get('RUN_IN_DOCKER', 0) :
        # 在开发docker模式下，webroot为link模式，无需拷贝
        actlog.log('docker mode skip this step !')
        return 1

    allpaths = [
                options.env['webroot_path'],
                options.env['backup_path'],
    ]
    for mp in allpaths:
        fsutils.makePath(mp, False)

    paths = []
    for proj in options.projectlist :
        src = fsutils.appendPath(proj['path'], 'webroot')
        if fsutils.dirExists(src) :
            paths.append({'path':src, 'include' : [], 'exclude' : [".*\\.svn\\.*", ".*pyc"]})

    if options.pokerdict['mode'] in (1, 2):
        fsutils.copyTree(paths, options.env['webroot_path'], logfun=actlog.log)
        return 1

    # MODE 3, 4: 只链接, 并且只链接 tygame-webroot/webroot
    dstpath = options.env['webroot_path']
    for pathconf in paths:
        if 'tygame-webroot' in pathconf['path']:
            srcpath = pathconf['path']
            if os.path.islink(dstpath):
                if os.readlink(dstpath) == srcpath:  # 已经链接好了
                    actlog.log('already linked.', dstpath, '->', srcpath)
                    return 1
            fsutils.deletePath(dstpath)
            os.symlink(srcpath, dstpath)
            actlog.log('symlink created.', dstpath, '->', srcpath)
            return 1
    else:
        fsutils.copyTree(paths, options.env['webroot_path'], logfun=actlog.log)
    return 1

