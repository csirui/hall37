# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

'''
GeoHash封装
算法参照:https://github.com/yinqiwen/ardb/blob/master/doc/spatial-index.md
zhouxin,2014.4.15
'''
import math

from poker.util.pokercffi import POKERC
from poker.util.pokercffi import POKERFFI

DEFAULT_STEP = 26
QUERY_STEP = 17


def encode(lat, lon, step=DEFAULT_STEP):
    '''
    给定经纬度，返回geohash-int，step为精度
    26步最精确，误差0.6m
    '''
    geobits = POKERFFI.new("GeoHashBits *")
    ret = POKERC.geohash_encode(lat, lon, step, geobits)
    if ret < 0:
        return None
    return geobits.bits


def decode(geobit, step=DEFAULT_STEP):
    '''
    给出GEO的锚点, 计算相邻的4各经度纬度数据
    '''
    geobits = POKERFFI.new("GeoHashBits *")
    geobits.bits = geobit
    geobits.step = step
    geoarea = POKERFFI.new("GeoHashArea *")
    ret = POKERC.geohash_decode(geobits, geoarea)
    if ret < 0:
        return None
    return [geoarea.latitude.min, geoarea.latitude.max,
            geoarea.longitude.min, geoarea.longitude.max]


def get_neighbors(geobit, step=DEFAULT_STEP):
    '''
    给定geohash-int，返回相邻8块的geohash-int
    '''
    geobits = POKERFFI.new("GeoHashBits *")
    geobits.bits = geobit
    geobits.step = step
    geoneig = POKERFFI.new("GeoHashNeighbors *")
    ret = POKERC.geohash_get_neighbors(geobits, geoneig)
    if ret < 0:
        return None
    return [geoneig.west.bits, geoneig.east.bits,
            geoneig.south.bits, geoneig.north.bits,
            geoneig.north_west.bits, geoneig.north_east.bits,
            geoneig.south_east.bits, geoneig.south_west.bits]


def _deg2rad(d):
    return d * math.pi / 180.0


def get_distance(geoint1, geoint2, step=DEFAULT_STEP):
    """
    计算两者之间的距离 单位：米
    """
    EARTH_RADIUS_METER = 6378137.0;
    geo1 = decode(geoint1, step)
    geo2 = decode(geoint2, step)
    location1 = (geo1[2], geo1[0])
    location2 = (geo2[2], geo2[0])
    # print(location1, location2)
    flon = _deg2rad(location1[0])
    flat = _deg2rad(location1[1])
    tlon = _deg2rad(location2[0])
    tlat = _deg2rad(location2[1])
    con = math.sin(flat) * math.sin(tlat)
    con += math.cos(flat) * math.cos(tlat) * math.cos(flon - tlon)
    return int(math.acos(con) * EARTH_RADIUS_METER)
