#!/bin/bash

SHELL_FOLDER=$(cd `dirname ${0}`; pwd)

export SSHOOK=hook

export PROCKEY=${SHELL_FOLDER}/start.sh
sh ${SHELL_FOLDER}/_stop_.sh

nohup sh ${PROCKEY} $* &
