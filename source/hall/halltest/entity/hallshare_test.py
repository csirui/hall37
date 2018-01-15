# -*- coding=utf-8
'''
Created on 2015年7月31日

@author: zhaojiangang
'''
import unittest

from biz.mock import patch
from entity.hallbenefits_test import benefits_conf
from entity.hallstore_test import clientIdMap, item_conf, products_conf, \
    store_template_conf, store_default_conf
from entity.hallvip_test import vip_conf
from hall.entity import hallitem, hallvip, hallbenefits, hallshare
import poker.util.timestamp as pktimestamp
from test_base import HallTestMockContext
import freetime.util.log as ftlog

share_conf = {
    "shares":[
        {
            "shareId":100,
            "type":"weixin",
            "subType":"0",
            "desc":"我发现了一个好玩的游戏，快来陪我玩~还有免费金币可以领！",
            "tips":"现在分享即可获得金币奖励呦！",
            "title":"亲爱的小伙伴",
            "url":"http://3g.tuyoo.com/weixin/hallShareDizhu.html",
            "typeId":"hall.share.url",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":1000}
                ]
            },
            "mail":"恭喜您获得\\${rewardContent}的分享奖励！"
        },
        {
            "shareId":2,
            "desc":"来玩途游斗地主，输入我的推荐码\\${promoteCode}，一起拿红包，赢话费！",
            "smsDesc":"来玩途游斗地主，输入我的推荐码\\${promoteCode}，一起拿红包，赢话费！下载地址：\\${url}",
            "title":"亲爱的小伙伴",
            "url":"http://3g.tuyoo.com/fenxiang/promotionCode.html?json=\\${promoteCode}",
            "typeId":"hall.share.promote",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":1000}
                ]
            },
            "bottomRewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":10000}
                ]
            },
            "mail":"恭喜您获得1000金币的分享奖励！"
        },
        {
            "shareId":4,
            "type":"weixin",
            "subType":"0",
            "desc":"啦啦啦",
            "tips":"现在分享即可获得金币奖励！",
            "title":"飞机炸弹嗨翻天,还有话费送哦~",
            "url":"http://wxddz.tuyoo.com/",
            "typeId":"hall.share.url",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":500}
                ]
            },
            "mail":"恭喜您获得\\${rewardContent}的分享奖励！"
        },
        {
            "shareId":5,
            "type":"weixin",
            "subType":"0",
            "desc":"啦啦啦",
            "tips":"现在分享即可获得金币奖励！",
            "title":"飞机炸弹嗨翻天,还有话费送哦~",
            "url":"http://360dj.cjddz.tuyoo.com/index.php?stage=2&skin=grass",
            "typeId":"hall.share.url",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":500}
                ]
            },
            "mail":"恭喜您获得\\${rewardContent}的分享奖励！"
        },
        {
            "shareId":6,
            "type":"weixin",
            "subType":"0",
            "desc":"啦啦啦",
            "tips":"现在分享即可获得金币奖励！",
            "title":"飞机炸弹嗨翻天,还有话费送哦~",
            "url":"http://360tu.cjddz.tuyoo.com/index.php?stage=2&skin=grass",
            "typeId":"hall.share.url",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":500}
                ]
            },
            "mail":"恭喜您获得\\${rewardContent}的分享奖励！"
        },
        {
            "shareId":7,
            "type":"weixin",
            "subType":"0",
            "desc":"啦啦啦",
            "tips":"现在分享即可获得金币奖励！",
            "title":"飞机炸弹嗨翻天,还有话费送哦~",
            "url":"http://360happy.cjddz.tuyoo.com/index.php?stage=2&skin=grass",
            "typeId":"hall.share.url",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":500}
                ]
            },
            "mail":"恭喜您获得\\${rewardContent}的分享奖励！"
        },
        {
            "shareId":8,
            "type":"weixin",
            "subType":"0",
            "desc":"啦啦啦",
            "tips":"现在分享残局斗地主即可获得金币奖励！",
            "title":"飞机炸弹嗨翻天,还有话费送哦~",
            "url":"http://360win.cjddz.tuyoo.com/index.php?stage=2&skin=grass",
            "typeId":"hall.share.url",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":500}
                ]
            },
            "mail":"恭喜您获得\\${rewardContent}的分享奖励！"
        },
        {
            "shareId":9,
            "type":"weixin",
            "subType":"0",
            "desc":"啦啦啦",
            "tips":"现在分享即可获得金币奖励！",
            "title":"飞机炸弹嗨翻天,还有话费送哦~",
            "url":"http://qqdj.cjddz.tuyoo.com/index.php?stage=2&skin=grass",
            "typeId":"hall.share.url",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":500}
                ]
            },
            "mail":"恭喜您获得\\${rewardContent}的分享奖励！"
        },
        {
            "shareId":10,
            "type":"weixin",
            "subType":"0",
            "desc":"啦啦啦",
            "tips":"现在分享即可获得金币奖励！",
            "title":"飞机炸弹嗨翻天,还有话费送哦~",
            "url":"http://qqtu.cjddz.tuyoo.com/index.php?stage=2&skin=grass",
            "typeId":"hall.share.url",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":500}
                ]
            },
            "mail":"恭喜您获得\\${rewardContent}的分享奖励！"
        },
        {
            "shareId":11,
            "type":"weixin",
            "subType":"0",
            "desc":"啦啦啦",
            "tips":"现在分享即可获得金币奖励！",
            "title":"飞机炸弹嗨翻天,还有话费送哦~",
            "url":"http://qqhappy.cjddz.tuyoo.com/index.php?stage=2&skin=grass",
            "typeId":"hall.share.url",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":500}
                ]
            },
            "mail":"恭喜您获得\\${rewardContent}的分享奖励！"
        },
        {
            "shareId":12,
            "type":"weixin",
            "subType":"0",
            "desc":"啦啦啦",
            "tips":"现在分享即可获得金币奖励！",
            "title":"飞机炸弹嗨翻天,还有话费送哦~",
            "url":"http://baidu.cjddz.tuyoo.com/index.php?stage=2&skin=grass",
            "typeId":"hall.share.url",
            "maxRewardCount":1,
            "rewardContent":{
                "typeId":"FixedContent",
                "items":[
                    {"itemId":"user:chip", "count":500}
                ]
            },
            "mail":"恭喜您获得\\${rewardContent}的分享奖励！"
        }
    ]
}

class TestHallShare(unittest.TestCase):
    userId = 10001
    gameId = 6
    clientId = 'IOS_3.6_momo'
    testContext = HallTestMockContext()
    
    def setUp(self):
        self.testContext.startMock()
        self.testContext.configure.setJson('game:9999:map.clientid', clientIdMap, 0)
        self.testContext.configure.setJson('game:9999:item', item_conf, 0)
        self.testContext.configure.setJson('game:9999:products', products_conf, 0)
        self.testContext.configure.setJson('game:9999:store', store_template_conf, 0)
        self.testContext.configure.setJson('game:9999:store', store_default_conf, clientIdMap[self.clientId])
        self.testContext.configure.setJson('game:9999:vip', vip_conf, 0)
        self.testContext.configure.setJson('game:9999:benefits', benefits_conf, 0)
        self.testContext.configure.setJson('game:9999:share', share_conf, 0)
        self.timestamp = pktimestamp.getCurrentTimestamp()
        self.pktimestampPatcher = patch('poker.util.timestamp.getCurrentTimestamp', self.getCurrentTimestamp)
        self.pktimestampPatcher.start()
        
        hallitem._initialize()
        hallvip._initialize()
        hallbenefits._initialize()
        hallshare._initialize()
        
    def tearDown(self):
        self.pktimestampPatcher.stop()
        self.testContext.stopMock()
        
    def getCurrentTimestamp(self):
        return self.timestamp
    
    def testLoad(self):
        shareList = hallshare.getAllShare()
        for share in shareList:
            ftlog.debug('>>> sendReward %s' % (share.shareId))
            hallshare.sendReward(self.gameId, self.userId, share, 'test')
            ftlog.debug('<<< sendReward %s' % (share.shareId))
            
if __name__ == '__main__':
    unittest.main()


