# coding=utf-8
"""
标签相关 handler
"""
from cores.const import const_tag, const_err, const_user
from server_app.handler.base_handler import BaseHandler
from cores.tag import tag_service
from cores.favor import favor_service
from cores.base import base_service
from cores.user import user_service
from cores.utils.param_validator import JsonSchemaValidator, STRING_SCHEMA, OBJECTID_SCHEMA


class TagCreateHandler(BaseHandler):
    """
    用户创建话题
    """
    _label = 'TagCreateHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'name': STRING_SCHEMA,
        },
        'required': ['name'],
    })

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):
        self._schema.validate(self.params)

        tag_name = self.params['name']
        raw_cover = self.params.get('raw_cover')

        if len(tag_name) < const_tag.TAG_NAME_LEN_MIN or len(tag_name) > const_tag.TAG_NAME_LEN_MAX:
            self.jsonify_err(const_err.CODE_TAG_NAME_LEN_ERROR)
            return

        # TBD：后续考虑用户单日创建、滤重等限制
        user = await user_service.get_raw_user(uid=self.uid)
        if not user:
            self.jsonify_err(const_err.CODE_FAILED)
            return

        # 屏蔽封禁用户
        is_forbidden = await user_service.is_forbidden_user(self.uid, forbidden_status_list=const_user.ALL_ILLEGAL_USER_STATUS)
        if is_forbidden:
            self.jsonify_err(const_err.CODE_PERMISSION_FORBIDDEN_FAILED)
            return

        # 创建标签
        tid = await tag_service.create_new_tag(tag_name, raw_cover)
        if not tid:
            self.jsonify_err(const_err.CODE_FAILED)
            return

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {'tid': tid}, 'msg': ''})


class TagDetailHandler(BaseHandler):
    """
    查询标签详情
    """
    _label = 'TagDetailHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'tid': OBJECTID_SCHEMA,
        },
        'required': ['tid'],
    })

    @BaseHandler.check_permission(need_normal_user=False)
    async def post(self):
        self._schema.validate(self.params)
        tid = self.params['tid']

        # 用户喜好表
        favor = await favor_service.initial_user_favor_info(self.uid)

        # 创建标签
        tag_info = await tag_service.query_tags_detail_for_handler(tid, viewer_favor_info=favor)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': tag_info, 'msg': ''})


class TagQueryListHandler(BaseHandler):
    """
    查询标签列表
    """
    _label = 'TagQueryListHandler'

    @BaseHandler.check_permission(need_login=False)
    async def post(self):
        keyword = self.params.get('keyword', '').strip().lower()[:20]
        tid = self.params.get('tid', '')

        # 分页信息
        cursor_info = base_service.get_cursor_info_from_req_param(self.params)

        # 用户喜好表
        favor = await favor_service.initial_user_favor_info(self.uid)

        # 搜索主题标签
        offset = cursor_info.get('offset', 0)
        limit = cursor_info.get('limit', 20)

        # 关键词搜索使用ES为数据来源
        tid_or_tids = None
        if keyword:
            # TODO es function
            # tids = es.search_tag()
            offset, limit = 0, const_tag.TAG_PAGE_PER_NUM
        elif tid:
            tid_or_tids = tid

        # 构造查询请求
        query_dict = tag_service.build_tag_query_dict(tid=tid_or_tids, status=[const_tag.TAG_STATUS_REC, const_tag.TAG_STATUS_VISIBLE])

        # 搜索主题标签 - 新
        has_more, next_cursor_info, tags = await tag_service.query_tags_for_handler(offset=offset, limit=limit, query_dict=query_dict, viewer_favor_info=favor)

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {'list': tags}, 'msg': ''})

