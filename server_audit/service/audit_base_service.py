# coding=utf-8

from uuid import uuid4
import ujson
from config import config
from cores.database import db


class AdminRedisSession:
    """
    登录admin session管理类
    """
    rd_cli = db.get_redis(config.REDIS_DB_USER_SESSION)

    @classmethod
    def open_session(cls, sid):
        raw_data = cls.rd_cli.get(cls.prefixed(sid))
        data = ujson.loads(raw_data) if raw_data else {}
        return data

    @classmethod
    def create_new_session(cls, admin_uid, expire_time=config.USER_SESSION_EXT):

        # 生成新uid - session 映射关系
        new_sid = cls.gen_sid()
        cls.rd_cli.setex(name=cls.uid_prefixed(admin_uid), time=expire_time, value=new_sid)

        #  生成新session
        data = {'admin_uid': admin_uid, 'sid': new_sid}
        cls.save_session(new_sid, data)
        return new_sid

    @classmethod
    def save_session(cls, sid, data, expire=config.USER_SESSION_EXT):
        cls.rd_cli.setex(
            name=cls.prefixed(sid),
            time=expire,
            value=ujson.dumps(data),
        )

    @classmethod
    def expire_session(cls, sid, expire=config.USER_SESSION_EXT):
        cls.rd_cli.expire(
            cls.prefixed(sid),
            expire
        )

    @classmethod
    def delete_session(cls, sid):
        cls.rd_cli.delete(cls.prefixed(sid))

    @classmethod
    def prefixed(cls, sid):
        return 'session_%s' % sid

    @classmethod
    def uid_prefixed(cls, uid):
        return 'uid_session_map_%s' % uid

    @staticmethod
    def gen_sid():
        return str(uuid4())
