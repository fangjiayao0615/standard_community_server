# -*- coding:utf-8 -*-
"""
mongo 异步基础方法
"""

import motor.motor_tornado
import logging
from bson.json_util import dumps
from pymongo.errors import PyMongoError, AutoReconnect, OperationFailure, BulkWriteError


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
                'minPoolSize': 5,  # default is 0
            }
            db_connection = motor.motor_tornado.MotorClient(host, port, **pool_settings)
            db_connection_map[(host, port)] = db_connection

        db_connection = db_connection_map[(host, port)]
        db = db_connection.get_database(db_name)
        col = db[col_name]
    except AutoReconnect as e:
        logging.error('connect failed, host %s, port %d, %s' % (host, port, str(e)))
        return None

    return col


def mongo_db(db_name, host, port):
    """
    获取db
    """
    try:
        db_connection = motor.motor_tornado.MotorClient(host, port)
        db = db_connection.get_database(db_name)
    except AutoReconnect as e:
        logging.error('connect failed, host %s, port %d, %s' % (host, port, str(e)))
        return None

    return db


async def mongo_insert_one(col, item, returnid=False):
    """
    插入一条数据
    """
    try:
        ret = await col.insert_one(item)
        if returnid:
            return ret.inserted_id
        else:
            return True
    except (OperationFailure, AutoReconnect) as e:
        stritem = dumps(item)
        logging.warning("mongo_insert failed, item %s, reason %s" % (stritem[0:10240], str(e)))
        return False


async def mongo_insert_many(col, item, ordered=True):
    """
    插入多条数据
    """
    try:
        await col.insert_many(item, ordered=ordered)
        return True
    except (OperationFailure, AutoReconnect) as e:
        stritem = dumps(item)
        logging.error("mongo_insert failed, item %s, reason %s, details %s" % (
            stritem[:1024], str(e), str(e.details)[:1024]))
        return False


async def mongo_find_one(col, query, projection=None):
    """
    查找一条数据
    """
    try:
        if projection:
            r = await col.find_one(query, projection=projection)
        else:
            r = await col.find_one(query)
        return r
    except PyMongoError as e:
        logging.error("mongo_find_one failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


async def mongo_update(col, query, update, up=False):
    """
    更新多条数据
    """
    try:
        await col.update_many(query, update, upsert=up)
        return True
    except PyMongoError as e:
        logging.error("mongo_update failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


async def mongo_update_one(col, query, update, up=False, returnid=False):
    """
    更新一条数据
    """
    try:
        ret = await col.update_one(query, update, upsert=up)
        if up and returnid and ret:
            return {'matched_count': ret.matched_count, 'upserted_id': ret.upserted_id}
        else:
            return True
    except PyMongoError as e:
        logging.error("mongo_update failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


async def mongo_delete_one(col, query):
    """
    删除一条数据
    """
    try:
        r = await col.delete_one(query)
        return r
    except PyMongoError as e:
        logging.error("mongo_delete_one failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


async def mongo_find(col, query, projection=None):
    """
    查找多条数据
    """
    try:
        if projection:
            cursor = col.find(query, projection=projection)
        else:
            cursor = col.find(query)
        docs = await cursor.to_list(None)
        return docs
    except PyMongoError as e:
        logging.error("mongo_find failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


async def mongo_find_limit(col, query, limit, projection=None):
    """
    查找多条数据（分页）
    """
    try:
        if projection:
            cursor = col.find(query, projection=projection).limit(limit)
        else:
            cursor = col.find(query).limit(limit)
        docs = await cursor.to_list(None)
        return docs
    except PyMongoError as e:
        logging.error("mongo_find failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


async def mongo_find_count(col, query, limit=None):
    """
    统计数据数量
    """
    try:
        if motor.get_version_string().startswith('1'):
            r = await col.find(query).count()
        elif isinstance(limit, int) and limit > 0:
            r = await col.count_documents(query, limit=limit)
        else:
            r = await col.count_documents(query)
        return r
    except PyMongoError as e:
        logging.error("mongo_find_count failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


async def mongo_find_sort(col, query, sort, projection=None):
    """
    查找多条数据（排序）
    """
    try:
        if projection:
            cursor = col.find(query, projection=projection).sort(sort)
        else:
            cursor = col.find(query).sort(sort)
        docs = await cursor.to_list(None)
        return docs
    except PyMongoError as e:
        logging.error("mongo_find_sort failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


async def mongo_find_sort_skip_limit(col, query, sort, skip, limit, projection=None):
    """
    查找多条数据（分页-排序）
    """
    try:
        if projection:
            cursor = col.find(query, projection=projection).skip(skip).limit(limit)
        else:
            cursor = col.find(query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        docs = await cursor.to_list(None)
        return docs
    except PyMongoError as e:
        logging.error("mongo_find_sort_skip_limit failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


async def mongo_find_one_and_update(col, query, update, upsert=False, return_document=True):
    """
    查找并修改一条数据
    :param col: collection
    :param query: 查找条件
    :param update: 更新行为
    :param upsert: True 找不到则插入新数据  False 找不到则不做任何处理
    :param return_document:  True 返回修改后结果     False 返回修改前结果
    :return:
    """
    try:
        r = await col.find_one_and_update(query, update, upsert=upsert, return_document=return_document)
        return r
    except (OperationFailure, AutoReconnect) as e:
        logging.error("mongo_find_and_modify failed, query %s, reason %s" % (dumps(query), str(e)))
        return None


async def mongo_distinct(col, key, query_dict):
    """
    滤重查找
    """
    try:
        docs = await col.distinct(key, query_dict)
        return docs
    except PyMongoError as e:
        logging.error("mongo_distinct failed, key %s, query %s, reason %s" % (key, dumps(query_dict), str(e)))
        return False


async def mongo_delete(col, query):
    """
    删除多条数据
    """
    try:
        r = await col.delete_many(query)
        return r
    except PyMongoError as e:
        logging.error("mongo_delete failed, query %s, reason %s" % (dumps(query), str(e)))
        return False


async def mongo_aggregate(col, pipeline):
    """
    聚合查找
    """
    try:
        cursor = col.aggregate(pipeline)
        docs = await cursor.to_list(None)
        return docs
    except PyMongoError as e:
        logging.error("mongo_aggregate failed, pipeline %s, reason %s" % (dumps(pipeline), str(e)))
        return False


async def mongo_group(col, para_key, para_condition, para_initial, para_reduce):
    """
    分组查找
    """
    try:
        r = await col.group(para_key, para_condition, para_initial, para_reduce)
        return r
    except PyMongoError as e:
        logging.error("mongo_group failed, key %s, condition %s, initial %s, reduce %s, reason %s" % (
            dumps(para_key), dumps(para_condition), dumps(para_initial), dumps(para_reduce), str(e)))
        return False


async def mongo_bulk_write(col, requests, ordered=True):
    """
    批量更新
    """
    try:
        await col.bulk_write(requests, ordered=ordered)
        return True
    except BulkWriteError as bwe:
        logging.error("mongo_bulk_write failed, updates %r, reason %s" % (requests, str(bwe.details[:1024])))
        return False

