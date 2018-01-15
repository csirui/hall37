#!/bin/bash
SHELL_FOLDER=$(cd `dirname ${0}`; pwd)/
BINDIR=/usr/local/redis/bin
cd ${SHELL_FOLDER}


echo "shutdown" | ${BINDIR}/redis-cli -p 7901 > /dev/null 2>&1
sleep 1
nohup ${BINDIR}/redis-server ${SHELL_FOLDER}/7901.conf > ${SHELL_FOLDER}/7901.log 2>&1 &
echo start redis 7901

echo "shutdown" | ${BINDIR}/redis-cli -p 7902 > /dev/null 2>&1
sleep 1
nohup ${BINDIR}/redis-server ${SHELL_FOLDER}/7902.conf > ${SHELL_FOLDER}/7902.log 2>&1 &
echo start redis 7902

echo "shutdown" | ${BINDIR}/redis-cli -p 7903 > /dev/null 2>&1
sleep 1
nohup ${BINDIR}/redis-server ${SHELL_FOLDER}/7903.conf > ${SHELL_FOLDER}/7903.log 2>&1 &
echo start redis 7903

echo "shutdown" | ${BINDIR}/redis-cli -p 7904 > /dev/null 2>&1
sleep 1
nohup ${BINDIR}/redis-server ${SHELL_FOLDER}/7904.conf > ${SHELL_FOLDER}/7904.log 2>&1 &
echo start redis 7904

echo "shutdown" | ${BINDIR}/redis-cli -p 7905 > /dev/null 2>&1
sleep 1
nohup ${BINDIR}/redis-server ${SHELL_FOLDER}/7905.conf > ${SHELL_FOLDER}/7905.log 2>&1 &
echo start redis 7905

echo "shutdown" | ${BINDIR}/redis-cli -p 7906 > /dev/null 2>&1
sleep 1
nohup ${BINDIR}/redis-server ${SHELL_FOLDER}/7906.conf > ${SHELL_FOLDER}/7906.log 2>&1 &
echo start redis 7906

echo "shutdown" | ${BINDIR}/redis-cli -p 7907 > /dev/null 2>&1
sleep 1
nohup ${BINDIR}/redis-server ${SHELL_FOLDER}/7907.conf > ${SHELL_FOLDER}/7907.log 2>&1 &
echo start redis 7907

echo "shutdown" | ${BINDIR}/redis-cli -p 7908 > /dev/null 2>&1
sleep 1
nohup ${BINDIR}/redis-server ${SHELL_FOLDER}/7908.conf > ${SHELL_FOLDER}/7908.log 2>&1 &
echo start redis 7908
