# -*- coding:utf-8 -*-

from config import config
import redis
import aioredis
from cores.database import mongo_sync, mongo_async


# ---------- 同步redis
default_rd_cli = None
snap_rd_cli = None
long_rd_cli = None


def get_redis(db=config.REDIS_DB_DEFAULT):
    redis_cli = redis.StrictRedis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=db,
        password=config.REDIS_PASSWORD,
        socket_timeout=0.5,  # 连接或者执行时间
    )
    return redis_cli


def init_redis():
    """
    初始化redis
    """
    global default_rd_cli
    if not default_rd_cli:
        default_rd_cli = get_redis(config.REDIS_DB_DEFAULT)
    global snap_rd_cli
    if not snap_rd_cli:
        snap_rd_cli = get_redis(config.REDIS_DB_SNAP)
    global long_rd_cli
    if not long_rd_cli:
        long_rd_cli = get_redis(config.REDIS_DB_LONG)


# ---------- 异步redis
default_aioredis = None
snap_aioredis = None
long_aioredis = None

async def get_aioredis(db):
    return await aioredis.create_redis_pool(
        (config.REDIS_HOST, config.REDIS_PORT),
        db=db,
        password=config.REDIS_PASSWORD,
        minsize=0,
        maxsize=20,
        timeout=3.2,  # 等一次syn重试
        encoding='utf8'
    )


async def get_aioredis_r(db):
    return await aioredis.create_redis_pool(
        (config.REDIS_HOST, config.REDIS_PORT),
        db=db,
        password=config.REDIS_PASSWORD,
        minsize=0,
        maxsize=20,
        timeout=3.2,
        encoding='utf8'
    )


async def init_aioredis():
    """
    初始化异步redis
    """
    global default_aioredis
    if not default_aioredis:
        default_aioredis = await get_aioredis(config.REDIS_DB_DEFAULT)

    global snap_aioredis
    if not snap_aioredis:
        snap_aioredis = await get_aioredis(config.REDIS_DB_SNAP)

    global long_aioredis
    if not long_aioredis:
        long_aioredis = await get_aioredis(config.REDIS_DB_LONG)


# -------- mongo Db
DB_COMMUNITY = 'community'
DB_COMMUNITY_AUDIT = 'community_audit'


# --------- 帖子
col_post = None
def get_col_post():
    global col_post
    if not col_post:
        col_post = mongo_sync.mongo_collection(DB_COMMUNITY, 'post', config.DB_HOST, config.DB_PORT)
    return col_post


motordb_col_post = None
def get_motordb_col_post():
    global motordb_col_post
    if not motordb_col_post:
        motordb_col_post = mongo_async.mongo_collection(DB_COMMUNITY, 'post', config.DB_HOST, config.DB_PORT)
    return motordb_col_post


# --------- 推荐帖子浏览历史记录
col_post_recommend_history = None
def get_col_post_recommend_history():
    global col_post_recommend_history
    if not col_post_recommend_history:
        col_post_recommend_history = mongo_sync.mongo_collection(DB_COMMUNITY, 'post_recommend_history', config.DB_HOST, config.DB_PORT)
    return col_post_recommend_history


motordb_col_post_recommend_history = None
def get_motordb_col_post_recommend_history():
    global motordb_col_post_recommend_history
    if not motordb_col_post_recommend_history:
        motordb_col_post_recommend_history = mongo_async.mongo_collection(DB_COMMUNITY, 'post_recommend_history', config.DB_HOST, config.DB_PORT)
    return motordb_col_post_recommend_history


# --------- 账户
col_user = None
def get_col_user():
    global col_user
    if not col_user:
        col_user = mongo_sync.mongo_collection(DB_COMMUNITY, 'user', config.DB_HOST, config.DB_PORT)
    return col_user


motordb_col_user = None
def get_motordb_col_user():
    global motordb_col_user
    if not motordb_col_user:
        motordb_col_user = mongo_async.mongo_collection(DB_COMMUNITY, 'user', config.DB_HOST, config.DB_PORT)
    return motordb_col_user


# --------- 第三方账户
col_user_third = None
def get_col_user_third():
    global col_user_third
    if not col_user_third:
        col_user_third = mongo_sync.mongo_collection(DB_COMMUNITY, 'user_third', config.DB_HOST, config.DB_PORT)
    return col_user_third


motordb_col_user_third = None
def get_motordb_col_user_third():
    global motordb_col_user_third
    if not motordb_col_user_third:
        motordb_col_user_third = mongo_async.mongo_collection(DB_COMMUNITY, 'user_third', config.DB_HOST, config.DB_PORT)
    return motordb_col_user_third


# --------- 用户设备管理
col_user_device = None
def get_col_user_device():
    global col_user_device
    if not col_user_device:
        col_user_device = mongo_sync.mongo_collection(DB_COMMUNITY, 'user_device', config.DB_HOST, config.DB_PORT)
    return col_user_device


motordb_col_user_device = None
def get_motordb_col_user_device():
    global motordb_col_user_device
    if not motordb_col_user_device:
        motordb_col_user_device = mongo_async.mongo_collection(DB_COMMUNITY, 'user_device', config.DB_HOST, config.DB_PORT)
    return motordb_col_user_device


# --------- 主题标签
col_tag = None
def get_col_tag():
    global col_tag
    if not col_tag:
        col_tag = mongo_sync.mongo_collection(DB_COMMUNITY, 'tag', config.DB_HOST, config.DB_PORT)
    return col_tag


motordb_col_tag = None
def get_motordb_col_tag():
    global motordb_col_tag
    if not motordb_col_tag:
        motordb_col_tag = mongo_async.mongo_collection(DB_COMMUNITY, 'tag', config.DB_HOST, config.DB_PORT)
    return motordb_col_tag


# --------- 评论
col_comment = None
def get_col_comment():
    global col_comment
    if not col_comment:
        col_comment = mongo_sync.mongo_collection(DB_COMMUNITY, 'comment', config.DB_HOST, config.DB_PORT)
    return col_comment


motordb_col_comment = None
def get_motordb_col_comment():
    global motordb_col_comment
    if not motordb_col_comment:
        motordb_col_comment = mongo_async.mongo_collection(DB_COMMUNITY, 'comment', config.DB_HOST, config.DB_PORT)
    return motordb_col_comment


# --------- 用户喜好
col_favor = None
def get_col_favor():
    global col_favor
    if not col_favor:
        col_favor = mongo_sync.mongo_collection(DB_COMMUNITY, 'favor', config.DB_HOST, config.DB_PORT)
    return col_favor


motordb_col_favor = None
def get_motordb_col_favor():
    global motordb_col_favor
    if not motordb_col_favor:
        motordb_col_favor = mongo_async.mongo_collection(DB_COMMUNITY, 'favor', config.DB_HOST, config.DB_PORT)
    return motordb_col_favor


# --------- 用户关注历史记录
col_fan_history = None
def get_col_fan_history():
    global col_fan_history
    if not col_fan_history:
        col_fan_history = mongo_sync.mongo_collection(DB_COMMUNITY, 'fan_history', config.DB_HOST, config.DB_PORT)
    return col_fan_history


motordb_col_fan_history = None
def get_motordb_col_fan_history():
    global motordb_col_fan_history
    if not motordb_col_fan_history:
        motordb_col_fan_history = mongo_async.mongo_collection(DB_COMMUNITY, 'fan_history', config.DB_HOST, config.DB_PORT)
    return motordb_col_fan_history


# --------- 用户点赞历史记录
col_like_history = None
def get_col_like_history():
    global col_like_history
    if not col_like_history:
        col_like_history = mongo_sync.mongo_collection(DB_COMMUNITY, 'like_history', config.DB_HOST, config.DB_PORT)
    return col_like_history


motordb_col_like_history = None
def get_motordb_col_like_history():
    global motordb_col_like_history
    if not motordb_col_like_history:
        motordb_col_like_history = mongo_async.mongo_collection(DB_COMMUNITY, 'like_history', config.DB_HOST, config.DB_PORT)
    return motordb_col_like_history


# --------- 用户关注话题记录
col_favor_tag_history = None
def get_col_favor_tag_history():
    global col_favor_tag_history
    if not col_favor_tag_history:
        col_favor_tag_history = mongo_async.mongo_collection(DB_COMMUNITY, 'favor_tag_history', config.DB_HOST, config.DB_PORT)
    return col_favor_tag_history


motordb_col_favor_tag_history = None
def get_motordb_col_favor_tag_history():
    global motordb_col_favor_tag_history
    if not motordb_col_favor_tag_history:
        motordb_col_favor_tag_history = mongo_async.mongo_collection(DB_COMMUNITY, 'favor_tag_history', config.DB_HOST, config.DB_PORT)
    return motordb_col_favor_tag_history


# --------- APP配置信息
col_app_conf = None
def get_col_app_conf():
    global col_app_conf
    if not col_app_conf:
        col_app_conf = mongo_sync.mongo_collection(DB_COMMUNITY, 'app_conf', config.DB_HOST, config.DB_PORT)
    return col_app_conf


motordb_col_app_conf = None
def get_motordb_col_app_conf():
    global motordb_col_app_conf
    if not motordb_col_app_conf:
        motordb_col_app_conf = mongo_async.mongo_collection(DB_COMMUNITY, 'app_conf', config.DB_HOST, config.DB_PORT)
    return motordb_col_app_conf


# --------- 用户通知
col_notice = None
def get_col_notice():
    global col_notice
    if not col_notice:
        col_notice = mongo_sync.mongo_collection(DB_COMMUNITY, 'notices', config.DB_HOST, config.DB_PORT)
    return col_notice


motordb_col_notice = None
def get_motordb_col_notice():
    global motordb_col_notice
    if not motordb_col_notice:
        motordb_col_notice = mongo_async.mongo_collection(DB_COMMUNITY, 'notices', config.DB_HOST, config.DB_PORT)
    return motordb_col_notice


# ----------- 管理员信息表
col_admin = None
def get_col_admin():
    global col_admin
    if not col_admin:
        col_admin = mongo_sync.mongo_collection(DB_COMMUNITY, 'admin', config.DB_HOST, config.DB_PORT)
    return col_admin


motordb_col_admin = None
def get_motordb_col_admin():
    global motordb_col_admin
    if not motordb_col_admin:
        motordb_col_admin = mongo_async.mongo_collection(DB_COMMUNITY, 'admin', config.DB_HOST, config.DB_PORT)
    return motordb_col_admin

