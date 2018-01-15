# -*- coding=utf-8
import time

import freetime.util.log as ftlog
from poker.util.reflection import TYClassRegister


class TYActivityRegister(TYClassRegister):
    _typeid_clz_map = {}


class TYActivityEventRegister(TYClassRegister):
    _typeid_clz_map = {}


class TYActivitySystem(object):
    def reloadConf(self):
        pass


class TYActivity(object):
    TYPE_ID = 0

    def __init__(self, dao, clientConfig, serverConfig):
        self._dao = dao
        self._clientConf = clientConfig
        self._serverConf = serverConfig

    def checkOperative(self):
        start_ts = time.mktime(time.strptime(self._serverConf['start'], '%Y-%m-%d %H:%M:%S'))
        end_ts = time.mktime(time.strptime(self._serverConf['end'], '%Y-%m-%d %H:%M:%S'))
        now_ts = time.time()
        if now_ts < start_ts or now_ts > end_ts:
            return False
        else:
            return True

    def getConfigForClient(self, gameId, userId, clientId):
        '''
        活动模板的配置
        即：
            本次活动的配置
        '''
        return self._clientConf

    def handleRequest(self, msg):
        return None

    def reload(self, config):
        if 'config' not in config:
            ftlog.info('ERROR', config)
        # 某情况下vc发生变化，但是activity的reload将所有tc相关内容也进行了reload
        # 当发现已有actId时，其配置是缓存的，config在上一次已经pop过了，再次pop就会出问题
        if "server_config" in config:
            self._serverConf = config.pop("server_config")
        else:
            if not self._serverConf:
                ftlog.info('ERROR _serverConf', config)
        self._clientConf = config

    def getid(self):
        return self._clientConf['id']

    def finalize(self):
        pass
