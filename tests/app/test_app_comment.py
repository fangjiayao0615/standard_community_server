# -*- coding: utf-8 -*-
"""
测试 comment 相关 功能
"""
import unittest

import requests
import tornado
import ujson

from bson import ObjectId

from config import config
from cores.const import const_post, const_mix, const_base, const_err, const_cmt
from cores.database import db
from cores.post import post_service
from tests.base_service import TestCaseEnvUtil, BaseTestCase, TestFuncUtils


class TestCommentFuncs(BaseTestCase):

    @tornado.testing.gen_test
    async def test_comment_base_handlers(self):
        """
        测试评论基本 handlers
        :return:
        """
        # 创建测试用户
        uid, name, session, nick = TestFuncUtils.create_new_login_user_for_test()

        # 创建话题标签
        pid, _ = await post_service.create_new_post(uid, '测试帖子', const_post.POST_TYPE_NORMAL)

        # 创建评论
        rsp = requests.post("http://%s/%s/comment/create" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'pid': pid,
            'text': "测试内容A",
            'ctype': const_cmt.COMMENT_TYPE_NORMAL,
            'raw_imgs': [{"url": "aaa/bbb.jpg", "w": 100, "h": 200, "type": const_base.IMAGE_TYPE_NORMAL}],
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        cid = res['data']['cid']
        cmt_col = db.get_col_comment()
        comment = cmt_col.find_one({'_id': ObjectId(cid)})
        self.assertEqual(comment['pid'], pid)

        # 查询评论
        rsp = requests.post("http://%s/%s/comment/post_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['cid'], cid)

        # 查询帖子
        rsp = requests.post("http://%s/%s/post/user_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'p_uid': uid,
            'ptype': const_post.POST_TYPE_NORMAL,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['cmts'], 1)

        # 删除评论
        rsp = requests.post("http://%s/%s/comment/delete" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'cid': cid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查询帖子
        rsp = requests.post("http://%s/%s/post/user_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'p_uid': uid,
            'ptype': const_post.POST_TYPE_NORMAL,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['cmts'], 0)

        # 查询评论 - 空
        rsp = requests.post("http://%s/%s/comment/post_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 0)


if __name__ == '__main__':
    TestCaseEnvUtil.prepare_server_for_test_cases()

    # 运行全部用例
    unittest.main(buffer=True)

    # 执行指定用例
    # suite = unittest.TestSuite()
    # suite.addTest(TestCommentFuncs("test_comment_base_handlers"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)


