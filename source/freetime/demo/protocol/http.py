#! encoding=utf-8

# Author:        yuejianqiang@tuyoogame.com
# Created:       2015年04月17日
#
import stackless
from freetime.core.protocol import FTHttpRequest, FTHttpChannel
import freetime.entity.service as ftsvr

class MyHttpRequest(FTHttpRequest):

    def handleRequest(self):
        taskarg = ftsvr.getTaskRunArg()
        request = taskarg['data']
        # render path
        request.write('<html>')
        request.write('<div>Host=%s</div>' % self.host)
        request.write('<div>Path=%s</div>' % request.path)
        request.write('<div>Args=%s</div>' % request.args)
        request.write('<div>Method=%s</div>' % request.method)
        request.write('<div>Client=%s</div>' % request.getClientIP())
        request.write('<div>Body=%s</div>' % request.content.read())
        # render headers
        headers = []
        for k, v in request.getAllHeaders().items():
            headers.append('<li>%s=%s</li>' % (k, v))
        request.write('<h1>Header:</h1>')
        request.write('<div>%s</div>' % '\n'.join(headers))
        request.write('</html>')
        request.finish()

class MyHttpChannel(FTHttpChannel):
    requestFactory=MyHttpRequest
