# -*- coding=utf-8 -*-

# Author:        zipxing@hotmail.com
# Created:       2015年04月23日 星期四 18时32分00秒

import freetime.core.cffi_ as ftcffi

_clib, _cdef = ftcffi.getCffi("ft")
_ffibuf = _cdef.new("char[]", 65536)


def pwrite(fd, data, count, offset):
    global _clib, _cdef
    return _clib.ftpwrite(fd.fileno(), data, count, offset)


def pread(fd, count, offset):
    global _clib, _cdef, _ffibuf
    fbuf = None
    # 减少new的开销，对于小于64K的读请求，都使用预先分配的buf
    if count < 65536:
        fbuf = _ffibuf
    else:
        fbuf = _cdef.new("char[]", count + 12)
    ret = _clib.ftpread(fd.fileno(), fbuf, count, offset)
    return (ret, _cdef.buffer(fbuf, count)[:])
