# -*- coding=utf-8 -*-

sql_schema = '''
DROP SCHEMA IF EXISTS `tydata%d`;
CREATE SCHEMA IF NOT EXISTS `tydata%d` CHARACTER SET utf8;
'''

sql_table = '''
DROP TABLE IF EXISTS `tydata%d`.`t%d`;
CREATE TABLE `tydata%d`.`t%d` (
  `userid` BIGINT UNSIGNED NOT NULL,
  `writetime` DATETIME NOT NULL,
  `data` LONGTEXT NOT NULL,
  PRIMARY KEY (`userid`)
) ENGINE = MyISAM CHARACTER SET utf8;
'''

def make_swap_table():
    for i in xrange(8) :
        print sql_schema % (i, i)
        for x in xrange(200) :
            print sql_table % (i, x, i, x)
    print ''
    print ''

if __name__ == '__main__' :
    make_swap_table()
