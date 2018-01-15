#!/bin/bash
 
# Author:        zipxing@hotmail.com
# Created:       2015年04月09日 星期四 18时25分35秒
# FileName:      tp.sh
# 
 echo "测试每秒处理"$1"个包" > stat.txt
SHELL_PATH=`dirname $(readlink -f $0)`
PROJECT_PATH=$SHELL_PATH"/../"
FREETIME_PATH=$SHELL_PATH"/../../"
export PYTHONPATH=$FREETIME_PATH
cd $PROJECT_PATH 
killall -9 pypy
rm -fr /home/zhoux/log/*

#pypy run.py CO01 127.0.0.1 7979 0 &

#write profile to CO01.log
/home/zhoux/pypy261/bin/pypy -m cProfile -s time run.py CO01 127.0.0.1 7979 0 &

cd script
sleep 15s
./client.sh $1
more stat.txt
