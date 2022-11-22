# -*- coding:utf-8 -*-
"""
audit 相关接口
"""
from cores.const import const_mix
from server_audit.handler.audit_admin_handler import *
from server_audit.handler.audit_mobile_handler import *
from server_audit.handler.audit_post_handler import *
from server_audit.handler.audit_user_handler import *

audit_urls = [
    # ------ 账户相关操作
    (r'/%s/admin/login' % const_mix.URL_NAME_AUDIT, AdminLoginHandler),
    (r'/%s/admin/logout' % const_mix.URL_NAME_AUDIT, AdminLogoutHandler),

    # ------ 移动版管理后台
    (r'/%s/mobile/post_query_list' % const_mix.URL_NAME_AUDIT, AdminMobPostQueryListsHandler),
    (r'/%s/mobile/post_update_tags' % const_mix.URL_NAME_AUDIT, AdminMobPostUpdateTagsHandler),
    (r'/%s/mobile/post_update_status' % const_mix.URL_NAME_AUDIT, AdminMobPostUpdateStatusHandler),

    (r'/%s/mobile/comment_query_list' % const_mix.URL_NAME_AUDIT, AdminMobCommentQueryListHandler),
    (r'/%s/mobile/comment_update_status' % const_mix.URL_NAME_AUDIT, AdminMobCommentUpdateStatusHandler),

    (r'/%s/mobile/user_query_list' % const_mix.URL_NAME_AUDIT, AdminMobUserQueryListHandler),
    (r'/%s/mobile/user_update_status' % const_mix.URL_NAME_AUDIT, AdminMobUserUpdateStatusHandler),

    # ------- 用户管理
    (r'/%s/user/create' % const_mix.URL_NAME_AUDIT, AdminUserCreateHandler),

    # ------- 标签管理


    # ------- 帖子管理
    (r'/%s/post/create' % const_mix.URL_NAME_AUDIT, AdminPostCreateHandler),


]
