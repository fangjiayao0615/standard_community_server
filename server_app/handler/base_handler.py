# -*- coding:utf-8 -*-
"""
基础功能 handler
"""
import logging
import random
import traceback
import ujson

from datetime import datetime
from functools import wraps
from inspect import isawaitable

from jsonschema import ValidationError
from tornado import web
from tornado.web import StaticFileHandler
from tornado.ioloop import IOLoop

from config import config, ENV
from cores.const import const_err
from cores.base import base_service
from cores.user import user_service
from cores.base.base_service import AioRedisSession


class BaseHandler(web.RequestHandler):
    """
    handler 基础类 主要负责登录校验、异常捕获、通用消息处理等功能
    """
    _label = 'BaseHandler'
    _app_logger = logging.getLogger(config.PROJECT_NAME)

    def __init__(self, application, request, **kwargs):
        web.RequestHandler.__init__(self, application, request, **kwargs)
        self.session = None
        self.uid = None
        self.user_agent = None
        self.params = {}
        self.response = {}

    def head(self, *args, **kwargs):
        self.get(*args, **kwargs)

    def prepare(self):
        if 'User-Agent' in self.request.headers:
            self.user_agent = self.request.headers['User-Agent'].lower()
            content_type = self.request.headers.get("Content-Type", '')
            if content_type.find('multipart/form-data') > -1:
                pass
            else:
                if not self.request.body:
                    self.request.body = ''
                if len(self.request.body) > 1:
                    try:
                        self.params = ujson.loads(self.request.body)
                    except ValueError:
                        self.params = {}
        else:
            if not self.request.body:
                self.request.body = ''
            if len(self.request.body) > 1:
                try:
                    self.params = ujson.loads(self.request.body)
                except ValueError:
                    self.params = {}
        # remote_ip
        try:
            self.params['request_remote_ip'] = self.request.remote_ip
        except:
            pass

    def on_finish(self):
        pass

    def jsonify(self, response):
        if self.session and self.session.get('sid'):
            self.set_cookie('session', self.session['sid'])
        self.set_header('Cache-Control', 'private')
        self.set_header('Date', datetime.now())
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        self.write(response)
        self.finish()

    def jsonify_err(self, ret, msg=''):
        response = {
            'ret': ret,
            'data': {},
            'msg': msg or const_err.errmsg.get(ret)
        }
        self.jsonify(response)

    def html_response(self, template_name, cache, **kwargs):
        if cache:
            self.set_header('Cache-Control', 'public, max-age=2592000')
        else:
            self.set_header('Cache-Control', 'no-cache')
        self.set_header('Date', datetime.now())
        self.set_header('Content-Type', 'text/html; charset=utf-8')

        self.render(template_name, **kwargs)

    def send_error(self, status_code=500, **kwargs):
        if 'exc_info' in kwargs:
            exception = kwargs['exc_info'][1]
            if isinstance(exception, ValidationError):
                err = const_err.CODE_PARAM_ERROR
                msg = const_err.errmsg.get(err, '')
                if self.settings.get("serve_traceback"):
                    msg += ': ' + str(exception)
                self.jsonify_err(err, msg)
                return
        return super().send_error(status_code, **kwargs)

    def write_error(self, status_code, **kwargs):
        """Override to implement custom error pages.

        ``write_error`` may call `write`, `render`, `set_header`, etc
        to produce output as usual.

        If this error was caused by an uncaught exception (including
        HTTPError), an ``exc_info`` triple will be available as
        ``kwargs["exc_info"]``.  Note that this exception may not be
        the "current" exception for purposes of methods like
        ``sys.exc_info()`` or ``traceback.format_exc``.
        """
        if "exc_info" in kwargs and status_code >= 500:
            # TODO: 报警通知
            pass
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            self.set_header('Content-Type', 'text/plain')
            for line in traceback.format_exception(*kwargs["exc_info"]):
                self.write(line)
            self.finish()
        else:
            self.finish("<html><title>%(code)d: %(message)s</title>"
                        "<body>%(code)d: %(message)s</body></html>" % {
                            "code": status_code,
                            "message": self._reason,
                        })

    @classmethod
    def label(cls):
        return cls._label

    @staticmethod
    def check_permission(need_login=True, need_normal_user=False):
        """
        权限验证
        :param need_login: True: 强制登录检测，没登录侧不许访问接口；False 非强制登录
        :param need_normal_user: True: 强制登录检测且是正式用户；False 非强制正式用户
        :return:
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(self):
                sid = self.params.get('session', '')

                # 尝试从URL里面获取session信息
                if not sid:
                    header_str = self.get_argument('header', '{}')
                    try:
                        header_info = ujson.loads(header_str)
                    except:
                        header_info = {}
                    sid = header_info.get('session', '')

                # 保存用户基本信息
                session_info = await AioRedisSession.open_session(sid) if sid else {}
                if session_info:
                    self.uid = session_info['uid']
                    self.session = session_info
                    IOLoop.current().add_callback(self.extend_session_if_needed, self.uid, sid)

                # 要求登录
                if need_login and not session_info:
                    self.jsonify_err(const_err.CODE_SESSION_ERROR)
                    return

                # 要求正式用户身份登录
                if need_login and need_normal_user:
                    if not session_info or base_service.is_guest(session_info.get('user', {})):
                        self.jsonify_err(const_err.CODE_PERMISSION_GUEST_FAILED)
                        return

                # 验证通过则执行相关逻辑
                ret = func(self)

                # 兼容异步/同步调用
                if isawaitable(ret):
                    return await ret
                else:
                    return ret

            return wrapper

        return decorator

    async def extend_session_if_needed(self, uid, sid):
        """
        10% 概率自动延长 session
        """
        if random.random() > 0.9:
            return
        ttl = await AioRedisSession.get_session_ttl(sid)
        if ttl <= max(int(config.USER_SESSION_EXT) - 86400, 0):
            user_info = await user_service.get_user_info(uid=uid)
            if not user_info:
                return
            await AioRedisSession.save_session_by_user_info(uid, sid, user_info)

            # 更新关联设备
            # TODO update_user_device_info_by_uid
            pass

    def static_url(self, path, include_host=None, **kwargs):
        """Returns a static URL for the given relative static file path.

        This method requires you set the ``static_path`` setting in your
        application (which specifies the root directory of your static
        files).

        This method returns a versioned url (by default appending
        ``?v=<signature>``), which allows the static files to be
        cached indefinitely.  This can be disabled by passing
        ``include_version=False`` (in the default implementation;
        other static file implementations are not required to support
        this, but they may support other options).

        By default this method returns URLs relative to the current
        host, but if ``include_host`` is true the URL returned will be
        absolute.  If this handler has an ``include_host`` attribute,
        that value will be used as the default for all `static_url`
        calls that do not pass ``include_host`` as a keyword argument.

        """
        self.require_setting("static_path", "static_url")
        get_url = self.settings.get("static_handler_class",
                                    StaticFileHandler).make_static_url

        if ENV == 'production':
            base = self.request.protocol + "://" + config.PROJECT_WEB_CDN_DOMAIN
        else:
            if include_host is None:
                include_host = getattr(self, "include_host", False)

            if include_host:
                base = self.request.protocol + "://" + self.request.host
            else:
                base = ""

        return base + get_url(self.settings, path, **kwargs)

