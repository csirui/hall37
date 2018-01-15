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

import os

from freetime.core import cffi_

__cdef_text = """
typedef enum
{
    GEOHASH_NORTH = 0,
    GEOHASH_EAST,
    GEOHASH_WEST,
    GEOHASH_SOUTH,
    GEOHASH_SOUTH_WEST,
    GEOHASH_SOUTH_EAST,
    GEOHASH_NORT_WEST,
    GEOHASH_NORT_EAST
} GeoDirection;

typedef struct
{
        uint64_t bits;
        uint8_t step;
} GeoHashBits;

typedef struct
{
        double max;
        double min;
} GeoHashRange;

typedef struct
{
        GeoHashBits hash;
        GeoHashRange latitude;
        GeoHashRange longitude;
} GeoHashArea;

typedef struct
{
        GeoHashBits north;
        GeoHashBits east;
        GeoHashBits west;
        GeoHashBits south;
        GeoHashBits north_east;
        GeoHashBits south_east;
        GeoHashBits north_west;
        GeoHashBits south_west;
} GeoHashNeighbors;

int geohash_encode(double latitude, double longitude, uint8_t step, GeoHashBits* hash);
int geohash_decode(const GeoHashBits* hash, GeoHashArea* area);
int geohash_get_neighbors(const GeoHashBits* hash, GeoHashNeighbors* neighbors);
int des_decrypt(unsigned char *src, unsigned srclen, unsigned char *key, unsigned char *out);
int des_encrypt(unsigned char *src, unsigned srclen, unsigned char *key, unsigned char *out);

"""
__sodir = os.path.dirname(os.path.abspath(__file__)) + "/cffi/"
cffi_.loadCffi('pokerutil', __cdef_text, __sodir)

'''
POKER大模块使用的CFFI的集中定义装载
'''
POKERC, POKERFFI = cffi_.getCffi('pokerutil')
