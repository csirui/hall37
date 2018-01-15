#!/bin/bash
SHELL_FOLDER=$(cd `dirname ${0}`; pwd)
rm -fr ${SHELL_FOLDER}/logs/*

cd ${SHELL_FOLDER}
pypy main.py --httpport=8000 --path /Users/zqh/workspace2/tuyoo-trunk/test/test_zvm/dev/
