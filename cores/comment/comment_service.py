# -*- coding:utf-8 -*-
"""
comment service 方法
"""
import copy

import time
from bson import ObjectId

from cores.const import const_cmt, const_base
from cores.database import db, mongo_async
from cores.favor import favor_service
from cores.base import base_service
from cores.user import user_service
from cores.post import post_service


def build_comment_query_sort(sort_type):
    """
    构造排序信息
    :return: 
    """
    # 排序最新
    sort = [('ct', -1)]
    # 排序最热
    if sort_type == const_cmt.COMMENT_QUERY_SORT_T_HOT:
        sort = [('rec_score', -1), ('ct', -1)]
    return sort


def build_comment_query_dict(uid=None, pid=None, status=None, cid=None, ct_lt=None, ct_gte=None, ctype=None):
    """
    构造评论查询参数
    :return:
    """
    query_dict = {}

    if cid is not None:
        if isinstance(cid, str):
            query_dict['_id'] = ObjectId(cid)
        if isinstance(cid, const_base.LIST_TYPES):
            query_dict['_id'] = {'$in': base_service.ensure_mongo_obj_ids(cid)}

    if uid:
        query_dict['uid'] = uid
        if isinstance(uid, const_base.LIST_TYPES):
            query_dict['uid'] = {'$in': list(uid)}

    if pid is not None:
        query_dict['pid'] = pid
        if isinstance(pid, const_base.LIST_TYPES):
            query_dict['pid'] = {'$in': list(pid)}

    if status is not None:
        query_dict['status'] = status
        if isinstance(status, const_base.LIST_TYPES):
            query_dict['status'] = {'$in': list(status)}

    if ct_gte or ct_lt:
        query_dict['ct'] = {}
        if ct_gte:
            query_dict['ct']['$gte'] = ct_gte
        if ct_lt:
            query_dict['ct']['$lt'] = ct_lt

    if ctype is not None:
        query_dict['ctype'] = ctype

    return query_dict


async def get_comment_info_list_for_handler(uid, cursor_info, query_dict, sorts, favor_info=None):
    """
    获取帖子下的评论列表
    :return:
    """
    offset = cursor_info.get('offset', 0) if cursor_info else 0
    limit = cursor_info.get('limit', const_cmt.COMMENT_PAGE_PER_NUM) if cursor_info else const_cmt.COMMENT_PAGE_PER_NUM
    limit = const_cmt.COMMENT_PAGE_PER_NUM_MAX if limit > const_cmt.COMMENT_PAGE_PER_NUM_MAX else limit

    # 获取当前帖子下评论列表
    comment_col = db.get_motordb_col_comment()
    comments = await mongo_async.mongo_find_sort_skip_limit(comment_col, query_dict, sorts, offset, limit+1)
    has_more = bool(len(comments) > limit)
    comments = comments[:limit]
    if not comments:
        return False, copy.deepcopy(cursor_info), []

    # 获取用户信息映射表
    uids = [comment['uid'] for comment in comments]
    user_map = await user_service.get_user_map_by_uids(uids)

    # 构造赞踩列表
    cids = [str(comment['_id']) for comment in comments]
    like_cids, disliked_cids = await favor_service.get_user_liked_disliked_cids(uid, cids)

    # 构造返回列表
    result = []
    for comment in comments:
        result.append(
            build_comment_base_info(
                comment, user_map, like_cids, disliked_cids, viewer_favor_info=favor_info)
        )

    # 下一次分页信息
    next_cursor_info = {
        'offset': offset + limit,
        'limit': limit,
    }

    return has_more, next_cursor_info, result


async def get_comment_by_id(cid):
    """
    获取单个评论信息
    :return:
    """
    if not cid:
        return {}

    comment_map = await get_comment_info_map_by_cids([cid])
    return comment_map.get(cid, {})


async def get_comment_info_map_by_cids(cids):
    """
    批量获取评论信息映射表
    :return:
    """
    if not cids:
        return {}

    result = {}
    comment_col = db.get_motordb_col_comment()
    comments = await mongo_async.mongo_find(comment_col, {'_id': {'$in': base_service.ensure_mongo_obj_ids(cids)}})
    for comment in comments:
        result[str(comment['_id'])] = comment
    return result


async def attach_fine_comment_for_handler(pid, uid, cursor_info, comments):
    """
    首页插入精评
    :param pid:
    :param uid:
    :param cursor_info:
    :param comments:
    :return:
    """
    # 无指定pid
    if not pid:
        return comments
    # 非首页
    if cursor_info:
        return comments
    # 插入置顶评论
    cursor_info = {'offset': 0, 'limit': const_cmt.COMMENT_PAGE_PER_NUM_MAX}
    sorts = [('rec_score', -1), ('ct', -1)]
    query_dict = build_comment_query_dict(pid=pid, status=const_cmt.COMMENT_STATUS_FINE)
    _, _, fine_comments = await get_comment_info_list_for_handler(uid, cursor_info, query_dict, sorts)
    fine_comments.extend(comments)
    comments = fine_comments
    return comments


async def create_new_comment(uid, pid, text, raw_imgs=None, likes=0, p_uid=None, ctype=None, status=None, extra=None, ct=None):
    """
    创建新评论
    :return:
    """
    new_cid_obj = ObjectId()
    now_ts = int(time.time())
    comment_col = db.get_motordb_col_comment()

    # 补充 p_uid
    if pid and not p_uid:
        post = await post_service.get_post_by_id(pid)
        p_uid = post['uid'] if post else ''

    new_comment = {
        '_id': new_cid_obj,
        'ctype': ctype or const_cmt.COMMENT_TYPE_NORMAL,
        'uid': uid,
        'pid': pid,
        'p_uid': p_uid or '',
        'text': text,
        'status': status or const_cmt.COMMENT_STATUS_VISIBLE,
        'likes': likes,
        'ct': ct or now_ts,
        'ut': ct or now_ts,
        'raw_imgs': raw_imgs or [],
        'score': 0,
    }
    if extra is not None:
        new_comment.update(extra)

    cid = await mongo_async.mongo_insert_one(comment_col, new_comment, returnid=True)
    cid = str(cid) if cid else ''

    # 增加评论计数
    if cid and pid and new_comment['status'] >= const_cmt.COMMENT_STATUS_VISIBLE:
        await create_cmt_stat_by_new_comment(new_comment)

    return cid, new_comment


async def create_cmt_stat_by_new_comment(new_comment):
    """
    根据评论信息新增相关记录
    :param new_comment:
    :return:
    """
    # 获取上一级别的用户信息
    uid = new_comment.get('uid')
    pid = new_comment.get('pid')

    # 帖子下评论数目+1
    await post_service.increase_post_count_stat(pid, cmt_inc_num=1)

    # 更新统计计数
    await favor_service.increase_favor_count_stat(uid, comment_num_inc_num=1)


async def delete_comment_for_handler(c_uid, cid):
    """
    用户删除评论信息
    :param c_uid: 评论作者
    :param cid: 评论ID
    :return:
    """
    # 删除评论并获取之前状态
    comment_col = db.get_motordb_col_comment()
    query_dict = build_comment_query_dict(uid=c_uid, cid=cid)
    before_comment = await mongo_async.mongo_find_one_and_update(
        comment_col, query_dict, {'$set': {'status': const_cmt.COMMENT_STATUS_SELF_DELETE}}, upsert=False, return_document=False)

    # 如果不存在, 或之前已经删除了则直接返回
    if not before_comment or before_comment['status'] == const_cmt.COMMENT_STATUS_SELF_DELETE:
        return

    # 更改用户发出的评论数目-1
    await favor_service.increase_favor_count_stat(c_uid, comment_num_inc_num=-1)

    # 更新帖子的评论数目-1
    await post_service.increase_post_count_stat(before_comment['pid'], cmt_inc_num=-1)


def build_comment_base_info(comment, user_map, user_like_cids, user_dislike_cids, viewer_favor_info=None):
    """
    构造评论的基本信息
    :param uid: 请求者的UID
    :param comment:
    :param user_map:
    :param org_comment_map:
    :param user_like_cids: 外层comment列表里面，已经被用户点赞的cid列表
    :param user_dislike_cids: 外层comment列表里面，已经被用户点踩的cid列表
    :param sub_comment_map: 子评论映射表
    :return:
    """
    # 评论基本数据
    cid = str(comment['_id'])
    result = {
        'cid': cid,
        'pid': comment['pid'],
        'ct': comment['ct'],
        'ctype': comment['ctype'],
        'text': comment['text'],
        'status': comment['status'],
        'likes': comment['likes'],
        'liked': cid in user_like_cids,
        'dislikes': comment.get('dislikes', 0),
        'disliked': cid in user_dislike_cids,
        'participate_num': comment['likes'] + comment.get('dislikes', 0),
        'imgs': base_service.build_img_infos(comment.get('raw_imgs', [])),
    }

    # 作者信息
    if user_map.get(comment['uid']):
        user_info = user_map[comment['uid']]
        result['user'] = user_service.build_user_info_by_favor(user_info, viewer_favor_info=viewer_favor_info)

    return result


async def increase_comment_count_stat(cid, likes_inc_num=0, dislikes_inc_num=0):
    """
    修改post的计数字段
    :param cid:
    :param likes_inc_num: 点赞新增数
    :param dislikes_inc_num: 点踩新增数
    :param need_calc_rec_score: 是否重新计算热度值
    :return:
    """
    comment_col = db.get_motordb_col_comment()

    # 新增计数
    inc_dict = {}
    if likes_inc_num:
        inc_dict['likes'] = likes_inc_num
    if dislikes_inc_num:
        inc_dict['dislikes'] = dislikes_inc_num

    # 更新修改时间
    set_dict = {'ut': int(time.time())}

    # 保存修改数据
    update_dict = {}
    if inc_dict:
        update_dict['$inc'] = inc_dict
    if set_dict:
        update_dict['$set'] = set_dict
    if not update_dict:
        return cid

    # 修改计数
    await mongo_async.mongo_find_one_and_update(comment_col, {'_id': ObjectId(cid)}, update_dict, upsert=False, return_document=True)
    return cid


