# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import os

from tyserver.tycmds import runhttp
from tyserver.tycmds.runhttp import markHttpRequestEntry
from tyserver.tyutils import fsutils, strutil, tylog, tyhttp
from tyserver.tyutils.msg import MsgPack
from webmgr.action import actqueue, acthistory
from webmgr.action.debugs import redisdata
from webmgr.handler import getResourcePath
import json
from webmgr.action.remote import hotfix


class ActionHandler(object):
    
    
    def __init__(self, options):
        self.options = options


    @markHttpRequestEntry(jsonp=1)
    def do_http_info(self):
        mo = MsgPack()
        mo.setCmd('info')
        return mo
    
    @markHttpRequestEntry(jsonp=1)
    def do_http_model_list(self):
        mj = getResourcePath('menu.json')
        models = fsutils.readJsonFile(mj)
        # 读取game目录下的游戏目录
        otherConfPath = fsutils.appendPath(self.options.pokerpath, 'game')
        otherconf = os.listdir(otherConfPath)
        games = []
        for gid in otherconf :
            try:
                # 创建game-游戏配置目录。由于其它游戏的配置目录都是空, 就都跳过
                if int(gid) not in [8, 30, 39]:
                    continue

                gid = str(int(gid))
                children = []
                tylog.debug("do_http_model_list|get game mode|", gid=gid)
                self.getGameConfiger(int(gid), children)
                if children:
                    games.append({'text': 'game-' + gid, 'children': children})

                # # 创建该游戏下面的所有配置目录
                # gameConfigPath = fsutils.appendPath(otherConfPath, gid)
                # gameConfigs = os.listdir(gameConfigPath)
                # for gc in gameConfigs:
                #     if str(gc) != '.svn':
                #         children.append({'text': str(gc), 'attributes':{
                #                 "purl" : "model/config/game/" + gid + '/' + gc + '.html'
                #             }}
                #         )
            except:
                tylog.error("do_http_model_list|get game mode error|", gid=gid)
        models[0]['children'].extend(games)
        # models[0]['children'].append({'text': '查看模板关联', 'attributes':{
        #                         "purl" : "model/config/game/incidence.html"
        #                     }})
        
        # 动态测试工具
        debugs = []
        models.append({'text' : '调试工具',
                        'children'  : debugs})
        
        webroot = fsutils.appendPath(self.options.workpath, 'webroot', 'model', 'debug')
        hfs = os.listdir(webroot)
        for hf in hfs:
            if hf.endswith('.html'):
                hc = fsutils.readFile(webroot + '/' + hf)
                t = self._findTitle(hc)
                if t:
                    purl = "model/debug/" + hf
                    debugs.append({'text': t,
                                   'attributes': {
                                       "purl": purl
                                   }
                                   })
        debugs.sort(key=lambda x : x['text'])
        mo = MsgPack()
        mo.setCmd('model_list')
        mo.setResult('models', models)
        mo.setResult('pokerpath', self.options.pokerpath)
        mo.setResult('mgrpath', self.options.workpath)
        mo.setResult('localip', fsutils.getLocalMachineIp())
        mo.setResult('title', '.'.join(fsutils.getLocalMachineIp()[0].split('.')[2:]) + '管理器')
        return mo

    def makeChild(self, gameId, name, purl):
        return {
            'text': str(gameId) + '-' + name,
            'attributes': {
                "purl": purl
            }
        }

    def getGameConfiger(self, gameId, children):
        if gameId in (8, 30, 39):
            purl = "model/config/game/" + str(gameId) + '/' + 'room' + '.html'
            children.append(self.makeChild(gameId, 'room', purl))

        names = []
        if gameId == 8:
            names = ['red_envelope']

        for name in names:
            params = {
                "action": "show",
                "gameId": str(gameId),
                "name": name,
            }
            param_pairs = ["%s=%s" % (k, v) for k, v in params.items()]

            purl = "confighttp?" + '&'.join(param_pairs)
            children.append(self.makeChild(gameId, name, purl))

    def _findTitle(self, hc):
        i = hc.find('<title>')
        j = hc.find('</title>')
        if i > 0 and j > 0 :
            t = hc[i + 7 : j]
            return t
        return None
    
    
    def _check_param_jsonfile(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        return None, value


    def _check_param_jsondata(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        value = strutil.loads(value, ignoreException=True)
        if isinstance(value, (list, dict)) :
            return None, value
        return 'the json data error', None


    @markHttpRequestEntry(jsonp=1)
    def do_http_get_json_file(self, jsonfile):
        jfile = fsutils.appendPath(self.options.pokerpath, jsonfile)
        print "DEBUG", "self.options.pokerpath:", self.options.pokerpath, "jsonfile:", jsonfile, 'jfile:', jfile
        if fsutils.fileExists(jfile) :
            datas = fsutils.readJsonFile(jfile)
        else:
            if jsonfile in ('project.json', 'server.json') :
                datas = []
            # elif jsonfile in model.models:
            #     method = model.models[jsonfile].get('get')
            #     if method:
            #         datas = method()
            else:
                datas = {}
        mo = MsgPack()
        mo.setCmd('json_file_data')
        mo.setResult('jsonfile', jsonfile)
        mo.setResult('datas', datas)
        return mo  


    @markHttpRequestEntry(jsonp=1)
    def do_http_get_process_list(self):
        jfile = fsutils.appendPath(self.options.pokerpath, '._process_.json')
        if fsutils.fileExists(jfile) :
            datas = fsutils.readJsonFile(jfile)
        else:
            datas = []
        datas.sort(key=lambda x: x['type'] + x['id'])
        mo = MsgPack()
        mo.setCmd('process_list')
        mo.setResult('datas', datas)
        return mo


    @markHttpRequestEntry(jsonp=1)
    def do_http_set_json_file(self, jsonfile, jsondata):
        jfile = fsutils.appendPath(self.options.pokerpath, jsonfile)
        jsondata = json.dumps(jsondata, indent=2, separators=(', ', ' : '), sort_keys=True, ensure_ascii=False)
        lines = jsondata.split('\n')
        for x in xrange(len(lines)) :
            lines[x] = lines[x].rstrip()
        jsondata = '\n'.join(lines)

        fsutils.writeFile('', jfile, jsondata)
        datas = fsutils.readJsonFile(jfile)
        mo = MsgPack()
        mo.setCmd('json_file_data')
        mo.setResult('jsonfile', jsonfile)
        mo.setResult('datas', datas)
        return mo  
    

    def _check_param_action_user(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        return None, value


    def _check_param_action_name(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        if len(value) > 0 :
            return None, value
        if value in ('config_check', 'config_update'):
            return None, value
        return 'the action name error', None


    def _check_param_action_params(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        value = strutil.loads(value, ignoreException=True)
        if isinstance(value, (list, dict)) :
            return None, value
        return 'the action params error', None


    @markHttpRequestEntry(jsonp=1)
    def do_http_add_action(self, action_user, action_name, action_params):
        action = actqueue.add_action(action_name, action_params, action_user)
        tylog.info('do_http_add_action->', action)
        mo = MsgPack()
        mo.setCmd('add_action')
        mo.setResult('action', action)
        return mo  


    def _check_param_action_uuid(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        if isinstance(value, (str, unicode)) and len(value) > 0 :
            return None, value
        return 'the action_uuid error', None


    def _check_param_line_num(self, key, params, extend_tag):
        value = runhttp.getParamInt(key, 0)
        if isinstance(value, int) and value >= 0 :
            return None, value
        return 'the line_num error', None


    @markHttpRequestEntry(jsonp=1)
    def do_http_get_action_log(self, action_uuid, line_num):
        lines = acthistory.get_action_log(self.options, action_uuid, line_num)
        for x in xrange(len(lines)) :
            try:
                json.dumps([lines[x]])
            except:
                lines[x] = 'repr(' + repr(lines[x]) + ')'

        mo = MsgPack()
        mo.setCmd('action_log')
        mo.setResult('uuid', action_uuid)
        mo.setResult('lines', lines)
        return mo



    @markHttpRequestEntry(jsonp=1)
    def do_http_get_action_list(self):
        actions = acthistory.get_action_list(self.options)
        mo = MsgPack()
        mo.setCmd('action_list')
        mo.setResult('actions', actions)
        return mo

    def _check_param_action_uuids(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        value = strutil.loads(value, ignoreException=1)
        if isinstance(value, list) and len(value) >= 0 :
            return None, value
        return 'the action_uuids error', None


    @markHttpRequestEntry(jsonp=1)
    def do_http_remove_action(self, action_uuids):
        acthistory.remove_action(self.options, action_uuids)
        mo = MsgPack()
        mo.setCmd('remove_action')
        mo.setResult('ok', 1)
        return mo


    def _check_param_action(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        if isinstance(value, (str, unicode)) and len(value) >= 0 :
            return None, value
        return 'the action error', None


    @markHttpRequestEntry(jsonp=1)
    def do_http_debug_action(self, action):
        
        if action == 'redis_clear_all' :
            result = redisdata.redis_clear_all(self.options)

        userId = runhttp.getParamInt('userId', 0)
        gameId = runhttp.getParamInt('gameId', 0)
        key = runhttp.getParamStr('key', '')
        value = runhttp.getParamStr('value', '')
        
        if action == 'redis_search_all_userdata' :
            result = redisdata.redis_search_all_userdata(self.options, userId)
        
        if action == 'html_redirect' :
            datas = redisdata._getLastOkDefines(self.options)
            httpgame = datas['pokerdict']['http_game']
            rurl = runhttp.getParamStr('url')
            if os.environ.get('RUN_IN_DOCKER', 0) :
                # 在开发docker模式下，需要替换为外部HALL37HTTP端口号(此端口由nginx代理服务)
                refhost = runhttp.getParamStr('refhost')
                tks = refhost.split(':')
                tks[-1] = os.environ.get('PORT_NGINX', '80')
                httpgame = ':'.join(tks)
            result = rurl.replace('${http_game}', httpgame)
        
        if action == 'redis_get_userdata' :
            result = redisdata.redis_get_userdata(self.options, userId)

        if action == 'redis_set_userdata' :
            result = redisdata.redis_set_userdata(self.options, userId, key, value)

        if action == 'redis_get_gamedata' :
            result = redisdata.redis_get_gamedata(self.options, userId, gameId)

        if action == 'redis_set_gamedata' :
            result = redisdata.redis_set_gamedata(self.options, userId, gameId, key, value)
    
        if action == 'redis_get_map_clientid' :
            result = redisdata.redis_get_config(self.options, 'poker:map.clientid')

        if action == 'redis_get_map_productid' :
            result = redisdata.redis_get_config(self.options, 'poker:map.productid')

        if action == 'redis_get_map_activityid' :
            result = redisdata.redis_get_config(self.options, 'poker:map.activityid')

        if action == 'redis_get_map_evnetid' :
            result = redisdata.redis_get_config(self.options, 'poker:map.bieventid')

        if action == 'redis_del_userdata' :
            result = redisdata.redis_del_userdata(self.options, userId)

        if action == 'redis_del_gamedata' :
            result = redisdata.redis_del_gamedata(self.options, userId, gameId)

        if action == 'redis_del_day1st' :
            result = redisdata.redis_del_weakdata(self.options, userId, False)

        if action == 'redis_del_daylogin' :
            result = redisdata.redis_del_weakdata(self.options, userId, True)

        if action == 'redis_get_usertime' :
            result = redisdata.redis_get_usertime(self.options, userId)

        if action == 'redis_command' :
            cmdline = runhttp.getParamStr('command', '')
            cmdline = strutil.loads(cmdline);
            ralias = runhttp.getParamStr('redisalias', '')
            roomId = runhttp.getParamInt('roomId', 0)
            result = redisdata.redis_do_command(self.options, userId, roomId, ralias, cmdline)

        datas = redisdata._getLastOkDefines(self.options)
        httpgame = datas['pokerdict']['http_game']
        if action == 'putmsg' :
            httpgame = httpgame + '/v1/putmsg'
            result = tyhttp.dohttpquery(httpgame, runhttp.getDict())
        
        if action == 'get_room_info' :
            httpgame = httpgame + '/_http_manager_get_room_details'
            result = tyhttp.dohttpquery(httpgame, runhttp.getDict())

        if action == 'hotfix_code' :
            from optparse import Values
            options = Values()
            setattr(options, 'poker_path', self.options.pokerpath)
            setattr(options, 'hotfixpy', runhttp.getParamStr('hotfixpy'))
            setattr(options, 'hotfixwait', 1)
            setattr(options, 'serverIds', runhttp.getParamStr('serverIds'))
            result = hotfix.action(options, 0)

        if isinstance(result, (long, int, float, bool)) :
            result = str(result)
        if isinstance(result, (list, tuple, dict, set)) : 
            result = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
        if not isinstance(result, (str, unicode)) : 
            result = str(result)
        result = result.replace('<', '&lt;')
        result = result.replace('>', '&gt;')
        result = result.replace('\r', '')
        result = result.replace('\n', '<br>')
        result = result.replace('\\n', '<br>')
        result = result.replace(' ', '&nbsp;')
        result = result.replace('\\\\x', '\\x')
        mo = MsgPack()
        mo.setCmd(action)
        mo.setResult('ok', 1)
        mo.setResult('text', result)
        return mo

