# -*- coding:utf-8 -*-
import logging
import sys
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
import asyncio
import time
import ujson
import requests
from bson import ObjectId
from tornado import ioloop
from tornado.testing import AsyncTestCase


class BaseTestCase(AsyncTestCase):
    def setUp(self):
        super().setUp()

        # 辅助 buffer log 实现
        # unittest buffer stderr时直接替换sys.stderr，但是 logging 系统构造时就已经绑定了原来的
        # sys.stderr，所以不生效，这里直接帮助把logging用的 stream 换成当前被替换后的sys.stderr
        self._old_log_stream = None
        if len(logging.getLogger().handlers) == 1:
            handler = logging.getLogger().handlers[0]
            if isinstance(handler, logging.StreamHandler):
                handler.flush()
                self._old_log_stream = handler.stream
                handler.stream = sys.stderr

        # 使主线程（测试线程）的 loop 可以一直循环，而不是永远等待不存在的 io 事件
        def waker():
            self.io_loop.call_later(0.001, waker)
        waker()

        # 清空测试数据
        self.clean_all_test_data()

    def tearDown(self):
        # 清空测试数据
        self.clean_all_test_data()

        # 还原logging stream
        if self._old_log_stream:
            handler = logging.getLogger().handlers[0]
            handler.stream = self._old_log_stream

        super().tearDown()

    @classmethod
    def get_test_server_loop(cls):
        # 获取主server的 loop
        global TEST_SERVER_LOOP
        return TEST_SERVER_LOOP

    def run_server_coroutine(self, coro):
        # 阻塞执行任务
        return asyncio.run_coroutine_threadsafe(
            coro,
            self.get_test_server_loop().asyncio_loop
        ).result()

    @classmethod
    def clean_all_test_data(cls):
        """
        清空所有测试环境的垃圾数据
        """
        from config import config
        from cores.database import db

        # 数据库保险
        if '127.0.0.1' not in config.DB_HOST:
            logging.error('测试用数据库不能使用线上数据库！')
            return
        # redis保险
        if '127.0.0.1' not in config.REDIS_HOST:
            logging.error('测试用redis不能使用线上数据库！')
            return

        # 获取所有数据库同步链接
        test_dbs = []
        for method_name in dir(db):
            if method_name.startswith('get_col') and 'motor' not in method_name:
                test_dbs.append(getattr(db, method_name)())

        # 清空数据表
        with ThreadPoolExecutor() as executor:
            for test_db in test_dbs:
                executor.submit(test_db.delete_many, {})

        for db_name in config.ALL_REDIS_DBS:
            rd_db = db.get_redis(db=db_name)
            rd_db.flushdb()


class TestCaseEnvUtil:
    """
    单元测试环境管理类
    """
    # 测试redis子进程
    TEST_REDIS_THREAD_HANDLER = None
    # 测试mongo子进程
    TEST_MONGO_THREAD_HANDLER = None

    @classmethod
    def prepare_server_for_test_cases(cls):
        """
        单元测试环境相关准备：启动测试服务server
        """
        import asyncio
        from tornado.platform.asyncio import AnyThreadEventLoopPolicy
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

        # 子线程方式启动 main 接口
        test_server_thread = TServerThread('son_test_thread')
        test_server_thread.setDaemon(True)
        test_server_thread.start()
        time.sleep(1)
        global TEST_SERVER_READY
        if not TEST_SERVER_READY:
            return False

        # 启动 redis-server
        cls.TEST_REDIS_THREAD_HANDLER = subprocess.Popen('redis-server', shell=True, stdout=subprocess.PIPE)

        # 启动 mongo-server
        cls.TEST_MONGO_THREAD_HANDLER = subprocess.Popen('mongod --config /usr/local/etc/mongod.conf', shell=True, stdout=subprocess.PIPE)

        time.sleep(1)
        return True

    @classmethod
    def close_server_for_test_cases(cls):
        """
        退出测试时管理相关服务
        """

        try:
            cls.TEST_MONGO_THREAD_HANDLER.kill()
        except Exception:
            pass

        try:
            cls.TEST_REDIS_THREAD_HANDLER.kill()
        except Exception:
            pass


# 测试主服务成功标志位
TEST_SERVER_READY = True
# 当前主服务子进程
TEST_SERVER_LOOP = None


class TServerThread(threading.Thread):
    """
    单元测试环境下的主服务子线程
    """

    def __init__(self, thread_name):
        threading.Thread.__init__(self, name=thread_name)

    def run(self):
        global TEST_SERVER_LOOP
        TEST_SERVER_LOOP = ioloop.IOLoop.current()

        # 优先调用 motor 将 loop 绑到本线程, 否则主线程的在测试时会阻塞.
        from cores.database import db
        db.get_motordb_col_app_conf()

        try:
            # 初始化主服务
            from main import main
            from tornado.options import options
            from config import config
            options.port = config.TEST_PORT
            main()

        except Exception as e:
            global TEST_SERVER_READY
            TEST_SERVER_READY = False
            logging.error("failed to start test-server", str(e))


class TestFuncUtils:
    """
    测试使用常用方法
    """

    @classmethod
    def create_new_login_user_for_test(cls, utype=None, invite_code='', h_dt=None, h_did=None, h_av=None):
        """
        创建新测试用户并登录
        :return:
        """
        from config import config
        from cores.base import base_service
        from cores.database import db
        from cores.const import const_mix

        # 基本信息
        pwd = '1234567'
        h_did2 = base_service.get_random_str(seed='0123456789')
        name = '86-158%s' % h_did2

        # 验证码
        requests.post("http://%s/%s/account/send_code" % (config.TEST_HOST, const_mix.URL_NAME_APP), data=ujson.dumps({'name': name}))
        verification_code = db.default_rd_cli.get(base_service.build_verification_code_rd_key(name))

        # 注册
        rsp = requests.post("http://%s/%s/account/register" % (config.TEST_HOST,  const_mix.URL_NAME_APP), data=ujson.dumps({
            'name': name,
            'pwd': pwd,
            'code': verification_code,
            'invite_code': invite_code,
            'h_did': h_did or h_did2,
            'h_dt': h_dt,
            'h_av': h_av,
        }))
        res = ujson.loads(rsp.content)
        uid = res['data']['uid']
        nick = res['data']['nick']
        session = res['data']['session']

        # 获取用户信息
        user_col = db.get_col_user()
        name = user_col.find_one({'nick': nick})['name']
        if utype is not None:
            col_user = db.get_col_user()
            col_user.update_one({'_id': ObjectId(uid)}, {'$set': {'utypes': [utype]}})

        return uid, name, session, nick


