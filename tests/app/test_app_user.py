# -*- coding: utf-8 -*-
"""
测试 user 相关 功能
"""
import unittest

import requests
import time
import tornado
import ujson

from bson import ObjectId

from config import config
from cores.const import const_err, const_user, const_mix
from cores.database import db
from server_app.handler.user_handler import SendVerificationCodeHandler
from cores.base import base_service
from tests.base_service import BaseTestCase, TestCaseEnvUtil, TestFuncUtils
from cores.utils import redis_lock


class TestAccountFuncs(BaseTestCase):

    @tornado.testing.gen_test
    async def test_account_guest_register_handlers(self):
        """
        测试账户基本 handlers
        :return:
        """
        # 游客身份登录
        h_did = 'abcdefghijklmn'
        rsp = requests.post("http://%s/%s/account/guest_register" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'h_did': h_did,
            'h_carrier': 'Vodafone IN,in,405840',
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        uid = res['data']['uid']
        user_col = db.get_col_user()
        user = user_col.find_one({'_id': ObjectId(uid)})
        self.assertTrue(h_did in user['name'])
        self.assertTrue(bool(user['nick']))
        self.assertEqual(user['utypes'], [const_user.USER_TYPE_GUEST])
        self.assertEqual(user['h_carrier'], 'Vodafone IN,in,405840')

        session_id = res['data']['session']
        session_info = self.run_server_coroutine(base_service.AioRedisSession.open_session(session_id))
        self.assertEqual(session_info['uid'], uid)

        # 发送验证码
        name = '86-15888888888'
        # 清除发送计数
        count_rd_key = base_service.build_verification_code_count_rd_key(name)
        db.default_rd_cli.delete(count_rd_key)
        # 清除验证码缓存
        code_rd_key = base_service.build_verification_code_rd_key(name)
        db.default_rd_cli.delete(code_rd_key)
        # 触发发送
        rsp = requests.post("http://%s/%s/account/send_code" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'name': name
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(int(db.default_rd_cli.get(count_rd_key)), 1)
        verification_code = db.default_rd_cli.get(code_rd_key)
        self.assertTrue(bool(verification_code))

        # 游客用户注册, 覆盖掉游客用户。
        pwd = '1234567'
        rsp = requests.post("http://%s/%s/account/register" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'name': name,
            'pwd': pwd,
            'code': verification_code,
            'h_did': h_did,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        new_uid = res['data']['uid']
        user_col = db.get_col_user()
        user = user_col.find_one({'_id': ObjectId(new_uid)})
        self.assertEqual(new_uid, uid)
        self.assertTrue(name in user['name'])
        self.assertEqual(user['utypes'], [const_user.USER_TYPE_NORMAL])

        session_id = res['data']['session']
        session_info = self.run_server_coroutine(base_service.AioRedisSession.open_session(session_id))
        self.assertEqual(session_info['uid'], new_uid)

        # 游客用户注册, - 失败 频率过高
        name2 = '86-15888883344'
        requests.post("http://%s/%s/account/send_code" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'name': name2
        }))
        code_rd_key2 = base_service.build_verification_code_rd_key(name2)
        verification_code2 = db.default_rd_cli.get(code_rd_key2)
        rsp = requests.post("http://%s/%s/account/register" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'name': name2,
            'pwd': pwd,
            'code': verification_code2,
            'h_did': h_did,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_REG_CREATE_QUICKLY_ERROR)

        # 用户登出
        rsp = requests.post("http://%s/%s/account/logout" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'h_did': h_did,
            'session': session_id,
            'h_zone_name': 'Asia/Shanghai',
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        new_guest_uid = res['data']['uid']
        user_col = db.get_col_user()
        user = user_col.find_one({'_id': ObjectId(new_guest_uid)})
        self.assertTrue(h_did in user['name'])
        self.assertTrue(uid != new_guest_uid)

        session_id = res['data']['session']
        session_info = self.run_server_coroutine(base_service.AioRedisSession.open_session(session_id))
        self.assertEqual(session_info['uid'], new_guest_uid)

        # 用户重置密码
        redis_lock.user_redis_unlock(name, SendVerificationCodeHandler._label)
        requests.post("http://%s/%s/account/send_code" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'name': name
        }))
        verification_code = db.default_rd_cli.get(code_rd_key)
        pwd2 = '787878787878'
        rsp = requests.post("http://%s/%s/account/reset" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'name': name,
            'pwd': pwd2,
            'code': verification_code,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        uid = res['data']['uid']
        user = user_col.find_one({'_id': ObjectId(uid)})
        self.assertEqual(pwd2, user['passwd'])

        # 用户登录 - 使用新密码
        rsp = requests.post("http://%s/%s/account/login" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'name': name,
            'h_did': "abcdefg",
            'pwd': pwd2,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        uid = res['data']['uid']
        session_id = res['data']['session']
        session_info = self.run_server_coroutine(base_service.AioRedisSession.open_session(session_id))
        self.assertEqual(session_info['uid'], uid)

    @tornado.testing.gen_test
    async def test_account_direct_register_handlers(self):
        """
        测试账户 直接注册 handlers
        :return:
        """

        # 非游客纯新用户注册
        pwd = '1234567'
        h_did2 = 'klsjhdflkjshd'
        name2 = '86-15888888881'
        # 发送验证码
        requests.post("http://%s/%s/account/send_code" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'name': name2
        }))
        verification_code = db.default_rd_cli.get(base_service.build_verification_code_rd_key(name2))

        # 直接注册
        rsp = requests.post("http://%s/%s/account/register" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'name': name2,
            'pwd': pwd,
            'code': verification_code,
            'h_did': h_did2,
        }))
        time.sleep(0.1)
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        uid2 = res['data']['uid']
        user_col = db.get_col_user()
        user = user_col.find_one({'_id': ObjectId(uid2)})
        self.assertTrue(name2 in user['name'])
        self.assertEqual(user['utypes'], [const_user.USER_TYPE_NORMAL])

    @tornado.testing.gen_test
    async def test_account_update_handlers(self):
        """
        测试账户 更新功能 handlers
        :return:
        """
        # 创建测试用户
        uid, name, session, nick = TestFuncUtils.create_new_login_user_for_test()

        # 用户重置个人信息 - 失败，昵称太短
        rsp = requests.post("http://%s/%s/account/update" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'nick': '你a',
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_NICK_TOO_SHORT_ERROR)

        # 用户重置个人信息
        rsp = requests.post("http://%s/%s/account/update" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'nick': '11111',
            'sign': '222',
            'raw_avatar': {'url': '333'},
            'raw_bg': {'url': '444'},
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 更新成功
        user_col = db.get_col_user()
        user = user_col.find_one({'_id': ObjectId(uid)})
        self.assertEqual(user['nick'], '11111')
        self.assertEqual(user['sign'], '222')
        self.assertTrue('333' in user['raw_avatar']['url'])
        self.assertTrue('444' in user['raw_bg']['url'])

    @tornado.testing.gen_test
    async def test_account_vc_check_handlers(self):
        """
        测试账户 验证码校验 handlers
        :return:
        """
        # 创建测试用户
        uid, name, session, nick = TestFuncUtils.create_new_login_user_for_test()

        # 发送验证码
        # 清除发送计数
        count_rd_key = base_service.build_verification_code_count_rd_key(name)
        db.default_rd_cli.delete(count_rd_key)
        # 清除验证码缓存
        code_rd_key = base_service.build_verification_code_rd_key(name)
        db.default_rd_cli.delete(code_rd_key)
        # 触发发送
        redis_lock.user_redis_unlock(name, SendVerificationCodeHandler._label)
        rsp = requests.post("http://%s/%s/account/send_code" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(int(db.default_rd_cli.get(count_rd_key)), 1)
        verification_code = db.default_rd_cli.get(code_rd_key)
        self.assertTrue(bool(verification_code))

        # 检验验证码
        rsp = requests.post("http://%s/%s/account/valid_code" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'h_did': "123",
            'code': verification_code,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)


if __name__ == '__main__':
    TestCaseEnvUtil.prepare_server_for_test_cases()

    # 运行全部用例
    unittest.main()

    # 执行指定用例
    # suite = unittest.TestSuite()
    # suite.addTest(TestAccountFuncs("test_account_guest_register_handlers"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)
