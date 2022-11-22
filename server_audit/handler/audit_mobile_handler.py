# coding=utf-8
"""
基础 handler、功能单一 handler
"""
import ujson

from cores.const import const_err, const_post, const_user
from cores.utils.param_validator import JsonSchemaValidator, OBJECTID_SCHEMA, INT_SCHEMA
from server_app.handler.base_handler import BaseHandler
from cores.favor import favor_service
from cores.base import base_service
from cores.user import user_service
from cores.post import post_service
from server_audit.service import audit_admin_service


class AdminMobPostQueryListsHandler(BaseHandler):
    """
    移动版 管理员 查看帖子列表
    """
    _label = 'AdminMobPostQueryListsHandler'

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):

        # 获取管理员信息
        admin = await audit_admin_service.get_admin_info_by_uid(self.uid)
        if not admin:
            return self.jsonify_err(const_err.CODE_PARAM_ERROR)

        # 分页信息
        cursor_info = base_service.get_cursor_info_from_req_param(self.params)

        # 初始化关注
        favor = await favor_service.initial_user_favor_info(self.uid)

        # 查询请求
        query_dict = post_service.build_post_query_dict(status=const_post.ALL_VISIBLE_STATUS)
        sorts = post_service.build_post_query_sort(const_post.POST_QUERY_SORT_T_NEW)

        # 获取帖子列表
        has_more, next_cursor_info, posts = await post_service.get_post_info_list_for_handler(
            self.uid, cursor_info, query_dict=query_dict, sorts=sorts, favor_info=favor)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {'list': posts, 'has_more': has_more, 'cursor': ujson.dumps(next_cursor_info)}, 'msg': ''}
        self.jsonify(ret)


class AdminMobPostUpdateTagsHandler(BaseHandler):
    """
    移动版 管理员 更新帖子标签
    """
    _label = 'AdminMobPostUpdateTagsHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'pid': OBJECTID_SCHEMA,
        },
        'required': ['pid'],
    })

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):
        self._schema.validate(self.params)

        pid = self.params['pid']
        new_tids = self.params.get('tids', [])[:3]

        # 获取管理员信息
        admin = await audit_admin_service.get_admin_info_by_uid(self.uid)
        if not admin:
            return self.jsonify_err(const_err.CODE_PARAM_ERROR)

        # 更新标签
        await post_service.update_post_tags_for_handler(pid, new_tids)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class AdminMobPostUpdateStatusHandler(BaseHandler):
    """
    移动版 管理员 更新帖子状态
    """
    _label = 'AdminMobPostUpdateStatusHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'pid': OBJECTID_SCHEMA,
            'status': INT_SCHEMA,
        },
        'required': ['pid', 'status'],
    })

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):
        self._schema.validate(self.params)

        pid = self.params['pid']
        new_status = self.params['status']

        # 获取管理员信息
        admin = await audit_admin_service.get_admin_info_by_uid(self.uid)
        if not admin:
            return self.jsonify_err(const_err.CODE_PARAM_ERROR)

        # 获取当前帖子信息
        post = await post_service.get_post_by_id(pid)
        if not post:
            return self.jsonify_err(const_err.CODE_PID_ERROR)

        # 更新状态转换
        if post['status'] != new_status:
            await post_service.update_post_status_for_handler(pid, new_status)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})
        

class AdminMobCommentQueryListHandler(BaseHandler):
    """
    移动版 管理员 查询评论列表
    """
    _label = 'AdminMobCommentQueryListHandler'

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):

        # 获取管理员信息
        admin = await audit_admin_service.get_admin_info_by_uid(self.uid)
        if not admin:
            return self.jsonify_err(const_err.CODE_PARAM_ERROR)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class AdminMobCommentUpdateStatusHandler(BaseHandler):
    """
    移动版 管理员 评论更新状态
    """
    _label = 'AdminMobCommentUpdateStatusHandler'

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):

        # 获取管理员信息
        admin = await audit_admin_service.get_admin_info_by_uid(self.uid)
        if not admin:
            return self.jsonify_err(const_err.CODE_PARAM_ERROR)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class AdminMobUserQueryListHandler(BaseHandler):
    """
    移动版 管理员 用户列表
    """
    _label = 'AdminMobUserQueryListHandler'

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):

        # 获取管理员信息
        admin = await audit_admin_service.get_admin_info_by_uid(self.uid)
        if not admin:
            return self.jsonify_err(const_err.CODE_PARAM_ERROR)

        # 分页信息
        cursor_info = base_service.get_cursor_info_from_req_param(self.params)

        # 查询请求
        query_dict = user_service.build_user_query_dict(status=const_user.ALL_LEGAL_USER_STATUS, utypes=const_user.USER_TYPE_NORMAL)
        sorts = user_service.build_user_query_sort(const_post.POST_QUERY_SORT_T_NEW)

        # 获取帖子列表
        has_more, next_cursor_info, users = await user_service.get_user_info_list_for_handler(
            cursor_info, query_dict=query_dict, sorts=sorts)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {'list': users, 'has_more': has_more, 'cursor': ujson.dumps(next_cursor_info)}, 'msg': ''})


class AdminMobUserUpdateStatusHandler(BaseHandler):
    """
    移动版 管理员 更新用户状态
    """
    _label = 'AdminMobUserUpdateStatusHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'uid': OBJECTID_SCHEMA,
            'status': INT_SCHEMA,
        },
        'required': ['uid', 'status'],
    })

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):
        self._schema.validate(self.params)
        uid = self.params['uid']
        status = self.params['status']

        # 获取管理员信息
        admin = await audit_admin_service.get_admin_info_by_uid(self.uid)
        if not admin:
            return self.jsonify_err(const_err.CODE_PARAM_ERROR)

        # 更新用户状态
        await user_service.update_user_by_uid(uid, status=status)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


