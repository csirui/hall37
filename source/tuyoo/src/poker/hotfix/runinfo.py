# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from freetime.core.timer import FTLoopTimer


def cancel(self):
    if self.handle:
        try:
            self.handle.cancel()
        except:
            pass
    self.loopCount = 0
    self.handle = None
    return True


FTLoopTimer.cancel = cancel
