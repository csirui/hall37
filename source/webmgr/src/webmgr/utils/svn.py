# coding: utf-8

"""
对svn命令的包装
"""

import commands
import traceback
from tyserver.tyutils import tylog

try:
    from lxml import etree
except:
    tylog.error("import etree error")


def svnCmd(workingpath, cmd, *svnArgs):
    tylog.debug('svnCmd <<| workingpath, svnCmd, svnArgs:',
                workingpath, cmd, ' '.join(svnArgs))
    parts = []
    if workingpath:
        parts.append('cd %s' % workingpath)
    parts.append('LANG=en_US.UTF-8')
    parts.append(' '.join(['svn', cmd, '--non-interactive'] + list(svnArgs)))

    script = ';'.join(parts)
    status, output = commands.getstatusoutput(script)

    if status != 0:
        tylog.error("svnCmd >>| Failed"
                    '|path, cmd:', workingpath, cmd,
                    '|script:', script,
                    '|status, output:', status, output,
                    )
    else:
        tylog.debug('svnCmd >>'
                    '|path, cmd:', workingpath, cmd,
                    #'|script:', script,
                    #'|status, output:', status, output
                    )

    return script, status, output


def status(_file):
    _, _, xmldoc = svnCmd('', "status", _file, '--xml')
    status = etree.XML(xmldoc).xpath('//wc-status/@item')
    if status:
        return status[0]
    return ""


def export(_file, dst, revision='HEAD'):
    return svnCmd('', "export", '-r', revision, _file, dst, '--force')


def log(_file):
    _, _, xmldoc = svnCmd('', "log", _file, '-l 5', '--xml')
    selector = etree.XML(xmldoc).xpath('//msg|//date|//author')
    logs = []
    for i in selector:
        revision = i.getparent().attrib['revision']
        if not logs or logs[-1]['revision'] != revision:
            logs.append({'revision': revision})
        logs[-1][i.tag] = i.text
    return logs


def commit(_file, commitLog):
    if '\n' in commitLog:  # 处理多行提交日志
        commitLog = "$'%s'" % commitLog

    _, status, output = svnCmd('', "commit", _file, '-m', commitLog)
    return output


def revert(_file):
    _, _, output = svnCmd('', 'revert', _file)
    return output


def add(_file):
    _, _, output = svnCmd('', 'add', _file)
    return output


def test():
    f = '/Users/windaoo/ty/tytrunk/tywebmgr/src/a.sh'
    # revert(f)
    # add(f)
    # import random
    # with open(f, 'w') as fp:
    #     fp.write(str(random.randint(0, 10000)) + '\n')

    # commit(f, '中文日志\n第二行')
    # print log(f)
    # print log('/Users/windaoo/ty/tytrunk/team/testing/8/red_envelope/0.json')
    # print status(f)

    # export('/Users/windaoo/ty/tytrunk/team/testing/8/red_envelope/0.json',
    #        '/Users/windaoo/ty/tytrunk/team/testing/8/red_envelope/0.json.HEAD')
    pass


if __name__ == '__main__':
    import sys
    reload(sys)
    sys.setdefaultencoding("utf-8")

    test()