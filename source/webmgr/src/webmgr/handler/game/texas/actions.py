# -*- coding: utf-8 -*-
'''
Created on 2016-1-14
@author: wangtao
'''
import os
import json
import commands
import traceback

from tyserver.tycmds import runhttp
from tyserver.tycmds.runhttp import markHttpRequestEntry
from tyserver.tyutils import fsutils, strutil, tylog, tyhttp
from tyserver.tyutils.msg import MsgPack
from webmgr.action import actqueue, acthistory
from webmgr.action.debugs import redisdata
from webmgr.handler import getResourcePath
from webmgr.action.remote import hotfix
from webmgr.handler import model
from webmgr.handler.game.texas import room_conf_generator
from tyserver.tyutils.cron import FTCron
import tyserver.tyutils.tylog as ftlog


svnroot = 'http://202.106.9.134:9055/newsvn'
roomConfTestingUrl = svnroot + '/config/trunk/test/game/8/room'
roomConfReleaseUrl = svnroot + '/config/branches/online-release/game/8/room'
teamConfUrl = svnroot + '/poker/config'

teamRoot = ""
teamCfgDir = ""
testingDir = ""
releaseDir = ""
runningDir = ""

def initDirs(_teamRoot, _runningDir):
    global teamRoot
    global teamCfgDir
    global testingDir
    global releaseDir
    global runningDir
    
    teamRoot = _teamRoot
    teamCfgDir = os.path.join(teamRoot, 'team')
    testingDir = os.path.join(teamRoot, 'testing')
    releaseDir = os.path.join(teamRoot, 'release')
    runningDir = _runningDir

class TexasActionHandler(object):
    
    def __init__(self, options):
        self.options = options

    @markHttpRequestEntry(jsonp=1)
    def do_http_texas_gen_json_file(self, jsonfile):
        self._initBase()
        ftlog.debug('do_http_texas_gen_json_file', jsonfile)
        if jsonfile == 'game/8/room/0.json':
            return self.gen_texas_room_json()
        
    @markHttpRequestEntry(jsonp=1)
    def do_http_texas_get_json_file(self, jsonfile):
        self._initBase()
        ftlog.debug("do_http_texas_gen_json_file jsonfile:", jsonfile)
        if fsutils.fileExists(jsonfile) :
            datas = fsutils.readJsonFile(jsonfile)
        else:
            datas = {'error': 'file "%s" not existed' % jsonfile}

        mo = MsgPack()
        mo.setCmd('json_file_data')
        mo.setResult('isOk', True)
        mo.setResult('jsonfile', jsonfile)
        mo.setResult('datas', datas)
        return mo 

    @markHttpRequestEntry()
    def do_http_texas_precommit(self, branch):
        self._initBase()
        ftlog.debug("do_http_texas_precommit branch:", branch)
        if branch == 'testing':
            jsonfile        = os.path.join(teamCfgDir, '0.json.all')
            jsonfileprev    = os.path.join(testingDir, '0.json.all')
        elif branch == 'release':
            jsonfile        = os.path.join(testingDir, '0.json.all')
            jsonfileprev    = os.path.join(releaseDir, '0.json.all')
            
        _, _, svnlog = self._svnCmd(teamRoot, 'log', '-l 5', jsonfileprev)
        svnlog = '\n'.join([line for line in svnlog.split('\n') if not line.startswith('------')])

        mo = MsgPack()
        mo.setCmd('texas_precommit')
        mo.setResult('isOk', True)
        mo.setResult('jsonfile', jsonfile)
        mo.setResult('jsonfileprev', jsonfileprev)
        mo.setResult('svnlog', svnlog)
        return mo 
    
    @markHttpRequestEntry()
    def do_http_texas_commit(self, branch, commitlog):
        self._initBase()
        ftlog.debug("do_http_texas_commit branch, commitlog:", branch, commitlog)
        if branch == 'testing':
            src = teamCfgDir
            tgt = testingDir
        elif branch == 'release':
            src = testingDir
            tgt = releaseDir

            
        outputs = ['提交到 '+branch]
        outputs.append('提交日志：\n'+ commitlog + '\n')

        sh_file = os.path.join(os.path.dirname(__file__), "commit.sh")
        cmd = 'bash %s %s %s %s %s' % (sh_file, src, tgt, "wangt", "g01dfish")
        ftlog.debug("do_http_texas_commit| cmd:", cmd)
        sh_output = os.popen(cmd).read()
        ftlog.debug("do_http_texas_commit| sh_output:", sh_output)
        outputs.append(sh_output)


        ftlog.debug("do_http_texas_commit branch, tgt, commitlog:", branch, tgt, commitlog)
        cmd, status, output = self._svnCmd(teamRoot, 'commit', tgt, '-m', '"%s"' % commitlog)
        ftlog.debug("do_http_texas_commit| branch:", branch,
                    "| status, output:", status, output)
        outputs.append('svn 提交输出：\n'+ output + '\n')


        output = ('\n\n').join(outputs)

        mo = MsgPack()
        mo.setCmd('texas_commit')
        mo.setResult('output', output.replace(' ', '&nbsp;').replace('\n', '<br />'))
        return mo 


    def _initBase(self):
        ''' 初始化一些基本配置 '''

        if getattr(self.options, 'texasTeamConfInited', False):
            return

        _datas = redisdata._getLastOkDefines(self.options)
        projects_path = _datas['pokerdict']['projects_path']   # 源码目录。一般为： /home/tyhall/hall37/source

        pokerpath = self.options.pokerpath  # 也就是配置目录。一般为 /home/tyhall/hall37/source/config
        teamRoot = os.path.join(projects_path, 'texas-team')
        runningDir = os.path.join(pokerpath, 'game/8/room/')

        ftlog.debug('TexasActionHandler._initBase >>|', 'projects_path, teamRoot, runningDir:',
                projects_path, teamRoot, runningDir)

        if not os.path.exists(teamRoot):
            ftlog.debug('create teamRoot:', teamRoot)
            fsutils.makePath(teamRoot)

            self._svnCmd(teamRoot, 'checkout', teamConfUrl, 'team')
            self._svnCmd(teamRoot, 'checkout', roomConfTestingUrl, 'testing')
            self._svnCmd(teamRoot, 'checkout', roomConfReleaseUrl, 'release')

        initDirs(teamRoot, runningDir)

        self.options.texasTeamConfInited = True
    
    def _svnCmd(self, workingpath, svnCmd, *svnArgs):
        print 'DEBUG TexasActionHandler._svnCmd <<| workingpath, svnCmd, svnArgs', workingpath, svnCmd, svnArgs
        svnau = '--username wangt --password g01dfish --no-auth-cache'
        cmd = ['cd ' + workingpath]
        cmd.append('export LANG=en_US.UTF-8')
        cmd.append(' '.join(['svn', svnCmd, '--non-interactive', svnau] + list(svnArgs)))

        cmd = ';'.join(cmd)
        status, output = commands.getstatusoutput(cmd)
        ftlog.debug('TexasActionHandler._svnCmd >>| cmd, status, output:', cmd, status, output)
        return cmd, status, output
    
    def gen_texas_room_json(self):
        self._initBase()

        xlsfile = fsutils.appendPath(teamCfgDir, 'room.xls')
        jsonallfile = fsutils.appendPath(teamCfgDir, '0.json.all')
        jsonfile = fsutils.appendPath(teamCfgDir, 'room.json')
        jsonfileprev = fsutils.appendPath(teamCfgDir, 'room.json.prev')

        self._svnCmd(teamCfgDir, 'update', xlsfile)
        # 获取历史记录 svn log
        _, _, svnlog = self._svnCmd(teamCfgDir, 'log', '-l 5', xlsfile)
        logcontent = '\n'.join([line for line in svnlog.split('\n') if not line.startswith('-----')])
        svnlog = svnlog.replace('\n', '<br/>')

        commands.getstatusoutput("rm -f [0-9]*.json")

        try:
            room_conf_generator.gen_split_file(xlsfile, teamCfgDir)
        except Exception, e:
            errstr = traceback.format_exc()
            mo = MsgPack()
            mo.setCmd('json_file_data')
            mo.setResult('isOk', False)
            mo.setResult("error", errstr)
            return mo

        commands.getstatusoutput("/bin/cp -f %s %s" % (jsonallfile, jsonfile))
        self._svnCmd(teamCfgDir, 'commit', jsonfile, '-m', '"%s"' % logcontent)
        self._svnCmd(teamCfgDir, 'export', '-rPREV', jsonfile, jsonfileprev, '--force')

        #datas = fsutils.readJsonFile(jsonfile)
        mo = MsgPack()
        mo.setCmd('json_file_data')
        mo.setResult('isOk', True)
        mo.setResult('svn_commit_log', svnlog)
        mo.setResult('jsonfile', jsonfile)
        mo.setResult('jsonfileprev', jsonfileprev)
        return mo
    
    def _check_param_jsonfile(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        return None, value
    
    def _check_param_branch(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        return None, value
    
    def _check_param_commitlog(self, key, params, extend_tag):
        value = runhttp.getParamStr(key, '')
        return None, value
    
    @markHttpRequestEntry(jsonp=1)
    def do_http_texas_get_match_time(self):
        '''获取所有比赛的所有场次的所有开赛时间'''
        self._initBase()
        days = int(runhttp.getParamStr('days', 5))
        ftlog.debug("TexasActionHandler.do_http_texas_get_match_time", "days:", days)
        match_time = self.calcAllStartTimes(days)
        mo = MsgPack()
        mo.setCmd('match_time')
        mo.setResult('match_time', match_time)
        return mo
    
    def calcAllStartTimes(self, days):
        '''
        获取所有比赛的所有场次的所有开赛时间

        return: {
            'mtt_chip_10w': {
                'name': '10万金币赛',
                'rooms': {
                    '8300': [
                        14232423423,
                        14232423423,
                        ...
                    ],
                    '8301': [
                        14232423423,
                        14232423423,
                        ...
                    ]
                }
            },
            'mtt_chip_100w': {...},
            ...
        }
        '''
        self._initBase()
        jsonfile = fsutils.appendPath(teamCfgDir, 'room.json')
        matchRoomConfs = fsutils.readJsonFile(jsonfile)

        allStartTimes = {}

        for roomId, roomConf in matchRoomConfs.items():
            if roomConf['typeName'] == 'mtt':
                matchConf = roomConf['matchConf']
                matchTypeId = matchConf['match_id']
                statTimeList = self.calcStartTimes(roomId, matchConf, days)
                if matchTypeId not in allStartTimes:
                    allStartTimes[matchTypeId] = {}
                    allStartTimes[matchTypeId]['name'] = roomConf['name']
                    allStartTimes[matchTypeId]['visible'] = matchConf['visible']
                    allStartTimes[matchTypeId]['rooms'] = {}
                allStartTimes[matchTypeId]['rooms'][roomId] = statTimeList
        return allStartTimes
    
    def calcStartTimes(self, roomId, match_room_conf, days):
        ''' 获取某个房间的开赛时间完整列表'''
        import time
        from datetime import datetime, timedelta

        cron = FTCron(match_room_conf["startTimes"])
        if match_room_conf.get('startTimesExcluded'):
            match_room_conf['startTimesExcluded'] = set(match_room_conf['startTimesExcluded'])

        excludedTimes = match_room_conf.get('startTimesExcluded')
        timestamp = time.time()
        ntime = datetime.fromtimestamp(int(timestamp))
        now = datetime.now()
        
        startTimeList = []
        
        while True:
            nexttime = cron.getNextTime(ntime)
            if nexttime is not None:
                if (nexttime - now).days >= days:  # 最多给看未来这么多天的配置。太多了数据量大，慢
                    break
                nextStartTime = int(time.mktime(nexttime.timetuple()))
                ntime = nexttime + timedelta(seconds=30)
                if excludedTimes and (
                        nexttime.strftime('%H:%M') in excludedTimes
                        or nexttime.strftime('%Y%m%d') in excludedTimes
                        or nexttime.strftime('%Y%m%d %H:%M') in excludedTimes
                        or nexttime.strftime('%w') in excludedTimes
                        ):
                    ftlog.debug("|skip nextStartTime:", nexttime, nextStartTime)
                    continue
                ftlog.debug("|nextStartTime:", nexttime, nextStartTime)
                startTimeList.append('%d-%02d-%02d %02d:%02d' % nexttime.timetuple()[:5])
            else:
                break
        return startTimeList
        