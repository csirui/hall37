# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import json
import os
import zipfile

from tyserver.tyutils import fsutils, strutil
from webmgr.action import actlog
from zipfile import ZipInfo
import commands


def make_static_json_file(options, alldata):
    confs = {}
    _load_decorations(options, confs, alldata)
    _load_activity(options, confs, alldata)
    _load_gamelist2(options, confs, alldata)
    webroot = options.env['webroot_path'] + '/static_file/'
    staticjson = webroot + 'static.json'
    if not fsutils.dirExists(webroot) :
        fsutils.makeDirs(webroot)
    fsutils.writeFile('', staticjson, confs)
    _remake_static_zip(options, confs, alldata)
    return 1


def _merageDatas(datas, subdata):
    subdata = strutil.cloneData(subdata)
    for k, d in subdata.items() :
        if not k in datas :
            datas[k] = d
        else:
            if isinstance(d, dict):
                datas[k].update(d)
            elif isinstance(d, list):
                datas[k].extend(d)
            else:
                datas[k] = d
    return datas


def _load_decorations(options, confs, alldata):
    if 'game:9999:decorations:0' in alldata :
        datas = alldata.get('game:9999:decorations:0', {})
    else:
        datas = {}
        gids = options.pokerdict['config.game.ids']
        for gid in gids :
            subdata = alldata.get('game:' + str(gid) + ':decorations:tc', {})
            _merageDatas(datas, subdata)

    confs['decorations'] = datas.get('decorations', None)


def _load_activity(options, confs, alldata):
    if 'game:9999:activity:0' in alldata :
        datas = alldata.get('game:9999:activity:0', {})
    else:
        datas = {}
        gids = options.pokerdict['config.game.ids']
        for gid in gids :
            subdata = alldata.get('game:' + str(gid) + ':activity:tc', {})
            _merageDatas(datas, subdata)
            
    confs['activities'] = {'activities' : datas.get('activities', None),
                  'modules' : datas.get('modules', None)}


def _load_gamelist2(options, confs, alldata):
    if 'game:9999:gamelist2:0' in alldata :
        datas = alldata.get('game:9999:gamelist2:0', {})
    else:
        datas = {}
        gids = options.pokerdict['config.game.ids']
        for gid in gids :
            subdata = alldata.get('game:' + str(gid) + ':gamelist2:tc', {})
            _merageDatas(datas, subdata)

    confs['games'] = datas.get('games', None)


def _remake_static_zip(options, jdatas, alldata):
    webroot = options.env['webroot_path']
    zfiletmp = webroot + '/static_file/static.zip'
    zipf = zipfile.ZipFile(zfiletmp, mode="w", compression=zipfile.ZIP_DEFLATED)
    zinfo = ZipInfo(filename='static.json', date_time=(2015, 12, 16, 0, 0, 0))
    jdatas = json.dumps(jdatas, sort_keys=True, indent=4, separators=(', ', ' : '))
    zipf.writestr(zinfo, jdatas, zipfile.ZIP_DEFLATED)
    zipf.close()
    
    zdata = fsutils.readFile(zfiletmp)
    md5s = strutil.md5digest(zdata)
    zfile = webroot + '/static_file/' + md5s + '.zip'
    os.rename(zfiletmp, zfile)

    conf = alldata.get('game:9999:upgrade_client_static:0', None)
    if conf != None :
        conf['static_file_md5'] = md5s
        ulist = conf['static_file_url']
        if options.pokerdict.get('mode') != 1 :
            http_game = options.pokerdict['http_game']
            myurl = http_game + '/static_file'
            if myurl not in ulist :
                if options.pokerdict['mode'] > 1 :
                    ulist.insert(0, myurl)
                else:
                    ulist.append(myurl)
            actlog.log('THE STATIC JSON CHANGED !! ', myurl + '/' + md5s + '.zip')

    actlog.log('THE STATIC JSON CHANGED !! ', zfile)

    setattr(options, 'push_static', 0)
    if fsutils.fileExists('./cdn/copy_static_file.sh') :
        setattr(options, 'push_static', 1)
        actlog.log('UPLOAD ZIP TO CDN !!')
        st, out = commands.getstatusoutput('./cdn/copy_static_file.sh')
        if st != 0 :
            actlog.log('UPLOAD ZIP TO CDN ERROR !!')
            actlog.log(out)
            return 0
        else:
            actlog.log('UPLOAD ZIP TO CDN OK !!', out)
    else:
        actlog.log('UPLOAD ZIP TO CDN THE SHELL NOT FOUND !')
    return 1


