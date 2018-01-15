# -*- coding=utf-8
'''
Created on 2015年10月22日

@author: zhaojiangang
'''
import freetime.util.log as ftlog
from hall.entity import hallitem, hallpopwnd
from hall.entity.todotask import TodoTaskHelper, TodoTaskOrderShow
from poker.entity.dao import userdata as pkuserdata
from poker.util import strutil


def makeTodoTaskZhuanyun_(gameId, userId, clientId, benefitsSend, userBenefits, roomId):
    from hall.entity import hallproductselector
    if ftlog.is_debug():
        ftlog.debug('hallpopwnd.makeTodoTaskZhuanyun gameId=', gameId,
                    'userId=', userId,
                    'clientId=', clientId,
                    'benefitsSend=', benefitsSend,
                    'userBenefits=', userBenefits.__dict__,
                    'roomId=', roomId)
    clientOs, _clientVer, _ = strutil.parseClientId(clientId)
    clientOs = clientOs.lower()

    if clientOs != 'winpc':
        return TodoTaskHelper.makeZhuanyunTodoTaskNew(gameId, userId, clientId,
                                                      benefitsSend, userBenefits, roomId)

    product, _ = hallproductselector.selectLessbuyProduct(gameId, userId, clientId, roomId)
    if not product:
        return None

    user_diamond = pkuserdata.getAttr(userId, 'diamond')
    if user_diamond >= int(product.priceDiamond):
        chip = product.getMinFixedAssetCount(hallitem.ASSET_CHIP_KIND_ID)
        show_str = u'运气不好，来个转运礼包！%s元得%s万金币。' % (product.price, chip)
        buy_type = 'consume'
        btn_txt = u'兑换'
    else:
        show_str = u'运气不好~，买点金币战个痛快吧！'
        buy_type = 'charge'
        btn_txt = u'去充值'
    orderShow = TodoTaskOrderShow.makeByProduct(show_str, '', product, buy_type)
    orderShow.setParam('sub_action_btn_text', btn_txt)
    return orderShow


hallpopwnd.makeTodoTaskZhuanyun = makeTodoTaskZhuanyun_
