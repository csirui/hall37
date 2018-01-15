# -*- coding: utf-8 -*-

__author__ = [
    '"Zhouhao" <zhouhao@tuyoogame.com>',
]

import freetime.util.log as ftlog
from difang.entity import plugin_event_const as PluginEvent
from hall.servers.common.base_http_checker import BaseHttpMsgChecker
from poker.entity.configure import gdata
from poker.entity.game.plugin import TYPluginCenter, TYPluginUtils
from poker.protocol import runhttp
from poker.protocol.decorator import markHttpHandler, markHttpMethod


@markHttpHandler
class DiFangHTTPCommon(BaseHttpMsgChecker):
    GAME_ID = 0

    def __init__(self):
        pass

    # @markHttpMethod(httppath='/v2/game/gamble/common')
    def onHttpCommon(self):
        return self._doHttpCommon()

    def _doHttpCommon(self):
        ''' 多封装这一层，纯粹是为了 hotfix 维护方便 '''
        try:
            request = runhttp.getRequest()
            args = request.args
            if ftlog.is_debug():
                ftlog.debug('<<', args, caller=self)
            msg = TYPluginUtils.updateMsg(cmd='EV_HTTP_COMMON_REQUEST',
                                          params={'httpArgs': args, 'httpRequest': request},
                                          result={'httpResult': {}}
                                          )
            TYPluginCenter.event(msg, self.GAME_ID)
            httpResult = msg.getResult('httpResult')
            if ftlog.is_debug():
                ftlog.debug('>>', httpResult, caller=self)
            if not httpResult:
                httpResult = {'error': 'NotImplement'}
            return self.makeResponse(httpResult)
        except Exception, e:
            ftlog.error('HTTPCommon._doHttpCommon: request.args:', args)
            return self.makeErrorResponse(str(e), u'有异常')

    def makeErrorResponse(self, ec, message):
        return {'error': {'ec': ec, 'message': message}}

    def makeResponse(self, result):
        return {'result': result}

    # @markHttpMethod(httppath='/v2/game/gamble/img', responseType='gif')
    def onHttpImg(self):
        return self._doHttpImg()

    def _doHttpImg(self):
        ''' 多封装这一层，纯粹是为了 hotfix 维护方便 '''
        try:
            request = runhttp.getRequest()
            args = request.args
            if ftlog.is_debug():
                ftlog.debug('<<', self.GAME_ID, args, caller=self)
            msg = TYPluginUtils.updateMsg(cmd='EV_HTTP_COMMON_REQUEST',
                                          params={'httpArgs': args, 'httpRequest': request},
                                          result={'httpResult': {}}
                                          )
            TYPluginCenter.event(msg, self.GAME_ID)
            httpResult = msg.getResult('httpResult')
            if ftlog.is_debug():
                ftlog.debug('>> ', self.GAME_ID, httpResult, caller=self)
            if not httpResult:
                return self.errorpage('')
            return httpResult['img']
        except Exception, e:
            ftlog.error('HTTPCommon._doHttpImg request.args:', self.GAME_ID, args)
            return self.makeErrorResponse(str(e), u'有异常')

    # @markHttpMethod(httppath='/v2/game/gamble/common_page', responseType='html')
    def onHttpCommonPage(self):
        return self._doHttpCommonPage()

    def _doHttpCommonPage(self):
        ''' 多封装这一层，纯粹是为了 hotfix 维护方便 '''
        try:
            request = runhttp.getRequest()
            args = request.args
            if ftlog.is_debug():
                ftlog.debug('GambleHttp._doHttpCommonPage << ', args)
            msg = TYPluginUtils.updateMsg(cmd=PluginEvent.EV_HTTP_COMMON_REQUEST_PAGE,
                                          params={
                                              'httpArgs': args,
                                              'httpRequest': request
                                          },
                                          result={
                                              'httpResult': {
                                                  'page': '',
                                                  'error': '',
                                              },
                                          }
                                          )
            TYPluginCenter.event(msg, self.GAME_ID)
            error = msg.getResult('error')
            if error:
                ftlog.error('GambleHttp._doHttpCommonPage >>| error:', error)
                return self.errorpage(error)
            page = msg.getResult('httpResult', {}).get('page')
            if not page:
                return self.errorpage('')
            return page

        except Exception, e:
            ftlog.error('HTTPCommon._doHttpCommon: request.args:', args)
            return self.errorpage(str(e))

    def errorpage(self, error):
        if ftlog.is_debug():
            return "少年, 出错啦: <br />" + error
        else:
            return "<h3>404: 页面不存在</h3>"


@markHttpHandler
class DiFangCommonHttpDispatcher(BaseHttpMsgChecker):
    @markHttpMethod(httppath='/v2/game/common')
    def onHttpCommon(self, gameId):
        handler = self._getGameHttpCommonHandler(gameId)
        if not handler:
            return {'error': 404}
        return handler.onHttpCommon()

    @markHttpMethod(httppath='/v2/game/common_page', responseType='html')
    def onHttpCommonPage(self, gameId):
        handler = self._getGameHttpCommonHandler(gameId)
        if not handler:
            return "<h3>404: 页面不存在</h3>"
        return handler.onHttpCommonPage()

    def _getGameHttpCommonHandler(self, gameId):
        game = gdata.getGame(gameId)
        if game:
            if hasattr(game, 'getCommonHttpHandler'):
                return game.getCommonHttpHandler()
