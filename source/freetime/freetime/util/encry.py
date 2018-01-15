# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.4.3

import freetime.core.cffi_ as ftcffi

_clib, _cdef = ftcffi.getCffi("ft")
_codestr = _cdef.new("char []", 65536)


def code(seed, data):
    global _clib, _cdef, _codestr
    dl = len(data)
    assert (dl <= 65500), 'the ftcode length too long ' + str(dl)
    _clib.ftcode(seed, data, len(data), _codestr)
    return _cdef.buffer(_codestr, len(data))[:]
