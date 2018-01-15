# -*- coding=utf-8 -*-
# Author:        zipxing@hotmail.com
# Created:       2015年04月10日 星期五 14时26分31秒
#

import collections
import functools
import json
from copy import deepcopy
from heapq import nsmallest
from itertools import ifilterfalse
from operator import itemgetter
from time import time

from datetime import datetime

import freetime.util.log as ftlog


class Counter(dict):
    'Mapping where default values are zero'

    def __missing__(self, key):
        return 0


def lru_cache(maxsize=100, cache_key_args_index=1):
    '''Least-recently-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    '''
    maxqueue = maxsize * 10

    def decorating_function(user_function,
                            len_=len, iter_=iter, tuple_=tuple, sorted_=sorted, KeyError_=KeyError):
        cache = {}  # mapping of args to results
        queue = collections.deque()  # order that keys have been used
        refcount = Counter()  # times each key is in the queue
        sentinel = object()  # marker for looping around the queue

        # lookup optimizations (ugly but fast)
        queue_append, queue_popleft = queue.append, queue.popleft
        queue_appendleft, queue_pop = queue.appendleft, queue.pop

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            # cache key records both positional and keyword args
            key = args[cache_key_args_index]

            # record recent use of this key
            queue_append(key)
            refcount[key] += 1

            # get cache entry or compute if not found
            try:
                result = cache[key]
                wrapper.hits += 1
            except KeyError_:
                result = user_function(*args, **kwds)
                cache[key] = result
                wrapper.misses += 1

                # purge least recently used cache entry
                if len_(cache) > maxsize:
                    key = queue_popleft()
                    refcount[key] -= 1
                    while refcount[key]:
                        key = queue_popleft()
                        refcount[key] -= 1
                    del cache[key], refcount[key]

            # periodically compact the queue by eliminating duplicate keys
            # while preserving order of most recent access
            if len_(queue) > maxqueue:
                refcount.clear()
                queue_appendleft(sentinel)
                for key in ifilterfalse(refcount.__contains__,
                                        iter_(queue_pop, sentinel)):
                    queue_appendleft(key)
                    refcount[key] = 1

            return result

        def clearKey(*args):
            for key in args:
                if key in cache:
                    del cache[key]

        def clear():
            cache.clear()
            queue.clear()
            refcount.clear()
            wrapper.hits = wrapper.misses = 0

        wrapper.hits = wrapper.misses = 0
        wrapper.clear = clear
        wrapper.clearKey = clearKey
        wrapper.cache = cache
        wrapper.refcount = refcount
        wrapper.queue = queue

        return wrapper

    return decorating_function


def lfu_cache(maxsize=100, cache_key_args_index=1):
    '''Least-frequenty-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Least_Frequently_Used

    '''

    def decorating_function(user_function):
        cache = {}  # mapping of args to results
        use_count = Counter()  # times each key has been accessed

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            key = args[cache_key_args_index]

            use_count[key] += 1

            # get cache entry or compute if not found
            try:
                result = cache[key]
                wrapper.hits += 1
            except KeyError:
                result = user_function(*args, **kwds)
                cache[key] = result
                wrapper.misses += 1

                # purge least frequently used cache entry
                if len(cache) > maxsize:
                    for key, _ in nsmallest(maxsize // 10,
                                            use_count.iteritems(),
                                            key=itemgetter(1)):
                        if key in cache:
                            del cache[key]
                        if key in use_count:
                            del use_count[key]

            return result

        def clear_keys(args):
            for key in args:
                if key in cache:
                    ftlog.debug('clear_keys->ok->', key)
                    del cache[key]
                else:
                    ftlog.debug('clear_keys->not found->', key)
                if key in use_count:
                    del use_count[key]

        def clear():
            cache.clear()
            use_count.clear()
            wrapper.hits = 0
            wrapper.misses = 0

        wrapper.hits = 0
        wrapper.misses = 0
        wrapper.use_count = use_count
        wrapper.cache = cache
        wrapper.clear = clear
        wrapper.clear_keys = clear_keys
        return wrapper

    return decorating_function


def _count_pps_info(wrapper):
    try:
        if wrapper.call_count % wrapper.pps_block == 0:
            ct = datetime.now()
            dt = ct - wrapper.pps_time
            dt = dt.seconds + dt.microseconds / 1000000.0
            pps = '%0.2f' % (wrapper.pps_block / dt)
            wrapper.pps_time = ct
            if wrapper.hits + wrapper.misses > 0:
                rate = '%0.3f' % (float(wrapper.hits) / float(wrapper.hits + wrapper.misses))
            else:
                rate = 'None'
            ftlog.info("LFUTIMECACHE PPS", pps, 'ALLCOUNT=', wrapper.call_count, 'MAXSIZE=', wrapper.maxsize,
                       'CACHE COUNT=', len(wrapper.cache), 'HITS=', wrapper.hits, 'MISSES=', wrapper.misses,
                       'HIT RATE=', rate, 'NAME=', wrapper.cache_name)
    except:
        ftlog.error()


_cache_groups = {}
_cache_wrappers = {}


def cloneData(data):
    '''
    使用JSON的loads和dump克隆一个数据对象
    '''
    try:
        return json.loads(json.dumps(data))
    except:
        ftlog.warn('Can not use json copy !! data=' + repr(data))
        return deepcopy(data)


def lfu_time_cache(maxsize=100, mainindex=0, subindex=1, group=None):
    '''Least-frequenty-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Least_Frequently_Used

    '''

    def decorating_function(user_function):
        if group != None:
            cache, use_count = _cache_groups.get(group, (None, None))
            if cache == None:
                cache = {}  # mapping of args to results
                use_count = Counter()  # times each key has been accessed
                _cache_groups[group] = (cache, use_count)
        else:
            cache = {}  # mapping of args to results
            use_count = Counter()  # times each key has been accessed

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            if wrapper.pps_info:
                _count_pps_info(wrapper)

            key = args[mainindex]
            if subindex >= 0:
                subkey = args[subindex]
            wrapper.call_count += 1
            use_count[key] = wrapper.call_count

            # get cache entry or compute if not found
            try:
                if subindex >= 0:
                    result = cache[key][subkey]
                else:
                    result = cache[key]
                wrapper.hits += 1
                if wrapper.cache_log:
                    ftlog.info('lfu_time_cache hits', wrapper.cache_name, key)

            except KeyError:
                result = user_function(*args, **kwds)
                if subindex >= 0:
                    if key in cache:
                        cache[key][subkey] = result
                    else:
                        cache[key] = {subkey: result}
                else:
                    cache[key] = result
                wrapper.misses += 1
                if wrapper.cache_log:
                    ftlog.info('lfu_time_cache miss', wrapper.cache_name, key)

                # purge least frequently used cache entry
                _maxsize = wrapper.maxsize
                if len(cache) > _maxsize:
                    for key, _ in nsmallest(_maxsize // 10,
                                            use_count.iteritems(),
                                            key=itemgetter(1)):
                        if key in cache:
                            del cache[key]
                        if key in use_count:
                            del use_count[key]

            return result

        def clear_key(dataKey):
            c = 0
            if dataKey in cache:
                c = 1
                del cache[dataKey]
            if dataKey in use_count:
                del use_count[dataKey]
            if wrapper.cache_log:
                ftlog.info('lfu_time_cache clear_key', wrapper.cache_name, dataKey)
            return c

        def clear_keys(args):
            c = 0
            for key in args:
                c + clear_key(key)
            return c

        def clear():
            cache.clear()
            use_count.clear()
            wrapper.hits = 0
            wrapper.misses = 0
            wrapper.call_count = 0
            wrapper.pps_time = datetime.now()
            if wrapper.cache_log:
                ftlog.info('lfu_time_cache clear all', wrapper.cache_name)

        def replace_group_data(mainKey, subKey, subdata):
            data = cache.get(mainKey, None)
            if data != None:
                data[subKey] = subdata
                if wrapper.cache_log:
                    ftlog.info('lfu_time_cache replace_group_data !', mainKey, subKey, subdata)

        def update_group_dict_data(mainKey, subKey, subdatas):
            data = cache.get(mainKey, None)
            if data != None:
                subData = data.get(subKey, None)
                if subData != None:
                    for k, v in subdatas.items():
                        subData[k] = cloneData(v)
                        if wrapper.cache_log:
                            ftlog.info('lfu_time_cache update_group_dict_data !', mainKey, k, v)

        def remove_group_dict_data(mainKey, subKey, subdatas):
            if wrapper.cache_log:
                ftlog.info('lfu_time_cache remove_group_dict_data !', mainKey, subKey, subdatas)
            data = cache.get(mainKey, None)
            if data != None:
                subData = data.get(subKey, None)
                if subData != None:
                    for k, _ in subdatas.items():
                        if k in subData:
                            del subData[k]
                            if wrapper.cache_log:
                                ftlog.info('lfu_time_cache remove_group_dict_data !', mainKey, subKey, k)

        def replace_group_dict_data(mainKey, subKey, field, value):
            data = cache.get(mainKey, None)
            if data != None:
                subData = data.get(subKey, None)
                if subData != None:
                    subData[field] = cloneData(value)
                    if wrapper.cache_log:
                        ftlog.info('lfu_time_cache replace_group_dict_data !', mainKey, subKey, field, value)

        def replace_group_dict_data_nx(mainKey, subKey, field, value):
            data = cache.get(mainKey, None)
            if data != None:
                subData = data.get(subKey, None)
                if field not in subData:
                    subData[field] = cloneData(value)
                    if wrapper.cache_log:
                        ftlog.info('lfu_time_cache replace_group_dict_data_nx !', mainKey, subKey, field, value)

        def incrby_group_dict_data(mainKey, subKey, field, value):
            assert (isinstance(value, (int, float)))
            data = cache.get(mainKey, None)
            if data != None:
                subData = data.get(subKey, None)
                if subData != None:
                    if subData.get(field, None) == None:
                        subData[field] = value
                    else:
                        subData[field] += value
                    if wrapper.cache_log:
                        ftlog.info('lfu_time_cache incrby_group_dict_data !', mainKey, subKey, field, value,
                                   subData[field])

        wrapper.call_count = 0
        wrapper.hits = 0
        wrapper.misses = 0
        wrapper.use_count = use_count
        wrapper.cache = cache
        wrapper.clear = clear
        wrapper.clear_key = clear_key
        wrapper.clear_keys = clear_keys
        wrapper.replace_group_data = replace_group_data
        wrapper.update_group_dict_data = update_group_dict_data
        wrapper.replace_group_dict_data = replace_group_dict_data
        wrapper.incrby_group_dict_data = incrby_group_dict_data
        wrapper.remove_group_dict_data = remove_group_dict_data
        wrapper.maxsize = maxsize
        wrapper.pps_info = 1
        wrapper.pps_block = 10000
        wrapper.pps_time = datetime.now()
        wrapper.cache_log = 0
        wrapper.cache_name = user_function.__name__
        if user_function.__name__ in _cache_wrappers:
            raise Exception('the cache function name alread exits !' + user_function)
        else:
            _cache_wrappers[user_function.__name__] = wrapper
        return wrapper

    return decorating_function


def lfu_alive_cache(maxsize=100, cache_key_args_index=0, alive_second=30):
    '''Least-frequenty-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Least_Frequently_Used

    '''

    def decorating_function(user_function):
        cache = {}  # mapping of args to results
        use_count = Counter()  # times each key has been accessed

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            key = args[cache_key_args_index]
            ct = int(time())
            if key in use_count:
                if ct - use_count[key] > alive_second:
                    if key in cache:
                        del cache[key]
                        use_count[key] = ct
            else:
                use_count[key] = ct

            try:
                result = cache[key]
            except KeyError:
                result = user_function(*args, **kwds)
                if key in cache:  # recheck
                    result = cache[key]
                else:
                    cache[key] = result
                    # purge least frequently used cache entry
                    if len(cache) > maxsize:
                        for key, _ in nsmallest(maxsize // 10, use_count.iteritems(), key=itemgetter(1)):
                            if key in cache:
                                del cache[key]
                            if key in use_count:
                                del use_count[key]
            return result

        def clear_keys(args):
            for key in args:
                if key in cache:
                    del cache[key]
                if key in use_count:
                    del use_count[key]

        def clear():
            cache.clear()
            use_count.clear()

        wrapper.use_count = use_count
        wrapper.cache = cache
        wrapper.clear = clear
        wrapper.clear_keys = clear_keys
        return wrapper

    return decorating_function
