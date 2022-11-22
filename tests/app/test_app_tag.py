# -*- coding: utf-8 -*-
"""
测试 tag 相关 功能
"""
import unittest

import requests
import tornado
import ujson

from bson import ObjectId

from config import config
from cores.const import const_err, const_mix
from cores.database import db
from tests.base_service import TestCaseEnvUtil, BaseTestCase, TestFuncUtils


class TestTagFuncs(BaseTestCase):

    @tornado.testing.gen_test
    async def test_tag_base_handlers(self):
        """
        测试标签基本 handlers
        :return:
        """
        # 创建测试用户
        uid, name, session, nick = TestFuncUtils.create_new_login_user_for_test()

        # 用户创建标签
        tag_name = "aabccc"
        rsp = requests.post("http://%s/%s/tag/create" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'name': tag_name,
            'raw_cover': {"url": "aaa/bbb.jpg"},
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        tid = res['data']['tid']

        tag_col = db.get_col_tag()
        tag = tag_col.find_one({'_id': ObjectId(tid)})
        self.assertEqual(tag['name'], tag_name)

        # 用户查看标签
        rsp = requests.post("http://%s/%s/tag/query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'tid': tid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['tid'], tid)


if __name__ == '__main__':
    TestCaseEnvUtil.prepare_server_for_test_cases()

    # 运行全部用例
    unittest.main(buffer=True)

    # 执行指定用例
    # suite = unittest.TestSuite()
    # suite.addTest(TestAccountFuncs("test_tag_base_handlers"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

