# coding=utf-8
"""
主入口
"""
import time
import asyncio

import ujson
from tornado import ioloop, web
from tornado.httpserver import HTTPServer
from tornado.options import define, parse_command_line, options

from config import config
from cores.base import base_service
from cores.utils import logger
from cores.database import db

# 初始化logger
logger.init_logger(config.PROJECT_NAME)


class MyApplication(web.Application):
    def __init__(self, handlers=None, default_host="", transforms=None, **settings):
        web.Application.__init__(self, handlers, default_host, transforms, **settings)

    def log_request(self, handler):
        # 指定method输出
        if handler.request.method not in ['GET', 'POST']:
            return

        # 未设定logger
        if not hasattr(handler, '_app_logger'):
            super(MyApplication, self).log_request(handler)

        # logger级别
        log_method = logger.info

        # 针对超高频轮询接口，采取随机抛弃打印策略
        high_freq_uris = {
            '/api/center/get_my_badges'
        }
        if handler.request.uri in high_freq_uris and int(time.time()) % 10 > 1:
            return

        # 保存参数信息
        try:
            params_str = ujson.dumps(handler.params)
        except:
            params_str = handler.request.body.decode("utf8")

        # 超时打印
        request_time = int(1000 * handler.request.request_time())
        if request_time >= 1000:
            log_method("%d|%dms(too-long)\t%s █ para: %s\n" % (handler.get_status(), request_time, handler._request_summary(), params_str))
            return

        # 正常输出
        log_method("%d|%dms\t%s █ para: %s\n" % (handler.get_status(), request_time, handler._request_summary(), params_str))


class StaticFileHandler(web.StaticFileHandler):
    """
    静态资源配置
    """
    def set_extra_headers(self, path):
        """For subclass to add extra headers to the response"""
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header("Cache-control", "max-age=2592000")

# 定义环境变量
define('port', default=9801, type=int)


def main():
    # 解析启动命令
    parse_command_line()

    # 导入urls
    from server_app.url.url_app import app_urls
    from server_audit.url.url_audit import audit_urls
    from server_web.url.url_web import web_urls
    all_urls = app_urls
    all_urls.extend(audit_urls)
    all_urls.extend(web_urls)

    # 初始化database
    db.init_redis()
    asyncio.get_event_loop().run_until_complete(asyncio.gather(
        base_service.AioRedisSession.init(),
        db.init_aioredis()
    ))

    # 启动tornado主服务
    app = MyApplication(
        all_urls,
        debug=config.WEB_DEBUG,
        template_path='server_web/template',
        static_path='server_web/static',
        static_handler_class=StaticFileHandler,
    )
    logger.info('%s server listen on %d' % (config.PROJECT_NAME, options.port))
    server = HTTPServer(app, xheaders=True)
    server.bind(options.port, backlog=512)
    server.start()

    ioloop.IOLoop.current().start()
    logger.info('Exit')


if __name__ == '__main__':
    main()


