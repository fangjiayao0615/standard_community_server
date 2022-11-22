# coding=utf-8
"""
评论相关 handler
"""
import time

import ujson

from bson import ObjectId

from cores.const import const_err, const_cmt, const_user
from server_app.handler.base_handler import BaseHandler
from cores.base import base_service
from cores.user import user_service
from cores.comment import comment_service
from cores.post import post_service
from cores.utils import redis_lock
from cores.utils.param_validator import JsonSchemaValidator, OBJECTID_SCHEMA


class CommentPostQueryListHandler(BaseHandler):
    """
    查询帖子页面的评论列表
    """
    _label = 'CommentPostQueryListHandler'

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
        pid = self.params['pid']
        sort_type = self.params.get('sort_type')
        cursor_info = base_service.get_cursor_info_from_req_param(self.params)

        if not ObjectId.is_valid(pid):
            self.jsonify_err(const_err.CODE_PID_ERROR)
            return

        # 上界时间 优先使用回传分界
        ct_lt = cursor_info.get('ct_lt', int(time.time())+1)

        # 排序最新
        sorts = comment_service.build_comment_query_sort(sort_type)

        # 查询请求
        query_dict = comment_service.build_comment_query_dict(pid=pid, status=const_cmt.COMMENT_STATUS_VISIBLE, ct_lt=ct_lt)

        # 获取评论列表
        has_more, next_cursor_info, comments = await comment_service.get_comment_info_list_for_handler(self.uid, cursor_info, query_dict, sorts)

        # 指定边界时间
        next_cursor_info['ct_lt'] = ct_lt

        # 指定pid时首页插入精评
        comments = await comment_service.attach_fine_comment_for_handler(pid, self.uid, cursor_info, comments)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {'list': comments, 'has_more': has_more, 'cursor': ujson.dumps(next_cursor_info)}, 'msg': ''}
        self.jsonify(ret)


class CommentUserQueryListHandler(BaseHandler):
    """
    查询用户主页页面的评论列表
    """
    _label = 'CommentUserQueryListHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'uid': OBJECTID_SCHEMA,
        },
        'required': ['uid'],
    })

    @BaseHandler.check_permission()
    async def post(self):
        self._schema.validate(self.params)
        uid = self.params['uid']
        sort_type = self.params.get('sort_type')
        cursor_info = base_service.get_cursor_info_from_req_param(self.params)

        if not ObjectId.is_valid(uid):
            self.jsonify_err(const_err.CODE_PID_ERROR)
            return

        # 上界时间 优先使用回传分界
        ct_lt = cursor_info.get('ct_lt', int(time.time())+1)

        # 排序最新
        sorts = comment_service.build_comment_query_sort(sort_type)

        # 查询请求
        query_dict = comment_service.build_comment_query_dict(uid=uid, status=const_cmt.COMMENT_STATUS_VISIBLE, ct_lt=ct_lt)

        # 获取评论列表
        has_more, next_cursor_info, comments = await comment_service.get_comment_info_list_for_handler(self.uid, cursor_info, query_dict, sorts)

        # 指定边界时间
        next_cursor_info['ct_lt'] = ct_lt

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {'list': comments, 'has_more': has_more, 'cursor': ujson.dumps(next_cursor_info)}, 'msg': ''}
        self.jsonify(ret)


class CommentCreateHandler(BaseHandler):
    """
    创建评论
    """
    _label = 'CommentCreateHandler'

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
        text = self.params.get('text', '').strip()[:const_cmt.COMMENT_TEXT_MAX_LEN]
        ctype = self.params.get('ctype', const_cmt.COMMENT_TYPE_NORMAL)
        raw_imgs = self.params.get('raw_imgs', [])

        # 参数校验
        if not text and not raw_imgs:
            self.jsonify_err(const_err.CODE_COMMENT_EMPTY_ERROR)
            return

        # 调用频率限制
        if not redis_lock.user_redis_set_unblock_lock(self.uid, CommentCreateHandler._label, const_cmt.COMMENT_FREQUENCY_LIMIT_SEC):
            self.jsonify_err(const_err.CODE_COMMENT_CREATE_QUICKLY_ERROR)
            return

        # 获取post信息
        post = await post_service.get_post_by_id(pid)
        if not post:
            self.jsonify_err(const_err.CODE_PID_ERROR)
            return

        # 屏蔽封禁用户
        is_forbidden = await user_service.is_forbidden_user(self.uid, forbidden_status_list=const_user.ALL_ILLEGAL_USER_STATUS)
        if is_forbidden:
            self.jsonify_err(const_err.CODE_PERMISSION_FORBIDDEN_FAILED)
            return

        # 创建评论
        cid, new_comment = await comment_service.create_new_comment(
            self.uid, pid, text, p_uid=post['uid'], ctype=ctype, raw_imgs=raw_imgs)
        if not cid:
            self.jsonify_err(const_err.CODE_COMMENT_EMPTY_ERROR)
            return

        # 返回评论数据
        user_map = await user_service.get_user_map_by_uids([self.uid])
        comment_info = comment_service.build_comment_base_info(new_comment, user_map, [], [])

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': comment_info, 'msg': ''})


class CommentDeleteHandler(BaseHandler):
    """
    删除评论
    """
    _label = 'CommentDeleteHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'cid': OBJECTID_SCHEMA,
        },
        'required': ['cid'],
    })

    @BaseHandler.check_permission(need_login=True, need_normal_user=True)
    async def post(self):
        self._schema.validate(self.params)
        cid = self.params['cid']

        # 屏蔽封禁用户
        is_forbidden = await user_service.is_forbidden_user(self.uid, forbidden_status_list=const_user.ALL_ILLEGAL_USER_STATUS)
        if is_forbidden:
            self.jsonify_err(const_err.CODE_PERMISSION_FORBIDDEN_FAILED)
            return

        # 获取评论数据
        comment = await comment_service.get_comment_by_id(cid)
        if not comment:
            self.jsonify_err(const_err.CODE_CID_ERROR)
            return

        # 非作者
        if comment['uid'] != self.uid:
            self.jsonify_err(const_err.CODE_POST_DELETE_AUTHOR_ERROR)
            return

        # 删除评论
        await comment_service.delete_comment_for_handler(self.uid, cid)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''}
        self.jsonify(ret)


