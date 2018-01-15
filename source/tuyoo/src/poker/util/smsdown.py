# -*- coding=utf-8 -*-

from xml.etree import ElementTree

from poker.util import strutil
from poker.util import webpage


class SmsDownBaiFen(object):
    def __init__(self):
        self.smsurl = u'http://cf.lmobile.cn/submitdata/Service.asmx/g_Submit'

    def sendSms(self, mobile, content):
        content = content + '【在线途游】'

        querys = {
            'sname': 'dlzxty00',
            'spwd': '18lJsdrv',
            'scorpid': '',
            'sprdid': '1012818',
            'sdst': str(mobile),
            'smsg': content
        }

        # 不用post会500错误
        response, _ = webpage.webget(self.smsurl, postdata_=querys)
        xmlroot = ElementTree.fromstring(response)
        state = xmlroot.find('{http://tempuri.org/}State').text
        if int(state) != 0:
            return False
        return True


SmsDownBaiFen = SmsDownBaiFen()


class SmsDownManDao(object):
    def __init__(self):
        self.sn = 'SDK-BBX-010-19139'
        pwd = '140408'
        pwd = strutil.md5digest(self.sn + pwd)
        self.pwd = pwd.upper()
        self.smsurl = u'http://sdk2.entinfo.cn:8061/mdsmssend.ashx?'

    def sendSms(self, mobile, content):
        content = content + '【在线途游】'
        content = unicode(content, 'utf8')
        content = content.encode('utf8')

        querys = {
            'sn': self.sn,
            'pwd': self.pwd,
            'mobile': mobile,
            'content': content,
        }

        surl = self.smsurl + strutil.urlencode(querys)

        response, _ = webpage.webget(surl)
        response = str(response).strip()
        if response[0] == '-':
            return False
        return True


SmsDownManDao = SmsDownManDao()
