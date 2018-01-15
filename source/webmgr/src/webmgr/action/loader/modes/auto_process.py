# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''
import json
import math
from webmgr.action import actlog
from webmgr.action.loader.modes import modefactory
import os
import random


def auto_group_process(mcs, procs, rooms, mode):
    for mc in mcs.values() :
        weight = int(mc.get('weight', 1))
        if weight < 1 or weight > 9 :
            raise Exception('then machine weight must >= 1 and <= 9 machine=' + json.dumps(mc))
        mc['weight'] = weight

    rids, tids = _auto_room_ins_ids(rooms, procs, mode)

    stypes = ['PL', 'HT', 'CO', 'RB', 'CT', 'UT']
    for stype in stypes :
        _auto_group_process_normal(stype, mcs, procs)
    _auto_group_process_rooms('GR', mcs, procs, rids)
    _auto_group_process_rooms('GT', mcs, procs, tids)
    
    stypes = ['PL', 'HT', 'RB', 'CT', 'UT', 'GR', 'GT']
    agid = 0
    agmax = modefactory[mode].get_max_ag_count(mcs)
    for mn, mc in mcs.items() :
        ids = []
        if agmax > 0 :
            ag = agmax
        else:
            co = len(mc.get('CO', []))
            ot = 0
            for st in stypes :
                ot += len(mc.get(st, []))
            ag = co + int(math.ceil(ot / 10.0))  # CO进程1:1AG， 其它进程10:1AG
            ag = max(min(ag, 20), co)
            if ag > 999 :
                raise Exception('the auto ag count must be 0~999' + json.dumps(mc))
        
        for _ in xrange(ag) :
            agid += 1
            ids.append('%03d' % (agid))
        mc['AG'] = ids

    totals = {}
    ccc = 0
    stypes = ['CO', 'PL', 'HT', 'RB', 'CT', 'UT', 'GR', 'GT', 'AG']
    for mn, mc in mcs.items() :
        ptotals = {}
        cc = 0
        for st in stypes :
            c = len(mc.get(st, []))
            if c > 0 :
                ptotals[st] = c
                if st in totals :
                    totals[st] += c
                else:
                    totals[st] = c
            cc += c
            ccc += c
        actlog.log('COUNT %-3s %-4s %-10s' % (str(cc), mn, mc.get('intranet', mc.get('internet'))), json.dumps(ptotals))
    actlog.log('TOTAL %-4s' % (str(ccc)), json.dumps(totals))
    
    coPortMin = 0
    coPortMax = 0
    if os.environ.get('RUN_IN_DOCKER', 0) :
        coPortMin = int(os.environ['PORT_TCP_CONN_MIN'])
        coPortMax = int(os.environ['PORT_TCP_CONN_MAX'])

    srvs = []
    for stype in ['PL', 'HT', 'CO', 'AG', 'RB', 'CT', 'UT', 'GR', 'GT'] :
        mns = list(mcs.keys())
        mns.sort()
        for mn in mns :
            mc = mcs[mn]
            ids = mc.get(stype, [])
            if not 'agidx' in mc :
                mc['agidx'] = 0
            if ids :
                for x in ids : 
                    srv = {}
                    srv['mn'] = mn
                    srv['type'] = stype
                    srv['id'] = x 
                    srv['ip'] = mc.get('intranet', mc.get('internet'))
                    tc = procs.get(stype, {}).get("task-concurrent", 0)
                    if tc > 0 :
                        srv["task-concurrent"] = tc
                    
                    if stype in ('PL',):
                        srv["protocols" ] = { "server" : { "ht-http" : "${{port_http++}}" }}
                        srv["mysql"] = "${{db.mysql.all}}"
                        srv["redis"] = "${{db.redis.all}}"
                    elif stype in ('HT',):
                        srv["protocols" ] = { "server" : { "ht-http" : "${{port_http++}}" }}
                        srv["redis"] = "${{db.redis.all}}"
                    elif stype in ('CO',) :
                        srv["protocols" ] = { "server" : { "co-tcp" : "${{port_http++}}" }}
                        srv["mysql"] = "${{db.mysql.all}}"
                        srv["redis"] = "${{db.redis.all}}"
                    elif stype in ('AG',) :
                        srv["protocols" ] = { "server" : { "a2a" : "${{port_http++}}", "a2s" : "${{port_http++}}"}}
                    elif stype in ('RB', 'CT', 'GR', 'GT') :
                        srv["redis"] = "${{db.redis.all}}"
                    elif stype in ('UT') :
                        srv["redis"] = "${{db.redis.all}}"
                        if mode == 1 and int(x) <= 80 : 
                            srv["mysql"] = "${{db.mysql.all}}"
                        elif mode == 2 and int(x) <= 2 : 
                            srv["mysql"] = "${{db.mysql.all}}"
                        elif int(x) <= 1 : 
                            srv["mysql"] = "${{db.mysql.all}}"
                    
                    if os.environ.get('RUN_IN_DOCKER', 0) :
                        if stype in ('CO',) :
                            if coPortMin > coPortMax :
                                raise Exception('the PORT_TCP_CONN_MIN PORT_TCP_CONN_MAX not enought range ! coPortMax=' + str(coPortMax))
                            srv["protocols" ] = { "server" : { "co-tcp" : coPortMin }}
                            coPortMin += 1

                    if stype != 'AG' :
                        aids = mc.get('AG')
                        srv['agent'] = "AG" + aids[mc['agidx'] % len(aids)]
                        mc['agidx'] += 1

                    # print json.dumps(srv)
                    srvs.append(srv)
    return srvs


def _make_weight_list(mlist, mcs):
    wl = []
    for m in mlist :
        mc = mcs[m]
        w = mc['weight']
        for _ in xrange(w):
            wl.append(m)
    return wl


def _auto_group_process_normal(stype, mcs, procs):
#     print stype, idlist
    pdef = procs.get(stype, None)
    if not pdef :
        return
    count = int(pdef['count'])
    if count < 0 or count > 999 :
        raise Exception('the count must be 1~999 def=' + json.dumps(pdef))
    idlist = []
    for x in xrange(count) :
        idlist.append('%03d' % (x + 1))
        
    mlist = _make_weight_list(pdef['machines'], mcs)
#     print 'mlist->', mlist
    alist = []
    for x in xrange(len(idlist)) :
        mc = mcs.get(mlist[x % len(mlist)])
        if not stype in mc :
            sa = [0]
            alist.append(sa)
            mc[stype] = sa
        else:
            mc[stype].append(0)
    for sa in alist :
#         print len(sa), sa
        for x in xrange(len(sa)) :
            sa[x] = idlist.pop(0)
#         print sa


def _auto_group_process_rooms(stype, mcs, procs, idlist):
#     print stype, idlist
    pdef = procs.get(stype, None)
    if not pdef :
        return
        
    blist = _make_weight_list(pdef['machines'], mcs)
#     print 'mlist->', mlist
    mlist = []
    idlen = len(idlist)
    while len(mlist) < idlen:
        mlist.extend(blist)
    mlist = mlist[0:idlen]
    random.shuffle(mlist)
    random.shuffle(mlist)
    random.shuffle(mlist)

    random.shuffle(idlist)
    random.shuffle(idlist)
    random.shuffle(idlist)

    alist = []
    for x in xrange(idlen) :
        mc = mcs.get(mlist[x])
        if not stype in mc :
            sa = [0]
            alist.append(sa)
            mc[stype] = sa
        else:
            mc[stype].append(0)
    for sa in alist :
#         print len(sa), sa
        for x in xrange(len(sa)) :
            sa[x] = idlist.pop(0)
#         print sa


def _auto_room_ins_ids(rooms, procs, mode):
    rids = []
    tids = []
    groups = procs['GROUPS']
    def getgroupid(roomId):
        for k, v in groups.items() :
            if roomId >= v[0] and roomId <= v[1] :
                return str(k)
        return 0

    for roomId, roomDef in rooms.items() :
        roomId = int(roomId)
        gid = getgroupid(roomId)  
        if gid :
            if gid not in rids :
                rids.append(gid)
            if gid not in tids :
                tids.append(gid)
            continue

        gr = int(roomDef['controlServerCount'])
        gt = int(roomDef['gameServerCount'])
        if gr < 1 or gr > 9 :
            raise Exception('the controlServerCount must be 1~9 roomId=' + str(roomId))
        if gt < 1 or gt > 999 :
            raise Exception('the gameServerCount must be 1~999 roomId=' + str(roomId))
        if mode == 1 :
            pass
        elif mode == 2 :
            if gr > 2 :
                gr = 2
            if gt > 2 :
                gt = 2
        else :
            if gr > 1 :
                gr = 1
            if gt > 1 :
                gt = 1
        for x in xrange(gr) :
            ctlRoomId = int('%d%d' % (roomId, x + 1))
            rids.append(str(ctlRoomId))
            for y in xrange(gt) :
                tblRoomId = int('%d%03d' % (ctlRoomId, y + 1))
                tids.append(str(tblRoomId))
    return rids, tids

