# -*- coding:utf-8 -*-
'''
Created on 2014年11月22日

@author: zjgzzz@126.com
'''
import inspect


def getModuleAttr(pkgpath):
    '''
    动态加载对应的pkgpath,并取得pkgpath中的指定的属性的值
    例如: pkgpath为: com.tuyoo.test.A
        那么import的包为com.tuyoo.test, 取的该包中A的值返回, 
        若A不存在这抛出异常
    '''
    import importlib
    parts = pkgpath.rsplit('.', 1)
    if len(parts) != 2:
        raise ValueError('Bad attrpath:' + pkgpath)
    module = importlib.import_module(parts[0])
    attr = getattr(module, parts[1])
    if not attr:
        raise TypeError('Not found attr:' + parts[0] + '.' + parts[1])
    return attr


def getModuleClsIns(clspath):
    '''
    动态加载对应的clspath,并取得pkgpath中的指定的cls的实例值
    例如: pkgpath为: com.tuyoo.test.ClsA
        那么import的包为com.tuyoo.test, 取的该包中ClsA, 进行无参数的实例化,返回ClsA() 
    '''
    clzz = getModuleAttr(clspath)
    return clzz()


def getObjectFunctions(obj, funhead, funargcount):
    '''
    获取obj对象中的方法集合
        方法名称过滤: 必须以funhead开头
        方法参数个数过滤: 方法的参数个数等于funargcount
    '''
    funs = {}
    for key in dir(obj):
        if key.find(funhead) == 0:
            try:
                methodfun = getattr(obj, key)
                if inspect.ismethod(methodfun) and len(inspect.getargspec(methodfun)[0]) == funargcount:
                    key = key[len(funhead):]
                    funs[key] = methodfun
            except AttributeError:
                continue
    return funs


class TYClassRegister(object):
    '''
    类注册表
    '''
    _typeid_clz_map = {}

    @classmethod
    def findClass(cls, typeId):
        '''
        依据类型, 取得对应的注册的对象
        '''
        # ftlog.debug('TYClassRegister.classMap:', cls._typeid_clz_map)
        return cls._typeid_clz_map.get(typeId)

    @classmethod
    def unRegisterClass(cls, typeId):
        '''
        删除一个typeId的注册对象
        '''
        if typeId in cls._typeid_clz_map:
            del cls._typeid_clz_map[typeId]

    @classmethod
    def registerClass(cls, typeId, clz):
        '''
        以typeId为关键字,注册对象clz
        注册的typeId不允许重复
        '''
        oldClz = cls.findClass(typeId)
        if oldClz:
            raise TypeError('%s already register %s for type %s' % (cls, oldClz, typeId))
        cls._typeid_clz_map[typeId] = clz


def findPyFileListUnderModule(moduleName):
    '''
    查找所有的直属的py文件,并进行动态装载，只查当前所属,不递归查找py文件
    '''
    import importlib
    import os
    try:
        m = importlib.import_module(moduleName)
    except ImportError, _:
        return {}
    pymodule = set()
    for mpath in m.__path__:
        pyfiles = os.listdir(mpath)
        for pyfile in pyfiles:
            if pyfile.find('__init__') < 0 and (pyfile.endswith('.py') or pyfile.endswith('.pyc')):
                pymodule.add(moduleName + '.' + pyfile.rsplit('.', 1)[0])
    return pymodule


def findMethodUnderModule(moduleName, methodName, filterFun=None):
    '''
    查找给出的模块下的所有直属py文件， 并使用filterFun对直属的py文件进行过滤
    再过滤后的py文件中查找给出的methodName函数定义（只对照函数名，不检查参数）的列表集合
    '''
    import importlib
    pymodule = findPyFileListUnderModule(moduleName)
    # 装载所有的直属的py文件
    mlist = []
    for pymname in pymodule:
        if filterFun and not filterFun(pymname):
            continue
        pym = importlib.import_module(pymname)
        m = getattr(pym, methodName, None)
        if callable(m) and m not in mlist:
            mlist.append(m)
    return mlist
