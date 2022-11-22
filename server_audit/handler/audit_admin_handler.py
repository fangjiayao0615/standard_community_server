# coding=utf-8
"""
管理员相关 handler
"""
from config import config
from cores.const import const_err
from cores.utils.param_validator import JsonSchemaValidator, STRING_SCHEMA
from server_audit.handler.audit_base_handler import AuditBaseHandler
from server_audit.service import audit_admin_service
from cores.utils import logger


class AdminLoginHandler(AuditBaseHandler):
    """
    管理员登录
    """
    _label = 'AdminLoginHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'name': STRING_SCHEMA,
        },
        'required': ['name'],
    })

    async def post(self):
        try:
            admin_id = self.params.get('account', '').strip().lower()
            passwd = self.params.get('pwd', '').strip()
        except Exception as e:
            logger.error(str(e))
            self.jsonify_err(const_err.CODE_PARAM_ERROR)
            return

        # 账户密码不能为空
        if not (admin_id and passwd):
            self.jsonify_err(const_err.CODE_NAME_PASSWD_ERROR)
            return

        # 动态密码检查
        admin_info = await audit_admin_service.get_admin_info_by_admin_id(admin_id)
        if not admin_info:
            self.jsonify_err(const_err.CODE_NAME_PASSWD_ERROR, '没有管理用户')
            return

        # 动态密码检查
        passwds = audit_admin_service.totp(admin_info['secret'])
        if passwd not in passwds:
            self.jsonify_err(const_err.CODE_NAME_PASSWD_ERROR, '验证失败')
            return

        # 执行登录并返回登录信息
        session_id = audit_admin_service.admin_login(admin_id, config.OP_ADMIN_SESSION_EXT)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {'session': session_id, 'account': admin_id}, 'msg': ''}
        self.jsonify(ret)


class AdminLogoutHandler(AuditBaseHandler):
    """
    管理员登出
    """
    _label = 'AdminLogoutHandler'

    async def post(self):

        # 删除登录session
        session_id = self.params.get('session', '')
        audit_admin_service.AdminRedisSession.delete_session(session_id)
        ret = {'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''}
        self.jsonify(ret)

