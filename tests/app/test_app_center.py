# -*- coding: utf-8 -*-
"""
测试 center 相关 功能
"""
import unittest

import requests
import tornado
import ujson

from config import config
from cores.const import const_mix, const_err
from cores.center import center_service
from tests.base_service import TestCaseEnvUtil, BaseTestCase, TestFuncUtils


class TestBackstageFuncs(BaseTestCase):

    @tornado.testing.gen_test
    async def test_backstage_base_handlers(self):
        """
        测试 backstage handlers
        :return:
        """
        # 创建测试用户
        uid1, name1, session1, nick1 = TestFuncUtils.create_new_login_user_for_test()
        uid2, name2, session2, nick2 = TestFuncUtils.create_new_login_user_for_test()

        # 用户1 查看 用户2主页
        rsp = requests.post("http://%s/%s/center/get_user_homepage" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'viewed_uid': uid2,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['uid'], uid2)

        # 用户1 查看 自己主页
        rsp = requests.post("http://%s/%s/center/get_my_homepage" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['uid'], uid1)

        # 查看小红点信息
        rsp = requests.post("http://%s/%s/center/get_my_badges" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['new_likes_to_me'], 0)
        self.assertEqual(res['data']['new_cmt_to_me'], 0)
        self.assertEqual(res['data']['new_fans_to_me'], 0)
        self.assertEqual(res['data']['new_notices_to_me'], 0)

        # 创建系统通知
        nid = await center_service.create_new_notice(const_mix.NOTICE_TYPE_SYS, const_mix.NOTICE_STATUS_VISIBLE, "测试标题A")

        # 查看系统通知列表
        rsp = requests.post("http://%s/%s/center/get_my_notices" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'ntypes': [const_mix.NOTICE_TYPE_SYS],
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['nid'], nid)


if __name__ == '__main__':
    TestCaseEnvUtil.prepare_server_for_test_cases()

    # 运行全部用例
    unittest.main(buffer=True)

    # 执行指定用例
    # suite = unittest.TestSuite()
    # suite.addTest(TestBackstageFuncs("test_backstage_base_handlers"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)
