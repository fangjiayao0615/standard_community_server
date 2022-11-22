# coding=utf-8
"""
用户相关 handler
"""
import time

from cores.const import const_user, const_err
from server_app.handler.base_handler import BaseHandler
from cores.base import base_service
from cores.user import user_service
from cores.utils import redis_lock
from cores.utils import logger
from cores.utils.param_validator import JsonSchemaValidator, STRING_SCHEMA


class GuestRegisterHandler(BaseHandler):
    """
    游客注册
    """
    _label = 'GuestRegisterHandler'

    async def post(self):
        try:
            did = self.params.get('h_did', '').strip()[:const_user.USER_NAME_MAX_LEN]
            h_carrier = self.params.get('h_carrier', '').strip()
            h_region = self.params.get('h_region', '').strip()
            h_ip = self.request.remote_ip
        except Exception as e:
            logger.error(str(e))
            self.jsonify_err(const_err.CODE_PARAM_ERROR)
            return

        if not did:
            self.jsonify_err(const_err.CODE_PARAM_ERROR)
            return

        # 登录入口频率限制: IP限制设备
        ip = self.request.remote_ip
        if not redis_lock.user_redis_set_unblock_lock(ip, GuestRegisterHandler._label, 1):
            self.jsonify_err(const_err.CODE_ACT_QUICKLY_ERROR)
            return

        # 获取游客账号
        uid = await user_service.initial_guest_by_did(
            did, h_carrier=h_carrier, h_ip=h_ip, h_region=h_region
        )
        if not uid:
            self.jsonify_err(const_err.CODE_FAILED)
            return

        # 获取用户信息
        user_info = await user_service.get_user_info(uid=uid)
        if not user_info:
            self.jsonify_err(const_err.CODE_PARAM_ERROR)
            return

        # 用户登录
        session_id = await user_service.user_login(uid, user_info)

        # 用户登录信息
        data = base_service.build_user_login_info(user_info, session_id)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': data, 'msg': ''}
        self.jsonify(ret)


class RegisterHandler(BaseHandler):
    """
    用户注册入口
    """
    _label = 'RegisterHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'name': STRING_SCHEMA,
            'code': STRING_SCHEMA,
            'pwd': STRING_SCHEMA,
        },
        'required': ['name', 'code', 'pwd'],
    })

    async def post(self):
        self._schema.validate(self.params)
        name = self.params['name']
        passwd = self.params['pwd']
        code = self.params['code']
        did = self.params.get('h_did', '')
        is_pc = bool(self.params.get('is_pc', ''))
        h_carrier = self.params.get('h_carrier', '')
        h_zone_name = self.params.get('h_zone_name', '')
        h_region = self.params.get('h_region', '')
        h_ip = self.request.remote_ip

        # 验证账号格式
        if user_service.valid_user_name_type(name) == const_user.USER_NTYPE_ERR:
            self.jsonify_err(const_err.CODE_NAME_FMT_ERROR)
            return

        # 账户密码不能为空
        if not passwd:
            self.jsonify_err(const_err.CODE_NAME_PASSWORD_ERROR)
            return

        # 调用频率限制
        if not redis_lock.user_redis_set_unblock_lock(did, RegisterHandler._label, const_user.REGISTER_FREQUENCY_LIMIT_SEC):
            self.jsonify_err(const_err.CODE_REG_CREATE_QUICKLY_ERROR)
            return

        # 验证码是否正确
        if not base_service.check_verification_code(name, code, need_delete=False):
            self.jsonify_err(const_err.CODE_VERIFICATION_CODE_ERROR)
            return

        # 用户名是否已存在
        old_user_info = await user_service.get_raw_user(name=name)
        if old_user_info:
            self.jsonify_err(const_err.CODE_NAME_ALREADY_EXIST_ERROR)
            return

        # 游客账户转正
        now_ts = int(time.time())
        nick = user_service.generate_default_nick_by_name()
        guest_user_info = await user_service.get_user_info(name=user_service.build_guest_name(did))
        if guest_user_info:
            uid = guest_user_info['uid']
            await user_service.update_user_by_uid(uid, name, passwd, nick, utypes=const_user.USER_TYPE_NORMAL, reg_ts=now_ts)

        # 创建新用户
        else:
            uid = await user_service.create_new_user(
                name, passwd, nick, const_user.USER_STATUS_VISIBLE, const_user.USER_TYPE_NORMAL,
                h_carrier=h_carrier, h_zone_name=h_zone_name, h_ip=h_ip, h_region=h_region
            )
            if not uid:
                self.jsonify_err(const_err.CODE_FAILED)
                return

        # 用户信息
        user_info = await user_service.get_user_info(uid=uid)

        # 初始化喜好表
        from cores.favor import favor_service
        await favor_service.initial_user_favor_info(uid)

        # 执行登录
        login_from_type = user_service.get_user_login_from_type(is_pc)
        session_id = await user_service.user_login(uid, user_info, login_from_type=login_from_type)

        # 返回登录信息
        data = base_service.build_user_login_info(user_info, session_id)

        # 删除此次验证码
        base_service.check_verification_code(name, code, need_delete=True)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': data, 'msg': ''}
        self.jsonify(ret)


class SendVerificationCodeHandler(BaseHandler):
    """
    发送验证码
    """
    _label = 'SendVerificationCodeHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'name': STRING_SCHEMA,
        },
        'required': [],
    })

    @BaseHandler.check_permission(need_login=False)
    async def post(self):
        self._schema.validate(self.params)
        name = self.params.get('name')

        # 未指定手机号则使用登录session里面找用户发放
        if not name and self.session:
            user = await user_service.get_raw_user(self.uid)
            name = user['name']
        if not name:
            self.jsonify_err(const_err.CODE_NAME_FMT_ERROR)
            return

        # 账户格式检测
        if user_service.valid_user_name_type(name) == const_user.USER_NTYPE_ERR:
            self.jsonify_err(const_err.CODE_NAME_FMT_ERROR)
            return

        # 调用频率限制
        if not redis_lock.user_redis_set_unblock_lock(name, SendVerificationCodeHandler._label, lock_time=const_user.REGISTER_FREQUENCY_LIMIT_SEC):
            self.jsonify_err(const_err.CODE_ACT_QUICKLY_ERROR)
            return

        # 验证码当日发送达到最大次数
        if base_service.reach_verification_code_max_times(name):
            self.jsonify_err(const_err.CODE_VERIFICATION_MAX_ERROR)
            return

        # 发送验证码
        verification_code = await base_service.send_verification_code(name)
        logger.info('name %s, verification_code %s' % (name, verification_code))
        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class CheckVerificationCodeHandler(BaseHandler):
    """
    检测验证码
    """
    _label = 'CheckVerificationCodeHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'h_did': STRING_SCHEMA,
            'code': STRING_SCHEMA,
            'name': STRING_SCHEMA,
        },
        'required': ['h_did', 'code'],
    })

    @BaseHandler.check_permission(need_login=False)
    async def post(self):
        self._schema.validate(self.params)

        h_did = self.params['h_did'].strip()
        code = self.params['code'].strip()
        name = self.params.get('name', '').strip()

        # 未指定手机号则使用登录session里面找用户发放
        if not name and self.session:
            user = await user_service.get_raw_user(self.uid)
            name = user['name']

        # 账户格式检测
        if user_service.valid_user_name_type(name) is const_user.USER_NTYPE_ERR:
            self.jsonify_err(const_err.CODE_NAME_FMT_ERROR)
            return

        # 调用频率限制 - 手机号
        if not redis_lock.user_redis_set_unblock_lock(name, CheckVerificationCodeHandler._label, lock_time=const_user.REGISTER_FREQUENCY_LIMIT_SEC):
            self.jsonify_err(const_err.CODE_ACT_QUICKLY_ERROR)
            return

        # 调用频率限制 - 硬件号
        if not redis_lock.user_redis_set_unblock_lock(h_did, CheckVerificationCodeHandler._label, lock_time=const_user.REGISTER_FREQUENCY_LIMIT_SEC):
            self.jsonify_err(const_err.CODE_ACT_QUICKLY_ERROR)
            return

        # 验证码是否正确
        if not base_service.check_verification_code(name, code, need_delete=False):
            self.jsonify_err(const_err.CODE_VERIFICATION_CODE_ERROR)
            return

        self.jsonify({'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''})


class LoginHandler(BaseHandler):
    """
    用户登录
    """
    _label = 'LoginHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'h_did': STRING_SCHEMA,
            'name': STRING_SCHEMA,
            'pwd': STRING_SCHEMA,
        },
        'required': ['h_did', 'name', 'pwd'],
    })

    async def post(self):
        self._schema.validate(self.params)

        name = self.params['name'].strip().lower()[:const_user.USER_NAME_MAX_LEN]
        passwd = self.params['pwd'].strip()[:const_user.USER_NAME_MAX_LEN]
        is_pc = bool(self.params.get('is_pc', ''))

        # 账户密码不能为空
        if not (name and passwd):
            self.jsonify_err(const_err.CODE_NAME_PASSWORD_ERROR)
            return

        # 密码检查
        user_info = await user_service.get_user_info(name=name, need_passwd=True)
        if user_info['passwd'] != passwd:
            self.jsonify_err(const_err.CODE_NAME_PASSWORD_ERROR)
            return

        # 执行登录并返回登录信息
        login_from_type = user_service.get_user_login_from_type(is_pc)
        session_id = await user_service.user_login(user_info['uid'], user_info, login_from_type=login_from_type)
        data = base_service.build_user_login_info(user_info, session_id)

        # 初始化喜好表
        from cores.favor import favor_service
        await favor_service.initial_user_favor_info(user_info['uid'])

        ret = {'ret': const_err.CODE_SUCCESS, 'data': data, 'msg': ''}
        self.jsonify(ret)


class ValidCodeLoginHandler(BaseHandler):
    """
    验证码登录
    """
    _label = 'ValidCodeLoginHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'h_did': STRING_SCHEMA,
            'name': STRING_SCHEMA,
            'code': STRING_SCHEMA,
        },
        'required': ['h_did', 'name', 'code'],
    })

    async def post(self):
        self._schema.validate(self.params)
        h_did = self.params['h_did'].strip().lower()[:const_user.USER_NAME_MAX_LEN]
        name = self.params['name'].strip().lower()[:const_user.USER_NAME_MAX_LEN]
        code = self.params['code'].strip()[:const_user.USER_NAME_MAX_LEN]
        is_pc = bool(self.params.get('is_pc', ''))
        did = self.params.get('h_did', '')
        h_carrier = self.params.get('h_carrier', '')
        h_zone_name = self.params.get('h_zone_name', '')
        h_region = self.params.get('h_region', '')
        h_ip = self.request.remote_ip

        # 账户验证码不能为空
        if not (name and code):
            self.jsonify_err(const_err.CODE_NAME_PASSWORD_ERROR)
            return

        # 调用频率限制 - 手机号
        if not redis_lock.user_redis_set_unblock_lock(name, CheckVerificationCodeHandler._label, lock_time=const_user.REGISTER_FREQUENCY_LIMIT_SEC):
            self.jsonify_err(const_err.CODE_ACT_QUICKLY_ERROR)
            return

        # 调用频率限制 - 硬件号
        if not redis_lock.user_redis_set_unblock_lock(h_did, CheckVerificationCodeHandler._label, lock_time=const_user.REGISTER_FREQUENCY_LIMIT_SEC):
            self.jsonify_err(const_err.CODE_ACT_QUICKLY_ERROR)
            return

        # 验证码是否正确
        if not base_service.check_verification_code(name, code, need_delete=False):
            self.jsonify_err(const_err.CODE_VERIFICATION_CODE_ERROR)
            return

        # 账户检查
        user_info = await user_service.get_user_info(name=name, need_passwd=True)
        if not user_info:

            # 游客账户转正
            now_ts = int(time.time())
            nick = user_service.generate_default_nick_by_name()
            default_pwd = base_service.get_random_str()
            guest_user_info = await user_service.get_user_info(name=user_service.build_guest_name(did))
            if guest_user_info:
                uid = guest_user_info['uid']
                await user_service.update_user_by_uid(uid, name, default_pwd, nick, utypes=const_user.USER_TYPE_NORMAL, reg_ts=now_ts)

            # 创建新用户
            else:
                uid = await user_service.create_new_user(
                    name, default_pwd, nick, const_user.USER_STATUS_VISIBLE, const_user.USER_TYPE_NORMAL,
                    h_carrier=h_carrier, h_zone_name=h_zone_name, h_ip=h_ip, h_region=h_region
                )

            # 初始化失败
            if not uid:
                self.jsonify_err(const_err.CODE_ACCOUNT_CREATE_ERROR)
                return

            # 重新获取账户
            user_info = await user_service.get_user_info(uid=uid, need_passwd=True)
            if not user_info:
                self.jsonify_err(const_err.CODE_NAME_NO_EXIST_ERROR)
                return

        # 执行登录并返回登录信息
        login_from_type = user_service.get_user_login_from_type(is_pc)
        session_id = await user_service.user_login(user_info['uid'], user_info, login_from_type=login_from_type)
        data = base_service.build_user_login_info(user_info, session_id)

        # 初始化喜好表
        from cores.favor import favor_service
        await favor_service.initial_user_favor_info(user_info['uid'])

        ret = {'ret': const_err.CODE_SUCCESS, 'data': data, 'msg': ''}
        self.jsonify(ret)


class LogoutHandler(BaseHandler):
    """
    用户登出并以游客身份登录
    """
    _label = 'LogoutHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'h_did': STRING_SCHEMA,
        },
        'required': ['h_did'],
    })

    @BaseHandler.check_permission(need_login=True)
    async def post(self):
        self._schema.validate(self.params)

        did = self.params['h_did'].strip()[:const_user.USER_NAME_MAX_LEN]
        is_pc = bool(self.params.get('is_pc', ''))
        h_carrier = self.params.get('h_carrier', '')
        h_zone_name = self.params.get('h_zone_name', '')
        h_region = self.params.get('h_region', '')
        h_ip = self.request.remote_ip

        # 用户登出
        session_id = self.params.get('session', '')
        await base_service.AioRedisSession.delete_session(session_id)

        # 未提供设备号\桌面版 直接返回
        if (not did) or is_pc:
            ret = {'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''}
            self.jsonify(ret)
            return

        # 获取游客账号
        uid = await user_service.initial_guest_by_did(
            did, h_carrier=h_carrier, h_zone_name=h_zone_name, h_ip=h_ip, h_region=h_region
        )
        if not uid:
            self.jsonify_err(const_err.CODE_FAILED)
            return

        # 用户信息
        user_info = await user_service.get_user_info(uid=uid)
        if not user_info:
            self.jsonify_err(const_err.CODE_FAILED)
            return

        # 用户登录
        session_id = await user_service.user_login(uid, user_info)

        # 返回登录信息
        data = base_service.build_user_login_info(user_info, session_id)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': data, 'msg': ''}
        self.jsonify(ret)


class ResetPasswordHandler(BaseHandler):
    """
    用户重置密码
    """
    _label = 'ResetPasswordHandler'

    _schema = JsonSchemaValidator({
        'type': 'object',
        'properties': {
            'pwd': STRING_SCHEMA,
            'code': STRING_SCHEMA,
        },
        'required': ['pwd', 'code'],
    })

    @BaseHandler.check_permission(need_login=False)
    async def post(self):
        self._schema.validate(self.params)

        name = self.params.get('name', '').strip()[:const_user.USER_NAME_MAX_LEN]
        passwd = self.params['pwd']
        code = self.params['code']
        is_pc = bool(self.params.get('is_pc', ''))

        # 未指定手机号则使用登录session里面找用户发放
        if not name and self.session:
            user = await user_service.get_user_info(self.uid)
            name = user['name']

        # 验证码是否正确
        if not base_service.check_verification_code(name, code):
            self.jsonify_err(const_err.CODE_VERIFICATION_CODE_ERROR)
            return

        # 用户名是否存在
        user_info = await user_service.get_user_info(name=name)
        if not user_info:
            self.jsonify_err(const_err.CODE_NAME_NO_EXIST_ERROR)
            return

        # 重置密码
        await user_service.reset_user_passwd(name, passwd)

        # 执行登录 返回登录信息
        login_from_type = user_service.get_user_login_from_type(is_pc)
        session_id = await user_service.user_login(user_info['uid'], user_info, login_from_type=login_from_type)
        data = base_service.build_user_login_info(user_info, session_id)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': data, 'msg': ''}
        self.jsonify(ret)


class UpdateAccountHandler(BaseHandler):
    """
    更新用户信息
    """
    _label = 'UpdateAccountHandler'

    @BaseHandler.check_permission(need_normal_user=True)
    async def post(self):
        try:
            new_nick = self.params.get('nick')
            new_sign = self.params.get('sign')
            new_raw_avatar = self.params.get('raw_avatar')
            new_raw_bg = self.params.get('raw_bg')
        except Exception as e:
            logger.error(str(e))
            self.jsonify_err(const_err.CODE_PARAM_ERROR)
            return

        # 限制异常长度，异常字符串处理
        if new_nick:
            new_nick = new_nick.strip()[:const_user.USER_NAME_MAX_LEN]
        if new_sign:
            new_sign = new_sign.strip()[:const_user.USER_NAME_MAX_LEN]

        # 头像信息必须是
        if new_raw_avatar and not isinstance(new_raw_avatar, dict):
            self.jsonify_err(const_err.CODE_AVATAR_FMT_ERROR)
            return

        # 背景格式检查
        if new_raw_bg and not isinstance(new_raw_bg, dict):
            self.jsonify_err(const_err.CODE_BG_FMT_ERROR)
            return

        # 昵称不能为空
        if new_nick == '':
            self.jsonify_err(const_err.CODE_NAME_EMPTY_ERROR)
            return

        # 昵称字节长度需要大于4
        if new_nick and len(new_nick) <= 4:
            self.jsonify_err(const_err.CODE_NICK_TOO_SHORT_ERROR)
            return

        # 执行更新操作
        user = await user_service.update_user_by_uid(self.uid, nick=new_nick, raw_avatar=new_raw_avatar, raw_bg=new_raw_bg, sign=new_sign)
        user_info = user_service.build_user_base_info(user)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {'user': user_info}, 'msg': ''}
        self.jsonify(ret)



