# -*- coding=utf-8 -*-

import freetime.util.log as ftlog
from poker.entity.biz import bireport
from poker.entity.dao import daoconst, daobase, userdata, gamedata
from poker.servers.util.direct import dbuser

EVENT_NAME_SYSTEM_REPAIR = 'SYSTEM_REPAIR'


class ChipNotEnoughOpMode(object):
    def __call__(self, *args, **argd):
        return self

    def __init__(self):
        self.NOOP = 0
        self.CLEAR_ZERO = 1


ChipNotEnoughOpMode = ChipNotEnoughOpMode()


def getChip(uid):
    return userdata.getAttr(uid, daoconst.ATT_CHIP)


def getCoin(uid):
    return userdata.getAttr(uid, daoconst.ATT_COIN)


def getDiamond(uid):
    return userdata.getAttr(uid, daoconst.ATT_DIAMOND)


def getCoupon(uid):
    return userdata.getAttr(uid, daoconst.ATT_COUPON)


def getUserChipAll(uid):
    '''
    取得用户的所有金币, 包含被带入的金币
    '''
    uchip = userdata.getAttr(uid, daoconst.ATT_CHIP)
    gchip1 = gamedata.getGameAttrInt(uid, 1, daoconst.ATT_TABLE_CHIP)  # TODO 就代码数据兼容, 可删除
    gchip8 = gamedata.getGameAttrInt(uid, 8, daoconst.ATT_TABLE_CHIP)  # TODO 就代码数据兼容, 可删除
    tchips = daobase.executeUserCmd(uid, 'HVALS', daoconst.HKEY_TABLECHIP + str(uid))
    allchip = uchip + gchip1 + gchip8
    if tchips:
        for x in tchips:
            if isinstance(x, (int, float)):
                allchip += int(x)
    return allchip


def getTableChip(uid, gameid, tableId):
    '''
    取得用户的table_chip
    返回:
        否则返回gamedata中的tablechip
    '''
    mkey = daoconst.HKEY_TABLECHIP + str(uid)
    mfield = str(tableId)
    value = daobase.executeUserCmd(uid, 'HGET', mkey, mfield)
    ftlog.debug('UserChip->get_table_chip', uid, gameid, tableId, 'result->', value)
    if not isinstance(value, (int, float)):
        return 0
    return int(value)


def getTableChipsAll(uid):
    '''
    取得用户的table_chip
    返回:
        所有的tablechip
    '''
    mkey = daoconst.HKEY_TABLECHIP + str(uid)
    value = daobase.executeUserCmd(uid, 'HGETALL', mkey)
    ftlog.debug('UserChip->getTableChipsAll', uid, 'result->', value)
    return value


def delTableChips(uid, tableIdList):
    '''
    取得用户的table_chip
    返回:
        所有的tablechip
    '''
    value = 0
    if tableIdList:
        for tid in tableIdList:
            moveAllTableChipToChip(uid, 9999, 'TABLE_TCHIP_TO_CHIP', 0, None, int(tid))
        mkey = daoconst.HKEY_TABLECHIP + str(uid)
        value = daobase.executeUserCmd(uid, 'HDEL', mkey, *tableIdList)
    return value


def moveAllChipToTableChip(uid, gameid, eventId, intEventParam, clientId, tableId):
    '''
    转移用户所有的chip至tablechip
    参考: set_tablechip_to_range
    '''
    return _setTableChipToRange(uid, gameid, -1, -1, eventId, intEventParam, clientId, tableId)


def moveAllTableChipToChip(uid, gameid, eventId, intEventParam, clientId, tableId):
    '''
    转移用户所有的tablechip至chip
    参考: set_tablechip_to_range
    '''
    return _setTableChipToRange(uid, gameid, 0, 0, eventId, intEventParam, clientId, tableId)


def setTableChipToN(uid, gameid, tablechip, eventId, intEventParam, clientId, tableId):
    '''
    设置用户的tablechip至传入的值
    参考: set_tablechip_to_range
    '''
    return _setTableChipToRange(uid, gameid, tablechip, tablechip, eventId, intEventParam, clientId, tableId)


def setTableChipToBigThanN(uid, gameid, tablechip, eventId, intEventParam, clientId, tableId):
    '''
    设置用户的tablechip大于等于传入的值
    参考: set_tablechip_to_range
    '''
    return _setTableChipToRange(uid, gameid, tablechip, -1, eventId, intEventParam, clientId, tableId)


def setTableChipToNIfLittleThan(uid, gameid, tablechip, eventId, intEventParam, clientId, tableId):
    '''
    如果用户的tablechip小于传入的值, 至那么设置tablechip至传入的值
    参考: set_tablechip_to_range
    '''
    return _setTableChipToRange(uid, gameid, tablechip, -2, eventId, intEventParam, clientId, tableId)


def setTablechipNearToNIfLittleThan(uid, gameid, tablechip, eventId, intEventParam, clientId, tableId):
    '''
    tablechip 小于 n 时, 让 tablechip 尽量接近 n
    参考: set_tablechip_to_range
    '''
    return _setTableChipToRange(uid, gameid, -2, tablechip, eventId, intEventParam, clientId, tableId)


def setTableChipToRange(uid, gameid, _min, _max, eventId, intEventParam, clientId, tableId):
    '''
    chip与tablechip转换
    使得tablechip在 [_min, _max] 范围内尽量大。
    _min, _max 正常取值范围：>= 0
    特殊取值，代表redis中的当前值：
        -1: chip+tablechip
        -2: tablechip
        -3: chip
    否则设置gamedata中的tablechip
    返回: (table_chip_final, user_chip_final, delta_chip)
        table_chip_final 最终的tablechip数量
        user_chip_final 最终的userchip数量
        delta_chip 操作变化的数量
    '''
    return _setTableChipToRange(uid, gameid, _min, _max, eventId, intEventParam, clientId, tableId)


def _setTableChipToRange(uid, gameid, _min, _max, eventId, intEventParam, clientId, tableId):
    assert (isinstance(_min, int) and (_min >= 0 or _min in (-1, -2, -3)) and
            isinstance(_max, int) and (_max >= 0 or _max in (-1, -2, -3)))

    rfield = str(tableId)
    rhashkey = daoconst.HKEY_TABLECHIP + str(uid)

    tdelta, tfinal, tfixed, delta, final, fixed, appId, numberClientId = \
        dbuser._setTableChipToRange(uid, gameid, _min, _max, eventId, intEventParam,
                                    clientId, tableId, rhashkey, rfield)

    ftlog.debug('UserChip->set_tablechip_to_range', uid, gameid, _min, _max,
                eventId, intEventParam, clientId, tableId, rhashkey,
                'result->', tdelta, tfinal, tfixed, delta, final, fixed)

    args = {}
    args['clientId'] = clientId
    args['appId'] = appId
    args['_min'] = _min
    args['_max'] = _max

    if tfixed != 0:
        bireport.reportBiChip(uid, tfixed, tfixed, 0, EVENT_NAME_SYSTEM_REPAIR,
                              numberClientId, gameid, appId, intEventParam,
                              daoconst.CHIP_TYPE_TABLE_CHIP, argdict=args)
    if fixed != 0:
        bireport.reportBiChip(uid, fixed, fixed, 0, EVENT_NAME_SYSTEM_REPAIR,
                              numberClientId, gameid, appId, intEventParam,
                              daoconst.CHIP_TYPE_CHIP, argdict=args)
    if tdelta != 0:
        bireport.reportBiChip(uid, tdelta, tdelta, tfinal, eventId,
                              numberClientId, gameid, appId, intEventParam,
                              daoconst.CHIP_TYPE_TABLE_CHIP, argdict=args)
    if delta != 0:
        bireport.reportBiChip(uid, delta, delta, final, eventId,
                              numberClientId, gameid, appId, intEventParam,
                              daoconst.CHIP_TYPE_CHIP, argdict=args)

    return tfinal, final, delta


def _incrUserChipFiled(uid, gameid, deltaCount, lowLimit, highLimit, chipNotEnoughOpMode, eventId, chipType,
                       intEventParam, clientId, tableId=0):
    assert (isinstance(uid, int))
    assert (isinstance(gameid, int))
    assert (isinstance(deltaCount, int))
    assert (isinstance(lowLimit, int))
    assert (isinstance(highLimit, int))
    assert (isinstance(chipNotEnoughOpMode, int))
    assert (isinstance(chipType, int))

    if chipType == daoconst.CHIP_TYPE_CHIP:
        filed = daoconst.ATT_CHIP
        mkey = daoconst.HKEY_USERDATA + str(uid)
    elif chipType == daoconst.CHIP_TYPE_COIN:
        filed = daoconst.ATT_COIN
        mkey = daoconst.HKEY_USERDATA + str(uid)
    elif chipType == daoconst.CHIP_TYPE_DIAMOND:
        filed = daoconst.ATT_DIAMOND
        mkey = daoconst.HKEY_USERDATA + str(uid)
    elif chipType == daoconst.CHIP_TYPE_COUPON:
        filed = daoconst.ATT_COUPON
        mkey = daoconst.HKEY_USERDATA + str(uid)
    elif chipType == daoconst.CHIP_TYPE_TABLE_CHIP:
        mkey = daoconst.HKEY_TABLECHIP + str(uid)
        filed = str(tableId)
    else:
        raise Exception('UserChip unknow chipType of ' + str(chipType))

    trueDelta, finalCount, fixed, appId, numberClientId = dbuser._incrUserDatasLimit(uid, filed, deltaCount, lowLimit,
                                                                                     highLimit, chipNotEnoughOpMode,
                                                                                     mkey)

    ftlog.debug('UserChip->incr_user_chip_filed', uid, gameid, deltaCount, lowLimit, highLimit,
                chipNotEnoughOpMode, eventId, chipType, mkey, filed,
                'result->', trueDelta, finalCount, fixed)
    args = {}
    args['clientId'] = clientId
    args['appId'] = appId
    args['deltaCount'] = deltaCount
    args['lowLimit'] = lowLimit
    args['highLimit'] = highLimit
    args['chipType'] = chipType
    args['mode'] = chipNotEnoughOpMode

    if fixed != 0:
        bireport.reportBiChip(uid, fixed, fixed, 0, EVENT_NAME_SYSTEM_REPAIR,
                              numberClientId, gameid, appId, intEventParam, chipType, argdict=args)
    if trueDelta != 0 or deltaCount == 0:
        bireport.reportBiChip(uid, deltaCount, trueDelta, finalCount, eventId,
                              numberClientId, gameid, appId, intEventParam, chipType, argdict=args)
    return trueDelta, finalCount


def incrTableChip(uid, gameid, deltaCount, chipNotEnoughOpMode, eventId, intEventParam, clientId, tableId):
    '''
    对用户的tablechip进行INCR操作
    否则设置gamedata中的tablechip
    参考: incr_chip
    '''
    return _incrUserChipFiled(uid, gameid, deltaCount, -1, -1,
                              chipNotEnoughOpMode, eventId, daoconst.CHIP_TYPE_TABLE_CHIP,
                              intEventParam, clientId, tableId)


def incrTableChipLimit(uid, gameid, deltaCount, lowLimit, highLimit, chipNotEnoughOpMode, eventId, intEventParam,
                       clientId, tableId):
    '''
    对用户的tablechip进行INCR操作
    否则设置gamedata中的tablechip
    参考: incr_chip_limit
    '''
    return _incrUserChipFiled(uid, gameid, deltaCount, lowLimit, highLimit,
                              chipNotEnoughOpMode, eventId, daoconst.CHIP_TYPE_TABLE_CHIP,
                              intEventParam, clientId, tableId)


def incrChipLimit(uid, gameid, deltaCount, lowLimit, highLimit, chipNotEnoughOpMode, eventId, intEventParam, clientId):
    '''
    对用户的金币进行INCR操作
    @param uid: userId
    @param gameid: 游戏ID
    @param deltaCount: 变化的值可以是负数
    @param lowLimit 用户最低金币数，-1表示没有最低限制
    @param highLimit 用户最高金币数，-1表示没有最高限制
    @param mode: 当INCR动作会变成负数时的处理模式, 0表示不进行操作; 1会给金币清零
    @param eventId: 触发INCR的事件ID
    @param argdict: 需要根据事件传入intEventParam
    @return (trueDelta, final) trueDelta表示实际变化的值, final表示变化后的最终数量

    地主收房间服务费示例
    地主每玩完一局需要收服务费, 对用户金币没有上下限，如果用户的金币不够服务费就收取用户所有金币, 所以mode=ChipNotEnoughOpMode.CLEAR_ZERO
    用户10001当前金币为100, 在地主601房间(服务费为500)玩了一局, 收服务费代码为
    trueDelta, final = UserProps.incr_chip_limit(10001, 6, -500, -1, -1,
                                                            ChipNotEnoughOpMode.CLEAR_ZERO,
                                                            BIEvent.ROOM_GAME_FEE, roomId=601)
    此时trueDelta=-100, final=0

    地主收报名费示例
    用户10001当前金币为100, 报名610房间的比赛(需要报名费1000金币), 对用户金币没有上下限, 报名费不足则不处理，所以mode=ChipNotEnoughOpMode.NOOP
    trueDelta, final = UserProps.incr_chip_limit(10001, 6, -1000, -1, -1,
                                                            ChipNotEnoughOpMode.NOOP,
                                                            BIEvent.MATCH_SIGNIN_FEE, roomId=610)
    if trueDelta == -1000:
        # 收取报名费成功进行报名操作
        pass
    else:
        # 报名费不足，给客户端返回错误
        pass

    有上下限的示例
    在地主601房间最低准入为1000金币，扔鸡蛋价格为10金币，用户10001的当前金币为1000, 此时的delta为10下限为1010, 没有上限
    trueDelta, final = UserProps.incr_chip_limit(10001, 6, -10, 1010, -1,
                                                            ChipNotEnoughOpMode.NOOP,
                                                            BIEvent.EMOTICON_EGG_CONSUME, roomId=610)
    if trueDelta == -10:
        # 收取扔鸡蛋金币成功
        pass
    else:
        # 扔鸡蛋金币不足，给客户端返回错误
        pass
    '''
    return _incrUserChipFiled(uid, gameid, deltaCount, lowLimit, highLimit,
                              chipNotEnoughOpMode, eventId, daoconst.CHIP_TYPE_CHIP,
                              intEventParam, clientId, 0)


def incrChip(uid, gameid, deltaCount, chipNotEnoughOpMode, eventId, intEventParam, clientId):
    '''
    对用户的金币进行INCR操作
    @param uid: userId
    @param gameid: 游戏ID
    @param deltaCount: 变化的值可以是负数
    @param chipNotEnoughOpMode: 当INCR动作会变成负数时的处理模式, 0表示不进行操作; 1会给金币清零
    @param eventId: 触发INCR的事件ID
    @param argdict: 需要根据事件传入intEventParam
    @return (trueDelta, final) trueDelta表示实际变化的值, final表示变化后的最终数量
    参考incr_chip_limit的调用，此方法相当于用lowLimit, highLimit都是-1去调用incr_chip_limit
    '''
    return _incrUserChipFiled(uid, gameid, deltaCount, -1, -1,
                              chipNotEnoughOpMode, eventId, daoconst.CHIP_TYPE_CHIP,
                              intEventParam, clientId, 0)


def incrCoin(uid, gameid, deltaCount, chipNotEnoughOpMode, eventId, intEventParam, clientId):
    '''
    对用户的COIN进行INCR操作
    参考: incr_chip
    '''
    return _incrUserChipFiled(uid, gameid, deltaCount, -1, -1,
                              chipNotEnoughOpMode, eventId, daoconst.CHIP_TYPE_COIN,
                              intEventParam, clientId, 0)


def incrDiamond(uid, gameid, deltaCount, chipNotEnoughOpMode, eventId, intEventParam, clientId):
    '''
    对用户的钻石进行INCR操作
    参考: incr_chip
    '''
    return _incrUserChipFiled(uid, gameid, deltaCount, -1, -1,
                              chipNotEnoughOpMode, eventId, daoconst.CHIP_TYPE_DIAMOND,
                              intEventParam, clientId, 0)


def incrCoupon(uid, gameid, deltaCount, chipNotEnoughOpMode, eventId, intEventParam, clientId):
    '''
    对用户的兑换券进行INCR操作
    参考: incr_chip
    '''
    return _incrUserChipFiled(uid, gameid, deltaCount, -1, -1,
                              chipNotEnoughOpMode, eventId, daoconst.CHIP_TYPE_COUPON,
                              intEventParam, clientId, 0)
