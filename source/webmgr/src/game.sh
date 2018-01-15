#!/bin/bash

SHELL_FOLDER=$(cd `dirname ${0}`; pwd)

export PYTHONUNBUFFERED=1
export LOGDIR=./actlogs
pypy ${SHELL_FOLDER}/game.py "$@"
_RET_=$?
echo "=== game.sh done ==="
exit ${_RET_}
