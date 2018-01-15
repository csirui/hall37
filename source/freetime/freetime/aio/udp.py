# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.3.28
import stackless


def sendQuery(query_protocol, data, timeout=1):
    d = query_protocol.query(data, timeout)
    return stackless.getcurrent()._fttask.waitDefer(d)
