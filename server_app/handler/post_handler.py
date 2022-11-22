# coding=utf-8
"""
帖子相关 handler
"""
import ujson

from cores.const import const_post, const_err, const_user
from server_app.handler.base_handler import BaseHandler
from cores.favor import favor_service
from cores.base import base_service
from cores.user import user_service
from cores.post import post_service
from cores.utils import redis_lock
from cores.utils.param_validator import JsonSchemaValidator, OBJECTID_SCHEMA, INT_SCHEMA


class PostRecommendQueryListHandler(BaseHandler):
    """
    推荐帖子列表v1
    """
    _label = 'PostRecommendQueryListHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
        },
        'required': [],
    })

    @BaseHandler.check_permission(need_login=False)
    async def post(self):
        self._schema.validate(self.params)

        # 未识别uid
        if not self.uid:
            return self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {'list': []}, 'msg': ''})

        # 初始化关注
        favor = await favor_service.initial_user_favor_info(self.uid)

        # 获取帖子列表
        posts = await post_service.get_recommend_post_info_list_for_handler_v1(self.uid, favor_info=favor)

        # 记录推荐历史记录
        pids = [post['pid'] for post in posts]
        await post_service.record_recommend_post_history(self.uid, pids)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {'list': posts}, 'msg': ''}
        self.jsonify(ret)


class PostHistoryRecommendQueryListHandler(BaseHandler):
    """
    获取最近推荐帖子历史
    """
    _label = 'PostHistoryRecommendQueryListHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
        },
        'required': [],
    })

    @BaseHandler.check_permission(need_login=False)
    async def post(self):
        self._schema.validate(self.params)

        # 未识别uid
        if not self.uid:
            return self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {'list': []}, 'msg': ''})

        # 初始化关注
        favor = await favor_service.initial_user_favor_info(self.uid)

        # 获取帖子列表
        posts = await post_service.get_history_recommend_post_info_list_for_handler(self.uid, favor_info=favor)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {'list': posts}, 'msg': ''}
        self.jsonify(ret)


class PostUserQueryListHandler(BaseHandler):
    """
    用户页查询帖子列表
    """
    _label = 'PostUserQueryListHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'p_uid': OBJECTID_SCHEMA,
            'query_sort_type': {'type': 'integer'},
        },
        'required': ['p_uid'],
    })

    @BaseHandler.check_permission(need_login=False)
    async def post(self):
        self._schema.validate(self.params)
        p_uid = self.params.get('p_uid', '').strip()  # 帖子用户ID
        query_sort_type = self.params.get('qtype', const_post.POST_QUERY_SORT_T_NEW)

        # 分页信息
        cursor_info = base_service.get_cursor_info_from_req_param(self.params)

        # 初始化关注
        favor = await favor_service.initial_user_favor_info(self.uid)

        # 查询请求
        query_dict = post_service.build_post_query_dict(uid=p_uid, status=const_post.ALL_VISIBLE_STATUS)
        sorts = post_service.build_post_query_sort(query_sort_type)

        # 获取帖子列表
        has_more, next_cursor_info, posts = await post_service.get_post_info_list_for_handler(
            self.uid, cursor_info, query_dict=query_dict, sorts=sorts, favor_info=favor)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {'list': posts, 'has_more': has_more, 'cursor': ujson.dumps(next_cursor_info)}, 'msg': ''}
        self.jsonify(ret)


class PostTagQueryListHandler(BaseHandler):
    """
    标签页查询帖子列表
    """
    _label = 'PostTagQueryListHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'tid': OBJECTID_SCHEMA,
            'query_sort_type': {'type': 'integer'},
        },
        'required': ['tid'],
    })

    @BaseHandler.check_permission(need_login=False)
    async def post(self):
        self._schema.validate(self.params)
        tid = self.params['tid']
        query_sort_type = self.params.get('qtype', const_post.POST_QUERY_SORT_T_NEW)
        post_types = self.params.get('ptypes', const_post.ALL_VALID_POST_TYPES)

        # 分页信息
        cursor_info = base_service.get_cursor_info_from_req_param(self.params)

        # 初始化关注
        favor = await favor_service.initial_user_favor_info(self.uid)

        # 获取帖子列表
        query_dict = post_service.build_post_query_dict(tid=tid, ptype=post_types, status=const_post.ALL_VISIBLE_STATUS)
        sorts = post_service.build_post_query_sort(query_sort_type)

        # 获取帖子列表
        has_more, next_cursor_info, normal_posts = await post_service.get_post_info_list_for_handler(
            self.uid, cursor_info, sorts=sorts, favor_info=favor, query_dict=query_dict)

        ret = {
            'ret': const_err.CODE_SUCCESS, 'msg': '',
            'data': {
                'list': normal_posts,
                'has_more': has_more,
                'cursor': ujson.dumps(next_cursor_info)
            }
        }
        self.jsonify(ret)


class PostQueryDetailHandler(BaseHandler):
    """
    查询帖子详情
    """
    _label = 'PostQueryDetailHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'pid': OBJECTID_SCHEMA,
        },
        'required': ['pid'],
    })

    @BaseHandler.check_permission()
    async def post(self):
        self._schema.validate(self.params)
        view_uid = self.uid
        pid = self.params['pid']

        # 获取帖子详情
        post_info = await post_service.get_post_detail_for_handler(pid, view_uid)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': post_info, 'msg': ''}
        self.jsonify(ret)


class PostCreateHandler(BaseHandler):
    """
    创建帖子
    """
    _label = 'PostCreateHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'ptype': INT_SCHEMA,
        },
        'required': ['ptype'],
    })

    @BaseHandler.check_permission(need_login=True, need_normal_user=True)
    async def post(self):
        self._schema.validate(self.params)

        post_type = self.params['ptype']
        text = self.params.get('text', '').strip()
        title = self.params.get('title', '').strip()
        raw_imgs = self.params.get('raw_imgs', [])
        tids = self.params.get('tids', [])[:3]
        raw_articles = self.params.get('raw_articles', [])

        # 调用频率限制
        if not redis_lock.user_redis_set_unblock_lock(self.uid, PostCreateHandler._label, const_post.POST_FREQUENCY_LIMIT_SEC):
            self.jsonify_err(const_err.CODE_POST_CREATE_QUICKLY_ERROR)
            return

        # 屏蔽封禁用户
        is_forbidden = await user_service.is_forbidden_user(self.uid, forbidden_status_list=const_user.ALL_ILLEGAL_USER_STATUS)
        if is_forbidden:
            self.jsonify_err(const_err.CODE_PERMISSION_FORBIDDEN_FAILED)
            return

        # 创建帖子
        pid, new_post = await post_service.create_new_post(
            self.uid, text, post_type, raw_imgs=raw_imgs, tids=tids,
            raw_articles=raw_articles, title=title)

        if not pid:
            self.jsonify_err(const_err.CODE_POST_CREATE_ERROR)
            return

        # 返回创建的帖子信息
        post_info = await post_service.get_post_detail_for_handler(pid, self.uid)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': post_info, 'msg': ''}
        self.jsonify(ret)


class PostDeleteHandler(BaseHandler):
    """
    删除帖子
    """
    _label = 'PostDeleteHandler'
    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'pid': OBJECTID_SCHEMA,
        },
        'required': ['pid'],
    })

    @BaseHandler.check_permission(need_login=True, need_normal_user=True)
    async def post(self):
        self._schema.validate(self.params)
        pid = self.params['pid']

        # 获取帖子数据
        post = await post_service.get_post_by_id(pid)
        if not post:
            self.jsonify_err(const_err.CODE_PID_ERROR)
            return

        # 非作者
        if post['uid'] != self.uid:
            self.jsonify_err(const_err.CODE_POST_DELETE_AUTHOR_ERROR)
            return

        # 执行删除动作
        await post_service.delete_user_post_for_handler(self.uid, pid)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''}
        self.jsonify(ret)



