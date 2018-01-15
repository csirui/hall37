# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import json
import os
import time

from tyserver.tyutils import fsutils, strutil
from tyserver.tyutils.tyhttp import dohttpquery
from webmgr.action import actlog
from webmgr.action.loader import make_static_json
import commands


def action(options):
    '''
    装载并检测服务启动配置文件
    '''
    alldata = {}
    setattr(options, 'alldata', alldata)

    actlog.log('options.poker_path->', options.poker_path)
    checkprojects = options.checkprojects
    loadsprojs = set()
    datas, allGameIds = load_project_datas_all(options.poker_path + '/game/', options)
    alldata.update(datas)
    for cproj in checkprojects:
        projectdir = fsutils.appendPath(options.poker_path, cproj)
        loadsprojs.add(projectdir)
        datas = load_project_datas_room(projectdir, options)
        alldata.update(datas)
    allGameIds.sort()
    options.pokerdict['config.game.ids'] = allGameIds
    actlog.log('config.game.ids->', allGameIds)
    alldata['poker:map.activityid'] = readJsonData(options.poker_path + '/poker/map.activityid.json', options)
    alldata['poker:map.bieventid'] = readJsonData(options.poker_path + '/poker/map.bieventid.json', options)
    alldata['poker:map.giftid'] = readJsonData(options.poker_path + '/poker/map.giftid.json', options)

    # 重gdss获取数据
    ret = _syncDataFromGdss(options, 'poker:map.clientid', dict, 'getClientIdDict')
    if not ret:
        return ret

    ret = _syncDataFromGdss(options, 'poker:map.productid', dict, 'getProductIdDict')
    if not ret:
        return ret

    ret = make_static_json.make_static_json_file(options, alldata)
    if not ret:
        return ret

    outpath = options.pokerdict['output_path']
    fsutils.writeFile(outpath, 'out.redis.json', alldata)
    fsutils.writeFile(outpath, 'out.poker.global.json', options.pokerdict)
    fsutils.writeFile(options.poker_path, '._confdata_.json', alldata)

    patchpy = os.path.dirname(outpath) + '/patch_config.py'
    if os.path.isfile(patchpy):
        cmd = 'pypy ' + patchpy + ' ' + outpath
        actlog.log('执行游戏配置文件补丁:', cmd)
        status, output = commands.getstatusoutput(cmd)
        for l in output.split('\n'):
            actlog.log(l)
        if status != 0:
            actlog.error('游戏配置文件补丁失败:', patchpy)
            actlog.error(status, output)
            return 0
        if output and output.find('REMAKE_STATIC') >= 0:
            actlog.log('find REMAKE_STATIC !')
            alldata = json.loads(filterComment(outpath + '/out.redis.json'))
            ret = make_static_json.make_static_json_file(options, alldata)
            if not ret:
                return ret
            fsutils.writeFile(outpath, 'out.redis.json', alldata)
            fsutils.writeFile(options.poker_path, '._confdata_.json', alldata)
    return 1


def readJsonData(jf, options):
    try:
        return strutil.replace_objevn_value(json.loads(filterComment(jf)), options.env)
    except Exception, e:
        actlog.error('config item file->', jf)
        raise e


def filterComment(f):
    res = ''
    fp = None
    try:
        fp = open(f, 'r')
        for l in fp:
            if l.strip().startswith("#"):
                print l
            else:
                res += l
        return res
    finally:
        try:
            fp.close()
        except:
            pass


def load_project_datas_all(gamedir, options):
    datas = {}
    gameIds = []
    for gds in os.listdir(gamedir):
        if gds[0] == '.':
            continue
        try:
            game_id = str(int(gds))
        except:
            continue
        gameIds.append(int(game_id))
        projectdir = gamedir + '/' + gds
        actlog.log('projectdir->', projectdir)
        for game_mod in os.listdir(projectdir):
            if game_mod == 'room' and game_mod[0] == '.':
                continue
            moddir = projectdir + '/' + game_mod
            actlog.log('moduledir->', moddir)
            for f in os.listdir(moddir):
                if f[0] == '.' or not f.endswith('.json'):
                    continue
                jf = moddir + '/' + f
                js = readJsonData(jf, options)
                fn = os.path.basename(f).split('.')[0]
                #                 actlog.log('file->', 'game:' + game_id + ':' + game_mod + ':' + fn, jf)
                datas['game:' + game_id + ':' + game_mod + ':' + fn] = js
    return datas, gameIds


def load_project_datas_room(projectdir, options):
    datas = {}
    game_id = os.path.basename(projectdir)
    game_mod = 'room'
    moddir = projectdir + '/' + game_mod
    actlog.log('roomdir->', moddir)
    if os.path.isdir(moddir):
        for f in os.listdir(moddir):
            if f[0] == '.' or not f.endswith('.json'):
                continue
            jf = moddir + '/' + f
            js = readJsonData(jf, options)
            fn = os.path.basename(f).split('.')[0]
            #             actlog.log('room->', 'game:' + game_id + ':' + game_mod + ':' + fn, jf)
            datas['game:' + game_id + ':' + game_mod + ':' + fn] = js
    return datas


def _syncDataFromGdss(options, confKey, dataType, apiName):
    # httpgdss = options.pokerdict.get('http_gdss')
    # if not httpgdss :
    #     httpgdss = 'http://gdss.touch4.me'
    # actlog.log('_syncDataFromGdss->', httpgdss, apiName, confKey)
    # ct = int(time.time())
    # sign = strutil.md5digest('gdss.touch4.me-api-' + str(ct) + '-gdss.touch4.me-api')
    # posturl = '%s/?act=api.%s&time=%d&sign=%s' % (httpgdss, apiName, ct, sign)
    # retstr = dohttpquery(posturl, {})
    # datas = None
    # try:
    #     datas = strutil.loads(retstr)
    # except:
    #     pass
    # if datas and isinstance(datas, dict):
    #     dictdata = datas.get('retmsg', None)
    #     if isinstance(dictdata, dataType) and len(dictdata) > 0 :
    #         options.alldata[confKey] = dictdata
    #         return 1
    #     else:
    #         actlog.error('_syncDataFromGdss, datas not found, datas=', datas)
    # else:
    #     actlog.error('_syncDataFromGdss, gdss return error, datas=', datas)
    # return 0
    return 1
