# -*- coding:utf-8 -*-
"""
mongo 同步基础方法
"""

from pymongo.errors import PyMongoError, AutoReconnect, OperationFailure, BulkWriteError
from pymongo import MongoClient
from cores.utils import logger
from bson.json_util import dumps

# 共享连接池
db_connection_map = {}


def mongo_collection(db_name, col_name, host, port):
    """
    获取db.collection
    """
    try:
        global db_connection_map
        if not db_connection_map.get((host, port)):
            pool_settings = {
                'maxPoolSize': 100,  # default is 100
                'minPoolSize': 0,  # default is 0
            }
            db_connection = MongoClient(host, port, **pool_settings)
            db_connection_map[(host, port)] = db_connection
    except AutoReconnect as e:
        logger.error('connect failed, host %s, port %d, %s' % (host, port, str(e)))
        return None
    database = db_connection_map[(host, port)].get_database(db_name)
    return database.get_collection(col_name)


def mongo_insert_one(col, item):
    """
    插入一条数据
    """
    try:
        col.insert_one(item)
        return True
    except (OperationFailure, AutoReconnect) as e:
        stritem = dumps(item)
        logger.error("mongo_insert failed, item %s, reason %s" % (stritem[0:10240], str(e)))
        return False


def mongo_insert_many(col, item, ordered=True):
    """
    插入多条数据
    """
    try:
        col.insert_many(item, ordered=ordered)
        return True
    except (OperationFailure, AutoReconnect) as e:
        stritem = dumps(item)
        logger.error("mongo_insert_many failed, item %s, reason %s, details %s" % (
            stritem[:1024], str(e), str(e.details)[:1024]))
        return False


def mongo_find_and_modify(col, query, update, upsert=False, sort=None, full_response=False, manipulate=False, **kwargs):
    """
    查找并更新
    """
    try:
        r = col.find_and_modify(query, update, upsert, sort, full_response, manipulate, **kwargs)
        return r
    except (OperationFailure, AutoReconnect) as e:
        logger.error("mongo_find_and_modify failed, query %s, reason %s" % (dumps(query), str(e)))
        return None


def mongo_find_one(col, query, *args, **kwargs):
    """
    查找一条数据
    """
    try:
        r = col.find_one(query, *args, **kwargs)
        return r
    except PyMongoError as e:
        logger.error("mongo_find_one failed, query %s, reason %s" % (dumps(query), str(e)))
        return -1


def mongo_update_one(col, query, update, up=False):
    """
    更新一条数据
    """
    try:
        col.update_one(query, update, upsert=up)
        return True
    except PyMongoError as e:
        logger.error("mongo_update_one failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


def mongo_update_many(col, query, update, up=False):
    """
    更新多条数据
    """
    try:
        col.update_many(query, update, upsert=up)
        return True
    except PyMongoError as e:
        logger.error("mongo_update_many failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


def mongo_find(col, query, *args, **kwargs):
    """
    查找多条数据
    """
    try:
        r = col.find(query, *args, **kwargs)
        return r
    except PyMongoError as e:
        logger.error("mongo_find failed, query %s, reason %s" % (dumps(query), str(e)))
        return -1


def mongo_find_count(col, query):
    """
    查找数据计数
    """
    try:
        r = col.find(query).count()
        return r
    except PyMongoError as e:
        logger.error("mongo_find_count failed, query %s, reason %s" % (dumps(query), str(e)))
        return -1


def mongo_find_sort_skip_limit(col, query, sort, skip, limit):
    """
    查找数据并排序、分页
    """
    try:
        r = col.find(query).sort(sort).skip(skip).limit(limit)
        return r
    except PyMongoError as e:
        logger.error("mongo_find_sort_skip_limit failed, query %s, reason %s" % (dumps(query), str(e)))
        return -1


def mongo_remove(col, query):
    """
    条件删除数据
    """
    try:
        col.remove(query)
        return True
    except PyMongoError as e:
        logger.error("mongo_remove failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


def mongo_batch_update(col, updatas, upsert=False, ordered=True):
    """
    批量更新数据
    """
    if ordered:
        bulk = col.initialize_ordered_bulk_op()
    else:
        bulk = col.initialize_unordered_bulk_op()  # paral execute
    if upsert:
        for item in updatas:
            bulk.find(item[0]).upsert().update(item[1])
    else:
        for item in updatas:
            bulk.find(item[0]).update(item[1])
    try:
        bulk.execute()
    except BulkWriteError as bwe:
        return bwe.details
