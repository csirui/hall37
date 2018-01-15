# -*- coding: utf-8 -*-
'''
Created on 2015年5月20日

@author: zqh
'''


def getLed(userId, gameId, clientId):
    pass

# 
# import datetime
# import random
# from freetime.util.log import ftlog
# from tyframework.context import TyContext
# import json
# from freetime.todotask.todotask_moudle import TodoTaskObserve,\
#     TodoTaskQuickStart
# 
# class Message():
# 
#     # 全局的LED消息的缓存
#     LEDS = {}
# 
#     @classmethod
#     def sendPrivate(self, tasklet, gameId, toUid, fromUid, msg):
#         maxkey = 'g' + str(gameId) + 'u' + str(toUid)
#         return self._putMsg(tasklet, maxkey, msg, gameId, fromUid)
# 
#     @classmethod
#     def sendGlobal(self, tasklet, gameId, msg):
#         maxkey = 'g' + str(gameId)
#         return self._putMsg(tasklet, maxkey, msg, gameId, 0)
# 
#     @classmethod
#     def decodeMsgV3(cls, gameId, msgstr):
#         try:
#             d = json.loads(msgstr)
#             if not isinstance(d, dict):
#                 return None
#             d['gameId'] = gameId
#             return d
#         except:
#             if TyContext.ftlog.is_debug():
#                 TyContext.ftlog.exception()
#             return None
#     
#     @classmethod
#     def decodeMsgV2(cls, gameId, msgstr):
#         try:
#             header = 'richTextLedMsg'
#             if not msgstr.startswith(header):
#                 return None
#             '''msg json 格式示例:
#             {
#                 'richText': {
#                     'text': [{
#                         "color": "RRGGBB",
#                         "text": "aaa"
#                     },{
#                         "color": "RRGGBB",
#                         "text": "bbbccc"
#                     }],
#                 },
#                 'excludeUsers': [123456, 32134534],
#                 'type':'led', #type://“led”为无按钮,”watch”为观战 “vip”: quick_start
#                 'roomId':roomId,
#                 'tableId':tableId
#             }
#             '''
#             # 德州版本的富文本协议
#             d = json.loads(msgstr[len(header):])
#             msgDict = {}
#             msgDict['gameId'] = d.get('gameId', gameId)
#             msgDict['text'] = d.get('richText', {}).get('text', [])
#             ledType = d.get('type', 'led')
#             if ledType == 'watch':
#                 msgDict['lbl'] = '观战'
#                 msgDict['tasks'] = [TodoTaskObserve(gameId, d.get('roomId', 0), d.get('tableId', 0)).toStr()]
#             elif ledType == 'vip':
#                 msgDict['lbl'] = '进入'
#                 msgDict['tasks'] = [TodoTaskQuickStart(gameId, d.get('roomId', 0), d.get('tableId', 0), d.get('seatId', 0)).toStr()]
#             excludeUsers = d.get('excludeUsers')
#             if excludeUsers:
#                 msgDict['excludeUsers'] = d.get('excludeUsers') 
#             return msgDict
#         except:
#             if TyContext.ftlog.is_debug():
#                 TyContext.ftlog.exception()
#             return None
#     
#     @classmethod
#     def translateToMsgDictV2(cls, msgDict):
#         tasks = msgDict.get('tasks')
#         extDict = {}
#         if tasks:
#             if len(tasks) > 1:
#                 return None
#             # V2只支持旁观，quickstart
#             todotask = tasks[0]
#             action = todotask.getAction()
#             if action == 'quick_start':
#                 extDict['type'] = 'vip'
#                 extDict['roomId'] = todotask.getParams('roomId', 0)
#                 extDict['tableId'] = todotask.getParams('tableId', 0)
#                 extDict['seatId'] = todotask.getParams('seatId', 0)
#             elif action == 'observe':
#                 extDict['type'] = 'watch'
#                 extDict['roomId'] = todotask.getParams('roomId', 0)
#                 extDict['tableId'] = todotask.getParams('tableId', 0)
#             else:
#                 return None
#         msgDictV2 = {'richText':{'text':msgDict.get('text')}}
#         excludeUsers = msgDict.get('excludeUsers')
#         if excludeUsers:
#             msgDictV2['excludeUsers'] = excludeUsers
#         msgDictV2.update(extDict)
#         if 'gameId' in msgDict:
#             msgDictV2['gameId'] = msgDict.get('gameId')
#         return msgDictV2
#             
#     @classmethod
#     def translateToMsgDictV1(cls, msgDict):
#         tasks = msgDict.get('tasks')
#         if tasks:
#             # 有tasks的只有V2, V3支持
#             return None
#         
#         msgstr = ''
#         richTextList = msgDict.get('text', [])
#         for richText in richTextList:
#             text = richText.get('text')
#             if text:
#                 msgstr += text
#         if TyContext.ftlog.is_debug():
#             TyContext.ftlog.debug('Message.translateToMsgDictV1 msgDict=', msgDict, 'msgstr=', msgstr)
#         return msgstr
#     
#     @classmethod
#     def decodeMsg(cls, gameId, msgstr):
#         msgDict = cls.decodeMsgV2(gameId, msgstr)
#         if msgDict:
#             return msgDict
#         
#         msgDict = cls.decodeMsgV3(gameId, msgstr)
#         if msgDict:
#             return msgDict
#         
#         return {
#             'text':[{'color':'FFFFFF', 'text':msgstr, 'gameId':gameId}]
#         }
#         
#     @classmethod
#     def ledMsgFilterOrig(cls, tasklet, gameId, userId, clientVer, led, newleds):
#         """ 这是以前的过滤方法 """
# 
#         _id, _gid, ledmsg = led
#         if isinstance(ledmsg, str) and ledmsg[0] == '#':
#             cutVer = TyContext.Configure.get_game_item_float(gameId, 'version.2.2', 2.15)
#             if clientVer and clientVer < cutVer:
#                 ledmsg = ledmsg[7:]
#         newleds['origLeds'].append([_id, _gid, ledmsg])
# 
#         return True
# 
#     @classmethod
#     def ledMsgFilterRich(cls, tasklet, gameId, userId, clientVer, led, newleds):
#         """ 过滤富文本 led 消息 """
# 
#         _id, _gid, ledmsg = led
#         isRichTextLed = isinstance(ledmsg, dict) and ledmsg.has_key('richText')
#         if not isRichTextLed:
#             # 德州1.67版本LED有bug,这是bug处理，3.37解决bug，不对3.37以上的版本做处理，但是3.37的插件又存在这个bug
#             if gameId == 8:
#                 from freetime.games.texaspoker import config
#                 clientId = TyContext.ClientUtils.getUserSessionClientId(tasklet, userId);
#                 if config.versionLedBugFixed > clientVer >= config.versionHaveLedBug or 'hall8' not in clientId:
#                     ledmsg = {"richText": {"text": [{"color": "FFFFFF", "text": ledmsg}], "type":"led", "gameId":8},
#                             "excludeUsers": set()}
#                     ftlog.debug("convert orig  led to richtext led", ledmsg)
#                 else:
#                     return False
#             else:
#                 return False
# 
#         # 加入 exclude 机制：业务需求要求一部分LED实时发送给用户，其余用户
#         # 保留现有心跳时接收 LED 方式。为了让收过LED的用户不再重复接收，
#         # 凡是在 excludeUsers 中的用户就不再接收 LED 了。
#         if userId in ledmsg['excludeUsers']:
#             return False
# 
#         if gameId == 8:
#             from freetime.games.texaspoker import config
#             # 德州 1.67 版本加入富文本消息
#             if clientVer < config.versionCanReceiveRichTextLed:
#                 newleds['origLeds'].append([_id, _gid, ledmsg['plainText']])
# 
#             # 1.67版本LED有bug,这是bug处理
#             elif clientVer >= config.versionHaveLedBug:
#                 newleds['richLeds'] = ledmsg['richText']
#                 newleds['origLeds'] = ledmsg['richText']
#             else:
#                 newleds['richLeds'].append(ledmsg['richText'])
#             return True
#         elif gameId == 1:
#             newleds['richLeds'] = ledmsg['richText']
#             newleds['origLeds'] = ledmsg['richText']
#             return True
# 
#         return False
# 
#     @classmethod
#     def tryParseRichTextLed(cls, msg):
#         """检查led消息是否富文本格式。
#         如果是，解析格式并返回；如否，原样返回；如果出错，返回None
# 
#         msg json 格式示例:
#         {
#             'richText': {
#                 'text': [{
#                     "color": "RRGGBB",
#                     "text": "aaa"
#                 },{
#                     "color": "RRGGBB",
#                     "text": "bbbccc"
#                 }],
#             },
#             'excludeUsers': [123456, 32134534]
#         }
#         """
# 
#         header = 'richTextLedMsg'
#         if not msg.startswith(header):
#             return msg
# 
#         try:
#             ledmsg = json.loads(msg[len(header):])
#             ledmsg['excludeUsers'] = set(ledmsg.get('excludeUsers', []))
#             ledmsg['plainText'] = u''.join((unicode(seg['text']) for seg in ledmsg['richText']['text']))
#             return ledmsg
#         except:
#             ftlog.error("load led json error", msg)
#             TyContext.ftlog.exception()
# 
#     @classmethod
#     def getLedMsgLists(cls, tasklet, leds, gameId, userId, clientVer):
#         if not leds:
#             return
# 
#         newleds = {
#                 'richLeds': [],  # 带格式的 led 消息
#                 'origLeds': [],  # 纯文本的 led 消息
#         }
# 
#         # 过滤 led 消息。过滤器把通过过滤器的消息加入到 richLeds 或者 origLeds 里
#         for led in leds:
#             if cls.ledMsgFilterRich(tasklet, gameId, userId, clientVer, led, newleds):
#                 continue
#             if cls.ledMsgFilterOrig(tasklet, gameId, userId, clientVer, led, newleds):
#                 continue
# 
#         return newleds
# 
#     @classmethod
#     def sendLed3(cls, tasklet, gameId, msgstr, isManager=False):
#         if TyContext.ftlog.is_debug():
#             TyContext.ftlog.debug('Message.sendLed3 gameId=', gameId,
#                                   'msgstr=', msgstr,
#                                   'isManager=', isManager)
#         if not isManager :
#             randmod = TyContext.Configure.get_game_item_int(gameId, 'led.random.mod', 3)
#             randint = random.randint(0, randmod - 1)
#             if randint % randmod != 0 :
#                 if TyContext.ftlog.is_debug():
#                     TyContext.ftlog.debug('Message.sendLed3 Failed gameId=', gameId,
#                                           'msgstr=', msgstr,
#                                           'isManager=', isManager,
#                                           'noRandom')
#                 return
#             
#         try:
#             msgDict = cls.decodeMsg(gameId, msgstr)
#             msg = [0, gameId, msgDict]
#             leds = Message.LEDS
#             kmsg = 'm:' + str(gameId)
#             ktime = 't:' + str(gameId)
#             
#             if isManager :
#                 leds[kmsg] = [msg]
#                 leds[ktime] = datetime.datetime.now()
#             else:
#                 if not kmsg in leds :
#                     leds[kmsg] = []
#                     leds[ktime] = None
#                 timeout = leds[ktime]
#                 if timeout != None :
#                     timeouts = TyContext.Configure.get_game_item_int(gameId, 'led.manager.timeout', 30)
#                     secondes = (datetime.datetime.now() - timeout).seconds
#                     if secondes < timeouts :
#                         if TyContext.ftlog.is_debug():
#                             TyContext.ftlog.debug('Message.sendLed3 Failed gameId=', gameId,
#                                                   'msgstr=', msgstr,
#                                                   'isManager=', isManager,
#                                                   'timeouts=', timeouts,
#                                                   'secondes=', secondes)
#                         return
#                 msgq = leds[kmsg]
#                 msgq.append(msg)
#                 #ledlength = TyContext.Configure.get_game_item_int(gameId, 'led.max.length', 3)
#                 ledlength = 3
#                 if gameId == 7:
#                     leds[ktime] = datetime.datetime.now()
#                 else:
#                     leds[ktime] = None
#                 leds[kmsg] = msgq[-ledlength:]
#             if TyContext.ftlog.is_debug():
#                 TyContext.ftlog.debug('Message.sendLed3 gameId=', gameId,
#                                       'msgstr=', msgstr,
#                                       'isManager=', isManager,
#                                       'msg=', msg,
#                                       'leds=', leds,
#                                       'Message.LEDS=', Message.LEDS)
#             return msg
#         except:
#             TyContext.ftlog.exception()
#             return None
#         
#     @classmethod
#     def sendLed(self, tasklet, gameId, msg, isManager=False):
#         if not isManager :
#             randmod = TyContext.Configure.get_game_item_int(gameId, 'led.random.mod', 3)
#             randint = random.randint(0, randmod - 1)
#             if randint % randmod != 0 :
#                 return
# 
#         msg = self.tryParseRichTextLed(msg)
#         if not msg:
#             return
# 
#         msg = [0, gameId, msg]
#         leds = Message.LEDS
#         kmsg = 'm:' + str(gameId)
#         ktime = 't:' + str(gameId)
# 
#         if isManager :
#             leds[kmsg] = [msg]
#             leds[ktime] = datetime.datetime.now()
#         else:
#             if not kmsg in leds :
#                 leds[kmsg] = []
#                 leds[ktime] = None
#             timeout = leds[ktime]
#             if timeout != None :
#                 timeouts = TyContext.Configure.get_game_item_int(gameId, 'led.manager.timeout', 30)
#                 secondes = (datetime.datetime.now() - timeout).seconds
#                 if secondes < timeouts :
#                     return
#             msgq = leds[kmsg]
#             msgq.append(msg)
#             #ledlength = TyContext.Configure.get_game_item_int(gameId, 'led.max.length', 3)
#             ledlength = 3
#             if gameId == 7:
#                 leds[ktime] = datetime.datetime.now()
#             else:
#                 leds[ktime] = None
#             leds[kmsg] = msgq[-ledlength:]
#         return msg
# 
#     @classmethod
#     def checkMgrLedTimeOut(self, tasklet, gameId):
#         leds = Message.LEDS
#         kmsg = 'm:' + str(gameId)
#         ktime = 't:' + str(gameId)
#         if not kmsg in leds :
#             leds[ktime] = None
#             leds[kmsg] = []
#             return True
# 
#         timeout = leds[ktime]
#         if timeout != None :
#             timeouts = TyContext.Configure.get_game_item_int(gameId, 'led.manager.timeout', 30)
#             secondes = (datetime.datetime.now() - timeout).seconds
#             if secondes >= timeouts :
#                 leds[ktime] = None
#                 leds[kmsg] = []
#                 return True
#             else:
#                 return False
#         return True
# 
#     @classmethod
#     def __check_max_msg_id__(self, tasklet, maxkey, detalid):
#         try:
#             datas = tasklet.waitForRedis('LRANGE', 'message:' + maxkey, 0, 1)
#             if datas :
#                 maxid = int(datas[0].split('#')[0]) + detalid
#                 tasklet.waitForRedis('HSET', 'message', maxkey, maxid)
#                 return maxid
#         except:
#             TyContext.ftlog.exception()
#         return detalid
# 
#     @classmethod
#     def _putMsg(self, tasklet, maxkey, msg, gameId, fromUid):
#         ctstr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         msgid = tasklet.waitForRedis('HINCRBY', 'message', maxkey, 1)
#         if msgid == 1 :
#             msgid = self.__check_max_msg_id__(tasklet, maxkey, 1)
#         datas = str(msgid) + '#' + str(gameId) + '#' + str(fromUid) + '#' + ctstr + '#' + msg
#         tasklet.waitForRedis('LPUSH', 'message:' + maxkey, datas)
#         return datas
# 
#     @classmethod
#     def _parseMessage(self, content):
#         try:
#             datas = content.split('#', 4)
#             datas[0] = int(datas[0])
#             datas[1] = int(datas[1])
#             datas[2] = int(datas[2])
#             if type(datas[4]) != unicode :
#                 datas[4] = datas[4].decode('utf-8')
#     
#             return {'id':datas[0], 'gid':datas[1], 'uid':datas[2],
#                     'time':datas[3], 'msg':datas[4]}
#         except:
#             ftlog.exception('message content format error !!')
#         return None
# 
#     @classmethod
#     def _getMsgList(self, tasklet, maxkey, readkey, minTime, isOnlyUnRead, pageNo, pageSize):
#         maxMsgId, readMaxId = tasklet.waitForRedis('HMGET', 'message', maxkey, readkey)
#         if not maxMsgId :
#             maxMsgId = 0
#         if not readMaxId:
#             readMaxId = 0
#         msglist = []
#         maxId = readMaxId
# 
#         if isOnlyUnRead :
#             if maxMsgId <= readMaxId :
#                 return {'count':0}
#         if pageNo < 1 :
#             pageNo = 1
#         lstart = (pageNo - 1) * pageSize
#         lend = lstart + pageSize - 1
#         datas = tasklet.waitForRedis('LRANGE', 'message:' + maxkey, lstart, lend)
#         count = 0
#         if datas :
#             for msgstr in datas :
#                 msg = self._parseMessage(msgstr)
#                 if not msg :
#                     continue
#                 maxId = max(maxId, msg['id'])
#                 append = True
#                 if minTime != None :
#                     mtime = datetime.datetime.strptime(msg['time'], '%Y-%m-%d %H:%M:%S')
#                     if mtime <= minTime :
#                         append = False
# 
#                 if isOnlyUnRead and msg['id'] <= readMaxId :
#                     append = False
# 
#                 if append :
#                     msglist.append(msg)
#                     count += 1
#         if maxId > 0 :
#             tasklet.waitForRedis('HSET', 'message', readkey, maxId)
#         return {'count':count, 'maxId': maxMsgId, 'readId': readMaxId, 'pageNo':pageNo, 'list':msglist}
# 
#     @classmethod
#     def getUnReadCounts(self, tasklet, gameId, userId):
#         pmaxkey = 'g' + str(gameId) + 'u' + str(userId)
#         preadkey = 'g' + str(gameId) + 'u' + str(userId) + 'p'
#         gmaxkey = 'g' + str(gameId)
#         greadkey = 'g' + str(gameId) + 'u' + str(userId) + 'g'
#         gmaxId, greadId, pmaxId, preadId = tasklet.waitForRedis('HMGET', 'message', gmaxkey, greadkey, pmaxkey, preadkey)
#         if gmaxId == None :
#             gmaxId = self.__check_max_msg_id__(tasklet, gmaxkey, 0)
#         if greadId == None :
#             greadId = 0
#         if pmaxId == None :
#             pmaxId = self.__check_max_msg_id__(tasklet, pmaxkey, 0)
#         if preadId == None :
#             preadId = 0
#         gcount = gmaxId - greadId
#         pcount = pmaxId - preadId
#         return {'global':gcount, 'private':pcount, 'led':0}
# 
#     @classmethod
#     def getLedMsgList(self, tasklet, gameId):
#         leds = Message.LEDS
#         kmsg = 'm:' + str(gameId)
#         if kmsg in leds :
#             return leds[kmsg]
#         return []
# 
#     # 私信：不过期过期,用户主动删除,每页取20条
#     @classmethod
#     def getPrivateMsgList(self, tasklet, gameId, userId, pageNo=1):
#         maxkey = 'g' + str(gameId) + 'u' + str(userId)
#         readkey = 'g' + str(gameId) + 'u' + str(userId) + 'p'
#         return self._getMsgList(tasklet, maxkey, readkey, None, False, pageNo, 20)
# 
#     # 公告：时效7天，不删除,，只取最后20条
#     @classmethod
#     def getGlobalMsgList(self, tasklet, gameId, userId):
#         mintime = datetime.datetime.now() - datetime.timedelta(days=7)
#         maxkey = 'g' + str(gameId)
#         readkey = 'g' + str(gameId) + 'u' + str(userId) + 'g'
#         return self._getMsgList(tasklet, maxkey, readkey, mintime, False, 1, 20)
