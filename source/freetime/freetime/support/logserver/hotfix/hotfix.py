# -*- coding=utf-8 -*-
import urllib
import urllib2


def sendout(posturl, pdatas):
    Headers = {'Content-type': 'application/x-www-form-urlencoded'}
    postData = urllib.urlencode(pdatas)
    request = urllib2.Request(url=posturl, data=postData, headers=Headers)
    response = urllib2.urlopen(request)
    if response != None:
        retstr = response.read()
        print posturl, 'server response =', retstr
    else:
        print posturl, 'server response is None'


print '====================================='

purls = ['http://10.3.0.38:10001',
         'http://10.3.0.38:10002',
         'http://10.3.0.38:10003',
         'http://10.3.0.38:10004',
         'http://10.3.0.38:10005',
         'http://10.3.0.38:10006',
         'http://10.3.0.38:10007',
         'http://10.3.0.38:10008',
         'http://10.3.0.38:10009',
         'http://10.3.0.38:10010',
         'http://10.3.0.38:10011',
         'http://10.3.0.38:10012',
         'http://10.3.0.38:10013',
         'http://10.3.0.38:10014',
         'http://10.3.0.38:10015',
         'http://10.3.0.38:10016',
         'http://10.3.0.38:10017',
         'http://10.3.0.38:10018',
         'http://10.3.0.38:10019',
         'http://10.3.0.38:10020',
         'http://10.3.0.38:10021',
         'http://10.3.0.38:10022',
         'http://10.3.0.38:10023',
         'http://10.3.0.38:10024',
         ]

gccode = '''
import freetime.util.log as ftlog
ftlog.info('hotfix *********** gc.collect in ************************************************')
import gc, stackless, types
ftlog.info('hotfix gc.isenabled()=', gc.isenabled())
#gc.collect()

ftlog.info('hotfix *********** gc.collect dump **********************************************')
objects = gc.get_objects()
ftlog.info('hotfix gc objects size:', len(objects))
ftlog.info('hotfix current tasklet count:', stackless.getruncount())
dcinst={}
dcother={}
for o in objects:
    if hasattr(o, '__class__'):
        key=str(o.__class__)
        dc=dcinst
    else:
        key=type(o)
        dc=dcother

    if key in dc:
        dc[key]+=1
    else:
        dc[key]=1
for dd in dcinst:
    ftlog.info('hotfixgc', dd, dcinst[dd])
for dd in dcother:
    ftlog.info('hotfixgc', dd, dcother[dd])
ftlog.info('hotfix *********** gc.collect out ***********************************************')
'''

datas = {'pycode': '''
import freetime.util.log as ftlog
ftlog.info('hotfix start')
ftlog.info('hotfix end')
'''}

datas['pycode'] = gccode

for x in xrange(len(purls)):
    sendout(purls[x], datas)
