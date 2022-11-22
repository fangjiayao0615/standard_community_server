# -*- coding:utf-8 -*-
"""
tag service 方法
"""
import time
from bson import ObjectId

from cores.const import const_tag, const_base
from cores.database import mongo_async, db
from cores.base import base_service


def build_tag_query_dict(tid=None, name=None, status=None, ttype=None):
    """
    构造标签查询query
    :return:
    """
    query_dict = {}

    if name is not None:
        query_dict['name'] = {'$regex': name}

    if tid:
        if isinstance(tid, str):
            query_dict['_id'] = ObjectId(tid)
        elif isinstance(tid, const_base.LIST_TYPES):
            query_dict['_id'] = {'$in': base_service.ensure_mongo_obj_ids(tid)}

    if ttype is not None:
        query_dict['ttypes'] = ttype
        if isinstance(ttype, const_base.LIST_TYPES):
            query_dict['ttypes'] = {'$in': list(ttype)}

    if status is not None:
        query_dict['status'] = status
        if isinstance(status, const_base.LIST_TYPES):
            query_dict['status'] = {'$in': list(status)}

    return query_dict


async def query_tags_detail_for_handler(tid, viewer_favor_info=None):
    """
    查询标签列表
    :return:
    """
    tag_col = db.get_motordb_col_tag()
    tag = await mongo_async.mongo_find_one(tag_col, {'_id': ObjectId(tid)})
    if not tag:
        return {}
    return build_tag_info_by_favor(tag, viewer_favor=viewer_favor_info)


async def query_tags_for_handler(offset=0, limit=10, query_dict=None, sorts=None, viewer_favor_info=None):
    """
    查询标签列表
    :return:
    """
    query_dict = query_dict or {}
    sorts = sorts or [('post_num', -1)]

    tag_col = db.get_motordb_col_tag()
    tags = await mongo_async.mongo_find_sort_skip_limit(tag_col, query_dict, sorts, offset, limit+1)
    if not tags:
        return False, {}, []

    has_more = bool(len(tags) > limit)
    tags = tags[:limit]
    next_cursor_info = {'offset': offset+limit, 'limit': limit}

    result = []
    for tag in tags:
        res = build_tag_info_by_favor(tag, viewer_favor=viewer_favor_info)
        result.append(res)
    return has_more, next_cursor_info, result


def build_tag_info_by_favor(tag, viewer_favor=None):
    """
    构造标签信息, 包含是否有查看者已关注标识。
    :return:
    """
    result = {}
    if tag:
        result = build_tag_base_info(tag)

        # 查看者是否已关注该标题
        result['favored'] = False
        if viewer_favor:
            result['favored'] = result['tid'] in viewer_favor.get('f_tids', [])

    return result


def build_tag_base_info(tag):
    """
    构造标签基础信息
    :return:
    """
    result = {}
    if tag:
        result = {
            'tid': str(tag['_id']),
            'ttypes': tag['ttypes'],
            'name': tag['name'],
            'status': tag['status'],
            'desc': tag['desc'],
            'cover_info': base_service.build_img_infos_item(tag['raw_cover']),
            'post_num': tag.get('post_num', 0) if tag.get('post_num', 0) >= 0 else 0,
            'favor_num': tag.get('favor_num', 0) if tag.get('favor_num', 0) >= 0 else 0,
            'ct': tag['ct'],
            'ut': tag['ut'],
        }
    return result


async def create_new_tag(name, raw_cover, desc='', ttypes=None, post_num=0, crt_post_num=0, status=None, extra=None):
    """
    创建新tag
    :return:
    """

    if ttypes is None:
        ttypes = [const_tag.TAG_TYPE_NORMAL]
    if isinstance(ttypes, int):
        ttypes = [ttypes]

    now_ts = int(time.time())
    tag_col = db.get_motordb_col_tag()
    new_tag = {
        'ttypes': ttypes,
        'name': name,
        'raw_cover': raw_cover,
        'desc': desc,
        'status': status or const_tag.TAG_STATUS_VISIBLE,
        'post_num': post_num,
        'crt_post_num': crt_post_num,
        'ct': now_ts,
        'ut': now_ts,
    }
    if extra and isinstance(extra, dict):
        new_tag.update(extra)
    tid = await mongo_async.mongo_insert_one(tag_col, new_tag, returnid=True)
    if not tid:
        return ''
    tid = str(tid)
    return tid


async def get_tag_map_by_tids(tids):
    """
    批量获取标签信息映射表
    :return:
    """
    result = {}
    if not tids:
        return result

    tag_col = db.get_motordb_col_tag()
    tags = await mongo_async.mongo_find(tag_col, {'_id': {'$in': base_service.ensure_mongo_obj_ids(tids)}})
    for tag in tags:
        result[str(tag['_id'])] = tag
    return result


async def increase_tag_count_stat(tid_or_tids=None, post_num_inc_num=0, favor_num_inc=0, view_num=0):
    """
    修改tag的计数字段
    :param tid_or_tids: tid 或 tid列表
    :param post_num_inc_num: 发帖新增数
    :param favor_num_inc: 关注人数目
    :param delete_pid: 需要从最近发帖pids缓存中删除的pid
    :param add_pid: 需要往最近发帖pids缓存中添加的pid
    :param pid_ct: 帖子的创建时间
    :param view_num: 查看次数+1
    :return:
    """
    if not tid_or_tids:
        return

    # 查询条件
    query_dict = build_tag_query_dict(tid_or_tids)

    # 新增计数
    inc_dict = {}
    if post_num_inc_num:
        inc_dict['post_num'] = post_num_inc_num
    if favor_num_inc:
        inc_dict['favor_num'] = favor_num_inc
    if view_num:
        inc_dict['view_num'] = view_num

    # 更新修改时间
    set_dict = {'ut': int(time.time())}

    # 保存修改数据
    update_dict = {}
    if inc_dict:
        update_dict['$inc'] = inc_dict
    if set_dict:
        update_dict['$set'] = set_dict

    # 更新tag统计
    tag_col = db.get_motordb_col_tag()
    await mongo_async.mongo_update(tag_col, query_dict, update_dict)

