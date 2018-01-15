# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import base64
import json
import os
import re
import struct
import urllib
import uuid
from copy import deepcopy
from hashlib import md5
from sre_compile import isstring

import freetime.util.log as ftlog
from freetime.util import encry
from freetime.util.cache import lfu_cache
from poker.util import constants
from poker.util.constants import CLIENT_SYS_IOS, CLIENT_SYS_ANDROID, CLIENT_SYS_H5, \
    CLIENT_SYS_WINPC, CLIENT_SYS_MACOS
from poker.util.pokercffi import POKERC
from poker.util.pokercffi import POKERFFI

__buffered_reg = {}
__int62 = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
__int62dictint = {}
__int62dictstr = {}
for x in xrange(len(__int62)):
    __int62dictint[x] = __int62[x]
    __int62dictstr[__int62[x]] = x

__ffi_des_str = POKERFFI.new("unsigned char[]", 65536)
__ffi_code_str = POKERFFI.new("char[]", 65536)


def tycode(seed, datas):
    return encry.code(seed, datas)


def desEncrypt(deskey, desstr):
    '''
    DES加密算法
    '''
    deslen = len(desstr)
    if deslen > 65000:
        raise Exception('the desstr length too long !! 65000 limited !!')
    outlen = POKERC.des_encrypt(desstr, deslen, deskey, __ffi_des_str)
    return POKERFFI.buffer(__ffi_des_str, outlen)[:]


def desDecrypt(deskey, desstr):
    '''
    DES解密算法
    '''
    deslen = len(desstr)
    if deslen > 65000:
        raise Exception('the desstr length too long !! 65000 limited !!')
    outlen = POKERC.des_decrypt(desstr, deslen, deskey, __ffi_des_str)
    return POKERFFI.buffer(__ffi_des_str, outlen)[:]


def tyDesEncode(desstr):
    '''
    途游标准加密算法(固定的deskey)
    '''
    if isinstance(desstr, unicode):
        desstr = desstr.encode('utf8')
    desstr = b'TUYOO~' + desstr + b'~POKER201309031548'
    desstr = desEncrypt(b'tuyoocom', desstr)
    desstr = base64.b64encode(desstr)
    return desstr


def tyDesDecode(desstr):
    '''
    途游标准解密算法(固定的deskey)
    '''
    desstr = b64decode(desstr)
    desstr = desDecrypt(b'tuyoocom', desstr)
    postail = desstr.find('~POKER201309031548')
    poshead = desstr.find('TUYOO~')
    if poshead == 0 and postail > 6:
        desstr = desstr[6:postail]
        return desstr
    return None


def getEnv(ekey, defaultval):
    '''
    获取系统环境变量
    '''
    return os.environ.get(ekey, defaultval)


def cloneData(data):
    '''
    使用JSON的loads和dump克隆一个数据对象
    '''
    return deepcopy(data)


#     try:
#         return json.loads(json.dumps(data))
#     except:
#         ftlog.warn('Can not use json copy !! data=' + repr(data))
#         return deepcopy(data)


def uuid():
    '''
    取得一个32位长的UUID字符串
    '''
    return str(uuid.uuid4()).replace('-', '')


def dumps(obj):
    '''
    驳接JSON的dumps方法, 使用紧凑的数据格式(数据项之间无空格)
    '''
    return json.dumps(obj, separators=(',', ':'))


def dumpsbase64(obj):
    '''
    驳接JSON的dumps方法,并对结果进行BASE64的编码
    '''
    jstr = json.dumps(obj, separators=(',', ':'))
    return base64.b64encode(jstr)


def loadsbase64(base64jsonstr, decodeutf8=False):
    '''
    驳接JSON的loads方法, 先对json串进行BASE64解密,再解析为JSON格式
    若decodeutf8为真, 那么将所有的字符串转换为ascii格式
    '''
    jsonstr = b64decode(base64jsonstr)
    datas = json.loads(jsonstr)
    if decodeutf8:
        datas = decodeObjUtf8(datas)
    return datas


def loads(jsonstr, decodeutf8=False, ignoreException=False, execptionValue=None):
    '''
    驳接JSON的loads方法
    若decodeutf8为真, 那么将所有的字符串转换为ascii格式
    若ignoreException为真, 那么忽略JSON格式的异常信息
    若execptionValue为真, 当若ignoreException为真时,发生异常,则使用该缺省值
    '''
    if ignoreException:
        try:
            datas = json.loads(jsonstr)
        except:
            datas = execptionValue
    else:
        datas = json.loads(jsonstr)
    if datas and decodeutf8:
        datas = decodeObjUtf8(datas)
    return datas


def b64decode(base64str):
    '''
    驳接BASE64的解密方法, 替换数据中的空格到+号后,再进行解密
    '''
    base64str = base64str.replace(' ', '+')
    base64str = base64str.replace('%3d', '=')
    return base64.b64decode(base64str)


def b64encode(normalstr):
    '''
    驳接BASE64的加密方法
    '''
    return base64.b64encode(normalstr)


def md5digest(md5str):
    '''
    计算一个字符串的MD5值, 返回32位小写的MD5值
    '''
    m = md5()
    m.update(md5str)
    md5code = m.hexdigest()
    return md5code.lower()


def urlencode(params):
    '''
    将params进行URL编码
    '''
    return urllib.urlencode(params)


@lfu_cache(maxsize=1000, cache_key_args_index=0)
def _getCompiledReg(regExp):
    return re.compile(regExp)


def regMatch(regExp, checkStr):
    '''
    正则表达式匹配处理
    支持特殊的正则"*",意味全量匹配
    此方法会缓存已经编译过的正则, 进行加速处理
    '''
    if regExp == '*':
        return True
    breg = _getCompiledReg(regExp)
    if breg.match(checkStr):
        return True
    return False


def regMatchList(regExpList, checkStr):
    '''
    正则表达式匹配处理, regExpList为一个正则表达式的列表, 若匹配到一个则返回真
    支持特殊的正则"*",意味全量匹配
    此方法会缓存已经编译过的正则, 进行加速处理
    '''
    for regExp in regExpList:
        if regMatch(regExp, checkStr):
            return True
    return False


def tostr62(int10, slenfix=0):
    '''
    10进制转换为62进制
    '''
    if int10 <= 0:
        s62 = '0'
    else:
        s62 = ''
        while int10 > 0:
            c = __int62dictint[int10 % 62]
            int10 = int10 / 62
            s62 = c + s62

    if slenfix > 0:
        while len(s62) < slenfix:
            s62 = '0' + s62
        if len(s62) > slenfix:
            s62 = s62[-slenfix:]
    return s62


def toint10(str62):
    '''
    62进制转换为10进制
    '''
    int10 = 0
    slen = len(str62)
    for x in xrange(slen):
        m = __int62dictstr[str62[x]]
        if m > 0:
            for _ in xrange(slen - x - 1):
                m = m * 62
        int10 = m + int10
    return int10


def getJsonStr(jsonstr, key, defaultVal=''):
    '''
    JSON的快速替代方法
    找到对应的key的字符串值, 
    注意: 必须确信key对应的值为标准的字符串格式,且其中没有转义的双引号存在
    '''
    key = '"' + key + '":'
    i = jsonstr.find(key)
    if i > 0:
        x = jsonstr.find('"', i + len(key))
        y = jsonstr.find('"', x + 1)
        return jsonstr[x + 1:y]
    else:
        return defaultVal


def getJsonInt(jsonstr, key, defaluVal=0):
    '''
    JSON的快速替代方法
    找到对应的key的字符串的int值, 
    注意: 必须确信key对应的值为标准的数字格式,且其中没有转义的双引号存在
    '''
    key = '"' + key + '":'
    i = jsonstr.find(key)
    if i > 0:
        linelen = len(jsonstr)
        i = i + len(key)
        value = 0
        flg = 0
        while i < linelen:
            c = jsonstr[i]
            if c == '0':
                value = value * 10
                flg = 1
            elif c == '1':
                value = value * 10 + 1
                flg = 1
            elif c == '2':
                value = value * 10 + 2
                flg = 1
            elif c == '3':
                value = value * 10 + 3
                flg = 1
            elif c == '4':
                value = value * 10 + 4
                flg = 1
            elif c == '5':
                value = value * 10 + 5
                flg = 1
            elif c == '6':
                value = value * 10 + 6
                flg = 1
            elif c == '7':
                value = value * 10 + 7
                flg = 1
            elif c == '8':
                value = value * 10 + 8
                flg = 1
            elif c == '9':
                value = value * 10 + 9
                flg = 1
            elif c == ' ' or c == '"':
                pass
            else:
                break
            i += 1
        if flg == 1:
            return value
    return defaluVal


def dumpDatas(data):
    '''
    使用JSON的方式, 序列化data数据
    '''
    if data == None:
        return 'none'
    if isinstance(data, set):
        return json.dumps(list(data), separators=(',', ':'))
    elif isinstance(data, (list, tuple, dict)):
        return json.dumps(data, separators=(',', ':'))
    elif isinstance(data, (int, float, bool)):
        return str(data)
    elif isinstance(data, (str, unicode)):
        return data
    else:
        raise Exception('Un Support Value Data Type !! type(data)=' + str(type(data)))


def replaceEvnValue(datastr, envdict):
    '''
    查找datastr中${XX}格式的字符串, 替换为envdict中的XX对应的值
    对于${标记,支持"\"转义处理
    若标记为: ${XX++}, 那么取得envdict中的XX值后, 将envdict中的XX值加1
    若标记为: ${XX+n}, 那么取得envdict中的XX+n值
    '''
    if datastr.startswith('${{') and datastr.endswith('}}'):
        k = datastr[3:-2]
        if k.endswith('++'):
            k = k[:-2]
            v = envdict[k] + 1
            envdict[k] = v
            return v
        elif k.find('+') > 0:
            ik = k[:k.find('+')]
            pv = k[k.find('+') + 1:]
            v = envdict[ik] + int(pv)
            return v
        else:
            return envdict[k]

    calltype = str
    if isinstance(datastr, unicode):
        calltype = unicode
    seqs = []
    append = seqs.append

    i = datastr.find('${')
    while i >= 0:
        if i > 0:
            if datastr[i - 1] == '\\':
                append(datastr[0:i - 2])
                append(calltype('${'))
                datastr = datastr[i + 2:]
                i = datastr.find('${')
                continue

        j = datastr.find('}', i)
        k = datastr[i + 2:j]
        append(datastr[0:i])
        if k.endswith('++'):
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


def replaceObjEvnValue(obj, envdict):
    '''
    遍历obj(list, dict)中的所有数据, 并使用replaceEvnValue方法,处理遇到的所有的字符串
    '''
    if isinstance(obj, list):
        for x in xrange(len(obj)):
            obj[x] = replaceObjEvnValue(obj[x], envdict)
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            k2 = replaceObjEvnValue(k, envdict)
            v = replaceObjEvnValue(obj[k], envdict)
            if k2 != k:
                del obj[k]
            obj[k2] = v
        return obj
    elif isinstance(obj, (str, unicode)):
        return replaceEvnValue(obj, envdict)
    else:
        return obj


def replaceObjRefValue(obj):
    return _replaceObjRefValue(obj, [])


def _replaceObjRefValue(obj, stack):
    if isinstance(obj, list):
        assert (obj not in stack), '_replaceObjRefValue found dide ref list loop !!'
        stack.append(obj)
        for x in xrange(len(obj)):
            obj[x] = _replaceObjRefValue(obj[x], stack)
        stack.remove(obj)
        return obj
    elif isinstance(obj, dict):
        assert (obj not in stack), '_replaceObjRefValue found dide ref dict loop !!'
        stack.append(obj)
        for k in obj.keys():
            v = _replaceObjRefValue(obj[k], stack)
            obj[k] = v
        stack.remove(obj)
        return obj
    elif isinstance(obj, (str, unicode)):
        return _replaceRefValue(obj, stack[0])
    else:
        return obj


def _replaceRefValue(datastr, envdict):
    try:
        if datastr.startswith('#ref://') and datastr.endswith('#'):
            k = datastr[7:-1]
            tks = k.split('/')
            datas = envdict
            for tk in tks:
                if isinstance(datas, list):
                    tk = int(tk)
                datas = datas[tk]
            return datas
        return datastr
    except Exception, e:
        raise Exception('the ref value replace error ! ' + str(datastr) + ' ' + str(e))


def unicode2Ascii(idata):
    '''
    编码转换: UNICODE至ASCII
    '''
    try:
        return idata.encode('utf-8')
    except:
        return str(idata)


def pack(struct_fmt, *datas):
    '''
    驳接struct的pack方法
    '''
    return struct.pack(struct_fmt, *datas)


def unpack(struct_fmt, datas):
    '''
    驳接struct的unpack方法
    '''
    return struct.unpack(struct_fmt, unicode2Ascii(datas))


def decodeObjUtf8(datas):
    '''
    遍历datas(list,dict), 将遇到的所有的字符串进行encode utf-8处理
    '''
    if isinstance(datas, dict):
        ndatas = {}
        for key, val in datas.items():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            ndatas[key] = decodeObjUtf8(val)
        return ndatas
    if isinstance(datas, list):
        ndatas = []
        for val in datas:
            ndatas.append(decodeObjUtf8(val))
        return ndatas
    if isinstance(datas, unicode):
        return datas.encode('utf-8')
    return datas


def getTableRoomId(tableId):
    '''
    解析大房间的roomId, 取得gameId和configId
    '''
    tableId = int(tableId)
    assert (tableId > 0)
    return tableId / 10000


@lfu_cache(maxsize=1000, cache_key_args_index=0)
def parseBigRoomId(roomId):
    '''
    解析大房间的roomId, 取得gameId和configId
    '''
    roomId = int(roomId)
    assert (roomId > 0)
    configid = roomId % 1000
    gameid = roomId / 1000
    return gameid, configid


def getBigRoomIdFromInstanceRoomId(roomId):
    '''
    解析大房间的roomId, 取得gameId和configId
    '''
    roomId = int(roomId)
    assert (roomId > 0)
    return roomId / 10000


@lfu_cache(maxsize=1000, cache_key_args_index=0)
def parseInstanceRoomId(roomId):
    '''
    解析房间实例的roomId(控制房间和桌子房间), 取得gameId, configId, controlId, showdId
    注: 若为控制房间showdId必定为0, 若为桌子房间showdId必定大于0
    '''
    roomId = int(roomId)
    assert (roomId > 0)
    showdid = roomId % 1000
    controlid = (roomId / 1000) % 10
    configid = (roomId / 10000) % 1000
    gameid = roomId / 10000000
    return gameid, configid, controlid, showdid


@lfu_cache(maxsize=1000, cache_key_args_index=0)
def getGameIdFromInstanceRoomId(roomId):
    '''
    解析房间实例的roomId(控制房间和桌子房间), 取得gameId
    注: 若为控制房间showdId必定为0, 若为桌子房间showdId必定大于0
    '''
    roomId = int(roomId)
    assert (roomId > 0)
    gameid = roomId / 10000000
    return gameid


@lfu_cache(maxsize=1000, cache_key_args_index=0)
def getGameIdFromBigRoomId(bigRoomId):
    '''
    解析房间的BigRoomId 取得gameId
    '''
    bigRoomId = int(bigRoomId)
    assert (bigRoomId > 0)
    gameid = bigRoomId / 1000
    return gameid


@lfu_cache(maxsize=1000, cache_key_args_index=0)
def parseClientId(clientId):
    if isinstance(clientId, (str, unicode)):
        infos = clientId.split('_', 2)
        if len(infos) == 3:
            try:
                clientsys = infos[0][0]
                if clientsys == 'W':
                    clientsys = CLIENT_SYS_WINPC
                elif clientsys == 'I' or clientsys == 'i':
                    clientsys = CLIENT_SYS_IOS
                elif clientsys == 'H' or clientsys == 'h':
                    clientsys = CLIENT_SYS_H5
                elif clientsys == 'M' or clientsys == 'm':
                    clientsys = CLIENT_SYS_MACOS
                else:
                    clientsys = CLIENT_SYS_ANDROID
                return clientsys, float(infos[1]), infos[2]
            except:
                ftlog.error('clientId=', clientId)
                return 'error', 0, 'error'
    ftlog.error('parseClientId params error, clientId=', clientId)
    return 'error', 0, 'error'


def isTheOsClient(clientId, osName):
    clientOs, _, _ = parseClientId(clientId)
    return osName.lower() == clientOs.lower()


def isWinpcClient(clientId):
    return isTheOsClient(clientId, 'winpc')


_OLDCLIENTID_HALL6 = {'Android_3.28_360.aigame,weakChinaMobile,woStore.0.360.mayor360',
                      'Android_3.27_360.360.0.360.mayor360', 'Android_3.26_tuyoo.tuyoo.0.tuyoo.tuyoostar',
                      'Android_3.25_tuyoo.tuyoo.0.tuyoo.tuyoostar', 'Android_3.2_tuyoo.newYinHe.0.wangyi.tuwangyi',
                      'Android_3.33_newpay', 'Android_3.27_tuyoo.weakChinaMobile.0.tuyoo.mayortuyooyidongmm',
                      'Android_3.28_tuyoo.woStore.0.tuyoo.mayortuyoowoStore',
                      'Android_3.27_tuyoo.tuyoo.0.tuyoo.mayortuyoo',
                      'Android_3.27_tuyoo.woStore.0.starwoStore.starzszhwoStore1',
                      'Android_3.1_360sns.360sns.1.360.360sns', 'Android_3.11_360sns.360sns,newYinHe.1.360.360sns',
                      'Android_3.25_360.360.0.360.star360', 'Android_3.26_360.360.0.360.star360',
                      'Android_3.27_360.360.0.360.star360', 'Android_3.21_360.newYinHe.0.360.tu360',
                      'Android_3.22_360.newYinHe.0.360.tu360', 'Android_3.23_360.newYinHe.0.360.tu360',
                      'Android_3.25_360.tuyoo.0.360.tu360', 'Android_3.2_360.newYinHe.0.360.tu360',
                      'Android_3.21_360.newYinHe.0.360.laizi360', 'Android_3.23_360.newYinHe.0.360.laizi360',
                      'Android_3.24_360.360.0.360.laizi360', 'Android_3.25_360.360.0.360.laizi360',
                      'Android_3.2_360.newYinHe.0.360.laizi360', 'Android_3.29_360.360.0.360.mayor360',
                      'Android_3.28_360.weakChinaMobile.0.360.mayor360yidongmm',
                      'Android_3.33_kugou.weakChinaMobile.0-6.kugou.kgtongcheng', 'Android_3.7_monitor',
                      'Android_3.3_monitor'}


@lfu_cache(maxsize=1000, cache_key_args_index=0)
def getGameIdFromHallClientId(clientId):
    try:
        if isinstance(clientId, int):
            from poker.entity.configure import pokerconf
            clientId = pokerconf.numberToClientId(clientId)
        gid = re.match('^.*-hall(\\d+).*$', clientId).group(1)
        return int(gid)
    except:
        if clientId in _OLDCLIENTID_HALL6:
            return 6
        ftlog.error('clientId=' + str(clientId))
        return 0


@lfu_cache(maxsize=1000, cache_key_args_index=0)
def getChannelFromHallClientId(clientId):
    try:
        if isinstance(clientId, int):
            from poker.entity.configure import pokerconf
            clientId = pokerconf.numberToClientId(clientId)

        cList = clientId.split('.')
        return cList[-2] + '.' + cList[-1]
    except:
        return clientId


def getPhoneTypeName(phone_type_code):
    if phone_type_code == constants.PHONETYPE_CHINAMOBILE or phone_type_code == constants.PHONETYPE_CHINAMOBILE_STR:
        return constants.PHONETYPE_CHINAMOBILE_STR
    elif phone_type_code == constants.PHONETYPE_CHINAUNION or phone_type_code == constants.PHONETYPE_CHINAUNION_STR:
        return constants.PHONETYPE_CHINAUNION_STR
    elif phone_type_code == constants.PHONETYPE_CHINATELECOM or phone_type_code == constants.PHONETYPE_CHINATELECOM_STR:
        return constants.PHONETYPE_CHINATELECOM_STR
    else:
        return constants.PHONETYPE_OTHER_STR


def getPhoneTypeCode(phone_type_name):
    phone_type_name = str(phone_type_name)
    if phone_type_name == str(
            constants.PHONETYPE_CHINAMOBILE) or phone_type_name == constants.PHONETYPE_CHINAMOBILE_STR:
        return constants.PHONETYPE_CHINAMOBILE
    elif phone_type_name == str(
            constants.PHONETYPE_CHINAUNION) or phone_type_name == constants.PHONETYPE_CHINAUNION_STR:
        return constants.PHONETYPE_CHINAUNION
    elif phone_type_name == str(
            constants.PHONETYPE_CHINATELECOM) or phone_type_name == constants.PHONETYPE_CHINATELECOM_STR:
        return constants.PHONETYPE_CHINATELECOM
    else:
        return constants.PHONETYPE_OTHER


def replaceParams(string, params):
    if string:
        for k, v in params.iteritems():
            k = '${%s}' % (k)
            if not isstring(v):
                v = str(v)
            string = string.replace(k, v)
    return string


def parseInts(*args):
    rets = []
    for x in args:
        try:
            i = int(x)
        except:
            i = 0
        rets.append(i)
    if len(rets) == 1:
        return rets[0]
    return rets


def ensureString(val, defVal=''):
    if isstring(val):
        return val
    if val is None:
        return defVal
    return str(val)
