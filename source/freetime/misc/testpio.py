#-*- coding=utf-8 -*-
 
# Author:        zipxing@hotmail.com
# Created:       2015年04月23日 星期四 18时38分09秒
# 
import freetime.util.pio as pio

fd = open("test.dat", "r+")
print pio.pwrite(fd,"11111",5,2)
ret, data = pio.pread(fd, 5, 2)
print ret, data
