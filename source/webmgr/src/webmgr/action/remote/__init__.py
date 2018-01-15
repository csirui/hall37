# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from tyserver.tyutils import fsutils
from webmgr.action import actlog
from webmgr.action.remote.utils import tyssh


def execute_remote_py(options, machine, paramlist):
    bin_path = options.env['bin_path']
    remotepy = fsutils.appendPath(bin_path, 'remote.py')
    cmdline = ['pypy', remotepy]
    cmdline.extend(paramlist)
    if machine.get('localhost', 0) == 1:
        outputs = tyssh.executecmd_local(cmdline)
    else:
        host = machine['host']
        tyssh.connect(host, machine['user'], machine['pwd'], machine['ssh'])
        outputs = tyssh.executecmd(host, ' '.join(cmdline))
        tyssh.close_ip(host)
    result = tyssh.parse_remote_datas_int(outputs)
    return result, outputs


def find_first_machine(options):
    first = None
    machines = options.machinedict.values()
    for m in machines:
        if m['localhost'] == 1:
            first = m
            break
    if first == None:
        first = machines[0]
    return first


def getMachinePids(options, machine, pfilter=None):
    processids = options.processids
    procids = []
    for p in options.serverlist:
        if p['ip'] == machine['intranet'] or p['ip'] == machine['internet']:
            pid = str(p['type']) + str(p['id'])
            if processids:
                if pid in processids:
                    if pfilter:
                        if str(p['type']) in pfilter:
                            procids.append(pid)
                    else:
                        procids.append(pid)
            else:
                if pfilter:
                    if str(p['type']) in pfilter:
                        procids.append(pid)
                else:
                    procids.append(pid)

    if len(procids) <= 0:
        actlog.log('this machine has no server defines !' + str(machine['intranet']))
        return 0
    actlog.log('machine', machine['internet'], 'sids=', procids)
    return procids
