# coding=utf-8
"""
通用常量
"""
# ----------- URL API 路径前缀
import copy

URL_NAME_APP = "app"
URL_NAME_AUDIT = "audit"
URL_NAME_WEB = "web"

IMG_LOCAL_PATH = "/tmp/img"

# ----------- favor 相关 ----------------
# 互动行为类型
F_ACTION_TYPE_LIKE = 1
F_ACTION_TYPE_CANCEL_LIKE = 2
F_ACTION_TYPE_DISLIKE = 3
F_ACTION_TYPE_CANCEL_DISLIKE = 4

# 互动行为类型信息
F_ACTION_TYPE_DICT = {
    F_ACTION_TYPE_LIKE: '点赞',
    F_ACTION_TYPE_CANCEL_LIKE: '取消点赞',
    F_ACTION_TYPE_DISLIKE: '点踩',
    F_ACTION_TYPE_CANCEL_DISLIKE: '取消点踩',
}

# 最大关注话题上限
MAX_F_TIDS_LEN = 1000

# 最大关注用户上限
MAX_F_UIDS_LEN = 1000

# 最大关注帖子上限
MAX_F_PIDS_LEN = 1000

# 最大关注评论上限
MAX_F_CIDS_LEN = 1000

# 查询排序类型
FAVOR_QUERY_SORT_FANS = 1
FAVOR_QUERY_SORT_POST = 2

# 翻页列表单页限制
FAVOR_PAGE_PER_NUM = 20

# 数据类型总体分类码
CONTENT_TYPE_USER_CODE = 1  # 用户
CONTENT_TYPE_POST_CODE = 2  # 帖子
CONTENT_TYPE_TAG_CODE = 3  # 标签
CONTENT_TYPE_COMMENT_CODE = 4  # 评论

# ----------- history 相关 ---------------
# 每页展示数目
HISTORY_PAGE_PER_NUM = 10
HISTORY_PAGE_PER_NUM_MAX = 200

# ----------- notice 相关 ----------------
# 通知类型
NOTICE_TYPE_SYS = 1  # 系统通知

# 通知类型信息
NOTICE_TYPE_DICT = {
    NOTICE_TYPE_SYS: '系统通知',
}

# 所有通知类型
ALL_NOTICE_TYPES = set(NOTICE_TYPE_DICT.keys())

# 通知状态
NOTICE_STATUS_INVISIBLE = -10
NOTICE_STATUS_VISIBLE = 10

# 通知列表最大每页展示数目
NOTICES_PAGE_PER_NUM = 10

# ------------ APP conf 信息 ---------------
_APP_CONF_DATA = {
    # 审核检测
    'ios_in_review': False,
    'android_in_review': False,

    # 首页标签映射关系
    'category_tag_map': {
        'funny': '5fb1338360ff5c77a1d7458e',
        'relax': '5fb1338360ff5c77a1d7458e',
        'entertainment': '5fbd2024f693ae6076d75edd',
        'knowledge': '5fbd2024f693ae6076d75edd',
    },

    # 反馈建议帖子ID
    'support_pid': '5fde0fb6ae79a9393872f9bf',
}


def get_app_conf():
    """
    获取APP配置，需要copy一份。防止在使用中被无意中修改
    :return: 
    """
    return copy.deepcopy(_APP_CONF_DATA)


# ------APP 版本号
VERSION_0_0_9 = '0.0.9'
VERSION_1_0_0 = '1.0.0'

