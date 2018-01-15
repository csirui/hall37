# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

def getResourcePath(fileName):
    import os
    cpath = os.path.abspath(__file__)
    cpath = os.path.dirname(cpath)
    fpath = cpath + os.path.sep + fileName
    return fpath


def loadResource(fileName):
    fpath = getResourcePath(fileName)
    f = None
    try:
        f = open(fpath)
        c = f.read()
        f.close()
        return c
    finally:
        try:
            f.close()
        except:
            pass


