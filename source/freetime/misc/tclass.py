#-*- coding=utf-8 -*-
 
# Author:        zipxing@hotmail.com
# Created:       2015年04月06日 星期一 19时10分07秒
# 

class ABC():
    def aaa(self):
        print "aaa"

def getClass():
    return ABC

print getClass()()

a=ABC()
print a.__class__
