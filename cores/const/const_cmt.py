# coding=utf-8
"""
评论常量
"""

# 帖子文案最长限制
COMMENT_TEXT_MAX_LEN = 1000

# 评论类型
COMMENT_TYPE_NORMAL = 1  # 普通评论

# 每页评论暂时数目
COMMENT_PAGE_PER_NUM = 15
COMMENT_PAGE_PER_NUM_MAX = 200

# 评论状态
COMMENT_STATUS_SELF_DELETE = -30
COMMENT_STATUS_INVISIBLE = -20
COMMENT_STATUS_SELF = -10
COMMENT_STATUS_VISIBLE = 10
COMMENT_STATUS_FINE = 20

# 评论信息
COMMENT_STATUS_DICT = {
    COMMENT_STATUS_SELF_DELETE: '自己删除',
    COMMENT_STATUS_INVISIBLE: '不可见',
    COMMENT_STATUS_SELF: '自己可见',
    COMMENT_STATUS_VISIBLE: '可见',
    COMMENT_STATUS_FINE: '精评',
}

# 所有评论状态
ALL_VALID_COMMENT_STATUS = set(COMMENT_STATUS_DICT.keys())

# 评论来源
COMMENT_SOURCE_TYPE_USER = 'user'              # 用户
COMMENT_SOURCE_TYPE_OPERATOR = 'operator'      # 运营

# 评论来源信息
COMMENT_SOURCE_TYPE_DICT = {
    COMMENT_SOURCE_TYPE_USER: '用户',
    COMMENT_SOURCE_TYPE_OPERATOR: '运营',
}

# 评论查询排序
COMMENT_QUERY_SORT_T_NEW = 1  # 最新
COMMENT_QUERY_SORT_T_OLD = 2  # 最旧
COMMENT_QUERY_SORT_T_HOT = 3  # 最热

# 发评论限制
COMMENT_FREQUENCY_LIMIT_SEC = 5

