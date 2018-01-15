# -*- coding=utf-8
'''
Created on 2015年10月22日

@author: zhaojiangang
'''
from hall.entity import hallsubmember, hallitem, hallstore
from hall.entity.hallpopwnd import decodeTodotaskFactoryByDict, \
    TodoTaskMemberBuy2Template
from hall.entity.todotask import TodoTaskMemberBuy, TodoTaskPayOrder
from poker.util import strutil


def newTodoTask(self, gameId, userId, clientId, timestamp, **kwargs):
    subMemberStatus = kwargs.get('subMemberStatus') or hallsubmember.loadSubMemberStatus(userId)
    if subMemberStatus.isSub:
        todotask = TodoTaskMemberBuy(self.descForMember, self.pic)
        todotask.setParam('tip_bottom', self.tipForSubMember)
        return todotask

    memberInfo = kwargs.get('memberInfo') or hallitem.getMemberInfo(userId, timestamp)
    remainDays = memberInfo[0]
    todotask = None
    subActionText = None

    product, _ = hallstore.findProductByPayOrder(gameId, userId, clientId, self.payOrder)

    if not product:
        return None

    if remainDays > 0:
        todotask = TodoTaskMemberBuy(self.descForMember, self.pic)
        tipForMember = strutil.replaceParams(self.tipForMember, {'remainDays': str(remainDays)})
        todotask.setParam('tip_bottom_left', tipForMember)
        todotask.setParam('sub_action_text', self.subActionTextForMember)
    else:
        price = product.price
        priceUnits = '元'
        if product.buyType == 'consume':
            price = product.priceDiamond
            priceUnits = '钻石'
        params = {'product.price': str(price), 'product.priceUnits': priceUnits}
        if product.content and product.content.desc:
            params['product.content.desc'] = product.content.desc
        desc = strutil.replaceParams(self.desc, params)
        todotask = TodoTaskMemberBuy(desc, self.pic)
        todotask.setSubText(self.subActionText)
        todotask.setParam('sub_action_text', self.subActionText)

    todotask.setSubCmdWithText(TodoTaskPayOrder(product), subActionText)

    if remainDays <= 0 and self.closeAction:
        closeAction = decodeTodotaskFactoryByDict(self.closeAction).newTodoTask(gameId, userId, clientId, **kwargs)
        if closeAction:
            todotask.setParam('sub_action_close', closeAction)
    return todotask


TodoTaskMemberBuy2Template._newTodoTask = newTodoTask
