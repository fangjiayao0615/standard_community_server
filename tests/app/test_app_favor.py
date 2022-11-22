# -*- coding: utf-8 -*-
"""
测试 favor 相关 功能
"""
import unittest

import requests
import tornado
import ujson

from config import config
from cores.const import const_mix, const_err, const_post, const_base
from cores.tag import tag_service
from cores.comment import comment_service
from cores.post import post_service
from tests.base_service import TestCaseEnvUtil, BaseTestCase, TestFuncUtils


class TestFavorFuncs(BaseTestCase):

    @tornado.testing.gen_test
    async def test_favor_user_handlers(self):
        """
        测试 关注用户 handlers
        :return:
        """
        # 创建测试用户
        uid1, name1, session1, nick1 = TestFuncUtils.create_new_login_user_for_test()
        uid2, name2, session2, nick2 = TestFuncUtils.create_new_login_user_for_test()

        # 用户2 关注 用户1
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/follow_user" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session2,
                'uid': uid1,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 用户2 主页 - 1个关注
        rsp = requests.post("http://%s/%s/center/get_user_homepage" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'viewed_uid': uid2,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['uid'], uid2)
        self.assertEqual(res['data']['f_user_num'], 1)
        self.assertEqual(res['data']['fans_num'], 0)
        self.assertEqual(res['data']['fans_to_viewer'], True)
        self.assertEqual(res['data']['favored'], False)

        # 用户1 主页 - 1个fans
        rsp = requests.post("http://%s/%s/center/get_user_homepage" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session2,
            'viewed_uid': uid1,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['f_user_num'], 0)
        self.assertEqual(res['data']['fans_num'], 1)
        self.assertEqual(res['data']['fans_to_viewer'], False)
        self.assertEqual(res['data']['favored'], True)

        # 用户2 取消关注 用户1
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/cancel_follow_user" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session2,
                'uid': uid1,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 用户2 主页 - 1个关注
        rsp = requests.post("http://%s/%s/center/get_user_homepage" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'viewed_uid': uid2,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['uid'], uid2)
        self.assertEqual(res['data']['f_user_num'], 0)
        self.assertEqual(res['data']['fans_num'], 0)
        self.assertEqual(res['data']['fans_to_viewer'], False)
        self.assertEqual(res['data']['favored'], False)

        # 用户1 主页 - 1个fans
        rsp = requests.post("http://%s/%s/center/get_user_homepage" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session2,
            'viewed_uid': uid1,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(res['data']['f_user_num'], 0)
        self.assertEqual(res['data']['fans_num'], 0)
        self.assertEqual(res['data']['fans_to_viewer'], False)
        self.assertEqual(res['data']['favored'], False)

    @tornado.testing.gen_test
    async def test_favor_tag_handlers(self):
        """
        测试 关注标签 handlers
        :return:
        """
        # 创建测试用户
        uid1, name1, session1, nick1 = TestFuncUtils.create_new_login_user_for_test()

        # 创建标签
        tid = await tag_service.create_new_tag('测试标签', {"url": "aaa/bbb.jpg"})

        # 用户关注标签
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/follow_tag" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'tid': tid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查看标签信息
        rsp = requests.post("http://%s/%s/tag/query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'tid': tid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['tid'], tid)
        self.assertEqual(res['data']['list'][0]['favored'], True)
        self.assertEqual(res['data']['list'][0]['favor_num'], 1)

        # 用户取消关注标签
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/cancel_follow_tag" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'tid': tid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查看标签信息
        rsp = requests.post("http://%s/%s/tag/query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'tid': tid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['tid'], tid)
        self.assertEqual(res['data']['list'][0]['favored'], False)
        self.assertEqual(res['data']['list'][0]['favor_num'], 0)

    @tornado.testing.gen_test
    async def test_favor_post_handlers(self):
        """
        测试 关注帖子 handlers
        :return:
        """
        # 创建测试用户
        uid1, name1, session1, nick1 = TestFuncUtils.create_new_login_user_for_test()

        # 创建帖子
        pid, _ = await post_service.create_new_post(uid1, "测试帖子A", const_post.POST_TYPE_NORMAL, raw_imgs=[{"url": "aaa/bbb.jpg", "w": 100, "h": 200, "type": const_base.IMAGE_TYPE_NORMAL}])

        # 用户点赞帖子
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/like_post" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'pid': pid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查看帖子信息
        rsp = requests.post("http://%s/%s/post/user_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'p_uid': uid1,
            'ptype': const_post.POST_TYPE_NORMAL,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['likes'], 1)
        self.assertEqual(res['data']['list'][0]['liked'], True)
        self.assertEqual(res['data']['list'][0]['dislikes'], 0)
        self.assertEqual(res['data']['list'][0]['disliked'], False)

        # 用户取消点赞帖子
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/cancel_like_post" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'pid': pid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查看帖子信息
        rsp = requests.post("http://%s/%s/post/user_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'p_uid': uid1,
            'ptype': const_post.POST_TYPE_NORMAL,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['likes'], 0)
        self.assertEqual(res['data']['list'][0]['liked'], False)
        self.assertEqual(res['data']['list'][0]['dislikes'], 0)
        self.assertEqual(res['data']['list'][0]['disliked'], False)

        # 用户点踩帖子
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/dislike_post" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'pid': pid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查看帖子信息
        rsp = requests.post("http://%s/%s/post/user_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'p_uid': uid1,
            'ptype': const_post.POST_TYPE_NORMAL,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['likes'], 0)
        self.assertEqual(res['data']['list'][0]['liked'], False)
        self.assertEqual(res['data']['list'][0]['dislikes'], 1)
        self.assertEqual(res['data']['list'][0]['disliked'], True)

        # 用户取消点踩帖子
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/cancel_dislike_post" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'pid': pid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查看帖子信息
        rsp = requests.post("http://%s/%s/post/user_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'p_uid': uid1,
            'ptype': const_post.POST_TYPE_NORMAL,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['likes'], 0)
        self.assertEqual(res['data']['list'][0]['liked'], False)
        self.assertEqual(res['data']['list'][0]['dislikes'], 0)
        self.assertEqual(res['data']['list'][0]['disliked'], False)

        # 用户点赞帖子
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/like_post" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'pid': pid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 用户点踩帖子
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/dislike_post" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'pid': pid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查看帖子信息
        rsp = requests.post("http://%s/%s/post/user_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'p_uid': uid1,
            'ptype': const_post.POST_TYPE_NORMAL,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['likes'], 0)
        self.assertEqual(res['data']['list'][0]['liked'], False)
        self.assertEqual(res['data']['list'][0]['dislikes'], 1)
        self.assertEqual(res['data']['list'][0]['disliked'], True)

        # 用户点赞帖子
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/like_post" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'pid': pid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查看帖子信息
        rsp = requests.post("http://%s/%s/post/user_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'p_uid': uid1,
            'ptype': const_post.POST_TYPE_NORMAL,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)
        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['likes'], 1)
        self.assertEqual(res['data']['list'][0]['liked'], True)
        self.assertEqual(res['data']['list'][0]['dislikes'], 0)
        self.assertEqual(res['data']['list'][0]['disliked'], False)

    @tornado.testing.gen_test
    async def test_favor_comment_handlers(self):
        """
        测试 关注评论 handlers
        :return:
        """
        # 创建测试用户
        uid1, name1, session1, nick1 = TestFuncUtils.create_new_login_user_for_test()

        # 创建帖子
        pid, _ = await post_service.create_new_post(uid1, "测试帖子A", const_post.POST_TYPE_NORMAL, raw_imgs=[{"url": "aaa/bbb.jpg", "w": 100, "h": 200, "type": const_base.IMAGE_TYPE_NORMAL}])

        # 创建评论
        cid, _ = await comment_service.create_new_comment(pid, pid, "测试评论A")

        # 点赞评论
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/like_comment" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'cid': cid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查询评论
        rsp = requests.post("http://%s/%s/comment/post_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['cid'], cid)
        self.assertEqual(res['data']['list'][0]['likes'], 1)
        self.assertEqual(res['data']['list'][0]['liked'], True)
        self.assertEqual(res['data']['list'][0]['dislikes'], 0)
        self.assertEqual(res['data']['list'][0]['disliked'], False)

        # 取消点赞评论
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/cancel_like_comment" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'cid': cid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查询评论
        rsp = requests.post("http://%s/%s/comment/post_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['cid'], cid)
        self.assertEqual(res['data']['list'][0]['likes'], 0)
        self.assertEqual(res['data']['list'][0]['liked'], False)
        self.assertEqual(res['data']['list'][0]['dislikes'], 0)
        self.assertEqual(res['data']['list'][0]['disliked'], False)

        # 点踩评论
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/dislike_comment" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'cid': cid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查询评论
        rsp = requests.post("http://%s/%s/comment/post_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['cid'], cid)
        self.assertEqual(res['data']['list'][0]['likes'], 0)
        self.assertEqual(res['data']['list'][0]['liked'], False)
        self.assertEqual(res['data']['list'][0]['dislikes'], 1)
        self.assertEqual(res['data']['list'][0]['disliked'], True)

        # 取消点踩评论
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/cancel_dislike_comment" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'cid': cid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查询评论
        rsp = requests.post("http://%s/%s/comment/post_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['cid'], cid)
        self.assertEqual(res['data']['list'][0]['likes'], 0)
        self.assertEqual(res['data']['list'][0]['liked'], False)
        self.assertEqual(res['data']['list'][0]['dislikes'], 0)
        self.assertEqual(res['data']['list'][0]['disliked'], False)

        # 点赞评论
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/like_comment" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'cid': cid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 点踩评论
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/dislike_comment" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'cid': cid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查询评论
        rsp = requests.post("http://%s/%s/comment/post_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['cid'], cid)
        self.assertEqual(res['data']['list'][0]['likes'], 0)
        self.assertEqual(res['data']['list'][0]['liked'], False)
        self.assertEqual(res['data']['list'][0]['dislikes'], 1)
        self.assertEqual(res['data']['list'][0]['disliked'], True)

        # 点赞评论
        for i in range(0, 2):
            rsp = requests.post("http://%s/%s/favor/like_comment" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
                'session': session1,
                'cid': cid,
            }))
            res = ujson.loads(rsp.content)
            self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        # 查询评论
        rsp = requests.post("http://%s/%s/comment/post_query_list" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({
            'session': session1,
            'pid': pid,
        }))
        res = ujson.loads(rsp.content)
        self.assertEqual(res['ret'], const_err.CODE_SUCCESS)

        self.assertEqual(len(res['data']['list']), 1)
        self.assertEqual(res['data']['list'][0]['cid'], cid)
        self.assertEqual(res['data']['list'][0]['likes'], 1)
        self.assertEqual(res['data']['list'][0]['liked'], True)
        self.assertEqual(res['data']['list'][0]['dislikes'], 0)
        self.assertEqual(res['data']['list'][0]['disliked'], False)

    @tornado.testing.gen_test
    async def test_like_history_handlers(self):
        """
        测试赞踩历史记录接口
        :return: 
        """
        # TODO

    @tornado.testing.gen_test
    async def test_fans_history_to_me(self):
        """
        测试关注历史记录接口
        :return: 
        """
        # TODO


if __name__ == '__main__':
    TestCaseEnvUtil.prepare_server_for_test_cases()

    # 运行全部用例
    unittest.main()

    # 执行指定用例
    # suite = unittest.TestSuite()
    # suite.addTest(TestFavorFuncs("test_favor_comment_handlers"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)
