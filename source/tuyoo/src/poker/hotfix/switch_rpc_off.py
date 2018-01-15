# -*- coding: utf-8 -*-

import freetime.util.log as ftlog
from freetime.util import performance

global results

# bidata.dbbi = dbbi
# exchangedata.dbexchange = dbexchange
# itemdata.dbitem = dbitem
# keymapdata.dbkeymap = dbkeymap
# onlinedata.dbonline = dbonline
# onlinedata.dbgeo = dbgeo
# onlinedata.dbuser = dbuser
# paydata.dbpay = dbpay
# taskdata.dbtask = dbtask
# userchip.dbuser = dbuser
# userdata.dbuser = dbuser
# weakdata.dbuser = dbuser
ftlog.info('SWITCH RPC ACCESS TO DIRECT REDIS ACCESS !!')
performance.PERFORMANCE_NET = 0
