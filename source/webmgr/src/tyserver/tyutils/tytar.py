# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

import shutil, os, tarfile


###############################################################################
# UTIL for local machine action
###############################################################################
def tar_cvfz(taroutbase, root_dir):
    root_dir = os.path.abspath(root_dir)
    lastname = root_dir.split(os.path.sep)[-1]
    root_dir = os.path.dirname(root_dir)
    base_dir = '.' + os.path.sep + lastname
    # print taroutbase, lastname, 'tar', root_dir, base_dir
    return shutil.make_archive(taroutbase, 'tar', root_dir, base_dir)


def tar_xvf(tarfilepath, out_dir):
    tar = tarfile.open(tarfilepath)
    names = tar.getnames()
    for name in names:
        tar.extract(name, path=out_dir)
    tar.close()


if __name__ == '__main__' :
    tarfilepath = os.sys.argv[1]
    outdir = os.sys.argv[2]
    print 'tarfilepath =', tarfilepath
    print 'outdir =', outdir
    tar_xvf(tarfilepath, outdir)
    print 'TY_TASK_RESULT_INT=0'
    print 'done'

