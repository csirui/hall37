# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015.4.15
from freetime.core.exception import FTMsgPackException
from freetime.core.protocol import _SocketOpt


def unpack(data):
    datas = data.split('|', 5)
    if len(datas) != 6:
        return (None, None, None, None, None, None)
    return (datas[0], datas[1], datas[2], datas[3], datas[4], datas[5])


# 预留两个用户定义header，以便不需要解析body的情况下，传输userid等信息
# src_server_id|dst_server_id|queryid(例如CO01.1000)|
# user_define_header1(例如userid)|user_define_header2|body
def packstr(src, dst, queryid, userheader1, userheader2, message):
    data = '|'.join(map(str, [src, dst, queryid, userheader1, userheader2, message]))
    if data[-1] != '\n':
        data = data + '\r\n'
    if isinstance(data, unicode):
        data = data.encode('utf-8')
    if len(data) > _SocketOpt.TCP_LINE_MAX_LENGTH:
        raise FTMsgPackException(
            'the message pack is too long for tcp ! max=' + str(_SocketOpt.TCP_LINE_MAX_LENGTH) + ' msglen=' + str(
                len(message)))
    return data
