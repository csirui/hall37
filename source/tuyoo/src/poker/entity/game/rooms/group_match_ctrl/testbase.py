# -*- coding:utf-8 -*-
'''
Created on 2016年1月17日

@author: zhaojiangang
'''

match_conf = {
    "buyinchip": 0,
    "controlServerCount": 1,
    "controlTableCount": 0,
    "dummyUserCount": 0,
    "gameServerCount": 20,
    "gameTableCount": 500,
    "goodCard": 0,
    "hasrobot": 0,
    "ismatch": 1,
    "matchConf": {
        "desc": "开赛时间：21:30 \n报名费用：免费",
        "fees": [],
        "rank.rewards": [
            {
                "desc": "价值1499元的游戏耳机",
                "ranking": {
                    "end": 1,
                    "start": 1
                },
                "rewards": [
                    {
                        "count": 1,
                        "itemId": "item:4151"
                    }
                ]
            },
            {
                "desc": "10万金币",
                "ranking": {
                    "end": 4,
                    "start": 2
                },
                "rewards": [
                    {
                        "count": 100000,
                        "itemId": "user:chip"
                    }
                ]
            },
            {
                "desc": "1万金币",
                "ranking": {
                    "end": 10,
                    "start": 5
                },
                "rewards": [
                    {
                        "count": 10000,
                        "itemId": "user:chip"
                    }
                ]
            }
        ],
        "stages": [
            {
                "animation.type": 0,
                "card.count": 6,
                "chip.base": 1000,
                "chip.grow": 0.3,
                "chip.grow.base": 200,
                "chip.grow.incr": 100,
                "chip.times": 60,
                "chip.user": 12000,
                "chip.user.2.rate": 0,
                "chip.user.3.base": 0,
                "lose.user.chip": 0.5,
                "name": "海选赛",
                "rise.user.count": 24,
                "rise.user.refer": 30,
                "seat.principles": 1,
                "grouping.type": 2,
                "grouping.user.count": 30,
                "type": 1
            },
            {
                "animation.type": 1,
                "card.count": 2,
                "chip.base": 100,
                "chip.grow": 0.5,
                "chip.times": 3600,
                "chip.user": 3,
                "chip.user.3.base": 300,
                "name": "24强赛",
                "rise.user.count": 12,
                "seat.principles": 2,
                "type": 2
            },
            {
                "animation.type": 1,
                "card.count": 2,
                "chip.base": 100,
                "chip.grow": 0.5,
                "chip.times": 3600,
                "chip.user": 2,
                "chip.user.2.rate": 0.2,
                "name": "12强赛",
                "rise.user.count": 6,
                "seat.principles": 2,
                "type": 2
            },
            {
                "animation.type": 3,
                "card.count": 2,
                "chip.base": 100,
                "chip.grow": 0.5,
                "chip.times": 3600,
                "chip.user": 2,
                "chip.user.2.rate": 0.2,
                "name": "6强赛",
                "rise.user.count": 3,
                "seat.principles": 2,
                "type": 2
            },
            {
                "animation.type": 2,
                "card.count": 2,
                "chip.base": 100,
                "chip.grow": 0.5,
                "chip.times": 3600,
                "chip.user": 2,
                "chip.user.2.rate": 0.2,
                "name": "决赛",
                "rise.user.count": 1,
                "seat.principles": 2,
                "type": 2
            }
        ],
        "start": {
            "fee.type": 0,
            "maxplaytime": 7200,
            "prepare.times": 0,
            "signin.times": 2400,
            "start.speed": 6,
            "times": {
                "days": {
                    "first": "",
                    "interval": "1d",
                    "count": 100,
                },
                "times_in_day": {
                    "first": "00:00",
                    "interval": 1,
                    "count": 2000
                }
            },
            "type": 2,
            "user.groupsize": 2000,
            "user.maxsize": 2000,
            "user.minsize": 3,
            "user.next.group": 0
        },
        "table.seat.count": 3,
        "tips": {
            "infos": [
                "积分相同时，按报名先后顺序确定名次。",
                "积分低于淘汰分数线会被淘汰，称打立出局。",
                "打立赛制有局数上限，打满局数会等待他人。",
                "打立阶段，轮空时会记1局游戏。",
                "定局赛制，指打固定局数后按积分排名。",
                "每局会按照开局时的底分结算。",
                "比赛流局时，可能会有积分惩罚。"
            ],
            "interval": 5
        }
    },
    "maxCoin": -1,
    "maxCoinQS": -1,
    "maxLevel": -1,
    "minCoin": -1,
    "minCoinQS": -1,
    "name": "途游阿里赛",
    "playDesc": "",
    "playMode": "happy",
    "robotUserCallUpTime": 10,
    "robotUserMaxCount": 0,
    "robotUserOpTime": [
        5,
        12
    ],
    "roomFee": 45,
    "roomMutil": 50,
    "sendCoupon": 0,
    "showCard": 0,
    "tableConf": {
        "autochange": 1,
        "basebet": 1,
        "basemulti": 1,
        "cardNoteChip": 500,
        "canchat": 0,
        "coin2chip": 1,
        "grab": 1,
        "gslam": 128,
        "lucky": 0,
        "maxSeatN": 3,
        "optime": 20,
        "passtime": 5,
        "rangpaiMultiType": 1,
        "robottimes": 1,
        "tbbox": 0,
        "unticheat": 1
    },
    "typeName": "big_match",
    "winDesc": ""
}


class MyRoom():
    def __init__(self, roomId):
        self.roomId = roomId


if __name__ == '__main__':
    pass
