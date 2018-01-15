import os,sys
import socket ,traceback, ssl
import time
import zlib
import datetime
import commands
import freetime.util.encry as ftenc

if len(sys.argv)!= 3:
    print "Usage: pypy tcpcli.py <host> <port>"
    sys.exit()

host = sys.argv[1] #127.0.0.1
port = int(sys.argv[2]) #9976

def _encode(src, encry_seed):
    zsrc = zlib.compress(src)
    dlen = len(zsrc)
    return '%04X'%dlen + ftenc.code(encry_seed+dlen, zsrc)


def _decode(dst):
    return ftenc.code(self.encry_seed+int(dst[:4], 16), dst[4:]) 


ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
try:
    ss.connect((host, port))
    seed = int(ss.recv(4), 16)
    print seed
    se = _encode("aaaaaaa", seed)
    print len(se), se
    ss.send(se)
except:
    traceback.print_exc()
    pass
