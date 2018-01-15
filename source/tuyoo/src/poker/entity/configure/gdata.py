# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import psutil
import stackless

import freetime.entity.config as ftcon
import freetime.util.log as ftlog

ENABLIE_DEFENCE_2 = 0

RUN_MODE_ONLINE = 1  # 服务运行模式: 正式线上
RUN_MODE_SIMULATION = 2  # 服务运行模式: 仿真
RUN_MODE_RICH_TEST = 3  # 服务运行模式: 大机器测试模式（机器资源多，可自由配置进程）
RUN_MODE_TINY_TEST = 4  # 服务运行模式: 个人小机器测试模式（机器资源少，自动最小资源模式）

SRV_TYPE_AGENT = 'AG'  # 服务类型: 消息代理传输服务
SRV_TYPE_SDK_HTTP = 'PL'  # 服务类型: PLATFORM SDK的HTTP服务
SRV_TYPE_SDK_GATEWAY = 'PG'  # 服务类型: PLATFORM SDK的HTTP服务
SRV_TYPE_CONN = 'CO'  # 服务类型: 游戏接入的TCP链接服务
SRV_TYPE_HTTP = 'HT'  # 服务类型: 游戏的HTTP服务
SRV_TYPE_ROBOT = 'RB'  # 服务类型: 游戏的机器人服务
SRV_TYPE_UTIL = 'UT'  # 服务类型: 游戏的无状态消息处理服务(例如: 取得插件列表)
SRV_TYPE_ROOM = 'GR'  # 服务类型: 游戏的房间服务
SRV_TYPE_TABLE = 'GT'  # 服务类型: 游戏的桌子服务
SRV_TYPE_CENTER = 'CT'  # 服务类型: 游戏的业务处理中心服务(例如: 排行榜等集中处理的业务)

SRV_TYPE_PKG_NAME = {
    SRV_TYPE_AGENT: 'agent',
    SRV_TYPE_SDK_HTTP: 'http',
    SRV_TYPE_CONN: 'conn',
    SRV_TYPE_HTTP: 'http',
    SRV_TYPE_ROBOT: 'robot',
    SRV_TYPE_UTIL: 'util',
    SRV_TYPE_ROOM: 'room',
    SRV_TYPE_TABLE: 'table',
    SRV_TYPE_CENTER: 'center',
    SRV_TYPE_SDK_GATEWAY: 'gateway'
}

SRV_TYPE_ALL = (SRV_TYPE_AGENT, SRV_TYPE_SDK_HTTP, SRV_TYPE_CONN, SRV_TYPE_HTTP,
                SRV_TYPE_ROBOT, SRV_TYPE_UTIL, SRV_TYPE_ROOM, SRV_TYPE_TABLE,
                SRV_TYPE_CENTER, SRV_TYPE_SDK_GATEWAY)

PROTOCOL_TYPE_HTTP = 'ht-http'  # 协议类型 : 游戏服的HTTP协议
PROTOCOL_TYPE_CONN = 'co-tcp'  # 协议类型 : CONN服务的TCP协议
PROTOCOL_TYPE_GAME_S2A = 's2a'  # 协议类型 : 游戏服务的TCP协议

CONN_CMD_ROUTE_TYPE_RANDOM = 'random'  # CONN接到命令时的路由类型: 在目标类型服务进程中, 随机选择一个进程, 进行转发
CONN_CMD_ROUTE_TYPE_UESRID = 'userId'  # CONN接到命令时的路由类型: 在目标类型服务进程中, 选择参数USERID取模所在进程, 进行转发
CONN_CMD_ROUTE_TYPE_ROOMID = 'roomId'  # CONN接到命令时的路由类型: 目标类型一定是GR类型, 选择参数ROOMID的值所对应的进程, 直接转发
CONN_CMD_ROUTE_TYPE_TABLEID = 'tableId'  # CONN接到命令时的路由类型: 目标类型一定是GT类型, 选择参数TABLEID的值所对应的进程, 直接转发

__datas = {}  # 内部变量保存空间

curProcess = psutil.Process()


def _initialize():
    global __datas
    if len(__datas) <= 0:
        ftlog.info('_initialize gdata begin.')
        __datas = {}
        pgdict = ftcon.getConf('poker:global')
        sid = ftcon.global_config["server_id"]
        __datas['server_type'] = sid[0:2]
        __datas['server_num'] = sid[2:]
        try:
            __datas['server_num_idx'] = int(sid[2:]) - 1
        except:
            __datas['server_num_idx'] = -1
        __datas.update(pgdict)
        __datas['game_packages'] = tuple(pgdict['game_packages'])
        mincenter = min(ftcon.server_type_map.get(SRV_TYPE_HTTP))
        if mincenter == sid:
            __datas['is_control_process'] = 1
        else:
            __datas['is_control_process'] = 0

        __datas['is_http_process'] = 0
        sdef = ftcon.server_map[sid]
        protocols = sdef.get('protocols')
        if protocols:
            server = protocols.get('server')
            if server:
                for p in server:
                    if p.endswith('http'):
                        __datas['is_http_process'] = 1
                        break
        _dumpGdataInfo()
        ftlog.info('_initialize gdata end.')
    return __datas


def initializeOk():
    '''
    判定当前各个游戏是否初始化完成
    注: 由poker系统initialize()方法进行初始化
    '''
    return __datas.get('initialize.ok', 0)


def getTaskSession():
    return stackless.getcurrent()._fttask.session


def isControlProcess():
    return __datas['is_control_process']


def isHttpProcess():
    return __datas['is_http_process']


def gamePackages():
    '''
    取得要初始化的游戏的package包列表, 例如: ['hall', 'dizhu', 'texas']
    '''
    return __datas['game_packages']


def games():
    '''
    取得当前系统初始化后的TYGame的所有实例
    key为: int(gameId)
    value为: TYGame()
    注: 由poker系统initialize()方法进行初始化
    '''
    return __datas['tygame.instance.dict']


def gameIds():
    '''
    取得当前系统初始化后的TYGame的ID列表
    注: 由poker系统initialize()方法进行初始化
    '''
    return __datas['tygame.instance.ids']


def getGame(gameId):
    '''
    取得当前系统初始化后的TYGame的所有实例
    key为: int(gameId)
    value为: TYGame()
    注: 由poker系统initialize()方法进行初始化
    '''
    return __datas['tygame.instance.dict'].get(gameId)


def rooms():
    '''
    取得当前系统初始化后的TYRoom的所有实例
    key为: int(roomId)
    value为: TYRoom()
    注: 由poker系统initialize()方法进行初始化
    '''
    return __datas.get('tyrooms.instance.dict', {})


def srvIdRoomIdListMap():
    '''
    取得ROOM的进程的映射关系, key为str(serverId), value为int(ROOMID)的list
    '''
    return __datas['srvid_roomid_map']


def roomIdDefineMap():
    '''
    取得ROOM的进程的映射关系, key为int(roomId), value为ROOM的基本定义信息
    ROOM的基本定义信息RoomDefine:
    
    RoomDefine.bigRoomId     int 当前房间的大房间ID, 即为game/<gameId>/room/0.json中的键
    RoomDefine.parentId      int 父级房间ID, 当前为管理房间时, 必定为0 (管理房间, 可以理解为玩家队列控制器)
    RoomDefine.roomId        int 当前房间ID
    RoomDefine.gameId        int 游戏ID
    RoomDefine.configId      int 配置分类ID
    RoomDefine.controlId     int 房间控制ID
    RoomDefine.shadowId      int 影子ID
    RoomDefine.tableCount    int 房间中桌子的数量
    RoomDefine.shadowRoomIds tuple 当房间为管理房间时, 下属的桌子实例房间的ID列表
    RoomDefine.configure     dict 房间的配置内容, 即为game/<gameId>/room/0.json中的值
    '''
    return __datas['roomid_define_map']


def bigRoomidsMap():
    '''
    取得ROOM的配置ID的映射关系, key为int(bigRoomId), value为int(roomId)的list
    此处的roomId列表仅包含"管理房间"的ID, 不包含"桌子实例房间shadowRoom"的ID
    '''
    return __datas['big_roomids_map']


def gameIdBigRoomidsMap():
    '''
    取得ROOM的配置ID的映射关系, key为int(gameId), value为int(bigRoomId)的list
    '''
    return __datas['gameid_big_roomids_map']


def getBigRoomId(roomId):
    if roomId in bigRoomidsMap():
        return roomId
    if roomId in roomIdDefineMap():
        return roomIdDefineMap()[roomId].bigRoomId
    return 0


def getRoomConfigure(roomId):
    if roomId in bigRoomidsMap():
        # roomId是一个bigRoomId
        ctlRoomId = bigRoomidsMap()[roomId][0]
        return roomIdDefineMap()[ctlRoomId].configure
    elif roomId in roomIdDefineMap():
        # roomId是一个ctrlRoomId或者是一个桌子房间ID, 
        return roomIdDefineMap()[roomId].configure
    return None


def getRoomMinCoin(roomId):
    roomConf = getRoomConfigure(roomId)
    return roomConf['minCoin'] if roomConf else None


def getRoomMaxCoin(roomId):
    roomConf = getRoomConfigure(roomId)
    return roomConf['maxCoin'] if roomConf else None


def getRoomMutil(roomId):
    roomConf = getRoomConfigure(roomId)
    return roomConf['roomMutil'] if roomConf else None


def globalConfig():
    '''
    取得global.json的配置内容
    '''
    return ftcon.global_config


def serverTypeMap():
    '''
    取得服务类型和服务ID的配置, key为服务类型(SRV_TYPE_XXX), value 为服务ID的list
    '''
    return ftcon.server_type_map


def allServersMap():
    '''
    取得全部进程的定义,key为进程ID, value为进程信息的dict
    '''
    return ftcon.server_map


def serverId():
    '''
    当前进程的ID, 例如: GA00060001, UT01
    '''
    return globalConfig()['server_id']


def serverType():
    '''
    当前进程的类型, 例如: GA, UT
    '''
    return __datas['server_type']


def serverNum():
    '''
    当前进程的ID去掉类型后的部分, 例如: 00060001, 01
    '''
    return __datas['server_num']


def serverNumIdx():
    '''
    当前进程的ID去掉类型后的部分, 例如: 00060001, 01
    '''
    return __datas['server_num_idx']


def centerServerLogics():
    '''
    取得配置当中, CENTER定义的业务逻辑服务
    '''
    return __datas['center_server_logic']


def name():
    '''
    在poker.json中定义的name的值
    '''
    return __datas['name']


def corporation():
    '''
    在poker.json中定义的corporation的值
    '''
    return __datas['corporation']


def mode():
    '''
    运行模式, 在poker.json中定义的mode的值
    参考: RUN_MODE_ONLINE, RUN_MODE_SIMULATION, RUN_MODE_RICH_TEST, RUN_MODE_TINY_TEST
    '''
    return __datas['mode']


def pathBin():
    '''
    在poker.json中定义的output.path的值加上bin
    即PY文件的编译输出路径
    '''
    return __datas['bin_path']


def pathWebroot():
    '''
    在poker.json中定义的output.path的值加上webroot
    即WEBROOT的编译输出路径
    '''
    return __datas['webroot_path']


def httpDownload():
    '''
    在poker.json中定义的http.download的值
    '''
    return __datas['http_download']


def httpGame():
    '''
    在poker.json中定义的http.game的值
    '''
    return __datas['http_game']


def httpSdk():
    '''
    在poker.json中定义的http.sdk的值
    '''
    return __datas['http_sdk']


def httpSdkInner():
    '''
    在poker.json中定义的http.sdk.inner的值
    '''
    return __datas['http_sdk_inner']


def httpAvatar():
    '''
    在poker.json中定义的http.sdk.inner的值
    '''
    return __datas['http_avatar']


def httpGdss():
    '''
    全局数据同步中心的HTTP地址,例如: clientid的同步地址
    '''
    return __datas.get('http_gdss', 'http://gdss.touch4.me')


def httpOnlieGateWay():
    '''
    全局数据同步中心的HTTP地址,例如: clientid的同步地址
    '''
    return __datas.get('http_gateway', 'http://open.touch4.me')


def biReportGroupInfo():
    '''
    取得BI汇报的配置中, 对应汇报类型rec_type的分组个数
    '''
    return __datas['bireportgroup']


def enableTestHtml():
    '''
    判定是否开启测试页面, 通常线上服务是关闭的
    '''
    return __datas.get('enable_test_html', 0)


def isH5():
    '''
    判定是否运行于H5服务模式, H5模式TCP接入的是WEBSOCKET
    '''
    return ftcon.global_config.get('is_h5', 0)


def getUserConnIpPortList():
    '''
    取得客户端可接入的TCPIP的IP和端口号列表[(ip, port),(ip, port),(ip, port)...]
    '''
    srvs = serverTypeMap()
    ipports = srvs.getExtendAttr('ipports')
    if not ipports:

        ipdict = {}
        machines = ftcon.getConf('poker:machine')
        for m in machines.values():
            ipdict[m['internet']] = m['internet']
            ipdict[m['intranet']] = m['internet']

        ipports = []
        connids = srvs[SRV_TYPE_CONN][:]
        connids.sort()
        servers = allServersMap()
        for connid in connids:
            srvconn = servers[connid]
            ip = ipdict[srvconn['ip']]
            port = srvconn['protocols']['server']['co-tcp']
            ipports.append((ip, port))
        srvs.setExtendAttr('ipports', ipports)
    return ipports


def _dumpGdataInfo():
    ftlog.info('GLOBAL Setting Dump Begin')
    ftlog.info('GLOBAL name                    = %s' % (name()))
    ftlog.info('GLOBAL mode                    = %d' % (mode()))
    ftlog.info('GLOBAL corporation             = %s' % (corporation()))
    ftlog.info('GLOBAL server tid              = %s' % (serverId()))
    ftlog.info('GLOBAL server type             = %s' % (serverType()))
    ftlog.info('GLOBAL server num              = %s' % (serverNum()))
    ftlog.info('GLOBAL path bin                = %s' % (pathBin()))
    ftlog.info('GLOBAL path webroot            = %s' % (pathWebroot()))
    ftlog.info('GLOBAL http sdk                = %s' % (httpSdk()))
    ftlog.info('GLOBAL http sdk inner          = %s' % (httpSdkInner()))
    ftlog.info('GLOBAL http game               = %s' % (httpGame()))
    ftlog.info('GLOBAL http download           = %s' % (httpDownload()))
    ftlog.info('GLOBAL http gdss center        = %s' % (httpGdss()))
    ftlog.info('GLOBAL http gateway            = %s' % (httpOnlieGateWay()))

    #     for k, v in srvIdRoomIdListMap().items() :
    #         ftlog.info('GLOBAL serverid-roomid %s = %s\n' % (str(k), str(v)))
    #
    #     for k, v in roomIdDefineMap().items() :
    #         ftlog.info('GLOBAL roomid-define   %s = %s\n' % (str(k), str(v)))
    #
    #     for k, v in bigRoomidsMap().items() :
    #         ftlog.info('GLOBAL bigroomidmap    %s = %s\n' % (str(k), str(v)))
    ftlog.info('GLOBAL Setting Dump End')
