# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import sys
import os
from webmgr.action.actthread import thread_do_action
from webmgr.action import actlog
from datetime import datetime
from webmgr.action.remote import hotfix

def useage():
    print '''
TuYoo Game Server Controler V3.7

用法:game.sh -m <config path> -a config_check     检查当前的配置文件内容的有效性
  或:game.sh -m <config path> -a config_reload    重新编译游戏配置文件REDIS内容, 写入REDIS数据库
  或:game.sh -m <config path> -a config_update -keys <配置键值列表,逗号分隔>   重新编译游戏配置文件REDIS内容, 写入REDIS数据库, 并通知所有服务重新加载游戏配置
  或:game.sh -m <config path> -a config_reset     重新编译游戏配置文件REDIS内容, 写入REDIS数据库, 并通知所有服务重新加载所有的游戏配置
  或:game.sh -m <config path> -a config_status    查看当前的配置同步更新情况
  或:game.sh -m <config path> -a compile          重新编译游戏PY文件,拷贝webroot文件
  或:game.sh -m <config path> -a start            重新装载配置内容，启动所有服务进程
  或:game.sh -m <config path> -a reset -sid <SRVID列表,逗号分隔> 重新启动指定的进程
  或:game.sh -m <config path> -a stop             停止所有服务进程
  或:game.sh -m <config path> -a push_code        推送最后编译的PY文件内容到所有服务器
  或:game.sh -m <config path> -a push_web         推送最后编译的WEBROOT文件内容到所有服务器
  或:game.sh -m <config path> -a rm_logs          删除所有服务上的log日志文件
  或:game.sh -m <config path> -a hotfix -py <hotfix.py> -sid <SRVID列表,逗号分隔> 
                                                  再给出的<sid>进程中执行<hotfix.py>文件, -sid可以为all, 意味在所有的进程中执行
                                                  action可以为：hotfix_nowait， 不等待执行结果，只是触发执行       
'''
    return 0


if sys.getdefaultencoding().lower() != "utf-8" :
    reload(sys)
    sys.setdefaultencoding("utf-8")


def parse_cmd_lines():
    from optparse import Values
    options = Values()
    for x in xrange(1, len(sys.argv)) :
        flg = sys.argv[x]
        if flg == '-m' :
            setattr(options, 'pokerpath', sys.argv[x + 1])
            x = x + 1
            
        if flg == '-a' :
            setattr(options, 'action', sys.argv[x + 1])
            x = x + 1
        
        if flg == '-py' :
            setattr(options, 'hotfixpy', sys.argv[x + 1])
            x = x + 1

        if flg == '-sid' :
            setattr(options, 'serverIds', sys.argv[x + 1])
            x = x + 1

        if flg == '-keys' :
            setattr(options, 'keys', sys.argv[x + 1])
            x = x + 1

    mfileroot = os.path.abspath(__file__)
    mfileroot = os.path.dirname(mfileroot)
    mfileroot = os.path.dirname(mfileroot)
    os.sys.path.insert(0, mfileroot)
    return options


def main():
    from tyserver.tyutils import fsutils
    actlog._with_std = 1

    options = parse_cmd_lines()
    if not hasattr(options, 'pokerpath') :
        useage()
        actlog.log('You must input -m <poker path>')
        return
    if not hasattr(options, 'action') :
        useage()
        actlog.log('You Must input -a <action>')
        return

    pokerpath = options.pokerpath
    if not pokerpath :
        actlog.log("must specified the service entrance path")
        useage()
        return None

    pokerpath = fsutils.makeAsbpath(options.pokerpath)
    if not fsutils.dirExists(pokerpath) :
        actlog.log("the service entrance path not exists [" + pokerpath + ']')
        useage()
        return None

    setattr(options, 'pokerpath', pokerpath)

    workpath = fsutils.getParentDir(__file__, 1)
    setattr(options, 'workpath', workpath)

    fpath = os.environ.get('LOGDIR', '')
    if fpath and fsutils.dirExists(fpath):
        fpath = fsutils.abspath(fpath)
        setattr(options, 'logpath', fpath)
        ct = datetime.now().strftime('%Y%m%d%H%M%S')
        actlog.open_act_log(options, {'uuid':ct})
    else:
        setattr(options, 'logpath', None)

    actlog.log("pokerpath =", options.pokerpath)
    actlog.log("workpath  =", options.workpath)
    actlog.log("logpath   =", options.logpath)

    flogfile = fsutils.appendPath(fpath, 'webmagr.log') 
    setattr(options, 'logfile', flogfile)
    
    actlog.log("action    =", options.action)
    if options.action == 'config_check' :
        action = {'action' : 'config_check',
                  'params':{}}
        thread_do_action(options, action)
        return

    if options.action == 'config_reload' :
        action = {'action' : 'config_reload',
                  'params':{}}
        thread_do_action(options, action)
        return

    if options.action == 'config_update' :
        keys = []
        if hasattr(options, 'keys') :
            keys =  options.keys.split(',')
        action = {'action' : 'config_update',
                  'params':{'keys' : keys}}
        thread_do_action(options, action)
        return

    if options.action == 'config_reset' :
        action = {'action' : 'config_update',
                  'params':{'reset' : 1}}
        thread_do_action(options, action)
        return

    if options.action == 'config_status' :
        action = {'action' : 'config_status',
                  'params':{}}
        thread_do_action(options, action)
        return
    
    if options.action == 'compile' :
        action = {'action' : 'compile_source',
                  'params':{}}
        thread_do_action(options, action)
        return

    if options.action == 'start' :
        action = {'action' : 'config_compile_start',
                  'params':{}}
        thread_do_action(options, action)
        return

    if options.action == 'reset' :
        if not hasattr(options, 'serverIds') :
            useage()
            actlog.log('You must input -sid XXX,XXX')
            return
        processids = options.serverIds.split(',')
        if not processids :
            useage()
            actlog.log('You must input -sid XXX,XXX')
            return
        action = {'action' : 'reset',
                  'params':{'processids' : processids}}
        thread_do_action(options, action)
        return
    
    if options.action == 'stop' :
        action = {'action' : 'stop_all_process',
                  'params':{}}
        thread_do_action(options, action)
        return
    
    if options.action == 'push_code' :
        action = {'action' : 'push_bin',
                  'params':{}}
        thread_do_action(options, action)
        return

    if options.action == 'push_web' :
        action = {'action' : 'push_web',
                  'params':{}}
        thread_do_action(options, action)
        return

    hotfixwait = 1
    if options.action == 'hotfix_nowait' :
        options.action = 'hotfix'
        hotfixwait = 0
    setattr(options, 'hotfixwait', hotfixwait)
        
    if options.action == 'hotfix' :
        if not hasattr(options, 'serverIds') :
            useage()
            actlog.log('You must input -sid XXX,XXX or -sid all')
            return
        if not hasattr(options, 'hotfixpy') :
            useage()
            actlog.log('You Must input -py xxxx.py')
            return
        hotfix.action(options)
        return

    if options.action == 'rm_logs' :
        action = {'action' : 'remove_all_logs',
                  'params':{}}
        thread_do_action(options, action)
        return

    actlog.log('unknow action of :', options.action)
    useage()


if __name__ == '__main__':
    try:
        main()
    finally:
        try:
            actlog.close_act_log()
        except:
            pass
        
        
