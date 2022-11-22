# -*- coding:utf-8 -*-

"""
小红点提示统一管理
"""

from config import config
from cores.database import db


class BasicBadgeManager(object):
    """
    通用badge manager
    使用实例的方式，初始化时必须提供 带1个可变参数的 cache_key
    """
    my_redis = None
    expire_time = 60 * 60 * 24 * 180

    def __init__(self, basic_cache_key, my_redis=None, expire_time=None):
        self.basic_cache_key = basic_cache_key
        if my_redis:
            self.my_redis = my_redis
        else:
            self.my_redis = db.get_redis(config.REDIS_DB_LONG)
        if expire_time:
            self.expire_time = expire_time

    def _build_cache_key(self, key):
        return self.basic_cache_key % key

    def increase_badge(self, uid, *service_id):
        key = self._build_cache_key(uid)
        self.my_redis.sadd(key, *service_id)
        self.my_redis.expire(key, self.expire_time)

    def decrease_badge(self, uid, *service_id):
        key = self._build_cache_key(uid)
        return self.my_redis.srem(key, *service_id)

    def delete_badge(self, uid):
        key = self._build_cache_key(uid)
        return self.my_redis.delete(key)

    def has_new_badge(self, uid):
        key = self._build_cache_key(uid)
        return self.my_redis.exists(key)

    def get_badge_num(self, uid):
        key = self._build_cache_key(uid)
        return self.my_redis.scard(key)

    def get_badge_members(self, uid):
        key = self._build_cache_key(uid)
        res = self.my_redis.smembers(key)
        return [r.decode('utf-8') for r in res]

    def service_has_badge(self, uid, service_id):
        if not service_id:
            return False
        key = self._build_cache_key(uid)
        return self.my_redis.sismember(key, service_id)


class AioBasicBadgeManager(object):
    """
    通用badge manager
    """
    my_redis = None
    expire_time = 60 * 60 * 24 * 180

    def __init__(self, basic_cache_key, my_redis=None, expire_time=None):
        self.basic_cache_key = basic_cache_key
        if my_redis:
            self._my_redis = my_redis
        else:
            self._my_redis = None
        if expire_time:
            self.expire_time = expire_time

    @property
    def my_redis(self):
        if self._my_redis:
            return self._my_redis
        return db.long_aioredis

    def _build_cache_key(self, key):
        return self.basic_cache_key % key

    async def increase_badge(self, uid, *service_id):
        key = self._build_cache_key(uid)
        pipe = self.my_redis.pipeline()
        pipe.sadd(key, *service_id)
        pipe.expire(key, self.expire_time)
        await pipe.execute()

    async def decrease_badge(self, uid, *service_id):
        key = self._build_cache_key(uid)
        return await self.my_redis.srem(key, *service_id)

    async def delete_badge(self, uid):
        key = self._build_cache_key(uid)
        return await self.my_redis.delete(key)

    async def has_new_badge(self, uid):
        key = self._build_cache_key(uid)
        return await self.my_redis.exists(key)

    async def get_badge_num(self, uid):
        key = self._build_cache_key(uid)
        return await self.my_redis.scard(key)

    async def get_badge_members(self, uid):
        key = self._build_cache_key(uid)
        return await self.my_redis.smembers(key)

    async def service_has_badge(self, uid, service_id):
        if not service_id:
            return False
        key = self._build_cache_key(uid)
        return await self.my_redis.sismember(key, service_id)

