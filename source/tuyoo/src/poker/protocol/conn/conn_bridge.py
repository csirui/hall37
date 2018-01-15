# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
from freetime.entity.msg import MsgPack
from freetime.util import log as ftlog

OLDROOMDI_MAP = {
    700110: 70011000,
    700210: 70021000,
    700310: 70031000,
    700410: 70041000,
    710110: 71011000,
    710210: 71021000,
    710310: 71031000,
    710410: 71041000,
    740110: 74011000,
    740210: 74021000,
    740310: 74031000,
    740410: 74041000,
    750110: 75011000,
    750210: 75021000,
    750310: 75031000,
    750410: 75041000,
    760110: 76011000,
    760210: 76021000,
    760310: 76031000,
    760410: 76041000,
    770110: 77011000,
    770210: 77021000,
    770310: 77031000,
    770410: 77041000,
    730110: 73011000,
    730210: 73021000,
    730310: 73031000,
    730410: 73041000,
    730510: 73051000,
    730610: 73061000,
    730710: 73071000,
    730810: 73081000,
    730910: 73091000,
    731010: 73101000,
    731110: 73111000,
    731210: 73121000,
    731310: 73131000,
    731410: 73141000
}


def convertOldRoomId(roomId, msgstr):
    if roomId in OLDROOMDI_MAP:
        rid = OLDROOMDI_MAP[roomId]
        ftlog.info('convertOldRoomId', roomId, '->', rid)
        msg = MsgPack()
        try:
            msg.unpack(msgstr)
        except:
            raise Exception('the json data error 7 !! [' + repr(msgstr) + ']')
        msg.setParam('roomId', rid)
        msgstr = msg.pack()
        return rid, msgstr
    return roomId, msgstr
