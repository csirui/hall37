# -*- coding=utf-8
'''
Created on 2016年11月18日
庄家规则
@author: zhangwei
'''
import sys

sys.path += [
    "/Volumes/Nick.kai.lee/cocos2dx/newserver/hall37/source/hengyang/src",
    "/Volumes/Nick.kai.lee/cocos2dx/newserver/hall37/source/difang/src",
    "/Volumes/Nick.kai.lee/cocos2dx/newserver/hall37/source/freetime",
    "/Volumes/Nick.kai.lee/cocos2dx/newserver/hall37/source/hall/src",
    "/Volumes/Nick.kai.lee/cocos2dx/newserver/hall37/source/tuyoo/src"]

from hengyangmj.win_rule.win_rule_hengyang import MWinRuleHengYang
from freetime.util import log as ftlog

if __name__ == "__main__":
    hengyang = MWinRuleHengYang()
    # result = hengyang.is_banbanhu([[1,2,2,2,2,6,7,8,9,11,12,13,14]])
    # result = hengyang.is_banbanhu([1,4,4,4,6,6,7,7,9,11,13,13,14])
    # result = hengyang.is_banbanhu([1,4,4,4,6,6,6,7,9,11,13,13,14])
    # ftlog.info("is_banbanhu?", result)

    # result = hengyang.is_xiaohu([[1,2,3,4,4,4,5,5,6,7,8,11,12,13]])
    # result = hengyang.is_xiaohu([[1,8,11,14,17,22,28,5,5,25,26,27]])
    result = hengyang.is_xiaohu([[1, 2, 3, 18, 18]])
    ftlog.info("is_xiaohu?", result)

    # result = hengyang.is_pengpenghu([[1,3,1,2,2,2,5,5,5,7,7,7,13,13]])
    # # ftlog.info("is_pengpenghu?", result)

    # result = hengyang.is_jiangjianghu([[19,12,22,2,12,22,5,15,25,8,18],[],[],[]])
    # ftlog.info("is_jiangjianghu?", result)
    #
    # ftlog.info("find_repeat_suit_info?", HYWinRuleFunction.find_repeat_suit_info([1,2,3,11,23,12,9,4,15]))

    # tiles = [[1,2,4,4,4,4,5,5,6,7,8,11,12,13],[],[],[]]
    # if hengyang.is_xiaohu(tiles):
    # 	result = hengyang.is_qingyise_inc(tiles)
    # 	ftlog.info("is_qingyise_inc?", result)

    # tiles = [[1,1,2,2,3,3,4,4,5,5,6,6,7,7],[],[],[]]
    # if hengyang.is_qixiaodui(tiles):
    # 	result = hengyang.is_qingyise_inc(tiles)
    # 	ftlog.info("is_qingyise_inc?", result)

    # tiles = [[2,2,2,2,5,5,5,5,8,8,8,8,12,12],[],[],[]]
    # if hengyang.is_jiangjianghu(tiles):
    # 	if hengyang.is_qixiaodui(tiles):
    # 		result = hengyang.is_qingyise_inc(tiles)
    # 		ftlog.info("is_qingyise_inc?", result)


    # tiles = [[8,8],[[1,2,3],[4,5,6]],[[1,1,1]],[ {"pattern":[7,7,7,7],"style":0} ] ]
    # if hengyang.is_quanqiuren(tiles):
    # 	result = hengyang.is_qingyise_inc(tiles)
    # 	ftlog.info("is_qingyise_inc?", result)


    # result = hengyang.is_menqing([[1,2,3,4,4,4,5,5,6,7,8,11,12,13],[],[],[]])
    # ftlog.info("is_menqing?", result)
    # a = 0|0b1000
    # a = a|0b10000000000000000
    # ftlog.info("is_menqing?", 0|0b10000000000000000,0b10000000000000000,a)

    # a = 0
    # b = 0b1
    # c = 0b10
    # f = 0b100
    # g = 0b1000
    # HYLog.debug("a,b,c,f,g?",a,b,c,f,g)
    # d = 0
    # d |= b
    # HYLog.debug("d?",d)
    # d |= c
    # HYLog.debug("d?",d)
    # d |= f
    # HYLog.debug("d?",d)
    # HYLog.debug("-----")
    # # d & f
    # HYLog.debug("d?",d & f)
    # # d & c
    # HYLog.debug("d?",d & c)
    #
    # HYLog.debug("d?",d & g)
    #
    # if 0 & 0b10:
    #        a = a ^ 0b1000
    # HYLog.debug("is_menqing?",3 & 2,0b10)

    # from hengyangmj.win_lose_result.kong_budget import HYKongBudget
    # budget = HYKongBudget()
    # # HYKongBudget.BudgetType.EXPOSED_KONG = 3
    # # HYLog.debug("sdfjlksdjfkl:",HYKongBudget.BudgetType.EXPOSED_KONG)
    #
    # a = [0,1,2,3,4,5,6,7]
    # b = a[(len(a)-5):]
    # c = a.pop(5)
    # HYLog.debug("is_menqing?",a,b,c)

    # class a(object):
    # 	def __init__(self):
    # 		self.__tttt = [1,2,3]
    #
    # 	@property
    # 	def tttt(self):
    # 		return self.__tttt
    #
    #
    # class b(a):
    # 	def __init__(self):
    # 		super(b, self).__init__()
    #
    # 	def done(self):
    # 		HYLog.info("sdfjkljsdlkfjskdfl:",self.tttt.remove(2),self.tttt)
    #
    # c = b()
    # c.done()

    # a = [0 for i in range(4)]
    # a =[]
    a = None
    b = a[0] if a and 0 < len(a) else 0
# for i in range(4):
# 	a[i] = a[i] or 10
