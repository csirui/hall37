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
    actlog.log('push static config file to all machines !')

    if os.environ.get('RUN_IN_DOCKER', 0):
        # 在开发docker模式下，webroot为link模式，无需拷贝
        actlog.log('docker mode skip this step !')
        return 1

    cpath = 'stc_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    bpath = options.env['backup_path']
    outpath = fsutils.appendPath(bpath, cpath)
    stpath = options.env['webroot_path'] + '/static_file'
    tarfile = tytar.tar_cvfz(outpath, stpath)
    actlog.log('static config file =', tarfile)
    ret = typush.push_tar_to_all_server(options, tarfile,
                                        fsutils.getParentDir(stpath),
                                        fsutils.getLastPathName(stpath),
                                        1)
    actlog.log('push static config file to all machines ! done !!')
    return ret
