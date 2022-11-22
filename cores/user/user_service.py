# -*- coding:utf-8 -*-
"""
user service 方法
"""
import datetime
import time
from bson import ObjectId

from config import config
from cores.const import const_user, const_base
from cores.database import db, mongo_async
from cores.base import base_service
from cores.base.base_service import AioRedisSession


def build_user_base_info(user, need_passwd=False, need_raw_name=False):
    """
    构建用户基础信息
    :param user:
    :param need_passwd: 输出是否需要密码
    :param need_raw_name: 输出是否完整账户名
    :return:
    """
    result = {}
    if user:
        result['uid'] = str(user['_id'])
        result['name'] = user['name']
        result['status'] = user['status']
        result['utypes'] = user['utypes']
        result['nick'] = user['nick']
        result['sign'] = user.get('sign', '')
        result['invite_code'] = user.get('invite_code', '')
        if need_passwd:
            result['passwd'] = user['passwd']
        if not need_raw_name:
            result['name'] = '*******' + user['name'][-4:]
        result['avatar_info'] = base_service.build_img_infos_item(user['raw_avatar'])
        result['bg_info'] = base_service.build_img_infos_item(user['raw_bg'])
        result['young_mode'] = user.get('young_mode', False)
        result['ct'] = user['ct']
    return result


async def get_user_info(uid=None, name=None, need_passwd=False, need_raw_name=False):
    """
    获取指定用户信息
    :param uid: 用户ID
    :param name: 用户注册名称
    :param need_passwd: 需要密码
    :param need_raw_name: 是否需要完整账户名
    :return:
    """
    user_info = await get_raw_user(uid=uid, name=name)
    result = build_user_base_info(user_info, need_passwd, need_raw_name)
    return result


async def get_raw_user(uid=None, name=None):
    """
    获取指定用户的mongo原始信息
    :param uid: 用户ID
    :param name: 用户名称
    :return: 用户信息
    """
    user_col = db.get_motordb_col_user()
    user_info = {}
    if uid and ObjectId.is_valid(uid):
        user_info = await mongo_async.mongo_find_one(user_col, {'_id': ObjectId(uid)})
    elif name:
        user_info = await mongo_async.mongo_find_one(user_col, {'name': name})
    return user_info


def build_guest_name(did):
    """
    构造游客账户名出, 格式为: guest_xxxx
    """
    return 'guest_%s' % did


def generate_default_nick_by_name():
    """
    生成随机用户昵称
    """
    return datetime.datetime.now().strftime('%Y%m%d%S')[2:] + base_service.get_random_str(3)


async def initial_guest_by_did(did, rgns=None, langs=None,
                               h_carrier='', h_zone_name='', h_ip='', h_region=''):
    """
    初始化游客账户, 理论上永远不会出现失败。
    """
    guest_name = build_guest_name(did)
    guest_user_info = await get_raw_user(name=guest_name)
    # 已存在
    if guest_user_info:
        uid = str(guest_user_info['_id'])
    # 新创建
    else:
        nick = generate_default_nick_by_name()
        uid = await create_new_user(
            guest_name, base_service.get_random_str(), nick, const_user.USER_STATUS_VISIBLE,
            did=did, utypes=[const_user.USER_TYPE_GUEST], rgns=rgns, langs=langs,
            h_carrier=h_carrier, h_zone_name=h_zone_name, h_ip=h_ip, h_region=h_region
        )
    return uid


async def create_new_user(name, passwd, nick, status, utypes, raw_avatar=None, raw_bg=None, sign=None, did=None, rgns=None, langs=None,
                               h_carrier='', h_zone_name='', h_ip='', h_region='', extra=None, now_ts=None):
    """
    创建新用户
    """

    if not now_ts:
        now_ts = int(time.time())

    # 用户类型
    if isinstance(utypes, int):
        utypes = [utypes]

    new_user = {
        'name': name,
        'passwd': passwd,
        'nick': nick,
        'status': status or const_user.USER_STATUS_VISIBLE,
        'raw_avatar': raw_avatar or {},
        'raw_bg': raw_bg or {},
        'sign': sign or '',
        'did': did or '',
        'utypes': utypes,
        'ct': now_ts,
        'ut': now_ts,
        'reg_ts': now_ts,  # 注册时间
        'rgns': rgns or [],
        'langs': langs or [],
        'h_carrier': h_carrier,
        'h_zone_name': h_zone_name,
        'h_ip': h_ip,
        'h_region': h_region,
    }

    if extra and isinstance(extra, dict):
        new_user.update(extra)

    user_col = db.get_motordb_col_user()
    uid = await mongo_async.mongo_insert_one(user_col, new_user, returnid=True)
    return str(uid)


async def user_login(uid, user_info, expire_time=config.USER_SESSION_EXT, login_from_type=const_user.LOGIN_FROM_TYPE_PHONE):
    """
    用户登录
    :return:
    """
    return await AioRedisSession.create_new_session(uid, user_info, expire_time, login_from_type)


def valid_user_name_type(name):
    """
    用户名合法性验证, 判断注册账户名类型: 邮箱|手机号
    :return:
    """
    if not name:
        return const_user.USER_NTYPE_ERR
    if not isinstance(name, str):
        return const_user.USER_NTYPE_ERR
    # 邮箱
    if len(name.split('@')) == 2:
        return const_user.USER_NTYPE_MAIL
    # 大陆手机
    if len(name) == 14 and name[:3] == '86-':
        return const_user.USER_NTYPE_PHONE
    # 非大陆手机
    if '-' in name and len(name.split('-')) == 2 and name.split('-')[0].isdigit() and name.split('-')[1].isdigit():
        return const_user.USER_NTYPE_INTER_PHONE
    return const_user.USER_NTYPE_ERR


async def update_user_by_uid(uid, name='', passwd='', nick=None, raw_avatar=None, raw_bg=None, sign=None, utypes=None, status=None, reg_ts=None, young_mode=None):
    """
    更新用户信息
    :return:
    """
    user_col = db.get_motordb_col_user()
    old_user = await user_col.find_one(ObjectId(uid))
    if not old_user:
        return {}

    set_dict = {}
    if name:
        set_dict['name'] = name
    if passwd:
        set_dict['passwd'] = passwd
    if nick is not None:
        set_dict['nick'] = nick
    if raw_avatar is not None and raw_avatar.get('url'):
        set_dict['raw_avatar'] = raw_avatar
    if raw_bg is not None:
        set_dict['raw_bg'] = raw_bg
    if sign is not None:
        set_dict['sign'] = sign
    if utypes and isinstance(utypes, const_base.LIST_TYPES):
        set_dict['utypes'] = list(utypes)
    if utypes and isinstance(utypes, int):
        set_dict['utypes'] = [utypes]
    if status is not None:
        set_dict['status'] = status
    if reg_ts is not None:
        set_dict['reg_ts'] = reg_ts
    if young_mode is not None:
        set_dict['young_mode'] = young_mode

    update_dict = {}
    if set_dict:
        update_dict['$set'] = set_dict

    user = {}
    if update_dict:
        user = await mongo_async.mongo_find_one_and_update(user_col, {'_id': ObjectId(uid)}, update_dict, upsert=True)

    return user


def get_user_login_from_type(is_pc=False):
    """
    获取用户登录来源类型
    :return:
    """
    login_from_type = const_user.LOGIN_FROM_TYPE_PHONE
    if is_pc:
        login_from_type = const_user.LOGIN_FROM_TYPE_PC
    return login_from_type


async def reset_user_passwd(name, new_passwd):
    """
    创建新用户
    """
    user_col = db.get_motordb_col_user()
    await mongo_async.mongo_update_one(user_col, {'name': name}, {'$set': {'passwd': new_passwd}})


async def get_user_map_by_uids(uids):
    """
    批量获取用户信息映射表
    :return:
    """
    if not uids:
        return {}

    result = {}
    user_col = db.get_motordb_col_user()
    user_list = await mongo_async.mongo_find(user_col, {'_id': {'$in': base_service.ensure_mongo_obj_ids(uids)}})
    for user in user_list:
        result[str(user['_id'])] = user
    return result


def build_user_info_by_favor(user, need_passwd=False, viewer_favor_info=None, user_favor_info=None):
    """
    构建用户信息, 包含关注信息标识
    :return:
    """
    if not user:
        return {}

    # 用户基本信息
    result = build_user_base_info(user, need_passwd=need_passwd)

    # 查看者是否已经关注该用户
    result['favored'] = False
    if viewer_favor_info:
        result['favored'] = result['uid'] in viewer_favor_info.get('f_uids', [])

    # 该用户是否关注了查看者
    result['fans_to_viewer'] = False
    if user_favor_info and viewer_favor_info:
        result['fans_to_viewer'] = viewer_favor_info['uid'] in user_favor_info.get('f_uids', [])

    # 被查看者的其他计数
    if user_favor_info:
        result['fans_num'] = user_favor_info['fans_num']
        result['post_num'] = user_favor_info['post_num']
        result['comment_num'] = user_favor_info['comment_num']
        # 赞别人内容的总数
        result['liked_post_num'] = user_favor_info.get('liked_post_num', 0)
        result['liked_cmt_num'] = user_favor_info.get('liked_cmt_num', 0)
        # 内容获赞总数
        result['likes_post_to_me'] = user_favor_info.get('likes_post_to_me', 0)
        result['likes_cmt_to_me'] = user_favor_info.get('likes_cmt_to_me', 0)

    return result


async def is_forbidden_user(user_or_uid, forbidden_status_list=None):
    """
    检查用户是否是封禁状态
    :param user_or_uid:
    :param forbidden_status_list: 封禁状态列表
    :return:
    """
    user_info = user_or_uid
    if isinstance(user_or_uid, str):
        user_info = await get_raw_user(uid=user_or_uid)

    if not user_info:
        return True

    forbidden_status_list = forbidden_status_list or [const_user.USER_STATUS_BAN_ACCOUNT]
    return bool(user_info['status'] in forbidden_status_list)


async def get_user_info_list_for_handler(cursor_info, query_dict=None, sorts=None, viewer_favor_info=None):
    """
    获取用户列表信息
    :return:
    """

    # 确保分页合法
    offset = cursor_info.get('offset', 0)
    offset = offset if offset >= 0 else 0
    limit = cursor_info.get('limit', const_user.USER_SEARCH_PAGE_PER_NUM)
    limit = min(const_user.USER_SEARCH_PAGE_PER_NUM, limit)

    # 获取数据
    user_col = db.get_motordb_col_user()
    users = await mongo_async.mongo_find_sort_skip_limit(user_col, query_dict, sorts, offset, limit + 1)
    has_more = bool(len(users) > limit)
    users = users[:limit]
    if not users:
        return False, {}, []

    # 构造返回列表
    results = []
    for user in users:
        results.append(
            build_user_info_by_favor(user, viewer_favor_info=viewer_favor_info)
        )

    # 下一次分页信息
    next_cursor_info = {
        'offset': offset + limit,
        'limit': limit,
    }

    return has_more, next_cursor_info, results


def build_user_query_dict(uid=None, status=None, utypes=None):
    """
    构造用户的查询dict
    :return:
    """
    query_dict = {}

    if uid is not None:
        query_dict['uid'] = {}
        if isinstance(uid, const_base.LIST_TYPES):
            query_dict['uid']['$in'] = base_service.ensure_mongo_str_ids(uid)
        if isinstance(uid, ObjectId):
            query_dict['uid'] = str(uid)
        if isinstance(uid, str):
            query_dict['uid'] = uid

    if status is not None:
        query_dict['status'] = status
        if isinstance(status, const_base.LIST_TYPES):
            query_dict['status'] = {'$in': status}

    if utypes is not None:
        query_dict['utypes'] = utypes
        if isinstance(utypes, const_base.LIST_TYPES):
            query_dict['utypes'] = {'$in': utypes}

    return query_dict


def build_user_query_sort(query_sort_type=None):
    """
    构造排序信息
    :return:
    """
    sorts = [('ct', -1)]
    return sorts

