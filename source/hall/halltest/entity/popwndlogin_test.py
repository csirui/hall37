# -*- coding:utf-8 -*-
'''
Created on 2016年3月26日

@author: zhaojiangang
'''
import time
import unittest

from entity.hallpopwnd_test import popwnd_conf
from entity.hallstore_test import item_conf, products_conf, store_default_conf
from entity.hallvip_test import vip_conf
from hall.entity import hallpopwnd, hallitem, hallstore, hallvip
from hall.entity.hallpopwnd import TodoTasksGeneratorRegister
from test_base import HallTestMockContext


popwndlogin_conf = {
    "typeId": "todotasks.gen.switch",
    "list": [
        {
            "typeId": "todotasks.gen.list",
            "condition": {
                "typeId": "user.cond.registerDays",
                "startDays": 0,
                "stopDays": 1
            },
            "list": [
                {
                    "condition": {
                        "typeId": "user.cond.dayfirstlogin"
                    },
                    "typeId": "todotasks.gen.single",
                    "todotask": {
                        "templateName": "monthCheckin"
                    }
                },
                {
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId": "user.cond.notIsMember"
                            },
                            {
                                "typeId": "user.cond.notdayfirstlogin"
                            },
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":0,
                                "stopLevel":1
                            }
                        ]
                    },
                    "typeId": "todotasks.gen.single",
                    "todotask": {
                        "templateName": "memberBuy2"
                    }
                },
                {
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":0,
                                "stopLevel":1
                            },
                            {
                                "typeId": "user.cond.IsMember"
                            },
                            {
                                "typeId": "user.cond.notdayfirstlogin"
                            }
                        ]
                    },
                    "typeId": "todotasks.gen.single",
                    "todotask": {
                        "templateName": "recommendBuy"
                    }
                },
                {
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":1,
                                "stopLevel":-1
                            },
                            {
                                "typeId": "user.cond.notdayfirstlogin"
                            }
                        ]
                    },
                    "typeId": "todotasks.gen.single",
                    "todotask": {
                        "templateName": "activity"
                    }
                },
                {
                    "condition": {
                        "typeId": "user.cond.dayfirstlogin"
                    },
                    "typeId": "todotasks.gen.single",
                    "todotask": {
                        "templateName": "activity"
                    }
                }
            ]
        },
        {
            "typeId": "todotasks.gen.switch",
            "condition": {
                "typeId": "user.cond.registerDays",
                "startDays": 2,
                "stopDays": -1
            },
            "list": [
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":0,
                                "stopLevel":1
                            },
                            {
                                "typeId": "user.cond.notIsMember"
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "memberBuy2"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":0,
                                "stopLevel":1
                            },
                            {
                                "typeId": "user.cond.IsMember"
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":1,
                                "stopLevel":3
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":3,
                                "remainder":0
                            },
                            {
                                "typeId": "user.cond.notIsMember"
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "memberBuy2"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":1,
                                "stopLevel":3
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":3,
                                "remainder":0
                            },
                            {
                                "typeId": "user.cond.IsMember"
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":1,
                                "stopLevel":3
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":3,
                                "remainder":1
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":1,
                                "stopLevel":3
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":3,
                                "remainder":2
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":4,
                                "stopLevel":5
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":5,
                                "remainder":0
                            },
                            {
                                "typeId": "user.cond.IsMember"
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":4,
                                "stopLevel":5
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":5,
                                "remainder":0
                            },
                            {
                                "typeId": "user.cond.notIsMember"
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "memberBuy2"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":4,
                                "stopLevel":5
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":5,
                                "remainder":1
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":4,
                                "stopLevel":5
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":5,
                                "remainder":2
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy_chaozhi_30yuan"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":4,
                                "stopLevel":5
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":5,
                                "remainder":3
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":4,
                                "stopLevel":5
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":5,
                                "remainder":4
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy_vip_500zuan"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":6,
                                "stopLevel":-1
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":7,
                                "remainder":1
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy_vip_500zuan"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":6,
                                "stopLevel":-1
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":7,
                                "remainder":2
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy_vip_500zuan"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":6,
                                "stopLevel":-1
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":7,
                                "remainder":3
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy_chaozhi_30yuan"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":6,
                                "stopLevel":-1
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":7,
                                "remainder":4
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy_vip_1000zuan"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":6,
                                "stopLevel":-1
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":7,
                                "remainder":5
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy_vip_1000zuan"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":6,
                                "stopLevel":-1
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":7,
                                "remainder":6
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy_vip_1000zuan"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":6,
                                "stopLevel":-1
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":7,
                                "remainder":0
                            },
                            {
                                "typeId": "user.cond.IsMember"
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "recommendBuy"
                    }
                },
                {
                    "typeId": "todotasks.gen.single",
                    "condition": {
                        "typeId": "user.cond.and",
                        "list": [
                            {
                                "typeId":"user.cond.vipLevel",
                                "startLevel":6,
                                "stopLevel":-1
                            },
                            {
                                "typeId": "user.cond.signDayMod",
                                "mod":7,
                                "remainder":0
                            },
                            {
                                "typeId": "user.cond.notIsMember"
                            }
                        ]
                    },
                    "todotask": {
                        "templateName": "memberBuy2"
                    }
                }
            ]
        }
    ]
}
clientIdMap = {
    "IOS_3.6_momo":1,
    "IOS_3.71_tyGuest,weixin.appStore.0-hall6.tuyoo.huanle":2
}

store_template_conf = {
    "firstRechargeThreshold": 60,
    "templates"             : [
        {
            "name"                  : "goods_conf_3.7XX_hall_test",
            "shelves"               : [
                {
                    "displayName"           : "购买金币",
                    "iconType"              : "coin",
                    "name"                  : "coin",
                    "products"              : [
                        "TY9999D0030023",
                        "TY9999D0050010"
                    ],
                    "sort"                  : 0,
                    "visible"               : 1
                }
            ]
        }
    ],
    "pricePics"             : {
        "300"                   : "${http_download}/hall/store/imgs/price_300.png",
        "68"                    : "${http_download}/hall/store/imgs/price_68.png",
        "128"                   : "${http_download}/hall/store/imgs/price_128.png",
        "18"                    : "${http_download}/hall/store/imgs/price_18.png",
        "12"                    : "${http_download}/hall/store/imgs/price_12.png",
        "2"                     : "${http_download}/hall/store/imgs/price_2.png",
        "1"                     : "${http_download}/hall/store/imgs/price_1.png",
        "10"                    : "${http_download}/hall/store/imgs/price_10.png",
        "30"                    : "${http_download}/hall/store/imgs/price_30.png",
        "6"                     : "${http_download}/hall/store/imgs/price_6.png",
        "5"                     : "${http_download}/hall/store/imgs/price_5.png",
        "8"                     : "${http_download}/hall/store/imgs/price_8.png",
        "100"                   : "${http_download}/hall/store/imgs/price_100.png",
        "1000"                  : "${http_download}/hall/store/imgs/price_1000.png",
        "50"                    : "${http_download}/hall/store/imgs/price_50.png"
    },
    "lastBuy"               : {
        "desc"                  : "亲，您上次花费\\${product.price}元购买了\\${product.displayName}，是否继续购买该商品",
        "desc2"                 : "亲，您是否需要花费\\${product.price}元购买\\${product.displayName}",
        "payOrder"              : {
            "priceDiamond"          : {
                "count"                 : 120,
                "maxCount"              : -1,
                "minCount"              : 120
            },
            "shelves"               : [
                "member"
            ]
        },
        "subText"               : "是",
        "subTextExt"            : "逛逛商城"
    },
    "deliveryConf"          : {
        "fail"                  : {
            "content"               : "啊哦~这真是太尴尬了......请您尽快联系我们的客服！我们一定第一时间为您处理！感谢您对我们工作的支持和理解！",
            "timefmt"               : "%H点%M分%S秒",
            "tips"                  : "如有问题请拨打客服电话：4008-098-000",
            "title"                 : "很抱歉，添加物品失败啦！"
        },
        "succ"                  : {
            "content"               : "您于\\${datetime}成功购买 \\${productName}\n本次消费：\\${consume}\n添加\\${content}",
            "timefmt"               : "%H点%M分%S秒",
            "tips"                  : "如有问题请拨打客服电话：4008-098-000",
            "title"                 : "添加物品成功啦！"
        }
    },
    "exchangePricePics"     : {
        "user:chip"             : "${http_download}/hall/store/imgs/chip.png",
        "user:diamond"          : "${http_download}/hall/store/imgs/diamond.png",
        "user:coupon"           : "${http_download}/hall/store/imgs/coupon.png"
    }
}
    
class TestPopwndLogin(unittest.TestCase):
    userId = 10001
    gameId = 6
    clientId = 'IOS_3.71_tyGuest,weixin.appStore.0-hall6.tuyoo.huanle'
    testContext = HallTestMockContext()
    
    def setUp(self):
        self.testContext.startMock()
        self.testContext.configure.setJson('game:9999:map.clientid', clientIdMap, 0)
        self.testContext.configure.setJson('game:9999:item', item_conf, 0)
        self.testContext.configure.setJson('game:9999:popwnd', popwnd_conf, 0)
        self.testContext.configure.setJson('game:9999:products', products_conf, 0)
        self.testContext.configure.setJson('game:9999:store', store_template_conf, 0)
        self.testContext.configure.setJson('game:9999:store', store_default_conf, clientIdMap[self.clientId])
        self.testContext.configure.setJson('game:9999:vip', vip_conf, 0)
        
        hallitem._initialize()
        hallstore._initialize()
        hallpopwnd._initialize()
        hallvip._initialize()
        
        self.testContext.userDB.setAttrs(self.userId, ['createTime'], ['2016-04-03 17:18:05.985092'])
        
        
    def tearDown(self):
        self.testContext.stopMock()
        
    def testGenPopwnd(self):
        gen = TodoTasksGeneratorRegister.decodeFromDict(popwndlogin_conf)
        todotasks = gen.makeTodoTasks(self.gameId, self.userId, self.clientId, int(time.time()), isDayFirstLogin=True)
        print todotasks
    
if __name__ == '__main__':
    unittest.main()
    