# coding=utf-8
"""
用户中心相关 handler。
"""
import ujson

import time

from cores.const import const_err
from server_app.handler.base_handler import BaseHandler
from cores.favor import favor_service
from cores.base import base_service
from cores.user import user_service
from cores.center import center_service
from cores.utils.param_validator import JsonSchemaValidator, OBJECTID_SCHEMA, ARRAY_INT_SCHEMA


class GetUserHomePageHandler(BaseHandler):
    """
    用户获取其他人主页信息
    """
    _label = 'GetUserHomePageHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'viewed_uid': OBJECTID_SCHEMA,
        },
        'required': ['viewed_uid'],
    })

    @BaseHandler.check_permission(need_login=False)
    async def post(self):
        self._schema.validate(self.params)
        viewed_uid = self.params['viewed_uid']

        # 屏蔽封禁用户
        is_forbidden = await user_service.is_forbidden_user(viewed_uid)
        if is_forbidden:
            self.jsonify_err(const_err.CODE_FORBIDDEN_USER_ERROR)
            return

        # 获取目标用户的关注信息
        viewed_user = await user_service.get_raw_user(uid=viewed_uid)
        viewed_favor = await favor_service.initial_user_favor_info(viewed_uid)
        if not (viewed_user and viewed_favor):
            self.jsonify_err(const_err.CODE_NAME_NO_EXIST_ERROR)
            return

        # 获取当前自己的关注信息
        viewer_favor = await favor_service.initial_user_favor_info(self.uid)
        result = center_service.build_user_home_page_for_handler(viewed_favor, viewed_user, viewer_favor)
        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': result, 'msg': ''})


class GetMyHomePageHandler(BaseHandler):
    """
    用户获取自己主页信息
    """
    _label = 'GetMyHomePageHandler'

    @BaseHandler.check_permission()
    async def post(self):

        # 获取自己的关注信息
        my_user = await user_service.get_raw_user(uid=self.uid)
        my_favor = await favor_service.initial_user_favor_info(self.uid)
        if not (my_user and my_favor):
            self.jsonify_err(const_err.CODE_NAME_NO_EXIST_ERROR)
            return

        # 构造个人主页
        result = await center_service.build_my_home_page_for_handler(my_favor, my_user)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': result, 'msg': ''})


class GetMyBadgesHandler(BaseHandler):
    """
    查询我小红点提示信息
    """
    _label = 'GetMyBadgesHandler'

    @BaseHandler.check_permission(need_normal_user=False)
    async def post(self):

        result = await center_service.get_user_badges(self.uid)
        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': result, 'msg': ''})


class GetMyNoticesHandler(BaseHandler):
    """
    查询我通知列表
    """
    _label = 'GetMyNoticesHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'ntypes': ARRAY_INT_SCHEMA,
        },
        'required': ['ntypes'],
    })

    @BaseHandler.check_permission()
    async def post(self):
        self._schema.validate(self.params)
        ntypes = self.params['ntypes']
        cursor_info = base_service.get_cursor_info_from_req_param(self.params)

        # 获取通知列表
        query_dict = center_service.build_notice_query_dict(notice_types=ntypes)
        sorts = [('ct', -1)]
        has_more, next_cursor_info, notices = await center_service.query_notice_list_for_handler(
            cursor_info, uid=self.uid, query_dict=query_dict, sorts=sorts)

        # 查看首页时，清空未读点赞 badge
        if not cursor_info:
            await favor_service.update_user_last_read_notice_ct(self.uid, int(time.time()))

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {
            'list': notices, 'has_more': has_more, 'cursor': ujson.dumps(next_cursor_info)}, 'msg': ''})




