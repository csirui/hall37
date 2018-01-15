import os
import sys
import redis
import json, traceback

'''
配置分三个层级：freetime，poker，game
其中前两级是全局配置，在redis里的键值名字和对应的配置文件举例：
    freetime:db      <-->  freetime/db.json
    freetime:server  <-->  freetime/server.json
    freetime:global  <-->  freetime/global.json
    poker:cmd        <-->  poker/cmd.json
    poker:room       <-->  poker/room.json
    poker:global     <-->  poker/global.json

第三层配置，是按照gameid和clientid组织的(game:<gameid>:<game_module>:<client_id>):
 *** 注1:client_id为字典的自增id，是自然数
 *** 注2:0.json是一个特殊的配置，一些模版或者全局性的配置，请写到0.json中
     game:9999:ui:1  <-->  game/9999/ui/1.json
     game:9999:act:1 <-->  game/9999/act/1.json

 *** 注3:所有配置均为标准json，但可以加#注释，在导入redis前，会过滤掉#开头的行
'''

global_config_level=["freetime", "poker"]
client_config_level=["game"]


def filterComment(f):
    res = ''
    for l in open(f, 'r'):
        if not l.strip().startswith("#"):
            res+=l
    return res


def scanJsonAndSetRedis(rs, parent, fs, key_prefix):
    for f in fs:
        try:
            if parent.find(".svn")==-1:
                js = json.loads(filterComment(parent+'/'+f))
                jstr = json.dumps(js)
                fn = f.split('.')[0]
                key = key_prefix+fn
                rs.set(key, jstr)
                print key
        except:
            print "parse", parent, f, "error!"
            traceback.print_exc()
    

def processConfig(root_path):
    #读取配置redis的地址,并初始化连接
    try:
        for l in open(root_path+'/redis.conf'):
            rc = l.split()
            rs = redis.StrictRedis(host=rc[0], port=int(rc[1]), db=int(rc[2]))
            break
    except:
        print "read redis.conf error!", root_path
        return

    #初始化freetime和poker的配置
    for cl in global_config_level:
        for parent,dirnames,filenames in os.walk(root_path+'/'+cl): 
            scanJsonAndSetRedis(rs, parent, filenames, cl+':')

    #初始化game的配置
    for parent,dirnames,filenames in os.walk(root_path+'/game'): 
        for game_id in dirnames:
            for pt, ds, fs in os.walk(root_path+'/game/'+game_id):
                for game_mod in ds:
                    for pts, dss, fss in os.walk(root_path+'/game/'+game_id+'/'+game_mod):
                        scanJsonAndSetRedis(rs, pts, fss, 'game:'+game_id+':'+game_mod+':')
        

processConfig("/home/zhoux/freetime/trunk/misc/config/online")
#processConfig("/home/zhoux/config/online")
#processConfig("/home/zhoux/config/sim")
#processConfig("/home/zhoux/config/dev")
