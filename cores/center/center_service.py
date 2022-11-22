# -*- coding:utf-8 -*-
"""
用户中心 service 方法
"""
import time

from bson import ObjectId

from cores.const import const_mix, const_base
from cores.database import mongo_async, db
from cores.favor import favor_service
from cores.user import user_service
from cores.utils.badge import BasicBadgeManager

# 粉我的新增缓存
NEW_FANS_TO_ME_NUM = 150
NEW_FANS_TO_ME_KEY = 'user(%s)_new_fans_to_me'
new_fans_to_me_badge = BasicBadgeManager(NEW_FANS_TO_ME_KEY, expire_time=60*60*24*7)

# 赞我的新增缓存
NEW_LIKE_TO_ME_MAX_NUM = 200
NEW_LIKE_TO_ME_KEY = 'user(%s)_new_like_to_me'
new_like_to_me_badge = BasicBadgeManager(NEW_LIKE_TO_ME_KEY, expire_time=60*60*24*7)


# 评论我的新增缓存
NEW_COMMENT_TO_ME_NUM = 200
NEW_COMMENT_TO_ME_KEY = 'user(%s)_new_comment_to_me'
new_comment_to_me_badge = BasicBadgeManager(NEW_COMMENT_TO_ME_KEY, expire_time=60*60*24*7)


def build_comment_to_me_badge_item(uid, oid, otype):
    """
    构造评论我的新增统计用的元数据
    :param uid: 新评论的作者
    :param oid: 新评论所属上级的pid或cid
    :param otype: 上级数据UGC类型
    :return:
    """
    return '%s##%s##%s' % (uid, oid, otype)


def build_user_home_page_for_handler(dst_favor, dst_user, my_favor):
    """
    构造查看的其他用户主页信息
    :return:
    """
    result = user_service.build_user_info_by_favor(dst_user, need_passwd=False, viewer_favor_info=my_favor, user_favor_info=dst_favor)

    # 该用户关注的其他用户数量
    result['f_user_num'] = len(dst_favor['f_uids'])

    # 该用户关注的主题数量
    result['f_tag_num'] = len(dst_favor['f_tids'])

    # 该用户粉丝数量
    result['fans_num'] = dst_favor.get('fans_num', 0)
    if result['fans_num'] < 0:
        result['fans_num'] = 0

    return result


async def build_my_home_page_for_handler(my_favor, raw_user):
    """
    构造自己的其他用户主页信息, 注意：后续不再添加badge相关提示，统一在小红点管理方法中添加 get_user_badges
    :return:
    """

    # 基础信息
    result = build_user_home_page_for_handler(my_favor, raw_user, my_favor)

    # 发帖、评论数目
    result['post_num'] = my_favor.get('post_num', 0)
    result['comment_num'] = my_favor.get('comment_num', 0)

    # 我赞别人内容的总数
    result['liked_post_num'] = my_favor.get('liked_post_num', 0)
    result['liked_cmt_num'] = my_favor.get('liked_cmt_num', 0)

    # 我的内容获赞总数
    result['likes_post_to_me'] = my_favor.get('likes_post_to_me', 0)
    result['likes_cmt_to_me'] = my_favor.get('likes_cmt_to_me', 0)

    # 赞我的新增数目
    result['new_likes_to_me'] = new_like_to_me_badge.get_badge_num(result['uid'])

    # 评论我的新增数目
    result['new_cmt_to_me'] = new_comment_to_me_badge.get_badge_num(result['uid'])

    # 新增粉丝数目
    result['new_fans_to_me'] = new_fans_to_me_badge.get_badge_num(result['uid'])

    return result


async def get_user_badges(uid):
    """
    获取用户的所有小红点标识
    """
    result = dict()

    # 赞我的新增数目
    result['new_likes_to_me'] = new_like_to_me_badge.get_badge_num(uid)

    # 评论我的新增数目
    result['new_cmt_to_me'] = new_comment_to_me_badge.get_badge_num(uid)

    # 新增粉丝数目
    result['new_fans_to_me'] = new_fans_to_me_badge.get_badge_num(uid)

    # 新增我的通知
    new_notices_to_me = await get_new_notices_to_me(uid, 100, [const_mix.NOTICE_TYPE_SYS])
    result['new_notices_to_me'] = len(new_notices_to_me)

    return result


async def get_new_notices_to_me(uid, limit, ntypes=None):
    """
    获取用户的未读信息
    :param uid:
    :param limit:
    :return:
    """
    # 最近读取时间
    favor = await favor_service.get_user_favor(uid)
    last_read_notice_ct = favor.get('last_read_notice_ct', 0)

    # 计算未读消息数目
    ntypes = ntypes or const_mix.ALL_NOTICE_TYPES
    notice_col = db.get_motordb_col_notice()
    query_dict = build_notice_query_dict(
        uids=['', uid], notice_types=ntypes, status=[const_mix.NOTICE_STATUS_VISIBLE], ct_gt=last_read_notice_ct)
    projection = {'_id': True}
    new_notices_to_me = await mongo_async.mongo_find_limit(notice_col, query_dict, limit, projection)
    return new_notices_to_me


def build_notice_query_dict(uids=None, notice_types=None, status=None, ct_gte=None, ct_lt=None, ct_gt=None, rgns=None):
    """
    构造粉丝关注历史查询信息
    :return:
    """
    query_dict = {}
    if uids is not None:
        query_dict['uid'] = uids
        if isinstance(uids, const_base.LIST_TYPES):
            query_dict['uid'] = {'$in': uids}

    if notice_types is not None:
        query_dict['ntype'] = notice_types
        if isinstance(notice_types, const_base.LIST_TYPES):
            query_dict['ntype'] = {'$in': notice_types}

    if status is not None:
        query_dict['status'] = status
        if isinstance(status, const_base.LIST_TYPES):
            query_dict['status'] = {'$in': status}

    if ct_gte or ct_lt or ct_gt:
        query_dict['ct'] = {}
        if ct_gte:
            query_dict['ct']['$gte'] = ct_gte
        if ct_gt:
            query_dict['ct']['$gt'] = ct_gt
        if ct_lt:
            query_dict['ct']['$lt'] = ct_lt

    if rgns is not None:
        query_dict['rgns'] = rgns
        if isinstance(rgns, const_base.LIST_TYPES):
            query_dict['rgns'] = {'$in': rgns}

    return query_dict


def build_notice_info(notice):
    """
    构造系统通知消息
    :return:
    """
    if not notice:
        return {}

    result = {
        'nid': str(notice['_id']),
        'uid': notice['uid'],
        'title': notice['title'],
        'text': notice['text'],
        'ntype': notice['ntype'],
        'status': notice['status'],
        'ct': notice['ct'],
    }

    return result


async def query_notice_list_for_handler(cursor_info, uid, query_dict=None, sorts=None):
    """
    查询粉丝历史列表
    :param cursor_info: 分页信息
    :param uid: 用户
    :return:
    """
    # 分页信息
    offset = cursor_info.get('offset', 0)
    limit = cursor_info.get('limit', const_mix.NOTICES_PAGE_PER_NUM)
    limit = limit if limit < const_mix.NOTICES_PAGE_PER_NUM else const_mix.NOTICES_PAGE_PER_NUM

    # 下一次分页信息
    next_cursor_info = {
        'offset': offset + limit,
        'limit': limit,
    }

    # 获取数据列表
    notice_col = db.get_motordb_col_notice()
    notice_list = await mongo_async.mongo_find_sort_skip_limit(notice_col, query_dict, sorts, offset, limit+1)
    has_more = bool(len(notice_list) > limit)
    notice_list = notice_list[:limit]
    if not notice_list:
        return False, next_cursor_info, []

    # 构造返回列表
    results = []
    for notice in notice_list:
        notice['uid'] = uid
        results.append(
            build_notice_info(notice)
        )

    return has_more, next_cursor_info, results


async def create_new_notice(ntype, status, title, text=None, uid=None, extra=None):
    """
    创建新的通知消息
    :param ntype:
    :param status:
    :param title:
    :param text:
    :param uid:
    :param extra:
    :return:
    """
    notice_col = db.get_motordb_col_notice()
    new_notice = {
        'uid': uid or '',
        'title': title or '',
        'text': text or '',
        'ntype': ntype,
        'status': status,
        'ct': int(time.time()),
    }
    if extra and isinstance(extra, dict):
        new_notice.update(extra)
    new_id = await mongo_async.mongo_insert_one(notice_col, new_notice, returnid=True)
    return str(new_id)


async def get_notice_raw_by_id(nid):
    """
    获取notice
    :param nid:
    :return:
    """
    notice_col = db.get_motordb_col_notice()
    notice = await mongo_async.mongo_find_one(notice_col, {'_id': ObjectId(nid)})
    return notice


async def update_notice_by_nid(nid, status=None, ntype=None, title=None, text=None, uid=None):
    """
    更新通知
    """
    notice_col = db.get_motordb_col_notice()

    set_dict = {}
    if status is not None:
        set_dict['status'] = status
    if ntype is not None:
        set_dict['ntype'] = ntype
    if title is not None:
        set_dict['title'] = title
    if text is not None:
        set_dict['text'] = text
    if uid is not None:
        set_dict['uid'] = uid

    await mongo_async.mongo_update_one(notice_col, {'_id': ObjectId(nid)}, {'$set': set_dict})



