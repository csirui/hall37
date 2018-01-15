SHELL_FOLDER=$(cd `dirname ${0}`; pwd)
cd ${SHELL_FOLDER}
export DEBUG_MAP="TYWEBMGR:12321"
rm -fr ./logs/*
sh ./script/nohup.sh --httpport=8877 --path  ../../source/config_test 2>&1 > ./logs/nohup.out
