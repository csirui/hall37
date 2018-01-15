# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com, zhouhao@tuyoogame.com
# Created:       2015年04月09日 星期四 10时56分34秒
#
import os

"""
使用twisted的日志系统，纪录按天滚动的日志文件
对缺省日志格式做了修改：
  - 时间精确到微秒
  - 中括号里纪录了tasklet标识
"""

from datetime import datetime
from functools import wraps
import stackless
import sys
import time
import traceback

LOG_LEVEL_DEBUG = 0
LOG_LEVEL_INFO = 1
LOG_LEVEL_ERROR = 2

log_level = 0
log_file_opend = 0
_tracemsg = []


def initLog(log_file, log_path, loglevel=0):
    from twisted.python import log
    from twisted.python.logfile import DailyLogFile
    global log_level, _tracemsg
    log_level = loglevel

    if log_path == 'stdout':  # support the UnitTest
        fout = sys.stdout
    else:

        class TyDailyLogFile(DailyLogFile):

            def __init__(self, log_file, log_path):
                DailyLogFile.__init__(self, log_file, log_path)

            def _openFile(self):
                self.path = os.path.join(self.directory, self.name) + "." + datetime.now().strftime('%Y_%m_%d')
                DailyLogFile._openFile(self)

            def rotate(self):
                """每次打开文件均携带当前日期，因此不需要进行文件的重命名
                """
                self._file.close()
                self._openFile()

        fout = TyDailyLogFile(log_file, log_path)
        if _tracemsg:
            for msg in _tracemsg:
                fout.write(msg)
                fout.write('\n')
            _tracemsg = None

    class _(log.FileLogObserver):
        log.FileLogObserver.timeFormat = '%m-%d %H:%M:%S.%f'

        def emit(self, eventDict):
            taskinfo = "%r" % stackless.getcurrent()
            # "<tasklet[, 1]>"  --> ", 1"
            eventDict['system'] = taskinfo[11:-2]
            log.FileLogObserver.emit(self, eventDict)

    fl = _(fout)
    log.startLoggingWithObserver(fl.emit)


def openNormalLogfile(log_file_fullpath):
    import logging.handlers

    class DayFileHandler(logging.handlers.TimedRotatingFileHandler):

        def __init__(self, log_file_fullpath):
            self.trueBaseFilename = os.path.abspath(log_file_fullpath)
            logging.handlers.TimedRotatingFileHandler.__init__(self, log_file_fullpath, when='MIDNIGHT')

        def _open(self):
            self.baseFilename = self.trueBaseFilename + "." + datetime.now().strftime('%Y_%m_%d')
            stream = logging.handlers.TimedRotatingFileHandler._open(self)
            self.baseFilename = self.trueBaseFilename
            return stream

        def doRollover(self):
            """
            每次打开文件均携带当前日期，因此不需要进行文件的重命名
            """
            if self.stream:
                self.stream.close()
                self.stream = None
            self.stream = self._open()

            currentTime = int(time.time())
            dstNow = time.localtime(currentTime)[-1]
            newRolloverAt = self.computeRollover(currentTime)
            while newRolloverAt <= currentTime:
                newRolloverAt = newRolloverAt + self.interval
            # If DST changes and midnight or weekly rollover, adjust for this.
            if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
                dstAtRollover = time.localtime(newRolloverAt)[-1]
                if dstNow != dstAtRollover:
                    if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                        addend = -3600
                    else:  # DST bows out before next rollover, so we need to add an hour
                        addend = 3600
                    newRolloverAt += addend
            self.rolloverAt = newRolloverAt

    handler = DayFileHandler(log_file_fullpath)

    my_logger = logging.getLogger(log_file_fullpath)
    my_logger.setLevel(logging.DEBUG)
    my_logger.addHandler(handler)
    return my_logger


def _log(*argl, **argd):
    _log_msg = ""
    for l in argl:
        if type(l) == tuple:
            ps = str(l)
        else:
            try:
                ps = "%r" % l
            except:
                try:
                    ps = str(l)
                except:
                    ps = 'ERROR LOG OBJECT'
        if type(l) == str:
            _log_msg += ps[1:-1] + ' '
        elif type(l) == unicode:
            _log_msg += ps[2:-1] + ' '
        else:
            _log_msg += ps + ' '
    if len(argd) > 0:
        _log_msg += str(argd)
    return _log_msg


def trace(*argl, **argd):
    """
    这个方法仅用于initLog方法之前进行日志打印, 仅仅由freetime代码进行使用
    """
    ct = datetime.now().strftime('%m-%d %H:%M:%S.%f')
    msg = ct + ' TRACE ' + str(id(stackless.getcurrent())) + ' | ' + _log(*argl, **argd)
    if _tracemsg != None and len(_tracemsg) < 10000:
        _tracemsg.append(msg)
    return msg


def trace_stdout(*argl, **argd):
    print trace(*argl, **argd)


def _logFunc(*argl, **argd):
    # ftlog.xxx(... caller=self) for instance method
    # ftlog.xxx(... caller=cls) for @classmethod
    callerClsName = ""
    try:
        _caller = argd.get("caller", None)
        if _caller:
            if not hasattr(_caller, "__name__"):
                _caller = _caller.__class__
            callerClsName = _caller.__name__
            del argd["caller"]
    except:
        pass
    if log_level > LOG_LEVEL_DEBUG:
        print "[ ]",
    else:
        print "[" + callerClsName + "." + sys._getframe().f_back.f_back.f_code.co_name + "]",
    return argd


def info(*argl, **argd):
    if log_level > LOG_LEVEL_INFO:
        return
    print "I", str(id(stackless.getcurrent())), '|',
    argd = _logFunc(*argl, **argd)
    print _log(*argl, **argd)


def hinfo(*argl, **argd):
    if log_level > LOG_LEVEL_INFO:
        return
    print "H", str(id(stackless.getcurrent())), '|',
    argd = _logFunc(*argl, **argd)
    print _log(*argl, **argd)


def warn(*argl, **argd):
    if log_level > LOG_LEVEL_INFO:
        return
    print "W", str(id(stackless.getcurrent())), '|',
    argd = _logFunc(*argl, **argd)
    print _log(*argl, **argd)


#     if not 'errorLogGroup' in argd :
#         # 发送异常到异常收集器
#         sendWran(argl, argd)
#         pass
#     else:
#         # 异常收集由errorInfo得调用者同意处理发送
#         pass


def debug(*argl, **argd):
    if log_level > LOG_LEVEL_DEBUG:
        return
    print "D", str(id(stackless.getcurrent())), '|',
    argd = _logFunc(*argl, **argd)
    print _log(*argl, **argd)


def error(*argl, **argd):
    if log_level > LOG_LEVEL_ERROR:
        return

    try:
        etype, value, tb = sys.exc_info()
        print "E", str(id(stackless.getcurrent())), "| ************************************************************"
        print "E", str(id(stackless.getcurrent())), '|', _log(*argl, **argd)
        traceback.print_exception(etype, value, tb, None, None)
    finally:
        etype = value = tb = None
    print "E", str(id(stackless.getcurrent())), '| ------------------------ Call Stack ------------------------'
    traceback.print_stack()
    print "E", str(id(stackless.getcurrent())), "| ************************************************************"
    if not 'errorLogGroup' in argd:
        # 发送异常到异常收集器
        sendException(errorInfo(argl, argd))
        pass
    else:
        # 异常收集由errorInfo得调用者同意处理发送
        pass


def errorInfo(*argl, **argd):
    errors = {}
    import freetime.entity.config as ftcon
    errors['sid'] = ftcon.global_config["server_id"]
    errors['ip'] = ftcon.server_map[errors['sid']]['ip']
    errors['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    errors['tasklet'] = str(id(stackless.getcurrent()))
    errors['loglines'] = _log(*argl, **argd)
    errors['exception'] = traceback.format_exception(*sys.exc_info())
    errors['tarceback'] = traceback.format_stack()[0:-1]
    return errors


def sendException(errorInfos):
    from freetime.entity import clients
    if clients.isEnabled('logcenter'):
        datas = {'cmd': 'log', 'act': 'error', 'params': errorInfos}
        clients.sendToAdapter('logcenter', datas)


# def sendWran(argl, argd):
#     from freetime.entity import clients
#     if clients.isEnabled('logcenter') :
#         warnInfos = {}
#         import freetime.entity.config as ftcon
#         warnInfos['sid'] = ftcon.global_config["server_id"]
#         warnInfos['ip'] = ftcon.server_map[warnInfos['sid']]['ip']
#         warnInfos['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
#         warnInfos['tasklet'] = str(id(stackless.getcurrent()))
#         warnInfos['loglines'] = _log(*argl, **argd)
#         datas = {'cmd' : 'log', 'act' : 'warn', 'params': warnInfos}
#         clients.sendToAdapter('logcenter', datas)


exception = error


def stack(*argl, **argd):
    if log_level > LOG_LEVEL_ERROR:
        return
    print "S", str(id(stackless.getcurrent())), "| ************************************************************"
    print "S", str(id(stackless.getcurrent())), '|', _log(*argl, **argd)
    traceback.print_stack()
    print "S", str(id(stackless.getcurrent())), "| ************************************************************"


def format_exc(limit=None):
    return traceback.format_exc(limit)


def is_debug():
    return log_level <= LOG_LEVEL_DEBUG


def getMethodName():
    if log_level > LOG_LEVEL_DEBUG:
        return ""
    return sys._getframe().f_back.f_code.co_name


def catchedmethod(func):
    @wraps(func)
    def catchedCall(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            exception()

    return catchedCall


# 阻塞版本的http请求，会阻住tasklet，测试用
def testSendBi(url, header, data):
    from freetime.aio import http
    _start = time.time()
    _retry = 4
    _timeout = [0.1, 0.3, 0.5, 0.7]
    for x in xrange(_retry):
        code, _ = http.runHttp('POST', url, header, data, _timeout[x], _timeout[x])
        if code == 200:
            return (True, x, time.time() - _start)
    return (False, x, 0)


# group表示用户分群或者其他分群方式，例如user01, user02...
# type表示日志类型，例如chipupdate，login等
_log_server_idx = 0


def sendHttpLog(group, log_type, log_record):
    global _log_server_idx
    from freetime.aio import http
    import freetime.entity.config as ftcon
    lsurls = ftcon.global_config["log_server"]
    retryMax = ftcon.global_config.get('log_server_retry_count', 6)
    timeout = ftcon.global_config.get('log_server_time_out', 0.5)
    debug('sendHttpLog->', group, log_type, log_record)
    if lsurls:
        header = {"log-type": [log_type], "log-group": [group]}
        lsurl = lsurls[_log_server_idx % len(lsurls)]
        _log_server_idx = _log_server_idx + 1
        if lsurl:
            http.runHttpNoResponse("POST", lsurl, header, log_record, timeout, retrydata={'try': 0, 'max': retryMax})
