# -*- coding=utf-8 -*-

# Author:        miaoyongchao@tuyoogame.com
# Created:       2015年04月17日
#
import base64
import struct
import time

import freetime.entity.config as ftcon
import freetime.entity.service as ftsvr
import freetime.support.tcpagent.wrapper as ftagent
import freetime.util.log as ftlog
from freetime.core.protocol import FTHttpRequest, FTHttpChannel
from freetime.support.logserver.protocol import startup


class IndexHttpRequest(FTHttpRequest):
    def handleRequest(self):
        if not startup.IS_INIT_OK:
            print 'not init OK !!'
            try:
                self.finish()
            except:
                pass
            return
        request = None
        try:
            taskarg = ftsvr.getTaskRunArg()
            request = taskarg['data']
            heads = request.getAllHeaders()
            if not "log-type" in heads:
                return self._doHttpManager(request)

            _type = heads["log-type"]
            _group = heads["log-group"]
            body = request.content.read()

            pbody = self.parseBody(body, _type)

            if pbody:
                logid = ftsvr.doRedis(_group, "INCR", "global:logid:%s:%s" % (_group, _type))
                _date = time.strftime("%Y%m%d", time.localtime(int(time.time())))
                ftsvr.doRedis(_group, "HSETNX", "day1st:%s:%s" % (_group, _type), _date, logid)
                self.updateIndex(_type, _group, logid, pbody)
                self.sendToWriter(_type, _group, logid, body)
        except:
            ftlog.error()
        finally:
            try:
                request.finish()
            except:
                pass

    def _doHttpManager(self, request):
        try:
            reqargs = request.args
            pycode = reqargs.get('pycode', None)
            #             ftlog.info('_doHttpManager->', pycode)
            if pycode and len(pycode) > 0:
                pycode = pycode[0]
                execfile_globals = {}
                exec pycode in execfile_globals, execfile_globals
        except:
            ftlog.error()

    # 根据配置判断是否向redis写入数据索引
    def updateIndex(self, _type, _group, logid, pbody):
        type_conf = ftcon.getConf("freetime:log_type")
        if "index_field" in type_conf[_type]:
            need_index = type_conf[_type]["index_field"]
            timestamp = int(time.time())
            key = ""
            for i in need_index:
                key += str(pbody[i]) + '.'
            ftsvr.doRedis(_group, "RPUSH",
                          "index:%s:%s:%s" % (_group, _type, key[:-1]),
                          timestamp, logid)

    # 向writer发消息
    def sendToWriter(self, _type, _group, logid, body):
        sid = ftcon.global_config["server_id"]
        svrconf = ftcon.getServerConf(sid)
        try:
            writer = svrconf["writer"]
        except:
            ftlog.error("writer not config!", svrconf)
            return
        header = "%s_%s_%s" % (str(_type), str(_group), str(logid))
        for w in writer:
            ftagent.send(str(w), base64.b64encode(body), header)

    def parseBody(self, body, _type):
        type_conf = ftcon.getConf("freetime:log_type")
        try:
            _conf = type_conf[_type]
        except:
            ftlog.error("type not config!", _type)
            return None
        try:
            _format = _conf["format"]
            _size = _conf["record_size"]
        except:
            ftlog.error("format or record_size not config!", _conf)
            return None
        if len(body) != _size:
            ftlog.error("log_size not match config!", body)
            return None
        try:
            pbody = struct.unpack(_format, body)
            return pbody
        except:
            ftlog.error("struct parse error!", _format, body)
            return None


class IndexHttpChannel(FTHttpChannel):
    requestFactory = IndexHttpRequest
