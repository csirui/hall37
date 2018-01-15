# -*- coding=utf-8 -*-
import freetime.util.log as ftlog
from hall.servers.util import activity5_handler
from poker.util import strutil

# 测试
gameId = 6
userId = 10001
clientId = 'Android_3.71_tyOneKey,tyAccount,tyGuest.yisdkpay4.0-hall6.wandou.tu'

datas = activity5_handler._doActivity5ActMsgList(6, 10001, clientId)
ftlog.info('_doActivity5ActMsgList=', strutil.dumps(datas))

datas = activity5_handler._doActivity5CityMsgList(6, 10001, clientId)
ftlog.info('_doActivity5CityMsgList=', strutil.dumps(datas))

datas = activity5_handler._doActivity5PrizeMsgList(6, 10001, clientId)
ftlog.info('_doActivity5PrizeMsgList=', strutil.dumps(datas))

datas = activity5_handler._doActivity5ExchangeItemList(6, 10001, clientId)
ftlog.info('_doActivity5ExchangeItemList=', strutil.dumps(datas))
