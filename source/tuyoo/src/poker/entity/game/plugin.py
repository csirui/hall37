# coding=UTF-8
'''游戏插件管理模块
'''

__author__ = ['Wang Tao', 'Zhou Hao']

import importlib
import sys

import freetime.util.log as ftlog
from freetime.entity.msg import MsgPack
from freetime.util.log import catchedmethod
from poker.entity.configure import configure
from poker.entity.configure import gdata
from poker.protocol import router

_DEBUG = 1
debug = ftlog.info


class TYPluginUtils(object):
    @classmethod
    def updateMsg(cls, msg=None, cmd=None, params=None, result=None, **other):
        if not msg:
            msg = MsgPack()
        if cmd:
            msg.setCmd(cmd)
        if params is not None:
            msg.setKey('params', params)
        if result is not None:
            msg.setKey('result', result)

        for k, v in other.items():
            msg.setKey(k, v)

        return msg

    @classmethod
    def mkdict(cls, **kwargs):
        return kwargs

    @classmethod
    def sendMessage(cls, gameId, targetUserIds, cmd, result, logInfo=True):
        if isinstance(targetUserIds, int):
            targetUserIds = [targetUserIds]
        msg = cls.updateMsg(cmd=cmd, result=result)
        msg.setResult('gameId', gameId)
        if logInfo:
            if _DEBUG:
                debug('|to targetUserIds:', targetUserIds, '|msg:', msg, caller=cls)
        else:
            ftlog.debug('|to targetUserIds:', targetUserIds, '|msg:', msg, caller=cls)
        router.sendToUsers(msg, targetUserIds)

    @classmethod
    def makeHandlers(cls, handlerClass, events):
        ''' ['EV_GAME_INIT'] => {'EV_GAME_INIT': handlerClass.EV_GAME_INIT}'''
        return dict([(ev, getattr(handlerClass, ev)) for ev in events])


class TYPlugin(object):
    def __init__(self, gameId, cfg):
        ftlog.info('TYPlugin << |gameId, cfg:', gameId, cfg, caller=self)
        self.gameId = gameId
        self.name, self.module_name, self.class_name, self.object_name = (
            cfg['name'], cfg['module'], cfg.get('class'), cfg.get('object'))

        old_mod = sys.modules.get(self.module_name)
        if old_mod:
            del sys.modules[self.module_name]
        self.old_mod = old_mod
        self.module = importlib.import_module(self.module_name)
        reload(self.module)

        if self.object_name:
            self.object = getattr(self.module, self.object_name)(gameId)
            self.handlers = getattr(self.object, cfg['handle'])(gameId) or {}
        else:
            self._class = getattr(self.module, self.class_name)
            self.handlers = getattr(self._class, cfg['handle'])(gameId) or {}

        ftlog.info('TYPlugin |', 'handler:', self.name, 'loaded:', cfg,
                   'old_mod:', id(old_mod), old_mod, 'new_mod:', id(self.module),
                   'module:', self.module, 'events:', self.handlers.keys(),
                   caller=self
                   )
        # if not self.handlers:
        #     raise Exception("no handlers: name: %s" % self.name)

    @catchedmethod
    def onReload(self):
        if hasattr(self.module, 'onReload'):
            ftlog.info("TYPlugin.onReload >>|plugin name:", self.name)
            self.module.onReload(self.gameId, self.old_mod)
            delattr(self, 'old_mod')
        elif hasattr(self.module, 'onReloadNew'):
            ftlog.info("TYPlugin.onReloadNew >>|plugin name:", self.name)
            self.module.onReloadNew(self.gameId, self.object)

    def __str__(self):
        return '<TYPlugin object %s(id: %s), event handlers: %s>' % (
            self.name, id(self), self.handlers.keys())

    def __repr__(self):
        return self.__str__()


class TYPluginCenter(object):
    plugins = {}  # key: gameId, value {name: TYPluginObj}
    config_reload_flag = {}  # key: gameId, value: last reaload configure uuid(default None)
    map_events = {}  # key: gameId; value: {event1: [handler1, handler2, ...], evnet2: [handler1, handler2, ...]}

    EV_CHAIN_STOP = 'EV_CHAIN_STOP'  # handler 函数返回此值，表示中断事件链执行

    @classmethod
    def event(cls, msg, gameId):
        """ 发布事件 """
        if gameId not in cls.map_events:
            return msg

        # cls.map_events = {
        #     8: {"EV_PLAYER_GAME_FRAME_END": [("Winner", onEvPlayerGameFrameEnd), ("Shark",onEvPlayerGameFrameEnd)]},
        #     30: {}
        # }

        cmd = msg.getCmd()
        action = msg.getParam('action')
        ev = (cmd, action) if action else cmd
        receiver_plugins = msg.getKey('receiver_plugins') or []
        for plugin_name, handler in cls.map_events[gameId].get(ev, []):
            if receiver_plugins and plugin_name not in receiver_plugins:
                continue
            if _DEBUG:
                debug('TYPluginCenter.event| run handler <<|gameId, ev, plugin:', gameId, ev, plugin_name)
            try:
                if handler(gameId, msg) == cls.EV_CHAIN_STOP:
                    if _DEBUG:
                        debug('TYPluginCenter.event| chain break |gameId, ev, plugin:', gameId, ev, plugin_name)
                    return msg
            except:
                ftlog.exception()
            if _DEBUG:
                debug('TYPluginCenter.event| run handler >>|gameId, ev, plugin:', gameId, ev, plugin_name)

        return msg

    @classmethod
    def evmsg(cls, gameId, cmd, params=None, result=None, receivers=None):
        msg = TYPluginUtils.updateMsg(cmd=cmd, params=params, result=result,
                                      receiver_plugins=receivers)
        return cls.event(msg, gameId)

    @classmethod
    def get_plugin(cls, name, gameId):
        return cls.plugins.get(gameId, {}).get(name)

    @classmethod
    @catchedmethod
    def reload(cls, gameId, handler_name='', handler_names=[], handlers_config=None):
        '''
        reload 某个 gameId 的插件

        @handlers_names: 指定要reload哪些plugin。不指定就reload所有（plugins越来越多，会比较慢）

        不管有没有指定 reload 哪些插件，都会重新 build 事件表。
        为什么不优化为只处理指定的plugins的事件？
        没有必要，性能瓶颈不在这，而且全部重新build一定不会出问题，而且的而且，那样做会增加复杂性。
        '''

        if not cls.needLoadPlugin():
            ftlog.info('reload >> |this type of server not need load plugin',
                       '|serverId, gameId:', gdata.serverId(), gameId, caller=cls)
            return

        if cls.isOtherGameServer(gameId):
            ftlog.info('reload >> |', 'do not reload in other game GR/GT',
                       '|serverId, gameId:', gdata.serverId(), gameId, caller=cls)
            return

        if not handlers_config:
            handlers_config = configure.getGameJson(gameId, 'plugins', {})
            if not handlers_config:
                return
                # handlers_config = dict([(hc['name'], hc) for hc in handlers_config])
        handlers_config_dict = dict([(hc['name'], hc) for hc in handlers_config['handlers']])
        ftlog.info('<< |', cls.plugins, handlers_config, caller=cls)

        if handler_name:
            handler_names = [handler_name]

        handlers_config_list = []  # to be reload
        cls.map_events[gameId] = {}  # 事件表
        if handler_names:
            for handler_name in handler_names:
                if handler_name in handlers_config_dict:
                    handlers_config_list.append(handlers_config_dict.get(handler_name))
                if handler_name in cls.plugins[gameId]:
                    del cls.plugins[gameId][handler_name]
        else:
            handlers_config_list = handlers_config['handlers']
            cls.plugins[gameId] = {}  # plugins 表

        # 先 reload modules
        plugins = cls.plugins[gameId]
        reloadPlugins = []
        for cfg in handlers_config_list:
            try:
                plugin = TYPlugin(gameId, cfg)
                if plugin.handlers:
                    plugins[cfg['name']] = plugin
                    reloadPlugins.append(plugin)
            except Exception as e:
                ftlog.exception(e)

        cls.buildEventMap(gameId, plugins, handlers_config, cls.map_events[gameId])

        ftlog.info("TYPluginCenter.reload | "
                   "reloadPlugins:", [plugin.name for plugin in reloadPlugins])

        # onReload 时可能会有阻塞操作而让出CPU, 这时有可能会产生新的事件
        # 如果在 onReload 后才 buildEventMap,则这个事件会丢(因为eventMap在build之前是空的)
        # 所以,把 onReload 移到 build Event Map 之后
        for plugin in reloadPlugins:
            try:
                plugin.onReload()
            except Exception as e:
                ftlog.exception(e)

    @classmethod
    @catchedmethod
    def unload(cls, gameId, handler_names=None):
        """卸载插件"""

        for name in handler_names:
            plugin = cls.get_plugin(name, gameId)
            if hasattr(plugin.module, "onUnload"):
                try:
                    plugin.module.onUnload(gameId)
                except Exception:
                    ftlog.error("TYPluginCenter.unload"
                                "|gameId, name:", gameId, name)
            del cls.plugins[gameId][name]

        handlers_config = configure.getGameJson(gameId, 'plugins', {})
        cls.buildEventMap(gameId, cls.plugins[gameId], handlers_config, cls.map_events[gameId])

    @classmethod
    def buildEventMap(cls, gameId, plugins, handlers_config, map_events):
        # 然后 build 事件处理表
        # step 1: 有些事件是有顺序要求的，先按顺序要求，构架一个架子
        for event, plugin_names in handlers_config['event_seq'].items():
            if ' ' in event:
                event = tuple(event.split())
            map_events[event] = []
            for plugin_name in plugin_names:
                if plugin_name == '...':  # 事件顺序分割符号
                    map_events[event].append('...')
                    continue
                plugin = plugins.get(plugin_name)
                if plugin and event in plugin.handlers:
                    map_events[event].append((plugin_name, plugin.handlers[event]))

        # step 2: 把 event_seq 配置中未明确的事件，加到 '...' 的位置
        for plugin_name, plugin in plugins.items():
            for event, handler in plugin.handlers.items():
                if event not in map_events:
                    map_events[event] = []
                if not (plugin_name, handler) in map_events[event]:  # 加过的不再加
                    if '...' in map_events[event]:  # 如果包含事件顺序分割符，则普通事件添加到分割符前面
                        map_events[event].insert(map_events[event].index('...'), (plugin_name, handler))
                    else:
                        map_events[event].append((plugin_name, handler))

        # 最后把这个 '...' 标志删除掉
        for event_handlers in cls.map_events[gameId].values():
            if '...' in event_handlers:
                event_handlers.remove('...')

        ftlog.info('buildEventMap >> |', plugins, caller=cls)
        ftlog.info('buildEventMap >> |', map_events, caller=cls)

    @classmethod
    def isOtherGameServer(cls, gameId):
        '''判断是否为别的游戏的GR/GT,如果是,不加载当前游戏的 plugins'''
        serverType, serverId = gdata.serverType(), gdata.serverId()
        if serverType not in (gdata.SRV_TYPE_ROOM, gdata.SRV_TYPE_TABLE):
            return False

        if '-' in serverId:
            serverGameId = int(serverId.split('-')[0][2:])
        elif serverType == gdata.SRV_TYPE_ROOM:
            serverGameId = int(serverId[2:-4])
        elif serverType == gdata.SRV_TYPE_TABLE:
            serverGameId = int(serverId[2:-7])
        return serverGameId != gameId

    @classmethod
    def needLoadPlugin(cls):
        return gdata.serverType() in {
            gdata.SRV_TYPE_ROOM,
            gdata.SRV_TYPE_TABLE,
            gdata.SRV_TYPE_UTIL,
            gdata.SRV_TYPE_HTTP,
            gdata.SRV_TYPE_CENTER,
        }
