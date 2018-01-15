# -*- coding: utf-8 -*-

from poker.entity.configure import gdata

global results
for roomId in gdata.rooms():
    room = gdata.rooms()[roomId]
    ucount, pcount, users = room.getRoomOnlineInfoDetail()
    results[roomId] = [ucount, pcount, users]
