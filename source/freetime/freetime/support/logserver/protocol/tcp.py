# -*- coding=utf-8 -*-

# Author:        miaoyongchao@tuyoogame.com
# Created:       2015年09月15日
#
import base64
import struct
import time

import freetime.entity.config as ftcon
import freetime.entity.service as ftsvr
import freetime.util.log as ftlog
import freetime.util.pio as ftpio
from freetime.support.logserver.protocol import startup
from freetime.support.tcpagent.protocol import S2AProtocol


class WriteTcpRequest(S2AProtocol):
    HEAD_SIZE = 256  # 文件头长度
    EXTRA_SIZE = 17  # 17字节数据包含：TUYO（4字节） 、recType（1字节）、recvTime（4字节）、logId（8字节）

    FILE_INFO = {}

    def doSomeLogic(self):
        if not startup.IS_INIT_OK:
            print 'not init OK !!'
            try:
                self.finish()
            except:
                pass
            return
        try:
            taskarg = ftsvr.getTaskRunArg()
            heads = str(taskarg["userheader1"])
            ftlog.debug('WriteTcpRequest 1->', taskarg, heads)
            _type, _group, rec_id = heads.split('_')
            global_conf = ftcon.getConf("freetime:global")
            data_dir = global_conf["data_path"]
            type_conf = ftcon.getConf("freetime:log_type")
            log_conf = type_conf[_type]
            rec_type = int(log_conf["rec_type"])
            reserved_size = int(log_conf["reserved_size"])
            log_size = int(log_conf["record_size"]) + reserved_size + self.EXTRA_SIZE
            record_count = log_conf["single_file_record_count"]
            body = base64.b64decode(taskarg["pack"])
            ftlog.debug('WriteTcpRequest 2->', body)
            cur_time = int(time.time())
            record = "tu" + struct.pack("<BIQ", rec_type, cur_time, int(rec_id)) + body + struct.pack(
                "<%ds" % reserved_size, str()) + "yo"
            self.writeFile(data_dir, _type, _group, int(rec_id), record_count, log_size, record)
        except:
            ftlog.error()
        finally:
            try:
                self.finish()
            except:
                pass

    # record可写性校验
    def checkFileRecord(self, f, rec_id, log_size, record_count):
        offset = (rec_id % record_count) * log_size + self.HEAD_SIZE
        ret, data = ftpio.pread(f, log_size, offset)
        if ret == log_size:
            if data[0] == 'T' and data[1] == 'U' and data[-1] == 'O' and data[-2] == 'Y':
                return True
        return False

    # 写文件
    def writeFile(self, data_dir, _type, _group, rec_id, record_count, log_size, record):
        fhandle = self.switchFile(data_dir, _type, _group, rec_id, record_count)
        if not fhandle:
            ftlog.info("switch open file error!!!")
            return
        if False == self.checkFileRecord(fhandle, rec_id, log_size, record_count):
            ftlog.info("check file record error!!!")
            return
        ftlog.info("GLOBAL_WRITER -> global:logid:%s:%s -> " % (_group, _type), rec_id)
        offset = (rec_id % record_count) * log_size + self.HEAD_SIZE
        ftpio.pwrite(fhandle, record, log_size, offset)

    # 切换文件
    def switchFile(self, data_dir, _type, _group, rec_id, record_count):
        file_index = rec_id / record_count
        data_path = "%s/%s/%s/bidata_%s_%s_%d.data" % \
                    (data_dir, _type, _group, _type, _group, file_index)
        key = _type + _group
        fTuple = self.FILE_INFO.get(key)
        try:
            if fTuple:
                fIndex = fTuple[0]
                if file_index > fIndex:
                    fTuple[1].close()
                    fhandle = open(data_path, 'r+')
                    self.FILE_INFO[key] = (file_index, fhandle)
                    return fhandle
                elif file_index == fIndex:
                    return fTuple[1]
                else:
                    return None
            else:
                fhandle = open(data_path, 'r+')
                if fhandle:
                    self.FILE_INFO[key] = (file_index, fhandle)
                return fhandle
        except:
            ftlog.error("open bi file error!", data_path)
            return None

    def getTaskletFunc(self, argd):
        return self.doSomeLogic
