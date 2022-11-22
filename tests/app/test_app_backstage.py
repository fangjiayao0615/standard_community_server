# -*- coding: utf-8 -*-
"""
测试 backstage 相关 功能
"""
import unittest

import requests
import tornado
import ujson

from config import config
from cores.const import const_mix, const_err
from tests.base_service import TestCaseEnvUtil, BaseTestCase, TestFuncUtils


class TestBackstageFuncs(BaseTestCase):

    @tornado.testing.gen_test
    async def test_backstage_base_handlers(self):
        """
        测试 backstage handlers
        :return:
        """
        # 创建测试用户
        uid, name, session, nick = TestFuncUtils.create_new_login_user_for_test()

        # 删除评论
        rsp = requests.post("http://%s/%s/backstage/get_app_conf" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(res['data']['ios_in_review'], False)
        self.assertEqual(res['data']['android_in_review'], False)

    @tornado.testing.gen_test
    async def test_backstage_heartbeat_handlers(self):
        """
        测试 heartbeat 检测 handlers
        :return:
        """

        # post检查
        rsp = requests.post("http://%s/%s/heartbeat" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # get检查
        rsp = requests.get("http://%s/%s/heartbeat" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)


if __name__ == '__main__':
    TestCaseEnvUtil.prepare_server_for_test_cases()

    # 运行全部用例
    unittest.main(buffer=True)

    # 执行指定用例
    # suite = unittest.TestSuite()
    # suite.addTest(TestBackstageFuncs("test_backstage_base_handlers"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)




