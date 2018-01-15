import commands
import time

GETCOUNT=25

def getpid(cmdkey):
    cmd = "ps -ef | grep pypy | grep %s | grep -v grep | awk '{print $2}'"%(cmdkey)
    s, o = commands.getstatusoutput(cmd)
    if len(o)==0:
        #print 'Not found %s'%(cmdkey)
        return 0
    return int(o)

def getstat(pid):
    cmd = "top -bn 1 -p %d | grep pypy | awk '{print $9,$10}'"%(pid)
    s, o = commands.getstatusoutput(cmd)
    if s!=0:
        print 'Error top'
        return [0.0, 0.0]
    og = o.split()
    if len(og)!=2:
        print "output not 2 field!", o
        return [0.0, 0.0]
    return [float(og[0]), float(og[1])]

svrcpu=0
svrmem=0
svrcnt=0
clicpu=0
climem=0
clicnt=0

pids = getpid("run.py")
pidc = getpid("udpcli.py")
for x in xrange(GETCOUNT):
    if pids>0:
        cs,ms=getstat(pids)
        #print 'S', cs, ms
        svrcpu+=float(cs)
        svrmem+=float(ms)
        svrcnt+=1
    if pidc>0:
        cc,mc=getstat(pidc)
        #print 'C', cc, mc
        clicpu+=float(cc)
        climem+=float(mc)
        clicnt+=1
    time.sleep(0.5)

if svrcnt!=0:
    print "TPSvr:", "cpu", svrcpu/svrcnt, "mem", svrmem/svrcnt
if clicnt!=0:
    print "TPCli:", "cpu", clicpu/clicnt, "mem", climem/clicnt

commands.getstatusoutput("kill -9 %d"%(pids))
commands.getstatusoutput("kill -9 %d"%(pidc))
