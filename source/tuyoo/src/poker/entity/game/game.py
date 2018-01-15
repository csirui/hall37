# coding=UTF-8
'''
游戏基类
'''
from poker.entity.configure import gdata
from poker.entity.events.tyeventbus import TYEventBus
from poker.entity.robot.robot import TYRobotManager

__author__ = [
    '"Zqh"',
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]


class _TYGameCallAble(type):
    def __init__(self, name, bases, dic):
        super(_TYGameCallAble, self).__init__(name, bases, dic)
        self.instance = None

    def __call__(self, gameId=0, *args, **kwargs):
        v = None
        if gameId > 0:
            v = gdata.games()[gameId]
        else:
            if self.instance is None:
                self.instance = super(_TYGameCallAble, self).__call__(*args, **kwargs)
            v = self.instance
        return v


class TYGame(object):
    __metaclass__ = _TYGameCallAble
    PLAY_COUNT = 'playGameCount'  # 游戏局数
    WIN_COUNT = 'winGameCount'  # 胜利局数

    def __init__(self, *args, **argds):
        self._eventBus = TYEventBus()
        self._robotmgr = TYRobotManager()
        self._packageName = None  # 此变量由系统自动赋值, 其值为当前游戏的主package的名字

    def gameId(self):
        '''
        取得当前游戏的GAMEID, int值
        '''
        raise NotImplementedError('')

    def newTable(self, room, tableId):
        '''
        此方法由系统进行调用
        更具给出的房间的基本定义信息, 创建一个TYTable的实例
        其必须是 poker.entity.game.table.TYTable的子类
        room 桌子所属的房间的TYRoom实例
        tableId 新桌子实例的ID
        '''
        raise NotImplementedError('')

    def initGameBefore(self):
        '''
        此方法由系统进行调用
        游戏初始化的预处理
        '''

    def initGame(self):
        '''
        此方法由系统进行调用
        游戏自己初始化业务逻辑模块, 例如: 初始化配置, 建立事件中心等
        执行的时序为:  首先调用所有游戏的 initGameBefore()
                    再调用所有游戏的 initGame()
                    最后调用所有游戏的 initGameAfter()
        '''

    def initGameAfter(self):
        '''
        此方法由系统进行调用
        游戏初始化的后处理
        '''

    def getInitDataKeys(self):
        '''
        取得游戏数据初始化的字段列表
        '''
        return []

    def getInitDataValues(self):
        '''
        取得游戏数据初始化的字段缺省值列表
        '''
        return []

    def getGameInfo(self, userId, clientId):
        '''
        取得当前用户的游戏账户信息dict
        '''
        return {}

    def getDaShiFen(self, userId, clientId):
        '''
        取得当前用户的游戏账户的大师分信息
        '''
        return {}

    def getPlayGameCount(self, userId, clientId):
        '''
        取得当前用户游戏总局数
        '''
        return 0

    def getPlayGameInfoByKey(self, userId, clientId, keyName):
        '''
        取得当前用户的游戏信息
        key - 要取得的信息键值，枚举详见TYGame类的宏定义
        '''
        return None

    def createGameData(self, userId, clientId):
        '''
        此方法在UTIL服务中调用
        初始化该游戏的所有的相关游戏数据
        包括: 主游戏数据gamedata, 道具item, 勋章medal等
        返回主数据的键值和值列表
        '''
        return [], []

    def loginGame(self, userId, gameId, clientId, iscreate, isdayfirst):
        '''
        此方法在UTIL服务中调用
        用户登录一个游戏, 游戏自己做一些其他的业务或数据处理
        例如: 1. IOS大厅不发启动资金的补丁, 
             2. 麻将的记录首次登录时间
             3. 游戏插件道具合并至大厅道具
        '''
        pass

    def getEventBus(self):
        '''
        取得当前游戏的事件中心
        '''
        return self._eventBus

    def getRobotManager(self):
        '''
        取得游戏的机器人管理器
        一定是 : TYRobotManager 的实例
        '''
        return self._robotmgr

    def getTodoTasksAfterLogin(self, userId, gameId, clientId, isdayfirst):
        '''
        获取登录后的todotasks列表
        '''
        return []

    def isWaitPigTable(self, userId, room, tableId):
        '''
        检查是否是杀猪状态的桌子, 缺省为非杀猪状态的桌子
        '''
        return 0

    def canJoinGame(self, userId, roomId, tableId, seatId):
        '''
        检查参数描述的桌子是否可加入游戏
        eg:
            现金桌可加入则返回1
            MTT比赛桌不可加入则返回0
        '''
        return 0

    def getTuyooRedEnvelopeShareTask(self, userId, clientId, _type):
        '''
        获取可用的途游红包分享
        _type: 表示红包类型： all | register | login
        返回值不为None，则有待发送的红包
        返回值为None，则没哟独爱发送的红包

        '''
        return None

    def sendTuyooRedEnvelopeCallBack(self, userId, clientId, redEnvelopeId):
        '''
        途游红包的发送回调
        红包ID redEnvelopeId
        '''
        pass

    def checkFriendTable(self, ftId):
        '''
        检测自建桌ID是否继续使用，如果不使用，将回收次ftId
        0 - 有效
        1 - 无效
        
        返回值：
        False - 无用
        True - 有用
        '''
        return False

    def enterFriendTable(self, userId, gameId, clientId, ftId):
        """进入自建桌，插件实现具体功能"""
        pass
