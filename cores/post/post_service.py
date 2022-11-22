# -*- coding:utf-8 -*-
"""
post service 方法
"""
import time
from bson import ObjectId
from pymongo import UpdateOne

from cores.const import const_post, const_tag, const_base
from cores.database import db, mongo_async
from cores.tag import tag_service
from cores.base import base_service
from cores.user import user_service


def build_post_query_dict(pid=None, ptype=None, status=None, uid=None, tid=None, ct_gte=0, ct_lt=0):
    """
    构造帖子的查询dict
    :return:
    """
    query_dict = {}
    if pid is not None:
        query_dict['_id'] = {}
        if isinstance(pid, const_base.LIST_TYPES):
            query_dict['_id']['$in'] = base_service.ensure_mongo_obj_ids(pid)
        if isinstance(pid, ObjectId):
            query_dict['_id'] = pid
        if isinstance(pid, str):
            query_dict['_id'] = ObjectId(pid)

    if uid is not None:
        query_dict['uid'] = {}
        if isinstance(uid, const_base.LIST_TYPES):
            query_dict['uid']['$in'] = base_service.ensure_mongo_str_ids(uid)
        if isinstance(uid, ObjectId):
            query_dict['uid'] = str(uid)
        if isinstance(uid, str):
            query_dict['uid'] = uid

    if ptype is not None:
        query_dict['ptype'] = ptype
        if isinstance(ptype, const_base.LIST_TYPES):
            query_dict['ptype'] = {'$in': ptype}

    if status is not None:
        query_dict['status'] = status
        if isinstance(status, const_base.LIST_TYPES):
            query_dict['status'] = {'$in': status}

    if tid is not None:
        query_dict['tids'] = tid
        if isinstance(tid, const_base.LIST_TYPES):
            query_dict['tids']['$in'] = tid

    if ct_gte or ct_lt:
        query_dict['ct'] = {}
        if ct_gte:
            query_dict['ct']['$gte'] = ct_gte
        if ct_lt:
            query_dict['ct']['$lt'] = ct_lt

    return query_dict


async def get_post_map_by_pids(pids):
    """
    批量获取帖子信息映射表
    :return:
    """
    if not pids:
        return {}

    result = {}
    post_col = db.get_motordb_col_post()
    post_list = await mongo_async.mongo_find(post_col, {'_id': {'$in': base_service.ensure_mongo_obj_ids(pids)}})
    for post in post_list:
        result[str(post['_id'])] = post
    return result


async def get_post_by_id(pid):
    """
    根据帖子ID获取帖子
    :param pid:
    :return:
    """
    if not pid:
        return {}

    post_map = await get_post_map_by_pids([pid])
    if not post_map:
        return
    return post_map.get(pid, {})


def build_post_query_sort(query_sort_type=None):
    """
    构造排序信息
    :return:
    """
    sorts = [('ct', -1)]
    if query_sort_type == const_post.POST_QUERY_SORT_T_NEW:
        sorts = [('ct', -1)]
    elif query_sort_type == const_post.POST_QUERY_SORT_T_HOT:
        sorts = [('rec_score', -1)]
    return sorts


async def get_post_info_list_for_handler(uid, cursor_info, query_dict=None, sorts=None, favor_info=None):

    """
    获取帖子列表信息
    :return:
    """
    # 确保分页合法
    offset = cursor_info.get('offset', 0)
    offset = offset if offset >= 0 else 0
    limit = cursor_info.get('limit', const_post.POST_PAGE_PER_NUM)
    limit = min(const_post.POST_PAGE_PER_NUM_MAX, limit)

    # 获取数据
    post_col = db.get_motordb_col_post()
    posts = await mongo_async.mongo_find_sort_skip_limit(post_col, query_dict, sorts, offset, limit + 1)
    has_more = bool(len(posts) > limit)
    posts = posts[:limit]
    if not posts:
        return False, {}, []

    # 查询作者ID映射表
    uids = [post['uid'] for post in posts]
    uids.append(uid)
    user_map = await user_service.get_user_map_by_uids(uids)

    # 查询标签ID映射表
    tids = []
    for post in posts:
        tids.extend(post.get('tids', []))
    tag_map = await tag_service.get_tag_map_by_tids(tids)

    # 构造赞踩列表
    from cores.favor import favor_service
    pids = [str(post['_id']) for post in posts]
    like_pids, disliked_pids = await favor_service.get_user_liked_disliked_pids(uid, pids)

    # 构造返回列表
    results = []
    for post in posts:
        results.append(
            build_post_info(post, tag_map, user_map, viewer_favor_info=favor_info, like_pids=like_pids, disliked_pids=disliked_pids)
        )

    # 下一次分页信息
    next_cursor_info = {
        'offset': offset + limit,
        'limit': limit,
    }

    return has_more, next_cursor_info, results


def build_post_info(post, tag_map, user_map, viewer_favor_info=None, like_pids=None, disliked_pids=None):
    """
    构造推荐帖子信息
    :return:
    """
    pid = str(post['_id'])
    result = {
        'pid': pid,
        'ptype': post['ptype'],
        'ct': post['ct'],
        'ut': post['ut'],
        'rt': post['ct'],
        'status': int(post['status']),
        'cmts': post['cmts'],
        'likes': post['likes'],
        'liked': pid in (like_pids or []),
        'dislikes': post['dislikes'],
        'disliked': pid in (disliked_pids or []),
        'title': post.get('title', ''),
        'text': post['text'],
        'imgs': base_service.build_img_infos(post['raw_imgs']),
        'tags': [],
        'articles': build_post_article_items(post['raw_articles']),
        'user': user_service.build_user_info_by_favor(user_map.get(post['uid']), viewer_favor_info=viewer_favor_info),
    }

    # 标签
    for tid in post['tids']:
        if not tag_map.get(tid) or tag_map[tid]['status'] <= const_tag.TAG_STATUS_INVISIBLE:
            continue
        result['tags'].append(tag_service.build_tag_info_by_favor(tag_map[tid], viewer_favor=viewer_favor_info))

    return result


def build_post_article_items(article_items):
    """
    构造article items列表
    """
    if not article_items:
        return []
    results = []
    for article_item in article_items:
        item = article_item
        if article_item['type'] in [const_post.POST_ARTICLE_TYPE_IMAGE, const_post.POST_ARTICLE_TYPE_GIF, const_post.POST_ARTICLE_TYPE_GIF_VIDEO]:
            item = base_service.build_img_infos_item(article_item)
        results.append(item)
    return results


async def get_post_detail_for_handler(pid, viewer_uid, check_deleted=True):
    """
    获取 帖子 详情展示信息
    :return:
    """

    # 获取帖子信息
    post = await get_post_by_id(pid)
    if not post:
        return {}

    # 已经删除则直接返回简单字段
    if check_deleted and post['status'] in [const_post.POST_STATUS_INVISIBLE, const_post.POST_STATUS_SELF_DELETE]:
        return build_post_info(post, {}, {})

    # 最近10个用户数据，优先包含自己。
    from cores.favor import favor_service
    like_uids = await favor_service.query_post_current_like_uids(pid, 10, viewer_uid)

    # 查询用户ID映射表
    uids = [post['uid'], viewer_uid]
    uids.extend(like_uids)
    user_map = await user_service.get_user_map_by_uids(uids)

    # 用户喜好映射表
    favor_map = await favor_service.get_favor_map_by_ids([post['uid'], viewer_uid])

    # 查询标签ID映射表
    tids = post.get('tids', [])
    tag_map = await tag_service.get_tag_map_by_tids(tids)

    # 构造赞踩列表
    like_pids, disliked_pids = await favor_service.get_user_liked_disliked_pids(viewer_uid, [pid])

    # 返回结果数据
    viewer_favor = favor_map.get(viewer_uid, {})
    post_user_favor = favor_map.get(post['uid'], {})
    result = build_post_info(post, tag_map, user_map, viewer_favor_info=viewer_favor, like_pids=like_pids, disliked_pids=disliked_pids)
    # 作者信息
    result['user'] = user_service.build_user_info_by_favor(user_map.get(post['uid']), viewer_favor_info=viewer_favor, user_favor_info=post_user_favor)

    # 点赞用户列表
    result['crt_liked_users'] = [user_service.build_user_base_info(user_map[uid]) for uid in like_uids if user_map.get(uid)]

    return result


async def create_new_post(uid, text, post_type, cmts=0, likes=0, status='', ct=None, extra_info=None,
                          raw_imgs=None, title=None, raw_articles=None, tids=None):
    """
    创建新帖
    :param uid:
    :param title:
    :param text:
    :param post_type: 帖子类型
    :param cmts: 评论数目
    :param likes: 点赞数
    :param status: 状态
    :param ct: 指定创建时间
    :param extra_info: 外部自定义字段
    :return:
    """

    # 创建新帖
    post_col = db.get_motordb_col_post()
    ct = ct or int(time.time())
    status = status or const_post.POST_STATUS_VISIBLE
    title = title or ''
    new_post = {
        'uid': uid,
        'title': title.strip(),
        'text': text.strip(),
        'raw_imgs': raw_imgs or [],
        'ptype': post_type,
        'status': status,
        'ut': ct,
        'ct': ct,

        'cmts': cmts,                   # 评论数
        'likes': likes,                 # 点赞数
        'dislikes': 0,                  # 踩赞数

        'tids': tids or [],
        'raw_articles': raw_articles or [],
    }
    if extra_info:
        new_post.update(extra_info)

    # 插入帖子
    pid = await mongo_async.mongo_insert_one(post_col, new_post, returnid=True)
    if not pid:
        return "", {}

    if status >= const_post.POST_STATUS_VISIBLE:
        # 更新话题下发帖数计数
        if new_post['tids'] and isinstance(new_post['tids'], const_base.LIST_TYPES):
            await tag_service.increase_tag_count_stat(tid_or_tids=new_post['tids'], post_num_inc_num=1)

        # 更新个人的发帖总数
        from cores.favor import favor_service
        await favor_service.increase_favor_count_stat(uid, post_num_inc_num=1)

    pid = str(pid) if pid else ''
    new_post['_id'] = ObjectId(pid)

    return pid, new_post


async def delete_user_post_for_handler(p_uid, pid):
    """
    用户删除帖子
    :param p_uid: 帖子作者
    :param pid: 帖子ID
    :return:
    """
    # 删除帖子并获取之前状态
    post_col = db.get_motordb_col_post()
    query_dict = build_post_query_dict(uid=p_uid, pid=pid)
    before_post = await mongo_async.mongo_find_one_and_update(
        post_col, query_dict, {'$set': {'status': const_post.POST_STATUS_SELF_DELETE}}, upsert=False, return_document=False)

    # 如果不存在, 或之前已经删除了则直接返回
    if not before_post or before_post['status'] == const_post.POST_STATUS_SELF_DELETE:
        return

    # 更改用户发出的帖子数目-1
    from cores.favor import favor_service
    await favor_service.increase_favor_count_stat(p_uid, post_num_inc_num=-1)

    # 重置tag下的最新pid, 并更新缓存
    await tag_service.increase_tag_count_stat(before_post.get('tids', []), post_num_inc_num=-1)


async def increase_post_count_stat(pid, cmt_inc_num=0, likes_inc_num=0,
                                   dislikes_inc_num=0, collects_inc_num=0,
                                   reproduces_inc_num=0, shares_inc_num=0, view_inc_num=0):
    """
    修改post的计数字段
    :return:
    """
    post_col = db.get_motordb_col_post()

    # 新增计数
    inc_dict = {}
    if cmt_inc_num:
        inc_dict['cmts'] = cmt_inc_num
    if likes_inc_num:
        inc_dict['likes'] = likes_inc_num
    if dislikes_inc_num:
        inc_dict['dislikes'] = dislikes_inc_num
    if collects_inc_num:
        inc_dict['collects'] = collects_inc_num
    if reproduces_inc_num:
        inc_dict['reproduces'] = reproduces_inc_num
    if shares_inc_num:
        inc_dict['shares'] = shares_inc_num
    if view_inc_num:
        inc_dict['view_num'] = view_inc_num

    # 更新修改时间
    set_dict = {'ut': int(time.time())}

    # 保存修改数据
    update_dict = {}
    if inc_dict:
        update_dict['$inc'] = inc_dict
    if set_dict:
        update_dict['$set'] = set_dict

    if not update_dict:
        return

    # 更新计数
    query_dict = {'_id': pid}
    if isinstance(pid, str):
        query_dict['_id'] = ObjectId(pid)
    await mongo_async.mongo_update_one(post_col, query_dict, update_dict, up=False)


async def get_recommend_post_info_list_for_handler_v1(uid, favor_info=None):
    """
    推荐流数据
    :return:
    """
    # 获取最近用户浏览的推荐pids
    his_query_dict = {
        "uid": uid,
    }
    his_sorts = [('ct', -1)]
    col_post_recommend_history = db.get_motordb_col_post_recommend_history()
    history_list = await mongo_async.mongo_find_sort_skip_limit(col_post_recommend_history, his_query_dict, his_sorts, 0, 1000)
    history_pids_set = set([his['pid'] for his in history_list])

    # 获取最近上推荐的pids
    recommend_query_dict = {
        'status': const_post.POST_STATUS_REC,
    }
    recommend_sorts = [('rt', -1)]
    col_post = db.get_motordb_col_post()
    projection = {'_id': True}
    recommend_post_list = await mongo_async.mongo_find_sort_skip_limit(col_post, recommend_query_dict, recommend_sorts, 0, 1000, projection)
    recommend_pids_list = [str(post['_id']) for post in recommend_post_list]

    # 过滤已浏览pid
    recommend_pids_list = list(filter(lambda pid: pid not in history_pids_set, recommend_pids_list))

    # 获取帖子信息
    recommend_num = 5
    query_dict = build_post_query_dict(pid=recommend_pids_list[:recommend_num])
    cursor_info = {'offset': 0, 'limit': recommend_num}
    _, _, posts = await get_post_info_list_for_handler(uid, cursor_info, query_dict=query_dict, sorts=None, favor_info=favor_info)
    return posts


async def record_recommend_post_history(uid, pids):
    """
    保存帖子推荐历史
    :return:
    """
    if not pids:
        return

    ct = int(time.time())
    post_rec_his_col = db.get_motordb_col_post_recommend_history()
    updates = []
    for pid in pids:
        # 记录数据库
        query_dict = {
            'uid': uid,
            'pid': pid,
        }
        new_his = {
            'uid': uid,
            'pid': pid,
            'ct': ct,
        }
        updates.append(UpdateOne(
            query_dict,
            {'$set': new_his},
            upsert=True
        ))

    await post_rec_his_col.bulk_write(updates, ordered=False)


async def get_history_recommend_post_info_list_for_handler(uid, favor_info=None):
    """
    历史推荐流数据
    :return:
    """
    # 获取最近用户浏览的推荐pids
    his_query_dict = {
        "uid": uid,
    }
    his_sorts = [('ct', -1)]
    col_post_recommend_history = db.get_motordb_col_post_recommend_history()
    history_list = await mongo_async.mongo_find_sort_skip_limit(col_post_recommend_history, his_query_dict, his_sorts, 0, 10)
    history_pids_set = set([his['pid'] for his in history_list])

    # 获取帖子信息
    recommend_num = 5
    query_dict = build_post_query_dict(pid=history_pids_set)
    cursor_info = {'offset': 0, 'limit': recommend_num}
    _, _, posts = await get_post_info_list_for_handler(uid, cursor_info, query_dict=query_dict, sorts=None, favor_info=favor_info)
    return posts


async def update_post_tags_for_handler(pid, new_tids):
    """
    更新帖子的标签信息
    :param new_tids: 帖子的新tid列表
    :return:
    """
    # 获取post信息
    if not (pid and new_tids is not None):
        return False

    # 更新帖子标签
    post_col = db.get_motordb_col_post()
    await mongo_async.mongo_update_one(post_col, {'_id': ObjectId(pid)}, {'$set': {'tids': new_tids}})


async def update_post_status_for_handler(pid, new_status):
    """
    更新帖子的标签信息
    :param new_status: 帖子的新状态
    :return:
    """
    # 获取post信息
    if not (pid and new_status is not None):
        return False

    # 更新帖子标签
    post_col = db.get_motordb_col_post()
    await mongo_async.mongo_update_one(post_col, {'_id': ObjectId(pid)}, {'$set': {'status': new_status}})


