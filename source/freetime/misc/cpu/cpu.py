# -*- coding:utf-8 -*-  
import datetime
l1 = [1,2,3,4,5,6,7,8,9,0]
l2 = [2,3,5]

COUNT = 5000000
st = datetime.datetime.now()

for x in xrange(COUNT):
    #l3=list(set(l1)-set(l2)) 
    #比两个set相减更快的方法，省了一次set转换
    s1 = set(l1)
    for l in l2:
        if l in s1:
            s1.remove(l)
    l3=list(s1)

dt = (datetime.datetime.now()-st)
_time = (dt.seconds+dt.microseconds/1000000.0) 
pps = COUNT/_time
print _time, "出牌操作CPU测试:", pps, "次/秒"

