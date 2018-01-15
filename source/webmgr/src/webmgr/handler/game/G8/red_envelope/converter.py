# coding: utf-8

"""
红包配置转换器
"""

__author__ = ['Wang Tao']

import copy

import webmgr.utils.cfgutil as util

comments = [
        "红包分享配置",
        "-------------------------------------------------------------------------------",
        "win_share: 在牌桌盈利统计这块加入红包分享逻辑，配置盈利区间内触发指定红包",
        "配置说明: start <= win_chip <= stop : 发放 red_packet_id 红包",
        "-------------------------------------------------------------------------------",
        "match_share: 可配置 M ~ N 名触发指定红包",
        "配置说明: start <= 名次 <= stop: 发放 red_packet_id 红包",
        "match_id 用来指定比赛类型，可指定多个",
        "-------------------------------------------------------------------------------",
        "red_envelope: 红包内容配置",
        "content: 奖励内容配置",
        "    itemId: 资产ID, 可以是: coupon/chip/diamond/charm/exp/道具ID",
        "    value:  以这个数量为一组",
        "    count:  组数",
        "  所以, 总的数量是: value x count 个",
        "config: ",
        "    min ~ max: 随机数范围。这个范围内取一个随机数N,表示每个红包内有N组",
        "-------------------------------------------------------------------------------",
        "expireDays: 有效期, 单位: 天。不配置时默认7天",
        "clientId: 页面clientId",
        "红包ID说明：",
        "1、红包ID为6位",
        "2、首位为游戏编号，德州为8",
        "3、2和3位为红包类型区分（看右侧说明）",
        "4、后三位为红包编号，按照自然序列累计",
        "红包类型说明（8__001）：",
        "00：测试红包",
        "01：纯话费红包",
        "02：纯门票红包",
        "03：纯金币红包",
        "04：话费+门票红包",
        "05：金币+门票红包",
        "06：话费+金币红包",
        "07：话费+金币+门票红包"
    ]


def convert(handler, all_tables={}):
    res = {}
    tables = {}

    if not all_tables:
        matcher = lambda name: name.startswith('red_envelope')
        tables = handler.getConn().queryTable(matcher)
    else:
        for name, data in all_tables.items():
            if name.startswith('red_envelope'):
                tables[name] = copy.deepcopy(data)

    # 注释
    res['_comments'] = comments

    # 基本配置
    res['common'] = tables['red_envelope_common'][0]

    # 红包内容
    res['red_envelope_type'] = types = {}
    for type_conf in tables['red_envelope_content']:
        util.stripAll(type_conf)
        type_id = util.cutv(type_conf, 'type_id')
        util.rmk(type_conf, 'id')
        if type_id not in types:
            types[type_id] = {'content': []}

        keys = ['minCount', 'maxCount']
        types[type_id]['config'] = util.cutmkv2dict(type_conf, keys)

        keys = ['itemId', 'value', 'count', 'desc']
        types[type_id]['content'].append(util.cutmkv2dict(type_conf, keys))
        types[type_id].update(type_conf)



    # 分享点
    res['match_share'] = []
    res['manual_share'] = []
    res['win_share'] = []
    res['pay_share'] = []
    res['register'] = []
    res['login'] = []
    for share_point in tables['red_envelope_share_point']:
        util.stripAll(share_point)
        sp = {}
        keys = ['text_todo', 'text_share', 'icon_share']
        util.rmk(share_point, 'id')
        sp['res'] = util.cutmkv2dict(share_point, keys)
        for k, v in sp['res'].items():
            sp['res'][k] = v.replace('\\n', '\n')
        sp['red_envelope_type_id'] = util.cutv(share_point, 'type_id')
        if share_point.get('match_ids'):
            sp['match_ids'] = util.cutv(share_point, 'match_ids').split(',')
        sp_type = util.cutv(share_point, 'type')
        sp.update(share_point)
        sp = util.remove_none(sp)
        util.stripAll(sp)
        res[sp_type].append(sp)

    # 不分享的
    cids = [cfg['clientId'] for cfg in tables['red_envelope_no_share']]
    res['no_share'] = [cid.strip() for cid in cids]

    return res