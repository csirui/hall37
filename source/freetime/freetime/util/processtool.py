# coding=UTF-8
'''process tools
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import re

import psutil


def getOneProcessByKeyword(keyword):
    recpl = re.compile(keyword, re.I)
    processList = psutil.get_process_list()
    for process in processList:
        try:
            cmdlineStr = " ".join(process.cmdline())
        except:
            continue
        if recpl.search(cmdlineStr):
            return process
