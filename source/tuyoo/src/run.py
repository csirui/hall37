# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
from datetime import datetime


# noinspection PyBroadException
def pycharm_debug(title):
    import os
    if 'DEBUG_HOST' not in os.environ or 'DEBUG_MAP' not in os.environ:
        return
    debug_host = os.environ["DEBUG_HOST"]
    debug_map = dict(map(lambda x: str(x).split(":"), str(os.environ["DEBUG_MAP"]).split(";")))
    if title not in debug_map:
        return
    try:
        import pydevd
        port = int(debug_map[title])
        pydevd.settrace(debug_host, port=port)
        print("Connect PyCharm [%s:%s]" % (title, port))
    except:
        # 链接调试服务器失败了
        return


def main():
    import sys
    if len(sys.argv) < 5:
        print "Usage:pypy run.py <server_id> <config_redis_ip> <config_redis_port> <config_redis_dbid>"
        print "Currentn command line is :", sys.argv
        return

    print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'sys.path=', sys.path
    try:
        import time
        t1 = time.time()
        print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'initepollreactor begin'
        #         from twisted.internet import epollreactor
        #         epollreactor.install()
        from twisted.internet import reactor
        print datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S.%f'), 'initepollreactor done, use time ', time.time() - t1, 'reactor=', reactor
    except Exception, e:
        print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'reactor install error !', e
    # set default coding to utf8...
    print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'getdefaultencoding=', sys.getdefaultencoding()
    if sys.getdefaultencoding().lower() != "utf-8":
        reload(sys)
        sys.setdefaultencoding("utf-8")
        print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'setdefaultencoding to utf-8'

    sys.orig_stdout = sys.stdout
    sys.orig_stderr = sys.stderr

    _server_id = sys.argv[1]
    _conf_ip = sys.argv[2]
    _conf_port = int(sys.argv[3])
    _conf_dbid = int(sys.argv[4])

    import freetime.entity.service as ftsvr
    import poker.protocol.startup as pstartup
    pycharm_debug(_server_id)
    ftsvr.run(
        config_redis=(_conf_ip, _conf_port, _conf_dbid),
        server_id=_server_id,
        init_fun=pstartup.initialize,
        protocols=pstartup
    )


if __name__ == "__main__":
    main()
