# -*- coding:utf-8 -*-
"""
redis 锁集合
"""
from cores.database import db


# 用户级别锁key
USER_LOCK_RD_KEY = 'user_rd_lock_%s_%s'


def user_redis_set_unblock_lock(uid, lock_name, lock_time=10):
    """
    获得用户级别的redis锁
    :return:
    """
    rd_key = USER_LOCK_RD_KEY % (uid, lock_name)
    lock_count = db.snap_rd_cli.incrby(rd_key)

    # 首次认为上锁成功
    if lock_count == 1:
        db.snap_rd_cli.expire(rd_key, lock_time)
        return True

    # 否则认为上锁失败
    return False


def user_redis_unlock(uid, lock_name):
    """
    解除用户级别的redis锁
    :param uid:
    :param lock_name:
    :return:
    """
    rd_key = USER_LOCK_RD_KEY % (uid, lock_name)
    db.snap_rd_cli.delete(rd_key)


