# coding=utf-8
"""
生产环境配置
"""

# 项目名称
PROJECT_NAME = 'community_server'
PROJECT_HOST = 'https://www.jerryfun.com'

# 是否线上环境
IS_ONLINE_SERVER = True
WEB_DEBUG = False

# 单测环境相关
IS_TEST_CASE = False
TEST_IP = '127.0.0.1'
TEST_PORT = 9901
TEST_HOST = "%s:%s" % (TEST_IP, TEST_PORT)

# log配置
LOG_PATH = "/tmp/"

# mongo配置
DB_HOST = "mongodb://127.0.0.1:27017"
DB_PORT = 27017

# redis配置
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_PASSWORD = None
REDIS_DB_DEFAULT = 0        # 默认
REDIS_DB_FUNC_CACHE = 1     # function
REDIS_DB_USER_SESSION = 2   # 用户
REDIS_DB_AUDIT_SESSION = 3  # 管理员
REDIS_DB_SNAP = 4           # 短期（60分钟以内）
REDIS_DB_LONG = 5           # 长期（60分钟以上）

ALL_REDIS_DBS = (
    REDIS_DB_DEFAULT, REDIS_DB_FUNC_CACHE, REDIS_DB_USER_SESSION,
    REDIS_DB_AUDIT_SESSION, REDIS_DB_SNAP, REDIS_DB_LONG
)

# 登录超时
USER_SESSION_EXT = 60 * 60 * 24 * 30
AUDIT_SESSION_EXT = 60 * 60 * 24 * 7


# CDN 资源
ALIYUN_OSS_ACCESS_KEY_ID = ""
ALIYUN_OSS_SECRET_ACCESS_KEY = ""
ALIYUN_OSS_ENDPOINT = "oss-cn-beijing.aliyuncs.com"
ALIYUN_OSS_REGION = "http://%s" % ALIYUN_OSS_ENDPOINT
ALIYUN_OSS_IMAGE_BUCKET = "general-community-img"
ALIYUN_OSS_IMAGE_DIR = "general-community-img"
ALIYUN_OSS_VIDEO_BUCKET = "general-community-img"
ALIYUN_OSS_VIDEO_DIR = "general-community-img"
ALIYUN_OSS_STAT_BUCKET = "general-community-img"


# SMS 配置
ALIYUN_SMS_HOST = "https://eco.taobao.com"
ALIYUN_SMS_APP_ID = ""
ALIYUN_SMS_APP_SECRET = ""
ALIYUN_SMS_SIGN_NAME = "提醒业务"
ALIYUN_SMS_TEMPLATE_ID = ""

