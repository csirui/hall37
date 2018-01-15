# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from datetime import datetime

from tyserver.tyutils import fsutils, tytar
from webmgr.action import actlog
from webmgr.action.remote.utils import typush
import os


def action(options):
    actlog.log('push bin file to all machines !')

    if os.environ.get('RUN_IN_DOCKER', 0):
        # 在开发docker模式下，webroot为link模式，无需拷贝
        actlog.log('docker mode skip this step !')
        return 1

    if options.pokerdict['mode'] in (3, 4):
        actlog.log('Testing Mode, skip this step.')
        return 1
    cpath = 'bin_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    bpath = options.env['backup_path']
    outpath = fsutils.appendPath(bpath, cpath)
    bin_path = options.env['bin_path']
    tarfile = tytar.tar_cvfz(outpath, options.env['bin_path'])
    actlog.log('bin file =', tarfile)
    ret = typush.push_tar_to_all_server(options, tarfile,
                                        fsutils.getParentDir(bin_path),
                                        fsutils.getLastPathName(bin_path),
                                        1)
    actlog.log('push bin file to all machines ! done !!')
    return ret
