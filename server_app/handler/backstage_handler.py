# coding=utf-8
"""
后台服务相关 handler
"""
import ujson

from cores.const import const_err, const_mix
from server_app.handler.base_handler import BaseHandler
from cores.user import user_service
from cores.backstage import backstage_service
from config import config


class GetAppConfHandler(BaseHandler):
    """
    获取客户端配置项
    """
    _label = 'GetAppConfHandler'

    @BaseHandler.check_permission(need_login=False)
    async def post(self):

        # 获取配置文件
        result = const_mix.get_app_conf()

        # OSS相关信息
        result['oss_conf'] = backstage_service.get_oss_conf()

        # 当前域名
        result['host'] = config.PROJECT_HOST

        ret = {'ret': const_err.CODE_SUCCESS, 'data': result, 'msg': ''}
        self.jsonify(ret)


class HeartBeatHandler(BaseHandler):
    """
    心跳检测服务
    """
    _label = 'HeartBeatHandler'

    @BaseHandler.check_permission(need_login=False)
    async def post(self):
        ret = {'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': 'hello world'}
        self.jsonify(ret)

    @BaseHandler.check_permission(need_login=False)
    def get(self):
        ret = {'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': 'hello world'}
        self.jsonify(ret)

    @BaseHandler.check_permission(need_login=False)
    def head(self):
        ret = {'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': 'hello world'}
        content = ujson.dumps(ret)
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        self.set_header('Content-Length', len(content))
        self.finish()


class UpdateSettingsHandler(BaseHandler):
    """
    更新系统设置
    """
    _label = 'UpdateSettingsHandler'

    @BaseHandler.check_permission(need_login=True)
    async def post(self):

        # 更新青少年模式
        young_mode = self.params.get('young_mode')
        if young_mode in [True, False]:
            await user_service.update_user_by_uid(self.uid, young_mode=young_mode)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': {}, 'msg': ''}
        self.jsonify(ret)

