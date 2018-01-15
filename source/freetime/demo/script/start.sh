#!/bin/bash
 
# Author:        zipxing@hotmail.com
# Created:       2015年04月08日 星期三 09时19分55秒
# FileName:      start.sh
# 
SHELL_PATH=`dirname $(readlink -f $0)`
PROJECT_PATH=$SHELL_PATH"/../"
FREETIME_PATH=$SHELL_PATH"/../../"
export PYTHONPATH=$FREETIME_PATH
cd $PROJECT_PATH 
killall -9 pypy261
rm -fr /home/zhoux/log/*
pypy261 run.py CO01 127.0.0.1 7979 0 &
pypy261 run.py CO02 127.0.0.1 7979 0 &
pypy261 run.py LO01 127.0.0.1 7979 0 &
pypy261 run.py LO02 127.0.0.1 7979 0 &
pypy261 run.py GA01 127.0.0.1 7979 0 &
pypy261 run.py GA02 127.0.0.1 7979 0 &
pypy261 run.py AG01 127.0.0.1 7979 0 &
date > /home/zhoux/AG02.start
pypy261 run.py AG02 127.0.0.1 7979 0 &
pypy261 run.py AG03 127.0.0.1 7979 0 &
pypy261 run.py AG04 127.0.0.1 7979 0 &
sleep 15
cd script
pypy261 udpcli.py 127.0.0.1 5000 100000 1000 0.5
