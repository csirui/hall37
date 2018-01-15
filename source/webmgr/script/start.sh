#!/bin/bash

SHELL_FOLDER=$(cd `dirname ${0}`; pwd)

SRC1=$(cd ${SHELL_FOLDER}/../src; pwd)
WORKPATH=$(cd ${SHELL_FOLDER}/../; pwd)

cd ${WORKPATH}
echo WORKPATH=${WORKPATH}
export MAINCLS=${SRC1}/main.py

export PYTHONUNBUFFERED=1
export PYPY_GC_MAX=2GB

export PROCKEY=${MAINCLS}
sh ${SHELL_FOLDER}/_stop_.sh

if [ "${SSHOOK}" == "hook" ] 
then
	while  [ 1 ]
	do
		if [ -d "${WORKPATH}/logs/" ]
		then
		    rm -fr ${WORKPATH}/logs/*
		fi
		pypy ${MAINCLS} $* 2>&1
	done
else
	if [ -d "${WORKPATH}/logs/" ]
	then
	    rm -fr ${WORKPATH}/logs/*
	fi
	pypy ${MAINCLS} $* 2>&1
fi
