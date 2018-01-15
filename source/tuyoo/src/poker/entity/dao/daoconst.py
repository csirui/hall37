# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
from poker.entity.dao import dataschema
from poker.util import city_locator

OFFLINE = 0  # 用户不在线
ONLINE = 1  # 用户在线

ATT_CHIP = 'chip'
ATT_COIN = 'coin'
ATT_DIAMOND = 'diamond'
ATT_COUPON = 'coupon'
ATT_TABLE_CHIP = 'tablechip'
ATT_EXP = 'exp'
ATT_CHARM = 'charm'
ATT_NAME = 'name'
ATT_TRU_NAME = 'truename'
ATT_TABLE_ID = 'tableId'
ATT_SEAT_ID = 'seatId'
ATT_CLIENT_ID = 'clientId'
ATT_APP_ID = 'appId'

HKEY_USERDATA = 'user:'
HKEY_GAMEDATA = 'gamedata:'
HKEY_STATEDATA = 'statedata:'
HKEY_ONLINE_STATE = 'os:'
HKEY_ONLINE_LOC = 'ol:'
HKEY_PLAYERDATA = 'playerdata:'
HKEY_TABLECHIP = 'tablechip:'
HKEY_TABLEDATA = 'tabledata:%d:%d'

FILTER_KEYWORD_FIELDS = {ATT_NAME, ATT_TRU_NAME}
FILTER_MUST_FUNC_FIELDS = {ATT_CHIP, ATT_DIAMOND, ATT_COIN, ATT_COUPON, ATT_CHARM}

OLD_COUPON_ITEMID = '50'
VIP_ITEMID = '88'

CHIP_NOT_ENOUGH_OP_MODE_NONE = 0
CHIP_NOT_ENOUGH_OP_MODE_CLEAR_ZERO = 1

CHIP_TYPE_CHIP = 1  # 金币
CHIP_TYPE_TABLE_CHIP = 2  # TABLE_CHIP
CHIP_TYPE_COIN = 3  # COIN
CHIP_TYPE_DIAMOND = 4  # DIAMODN
CHIP_TYPE_COUPON = 5  # COUPON
CHIP_TYPE_ITEM = 6  # ITEM
CHIP_TYPE_ALL = (
    CHIP_TYPE_CHIP, CHIP_TYPE_TABLE_CHIP, CHIP_TYPE_COIN, CHIP_TYPE_DIAMOND, CHIP_TYPE_COUPON, CHIP_TYPE_ITEM)

###############################################################################
# 数据或业务对象缓存的最大值
###############################################################################
DATA_CACHE_SIZE = 600

###############################################################################
# BI 数据库数据键值定义
###############################################################################
BI_KEY_GCOIN = 'GCOIN:%s'
BI_KEY_USER_ONLINES = 'count:user:onlines'
BI_KEY_ROOM_ONLINES = 'count:room:onlines%d'


###############################################################################
# GEO 数据库数据键值定义
###############################################################################
@dataschema.redisDataSchema
class GameGeoSchema(dataschema.DataSchema):
    REDIS_KEY = 'offline_geo:%d'  # HSET 游戏内道具数据


###############################################################################
# ITEM 数据库数据键值定义
###############################################################################
@dataschema.redisDataSchema
class GameItemSchema(dataschema.DataSchema):
    REDIS_KEY = 'item2:%d:%d'  # HSET 游戏内道具数据


###############################################################################
# TASK 数据库数据键值定义
###############################################################################
@dataschema.redisDataSchema
class GameTaskSchema(dataschema.DataSchema):
    REDIS_KEY = 'task2:%d:%d'  # HSET 游戏内道具数据


###############################################################################
# EXCHANGE 数据库数据键值定义
###############################################################################
@dataschema.redisDataSchema
class GameExchangeSchema(dataschema.DataSchema):
    REDIS_KEY = 'eo:%d:%d'  # HSET 游戏内道具数据


###############################################################################
# ONLINE 数据库数据键值定义
###############################################################################
ONLINE_KEY_ALLKEYS = 'onlinelist_allkeys'
ONLINE_KEY_USERS = 'onlinelist:users'
ONLINE_KEY_LIST = 'onlinelist:%s:%s'
###############################################################################
# PAY 数据库数据键值定义
###############################################################################
PAY_KEY_CTY = 'cty:%s:%s'
PAY_KEY_EXCHANGE_ID = 'global.exchangeId'
PAY_KEY_GAME_ORDER_ID = 'global.gameOrderid'


@dataschema.redisDataSchema
class GameOrderSchema(dataschema.DataSchema):
    REDIS_KEY = 'gameOrder:%s'  # HSET 游戏内订单数据

    ORDERID = ('orderId', dataschema.DATA_TYPE_STR, '')
    PLATFORMORDERID = ('platformOrderId', dataschema.DATA_TYPE_STR, '')
    USERID = ('userId', dataschema.DATA_TYPE_INT, 0)
    GAMEID = ('gameId', dataschema.DATA_TYPE_INT, 0)
    PRODID = ('prodId', dataschema.DATA_TYPE_STR, '')
    COUNT = ('count', dataschema.DATA_TYPE_INT, 0)
    CREATETIME = ('createTime', dataschema.DATA_TYPE_INT, 0)
    UPDATETIME = ('updateTime', dataschema.DATA_TYPE_INT, 0)
    CLIENTID = ('clientId', dataschema.DATA_TYPE_STR, '')
    STATE = ('state', dataschema.DATA_TYPE_INT, 0)
    ERRORCODE = ('errorCode', dataschema.DATA_TYPE_INT, 0)
    CHARGEINFO = ('chargeInfo', dataschema.DATA_TYPE_DICT, {})


###############################################################################
# USER 数据库数据键值定义
###############################################################################
@dataschema.redisDataSchema
class UserOnlineGameSchema(dataschema.DataSchema):
    REDIS_KEY = 'og:%d'  # SADD 用户登录的游戏ID数据 


@dataschema.redisDataSchema
class UserLocationSchema(dataschema.DataSchema):
    REDIS_KEY = 'ol:%d'  # HSET 用户的location数据
    SEATID = ('seatId', dataschema.DATA_TYPE_INT, 0)  # 


@dataschema.redisDataSchema
class UserWeakSchema(dataschema.DataSchema):
    REDIS_KEY = 'weak:%s:%s:%d:%d'  # SETEX 用户的弱引用数据


@dataschema.redisDataSchema
class UserPlayTimeSchema(dataschema.DataSchema):
    REDIS_KEY = 'pt:%d'  # SETEX 用户的弱引用数据


@dataschema.redisDataSchema
class UserSessionSchema(dataschema.DataSchema):
    '''
    用户主数据,类型:HASH
    '''
    REDIS_KEY = 'session:%d'  # 数据主键
    '''
    在游戏当中使用的数据字段
    '''
    ONLINE_STATE = ('os', dataschema.DATA_TYPE_BOOLEAN, OFFLINE)  # 在线状态
    LAST_GAME = ('lg', dataschema.DATA_TYPE_INT, 0)  # 最后玩的游戏ID(插件的gameId)
    CLIENTID = ('ci', dataschema.DATA_TYPE_STR, '')  # 最后登录时的clientId
    IPADDRESS = ('ip', dataschema.DATA_TYPE_STR, '')  # 最后登录时的IP地址
    APPID = ('appId', dataschema.DATA_TYPE_INT, 0)  # 最后登录时的APPID
    DEVICEID = ('devId', dataschema.DATA_TYPE_STR, '')  # 最后登录时的deviceID
    CITYCODE = ('city', dataschema.DATA_TYPE_LIST, city_locator.DEFAULT_LOCATION)  # 最后登录时的城市代码数据
    CONN = ('conn', dataschema.DATA_TYPE_STR, '')  # 当前接入的CO进程的ID
    # 缓存的SESSION数据字段集合
    FIELD_GROUP_SESSION = (CLIENTID, IPADDRESS, APPID, DEVICEID, CITYCODE, CONN)


@dataschema.redisDataSchema
class UserDataSchema(dataschema.DataSchema):
    '''
    用户主数据,类型:HASH
    '''
    REDIS_KEY = 'user:%d'  # 数据主键
    '''
    在游戏当中使用的数据字段
    '''
    CHIP = ('chip', dataschema.DATA_TYPE_INT_ATOMIC, 0)  # 金币
    COIN = ('coin', dataschema.DATA_TYPE_INT_ATOMIC, 0)  # 老钻石
    DIAMOND = ('diamond', dataschema.DATA_TYPE_INT_ATOMIC, 0)  # 新钻石
    COUPON = ('coupon', dataschema.DATA_TYPE_INT_ATOMIC, 0)  # 奖券
    EXP = ('exp', dataschema.DATA_TYPE_INT_ATOMIC, 0)  # 经验值
    CHARM = ('charm', dataschema.DATA_TYPE_INT_ATOMIC, 0)  # 魅力值

    NAME = ('name', dataschema.DATA_TYPE_STR_FILTER, '')  # 昵称
    SEX = ('sex', dataschema.DATA_TYPE_BOOLEAN, 0)  # 性别
    ADDRESS = ('address', dataschema.DATA_TYPE_STR, '')  # 所在的地域
    PURL = ('purl', dataschema.DATA_TYPE_STR, '')  # 用户头像URL
    SNSID = ('snsId', dataschema.DATA_TYPE_STR, '')  # 第三方SNSID
    VIP360 = ('360.vip', dataschema.DATA_TYPE_STR, '')  # 360VIP信息
    VIP = ('vip', dataschema.DATA_TYPE_INT, 0)  # VIP级别
    CREATETIME = ('createTime', dataschema.DATA_TYPE_STR, '')  # 注册时间
    CHARGETOTAL = ('chargeTotal', dataschema.DATA_TYPE_FLOAT, 0.0)  # 充值RMB合计
    PAYCOUNT = ('payCount', dataschema.DATA_TYPE_INT, 0)  # 充值的次数
    FIRSTDAILYCHECKIN = ('firstDailyCheckin', dataschema.DATA_TYPE_INT, 0)  # 第一次登录
    LASTDAILYCHECKIN = ('lastDailyCheckin', dataschema.DATA_TYPE_INT, 0)  # 最后一次登录
    SET_NAME_SUM = ('set_name_sum', dataschema.DATA_TYPE_INT, 0)  # 昵称设置的此时
    SENDMEGIFT = ('sendMeGift', dataschema.DATA_TYPE_INT, 0)  # 是否发放启动资金
    ISYOUYIFUVIPUSER = ('isYouyifuVipUser', dataschema.DATA_TYPE_BOOLEAN, 0)  # 优易付VIP账号标志
    YOUYIFUVIPMSG = ('youyifuVipMsg', dataschema.DATA_TYPE_STR, '')  # 优易付VIP信息
    USEDALIPAY = ('used_alipay', dataschema.DATA_TYPE_INT, 0)  # 阿里支付信息

    EMAIL = ('email', dataschema.DATA_TYPE_STR, '')  # 邮箱
    PDEVID = ('pdevid', dataschema.DATA_TYPE_STR, '')  # 注册时的设备ID
    MDEVID = ('mdevid', dataschema.DATA_TYPE_STR, '')  # 注册时的设备ID
    ISBIND = ('isbind', dataschema.DATA_TYPE_BOOLEAN, 0)  # 是否已经绑定
    SOURCE = ('source', dataschema.DATA_TYPE_STR, '')  # 用户推广的来源
    SNSINFO = ('snsinfo', dataschema.DATA_TYPE_STR, '')  # SNS第三方扩展信息
    DAYANG = ('dayang', dataschema.DATA_TYPE_INT, 0)  # 大洋(已经废弃)
    IDCARDNO = ('idcardno', dataschema.DATA_TYPE_STR, '')  # 身份证号码
    TRUENAME = ('truename', dataschema.DATA_TYPE_STR, '')  # 真实姓名
    PHONENUMBER = ('phonenumber', dataschema.DATA_TYPE_STR, '')  # 手机号(兑换操作等输入的号码)
    DETECT_PHONENUMBER = ('detect_phonenumber', dataschema.DATA_TYPE_STR, '')  # 自动检测的手机号码
    LANG = ('lang', dataschema.DATA_TYPE_STR, '')  # 用户的客户端语言
    COUNTRY = ('country', dataschema.DATA_TYPE_STR, '')  # 用户的客户端国家
    SIGNATURE = ('signature', dataschema.DATA_TYPE_STR, '')  # 签名(大菠萝专用?)
    BEAUTY = ('beauty', dataschema.DATA_TYPE_INT, 0)  # 是否美女认证
    PASSWORD = ('password', dataschema.DATA_TYPE_STR, '')  # 密码
    BINDMOBILE = ('bindMobile', dataschema.DATA_TYPE_STR, '')  # 账号绑定的手机号码
    '''
    SESSION数据字段
    '''
    SESSION_APPID = ('sessionAppId', dataschema.DATA_TYPE_INT, 0)  # 最后登录时的APPID (老数据,过渡期后,将被废弃)
    SESSION_DEVID = ('sessionDevId', dataschema.DATA_TYPE_STR, '')  # 最后登录时的deviceID (老数据,过渡期后,将被废弃)
    SESSION_CLIENTID = ('sessionClientId', dataschema.DATA_TYPE_STR, '')  # 最后登录时的clientId (老数据,过渡期后,将被废弃)
    SESSION_IP = ('sessionClientIP', dataschema.DATA_TYPE_STR, '')  # 最后登录时的IP地址 (老数据,过渡期后,将被废弃)
    SESSION_CITY_CODE = (
        'city_code', dataschema.DATA_TYPE_LIST, city_locator.DEFAULT_LOCATION)  # 最后登录时的城市代码数据 (老数据,过渡期后,将被废弃)
    #     SESSION_SDK_REV = ('sessionClientSdkRev' , dataschema.DATA_TYPE_STR, '')  #
    #     SESSION_IDFA = ('sessionIdfa' , dataschema.DATA_TYPE_STR, '')  #
    #     SESSION_PHONE_TYPE = ('sessionPhoneType' , dataschema.DATA_TYPE_STR, '')  #
    #     SESSION_ICCID = ('sessionIccid' , dataschema.DATA_TYPE_STR, '')  #
    # 缓存的SESSION数据字段集合
    FIELD_GROUP_SESSION = (SESSION_CLIENTID, SESSION_IP, SESSION_APPID, SESSION_DEVID, SESSION_CITY_CODE, 'conn_dummy')
    '''
    再SDK中使用的数据字段或老旧的数据字段
    '''
    CHANGEPWDCOUNT = ('changePwdCount', dataschema.DATA_TYPE_INT, 0)  # 密码修改的次数
    STATE = ('state', dataschema.DATA_TYPE_INT, 0)  # 用户状态
    USERACCOUNT = ('userAccount', dataschema.DATA_TYPE_STR, '')  # 账号(类似第三方SNSID)
    CLIENTID = ('clientId', dataschema.DATA_TYPE_STR, '')  # 注册时的客户端ID
    APPID = ('appId', dataschema.DATA_TYPE_INT, 0)  # 注册时的APPID
    MAC = ('mac', dataschema.DATA_TYPE_STR, '')  # 设备的MAC地址
    IDFA = ('idfa', dataschema.DATA_TYPE_STR, '')  # 设备的IDFA号
    IMEI = ('imei', dataschema.DATA_TYPE_STR, '')  # 设备的IMEI号
    ANDROIDID = ('androidId', dataschema.DATA_TYPE_STR, '')  # 安卓设备的安卓ID
    UUID = ('uuid', dataschema.DATA_TYPE_STR, '')  # 设备中的UUID(途游主动生成)
    USERID = ('userId', dataschema.DATA_TYPE_INT, 0)  # 对应的途游USERID
    AGREEADDFRIEND = ('agreeAddFriend', dataschema.DATA_TYPE_BOOLEAN, 0)  # 是否统一添加好友
    STARID = ('starid', dataschema.DATA_TYPE_INT, 0)  # 明星斗地主的明星ID
    NEITUIGUANG_STATE = ('neituiguang:state', dataschema.DATA_TYPE_INT, 0)  # 内推广的状态
    AUTHORTOKEN = ('authorToken', dataschema.DATA_TYPE_STR, '')  #
