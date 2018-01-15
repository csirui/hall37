# -*- coding:utf-8 -*-
'''
Created on 2016年6月7日

@author: luoguanggui
'''


class MatchException(Exception):
    def __init__(self, errorCode, message):
        super(MatchException, self).__init__(errorCode, message)

    @property
    def errorCode(self):
        return self.args[0]

    @property
    def message(self):
        return self.args[1]


class ConfigException(MatchException):
    def __init__(self, message):
        super(ConfigException, self).__init__(-1, message)


if __name__ == '__main__':
    pass
