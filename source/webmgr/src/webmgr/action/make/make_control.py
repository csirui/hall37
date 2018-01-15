# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from datetime import datetime
import os
import stat
from tyserver.tyutils import fsutils
from webmgr.action.make.resource import loadResource
from webmgr.action import actlog


def action(options):
    '''
    生成所有的进程启动脚本
    '''
    bin_path = options.env['bin_path']
    config_redis = options.pokerdict.get('local_config_redis', options.pokerdict['config_redis'])
    remotepy = loadResource('remote.py')
    remotepy = remotepy.replace('${TIME}', str(datetime.now()))
    remotepy = remotepy.replace('${BIN_PATH}', bin_path)
    remotepy = remotepy.replace('${LOG_PATH}', options.env['log_path'])
    remotepy = remotepy.replace('${REDIS_CONFIG}', config_redis)

    cfilepath = fsutils.appendPath(bin_path, 'remote.py')
    fsutils.writeFile('', cfilepath, remotepy)

    if options.pokerdict['mode'] <= 2 :
        sendmail = '1'
    else:
        sendmail = '0'

    while1sh = loadResource('while1.sh')
    while1sh = while1sh.replace('${SENDMAIL}', sendmail)
    while1sh = while1sh.replace('${BIN_PATH}', bin_path)
    while1sh = while1sh.replace('${LOG_PATH}', options.env['log_path'])

    if os.environ.get('RUN_IN_DOCKER', 0):
        # 在开发docker模式下，设置PYTHONPATH环境变量
        paths = []
        for proj in options.projectlist:
            src = fsutils.appendPath(proj['path'], 'src')
            if fsutils.dirExists(src):
                paths.append(src)
            else:
                src = fsutils.appendPath(proj['path'], 'freetime')
                if fsutils.dirExists(src):
                    paths.append(proj['path'])
        paths.reverse()
        paths = ':'.join(paths)
        while1sh = while1sh.replace('${DOCKER_PROJECT_PATH}', paths)
        actlog.log('makeControlInDocker PYTHONPATH=', paths)

    shfile = fsutils.appendPath(bin_path, 'while1.sh')
    fsutils.writeFile('', shfile, while1sh)
    os.chmod(shfile, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    return 1

