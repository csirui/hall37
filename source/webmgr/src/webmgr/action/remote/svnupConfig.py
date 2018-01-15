# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import commands

from webmgr.action import actlog
from tyserver.tyutils import fsutils


def action(options, params={}):
    '''
    '''
    svnuser = params.get('svnuser', None)
    svnpwd = params.get('svnpwd', None)
    svnau = ''
    if svnuser and svnpwd :
        svnau = ' --username ' + str(svnuser) + ' --password ' + str(svnpwd) + ' --no-auth-cache '

    configPath = options.pokerdict['poker_path']
    configPath += '/game' 
    actlog.log('configPath:', configPath)
    
    cmd = ['cd ' + configPath]
    cmd.append('export LANG=en_US.UTF-8')
    cmd.append('echo "================================"')
    cmd.append('svn up --non-interactive ' + svnau + ' ./*')
    cmd.append('echo "================================"')
#     cmd.append('svn info ./*')
#     cmd.append('echo "================================"')
    cmd = ';'.join(cmd)
#     actlog.log('cmd line->', cmd)

    shname = '/home/tyhall/hall37/source/config_online/104/roomall.sh'
    if fsutils.fileExists(shname) :
        commands.getstatusoutput(shname)

    status, output = commands.getstatusoutput(cmd)
    actlog.log('cmd return->', status)
    actlog.log('cmd output->')
    lines = output.split('\n')
    for l in lines :
        actlog.log(l)
    actlog.log('done')

    return 1

