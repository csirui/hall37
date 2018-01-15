# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from datetime import datetime

from tyserver.tyutils import fsutils, tytar
from webmgr.action.remote.utils import typush
from webmgr.action import actlog
import os


def action(options):
    actlog.log('push webroot file to all machines !')

    if os.environ.get('RUN_IN_DOCKER', 0):
        # 在开发docker模式下，webroot为link模式，无需拷贝
        actlog.log('docker mode skip this step !')
        return 1

    if options.pokerdict['mode'] in (3, 4):
        actlog.log('Testing Mode, skip this step.')
        return 1
    cpath = 'web_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    bpath = options.env['backup_path']
    outpath = fsutils.appendPath(bpath, cpath)
    webpath = options.env['webroot_path']
    tarfile = tytar.tar_cvfz(outpath, webpath)
    actlog.log('webroot file =', tarfile)
    ret = typush.push_tar_to_all_server(options, tarfile,
                                        fsutils.getParentDir(webpath),
                                        fsutils.getLastPathName(webpath),
                                        0)
    actlog.log('push webroot file to all machines ! done !!')
    return ret
