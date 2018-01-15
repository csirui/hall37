# -*- coding:utf-8 -*-
'''
Created on 2015年12月22日

@author: zhaojiangang
'''
from datetime import datetime, timedelta
import unittest

from biz.mock import patch
from entity.hallshare_test import share_conf
from entity.hallstore_test import clientIdMap, item_conf, products_conf, \
    store_template_conf, store_default_conf
from entity.hallvip_test import vip_conf
from hall.entity import hallitem, hallvip, neituiguang, neituiguangtask, \
    halltask, hallshare
from hall.entity.hallconf import HALL_GAMEID
from hall.servers.util.neituiguang_new_handler import NeiTuiGuangTcpHandler
from poker.entity.dao import userdata, gamedata
import poker.util.timestamp as pktimestamp
from test_base import HallTestMockContext
from hall.servers.util.rpc import neituiguang_remote


tasks_conf = {
    "taskUnits":[
        {
            "taskUnitId":"hall.task.neituiguang.newUser",
            "pools":[
                {
                    "tasks":[
                        {
                            "kindId":10001,
                            "typeId":"hall.task.simple",
                            "name":"游戏5局",
                            "desc":"测试任务",
                            "pic":"${http_download}/dizhu/medal/img/play_5.png",
                            "count":5,
                            "star":0,
                            "totalLimit":1,
                            "inspector":{
                                "typeId":"hall.item.open",
                                "conditions":[
                                    {
                                        "typeId":"hall.item.open.kindId",
                                        "kindIds":[1001]
                                    }
                                ]
                            },
                            "rewardContent":{
                                "typeId":"FixedContent",
                                "desc":"50金币",
                                "items":[
                                    {"itemId":"user:chip", "count":50}
                                ]
                            },
                            "rewardMail":"勋章奖励：\\${rewardContent}"
                        }
                    ]
                },
                {
                    "tasks":[
                        {
                            "kindId":10002,
                            "typeId":"hall.task.simple",
                            "name":"游戏5局",
                            "desc":"测试任务",
                            "pic":"${http_download}/dizhu/medal/img/play_5.png",
                            "count":5,
                            "star":0,
                            "totalLimit":1,
                            "inspector":{
                                "typeId":"hall.item.open",
                                "conditions":[
                                    {
                                        "typeId":"hall.item.open.kindId",
                                        "kindIds":[1001]
                                    }
                                ]
                            },
                            "rewardContent":{
                                "typeId":"FixedContent",
                                "desc":"50金币",
                                "items":[
                                    {"itemId":"user:chip", "count":50}
                                ]
                            },
                            "rewardMail":"勋章奖励：\\${rewardContent}"
                        }
                    ]
                }
            ]
        }
    ]  
}

neituiguang2 = {
    "prizeDetail":"This is detail",
    "prizeImgUrl":"${http_download}/hall/item/imgs/coin.png",
    "prizeRewardItem":{
        "itemId":"user:chip",
        "count":1
    },
    "prizeRewardDesc":"每推荐一个人可获得\\${rewardContent}",
    "prizeNotGotRewardDesc":"还未获得奖励",
    "prizeGotTotalRewardDesc":"已经获得\\${totalRewardContent}",
    "prizeAvailableRewardDesc":"可领取奖励\\${availableRewardContent}",
    "prizeRewardTips":"恭喜您获得\\${rewardContent}",
    "shareLoc":"neituiguang",
    "taskDetail":"This is task detail"
}

class TestDailyCheckin(unittest.TestCase):
    userId = 10001
    inviteeUserId = 10002
    gameId = 9999
    clientId = 'IOS_3.6_momo'
    testContext = HallTestMockContext()
    regTaskClass = False
    
    def getCurrentTimestamp(self):
        return self.timestamp
    
    def setUp(self):
        self.testContext.startMock()
        
        self.timestamp = pktimestamp.getCurrentTimestamp()
        self.pktimestampPatcher = patch('poker.util.timestamp.getCurrentTimestamp', self.getCurrentTimestamp)
        self.pktimestampPatcher.start()
        
#         self.neituiguangRemotePatcher = mock._patch_multiple('hall.servers.util.rpc.neituiguang_remote',
#                                                       consumeAssets=self.userRemote.consumeAssets,
#                                                       addAssets=self.userRemote.addAssets,
#                                                       queryUserWeardItemKindIds=self.userRemote.queryUserWeardItemKindIds,
#                                                       presentItemByUnitsCount=self.userRemote.presentItemByUnitsCount,
#                                                       presentItem=self.userRemote.presentItem)
        
        self.testContext.configure.setJson('game:9999:map.clientid', clientIdMap, 0)
        self.testContext.configure.setJson('game:9999:item', item_conf, 0)
        self.testContext.configure.setJson('game:9999:products', products_conf, 0)
        self.testContext.configure.setJson('game:9999:store', store_template_conf, 0)
        self.testContext.configure.setJson('game:9999:store', store_default_conf, clientIdMap[self.clientId])
        self.testContext.configure.setJson('game:9999:vip', vip_conf, 0)
        self.testContext.configure.setJson('game:9999:tasks', tasks_conf, 0)
        self.testContext.configure.setJson('game:9999:share', share_conf, 0)
        self.testContext.configure.setJson('game:9999:neituiguang2', neituiguang2, 0)
        
        hallitem._initialize()
        hallvip._initialize()
        hallshare._initialize()
        if not TestDailyCheckin.regTaskClass:
            TestDailyCheckin.regTaskClass=True
            halltask._registerClasses()
            
        neituiguang._initialize()
        neituiguangtask._initialize()
        
    def tearDown(self):
        self.testContext.stopMock()
        self.pktimestampPatcher.stop()
        
#     def testGetStates(self):
#         handler = NeiTuiGuangTcpHandler()
#         createTime = datetime.now()# datetime.strptime('2015-12-22 18:20:00.0', '%Y-%m-%d %H:%M:%S.%f')
#         userdata.setAttr(self.userId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
#         userdata.setAttr(self.inviteeUserId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
#         print userdata.getAttr(self.userId, 'createTime')
#          
#         status = neituiguang.loadStatus(self.userId, self.timestamp)
#         self.assertTrue(handler.translateState(status) == 0)
#         self.assertTrue(status.isNewUser, 'status.isNewUser must be True')
#         handler.doQueryState(HALL_GAMEID, 10001, 'IOS_3.70_360.360.0-hall6.360.day')
#         
#     def testCheckCode(self):
#         handler = NeiTuiGuangTcpHandler()
#         createTime = datetime.now()# datetime.strptime('2015-12-22 18:20:00.0', '%Y-%m-%d %H:%M:%S.%f')
#         userdata.setAttr(self.userId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
#         userdata.setAttr(self.inviteeUserId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
#         createTime -= timedelta(days=8)
#         userdata.setAttr(self.userId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
#         handler.doCheckCode(HALL_GAMEID, self.inviteeUserId, self.clientId, self.userId)
#         
#     def testCancelCheckCode(self):
#         handler = NeiTuiGuangTcpHandler()
#         createTime = datetime.now()# datetime.strptime('2015-12-22 18:20:00.0', '%Y-%m-%d %H:%M:%S.%f')
#         userdata.setAttr(self.userId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
#         userdata.setAttr(self.inviteeUserId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
#         createTime += timedelta(days=8)
#         userdata.setAttr(self.userId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
#         handler.doCancelCodeCheck(HALL_GAMEID, self.inviteeUserId, self.clientId)
#         status = neituiguang.loadStatus(self.inviteeUserId, self.timestamp)
#         self.assertTrue(status.inviter and status.inviter.userId == 0)
#         
#         handler.doQueryTaskInfo(self.gameId, self.inviteeUserId)
#         
    def testGetPrize(self):
        handler = NeiTuiGuangTcpHandler()
        createTime = datetime.now()# datetime.strptime('2015-12-22 18:20:00.0', '%Y-%m-%d %H:%M:%S.%f')
        userdata.setAttr(self.userId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
        userdata.setAttr(self.inviteeUserId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
        createTime -= timedelta(days=8)
        userdata.setAttr(self.userId, 'createTime', createTime.strftime('%Y-%m-%d %H:%M:%S.%f'))
        gamedata.delGameAttr(self.userId, self.gameId, 'neituiguang')
        gamedata.delGameAttr(self.inviteeUserId, self.gameId, 'neituiguang')
        
        handler.doQueryPrize(self.gameId, self.userId, self.clientId)
        
        timestamp = pktimestamp.getCurrentTimestamp()
        handler.doCheckCode(self.gameId, self.inviteeUserId, self.clientId, self.userId)
        
        neituiguang_remote.onInvitationAccepted(self.userId, self.inviteeUserId)
        status = neituiguang.loadStatus(self.userId, timestamp)
        neituiguang.onNotifyInviterOk(status)
        
        handler.doQueryPrize(self.gameId, self.userId, self.clientId)
        handler.doGetPrize(self.gameId, self.userId, self.clientId)
        
if __name__ == '__main__':
    unittest.main()
    
    
    