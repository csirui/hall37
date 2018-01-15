# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.3.28

"""
所有加载过的cffi句柄都在ft_cffi中管理：
    key是so的文件名
    value是lib和ffi句柄
自定义的扩展cffi代码，请使用loadCffi方法加载
框架用到的cffi代码，在freetime/core/cffi/ft.so中, 此处预先load，键值是"ft"
"""

import os

from cffi import FFI

_ft_cffi = {}

_FT_CDEF = """int ftcode(int seed, char *data, int datalen, char *out); 
    ssize_t ftpread(int fd, void *buf, size_t count, size_t offset); 
    ssize_t ftpwrite(int fd, const void *buf, size_t count, size_t offset);"""


def loadCffi(libname, cdef_text, libpath):
    if libname in _ft_cffi:
        return _ft_cffi[libname]
    _ffi = FFI()
    _ffi.cdef(cdef_text)
    sofile = libpath + "/" + libname + ".so"
    _lib = _ffi.dlopen(sofile)
    _ft_cffi[libname] = (_lib, _ffi)


def loadFTCffi():
    sodir = os.path.dirname(os.path.abspath(__file__)) + "/cffi/"
    return loadCffi("ft", _FT_CDEF, sodir)


def getCffi(libname):
    if libname in _ft_cffi:
        return _ft_cffi[libname]
    return (None, None)


loadFTCffi()
