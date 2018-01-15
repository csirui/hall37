#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys

from difang.majiang2.tile.tile import new_hand_tails, human_tiles, human_one_tile, HuTiles
from difang.majiang2.win_rule.win_rule_jinan import MWinRuleJiNan
from difang.majiang2.win_rule.win_rule_sichuan import MWinRuleSichuan
from freetime.style import utf8_reload, Assert, FailError
from tyframework._private_.util.ftlog import ftlog

_rule = {
    "济南": MWinRuleJiNan(),
    "济南乱将": MWinRuleJiNan(jiang258=False),
    "四川": MWinRuleSichuan(),
    "": None
}


def test_flow(filename):
    def wrapper(func):
        def _wrapper():
            with open(os.path.join(os.path.dirname(__file__), "test_tiles", filename), mode="r") as fin:
                lines = map(str.strip, fin.readlines())
            for i, line in filter(lambda (_, x): not x.startswith("#") and len(x), enumerate(lines)):
                try:
                    func(line)
                except FailError as e:
                    print >> sys.stderr, "测试错误[%s][%s:%s]" % (e.message, i, line)
                except Exception:
                    print >> sys.stderr, "测试数据错误[%s:%s]" % (i, line)

        return _wrapper

    return wrapper


@test_flow("hu.txt")
def test_hu(line):
    tmp = line.split("|")[:5]
    tmp += [None] * (5 - len(tmp))
    rule, hand_tiles, last_tile, result, detail = tmp[:5]
    if len(result) == 0:
        result = None
    else:
        Assert(str(result).lower() in ("true", "false", "t", "f"), "true/false[%s]填写错误", result)
        result = str(result).lower() in ("true", "t")
    rule = _rule[rule]
    tiles = new_hand_tails(human_tiles(hand_tiles + last_tile))
    ret, hu_tiles = rule.isHu(tiles, human_one_tile(last_tile), True, [3])
    if result is not None:
        Assert(ret == result, "胡牌判断错误")
        if detail is not None and isinstance(hu_tiles, HuTiles):
            Assert(hu_tiles.title == detail, "胡牌的类型判断错误")


def test():
    test_hu()
    print
    "测试全部结束"


if __name__ == '__main__':
    utf8_reload()
    ftlog.exception()
    test()
