# coding=utf-8
"""
资源服务相关 handler
"""

import time
import os

from cores.const import const_err, const_mix
from server_app.handler.base_handler import BaseHandler
from cores.base import base_service
from cores.resource import resource_service


class UploadImgHandler(BaseHandler):
    """
    获取客户端上传文件
    """
    _label = 'UploadImgHandler'

    @BaseHandler.check_permission(need_login=False)
    async def post(self):

        # 初始化本地缓存路径
        if not os.path.exists(const_mix.IMG_LOCAL_PATH):
            os.mkdir(const_mix.IMG_LOCAL_PATH)

        # 本地保存文件
        file_metas = self.request.files["uploadedfile"]
        img_path = ""
        for meta in file_metas:
            file_name = "_".join(["img", str(int(time.time()*1000)), meta['filename']])
            img_path = os.path.join(const_mix.IMG_LOCAL_PATH, file_name)
            with open(img_path, 'wb') as up:
                up.write(meta['body'])

        # 本地上传OSS
        raw_info = resource_service.local_img_2_oss(img_path)
        result = base_service.build_img_infos_item(raw_info)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': result, 'msg': ''}
        self.jsonify(ret)
