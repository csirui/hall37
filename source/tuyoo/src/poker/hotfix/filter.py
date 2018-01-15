# -*- coding: utf-8 -*-
import getpass
import os
import sys

import psutil
from datetime import datetime


def _get_process_info():
    curuser = getpass.getuser()
    procs = []
    oldcwd = None
    for p in psutil.process_iter():
        try:
            if p.username() == curuser:
                cmdlines = p.cmdline()
            else:
                continue
        except:
            continue
        cmdline = ' '.join(cmdlines)
        if cmdline.find(' run.py ') > 0 and cmdline.find('pypy ') >= 0:
            if oldcwd == None:
                oldcwd = p.cwd()
            else:
                if oldcwd != p.cwd():
                    print 'oldcwd=', oldcwd
                    print 'proc.cwd=', p.cwd()
                    raise Exception('found diff cwd pypy process!')
            procs.append([p.pid, p.cwd(), cmdlines[2]])
            print procs[-1]
    return oldcwd, procs


def filter_log_file(proc, desp, lhead, logdate):
    llen = len(lhead)
    src = os.path.abspath(os.path.join(proc[1], '..', 'log', proc[2] + '.log' + logdate))
    print 'open->', src
    dest = os.path.join(desp, proc[2] + '.log')
    fs = open(src, 'r')
    ds = open(dest, 'w')
    for l in fs:
        i = l.find('] ')
        if i > 0:
            tag = l[i + 1:i + 4]
            wr = 0
            if tag == ' E ' or tag == ' W ' or tag == '   ' or tag == ' Tr':
                wr = 1
            elif tag == ' I ' and l.find('PPS') > 0:
                wr = 1

            if wr:
                if llen > 0:
                    lh = l[0:llen]
                    if lh >= lhead:
                        ds.write(l)
                else:
                    ds.write(l)

    fs.close()
    ds.close()


def main():
    if len(sys.argv) > 1:
        lhead = sys.argv[1]
    else:
        lhead = ''
    if len(sys.argv) > 2:
        logdate = sys.argv[2]
    else:
        logdate = ''
    ct = datetime.now().strftime('%Y%m%d_%H%M%S')
    print 'start', ct, 'head =', lhead
    cwd, procs = _get_process_info()
    outpath = os.path.abspath(os.path.join(cwd, '..', ct))
    print 'outpath=', outpath
    if not os.path.isdir(outpath):
        os.mkdir(outpath)
    for proc in procs:
        filter_log_file(proc, outpath, lhead, logdate)
    print 'done', datetime.now().strftime('%Y%m%d_%H%M%S')
    print 'result saved in:', outpath


if __name__ == '__main__':
    main()
