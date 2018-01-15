#!/bin/bash
SHELL_FOLDER=$(cd `dirname ${0}`; pwd)
rm -fr ${SHELL_FOLDER}/logs/*

cd ${SHELL_FOLDER}
pypy main.py --httpport=8000 --path /root/workspace2/config-trunk/dev/
