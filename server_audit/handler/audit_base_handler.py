# coding=utf-8
"""
基础 handler、功能单一 handler
"""
import logging
import ujson
from datetime import datetime
import traceback
from functools import wraps

from tornado import web

from config import config
from cores.const import const_err, const_user
from server_audit.service.audit_base_service import AdminRedisSession


class AuditBaseHandler(web.RequestHandler):
    _label = 'AuditBaseHandler'
    _app_logger = logging.getLogger(config.PROJECT_NAME)

    def __init__(self, application, request, **kwargs):
        web.RequestHandler.__init__(self, application, request, **kwargs)
        self.session = None
        self.admin_uid = None
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
                # str_all = self.request.body.replace("\r\n\r\n", "\r\n")
                # self.params = str_all.split("\r\n")
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

    def on_finish(self):
        pass

    def jsonify(self, response):
        if self.session and self.session.get('sid'):
            self.set_cookie('session', self.session['sid'])
        self.set_header('Cache-Control', 'private')
        self.set_header('Date', datetime.now())
        self.set_header('Access-Control-Allow-Origin', '*')
        if getattr(config, 'RSP_LOG', False):
            self.response = response
        response = ujson.dumps(response, ensure_ascii=False)
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        self.write(response)
        self.finish()

    def html_response(self, template_name, cache, **kwargs):
        if cache:
            self.set_header('Cache-Control', 'public, max-age=86400')
        else:
            self.set_header('Cache-Control', 'no-cache')
        self.set_header('Date', datetime.now())
        self.set_header('Content-Type', 'text/html; charset=utf-8')

        self.render(template_name, **kwargs)

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
            pass
            # msg = "".join(traceback.format_exception(*kwargs.get("exc_info")))
            # msg += "uri:%s\nbody:%s\nfrom:%s" % (config.PROJECT_OP_NAME, self.request.uri, self.params)
            # sync_call_dingding(config.url_dingding_alarm_notify, msg)
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

    @staticmethod
    def check_permission(need_login=True):
        """
        权限验证
        :param need_login: True: 强制登录检测，没登录侧不许访问接口；False 非强制登录
        :return:
        """
        def decorator(func):
            @wraps(func)
            def wrapper(self):
                sid = self.params.get('session', '')

                # 爬虫机器人
                if sid == const_user.SPIDER_ROB_ADMIN_SID:
                    self.admin_uid = sid
                    return func(self)

                # 判断登录状态
                session_info = AdminRedisSession.open_session(sid) if sid else {}
                if need_login and not session_info:
                    self.jsonify({'ret': const_err.CODE_SESSION_ERROR, 'data': {}, 'msg': const_err.errmsg.get(const_err.CODE_SESSION_ERROR)})
                    return

                # 已删除
                from server_audit.service import audit_admin_service
                admin = audit_admin_service.sync_get_admin_info_by_admin_id(session_info['admin_uid'])
                if not admin or admin.get('deleted'):
                    self.jsonify({'ret': const_err.CODE_SESSION_ERROR, 'data': {}, 'msg': const_err.errmsg.get(const_err.CODE_SESSION_ERROR)})
                    return

                # 验证通过
                AdminRedisSession.expire_session(sid, config.AUDIT_SESSION_EXT)
                self.admin_uid = session_info['admin_uid']
                self.session = session_info
                return func(self)
            return wrapper

        return decorator

    def jsonify_err(self, ret, msg=''):
        response = {
            'ret': ret,
            'data': {},
            'msg': msg or const_err.errmsg.get(ret)
        }
        self.jsonify(response)

