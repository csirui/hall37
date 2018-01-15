# -*- coding=utf-8
'''
Created on 2016年9月23日

@author: zhaol
'''
from difang.majiang2.table.table_config_define import MTDefine
from difang.majiang2.table_state.state import MTableState
from difang.majiang2.table_state_processor.extend_info import MTableStateExtendInfo
from difang.majiang2.table_state_processor.processor import MProcessor
from freetime.util import log as ftlog

"""
抢杠和的操作处理
情况：
一个人回头杠，可能有人和牌
本处理类只处理抢杠胡牌的情况，要处理的状态只有抢杠和一个，AI策略处理起来比较简单。
"""


class MQiangGangHuProcessor(MProcessor):
    def __init__(self, count):
        super(MQiangGangHuProcessor, self).__init__()
        self.__processors = [{"state": MTableState.TABLE_STATE_NEXT, "extendInfo": None, "response": 0} for _ in
                             range(count)]
        # 玩家数量
        self.__count = count
        # 开杠的那张牌
        self.__tile = 0
        # 杠牌的用户的座位号
        self.__cur_seat_id = 0
        # 杠牌用户当时的状态
        self.__gang_state = 0
        # 杠牌时pattern
        self.__gang_pattern = None
        # 杠牌时特殊的牌
        self.__special_tile = None
        # 杠牌的类型
        self.__style = 0
        # 抢杠胡的人的座位数组,在全部放弃后清空
        self.__qiang_gang_seats = []
        # 抢杠胡时如果抢的牌是赖子,需要显示为赖子,但是胡牌逻辑要按照正常胡的那张来算
        self.__magic_tile = 0

    @property
    def qiangGangSeats(self):
        return self.__qiang_gang_seats

    @property
    def style(self):
        return self.__style

    @property
    def magicTile(self):
        return self.__magic_tile

    @property
    def tile(self):
        return self.__tile

    @property
    def curSeatId(self):
        """获取当前座位号"""
        return self.__cur_seat_id

    @property
    def gangState(self):
        return self.__gang_state

    @property
    def gangPattern(self):
        return self.__gang_pattern

    @property
    def specialTile(self):
        return self.__special_tile

    def getSeatsBySchedule(self):
        """根据座位号，获取吃牌的座位号列表"""
        seats = []
        for index in range(1, self.__count):
            seats.append((self.curSeatId + index) % self.__count)
        ftlog.debug("getSeatsBySchedule self.curSeatId  = "
                    , self.curSeatId
                    , "self.count="
                    , self.__count
                    , "seats = "
                    , seats)
        return seats

    def getAutoDecideSeatsBySchedule(self):
        """根据座位号，获取托管的座位号列表"""
        seats = []
        for index in range(self.__count - 1):
            nextSeat = (self.curSeatId + index + 1) % self.__count
            if self.players[nextSeat].autoDecide or self.players[nextSeat].isTing() or (self.timeOut < 0) or (
                self.getResponseBySeatId(nextSeat) == 0):
                seats.append(nextSeat)
        return seats

    def getStateBySeatId(self, seatId):
        """根据seatId获取出牌状态
        """
        return self.__processors[seatId]['state']

    def getResponseBySeatId(self, seatId):
        """根据seatId获取响应状态"""
        return self.__processors[seatId]['response']

    def getState(self):
        """获取本轮出牌状态
        """
        state = 0
        for seat in range(self.__count):
            state = state | self.__processors[seat]['state']

        ftlog.debug('MQiangGangHuProcessor.getState return:', state)
        return state

    def reset(self):
        """重置数据"""
        self.__processors = [{"state": 0, "extendInfo": None, "response": 0} for _ in range(self.__count)]
        self.__tile = 0
        self.__magic_tile = 0
        self.__cur_seat_id = 0
        self.__qiang_gang_seats = []
        ftlog.debug('MQiangGangHuProcessor.reset now processors:', self.__processors)

    def resetSeatId(self, seatId):
        """重置某个座位，用户放弃"""
        self.__processors[seatId] = {"state": 0, "extendInfo": None, "response": 0}
        ftlog.debug('MQiangGangHuProcessor.resetSeatId now processors:', self.__processors)
        return True

    def initTile(self, tile, curSeat, gangState, gangPattern, style, specialTile=None, magicTile=None):
        """
        抢杠胡管理器保存杠的信息
        """
        ftlog.debug('MQiangGangHuProcessor.initTile will gang tile:', tile
                    , 'curSeat:', curSeat, 'gangState:', gangState,
                    'gangPattern:', gangPattern, 'specialTile', specialTile)
        self.__tile = tile
        if magicTile:
            self.__magic_tile = magicTile
        self.__cur_seat_id = curSeat
        self.__gang_state = gangState
        self.__gang_pattern = gangPattern
        self.__special_tile = specialTile
        self.__style = style

    def getExtendResultBySeatId(self, seatId):
        extendInfo = self.__processors[seatId]['extendInfo']
        return extendInfo

    def initProcessor(self, actionID, seatId, state, extendInfo=None, timeOut=9):
        """
        初始化处理器
        参数
            seatId - 座位号
            state - 状态集合，当前座位号可以做出的全部选择
        """
        ftlog.debug('MQiangGangHuProcessor.initProcessor seatId:', seatId, ' state:', state, ' extentdInfo:',
                    extendInfo)
        self.setActionID(actionID)
        self.__processors[seatId]['state'] = state
        self.__processors[seatId]['extendInfo'] = extendInfo
        # 用户未做出选择
        self.__processors[seatId]['response'] = 1
        if seatId not in self.__qiang_gang_seats:
            self.__qiang_gang_seats.append(seatId)
        self.setTimeOut(timeOut)
        ftlog.debug('MQiangGangHuProcessor.initProcessor end:', self.__processors)

    def updateProcessor(self, actionID, seatId, state, tile, pattern=None):
        """
        用户做出了选择，state为0，表示放弃
        用户的选择集合明确
        """
        if actionID != self.actionID:
            # 不是本轮处理的牌
            ftlog.debug('timeout dropcard processor update')
            return False

        ftlog.debug('MQiangGangHuProcessor.updateProcessor actionID:', actionID
                    , ' seatId:', seatId
                    , ' state:', state
                    , ' tile:', tile)

        #         if self.__processors[seatId]['response'] == 0:
        #             # 已经做过选择,再发送过来就不处理了
        #             ftlog.debug( 'MQiangGangHuProcessor.updateProcessor response = 0, already responsed' )
        #             return False
        self.__processors[seatId]['state'] = state
        # 用户已做出选择
        self.__processors[seatId]['response'] = 0
        ftlog.debug('MQiangGangHuProcessor.updateProcessor end:', self.__processors)
        return self.isBiggestPriority(state, seatId)

    def isBiggestPriority(self, state, seatId):
        """
        是否是最高优先级
        """
        seats = self.getSeatsBySchedule()
        curIndex = seats.index(seatId)
        if curIndex == 0:
            return True

        for index in range(curIndex):
            if self.__processors[seats[index]] == MTableState.TABLE_STATE_QIANGGANG:
                return False

        # 最高优先级    
        return True

    def hasAutoDecideAction(self, curSeat, trustTeeSet):
        """
        是否有自动托管的行为
        逆时针找到第一个抢杠和的人
        """
        seats = self.getAutoDecideSeatsBySchedule()
        for seat in seats:
            if self.__processors[seat]['state'] == MTableState.TABLE_STATE_QIANGGANG:
                return seat

        return MTDefine.INVALID_SEAT

    def allResponsed(self):
        """本轮出牌，所有人都已经响应
        """
        response = 0
        for seat in range(self.__count):
            response += self.__processors[seat]['response']
        return 0 == response

    def clearQiangGangSeats(self):
        """抢杠胡的人的座位数组"""
        self.__qiang_gang_seats = []


if __name__ == "__main__":
    dp = MQiangGangHuProcessor(4)
    exInfo = MTableStateExtendInfo()
    # exInfo.setExtend( {'peng': [[18, 18, 18]], 'pengTing': [{'tile': 18, 'ting': [{'winNo       des': [{'winTile': 17, 'pattern': [[17, 18, 19], [11, 11]], 'winTileCount': 3}], 'dropTile': 28}], 'pattern': [18, 18, 18]}], 'gang': [{'tile': 18, 'pattern': [18, 18, 18, 18], 'style': 1}], 'gangTing': [{'ti       le': 18, 'ting': [{'winNodes': [{'winTile': 26, 'pattern': [[26, 27, 28], [11, 11]], 'winTileCount': 2}, {'winTile': 29, 'pattern': [[27, 28, 29], [11, 11]], 'winTileCount': 2}], 'dropTile': 19}], 'style': 1,        'pattern': [18, 18, 18, 18]}]})
    exInfo.setExtend({'peng': [[18, 18, 18]], 'pengTing': [{'tile': 18, 'ting': [
        {'winNodes': [{'winTile': 17, 'pattern': [[17, 18, 19], [11, 11]], 'winTileCount': 3}], 'dropTile': 28}],
                                                            'pattern': [18, 18, 18]}]})
    dp.initProcessor(10, 0, 28, exInfo, 9)
