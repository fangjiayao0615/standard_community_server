# -*- coding:utf-8 -*-
"""
APP 相关接口.
"""
from server_app.handler.backstage_handler import *
from server_app.handler.resource_handler import *
from server_app.handler.comment_handler import *
from server_app.handler.post_handler import *
from server_app.handler.tag_handler import *
from server_app.handler.user_handler import *
from server_app.handler.favor_hanlder import *
from server_app.handler.center_handler import *


app_urls = [
    # --------- 健康检查相关
    (r'/heartbeat', HeartBeatHandler),
    (r'/%s/heartbeat' % const_mix.URL_NAME_APP, HeartBeatHandler),

    # --------- 用户登录相关
    (r'/%s/account/guest_register' % const_mix.URL_NAME_APP, GuestRegisterHandler),
    (r'/%s/account/register' % const_mix.URL_NAME_APP, RegisterHandler),
    (r'/%s/account/send_code' % const_mix.URL_NAME_APP, SendVerificationCodeHandler),
    (r'/%s/account/valid_code' % const_mix.URL_NAME_APP, CheckVerificationCodeHandler),
    (r'/%s/account/login' % const_mix.URL_NAME_APP, LoginHandler),
    (r'/%s/account/code_login' % const_mix.URL_NAME_APP, ValidCodeLoginHandler),
    (r'/%s/account/logout' % const_mix.URL_NAME_APP, LogoutHandler),
    (r'/%s/account/reset' % const_mix.URL_NAME_APP, ResetPasswordHandler),
    (r'/%s/account/update' % const_mix.URL_NAME_APP, UpdateAccountHandler),

    # ---------- 用户喜好相关
    (r'/%s/favor/follow_user' % const_mix.URL_NAME_APP, FollowUserHandler),
    (r'/%s/favor/cancel_follow_user' % const_mix.URL_NAME_APP, CancelFollowUserHandler),
    (r'/%s/favor/follow_tag' % const_mix.URL_NAME_APP, FollowTagHandler),
    (r'/%s/favor/cancel_follow_tag' % const_mix.URL_NAME_APP, CancelFollowTagHandler),
    (r'/%s/favor/like_post' % const_mix.URL_NAME_APP, LikePostHandler),
    (r'/%s/favor/cancel_like_post' % const_mix.URL_NAME_APP, CancelLikePostHandler),
    (r'/%s/favor/dislike_post' % const_mix.URL_NAME_APP, DislikePostHandler),
    (r'/%s/favor/cancel_dislike_post' % const_mix.URL_NAME_APP, CancelDislikePostHandler),
    (r'/%s/favor/like_comment' % const_mix.URL_NAME_APP, LikeCommentHandler),
    (r'/%s/favor/cancel_like_comment' % const_mix.URL_NAME_APP, CancelLikeCommentHandler),
    (r'/%s/favor/dislike_comment' % const_mix.URL_NAME_APP, DislikeCommentHandler),
    (r'/%s/favor/cancel_dislike_comment' % const_mix.URL_NAME_APP, CancelDislikeCommentHandler),
    (r'/%s/favor/get_likes_history_to_me' % const_mix.URL_NAME_APP, GetLikeHistoryToMeHandler),
    (r'/%s/favor/get_fans_history_to_me' % const_mix.URL_NAME_APP, GetFansHistoryToMeHandler),

    # ---------- 用户中心相关
    (r'/%s/center/get_user_homepage' % const_mix.URL_NAME_APP, GetUserHomePageHandler),
    (r'/%s/center/get_my_homepage' % const_mix.URL_NAME_APP, GetMyHomePageHandler),
    (r'/%s/center/get_my_badges' % const_mix.URL_NAME_APP, GetMyBadgesHandler),
    (r'/%s/center/get_my_notices' % const_mix.URL_NAME_APP, GetMyNoticesHandler),

    # ---------- 标签服务相关
    (r'/%s/tag/create' % const_mix.URL_NAME_APP, TagCreateHandler),
    (r'/%s/tag/detail' % const_mix.URL_NAME_APP, TagDetailHandler),
    (r'/%s/tag/query_list' % const_mix.URL_NAME_APP, TagQueryListHandler),

    # ---------- 帖子服务相关
    (r'/%s/post/recommend_query_list' % const_mix.URL_NAME_APP, PostRecommendQueryListHandler),
    (r'/%s/post/history_recommend_query_list' % const_mix.URL_NAME_APP, PostHistoryRecommendQueryListHandler),
    (r'/%s/post/user_query_list' % const_mix.URL_NAME_APP, PostUserQueryListHandler),
    (r'/%s/post/tag_query_list' % const_mix.URL_NAME_APP, PostTagQueryListHandler),
    (r'/%s/post/detail' % const_mix.URL_NAME_APP, PostQueryDetailHandler),
    (r'/%s/post/create' % const_mix.URL_NAME_APP, PostCreateHandler),
    (r'/%s/post/delete' % const_mix.URL_NAME_APP, PostDeleteHandler),

    # ---------- 评论服务相关
    (r'/%s/comment/create' % const_mix.URL_NAME_APP, CommentCreateHandler),
    (r'/%s/comment/post_query_list' % const_mix.URL_NAME_APP, CommentPostQueryListHandler),
    (r'/%s/comment/user_query_list' % const_mix.URL_NAME_APP, CommentUserQueryListHandler),
    (r'/%s/comment/delete' % const_mix.URL_NAME_APP, CommentDeleteHandler),

    # ---------- 资源处理
    (r'/%s/resource/upload_img' % const_mix.URL_NAME_APP, UploadImgHandler),

    # ---------- 后台服务相关
    (r'/%s/backstage/get_app_conf' % const_mix.URL_NAME_APP, GetAppConfHandler),
    (r'/%s/backstage/update_settings' % const_mix.URL_NAME_APP, UpdateSettingsHandler),

]
