# coding: utf-8

import pymysql.cursors


class MysqlConn(object):
    def __init__(self, host, port, user, password, db):
        self.conn = pymysql.connect(host=host, port=port,
                                    user=user, password=password,
                                    db=db, charset='utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor)

    def query(self, sql):
        with self.conn.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
            return result

    def execute(self, sql):
        with self.conn.cursor() as cursor:
            cursor.execute(sql)

    def getAllTableName(self):
        sql = 'SHOW TABLE STATUS WHERE ENGINE IS NOT NULL'
        tables = [table_status['Name'] for table_status in self.query(sql)]
        return tables

    def queryAllTable(self):
        tables = self.getAllTableName()
        sql = 'select * from %s'
        return dict([(table, self.query(sql % table)) for table in tables])

    def queryTable(self, match):
        sql = 'select * from %s'
        return dict([(table, self.query(sql % table))
                     for table in self.getAllTableName()
                     if match(table)])

def rmk(d, k, default_value=None):
    """删除字典的k"""
    if k in d:
        v = d[k]
        del d[k]

def cutkv(d, k, default_value=None):
    """从一个字典获取并删除数据, 返回 k, v 对"""
    v = default_value
    if k in d:
        v = d[k]
        del d[k]
    return k, v


def cutv(d, k, default_value=None):
    """从一个字典获取并删除数据, 返回 v"""
    k, v = cutkv(d, k, default_value)
    return v


def cutmkv(d, keys, default_values={}):
    """从一个字典获取并删除多项数据, 返回 [(k, v), ...] """
    return [cutkv(d, k, default_values.get(k)) for k in keys]


def cutmkv2dict(d, keys, filter_none=False, default_values={}):
    """从一个字典获取并删除多项数据, 返回这些数据组成的新字典
    filter_none: 是否过滤掉值为 None 的数据
    """
    r = dict(cutmkv(d, keys, default_values))
    return remove_none(r) if filter_none else r


def remove_none(d):
    """删除值为 None 的项并返回一个新的"""
    return dict([(k, v) for k, v in d.items() if v is not None])


def stripAll(obj):
    """找到所有的字符串执行 strip """
    def strip(o, k, v):
        if isinstance(k, (str, unicode)) and k.strip() != k:
            del o[k]
            k = k.strip()
            o[k] = v
        if isinstance(v, (str, unicode)):
            o[k] = v.strip()
    walkobj(obj, strip)
    return obj


def walkobj(o, fun):
    """遍历一个对象"""
    def pairizer(o):
        if isinstance(o, list):
            return lambda o: enumerate(o)
        elif isinstance(o, dict):
            return lambda o: o.items()

    def isContainer(o):
        return isinstance(o, (dict, list))

    if isContainer(o):
        for k, v in pairizer(o)(o):
            fun(o, k, v)
            if isContainer(v):
                walkobj(v, fun)


def list2table(data, default_values={}):
    """
    list: [{k1: v11, k2: v12}, {k1: v21, k2: v22}, ...] =>
    list: [[k1, k2], [v11, v12], [v21, v22], ...]

    default_values: {key: default_vavlue_of_key}
    """

    keys = []
    for line in data:
        keys += line.keys()
    keys = list(set(keys))

    return [keys] + [[line.get(key, default_values.get(key))
                      for key in keys]
                     for line in data]


def table2tsv(table):
    """
    '\t' 分割字段, '\n'分割记录的表
    """

    return '\n'.join(['\t'.join(map(str, line)) for line in table])


def table2sql(table, table_name):
    part1 = '\n'.join([
        'INSERT INTO ' + table_name,
        '(%s)' % (','.join(["%s" % k for k in table[0]]),),
        'VALUES',
        ])

    # values
    sql_v = lambda v: ("'%s'" % v) if v is not None else 'NULL'
    sql_values = lambda values: '(%s)' % ','.join(values)

    all_values = [sql_values([sql_v(v) for v in line]) for line in table[1:]]
    part2 = ',\n'.join(all_values)

    return '\n'.join(part1, part2)


def test():
    o = [{
          "config\r\n": {
            "\tmaxCount": 1,
            "minCount": 1
          },
          " content": [
            {
              "count": 1000,
              "desc": "凭票免费打女神专属赛",
              "itemId": "3065\r\n",
              "value": 1
            }
          ],
          "name": "TUPT女神赛门票*1000红包"
        }]
    print o
    stripAll(o)
    print o


if __name__ == '__main__':
    test()
