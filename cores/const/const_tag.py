# coding=utf-8
"""
标签常量
"""

# 标签状态
TAG_STATUS_INVISIBLE = -10  # 不可见
TAG_STATUS_VISIBLE = 10  # 可见不推荐
TAG_STATUS_REC = 20  # 普通推荐

TAG_STATUS_DICT = {
    TAG_STATUS_REC: '普通推荐',
    TAG_STATUS_VISIBLE: '可见不推荐',
    TAG_STATUS_INVISIBLE: '不可见',
}

TAG_SOURCE_TYPE_OPERATOR = 'operator'
TAG_SOURCE_TYPE_USER = 'user'
TAG_SOURCE_TYPE_SPORTMONKS = 'sportmonks'
TAG_SOURCE_TYPE_INSTAGRAM = 'instagram'

# 标签类型
TAG_TYPE_NORMAL = 1  # 普通, 默认类型

# 标签类型信息
TAG_TYPE_DICT = {
    TAG_TYPE_NORMAL: '普通',
}

# 所有标签类型
ALL_TAG_TYPES = set(TAG_TYPE_DICT.keys())

# 查询排序类型
TAG_QUERY_SORT_FANS = 1
TAG_QUERY_SORT_POST = 2

# 每页展示数目
TAG_PAGE_PER_NUM = 20

# 标签名称长度限制
TAG_NAME_LEN_MIN = 3
TAG_NAME_LEN_MAX = 100
