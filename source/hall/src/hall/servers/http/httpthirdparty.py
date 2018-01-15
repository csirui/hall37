# -*- coding=utf-8
'''
Created on 2015年8月4日

@author: zhaojiangang
'''
import time

from hall.servers.common.base_http_checker import BaseHttpMsgChecker
from poker.protocol import runhttp
from poker.protocol.decorator import markHttpHandler
from poker.util import strutil


@markHttpHandler
class HttpThirdPartyHandler(BaseHttpMsgChecker):
    def checkCode(self):
        code = ''
        datas = runhttp.getDict()
        if 'code' in datas:
            code = datas['code']
            del datas['code']
        keys = sorted(datas.keys())
        checkstr = ''
        for k in keys:
            checkstr += k + '=' + datas[k] + '&'
        checkstr = checkstr[:-1]

        apikey = 'www.tuyoo.com--third-party-api-e031f2a946854db29211a20f2252c3a3-www.tuyoo.com'
        checkstr = checkstr + apikey
        if code != strutil.md5digest(checkstr):
            return -1, 'Verify code error'

        acttime = int(datas.get('time', 0))
        if abs(time.time() - acttime) > 10:
            return -1, 'Verify time error'
        return 0, None

# 移动到德州的代码，其他游戏若需要再说
#     @markHttpMethod(httppath='/_gdss/thirdparty/user/info')
#     def doThirdPartyUserInfo(self, userId):
#         '''
#         玩家昵称
#         玩家id
#         钻石数量
#         金币数量
#         奖券数量
#         魅力值
#         vip等级
#         '''
#         ftlog.info('doThirdPartyUserInfo userId=', userId)
#         datas = user_remote.getThirdPartyUserInfo(userId)
#         mo = MsgPack()
#         mo.setCmd('user')
#         mo.setResult('info', datas)
#         return mo
