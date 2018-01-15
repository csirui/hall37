# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import os

from tyserver.tyutils import fsutils, strutil
from webmgr.action import actlog
from webmgr.action.loader.modes import auto_process
from webmgr.action.loader.modes import modefactory


def action(options):
    '''
    装载并检测服务启动配置文件
    '''
    projectlist, game_packages, gameids = __load_project_file(options)
    if not projectlist:
        return 0
    setattr(options, 'projectlist', projectlist)
    options.pokerdict['game_packages'] = game_packages

    otherconf = os.listdir(fsutils.appendPath(options.poker_path, 'game'))
    conf_projects = []
    for oc in otherconf:
        try:
            gid = int(oc)
            if gid in gameids:
                conf_projects.append('game/' + str(gid))
        except:
            pass
    if 'game/9998' not in conf_projects:
        conf_projects.append('game/9998')
    options.pokerdict['conf.projects'] = conf_projects
    #     actlog.log('projectlist=', projectlist)

    machinedict = __load_machine_file(options)
    if not machinedict:
        return 0
    setattr(options, 'machinedict', machinedict)

    myenv = options.env
    for mid, mdefs in machinedict.items():
        myenv[mid + '.internet'] = mdefs['internet']
        myenv[mid + '.intranet'] = mdefs['intranet']
    #     actlog.log('machinedict=', machinedict)

    globaldict = __load_global_file(options)
    if not globaldict:
        return 0
    setattr(options, 'globaldict', globaldict)
    #     actlog.log('globaldict=', globaldict)

    options.pokerdict['log_path'] = globaldict['log_path']
    myenv['log_path'] = globaldict['log_path']

    dbdict = __load_db_file(options)
    if not dbdict:
        return 0
    setattr(options, 'dbdict', dbdict)
    #     actlog.log('dbdict=', dbdict)

    myenv['db.mysql.all'] = dbdict['mysql'].keys()
    myenv['db.redis.all'] = dbdict['redis'].keys()

    serverlist = __load_server_file(options, machinedict, gameids)
    if not serverlist:
        return 0
    setattr(options, 'serverlist', serverlist)
    #     actlog.log('serverlist=', serverlist)

    cmddict = __load_cmd_file(options)
    if not cmddict:
        return 0
    setattr(options, 'cmddict', cmddict)
    #     actlog.log('cmddict=', cmddict)

    #     rooms = __load_rooms_file(options)
    #     if not rooms :
    #         return 0
    #     setattr(options, 'rooms', rooms)
    #     actlog.log('cmddict=', cmddict)

    datas = {}
    datas['env'] = options.env
    datas['pokerdict'] = options.pokerdict
    datas['projectlist'] = options.projectlist
    datas['machinedict'] = options.machinedict
    datas['globaldict'] = options.globaldict
    datas['dbdict'] = options.dbdict
    datas['serverlist'] = options.serverlist
    datas['cmddict'] = options.cmddict

    fsutils.writeFile(options.poker_path, '._service_.json', datas)
    fsutils.writeFile(options.poker_path, '._process_.json', datas['serverlist'])
    fsutils.writeFile(options.poker_path, '._confprojects_.json', conf_projects)

    outpath = options.pokerdict['output_path']
    fsutils.writeFile(outpath, 'out.datas.json', datas)
    fsutils.writeFile(outpath, 'out.db.json', datas['dbdict'])
    fsutils.writeFile(outpath, 'out.poker.global.json', datas['pokerdict'])
    fsutils.writeFile(outpath, 'out.freetime.global.json', datas['globaldict'])
    fsutils.writeFile(outpath, 'out.server.json', datas['serverlist'])

    if fsutils.fileExists(outpath + '/out.server.json.base'):
        s1 = fsutils.readFile(outpath + '/out.server.json.base')
        s2 = fsutils.readFile(outpath + '/out.server.json')
        if s1.strip() != s2.strip():
            raise Exception('the server.ison changed !! can not go !!')

    slist = []
    for k in datas['serverlist']:
        slist.append(str(k['type']) + str(k['id']) + ' ' + str(k['ip'] + ' ' + str(k.get('agent', ''))))
    slist.sort()
    slist = '\n'.join(slist)
    fsutils.writeFile(outpath, 'out.process.list', slist)

    return 1


def __load_json_file(options, jname, jtype):
    jsonfile = fsutils.appendPath(options.poker_path, jname)
    actlog.log('load %-15s :' % (jname), jsonfile)
    datadict = fsutils.readJsoFileParseEnv(options.env, jsonfile, True)
    if not isinstance(datadict, jtype):
        return actlog.error(jname + ' : format error, root object must be ' + str(jtype))
    return datadict


def __load_cmd_file(options):
    jname = 'poker/cmd.json'
    datadict = __load_json_file(options, jname, dict)

    if not datadict:
        return datadict

    return datadict


def __load_db_file(options):
    jname = 'freetime/db.json'
    datadict = __load_json_file(options, jname, dict)

    if not datadict:
        return datadict

    return datadict


def __load_global_file(options):
    jname = 'freetime/global.json'
    datadict = __load_json_file(options, jname, dict)

    if not datadict:
        return datadict

    return datadict


def __load_machine_file(options):
    jname = 'poker/machine.json'
    datadict = __load_json_file(options, jname, dict)

    if not datadict:
        return datadict

    ips = set()
    for mid, mdefs in datadict.items():
        actlog.log('check machine define :', mid)

        internet = mdefs.get('internet', None)
        intranet = mdefs.get('intranet', None)
        user = mdefs.get('user', None)
        pwd = mdefs.get('pwd', None)
        ssh = mdefs.get('ssh', None)

        if not isinstance(internet, str):
            return actlog.error('the machine internet format error ! [' + str(internet) + ']')
        if internet in ips:
            return actlog.error('the machine internet already exits ! [' + str(internet) + ']')
        ips.add(internet)

        if intranet == None:
            mdefs['intranet'] = internet
            intranet = internet
        if not isinstance(intranet, str):
            return actlog.error('the machine intranet format error ! [' + str(intranet) + ']')
        if intranet != internet:
            if intranet in ips:
                return actlog.error('the machine intranet already exits ! [' + str(intranet) + ']')
            ips.add(intranet)

        if user == None:
            mdefs['user'] = ''
            user = ''
        if not isinstance(user, str):
            return actlog.error('the machine user format error ! [' + str(user) + ']')

        if pwd == None:
            mdefs['pwd'] = ''
            pwd = ''
        if not isinstance(pwd, str):
            return actlog.error('the machine pwd format error ! [' + str(pwd) + ']')

        if ssh == None:
            mdefs['ssh'] = 22
            ssh = 22
        if not isinstance(ssh, int):
            return actlog.error('the machine ssh port format error ! [' + str(ssh) + ']')

        islocalhost = fsutils.isLocalMachine(intranet)
        if islocalhost:
            mdefs['localhost'] = 1
            mdefs['host'] = intranet
        else:
            if fsutils.checkMachinePort(intranet, ssh):
                mdefs['host'] = intranet
            else:
                if fsutils.checkMachinePort(internet, ssh):
                    mdefs['host'] = internet
                else:
                    return actlog.error('can not connect ssh port to machine ! [' + str(ssh) + ']')

    return datadict


def __load_project_file(options):
    jname = 'poker/project.json'
    datadict = __load_json_file(options, jname, list)

    if not datadict:
        return datadict

    game_packages = []
    gameids = []

    for proj in datadict:
        ppath = proj.get('path', None)
        if not isinstance(ppath, str):
            return actlog.error('the project path is not defined !', proj)
        if not fsutils.dirExists(ppath):
            return actlog.error('the project path not found !', ppath)

        srcpath = fsutils.appendPath(ppath, 'src')
        if fsutils.dirExists(srcpath):
            subdirs = os.listdir(srcpath)
            for subdir in subdirs:
                gamepy = fsutils.appendPath(srcpath, subdir, 'game.py')
                if fsutils.fileExists(gamepy):
                    if subdir in game_packages:
                        return actlog.error('the project package is double defined !', gamepy, 'proj=', proj)
                    game_packages.append(subdir)
                    proj['package'] = subdir
                    gameid = proj.get('gameId', 0)
                    if gameid > 0:
                        gameids.append(int(gameid))
                    actlog.log('find gam project-> GAMEID=', gameid, 'PACKAGE=', subdir)
    return datadict, game_packages, gameids


def __load_server_file(options, machinedict, gameids):
    mode = options.env['mode']
    processlist, machinedict = modefactory[mode].make_process_list(options, machinedict, gameids)
    if not processlist:
        return processlist

    allrooms = {}
    # 装载房间的配置，用于获取房间进程ID和数量
    for gameId in gameids:
        jname = 'game/' + str(gameId) + '/room/0.json'
        jsonfile = fsutils.appendPath(options.poker_path, jname)
        if fsutils.fileExists(jsonfile):
            actlog.log('load %-15s :' % (jname), jsonfile)
            rooms = fsutils.readJsonFile(jsonfile, True)
            if not isinstance(rooms, dict):
                return actlog.error(jname + ' : format error, root object must be dict')
            for rid in rooms:
                if rid in allrooms:
                    return actlog.error(jname + ' : the roomId already defined !! ' + str(rid))
                allrooms[rid] = rooms[rid]

    serverlist = auto_process.auto_group_process(machinedict, processlist, allrooms, mode)

    serverlist = strutil.replace_objevn_value(serverlist, options.env)

    checks = strutil.cloneData(serverlist)
    for _, m in options.machinedict.items():
        internet = m['internet']
        intranet = m['intranet']
        for x in xrange(len(checks) - 1, -1, -1):
            p = checks[x]
            if p['ip'] == internet or p['ip'] == intranet:
                del checks[x]

    if len(checks) > 0:
        for p in checks:
            actlog.error('can not find machine define of server ip :', p['ip'])
        return 0
    return serverlist
