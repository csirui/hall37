# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from hashlib import md5
import inspect, uuid, json, base64, urllib, re, struct
import os


__buffered_reg = {}
int62 = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
__int62dictint = {}
__int62dictstr = {}
for x in xrange(len(int62)) :
    __int62dictint[x] = int62[x]
    __int62dictstr[int62[x]] = x


def getEnv(ekey, defaultval):
    return os.environ.get(ekey, defaultval)


def cloneData(data):
    return json.loads(json.dumps(data))

def uuid():
    return str(uuid.uuid4()).replace('-', '')


def dumps(obj):
    return json.dumps(obj, separators=(',', ':'))


def dumpsbase64(obj):
    jstr = json.dumps(obj, separators=(',', ':'))
    return base64.b64encode(jstr)


def loadsbase64(base64jsonstr, decodeutf8=False):
    jsonstr = b64decode(base64jsonstr)
    datas = json.loads(jsonstr)
    if decodeutf8 :
        datas = decodeObjUtf8(datas)
    return datas


def loads(jsonstr, decodeutf8=False, ignoreException=False, execptionValue=None):
    if ignoreException :
        try:
            datas = json.loads(jsonstr)
        except:
            datas = execptionValue
    else:
        datas = json.loads(jsonstr)
    if datas and decodeutf8 :
        datas = decodeObjUtf8(datas)
    return datas


def b64decode(base64str):
    base64str = base64str.replace(' ', '+')
    return base64.b64decode(base64str)


def b64encode(normalstr):
    return base64.b64encode(normalstr)


def md5digest(md5str):
    m = md5()
    m.update(md5str)  
    md5code = m.hexdigest()
    return md5code.lower()


def urlencode(params):
    return urllib.urlencode(params)


def reg_match(regExp, checkStr):
    if regExp == '*' :
        return True
    if regExp in __buffered_reg :
        breg = __buffered_reg[regExp]
    else:
        breg = re.compile(regExp)
        __buffered_reg[regExp] = breg
    if breg.match(checkStr) :
        return True
    return False


def reg_matchlist(regExpList, checkStr):
    for regExp in regExpList :
        if reg_match(regExp, checkStr) :
            return True
    return False


def tostr62(int10, slenfix=0):
    if int10 <= 0 :
        s62 = '0'
    else:
        s62 = ''
        while int10 > 0 :
            c = __int62dictint[int10 % 62]
            int10 = int10 / 62
            s62 = c + s62
    
    if slenfix > 0  :
        while len(s62) < slenfix :
            s62 = '0' + s62
        if len(s62) > slenfix :
            s62 = s62[-slenfix:]
    return s62


def toint10(str62):
    int10 = 0
    slen = len(str62)
    for x in xrange(slen) :
        m = __int62dictstr[str62[x]]
        if m > 0 :
            for _ in xrange(slen - x - 1):
                m = m * 62
        int10 = m + int10
    return int10
    

def getJsonStr(jsonstr, key, defaultVal=''):
    key = '"' + key + '":'
    i = jsonstr.find(key)
    if i > 0 :
        x = jsonstr.find('"', i + len(key))
        y = jsonstr.find('"', x + 1)
        return jsonstr[x + 1:y]
    else:
        return defaultVal


def getJsonInt(jsonstr, key, defaluVal=0):
    key = '"' + key + '":'
    i = jsonstr.find(key)
    if i > 0 :
        linelen = len(jsonstr)
        i = i + len(key)
        value = 0
        flg = 0
        while i < linelen:
            c = jsonstr[i]
            if c == '0' :
                value = value * 10
                flg = 1
            elif c == '1' :
                value = value * 10 + 1
                flg = 1
            elif c == '2' :
                value = value * 10 + 2
                flg = 1
            elif c == '3' :
                value = value * 10 + 3
                flg = 1
            elif c == '4' :
                value = value * 10 + 4
                flg = 1
            elif c == '5' :
                value = value * 10 + 5
                flg = 1
            elif c == '6' :
                value = value * 10 + 6
                flg = 1
            elif c == '7' :
                value = value * 10 + 7
                flg = 1
            elif c == '8' :
                value = value * 10 + 8
                flg = 1
            elif c == '9' :
                value = value * 10 + 9
                flg = 1
            elif c == ' ' or c == '"':
                pass
            else:
                break
            i += 1
        if flg == 1 :
            return value
    return defaluVal


def dumpDatas(data):
    if data == None :
        return 'none'
    if isinstance(data, set) :
        return json.dumps(list(data), separators=(',', ':'))
    elif isinstance(data, (list, tuple, dict)) :
        return json.dumps(data, separators=(',', ':'))
    elif isinstance(data, (int, float, bool)) :
        return str(data)
    elif isinstance(data, (str, unicode)) :
        return data
    else:
        raise Exception('Un Support Value Data Type !! type(data)=' + str(type(data)))


def __replace_evn_value(datastr, envdict):
    if datastr.startswith('${{') and datastr.endswith('}}'):
        k = datastr[3:-2]
        if k.endswith('++') :
            k = k[:-2]
            v = envdict[k]
            envdict[k] = v + 1
            return v
        elif k.find('+') > 0 :
            ik = k[:k.find('+')]
            pv = k[k.find('+') + 1:]
            v = envdict[ik] + int(pv)
            return v
        else:
            return envdict[k]

    calltype = str
    if isinstance(datastr, unicode) :
        calltype = unicode
    seqs = []
    append = seqs.append

    i = datastr.find('${')
    while i >= 0 :
        if i > 0 :
            if datastr[i - 1] == '\\' :
                append(datastr[0:i - 1])
                append(calltype('${'))
                datastr = datastr[i + 2:]
                i = datastr.find('${')
                continue

        j = datastr.find('}', i)
        k = datastr[i + 2:j]
        append(datastr[0:i])
        if k.endswith('++') :
            k = k[:-2]
            v = envdict[k]
            envdict[k] = v + 1
            append(calltype(v))
            datastr = datastr[j + 1:]
        elif k.find('+') > 0:
            ik = k[:k.find('+')]
            pv = k[k.find('+') + 1:]
            v = envdict[ik] + int(pv)
            append(calltype(v))
            datastr = datastr[j + 1:]
        else:
            v = envdict[k]
            append(calltype(v))
            datastr = datastr[j + 1:]
        i = datastr.find('${')
    append(datastr)
    return calltype('').join(seqs)


def replace_objevn_value(obj, envdict):
    if isinstance(obj, list) :
        for x in xrange(len(obj)) :
            obj[x] = replace_objevn_value(obj[x], envdict)
        return obj
    elif isinstance(obj, dict) :
        for k in obj.keys() :
            k2 = replace_objevn_value(k, envdict)
            v = replace_objevn_value(obj[k], envdict)
            if k2 != k :
                del obj[k]
            obj[k2] = v
        return obj
    elif isinstance(obj, (str, unicode)) :
        return __replace_evn_value(obj, envdict)
    else:
        return obj


def to_string(obj, maxlen=0, needeascp=False):
    datas = []
    __makelines(obj, datas, maxlen, 1)
    str1 = ''.join(datas)
    if needeascp :
        str1 = str1.replace('\n', '\\n')
        str1 = str1.replace('\d', '\\\\d')
        str1 = str1.replace('\r', '')
    return str1


def __makelines(obj, datas, maxlen, flg=0):
    dtype = type(obj)
    if dtype == unicode :
        obj = obj.encode('utf-8')
        if maxlen > 0 and len(obj) > maxlen :
            obj = obj[0:maxlen] + '......'
        if flg :
            datas.append(obj)
        else:
            datas.append('"')
            datas.append(obj)
            datas.append('"')
    
    elif dtype == str :
        if maxlen > 0 and len(obj) > maxlen :
            obj = obj[0:maxlen] + '......'
        if flg :
            datas.append(obj)
        else:
            datas.append('"')
            datas.append(obj)
            datas.append('"')
    
    elif dtype == int or dtype == long or dtype == bool or dtype == float :
        datas.append(str(obj))
    
    elif dtype == list :
        datas.append('[')
        i = 0
        for sobj in obj :
            if i > 0 :
                datas.append(', ')
            __makelines(sobj, datas, maxlen)
            i = 1
        datas.append(']')

    elif dtype == tuple :
        datas.append('(')
        i = 0
        for sobj in obj :
            if i > 0 :
                datas.append(', ')
            __makelines(sobj, datas, maxlen)
            i = 1
        datas.append(')')

    elif dtype == dict :
        datas.append('{')
        i = 0
        for k, v in obj.items() :
            if i > 0 :
                datas.append(', ')
            if isinstance(k, unicode) :
                k = k.encode('utf-8')
            else:
                k = str(k)
            datas.append('"')
            datas.append(k)
            datas.append('":')
            __makelines(v, datas, maxlen)
            i = 1
        datas.append('}')

    else :
        obj = str(obj)
        if maxlen > 0 and len(obj) > maxlen :
            obj = obj[0:maxlen] + '......'
        if flg :
            datas.append(obj)
        else:
            datas.append('"')
            datas.append(obj)
            datas.append('"')


def unicode_2_ascii(idata):
    if isinstance(idata, unicode) :
        idata = idata.encode('utf-8')
    else:
        idata = str(idata)
    return idata


def pack(struct_fmt, *datas):
    return struct.pack(struct_fmt, *datas)


def unpack(struct_fmt, datas):
    return struct.unpack(struct_fmt, unicode_2_ascii(datas))


def pack1iB(int1, int2):
    return struct.pack("iB", int1, int2)


def unpack1iB(int12):
    return struct.unpack("iB", unicode_2_ascii(int12))


def pack2iB(int1, int2, int3):
    return struct.pack("2iB", int1, int2, int3)


def unpack2iB(int123):
    return struct.unpack("2iB", unicode_2_ascii(int123))


def pack3iB(int1, int2, int3, int4):
    return struct.pack("3iB", int1, int2, int3, int4)


def unpack3iB(int1234):
    return struct.unpack("3iB", unicode_2_ascii(int1234))


def decodeObjUtf8(datas):
    if isinstance(datas, dict) :
        ndatas = {}
        for key, val in datas.items() :
            if isinstance(key, unicode) :
                key = key.encode('utf-8')
            ndatas[key] = decodeObjUtf8(val)
        return ndatas
    if isinstance(datas, list) :
        ndatas = []
        for val in datas :
            ndatas.append(decodeObjUtf8(val))
        return ndatas
    if isinstance(datas, unicode) :
        return datas.encode('utf-8')
    return datas


def getObjectFunctions(obj, funhead, funargc):
    funs = {}
    for key in dir(obj):
        if key.find(funhead) == 0 :
            try:
                methodfun = getattr(obj, key)
                if inspect.ismethod(methodfun) and len(inspect.getargspec(methodfun)[0]) == funargc:
                    key = key[len(funhead):]
                    funs[key] = methodfun
            except AttributeError:
                continue
    return funs

