# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import urllib2, urllib


def dohttpquery(posturl, datadict):
    Headers = {'Content-type': 'application/x-www-form-urlencoded'}
    postData = urllib.urlencode(datadict)
    request = urllib2.Request(url=posturl, data=postData, headers=Headers)
    response = urllib2.urlopen(request)
    if response != None :
        retstr = response.read()
        return retstr
    return None
