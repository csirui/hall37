# -*- coding: utf-8 -*-
'''
Created on 2016-8-24
@author: wangt
'''


import os
import json
import pkgutil
import importlib
import codecs

from tyserver.tycmds import runhttp
from tyserver.tycmds.runhttp import markHttpRequestEntry
from tyserver.tyutils import fsutils, strutil, tylog, tyhttp
from tyserver.tyutils.msg import MsgPack
from webmgr.action.debugs import redisdata
from webmgr.handler import getResourcePath

from webmgr.utils import cfgutil
from webmgr.utils import svn

# TODO: action gen_json
# TODO: action compair
# TODO: action commit_trunk
# TODO: action commit_release


class BaseActionEntry(object):
    def __init__(self, options):
        self.options = options
        self.gameCfgHandlers = {}

        # 查找所有 game/_{gameId} 的包, import 它们的 config_actions
        # pkgpath = os.path.dirname(game.__file__)
        # subPkgs = [name for _, name, _ in pkgutil.iter_modules([pkgpath])]
        # for pkg in subPkgs:
        #     if pkg.startswith("G") and pkg[1:].isdigit():
        #         gameId = int(pkg[1:])
        #         modName = 'webmgr.handler.game.%s.config_actions' % pkg
        #         mod = importlib.import_module(modName)
        #         cls = mod.ActionHandler
        #         gameHandlerObj = cls(options)
        #         gameConfigHandlers[gameId] = gameHandlerObj
        #         runhttp.addHandler(gameHandlerObj)

        self.initGameHandler(8, BaseActionHandler)  # 德州

        # self.initGameHandler(30, G30Handler)  # 三张
        # self.initGameHandler(38, G30Handler)  # 百人三张

    def initGameHandler(self, gameId, cls):
        try:
            self.gameCfgHandlers[gameId] = cls(self.options, gameId)
        except Exception:
            tylog.error("BaseActionEntry.tryLoadGameHandler|gameId:", gameId)

    @markHttpRequestEntry(jsonp=1)
    def do_http_config(self, action, gameId, name):
        gameHandler = self.gameCfgHandlers[gameId]
        try:
            return gameHandler.onAction(action, name)
        except Exception:
            # TODO: error to page
            tylog.error('BaseActionHandler.do_http_config '
                        '|action, name, gameId:', action, name, gameId)

    @markHttpRequestEntry(response='html')
    def do_http_confighttp(self, action, gameId, name):
        gameHandler = self.gameCfgHandlers[gameId]
        try:
            return gameHandler.onAction(action, name)
        except Exception:
            # TODO: error to page
            tylog.error('BaseActionHandler.do_http_config_http '
                        '|action, name, gameId:', action, name, gameId)

    def _check_param_action(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        return None, value

    def _check_param_gameId(self, key, params, extend_tag):
        value = runhttp.getParamInt(key, 0)
        return None, value

    def _check_param_name(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, 'unknown')
        return None, value


class ConfigMod(object):
    def __init__(self, name, gameId, testingUrl, releaseUrl, teamRoot, gamePkgDir):
        self.name = name
        self.gameId = gameId
        self.testingUrl = '%s/%s/%s/0.json' % (testingUrl, gameId, name)
        self.releaseUrl = '%s/%s/%s/0.json' % (releaseUrl, gameId, name)
        self.testingDir = '%s/testing/%s/%s' % (teamRoot, gameId, name)
        self.releaseDir = '%s/release/%s/%s' % (teamRoot, gameId, name)
        self.testingFile = os.path.join(self.testingDir, '0.json')
        self.releaseFile = os.path.join(self.releaseDir, '0.json')

        self.converter = None
        self.editor = None

        self.initMods(gamePkgDir)

    def initMods(self, gamePkgDir):
        tylog.info("ConfigMod.initMods| try import", self.name)
        pkgPath = "webmgr.handler.game.G%d.%s" % (self.gameId, self.name)
        pkgDir = os.path.join(gamePkgDir, self.name)
        mods = {}

        for _, modname, _ in pkgutil.iter_modules([pkgDir]):
            try:
                mods[modname] = importlib.import_module('.' + modname, pkgPath)
            except:
                tylog.info("ConfigMod.initMods|import fail"
                           "|name, mod:", self.name, modname)

        self.converter = mods.get('converter')
        self.editor = mods.get('editor')


class BaseActionHandler(object):
    def __init__(self, options, gameId):
        self.options = options
        self.gameId = gameId


        currPath = os.path.dirname(__file__)
        self.templatePath = os.path.join(currPath, 'template')

        self.svnRoot = svnroot = 'http://202.106.9.134:9055/newsvn'
        self.svnTestingUrl = svnroot + '/config/trunk/test/game'
        self.svnReleaseUrl = svnroot + '/config/branches/online-release/game'

        self.teamRoot = ""
        self.testingDir = ""
        self.releaseDir = ""
        self.runningDir = ""
        self.initDirs()

        self.configMods = {}
        self.initConfigMods()

    def initDirs(self):
        if getattr(self.options, 'teamConfInited', False):
            return

        _datas = redisdata._getLastOkDefines(self.options)

        # 源码目录。一般为： /home/tyhall/hall37/source
        projects_path = _datas['pokerdict']['projects_path']

        # 也就是配置目录。一般为 /home/tyhall/hall37/source/config
        pokerpath = self.options.pokerpath

        teamRoot = os.path.join(projects_path, 'team')

        if not os.path.exists(teamRoot):
            tylog.debug('create teamRoot:', teamRoot)
            fsutils.makePath(teamRoot)

            svn.svnCmd(teamRoot, 'checkout', self.svnTestingUrl, 'testing')
            svn.svnCmd(teamRoot, 'checkout', self.svnReleaseUrl, 'release')

        self.teamRoot = teamRoot
        self.testingDir = os.path.join(teamRoot, 'testing')
        self.releaseDir = os.path.join(teamRoot, 'release')
        self.runningDir = pokerpath

    def initConfigMods(self):
        gamePkgPath = "webmgr.handler.game.G%d" % self.gameId
        gamePkg = importlib.import_module(gamePkgPath)

        gamePkgDir = os.path.dirname(gamePkg.__file__)
        for _, name, _ in pkgutil.iter_modules([gamePkgDir]):
            tylog.info("BaseActionHandler.initConverters| try init:", name)
            try:
                configMod = ConfigMod(name, self.gameId, self.svnTestingUrl,
                                      self.svnReleaseUrl, self.teamRoot,
                                      gamePkgDir)
                self.configMods[name] = configMod
            except:
                tylog.error("BaseActionHandler.initConverters| name:", name)

    def getConn(self):
        return cfgutil.MysqlConn(host='111.203.187.142',
                                 port=33066,
                                 user='config',
                                 password='config',
                                 db='config_%s' % self.gameId
                                 )

    def onAction(self, action, name):
        tylog.info('BaseActionHandler.onAction'
                   '| action, name:', action, name)

        ret = None
        if action == 'generate':
            ret = self.doGenerate(name)
        elif action == 'show':
            ret = self.doShowPage(name)
        elif action == 'get':
            revision = runhttp.getParamStr("revision")
            branch = runhttp.getParamStr("branch")
            ret = self.doGet(name, branch, revision)
        elif action == 'svnLog':
            branch = runhttp.getParamStr("branch")
            ret = self.doSvnLog(name, branch)
        elif action == 'commit':
            branch = runhttp.getParamStr("branch")
            log = runhttp.getParamStr("log")
            ret = self.doCommit(name, branch, log)

        tylog.info('BaseActionHandler.onAction'
                   '| action, name:', action, name,
                   '| ret:', ret)
        return ret

    def doGenerate(self, name):
        jsonData = None
        if name == 'room':
            pass
        elif name == 'all':
            pass
        else:
            jsonData = self.doConvertOne(name)

        return jsonData

    def doConvertOne(self, name):
        try:
            configMod = self.configMods.get(name)
            if configMod:
                jsonData = configMod.converter.convert(self)
                self.writeFile(configMod.testingFile, jsonData)
                modified = svn.status(configMod.testingFile) == 'modified'

                return self.jsonrsp('generate', isOk=True, modified=modified)
        except:
            tylog.error("doGenJson|name:", name)

    def doShowPage(self, name):
        pagePath = os.path.join(self.templatePath, 'config.html')
        content = open(pagePath).read()
        formatParams = {
            "gameId": self.gameId,
            "configName": name,
            "title": name + '-' + str(self.gameId)
        }
        content = content.format(**formatParams)
        return content

    def doGet(self, name, branch, revision):
        configMod = self.configMods[name]
        if branch == 'testing':
            _file = configMod.testingFile
        elif branch == 'release':
            _file = configMod.releaseFile
        # elif branch == 'online':
        #     _file = configMod.onlineFile

        if not revision or revision.upper() == 'LOCAL':
            fileContent = fsutils.readJsonFile(_file)
        elif revision == 'HEAD':
            tempFileName = _file + '.HEAD'
            svn.export(_file, tempFileName, revision='HEAD')
            fileContent = fsutils.readJsonFile(tempFileName)

        fileContent = self.formatJson(fileContent)

        return fileContent

    def doCommit(self, name, branch, log):
        configMod = self.configMods[name]
        if branch == 'testing':
            _file = configMod.testingFile
        elif branch == 'release':
            fsutils.copyFile(configMod.testingFile, configMod.releaseFile)
            _file = configMod.releaseFile
        else:
            tylog.error("doCommit| unknown branch"
                        "| gameId, name, branch:", self.gameId, name, branch)
            output = "\n错误: unknown branch: %s" % branch
            output = output.replace(' ', '&nbsp;').replace('\n', '<br />')

            return self.jsonrsp('commit', isOk=True, output=output)

        if svn.status(_file) == 'unversioned':
            svn.add(_file)

        output = svn.commit(_file, log)
        outputLines = [
            '',
            '提交文件到 %s:' % branch,
            './game/%s/%s/0.json' % (self.gameId, name),
            '',
            '修改内容:',
            log,
            '',
            '提交结果:',
            output,
        ]
        output = '\n'.join(outputLines)
        output = output.replace(' ', '&nbsp;').replace('\n', '<br />')

        return self.jsonrsp('commit', isOk=True, output=output)

    def doSvnLog(self, name, branch):
        configMod = self.configMods[name]

        _file = configMod.testingFile if branch == 'testing' \
            else configMod.releaseFile

        svnLog = svn.log(_file)

        formatter = '# r{revision: <7s} | {author: <10} | {date}\n{msg}\n'
        svnLog = '\n'.join([formatter.format(**i) for i in svnLog])

        return self.jsonrsp('svnLog', isOk=True, svnLog=svnLog)

    def jsonrsp(self, cmd, **result):
        msg = MsgPack()
        msg.setCmd(cmd)
        msg.setKey('result', result)
        return msg

    def writeFile(self, filename, data):
        with codecs.open(filename, 'w', 'utf-8') as f:
            json.dump(data, f, indent=4, sort_keys=True, ensure_ascii=False)

    @staticmethod
    def formatJson(jsondata):
        return json.dumps(jsondata, indent=4, sort_keys=True, ensure_ascii=False)