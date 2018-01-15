# coding=UTF-8
'''自定义元类
'''

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

from freetime.util import log as ftlog


class MultiDict(dict):
    '''
    扩展的字典
    使用此字典, 可以附加一组特殊的属性值到字典当中, 方便控制特殊属性和当前字典的生命周期一致性
    例如: 再getConf后取得一个字典配置, 但是需要进行一定的数据转换才可使用,
        那么就可以将转换后的结构放在setExtendAttr中, 再次使用的时候, 直接使用上次转换后的数据即可
    '''

    def __init__(self, odict=None):
        if odict:
            self.update(odict)
        self.__extend_attrs__ = {}

    def getExtendAttr(self, key):
        return self.__extend_attrs__.get(key, None)

    def setExtendAttr(self, key, value):
        self.__extend_attrs__[key] = value


class MultiList(list):
    '''
    扩展的字典
    使用此字典, 可以附加一组特殊的属性值到字典当中, 方便控制特殊属性和当前字典的生命周期一致性
    例如: 再getConf后取得一个字典配置, 但是需要进行一定的数据转换才可使用,
        那么就可以将转换后的结构放在setExtendAttr中, 再次使用的时候, 直接使用上次转换后的数据即可
    '''

    def __init__(self, olist=None):
        if olist:
            self.extend(olist)
        self.__extend_attrs__ = {}

    def getExtendAttr(self, key):
        return self.__extend_attrs__.get(key, None)

    def setExtendAttr(self, key, value):
        self.__extend_attrs__[key] = value


class Singleton(type):
    def __init__(self, name, bases, dic):
        super(Singleton, self).__init__(name, bases, dic)
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            ftlog.debug("creating a Singleton instance of %s" % self.__name__)
            self.instance = super(Singleton, self).__call__(*args, **kwargs)
        return self.instance
