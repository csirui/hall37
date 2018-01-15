#!/bin/bash

# 提交

src=$1
dst=$2
username=$3
password=$4

svnau="--username $username --password $password"
svnarg=--non-interactive

echo "复制文件: $src '=>' $dst"
cp "${src}"/{[0-9]*.json,*.all} "${dst}"

cd $dst
newfiles=$(svn st [0-9]*.json *.all | awk '/^\?/{print $2}')

if [ -n newfiles ]
then
    echo "添加新增文件"
    echo svn add: ${newfiles}
    svn add ${svnarg} ${svnau} ${newfiles}
fi
