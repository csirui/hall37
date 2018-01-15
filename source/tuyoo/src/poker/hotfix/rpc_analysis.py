# -*- coding=utf-8 -*-
import getpass
import json
import os
import sys

import psutil


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
            #             print procs[-1]
    return oldcwd, procs


total = ["SID", "LW", 0,
         "AG1", "LR", 0, "AG1", "LW", 0, "AG2", "LR", 0, "AG2", "LW", 0,
         "DST", "LR", 0, "DST", "DO", 0, "DST", "LW", 0,
         "AG2", "LR", 0, "AG2", "LW", 0, "AG1", "LR", 0, "AG1", "LW", 0,
         "SID", "LR", 0, "SID", "DO", 0]
lines = []


def dologfile(fname):
    f = open(fname, 'r')
    for l in f:
        if l:
            if l.find('QUERY REPLAY SLOW') > 0:
                th = l[0:21]
                x = l.find('xxxnettimexxx')
                if x > 0:
                    x1 = l.find('[', x)
                    x2 = l.find(']', x1)
                    xt = l[x1:x2 + 1]
                    xj = json.loads(xt)
                    if len(xj) == 42:
                        tt = xj[-1] - xj[2]
                        for n in xrange(len(xj) / 3 - 1, -1, -1):
                            m = n * 3 + 2
                            if m > 3:
                                dt = xj[m] - xj[m - 3]
                                total[m] = total[m] + dt
                                xj[m] = '%0.4f' % (dt)
                            else:
                                xj[m] = 0
                        xj.append('%0.4f' % (tt))
                        xj.append(th)
                        r = l.find('request= {"')
                        if r > 0:
                            r = l.find('"rpc":"', r)
                            r2 = l.find('"', r + 8)
                            rc = l[r + 7:r2]
                            xj.append(rc)
                        lines.append(xj)
    f.close()


def main():
    if len(sys.argv) > 1:
        logdate = sys.argv[1]
    else:
        logdate = ''
    print 'start'
    _, procs = _get_process_info()
    for proc in procs:
        src = os.path.abspath(os.path.join(proc[1], '..', 'log', proc[2] + '.log' + logdate))
        #         print src
        dologfile(src)

    # for n in xrange(len(total) / 3 - 1, -1, -1) :
    #         m = n * 3 + 2
    #         total[m] = '%0.4f' % (total[m])
    #     print json.dumps(total, separators=(',', ':'))[1:-1]

    x = 0
    for l in lines:
        x += 1
        if x < 65530:
            for i in xrange(len(l)):
                l[i] = str(l[i])
            print ';'.join(l)
        else:
            print 'too much lines !!'
            return
    print 'done'


if __name__ == "__main__":
    main()
