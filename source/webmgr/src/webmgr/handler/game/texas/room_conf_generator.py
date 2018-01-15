import json
import codecs
import sys
import traceback

try:
    import xlrd
except Exception, e:
    print 'import xlrd error:', e
import os

#reload(sys)
#sys.setdefaultencoding("utf8")

def tryEval(v):
    try:
        v = v.strip()
        if not v:
            return
        return eval(v)
    except:
        #traceback.print_exc()
        print "ERROR VALUE: '%s'" % v
        print "LOCALS:"
        for k, v in sys._getframe().f_back.f_locals.items():
            print k, ':', v
        raise

def open_excel(xlsfile):
    try:
        data = xlrd.open_workbook(xlsfile)
        return data
    except Exception, e:
        print str(e)

def CreatRoot(data, sheet):
    sheet = data.sheet_by_name(sheet)
    row = sheet.nrows
    col = sheet.ncols
    conf = {}
    for r in range(3, row):
        roomId = sheet.row_values(r, start_colx=0, end_colx=1)[0]
        if not roomId:
            continue
        roomId = int(roomId)

        conf[roomId] = {}
        for c in range(col):
            columname = sheet.row_values(0, start_colx=c, end_colx=c + 1)[0]
            columType = sheet.row_values(2, start_colx=c, end_colx=c + 1)[0]
            v = sheet.row_values(r, start_colx=c, end_colx=c + 1)[0]
            if v != '':
                try:
                    if columType == "int":
                        columValue = int(round(float(v)))
                    elif columType == "string":
                        columValue = str(sheet.row_values(r, start_colx=c, end_colx=c + 1)[0])
                    elif columType == "dict":
                        if columname in data.sheet_names():
                            columValue = CreatSub(data, columname, roomId)
                        else:
                            columValue = tryEval(v)
                    elif columType == "tup":
                        columValue = tryEval(v)
                    else:
                        columValue = v
                except Exception as _e:
                    errStr = '\nError! roomId: %s, columname: %s, columType: %s, v: %s. \n' \
                             'Exception: %s' % (roomId, columname, columType, v, str(_e))
                    raise Exception(errStr)
                conf[roomId][columname] = columValue
    return conf

def CreatSub(data, sheetname, roomIdkey):
    sheet = data.sheet_by_name(sheetname)
    row = sheet.nrows
    col = sheet.ncols
    columname = ''
    columType = ''
    roomId = 0
    conf = {}
    v = 'novalue'
    try:
        for r in range(3, row):
            getid = sheet.row_values(r, start_colx=0, end_colx=1)[0]
            if not getid or getid == '':
                continue
            roomId = int(getid)
            if roomId == roomIdkey:
                conf = {}
                for c in range(col):
                    columname = sheet.row_values(0, start_colx=c, end_colx=c + 1)[0]
                    columType = sheet.row_values(2, start_colx=c, end_colx=c + 1)[0]

                    v = sheet.row_values(r, start_colx=c, end_colx=c + 1)[0]
                    if  v != '':
                        if columType == "int":
                            columValue = int(round(float(v)))
                        elif columType == "float":
                            columValue = round(float(v), 3)
                        elif columType == "string":
                            columValue = str(v)
                        elif columType == "dict":
                            subsheetname = sheetname + "-" + columname
                            if subsheetname in data.sheet_names():
                                columValue = CreatSub(data, subsheetname, roomIdkey)
                            else:
                                columValue = tryEval(v)
                        elif columType == "tup":
                            subsheetname = sheetname + "-" + columname
                            if subsheetname in data.sheet_names():
                                columValue = CreatTupSub(data, subsheetname, roomIdkey)
                                # if subsheetname=="matchConf-betsConf":
                                #     print "matchConf-betsConf",roomIdkey,columValue

                                if not columValue or len(columValue) == 0:
                                    columValue = tryEval(v)
                            else:
                                columValue = tryEval(v)
                        else:
                            columValue = v
                        if columname.lower() != "roomid":
                            keyword = columname.split(":")
                            if len(keyword) > 1:
                                if not conf.has_key(keyword[0]):
                                    conf[keyword[0]] = {}
                                conf[keyword[0]][keyword[1]] = columValue
                            else:
                                conf[columname] = columValue
    except Exception as _e:
        errStr = 'Error! roomId: %s, columname: %s, columType: %s, v: %s. ' \
                 'Exception: %s' % (roomId, columname, columType, v, str(_e))
        raise Exception(errStr)
    return conf



def CreatTupSub(data, sheetname, roomIdkey):
    sheet = data.sheet_by_name(sheetname)
    row = sheet.nrows
    col = sheet.ncols
    conf = []
    for r in range(3, row):
        getid = sheet.row_values(r, start_colx=0, end_colx=1)[0]
        if not getid or getid == '':
            continue
        roomId = int(getid)
        if roomId == roomIdkey:
            item = {}
            for c in range(col):
                columname = sheet.row_values(0, start_colx=c, end_colx=c + 1)[0]
                columType = sheet.row_values(2, start_colx=c, end_colx=c + 1)[0]
                v = sheet.row_values(r, start_colx=c, end_colx=c + 1)[0]
                if v != '':
                    if columType == "int":
                        columValue = int(round(float(v)))
                    elif columType == "float":
                        columValue = round(float(v))
                    elif columType == "string":
                        columValue = str(v)
                    elif columType == "dict":
                        columValue = tryEval(v)
                    elif columType == "tup":
                        subsheetname = sheetname + "-" + columname
                        if subsheetname in data.sheet_names():
                            columValue = CreatTupSub(data, subsheetname, roomIdkey)
                            if not columValue or len(columValue) == 0:
                                columValue = tryEval(v)
                        else:
                            #print subsheetname, v
                            columValue = tryEval(v)
                    else:
                        columValue = v
                    if columname.lower() != "roomid":
                        keyword = columname.split(":")
                        if len(keyword) > 1:
                            if not item.has_key(keyword[0]):
                                item[keyword[0]] = {}
                            item[keyword[0]][keyword[1]] = columValue
                        else:
                            item[columname] = columValue
            conf.append(item)
    return conf

#def test():
#    data = open_excel(file="test.xls")
#    conf = CreatRoot(data, "room")
#    with codecs.open('0.json', 'w', 'utf-8') as f:
#        json.dump(conf, f, indent=4, sort_keys=True, ensure_ascii=False)
#    f.close()

def gen(xlsfile, jsonfile):
    data = open_excel(xlsfile)
    conf = CreatRoot(data, "room")
    with codecs.open(jsonfile, 'w', 'utf-8') as f:
        json.dump(conf, f, indent=4, sort_keys=True, ensure_ascii=False)

def gen_split_file(xlsfile, jsonpath):
    data = open_excel(xlsfile)
    conf = CreatRoot(data, "room")

    subkeys = ["controlServerCount", "controlTableCount", "gameServerCount", "gameTableCount"]

    with codecs.open(os.path.join(jsonpath, "0.json.all"), 'w', 'utf-8') as f:
        json.dump(conf, f, indent=4, sort_keys=True, ensure_ascii=False)


    with codecs.open(os.path.join(jsonpath, "0.json"), 'w', 'utf-8') as f:
        newjson = {}
        for roomId, roomConf in conf.items():
            newjson[roomId] = {}
            for subkey in subkeys:
                newjson[roomId][subkey] = roomConf[subkey]
            for subkey in subkeys:
                del(roomConf[subkey])
        json.dump(newjson, f, indent=4, sort_keys=True, ensure_ascii=False)


    for roomId, roomConf in sorted(conf.items()):
        with codecs.open(os.path.join(jsonpath, "%s.json" % roomId), 'w', 'utf-8') as f:
            json.dump(roomConf, f, indent=4, sort_keys=True, ensure_ascii=False)

