# -*- coding:utf-8 -*-
"""
web 页面渲染相关接口
"""
from server_web.handler.web_handler import *

web_urls = [
    # 官网首页
    (r'/', WebEntryHandler),
]
