# -*- coding:utf-8 -*-
'''
Created on 2016年7月1日

@author: zhaojiangang
'''

import json

from tyserver.tycmds import runhttp
from tyserver.tycmds.runhttp import markHttpRequestEntry
from tyserver.tyutils import fsutils, strutil
import tyserver.tyutils.tylog as ftlog


class DizhuActionHandler(object):
    def __init__(self, options):
        self.options = options
        self.gameConfPath = fsutils.appendPath(self.options.pokerpath, 'game/6')
        ftlog.info('DizhuActionHandler.__init__ options=', self.options,
                   'gameConfPath=', self.gameConfPath)
        
    def _check_param_roomConf(self, key, params, extend_tag):
        value = runhttp.getParamStr(key)
        try:
            value = strutil.loads(value)
            return None, value
        except:
            return 'roomConf must json string', None
    
    @markHttpRequestEntry(jsonp=1)
    def do_http_dizhu_room_list(self):
        ftlog.debug('do_http_dizhu_room_list')
        roomsPath = fsutils.appendPath(self.gameConfPath, 'room/0.json')
        with open(roomsPath, 'r') as f:
            rooms = json.load(f)
            return {'ec':0, 'rooms':rooms}
        return {'ec':-1, 'info':'Failed open file'}
    
    @markHttpRequestEntry(jsonp=1)
    def do_http_dizhu_get_room(self, roomId):
        ftlog.debug('do_http_dizhu_get_room roomId=', roomId)
        pass
    
    @markHttpRequestEntry(jsonp=1)
    def do_http_dizhu_save_room(self, roomId, roomConf):
        ftlog.debug('do_http_dizhu_save_room roomId=', roomId,
                    'roomConf=', roomConf)
        
        try:
            pass
        except:
            pass
            
    def checkRoomConf(self, roomConf):
        # TODO
        return False, '没实现';
    
if __name__ == '__main__':
    pass
