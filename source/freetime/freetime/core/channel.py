# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.3.28

import stackless
from stackless import bomb

import freetime.util.log as ftlog


class FTChannel(stackless.channel):
    def send_nowait(self, v):
        if self.balance == 0:
            self.value = v
        else:
            self.send(v)

    def send_exception_nowait(self, ntype, value):
        if self.balance == 0:
            self.exc = (ntype, value)
        else:
            if isinstance(value, ntype):
                self.send(bomb(ntype, value))
            else:
                self.send_exception(ntype, value)

    def receive(self):
        try:
            if hasattr(self, 'value'):
                v = self.value
                del self.value
                return v
            if hasattr(self, 'exc'):
                ntype, value = self.exc
                del self.exc
                raise ntype, value
            return stackless.channel.receive(self)
        except Exception, e:
            ftlog.error("Channel receive error", str(e))
            return None
