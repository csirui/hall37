# -*- coding=utf-8 -*-

# Author:        zipxing@hotmail.com
# Created:       2015年04月06日 星期一 18时27分50秒
# 
"""
统一使用run.py作为主程序入口，命令行只需要传入如下参数：

配置redis库的ip,port,dbid：所有配置信息都存在这个统一库中

服务ID：每个freetime服务进程都分配一个唯一编号：
格式为：服务类型+具体编号, 例如CO01
参见demo/conf/server.json的具体内容
"""


def main():
    from datetime import datetime
    import sys

    if len(sys.argv) != 5:
        print "Usage:pypy run.py <server_id> <config_redis_ip> <config_redis_port> <config_redis_dbid>"
        sys.exit()

    print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'getdefaultencoding=', sys.getdefaultencoding()
    if sys.getdefaultencoding().lower() != "utf-8":
        reload(sys)
        sys.setdefaultencoding("utf-8")
        print datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'setdefaultencoding to utf-8'

    _server_id = sys.argv[1]
    _conf_ip = sys.argv[2]
    _conf_port = int(sys.argv[3])
    _conf_dbid = int(sys.argv[4])

    import freetime.entity.service as ftsvr
    import freetime.support.logserver.protocol as ftpro
    from freetime.support.logserver.protocol import startup
    # 业务逻辑的主要扩展点是protocol
    ftsvr.run(
        config_redis=(_conf_ip, _conf_port, _conf_dbid),
        server_id=_server_id,
        init_fun=startup.initialize,
        protocols=ftpro
    )


if __name__ == "__main__":
    main()
