# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import sys, time

from datetime import datetime
import os
try:
    t1 = time.time()
    print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'initepollreactor begin'
    from twisted.internet import epollreactor
    epollreactor.install()
    from twisted.internet import reactor
    print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'initepollreactor done, use time ', time.time() - t1, 'reactor=', reactor
except Exception, e:
    print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'reactor install error !', e
print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'getdefaultencoding=', sys.getdefaultencoding()
if sys.getdefaultencoding().lower() != "utf-8" :
    reload(sys)
    sys.setdefaultencoding("utf-8")
    print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'setdefaultencoding to utf-8'

def main():
    from optparse import OptionParser
    from tyserver.tyutils import fsutils
    
    parser = OptionParser(version="%prog 1.0", usage="%prog --path entrancepath --port Num")  
    parser.add_option("--path", dest="pokerpath", default=None,
                      help="must specified the service entrance path, the poker.json's path")  
    parser.add_option("--httpport", dest="httpport", default=None,
                      help="the http port")  

    options, _ = parser.parse_args()
    pokerpath = options.pokerpath
    if not pokerpath :
        print "must specified the service entrance path"
        parser.print_help()
        return None

    pokerpath = fsutils.makeAsbpath(options.pokerpath)
    if not fsutils.dirExists(pokerpath) :
        print "the service entrance path not exists [" + pokerpath + ']'
        parser.print_help()
        return None

    setattr(options, 'pokerpath', pokerpath)

    port = options.httpport
    try:
        port = int(options.httpport)
        setattr(options, 'httpport', port)
    except:
        print "the http port must be a integer"
        parser.print_help()
        return

    workpath = fsutils.getParentDir(__file__, 1)
    setattr(options, 'workpath', workpath)

    fpath = os.environ.get('LOGDIR', '')
    if not fpath :
        fpath = fsutils.appendPath(workpath, './../logs')
        fpath = fsutils.abspath(fpath)
        fsutils.makeDirs(fpath)
    setattr(options, 'logpath', fpath)

    print "pokerpath =", options.pokerpath
    print "httpport  =", options.httpport
    print "workpath  =", options.workpath

    flogfile = fsutils.appendPath(fpath, 'webmagr.log') 
    setattr(options, 'logfile', flogfile)

    from tyserver.server import startup
    from webmgr.manager import initialize, heartbeat
    setattr(options, 'initialize', initialize)
    setattr(options, 'heartbeat', heartbeat)
    startup(options)


if __name__ == '__main__':
    main()
