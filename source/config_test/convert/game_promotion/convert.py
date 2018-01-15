# -*- coding=utf-8
'''
Created on 2015年8月3日

@author: zhaojiangang
'''
import json

import gdss


template2clientIds = {
    "template.3_5_02_wifikey":[
        "Android_3.503_wifikey.weakChinaMobile,YDJD.0-hall6.wifikeydemo.dj",
        'Android_3.501_wifikey.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wifikey.dj',
        'Android_3.501_wifikey.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wifikey.happy',
        'Android_3.503_wifikey.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wifikey.dj',
        'Android_3.503_wifikey.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wifikey.happy',
    ],
    "template.3_5_02_ios": [
        "IOS_3.502_tuyoo.appStore.0-hall6.tuyoo.huanle",
        'IOS_3.501_tuyoo.appStore.0-hall6.tuyoo.cherry',
        'IOS_3.60_360.360.0-hall6.360.day',
        "IOS_3.5_tuyoo.tuyoo.0.tuyoo.dj",
        "IOS_3.50_tuyoo.tuyoo.0-hall6.tuyoo.dj",
    ],
    "template.3_5_02":[
        'Android_3.503_tuyoo.tuyoo.0-hall6.ali.kuaile',
        'Android_3.60_tuyoo.tuyoo.0-hall6.ali.people',
        'Android_3.60_tuyoo.tuyoo.0-hall6.ali.fk',
        'Android_3.503_tuyoo.tuyoo.0-hall6.ali.rich',
        'Android_3.5030_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.dj',
        'Android_3.5030_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.happy',
        'Android_3.5030_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.tu',
        'Android_3.5030_360.360,weakChinaMobile,woStore.0-hall6.360.laizi',
        'Android_3.503_tuyoo.gefusdk.0-hall6.getui.dj',
        'Android_3.503_tuyoo.gefusdk.0-hall6.gefu.dj',
        'Android_3.503_360.360.0-hall6.360.win',
        'Android_3.503_360.360.0-hall6.360.day',
        'Android_3.503_kugou.weakChinaMobile,woStore,aigame.0-hall6.kugou.kugou',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.ppzhushou.dj',
        'Android_3.503_jinritoutiao.jinritoutiao,weakChinaMobile,woStore,YDJD.0-hall6.jinri.jinri',
        'Android_3.5031_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.dj',

        'Android_3.503_tuyoo.jinritoutiao,weakChinaMobile,woStore,YDJD.0-hall6.jinri.jinri',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qingmeng.dj',
        'Android_3.503_meizu.meizu,weakChinaMobile,woStore,aigame,YDJD.0-hall6.meizu.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.HTC.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.kubi.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qingmeng.dj',
        'Android_3.503_360.360.0-hall6.360.kuaile',
        'Android_3.503_360.360.0-hall6.360.people',
        'Android_3.503_360.360.0-hall6.360.fk',
        'Android_3.503_360.360.0-hall6.360.rich',
        'Android_3.5030_360.360.0-hall6.360.kuaile',
        'Android_3.5030_360.360.0-hall6.360.people',
        'Android_3.5030_360.360.0-hall6.360.fk',
        'Android_3.5030_360.360.0-hall6.360.rich',

        'Android_3.503_360.360,weakChinaMobile.0-hall6.360.laizi',
    
        'Android_3.503_tuyoo.woStore,aigame,YDJD.0-hall6.zhongpusai.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.ali.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sanxing.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sohuvideo.tu',
        'Android_3.503_huawei.huawei,weakChinaMobile,woStore,aigame,YDJD.0-hall6.huawei.dj',
        'Android_3.503_tuyoo.lenovo,weakChinaMobile,woStore,aigame,YDJD.0-hall6.lenovo.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinligame.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.meitu.dj',
        'Android_3.503_tuyoo.lenovo,weakChinaMobile,woStore,aigame,YDJD.0-hall6.lenovo.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.2345.tu',
        'Android_3.503_meizu.meizu,weakChinaMobile,woStore,aigame,YDJD.0-hall6.meizu.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.apphui.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wandou.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.chongchongzhushou.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.youyoucun.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.baidusearch.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.360search.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sougou.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wandou.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sanxing.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.4399.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sanxing.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.ali.tu',
        'Android_3.503_nearme.nearme,weakChinaMobile,woStore,aigame,YDJD.0-hall6.oppo.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.gdt.tu',
        
        'Android_3.503_nearme.nearme,weakChinaMobile,woStore,aigame,YDJD.0-hall6.oppo.dj',

        'Android_3.503_tuyoo.duoku,weakChinaMobile,woStore,aigame,YDJD.0-hall6.91new.dj',
        'Android_3.503_tuyoo.duoku,weakChinaMobile,woStore,aigame,YDJD.0-hall6.baidunew.dj',
        'Android_3.503_tuyoo.duoku,weakChinaMobile,woStore,aigame,YDJD.0-hall6.duokunew.dj',
        'Android_3.503_tuyoo.duoku,weakChinaMobile,woStore,aigame,YDJD.0-hall6.bdtiebanew.dj',
        'Android_3.503_pps.pps,weakChinaMobile,woStore,aigame,YDJD.0-hall6.pps.dj',
        'Android_3.503_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.tu',
        'Android_3.503_mi.mi,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.coolpad.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qq.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.tuyoo.tu',
        'Android_3.503_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.happy',
        'Android_3.503_huawei.huawei,weakChinaMobile,woStore,aigame,YDJD.0-hall6.huawei.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qingmeng.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.HTC.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sohuvideo.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.kubi.tu',
        'Android_3.503_tuyoo.woStore,aigame,YDJD.0-hall6.cocosplay.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.360search.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.baidusearch.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.chongchongzhushou.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.youyoucun.happy',
        'Android_3.503_youku.youku,weakChinaMobile,aigame,YDJD.0-hall6.youku.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sougou.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.coolpad.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.ali.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sougou.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.kunda.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.litianbaoli.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qq.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.ruilongxingkong.dj',
        'Android_3.503_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.muzhi.dj',
        'Android_3.503_midanji.midanji,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.midanji',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.ali.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sougou.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.coolpad.dj',
        'Android_3.503_midanji.midanji,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.midanji',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qq.happy',
        'Android_3.503_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.tu',
        'Android_3.503_huawei.huawei,weakChinaMobile,woStore,aigame,YDJD.0-hall6.huawei.tu',
        'Android_3.503_mi.mi,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.tu',
        'Android_3.503_tuyoo.lenovo,weakChinaMobile,woStore,aigame,YDJD.0-hall6.lenovo.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.2345.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.coolpad.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qq.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.tuyoo.tu',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wandou.tu',
        'Android_3.503_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.happy',
        'Android_3.503_meizu.meizu,weakChinaMobile,woStore,aigame,YDJD.0-hall6.meizu.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.4399.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.apphui.happy',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wandou.happy',
        'Android_3.503_huawei.huawei,weakChinaMobile,woStore,aigame,YDJD.0-hall6.huawei.dj',
        'Android_3.503_meizu.meizu,weakChinaMobile,woStore,aigame,YDJD.0-hall6.meizu.dj',
        'Android_3.503_mi.mi,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.dj',
        'Android_3.503_pps.pps,weakChinaMobile,woStore,aigame,YDJD.0-hall6.pps.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.leshi.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.meitu.dj',
        'Android_3.503_vivo.vivo,weakChinaMobile,woStore,aigame,YDJD.0-hall6.vivo.dj',
        'Android_3.503_midanji.midanji,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.midanji',
        'Android_3.503_tuyoo.duoku,weakChinaMobile,woStore,aigame,YDJD.0-hall6.91new.dj',
        'Android_3.503_tuyoo.duoku,weakChinaMobile,woStore,aigame,YDJD.0-hall6.baidunew.dj',
        'Android_3.503_tuyoo.duoku,weakChinaMobile,woStore,aigame,YDJD.0-hall6.duokunew.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.ali.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.googleplay.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.huashuo.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.kunda.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.litianbaoli.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qingcheng.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qq.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.ruilongxingkong.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sougou.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wandou.dj',
        'Android_3.503_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.dj',
        'Android_3.503_tuyoo.lenovo,weakChinaMobile,woStore,aigame,YDJD.0-hall6.lenovo.dj',
        'Android_3.503_tuyoo.weakChinaMobile,aigame,YDJD.0-hall6.guangsheng.dj',
        'Android_3.503_tuyoo.weakChinaMobile,aigame,YDJD.0-hall6.tianyu.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.coolpad.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinligame.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.kubi.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.muzhi.dj',
        'Android_3.503_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sanxing.dj',
        'Android_3.503_yyduowan.yyduowan.0-hall6.yygame.dj',
        'Android_3.503_tuyoo.woStore.0-hall6.ltwo.dj',
        'Android_3.501_youku.youku,weakChinaMobile,aigame,YDJD.0-hall6.youku.happy',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.tu',
        'Android_3.5010_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.dj',
        'Android_3.501_tuyoo.weakChinaMobile,aigame,YDJD.0-hall6.ruilongxingkong.dj',
        'Android_3.501_tuyoo.weakChinaMobile,aigame,YDJD.0-hall6.tianyu.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.kubi.dj',
        'Android_3.501_huawei.huawei,weakChinaMobile,woStore,aigame,YDJD.0-hall6.huawei.tu',
        'Android_3.501_meizu.meizu,weakChinaMobile,woStore,aigame,YDJD.0-hall6.meizu.happy',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.kubi.tu',
        'Android_3.503_kugou.tuyoo.0-hall6.kugou.kugou',
        'Android_3.501_tuyoo.weakChinaMobile,aigame,YDJD.0-hall6.tianyu.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.tu',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.kubi.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sohuvideo.tu',
        'Android_3.60_360.360.0-hall6.360.fk',
        'Android_3.60_360.360.0-hall6.360.people',
        'Android_3.60_360.360.0-hall6.360.day',
        'Android_3.70_360.360.0-hall6.360.day',
        'IOS_3.70_360.360.0-hall6.360.day',
        'Android_3.5010_kugou.tuyoo.0-hall6.kugou.kugou',
        'Android_3.502_360.360,weakChinaMobile.0-hall6.360.laizi',
        'Android_3.5010_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.dj',
        'Android_3.501_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.dj',
        'Android_3.501_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.tu',
        'Android_3.501_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.happy',
        'Android_3.501_nearme.nearme,weakChinaMobile,woStore,YDJD.0-hall6.oppo.dj',
        'Android_3.502_360.360.0-hall6.360.win',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.qq.dj',
        'Android_3.501_tuyoo.duoku,weakChinaMobile,YDJD.0-hall6.baidunew.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qq.tu',
        'Android_3.501_huawei.huawei,weakChinaMobile,woStore,aigame,YDJD.0-hall6.huawei.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.qq.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.wifikey.dj',
        'Android_3.5010_mi.mi,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.dj',
        'Android_3.5010_tuyoo.lenovo,weakChinaMobile,woStore,aigame,YDJD.0-hall6.lenovo.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wifikey.happy',
        'Android_3.501_mi.mi,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.coolpad.dj',
        'Android_3.501_tuyoo.duoku,weakChinaMobile,YDJD.0-hall6.91new.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.wifikey.dj',
        'Android_3.502_360.360.0-hall6.360.day',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.tuyoo.dj',
        'Android_3.501_tuyoo.weakChinaMobile.0-hall6.ydmm.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qq.happy',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.baidusearch.tu',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.ali.dj',
        'Android_3.501_tuyoo.weakChinaMobile.0-hall6.ydmm.tu',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.wandou.dj',
        'Android_3.501_YDJD.YDJD.0-hall6.ydjd.dj',
        'Android_3.501_mi.mi,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.tu',
        'Android_3.50_360.360.0-hall6.360.win',
        'Android_3.501_tuyoo.lenovo,weakChinaMobile,woStore,aigame,YDJD.0-hall6.lenovo.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.wandou.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.apphui.happy',
        'Android_3.5010_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.ali.dj',
        'Android_3.50_360.360.0-hall6.360.day',
        'Android_3.501_360.360,weakChinaMobile.0-hall6.360.laizi',
        'Android_3.501_360.360.0-hall6.360.people',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.tianyu.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.kunda.dj',
        'Android_3.501_360.360.0-hall6.360.fk',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.tianyu.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.cpa30.happy',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wandou.tu',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.360search.tu',
        'Android_3.501_tuyoo.lenovo,weakChinaMobile,woStore,aigame,YDJD.0-hall6.lenovo.tu',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.2345.tu',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.coolpad.tu',
        'Android_3.501_360.360.0-hall6.360.kuaile',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.litianbaoli.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.sougou.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.tuyoo.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.4399.happy',
        'Android_3.501_uc.uc.0-hall6.uc.dj',
        'Android_3.502_360.360.0-hall6.360.kuaile',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinligame.dj',
        'Android_3.501_360.360.0-hall6.360.rich',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.muzhi.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sanxing.dj',
        'Android_3.501_tuyoo.weakChinaMobile.0-hall6.ydmm.happy',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.kunda.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wandou.happy',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.dj',
        'Android_3.502_360.360.0-hall6.360.people',
        'Android_3.502_360.360.0-hall6.360.fk',
        'Android_3.501_YDJD.YDJD.0-hall6.ydjd.happy',
        'Android_3.501_tuyoo.duoku,weakChinaMobile,YDJD.0-hall6.duokunew.dj',
        'Android_3.501_tuyoo.jinri,jinritoutiao.0-hall6.jinri.jinri',
        'Android_3.501_YDJD.YDJD.0-hall6.ydjd.tu',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.leshi.dj',
        'Android_3.501_yyduowan.yyduowan.0-hall6.yygame.dj',
        'Android_3.501_kugou.tuyoo.0-hall6.kugou.kugou',
        'Android_3.501_pps.pps,weakChinaMobile,woStore,aigame,YDJD.0-hall6.pps.dj',
        'Android_3.5010_pps.pps,weakChinaMobile,woStore,aigame,YDJD.0-hall6.pps.dj',
        'Android_3.501_tuyoo.YDJD.0-hall6.sohuvideo.tu',
        'Android_3.501_YDJD.YDJD.0-hall6.ydjd.midanji',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.sougou.tu',
        'Android_3.501_tuyoo.duoku,weakChinaMobile,YDJD.0-hall6.bdtiebanew.dj',
        'Android_3.502_360.360.0-hall6.360.rich',
        'Android_3.501_360.360.0-hall6.360.dj',
        'Android_3.501_360.360,weakChinaMobile,aigame,YDJD.0-hall6.360.dj',
        'Android_3.501_360.360,weakChinaMobile.0-hall6.360.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.litianbaoli.dj',
        'Android_3.501_tuyoo.woStore,aigame,YDJD.0-hall6.leshiphone.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.duokunew.dj',
        'Android_3.501_360.360.0-hall6.360.tu',
        "Android_3.502_360.360.0-hall6.360.day",
        "Android_3.502_360.360.0-hall6.360.win",
        "Android_3.501_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.dj",
        "Android_3.501_mi.mi,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.dj",
        "Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.qq.dj",
        "Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.wandou.dj",
        "Android_3.501_tuyoo.lenovo,weakChinaMobile,woStore,aigame,YDJD.0-hall6.lenovo.dj",
        "Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.coolpad.dj",
        "Android_3.501_pps.pps,weakChinaMobile,woStore,aigame,YDJD.0-hall6.pps.dj",
        "Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.sougou.dj",
        "Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.googleplay.dj",
        "Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.litianbaoli.dj",
        "Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.tianyu.dj",
        "Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.kunda.dj",
        "Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.ali.dj",
        "Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.dj",
        "Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.wifikey.dj",
        "Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.tuyoo.dj",
        "Android_3.501_tuyoo.YDJD,woStore,aigame.0-hall6.sohuvideo.dj",
        "Android_3.501_yyduowan.yyduowan.0-hall6.yygame.dj",
        'Android_3.5010_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.dj',
        'Android_3.5010_pps.pps.weakChinaMobile,woStore,aigame,YDJD.0-hall6.pps.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.qq.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.wandou.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.wifikey.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.qq.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.wandou.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.jinli.dj',
        'Android_3.5010_pps.pps,weakChinaMobile,woStore,aigame,YDJD.0-hall6.pps.dj',
        'Android_3.5010_tuyoo.weakChinaMobile,YDJD.0-hall6.ali.dj',
        'Android_3.5010_mi.mi,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.dj',
        'Android_3.5010_tuyoo.lenovo,weakChinaMobile,woStore,aigame,YDJD.0-hall6.lenovo.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.qingcheng.dj',
        'Android_3.501_nearme.nearme,weakChinaMobile,woStore,YDJD.0-hall6.oppo.dj',
        'Android_3.501_tuyoo.duoku,weakChinaMobile,YDJD.0-hall6.duokunew.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.bdtiebanew.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.baidunew.dj',
        'Android_3.501_tuyoo.weakChinaMobile,YDJD.0-hall6.91new.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wifikey.happy',
        'Android_3.501_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.happy',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.tuyoo.tu',
        'Android_3.501_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall6.360.tu',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.qq.tu',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.2345.tu',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.coolpad.dj',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.apphui.happy',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.360search.tu',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.wandou.tu',
        'Android_3.501_mi.mi,weakChinaMobile,woStore,aigame,YDJD.0-hall6.mi.tu',
        'Android_3.501_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall6.coolpad.tu',
        'Android_3.501_360.360.0-hall6.360.people',
        'Android_3.501_360.360.0-hall6.360.fk',
        'Android_3.501_360.360.0-hall6.360.rich',
        'Android_3.502_360.360.0-hall6.360.fk',
        'Android_3.502_360.360.0-hall6.360.kuaile',
        'Android_3.502_360.360.0-hall6.360.people',
        'Android_3.502_360.360.0-hall6.360.rich',
        'Android_3.60_360.360.0-hall6.360.day',
        'Android_3.70_360.360.0-hall6.360.day',
        'IOS_3.70_360.360.0-hall6.360.day',
        'Android_3.601_360.360.0-hall6.360.dj',
        "IOS_3.60_360.360.0-hall8.360.day",
        "Android_3.60_360.360.0-hall8.360.tu",
        "Android_3.501_tuyoo.weakChinaMobile.0-hall6.apphui.dj",
    ],
    "template.online.beta":[
        "Android_3.50_tuyoo.tuyoo.0-hall6.tuyoo.dj",
    ],
    "template.mj": [
        "Android_3.50_tuyoo.weakChinaMobile.0-hall7.qq.dj",
        'Android_3.50_360.360,weakChinaMobile.0-hall7.360.fk',
        'Android_3.502_360.360,weakChinaMobile,woStore,aigame,YDJD.0-hall7.360.dj',
        'Android_3.502_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall7.ali.dj',
        'Android_3.502_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall7.googleplay.dj',
        'Android_3.502_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall7.coolpad.dj',
        'Android_3.502_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall7.qq.dj',
        'Android_3.502_tuyoo.weakChinaMobile,woStore,aigame,YDJD.0-hall7.sougou.dj',
    ],
    "template.mj.ios": [
        'IOS_3.502_tuyoo.appStore.0-hall7.appStore.kuaile',
        'IOS_3.501_tuyoo.appStore.0-hall7.tuyoo.cherry',
        "IOS_3.502_tuyoo.tuyoo.0-hall7.tuyoo.dj",
    ]
}

def writeTemplateForClientId(clientIdNumber, templateName):
    d = {
         "template" : templateName
    }
    jstr = json.dumps(d, ensure_ascii=False, indent=4)
    f = open('../../game/9999/promote/%s.json' % (clientIdNumber), 'w')
    f.write(jstr)
    f.close()
    
if __name__ == '__main__':
    clientIdMap = gdss.syncDataFromGdss('getClientIdDict')
    for templateName, clientIds in template2clientIds.iteritems():
        for clientId in clientIds:
            clientIdNumber = clientIdMap.get(clientId)
            if clientIdNumber:
                writeTemplateForClientId(clientIdNumber, templateName)
        
        