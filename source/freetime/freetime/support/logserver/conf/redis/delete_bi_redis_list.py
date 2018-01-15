import time

import redis


def delete(port):
    """delete redis date 3 day ago"""
    COUNT = 100
    DAY = 1
    MATCH = 'index:*'
    offset = 0

    time3a = int(time.time()) - DAY * 86400
    rs = redis.StrictRedis(host='127.0.0.1', port=port, db=0)
    while True:
        l = rs.scan(offset, MATCH, COUNT)
        try:
            if l[0] == 0:
                for i in l[1]:
                    if i.find('index:') != -1:
                        recs = rs.lrange(i, 0, -1)
                        index = -1
                        for j in range(0, len(recs), 2):
                            if int(recs[j]) < time3a:
                                continue
                            else:
                                index = j
                                break
                        if index == -1:
                            rs.delete(i)
                            print port, i, recs[0:]
                        else:
                            rs.ltrim(i, index, -1)
                            print port, i, recs[0:index]
                break
            else:
                offset = l[0]
            for i in l[1]:
                if i.find('index:') != -1:
                    recs = rs.lrange(i, 0, -1)
                    index = -1
                    for j in range(0, len(recs), 2):
                        if int(recs[j]) < time3a:
                            continue
                        else:
                            index = j
                            break
                    if index == -1:
                        rs.delete(i)
                        print port, i, recs[0:]
                    else:
                        rs.ltrim(i, index, -1)
                        print port, i, recs[0:index]
        except:
            pass


#### exec delete redis data #####
Port_list = ['7901', '7902', '7903', '7904', '7905', '7906', '7907', '7908']
for port in Port_list:
    delete(port)
