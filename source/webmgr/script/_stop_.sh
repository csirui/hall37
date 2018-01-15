#!/bin/bash

if [ "${PROCKEY}" == "" ]
then
	PROCKEY=${1}
fi

echo -n "Kill  : ${PROCKEY} ..."
COUNT=0
PIDS=1

while  [ "${PIDS}" != "" ]
do
	((COUNT++))
	ISFORCE=''
	if [ $COUNT -gt 200 ]
	then
		echo " failed"
		exit 1
	fi

	if [ $COUNT -gt 100 ]
	then
		ISFORCE='-9'
	fi

	echo -n "."
	PIDS=`ps -ef | grep -a "${PROCKEY}" | grep -v "grep" | grep -v "_stop_" | awk '{print $2}'`
	if [ "${PIDS}" != "" ]
	then
     	echo "${PIDS}" | xargs kill ${ISFORCE}
		sleep 0.01
    fi

done

echo " ok"
exit 0
