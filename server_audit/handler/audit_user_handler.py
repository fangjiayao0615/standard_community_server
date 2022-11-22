# coding=utf-8
"""
基础 handler、功能单一 handler
"""
from cores.const import const_err
from server_audit.handler.audit_base_handler import AuditBaseHandler
from cores.base import base_service
from cores.user import user_service


class AdminUserCreateHandler(AuditBaseHandler):
    """
    管理员创建用户
    """
    _label = 'AdminUserCreateHandler'

    @AuditBaseHandler.check_permission()
    async def post(self):

        name = self.params['name']
        nick = self.params['nick']
        status = self.params['status']
        sign = self.params.get('sign', '').strip()
        raw_avatar = self.params['raw_avatar']
        utypes = self.params['utypes']

        # 已经创建
        old_user = await user_service.get_raw_user(name=name)
        if old_user:
            return self.jsonify_err(const_err.CODE_NAME_ALREADY_EXIST_ERROR)

        # 创建用户
        uid = await user_service.create_new_user(
            name, base_service.get_random_str(), nick, status, utypes,
            raw_avatar=raw_avatar, raw_bg=None, sign=sign)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {'uid': uid}, 'msg': ''}
        self.jsonify(ret)

