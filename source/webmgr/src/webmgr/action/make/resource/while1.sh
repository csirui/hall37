#!/bin/bash
# Created on 2015-5-12
# @author: zqh

PROCID="${1}"
PROCKEY="${1} ${2} ${3} ${4}"
TASKSET="${5}"
PYPY="${6}"
SENDMAIL="${SENDMAIL}"
BIN_PATH="${BIN_PATH}"
SCRIPT_OUTFILE="${LOG_PATH}/nohup.${1}"

echo "${PROCID}" >> ${SCRIPT_OUTFILE}
export PYTHONUNBUFFERED=1
export PYPY_GC_MAX=4GB

if [ "${TASKSET}" -gt 0 ]
then
	TASKSET="taskset -c ${TASKSET}"
else
	TASKSET=""
fi

if [ "${SENDMAIL}" -eq 1 ]
then
	SENDMAIL=1
else
	SENDMAIL=0
fi

function echomsg()
{
	msg=`date '+%F %T'`
	msg="${msg} ${PROCID} ${1} ${2} ${3} ${4} ${5} ${6} ${7} ${8} ${9}"
	echo ${msg} >> ${SCRIPT_OUTFILE}
	echo ${msg}
}

cd ${BIN_PATH}

PROJECT_PATH="${DOCKER_PROJECT_PATH}"
if [ ! -z "${PROJECT_PATH}" ]
then
	export PYTHONPATH=${PROJECT_PATH}
fi

echomsg "Use PYTHONPATH :" "${PYTHONPATH}"
echomsg "Hook Script Log to :" "${SCRIPT_OUTFILE}"
echomsg "Hook Script argv :" "$@"
echomsg "Hook Script Start at :" "${BIN_PATH}"

while  [ 1 ]
do
	echomsg 'Hook Process Create.'
	echomsg "${TASKSET} ${PYPY} run.py ${PROCKEY}"
    export DEBUG_MAP="AG001:12000"
	${TASKSET} ${PYPY} run.py ${PROCKEY} >> ${SCRIPT_OUTFILE} 2>&1
	echomsg 'Hook Process Missing.'

	if [ ${SENDMAIL} -eq 1 ]
	then
		MAILPARAM="${PROCKEY} ${BIN_PATH} ${SCRIPT_OUTFILE}"
		# nohup pypy ${BIN_PATH}/remote.py sendmail crash ${MAILPARAM} >> ${SCRIPT_OUTFILE} 2>&1 &
	else
		exit 1
	fi
done

