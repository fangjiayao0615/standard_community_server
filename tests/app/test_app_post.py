# -*- coding: utf-8 -*-
"""
测试 tag 相关 功能
"""
import unittest

import requests
import time
import tornado
import ujson

from bson import ObjectId

from config import config
from cores.const import const_err, const_mix, const_base, const_post
from cores.database import db
from server_app.handler.post_handler import PostCreateHandler
from cores.tag import tag_service
from tests.base_service import TestCaseEnvUtil, BaseTestCase, TestFuncUtils
from cores.utils import redis_lock


class TestPostFuncs(BaseTestCase):

    @tornado.testing.gen_test
    async def test_post_base_handlers(self):
        """
        测试帖子基本 handlers
        :return:
        """
        # 创建测试用户
        uid, name, session, nick = TestFuncUtils.create_new_login_user_for_test()

        # 创建话题标签
        tid = await tag_service.create_new_tag('测试标签', {"url": "aaa/bbb.jpg"})

        # 创建帖子
        rsp = requests.post("http://%s/%s/post/create" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'tids': [tid],
            'title': "测试标题A",
            'text': "测试内容A",
            'ptype': const_post.POST_TYPE_NORMAL,
            'raw_imgs': [{"url": "aaa/bbb.jpg", "w": 100, "h": 200, "type": const_base.IMAGE_TYPE_NORMAL}],
            'raw_articles': [{"url": "aaa/bbb.jpg", "w": 100, "h": 200, "type": const_base.IMAGE_TYPE_NORMAL}],
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        pid = res['data']['pid']
        post_col = db.get_col_post()
        post = post_col.find_one({'_id': ObjectId(pid)})
        self.assertEqual(post['status'], const_post.POST_STATUS_VISIBLE)
        self.assertEqual(post['ptype'], const_post.POST_TYPE_NORMAL)

        # 查看帖子列表 - 用户页面查询
        rsp = requests.post("http://%s/%s/post/user_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'p_uid': uid,
            'ptype': const_post.POST_TYPE_NORMAL,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)

        # 查看帖子列表 - 标签页面查询
        rsp = requests.post("http://%s/%s/post/tag_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'tid': tid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)

        # 查看帖子详情
        rsp = requests.post("http://%s/%s/post/detail" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['pid'], pid)
        self.assertEqual(res['data']['user']['uid'], uid)

        # 自己删除帖子
        rsp = requests.post("http://%s/%s/post/delete" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查看帖子列表 - 用户页面查询 - 空
        rsp = requests.post("http://%s/%s/post/user_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'p_uid': uid,
            'ptype': const_post.POST_TYPE_NORMAL,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 0)

        # 查看帖子列表 - 标签页面查询 - 空
        rsp = requests.post("http://%s/%s/post/tag_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'tid': tid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 0)

        # 查看帖子详情 - 只有简单字段
        rsp = requests.post("http://%s/%s/post/detail" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['pid'], pid)
        self.assertEqual(ujson.dumps(res['data']['user']), '{}')

    @tornado.testing.gen_test
    async def test_post_recommend_handlers_v1(self):
        """
        测试帖子推荐 handlers
        :return:
        """
        # 创建测试用户
        uid, name, session, nick = TestFuncUtils.create_new_login_user_for_test()

        # 创建话题标签
        tid = await tag_service.create_new_tag('测试标签', {"url": "aaa/bbb.jpg"})

        # 创建帖子
        rsp = requests.post("http://%s/%s/post/create" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'tids': [tid],
            'title': "测试标题A",
            'text': "测试内容A",
            'ptype': const_post.POST_TYPE_NORMAL,
            'raw_imgs': [{"url": "aaa/bbb.jpg", "w": 100, "h": 200, "type": const_base.IMAGE_TYPE_NORMAL}],
            'raw_articles': [{"url": "aaa/bbb.jpg", "w": 100, "h": 200, "type": const_base.IMAGE_TYPE_NORMAL}],
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        pid = res['data']['pid']

        # 修改帖子至推荐状态
        col_post = db.get_col_post()
        col_post.update({'_id': ObjectId(pid)}, {'$set': {"status": const_post.POST_STATUS_REC, 'rt': int(time.time())}})

        # 用户获取推荐流帖子
        rsp = requests.post("http://%s/%s/post/recommend_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['list'][0]['pid'], pid)

        # 产生历史浏览记录
        col_his = db.get_col_post_recommend_history()
        his = col_his.find_one({'pid': pid})
        self.assertEqual(his['pid'], pid)

        # 用户获取推荐流帖子 - 为空
        rsp = requests.post("http://%s/%s/post/recommend_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 0)

        # 新增推荐贴2
        redis_lock.user_redis_unlock(uid, PostCreateHandler._label)
        rsp = requests.post("http://%s/%s/post/create" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
            'tids': [tid],
            'title': "测试标题B",
            'text': "测试内容B",
            'ptype': const_post.POST_TYPE_NORMAL,
            'raw_imgs': [{"url": "aaa/bbb.jpg", "w": 100, "h": 200, "type": const_base.IMAGE_TYPE_NORMAL}],
            'raw_articles': [{"url": "aaa/bbb.jpg", "w": 100, "h": 200, "type": const_base.IMAGE_TYPE_NORMAL}],
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        pid2 = res['data']['pid']
        # 新增推荐贴2
        col_post.update({'_id': ObjectId(pid2)}, {'$set': {"status": const_post.POST_STATUS_REC, 'rt': int(time.time())}})

        # 用户获取推荐流帖子
        rsp = requests.post("http://%s/%s/post/recommend_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['list'][0]['pid'], pid2)

        # 强制获取最近推荐历史记录
        rsp = requests.post("http://%s/%s/post/history_recommend_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        actual_pids = set([p['pid'] for p in res['data']['list']])
        self.assertTrue(pid in actual_pids)
        self.assertTrue(pid2 in actual_pids)

if __name__ == '__main__':
    TestCaseEnvUtil.prepare_server_for_test_cases()

    # 运行全部用例
    # unittest.main(buffer=True)

    # 执行指定用例
    suite = unittest.TestSuite()
    suite.addTest(TestPostFuncs("test_post_recommend_handlers_v1"))
    runner = unittest.TextTestRunner()
    runner.run(suite)

