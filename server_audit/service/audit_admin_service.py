# coding=utf-8
from bson import ObjectId
from cores.database import db, mongo_sync, mongo_async


def sync_get_admin_info_by_admin_id(admin_id):
    """
    通过管理员ID获取管理员信息
    :return: 
    """
    query_dict = {
        '_id': ObjectId(admin_id)
    }
    db_col = db.get_col_admin()
    return mongo_sync.mongo_find_one(db_col, query_dict)


async def get_admin_info_by_uid(uid):
    """
    通过用户ID获取管理员信息
    :return: 
    """
    query_dict = {
        'uid': uid
    }
    db_col = db.get_motordb_col_admin()
    admin = await mongo_async.mongo_find_one(db_col, query_dict)
    return admin


