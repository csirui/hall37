import os,sys
import socket ,traceback, ssl
import time
import datetime
import commands

if len(sys.argv)!= 6:
    print "Usage: pypy tpcli_udp.py <host> <port> <total_loop> <loop_persleep> <sleep_time>"
    sys.exit()

host = sys.argv[1] #127.0.0.1
port = int(sys.argv[2]) #9976

TOTAL_LOOP      = int(sys.argv[3])   #1000000
LOOP_PERSLEEP   = int(sys.argv[4])   #5000
LOOP_SLEEP      = float(sys.argv[5]) #0.1

lps = LOOP_PERSLEEP
wending = 0
callstat = 0

ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
for x in xrange(TOTAL_LOOP):
        st = datetime.datetime.now()
        for y in xrange(lps):
            ss.sendto('{"cmd":"dotask", "value":1234567890}', (host, port))

            #发送一条不合法的json，测试parseData接口
            #ss.sendto('{1234567890\r\n', (host, port))

            #ss.recvfrom(1024)
        time.sleep(LOOP_SLEEP)
        dt = (datetime.datetime.now()-st)
        pps = lps/(dt.seconds+dt.microseconds/1000000.0)
        print pps, lps
        continue
        #调整到最接近pps的速率...
        if pps>=LOOP_PERSLEEP/LOOP_SLEEP+80:
            lps-=20
            wending=0
        elif pps<=LOOP_PERSLEEP/LOOP_SLEEP-80:
            lps+=20
            wending=0
        else:
            wending+=1
            if wending>8:
                if callstat==0:
                    print "已经达到稳定状态(pps:%d),收集svr，cli的cpu和mem占用率"%(LOOP_PERSLEEP/LOOP_SLEEP)
                    os.system("pypy getstat.py >> stat.txt &")
                    callstat=1

