#!/bin/bash
 
# Author:        zipxing@hotmail.com
# Created:       2015年04月08日 星期三 09时19分55秒
# FileName:      start.sh
# 
SHELL_PATH=`dirname $(readlink -f $0)`
PROJECT_PATH=$SHELL_PATH"/../"
FREETIME_PATH=$SHELL_PATH"/../../"
PY="pypy261"
export PYTHONPATH=$FREETIME_PATH
cd $PROJECT_PATH 
killall -9 pypy
rm -fr /home/zhoux/log/*
pypy run.py CO01 127.0.0.1 7979 0 &
#pypy run.py CO02 127.0.0.1 6379 0 &
#pypy run.py LO01 127.0.0.1 7979 0 &
#pypy run.py LO02 127.0.0.1 6379 0 &
#pypy run.py GA01 127.0.0.1 7979 0 &
#pypy run.py GA02 127.0.0.1 6379 0 &
pypy run.py AG02 127.0.0.1 7979 0 &
#pypy run.py AG04 127.0.0.1 7979 0 &
sleep 10
cd script
echo "start client..."
pypy udpcli.py 127.0.0.1 5000 1000000 3 0.05 &
pypy udpcli.py 127.0.0.1 5000 1000000 3 0.05 &
pypy udpcli.py 127.0.0.1 5000 1000000 3 0.05 &
pypy udpcli.py 127.0.0.1 5000 1000000 3 0.05 &
pypy udpcli.py 127.0.0.1 5000 1000000 3 0.05 &
pypy udpcli.py 127.0.0.1 5000 1000000 3 0.05 &
#pypy udpcli.py 127.0.0.1 5000 1000000 3 0.05 &
#pypy udpcli.py 127.0.0.1 5000 1000000 3 0.05 &
#pypy udpcli.py 127.0.0.1 5000 1000000 3 0.05 &
#pypy udpcli.py 127.0.0.1 5000 1000000 3 0.05 &
