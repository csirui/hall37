# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import json

from tyserver.tyutils import fsutils, strutil
from webmgr.action import actlog, actutils
from webmgr.action.actlog import FormatPrintInfo


def action(options):
    '''
    load and check the poker file
    '''
    myenv = {'poker_path' : options.poker_path}

    pokerdict = __load_poker_file(options)
    if not pokerdict :
        return 0
    __print_poker_info(options, pokerdict)
    setattr(options, 'pokerdict', pokerdict)

    # fix path of output
    outpath = pokerdict['output_path']
    pokerdict['bin_path'] = fsutils.appendPath(outpath , 'bin')
    pokerdict['webroot_path'] = fsutils.appendPath(outpath, 'webroot')
    pokerdict['backup_path'] = fsutils.appendPath(outpath, 'backup')

    for k, v in pokerdict.items() :
        if isinstance(v, (str, unicode, int, float, bool)) :
            myenv[str(k)] = v
        else:
            myenv[str(k)] = json.dumps(v)
    setattr(options, 'env', myenv)

    return 1


def __get_value(pokerdict, key, defaultVal):
    val = pokerdict.get(key, defaultVal)
    if isinstance(val, (str, unicode)) :
        val = strutil.replace_objevn_value(val, pokerdict)
        pokerdict[key] = val
    return val


def __load_poker_file(options):
    pokerfile = options.pokerfile
    actlog.log('LOAD POKER FILE      :', pokerfile)
    pokerdict = fsutils.readJsonFile(pokerfile, True)
    pokerdict['poker_path'] = options.poker_path

    if not isinstance(pokerdict, dict) :
        return actlog.error('POKER FILE : format error，must be a dict')

    gameId = pokerdict.get('id', None)
    if not isinstance(gameId, int) or gameId <= 0 or gameId >= 10000 :
        return actlog.error('POKER FILE : id value is wrong')

    gameName = pokerdict.get('name', None)
    if not isinstance(gameName, (str, unicode)) or len(gameName) <= 0 :
        return actlog.error('POKER FILE : name value is wrong')
    if gameName.find('-') >= 0 :
        return actlog.error('POKER FILE : name value is wrong, can not have "-" (reserved char)')

    corporation = pokerdict.get('corporation', 'tuyoo')
    if corporation not in ('tuyoo', 'momo') :
        return actlog.error('POKER FILE : corporation value wrong, choice: tuyoo or momo')
    pokerdict['corporation'] = corporation

    mode = pokerdict.get('mode', 0)
    if mode not in (1, 2, 3, 4) :
        return actlog.error('POKER FILE : mode value must be an integer, choice : 1(online) or 2(simulation) or 3(rich test) or 4(tiny test)')

    port_redis = pokerdict.get('port_redis', 0)
    if not actutils.check_port(port_redis, True) :
        return actlog.error('POKER FILE : port_redis, socket port number wrong ' + str(port_redis))
    pokerdict['port_redis'] = port_redis

    local_internet = pokerdict.get('local_internet', '')
    if not isinstance(local_internet, (str, unicode)) :
        return actlog.error('POKER FILE : local_internet value is wrong')
    pokerdict['local_internet'] = local_internet

    local_intranet = __get_value(pokerdict, 'local_intranet', None)
    if not isinstance(local_intranet, (str, unicode)) :
        return actlog.error('POKER FILE : local_intranet value is wrong')
    pokerdict['local_intranet'] = local_intranet

    port_http = int(__get_value(pokerdict, 'port_http', 0))
    if not actutils.check_port(port_http, True) :
        return actlog.error('POKER FILE : port_http, socket port number wrong ' + str(port_http))
    pokerdict['port_http'] = port_http

    projects_path = __get_value(pokerdict, 'projects_path', None)
    if not isinstance(projects_path, str) :
        return actlog.error('POKER FILE : projects_path wrong, must pointing to the projects path')
    projects_path = fsutils.makeAsbpath(projects_path, pokerfile)
    if not fsutils.dirExists(projects_path) :
        return actlog.error('POKER FILE : projects_path, the path not exists [' + projects_path + ']')
    pokerdict['projects_path'] = projects_path

    output_path = __get_value(pokerdict, 'output_path', None)
    if not isinstance(output_path, str) :
        return actlog.error('POKER FILE : output_path wrong, must pointing to the compile output path')
    output_path = fsutils.makeAsbpath(output_path, pokerfile)
    if not fsutils.dirExists(output_path) :
        return actlog.error('POKER FILE : output_path wrong, the path not exists [' + output_path + ']')
    pokerdict['output_path'] = output_path

    http = __get_value(pokerdict, 'http_sdk', '')
    if not actutils.check_http_url(http, 'POKER FILE : http_sdk') :
        return 0
    pokerdict['http_sdk'] = http

    http = __get_value(pokerdict, 'http_sdk_inner', None)
    if http != None and not actutils.check_http_url(http, 'POKER FILE : http_sdk_inner') :
        return 0
    pokerdict['http_sdk_inner'] = http

    http = __get_value(pokerdict, 'http_game', None)
    if http != None and not actutils.check_http_url(http, 'POKER FILE : http_game') :
        return 0
    pokerdict['http_game'] = http

    http = __get_value(pokerdict, 'http_download', None)
    if http != None and not actutils.check_http_url(http, 'POKER FILE : http_download') :
        return 0
    pokerdict['http_download'] = http
    
    http = __get_value(pokerdict, 'http_gdss', None)
    if http != None and not actutils.check_http_url(http, 'POKER FILE : http_gdss') :
        return 0
    pokerdict['http_gdss'] = http

    config_redis = __get_value(pokerdict, 'config_redis', None)
    if not isinstance(config_redis, str) :
        return actlog.error('POKER FILE : config_redis wrong, must pointing to the configure redis <ip>:<port>:<dbid>')
    confdb = config_redis.split(':')
    if len(confdb) != 3 :
        return actlog.error('POKER FILE : config_redis wrong, must pointing to the configure redis <ip>:<port>:<dbid>')
    pokerdict['config_redis'] = config_redis

    return pokerdict


def __print_poker_info(options, pokerdict):
    fp = FormatPrintInfo('POKER', pokerdict, 14)
    keys = ['id', 'name', 'corporation', 'mode',
            'config_redis', 'game_packages', 'poker_path',
            'projects_path', 'output_path', 'port_http',
            'port_redis', 'http_sdk', 'http_sdk_inner',
            'http_game', 'http_download', 'http_avatar',
            'local_internet', 'local_intranet', 'http_gdss']
    for key in keys :
        fp.push_line(key)

#     for k in pokerdict.keys() :
#         if not k in keys :
#             fp.push_line(k)

    fp.printout()

