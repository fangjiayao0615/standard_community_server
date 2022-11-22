# coding=utf-8
"""
喜好相关 handler
"""
import ujson

from cores.const import const_err, const_mix
from server_app.handler.base_handler import BaseHandler
from cores.favor import favor_service
from cores.base import base_service
from cores.comment import comment_service
from cores.post import post_service
from cores.utils.param_validator import JsonSchemaValidator, OBJECTID_SCHEMA


class FollowUserHandler(BaseHandler):
    """
    用户关注其他用户
    """
    _label = 'FollowUserHandler'

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
        new_uid = self.params['uid']

        # 初始化
        favor = await favor_service.initial_user_favor_info(self.uid)
        if not favor:
            self.jsonify_err(const_err.CODE_FAILED)
            return

        # 达到关注用户上限则失败
        if len(favor['f_uids']) >= const_mix.MAX_F_UIDS_LEN:
            self.jsonify_err(const_err.CODE_FAVOR_UIDS_MAX)
            return

        # 关注用户
        await favor_service.user_follow_user(self.uid, new_uid)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class CancelFollowUserHandler(BaseHandler):
    """
    用户解除关注其他用户
    """
    _label = 'CancelFollowUserHandler'

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
        del_uid = self.params['uid']

        # 初始化
        favor = await favor_service.initial_user_favor_info(self.uid)
        if not favor:
            self.jsonify_err(const_err.CODE_FAILED)
            return

        # 取消关注
        await favor_service.user_no_follow_user(self.uid, del_uid)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class FollowTagHandler(BaseHandler):
    """
    用户关注标签
    """
    _label = 'FollowTagHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'tid': OBJECTID_SCHEMA,
        },
        'required': ['tid'],
    })

    @BaseHandler.check_permission()
    async def post(self):
        self._schema.validate(self.params)
        new_tid = self.params['tid']

        # 初始化
        favor = await favor_service.initial_user_favor_info(self.uid)
        if not favor:
            self.jsonify_err(const_err.CODE_FAILED)
            return

        # 达到关注话题上限则失败
        if len(favor['f_tids']) >= favor.get('max_f_tids_num', const_mix.MAX_F_TIDS_LEN):
            self.jsonify_err(const_err.CODE_FAVOR_TIDS_MAX)
            return

        # 关注话题
        await favor_service.user_follow_tag(self.uid, new_tid)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class CancelFollowTagHandler(BaseHandler):
    """
    用户解除关注标签
    """
    _label = 'CancelFollowTagHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'tid': OBJECTID_SCHEMA,
        },
        'required': ['tid'],
    })

    @BaseHandler.check_permission()
    async def post(self):
        self._schema.validate(self.params)
        del_tid = self.params['tid']

        await favor_service.user_no_follow_tag(self.uid, del_tid)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class LikePostHandler(BaseHandler):
    """
    点赞帖子
    """
    _label = 'LikePostHandler'

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

        # 获取帖子信息
        post = await post_service.get_post_by_id(pid)
        if not post:
            self.jsonify_err(const_err.CODE_PID_ERROR)
            return

        # 帖子点赞
        await favor_service.like_post_for_handler(self.uid, pid, post['uid'])

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class CancelLikePostHandler(BaseHandler):
    """
    取消点赞帖子
    """
    _label = 'CancelLikePostHandler'

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

        # 获取帖子信息
        post = await post_service.get_post_by_id(pid)
        if not post:
            self.jsonify_err(const_err.CODE_PID_ERROR)
            return

        # 取消帖子赞
        await favor_service.cancel_like_post_for_handler(self.uid, pid, post['uid'])

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class DislikePostHandler(BaseHandler):
    """
    点踩帖子
    """
    _label = 'DislikePostHandler'

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

        # 获取帖子信息
        post = await post_service.get_post_by_id(pid)
        if not post:
            self.jsonify_err(const_err.CODE_PID_ERROR)
            return

        # 帖子点踩
        await favor_service.dislike_post_for_handler(self.uid, pid, post['uid'])

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class CancelDislikePostHandler(BaseHandler):
    """
    取消点踩帖子
    """
    _label = 'CancelDislikePostHandler'

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

        # 获取帖子信息
        post = await post_service.get_post_by_id(pid)
        if not post:
            self.jsonify_err(const_err.CODE_PID_ERROR)
            return

        # 更新帖子赞踩
        await favor_service.cancel_dislike_post_for_handler(self.uid, pid, post['uid'])

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class LikeCommentHandler(BaseHandler):
    """
    点赞评论
    """
    _label = 'LikeCommentHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'cid': OBJECTID_SCHEMA,
        },
        'required': ['cid'],
    })

    @BaseHandler.check_permission()
    async def post(self):
        self._schema.validate(self.params)
        cid = self.params['cid']

        # 获取评论信息
        comment = await comment_service.get_comment_by_id(cid)
        if not comment:
            self.jsonify_err(const_err.CODE_CID_ERROR)
            return

        # 赞评论
        await favor_service.like_cmt_for_handler(self.uid, cid, comment['uid'])

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class CancelLikeCommentHandler(BaseHandler):
    """
    取消点赞评论
    """
    _label = 'CancelLikeCommentHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'cid': OBJECTID_SCHEMA,
        },
        'required': ['cid'],
    })

    @BaseHandler.check_permission()
    async def post(self):
        self._schema.validate(self.params)
        cid = self.params['cid']

        # 获取评论信息
        comment = await comment_service.get_comment_by_id(cid)
        if not comment:
            self.jsonify_err(const_err.CODE_CID_ERROR)
            return

        # 取消赞评论
        await favor_service.cancel_like_cmt_for_handler(self.uid, cid, comment['uid'])

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class DislikeCommentHandler(BaseHandler):
    """
    点赞评论
    """
    _label = 'LikeCommentHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'cid': OBJECTID_SCHEMA,
        },
        'required': ['cid'],
    })

    @BaseHandler.check_permission()
    async def post(self):
        self._schema.validate(self.params)
        cid = self.params['cid']

        # 获取评论信息
        comment = await comment_service.get_comment_by_id(cid)
        if not comment:
            self.jsonify_err(const_err.CODE_CID_ERROR)
            return

        # 踩评论
        await favor_service.dislike_cmt_for_handler(self.uid, cid, comment['uid'])

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class CancelDislikeCommentHandler(BaseHandler):
    """
    取消点赞评论
    """
    _label = 'CancelLikeCommentHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'cid': OBJECTID_SCHEMA,
        },
        'required': ['cid'],
    })

    @BaseHandler.check_permission()
    async def post(self):
        self._schema.validate(self.params)
        cid = self.params['cid']

        # 获取评论信息
        comment = await comment_service.get_comment_by_id(cid)
        if not comment:
            self.jsonify_err(const_err.CODE_CID_ERROR)
            return

        # 取消踩评论
        await favor_service.cancel_dislike_cmt_for_handler(self.uid, cid, comment['uid'])

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class GetLikeHistoryToMeHandler(BaseHandler):
    """
    获取点赞历史记录
    """
    _label = 'GetLikeHistoryToMeHandler'

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):

        # 分页信息
        cursor_info = base_service.get_cursor_info_from_req_param(self.params)

        # 查询请求
        query_dict = favor_service.build_like_history_query_dict(
            to_uid=self.uid, obj_type=[const_mix.CONTENT_TYPE_POST_CODE, const_mix.CONTENT_TYPE_COMMENT_CODE],
            action=const_mix.F_ACTION_TYPE_LIKE)
        sorts = [('ct', -1)]

        # 获取帖子列表
        has_more, next_cursor_info, histories = await favor_service.get_like_history_info_list_for_handler(
            self.uid, cursor_info, query_dict=query_dict, sorts=sorts)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {'has_more': has_more, 'cursor': ujson.dumps(next_cursor_info), 'list': histories}, 'msg': ''})


class GetFansHistoryToMeHandler(BaseHandler):
    """
    获取关注历史记录
    """
    _label = 'GetFansHistoryToMeHandler'

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):

        # 分页信息
        cursor_info = base_service.get_cursor_info_from_req_param(self.params)

        # 查询请求
        query_dict = favor_service.build_fans_history_query_dict(to_uid=self.uid)
        sorts = [('ct', -1)]

        # 获取帖子列表
        has_more, next_cursor_info, histories = await favor_service.get_fans_history_info_list_for_handler(
            self.uid, cursor_info, query_dict=query_dict, sorts=sorts)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {'has_more': has_more, 'cursor': ujson.dumps(next_cursor_info), 'list': histories}, 'msg': ''})

