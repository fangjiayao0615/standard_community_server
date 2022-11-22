# -*- coding:utf-8 -*-
"""
favor service 方法
"""
import copy
import time

from bson import ObjectId

from cores.const import const_mix, const_base
from cores.database import db, mongo_async
from cores.tag import tag_service
from cores.base import base_service
from cores.user import user_service
from cores.comment import comment_service
from cores.post import post_service


async def initial_user_favor_info(uid):
    """
    初始化或更新用户喜好信息
    :return:
    """
    if not uid:
        return {}

    now_ts = int(time.time())
    favor_col = db.get_motordb_col_favor()
    init_set_dict = {
        'uid': uid,
        'f_tids': [],       # 已关注 tag_id 列表
        'f_uids': [],       # 已关注 user_id 列表
        'fans_num': 0,      # 粉丝数
        'post_num': 0,      # 帖子数
        'comment_num': 0,   # 评论数
        'ct': now_ts,
        'ut': now_ts,
    }

    update_dict = {'$setOnInsert': init_set_dict}

    favor = await mongo_async.mongo_find_one_and_update(favor_col, {'_id': ObjectId(uid)}, update_dict, upsert=True, return_document=True)
    return favor


async def get_user_liked_disliked_oids(uid, oids, otype):
    """
    获取用户赞踩关系
    :return:
    """
    query_dict = {
        'from_uid': uid,
        'oid': {
            '$in': oids,
        },
        'otype': otype,
    }
    like_his_col = db.get_motordb_col_like_history()
    like_hiss = await mongo_async.mongo_find(like_his_col, query_dict)

    like_cids, disliked_cids = [], []
    for like_his in like_hiss:
        if like_his['action'] == const_mix.F_ACTION_TYPE_LIKE:
            like_cids.append(like_his['oid'])
        elif like_his['action'] == const_mix.F_ACTION_TYPE_DISLIKE:
            disliked_cids.append(like_his['oid'])

    return like_cids, disliked_cids


async def get_user_liked_disliked_pids(uid, pids):
    """
    获取用户对于帖子ID列表的赞踩关系
    :return:
    """
    like_cids, disliked_cids = await get_user_liked_disliked_oids(uid, pids, const_mix.CONTENT_TYPE_POST_CODE)
    return like_cids, disliked_cids


async def increase_favor_count_stat(uid, post_num_inc_num=0, comment_num_inc_num=0, fans_num_inc_num=0):
    """
    修改tag的计数字段
    :param uid: 用户ID
    :param post_num_inc_num: 发帖新增数
    :param comment_num_inc_num: 发评论新增数
    :param fans_num_inc_num: 粉丝新增数
    :return:
    """

    # 新增计数
    inc_dict = {}
    if post_num_inc_num:
        inc_dict['post_num'] = post_num_inc_num

    if comment_num_inc_num:
        inc_dict['comment_num'] = comment_num_inc_num

    if fans_num_inc_num:
        inc_dict['fans_num'] = fans_num_inc_num

    # 更新修改时间
    set_dict = {'ut': int(time.time())}

    # 保存修改数据
    update_dict = {}
    if inc_dict:
        update_dict['$inc'] = inc_dict
    if set_dict:
        update_dict['$set'] = set_dict

    if update_dict:
        favor_col = db.get_motordb_col_favor()
        await mongo_async.mongo_update_one(favor_col, {'_id': ObjectId(uid)}, update_dict)

    return uid


async def get_user_liked_disliked_cids(uid, cids):
    """
    获取用户对于评论ID列表的赞踩关系
    :return:
    """
    like_cids, disliked_cids = await get_user_liked_disliked_oids(uid, cids, const_mix.CONTENT_TYPE_COMMENT_CODE)
    return set(like_cids), set(disliked_cids)


async def user_follow_user(current_uid, new_uid):
    """
    关注新用户
    :return:
    """

    favor_col = db.get_motordb_col_favor()
    update_dict = {
        '$addToSet': {
            'f_uids': new_uid
        },
        '$set': {
            'ut': int(time.time()),
        }
    }
    old_favor = await mongo_async.mongo_find_one_and_update(favor_col, {'_id': ObjectId(current_uid)}, update_dict, upsert=False, return_document=False)

    # 重复添加直接返回
    if old_favor and new_uid in old_favor['f_uids']:
        return

    # 增加粉丝数目
    await increase_favor_count_stat(new_uid, fans_num_inc_num=1)

    # 增加粉丝关注历史
    await create_new_fans_history(current_uid, new_uid)


async def create_new_fans_history(from_uid, to_uid):
    """
    创建粉丝关注历史
    :param from_uid:  关注方 uid
    :param to_uid:   被关注方 uid
    :return:
    """
    fan_his_col = db.get_motordb_col_fan_history()

    query_dict = build_fans_history_query_dict(from_uid, to_uid)

    new_fan_his = {
        'from_uid': from_uid,
        'to_uid': to_uid,
        'ct': int(time.time()),
    }

    await mongo_async.mongo_find_one_and_update(fan_his_col, query_dict, {'$setOnInsert': new_fan_his}, upsert=True)


def build_fans_history_query_dict(from_uid='', to_uid=''):
    """
    构造粉丝关注历史查询信息
    :return:
    """
    query_dict = {}
    if from_uid:
        query_dict['from_uid'] = from_uid
    if to_uid:
        query_dict['to_uid'] = to_uid
    return query_dict


async def user_no_follow_user(current_uid, uid):
    """
    取消关注用户
    :return:
    """

    update_dict = {
        '$pull': {
            'f_uids': uid
        },
        '$set': {
            'ut': int(time.time()),
        }
    }
    favor_col = db.get_motordb_col_favor()
    old_favor = await mongo_async.mongo_find_one_and_update(favor_col, {'_id': ObjectId(current_uid)}, update_dict, upsert=False, return_document=False)

    # 重复取消关注直接返回
    if old_favor and uid not in old_favor['f_uids']:
        return

    # 减去粉丝数目
    await increase_favor_count_stat(uid, fans_num_inc_num=-1)

    # 删除粉丝关注历史
    await delete_fans_history(current_uid, uid)


async def delete_fans_history(from_uid, to_uid):
    """
    删除粉丝关注历史
    :param from_uid:  关注方 uid
    :param to_uid:   被关注方 uid
    :return:
    """
    fan_his_col = db.get_motordb_col_fan_history()

    query_dict = build_fans_history_query_dict(from_uid, to_uid)

    await mongo_async.mongo_delete_one(fan_his_col, query_dict)


async def user_follow_tag(current_uid, tid):
    """
    当前用户批量关注一批话题
    :return:
    """

    # 增加关注列表
    update_dict = {
        '$addToSet': {
            'f_tids': tid
        },
        '$set': {
            'ut': int(time.time()),
        }
    }

    favor_col = db.get_motordb_col_favor()
    old_favor = await mongo_async.mongo_find_one_and_update(favor_col, {'_id': ObjectId(current_uid)}, update_dict, upsert=False, return_document=False)

    # 重复关注直接返回
    if old_favor and tid in old_favor['f_tids']:
        return

    # 更新标签关注数目
    await tag_service.increase_tag_count_stat(tid_or_tids=tid, favor_num_inc=1)

    # 创建关注历史
    await create_new_favor_tag_history(tid, current_uid)


async def create_new_favor_tag_history(tid, uid):
    """
    创建用户关注主题历史记录
    :param tid:  话题ID
    :param uid:  用户ID
    :return:
    """
    favor_tag_his_col = db.get_motordb_col_favor_tag_history()

    query_dict = {
        'tid': tid,
        'uid': uid,
    }

    ct = int(time.time())
    new_his = copy.deepcopy(query_dict)
    new_his['ct'] = ct
    new_his['ut'] = ct

    await mongo_async.mongo_find_one_and_update(favor_tag_his_col, query_dict, {'$setOnInsert': new_his}, upsert=True)


async def user_no_follow_tag(current_uid, tid):
    """
    当前用户批量关注一批话题
    :return:
    """

    # 修改帖子ID列表
    update_dict = {
        '$pull': {
            'f_tids': tid
        },
        '$set': {
            'ut': int(time.time()),
        },
    }

    favor_col = db.get_motordb_col_favor()
    old_favor = await mongo_async.mongo_find_one_and_update(favor_col, {'_id': ObjectId(current_uid)}, update_dict, upsert=False, return_document=False)

    # 重复取消直接返回
    if old_favor and tid not in old_favor['f_tids']:
        return

    # 更新标签关注数目
    await tag_service.increase_tag_count_stat(tid_or_tids=tid, favor_num_inc=-1)

    # 删除关注主题关系
    await delete_favor_tag_history(tid, current_uid)


async def delete_favor_tag_history(tid, uid):
    """
    删除用户关注主题历史
    :return:
    """
    favor_tag_his_col = db.get_motordb_col_favor_tag_history()

    query_dict = {
        'tid': tid,
        'uid': uid,
    }

    await mongo_async.mongo_delete_one(favor_tag_his_col, query_dict)


async def increase_user_favor_num_stat(uid, likes_post_to_me_inc_num=0, liked_post_inc_num=0,
                                       likes_cmt_to_me_inc_num=0, liked_cmt_inc_num=0):
    """
    修改获赞的计数字段
    :return:
    """

    # 新增计数
    inc_dict = {}
    if likes_post_to_me_inc_num:
        inc_dict['likes_post_to_me'] = likes_post_to_me_inc_num
    if liked_post_inc_num:
        inc_dict['liked_post_num'] = liked_post_inc_num
    if likes_cmt_to_me_inc_num:
        inc_dict['likes_cmt_to_me'] = likes_cmt_to_me_inc_num
    if liked_cmt_inc_num:
        inc_dict['liked_cmt_num'] = liked_cmt_inc_num

    # 保存修改数据
    update_dict = {}
    if inc_dict:
        update_dict['$inc'] = inc_dict

    if not update_dict:
        return

    # 查询请求
    query_dict = {'_id': ObjectId(uid)}
    favor_col = db.get_motordb_col_favor()
    await mongo_async.mongo_update_one(favor_col, query_dict, update_dict)


async def like_post_for_handler(uid, pid, p_uid):
    """
    帖子点赞
    :return: 
    """
    # 历史点踩记录
    like_pids, disliked_pids = await get_user_liked_disliked_pids(uid, [pid])

    # 新增赞
    if not like_pids:
        # 增加点赞记录
        await update_like_dislike_history(uid, p_uid, pid, const_mix.CONTENT_TYPE_POST_CODE, const_mix.F_ACTION_TYPE_LIKE)
        # 帖子点赞计数
        await post_service.increase_post_count_stat(pid, likes_inc_num=1)
        # 作者获赞计数
        await increase_user_favor_num_stat(p_uid, likes_post_to_me_inc_num=1)
        # 读者点赞计数
        await increase_user_favor_num_stat(uid, liked_post_inc_num=1)

    # 取消踩
    if disliked_pids:
        # 帖子点踩计数
        await post_service.increase_post_count_stat(pid, dislikes_inc_num=-1)
        # 取消点踩记录
        await update_like_dislike_history(uid, p_uid, pid, const_mix.CONTENT_TYPE_POST_CODE, const_mix.F_ACTION_TYPE_CANCEL_DISLIKE)


async def cancel_like_post_for_handler(uid, pid, p_uid):
    """
    帖子取消点赞
    :return: 
    """
    # 历史点踩记录
    like_pids, disliked_pids = await get_user_liked_disliked_pids(uid, [pid])

    # 取消赞
    if like_pids:
        # 删除点赞记录
        await update_like_dislike_history(uid, p_uid, pid, const_mix.CONTENT_TYPE_POST_CODE, const_mix.F_ACTION_TYPE_CANCEL_LIKE)
        # 减少帖子点赞计数
        await post_service.increase_post_count_stat(pid, likes_inc_num=-1)
        # 减少作者获赞计数
        await increase_user_favor_num_stat(p_uid, likes_post_to_me_inc_num=-1)
        # 减少读者点赞计数
        await increase_user_favor_num_stat(uid, liked_post_inc_num=-1)


async def dislike_post_for_handler(uid, pid, p_uid):
    """
    帖子点踩
    :return: 
    """
    # 历史点踩记录
    like_pids, disliked_pids = await get_user_liked_disliked_pids(uid, [pid])

    # 新增踩
    if not disliked_pids:
        # 增加点踩记录
        await post_service.increase_post_count_stat(pid, dislikes_inc_num=1)
        # 增加点踩记录
        await update_like_dislike_history(uid, p_uid, pid, const_mix.CONTENT_TYPE_POST_CODE, const_mix.F_ACTION_TYPE_DISLIKE)

    # 取消赞
    if like_pids:
        # 减少点赞计数
        await post_service.increase_post_count_stat(pid, likes_inc_num=-1)
        # 删除点赞记录
        await update_like_dislike_history(uid, p_uid, pid, const_mix.CONTENT_TYPE_POST_CODE, const_mix.F_ACTION_TYPE_CANCEL_LIKE)
        # 减少作者获赞数
        await increase_user_favor_num_stat(p_uid, likes_post_to_me_inc_num=-1)
        # 减少读者点赞数
        await increase_user_favor_num_stat(uid, liked_post_inc_num=-1)


async def cancel_dislike_post_for_handler(uid, pid, p_uid):
    """
    取消帖子点踩
    :return: 
    """
    # 历史点踩记录
    like_pids, disliked_pids = await get_user_liked_disliked_pids(uid, [pid])

    # 取消点踩
    if disliked_pids:
        # 点踩计数
        await post_service.increase_post_count_stat(pid, dislikes_inc_num=-1)
        # 删除点踩记录
        await update_like_dislike_history(uid, p_uid, pid, const_mix.CONTENT_TYPE_POST_CODE, const_mix.F_ACTION_TYPE_CANCEL_DISLIKE)


async def like_cmt_for_handler(uid, cid, c_uid):
    """
    评论点赞
    :return: 
    """
    like_cids, disliked_cids = await get_user_liked_disliked_cids(uid, [cid])

    # 新增点赞
    if not like_cids:
        # 增加点赞计数
        await comment_service.increase_comment_count_stat(cid, likes_inc_num=1)
        # 增加点赞历史记录
        await update_like_dislike_history(uid, c_uid, cid, const_mix.CONTENT_TYPE_COMMENT_CODE, const_mix.F_ACTION_TYPE_LIKE)
        # 增加作者获赞计数
        await increase_user_favor_num_stat(c_uid, likes_cmt_to_me_inc_num=1)
        # 增加读者点赞计数
        await increase_user_favor_num_stat(uid, liked_cmt_inc_num=1)

    # 取消踩
    if disliked_cids:
        # 减少点踩计数
        await comment_service.increase_comment_count_stat(cid, dislikes_inc_num=-1)
        # 删除点踩历史记录
        await update_like_dislike_history(uid, c_uid, cid, const_mix.CONTENT_TYPE_COMMENT_CODE, const_mix.F_ACTION_TYPE_CANCEL_DISLIKE)


async def cancel_like_cmt_for_handler(uid, cid, c_uid):
    """
    取消评论点赞
    :return: 
    """
    like_cids, disliked_cids = await get_user_liked_disliked_cids(uid, [cid])

    # 取消点赞
    if like_cids:
        # 减少点赞计数
        await comment_service.increase_comment_count_stat(cid, likes_inc_num=-1)
        # 删除点赞历史记录
        await update_like_dislike_history(uid, c_uid, cid, const_mix.CONTENT_TYPE_COMMENT_CODE, const_mix.F_ACTION_TYPE_CANCEL_LIKE)
        # 减少作者获赞计数
        await increase_user_favor_num_stat(c_uid, likes_cmt_to_me_inc_num=-1)
        # 减少读者点赞计数
        await increase_user_favor_num_stat(uid, liked_cmt_inc_num=-1)


async def dislike_cmt_for_handler(uid, cid, c_uid):
    """
    评论点踩
    :return: 
    """
    like_cids, disliked_cids = await get_user_liked_disliked_cids(uid, [cid])

    # 评论点踩
    if not disliked_cids:
        # 增加点踩计数
        await comment_service.increase_comment_count_stat(cid, dislikes_inc_num=1)
        # 增加点踩历史记录
        await update_like_dislike_history(uid, c_uid, cid, const_mix.CONTENT_TYPE_COMMENT_CODE, const_mix.F_ACTION_TYPE_DISLIKE)

    # 取消点赞
    if like_cids:
        # 减少点赞计数
        await comment_service.increase_comment_count_stat(cid, likes_inc_num=-1)
        # 删除点赞历史记录
        await update_like_dislike_history(uid, c_uid, cid, const_mix.CONTENT_TYPE_COMMENT_CODE, const_mix.F_ACTION_TYPE_CANCEL_LIKE)
        # 减少作者获赞计数
        await increase_user_favor_num_stat(c_uid, likes_cmt_to_me_inc_num=-1)
        # 减少读者点赞计数
        await increase_user_favor_num_stat(uid, liked_cmt_inc_num=-1)


async def cancel_dislike_cmt_for_handler(uid, cid, c_uid):
    """
    取消点踩
    :param uid: 
    :param cid: 
    :param c_uid: 
    :return: 
    """
    like_cids, disliked_cids = await get_user_liked_disliked_cids(uid, [cid])

    # 取消点踩
    if disliked_cids:
        # 减少点踩计数
        await comment_service.increase_comment_count_stat(cid, dislikes_inc_num=-1)
        # 删除点踩历史记录
        await update_like_dislike_history(uid, c_uid, cid, const_mix.CONTENT_TYPE_COMMENT_CODE, const_mix.F_ACTION_TYPE_CANCEL_DISLIKE)


async def update_like_dislike_history(from_uid, to_uid, obj_id, obj_type, action):
    """
    更新赞我的相关缓存和历史记录
    :param from_uid: 赞的发出者
    :param to_uid: 赞的接收者
    :param obj_id: UGC id
    :param obj_type: UGC 类型
    :param action: 点赞动作 1 赞  2 取消赞
    :return:
    """

    # 新增赞
    if action == const_mix.F_ACTION_TYPE_LIKE:
        await create_new_like_history(from_uid, to_uid, obj_id, obj_type, const_mix.F_ACTION_TYPE_LIKE)

    # 取消赞
    elif action == const_mix.F_ACTION_TYPE_CANCEL_LIKE:
        # 删除历史记录
        await delete_like_history(from_uid, to_uid, obj_id, obj_type, const_mix.F_ACTION_TYPE_LIKE)

    # 新增踩
    elif action == const_mix.F_ACTION_TYPE_DISLIKE:
        await create_new_like_history(from_uid, to_uid, obj_id, obj_type, const_mix.F_ACTION_TYPE_DISLIKE)

    # 取消踩
    elif action == const_mix.F_ACTION_TYPE_CANCEL_DISLIKE:
        await delete_like_history(from_uid, to_uid, obj_id, obj_type, const_mix.F_ACTION_TYPE_DISLIKE)


async def create_new_like_history(from_uid, to_uid, obj_id, obj_type, action):
    """
    创建点赞历史记录
    :param from_uid:  发赞方 uid
    :param to_uid:   被赞方 uid
    :param obj_id: UGC id
    :param obj_type: UGC type
    :param action: 动作
    :return:
    """
    like_his_col = db.get_motordb_col_like_history()

    query_dict = build_like_history_query_dict(from_uid, to_uid, obj_id, obj_type, action=action)

    new_like_his = {
        'from_uid': from_uid,
        'to_uid': to_uid,
        'oid': obj_id,
        'otype': obj_type,
        'action': action,
        'ct': int(time.time()),
    }
    await mongo_async.mongo_find_one_and_update(like_his_col, query_dict, {'$setOnInsert': new_like_his}, upsert=True)


def build_like_history_query_dict(from_uid='', to_uid='', obj_id='', obj_type='', ct_lt=0, not_from_uid='', action=None):
    """
    构造点赞历史查询信息
    :return:
    """
    query_dict = {}
    if from_uid or not_from_uid:
        query_dict['from_uid'] = {}
        if from_uid:
            query_dict['from_uid']['$in'] = [from_uid]
        if not_from_uid:
            query_dict['from_uid']['$nin'] = [not_from_uid]

    if to_uid:
        query_dict['to_uid'] = to_uid
    if obj_id:
        query_dict['oid'] = obj_id
    if obj_type:
        query_dict['otype'] = obj_type
        if isinstance(obj_type, const_base.LIST_TYPES):
            query_dict['otype'] = {'$in': list(obj_type)}
    if ct_lt:
        query_dict['ct'] = {'$lt': ct_lt}

    if action:
        query_dict['action'] = action
        if isinstance(action, const_base.LIST_TYPES):
            query_dict['action'] = {'$in': list(action)}
    return query_dict


async def delete_like_history(from_uid, to_uid, obj_id, obj_type, action):
    """
    删除点赞历史
    :return:
    """
    like_his_col = db.get_motordb_col_like_history()
    query_dict = build_like_history_query_dict(from_uid, to_uid, obj_id, obj_type, action=action)
    await mongo_async.mongo_delete_one(like_his_col, query_dict)


async def query_post_current_like_uids(pid, need_num=10, viewer_uid=''):
    """
    查询当前点赞帖子的用户ID列表
    :return:
    """
    if not pid:
        return []

    # 其他用户列表
    query_dict = build_like_history_query_dict(obj_id=pid, obj_type=const_mix.CONTENT_TYPE_POST_CODE, not_from_uid=viewer_uid, action=const_mix.F_ACTION_TYPE_LIKE)
    his_col = db.get_motordb_col_like_history()
    hiss = await mongo_async.mongo_find_sort_skip_limit(his_col, query_dict, [('contribute_score', -1), ('ct', -1)], 0, need_num)
    result = [his['from_uid'] for his in hiss]

    # 查看用户已关注优先展示
    query_dict = build_like_history_query_dict(from_uid=viewer_uid, obj_id=pid, obj_type=const_mix.CONTENT_TYPE_POST_CODE, action=const_mix.F_ACTION_TYPE_LIKE)
    viewer_like_his = await mongo_async.mongo_find_one(his_col, query_dict)
    if viewer_like_his:
        result.insert(0, viewer_uid)

    return result


async def get_favor_map_by_ids(uids):
    """
    获取关注信息映射表
    :param uids:
    :return:
    """
    favor_col = db.get_motordb_col_favor()
    favors = await mongo_async.mongo_find(favor_col, {'_id': {'$in': base_service.ensure_mongo_obj_ids(uids)}})

    result = {}
    for favor in favors:
        result[favor['uid']] = favor
    return result


async def get_user_favor(uid):
    """
    获取用户喜好信息表
    :return:
    """
    favor_col = db.get_motordb_col_favor()
    favor = await mongo_async.mongo_find_one(favor_col, {'_id': ObjectId(uid)})
    return favor or {}


async def update_user_last_read_notice_ct(uid, last_read_notice_ct):
    """
    重置最后阅读的通知时间
    :param uid:
    :param last_read_notice_ct:
    :return:
    """
    favor_col = db.get_motordb_col_favor()
    await mongo_async.mongo_update_one(favor_col, {'_id': ObjectId(uid)}, {'$set': {'last_read_notice_ct': last_read_notice_ct}})


async def get_like_history_info_list_for_handler(uid, cursor_info, query_dict, sorts):
    """
    获取点赞踩历史信息
    :return: 
    """
    # 确保分页合法
    offset = cursor_info.get('offset', 0)
    offset = offset if offset >= 0 else 0
    limit = cursor_info.get('limit', const_mix.HISTORY_PAGE_PER_NUM)
    limit = min(const_mix.HISTORY_PAGE_PER_NUM_MAX, limit)

    # 获取数据
    his_col = db.get_motordb_col_like_history()
    hiss = await mongo_async.mongo_find_sort_skip_limit(his_col, query_dict, sorts, offset, limit + 1)
    has_more = bool(len(hiss) > limit)
    hiss = hiss[:limit]
    if not hiss:
        return False, {}, []

    # 查询评论映射表
    cids = [his['oid'] for his in hiss if his['otype'] == const_mix.CONTENT_TYPE_COMMENT_CODE]
    cmt_map = await comment_service.get_comment_info_map_by_cids(cids)

    # 查询帖子映射表
    pids = [his['oid'] for his in hiss if his['otype'] == const_mix.CONTENT_TYPE_POST_CODE]
    pids.extend([cmt['pid'] for _, cmt in cmt_map.items()])
    post_map = await post_service.get_post_map_by_pids(pids)

    # 用户映射表
    uids = [uid]
    uids.extend([his['from_uid'] for his in hiss])
    uids.extend([his['to_uid'] for his in hiss])
    user_map = await user_service.get_user_map_by_uids(uids)

    # 构造返回列表
    results = []
    for his in hiss:
        results.append(
            build_like_history_info(his, post_map=post_map, cmt_map=cmt_map, user_map=user_map)
        )

    # 下一次分页信息
    next_cursor_info = {
        'offset': offset + limit,
        'limit': limit,
    }
    return has_more, next_cursor_info, results


def build_like_history_info(his, post_map=None, cmt_map=None, user_map=None):
    """
    构造赞踩历史信息
    :return:
    """
    result = {
        'hid': str(his['_id']),
        'from_uid': his['from_uid'],
        'to_uid': his['to_uid'],
        'oid': his['oid'],
        'otype': his['otype'],
        'action': his['action'],
        'ct': his['ct'],
    }
    # 用户信息
    if his['from_uid'] in user_map:
        result['from_user_info'] = user_service.build_user_base_info(user_map[his['from_uid']])
    if his['to_uid'] in user_map:
        result['to_user_info'] = user_service.build_user_base_info(user_map[his['to_uid']])
    # 帖子快照
    if result['otype'] == const_mix.CONTENT_TYPE_POST_CODE and result['oid'] in post_map:
        result['post'] = post_service.build_post_info(post_map[result['oid']], {}, {})
    # 评论快照+帖子
    if result['otype'] == const_mix.CONTENT_TYPE_COMMENT_CODE and result['oid'] in cmt_map:
        cmt = cmt_map[result['oid']]
        result['comment'] = comment_service.build_comment_base_info(cmt, {}, [], [])
        if cmt['pid'] in post_map:
            result['post'] = post_service.build_post_info(post_map[cmt['pid']], {}, {})

    return result


async def get_fans_history_info_list_for_handler(uid, cursor_info, query_dict, sorts):
    """
    获取点赞踩历史信息
    :return: 
    """
    # 确保分页合法
    offset = cursor_info.get('offset', 0)
    offset = offset if offset >= 0 else 0
    limit = cursor_info.get('limit', const_mix.HISTORY_PAGE_PER_NUM)
    limit = min(const_mix.HISTORY_PAGE_PER_NUM_MAX, limit)

    # 获取数据
    his_col = db.get_motordb_col_fan_history()
    hiss = await mongo_async.mongo_find_sort_skip_limit(his_col, query_dict, sorts, offset, limit + 1)
    has_more = bool(len(hiss) > limit)
    hiss = hiss[:limit]
    if not hiss:
        return False, {}, []

    # 用户映射表
    uids = [uid]
    uids.extend([his['from_uid'] for his in hiss])
    uids.extend([his['to_uid'] for his in hiss])
    user_map = await user_service.get_user_map_by_uids(uids)

    # 构造返回列表
    results = []
    for his in hiss:
        results.append(
            build_fans_history_info(his, user_map=user_map)
        )

    # 下一次分页信息
    next_cursor_info = {
        'offset': offset + limit,
        'limit': limit,
    }
    return has_more, next_cursor_info, results


def build_fans_history_info(his, user_map=None):
    """
    构造赞踩历史信息
    :return:
    """
    result = {
        'fid': str(his['_id']),
        'from_uid': his['from_uid'],
        'to_uid': his['to_uid'],
        'ct': his['ct'],
    }
    # 用户信息
    if his['from_uid'] in user_map:
        result['from_user_info'] = user_service.build_user_base_info(user_map[his['from_uid']])
    if his['to_uid'] in user_map:
        result['to_user_info'] = user_service.build_user_base_info(user_map[his['to_uid']])
    return result

