# -*- coding=utf-8 -*-

global exec_result
_log_server_idx = 0


def sendHttpLog(group, log_type, log_record):
    global _log_server_idx
    import freetime.entity.config as ftcon
    from freetime.aio import http
    lsurls = ftcon.global_config["log_server"]
    if lsurls:
        header = {"log-type": [log_type], "log-group": [group]}
        lsurl = lsurls[_log_server_idx % len(lsurls)]
        _log_server_idx = _log_server_idx + 1
        http.runHttpNoResponse("POST", lsurl, header, log_record, 0.5)


from freetime.util import log

log.sendHttpLog = sendHttpLog
