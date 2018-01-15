# -*- coding: utf-8 -*-
from datetime import datetime

import psutil, getpass, os


def _get_process_info():
    curuser = getpass.getuser()
    procs = []
    oldcwd = None
    for p in psutil.process_iter():
        try:
            if p.username() == curuser :
                cmdlines = p.cmdline()
            else:
                continue
        except:
            continue
        cmdline = ' '.join(cmdlines)
        if cmdline.find(' run.py ') > 0 and cmdline.find('pypy ') >= 0 :
            if oldcwd == None :
                oldcwd = p.cwd()
            else:
                if oldcwd != p.cwd() :
                    print 'oldcwd=', oldcwd
                    print 'proc.cwd=', p.cwd()
                    raise Exception('found diff cwd pypy process!')
            procs.append([p.pid, p.cwd(), cmdlines[2]])
            print procs[-1]
    return oldcwd, procs


def filter_log_file(proc, desp):
    src = os.path.abspath(os.path.join(proc[1], '..', 'log' , proc[2] + '.log'))
    print 'open->', src
    dest = os.path.join(desp, proc[2] + '.log')
    fs = open(src, 'r')
    ds = open(dest, 'w')
    for l in fs :
        i = l.find('] ')
        if i > 0 :
            tag = l[i + 1:i + 4]
            if tag == ' E ' or tag == ' W ' or tag == '   ' :
                ds.write(l)
    fs.close()
    ds.close()
    

def main():
    ct = datetime.now().strftime('%Y%m%d_%H%M%S')
    print 'start', ct
    cwd, procs = _get_process_info()
    outpath = os.path.abspath(os.path.join(cwd, '..', ct))
    print 'outpath=', outpath
    if not os.path.isdir(outpath) :
        os.mkdir(outpath)
    for proc in procs :
        filter_log_file(proc, outpath)
    print 'done', datetime.now().strftime('%Y%m%d_%H%M%S')
    print 'result saved in:', outpath


if __name__ == '__main__' :
    main()

