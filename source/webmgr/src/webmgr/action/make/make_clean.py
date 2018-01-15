# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from tyserver.tyutils import fsutils


def action(options):
    '''
    '''
#     log_path = options.globaldict['log_path']
#     fsutils.cleanPath(log_path)

    bin_path = options.pokerdict['bin_path']
    fsutils.cleanPath(bin_path)

    return 1
