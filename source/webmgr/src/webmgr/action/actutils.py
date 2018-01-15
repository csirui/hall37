# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from webmgr.action import actlog


def check_port(port, canbezero=False):
    if not isinstance(port, int) :
        return False
    if canbezero and port == 0 :
        return True
    if port < 1000 or port > 65535 :
        return False
    return True


def check_http_url(http, desc):
    if not isinstance(http, str) or http.find('http://') != 0 or http[-1] == '/' :
        return actlog.error(desc + ' must start with "http://" and not end with "/"')
    return 1

