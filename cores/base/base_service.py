# -*- coding:utf-8 -*-
"""
基础 service 方法
"""
import copy
import datetime
import random
import time
import ujson
import asyncio
from functools import wraps
from uuid import uuid4
from bson import ObjectId
from config import config
from cores.const import const_user, const_base
from cores.database import db
from cores.utils import logger


def get_random_str(str_len=8, seed=None):
    """
    获取指定长度的随机字符串
    """
    seed = seed or [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
        'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
    ]
    result = []
    for i in range(str_len):
        result.append(random.choice(seed))
    return ''.join(result)


def build_pretty_num(num):
    """
    构造 w 或 k 格式
    :param num:
    :return:
    """
    if 1000 > num:
        return str(num)
    elif 1000 * 1000 > num >= 1000:
        return '%.1fk' % (num/1000)
    elif 1000 * 1000 * 1000 > num >= 1000 * 1000:
        return '%.2fm' % (num/(1000*1000))
    else:
        return '%.3fb' % (num/(1000*1000*1000))


def async_run(fun):
    """
    同步运行指定方法
    :return: 
    """
    from tornado import ioloop
    ret = ioloop.IOLoop.current().run_sync(lambda: fun)
    return ret


# ----------------- 登录session管理 ------------------
class AioRedisSession:
    """
    登录session管理类
    """
    aiord = None
    aiord_r = None

    @classmethod
    async def init(cls):
        # assert cls.aiord is None
        if not cls.aiord:
            cls.aiord, cls.aiord_r = await asyncio.gather(
                # 主库
                db.get_aioredis(config.REDIS_DB_USER_SESSION),
                # 从库
                db.get_aioredis_r(config.REDIS_DB_USER_SESSION)
            )

    @classmethod
    async def open_session(cls, sid):
        raw_data = await cls.aiord_r.get(cls.prefixed(sid))
        data = ujson.loads(raw_data) if raw_data else {}
        return data

    @classmethod
    async def create_new_session(cls, uid, user_info, expire_time=config.USER_SESSION_EXT, login_from_type=const_user.LOGIN_FROM_TYPE_PHONE):
        # 重复登录旧session失效
        await cls.delete_session_by_uid(uid, login_from_type)

        # 生成新 uid -> session 映射关系
        new_sid = cls.gen_sid()
        await cls.aiord.setex(key=cls.uid_prefixed(uid, login_from_type), seconds=expire_time, value=new_sid)

        #  生成新session
        await cls.save_session_by_user_info(uid, new_sid, user_info)
        return new_sid

    @classmethod
    async def update_session(cls, uid, user_info):

        # 手机 session
        old_sid = await cls.aiord.get(cls.uid_prefixed(uid, const_user.LOGIN_FROM_TYPE_PHONE))
        if old_sid:
            if await cls.aiord.exists(cls.prefixed(old_sid)):
                await cls.save_session_by_user_info(uid, old_sid, user_info)

        # pc session
        old_sid = await cls.aiord.get(cls.uid_prefixed(uid, const_user.LOGIN_FROM_TYPE_PC))
        if old_sid:
            if await cls.aiord.exists(cls.prefixed(old_sid)):
                await cls.save_session_by_user_info(uid, old_sid, user_info)

    @classmethod
    async def save_session_by_user_info(cls, uid, sid, user_info):
        #  生成新session
        data = {'uid': uid, 'sid': sid}
        # 只保留基本信息
        base_user_info = {
            'uid': user_info['uid'],
            'name': user_info['name'],
            'utypes': user_info['utypes'],
        }
        data['user'] = base_user_info
        await cls.save_session(sid, data)
        return data

    @classmethod
    async def save_session(cls, sid, data, expire=config.USER_SESSION_EXT):
        await cls.aiord.setex(
            key=cls.prefixed(sid),
            seconds=expire,
            value=ujson.dumps(data),
        )

    @classmethod
    async def expire_session(cls, sid, expire=config.USER_SESSION_EXT):
        await cls.aiord.expire(
            cls.prefixed(sid),
            expire
        )

    @classmethod
    async def delete_session(cls, sid):
        """
        使用 session_id 删除 session
        """
        await cls.aiord.delete(cls.prefixed(sid))

    @classmethod
    async def delete_session_by_uid(cls, uid, login_from_type=const_user.LOGIN_FROM_TYPE_PHONE):
        """
        使用 uid 删除 session
        """
        old_sid = await cls.aiord.get(cls.uid_prefixed(uid, login_from_type))
        if old_sid:
            await cls.delete_session(old_sid)

    @classmethod
    def prefixed(cls, sid):
        """
        session信息 使用的 redis-key
        """
        return 'session_%s' % sid

    @classmethod
    def uid_prefixed(cls, uid, login_from_type):
        """
        使用 uid + login_from_type 生成储存 session 的 key
        """
        return 'uid_session_map_%s_%s' % (uid, login_from_type)

    @staticmethod
    def gen_sid():
        """
        生成 session_id
        :return: 
        """
        return str(uuid4())

    @classmethod
    async def get_session_ttl(cls, sid):
        """
        获取 session 剩余时间
        """
        ttl = await cls.aiord_r.ttl(cls.prefixed(sid)) or 0
        return ttl


def build_user_login_info(user_info, session_id):
    """
    构建用户登录信息
    """
    return {
        'session': session_id,
        'uid': user_info['uid'],
        'nick': user_info['nick'],
        'name': user_info['name'],
        'utypes': user_info['utypes'],
    }


def is_guest(user_info):
    """
    判断用户是否是游客
    """
    return const_user.USER_TYPE_GUEST in user_info.get('utypes', [])


# ----------------- 验证码功能 ------------------
def build_verification_code_rd_key(name):
    """
    存放当前验证码的 redis-key
    """
    return 'check_verification_code_%s' % name


def build_verification_code_count_rd_key(name):
    """
    存放验证码累计次数的redis key
    """
    now_time = datetime.datetime.now().strftime('%Y%m%d')
    return 'check_verification_code_count_%s_%s' % (now_time, name)


def check_verification_code(name, verification_code, need_delete=True):
    """
    检查验证码是否正确
    :return:
    """
    result = False
    rd_key = build_verification_code_rd_key(name)
    store_verification_code = db.default_rd_cli.get(rd_key)
    if store_verification_code and store_verification_code.decode('utf-8') == str(verification_code):
        result = True
        # 验证后删除
        if need_delete:
            db.default_rd_cli.delete(rd_key)
    return result

# 验证码发送最大次数
MAX_VERIFICATION_CODE_SEND_TIMES = 50
MAX_VERIFICATION_CODE_SEND_TIMES_EXT = 60 * 60 * 24


def get_verification_code_send_times(name):
    """
    获取验证码已发送次数
    """
    rd_key = build_verification_code_count_rd_key(name)
    count = db.default_rd_cli.get(rd_key)
    count = int(count) if isinstance(count, (str, bytes)) and count.isdigit() else 0
    return count


def reach_verification_code_max_times(name):
    """
    是否达到验证法发送最大次数
    """
    count = get_verification_code_send_times(name)
    return bool(count >= MAX_VERIFICATION_CODE_SEND_TIMES)


def inc_verification_code_count(name):
    """
    验证码发送次数+1
    """
    count_rd_key = build_verification_code_count_rd_key(name)
    db.default_rd_cli.incrby(count_rd_key)
    db.default_rd_cli.expire(count_rd_key, 60 * 60 * 48)


def generate_store_verification_code(name):
    """
    生成并保存验证码
    :param name: 
    :return: 
    """
    verification_code = str(random.randint(1000, 9999))
    code_rd_key = build_verification_code_rd_key(name)
    db.default_rd_cli.setex(name=code_rd_key, value=verification_code, time=VERIFICATION_CODE_EXT)
    return verification_code


# 验证码保存最大时间
VERIFICATION_CODE_EXT = 60 * 60 * 24


async def send_verification_code(name):
    """
    检查验证码是否正确
    :return:
    """

    # 保存验证码
    verification_code = generate_store_verification_code(name)

    # 计数累加
    inc_verification_code_count(name)

    # 发送邮箱验证码
    # TODO

    # 发送手机验证码
    send_phone_verification_code(name, verification_code)
    return verification_code


def send_phone_verification_code(phone, verification_code):
    """
    发送手机验证码(国内)
    """
    if not config.IS_ONLINE_SERVER:
        return

    # 获取手机号
    phone = phone.split('-')[-1]

    # 使用Ali sms
    try:
        from cores.utils.sms_ali_sdk import top
        req = top.api.AlibabaAliqinFcSmsNumSendRequest(config.ALIYUN_SMS_HOST)
        req.set_app_info(top.appinfo(config.ALIYUN_SMS_APP_ID, config.ALIYUN_SMS_APP_SECRET))
        req.sms_type = "normal"
        req.sms_free_sign_name = config.ALIYUN_SMS_SIGN_NAME
        req.sms_param = "{\"code\":\"%s\"}" % verification_code
        req.rec_num = phone
        req.sms_template_code = config.ALIYUN_SMS_TEMPLATE_ID
        resp = req.getResponse()
        logger.info(str(resp))
    except Exception as e:
        logger.error("[send_phone_verification_code] error " + str(e))


# ----------------- mongo ------------------
def ensure_mongo_obj_ids(mongo_ids):
    """
    确保mongo id列表为 ObjectId 格式
    :param mongo_ids:
    :return:
    """
    result = []
    if not mongo_ids:
        return result

    for m_id in mongo_ids:
        try:
            if isinstance(m_id, str) and m_id:
                result.append(ObjectId(m_id))
            else:
                result.append(m_id)
        except:
            continue
    return result


def ensure_mongo_str_ids(mongo_ids):
    """
    确保mongo id列表为 string 格式
    :param mongo_ids:
    :return:
    """
    result = []
    for m_id in mongo_ids:
        result.append(str(m_id))
    return result


# ----------------- cursor功能 ------------------
def get_cursor_info_from_req_param(req_param, cursor_key='cursor'):
    """
    从请求参数中获取分页信息
    :param req_param:
    :param cursor_key: 存放cursor的key
    :return:
    """
    cursor_info = {}

    if not isinstance(req_param, dict):
        return cursor_info

    cursor_str = req_param.get(cursor_key)
    if cursor_str:
        cursor_info = ujson.loads(cursor_str)
    return cursor_info


def is_first_cursor(cursor):
    """
    是否是首页分页信息
    :return:
    """
    return cursor.get('offset', 0) == 0


def attach_ct_lt_to_next_cursor_info(next_cursor_info, cursor_info, new_objs):
    """
    给下一页cursor补充边界时间限制
    :param next_cursor_info: 下页cursor
    :param cursor_info: 当前页cursor
    :param new_objs: 按照时间排序的最新数据列表：posts、comments
    :return:
    """
    # 首页补充
    if cursor_info.get('offset', 0) == 0 and new_objs:
        next_cursor_info['ct_lt'] = new_objs[0]['ct'] + 1
    # 翻页继承
    elif cursor_info.get('ct_lt'):
        next_cursor_info['ct_lt'] = cursor_info['ct_lt']
    return next_cursor_info


# ----------------- 版本检测 ------------------
def later_or_equal_version(v1, v2):
    """
    版本检测, v1 是否 >= v2
    return
    """
    try:
        info1 = v1.split('.')
        info2 = v2.split('.')
        for i, sub_version_tuple in enumerate(zip(info1, info2)):
            sub_v1, sub_v2 = sub_version_tuple
            if int(sub_v1) > int(sub_v2):
                return True
            elif int(sub_v1) < int(sub_v2):
                return False
        return len(info1) >= len(info2)
    except:
        return False


def is_version_equal(v1, v2):
    """
    判断两个版本是否相等
    :param v1:
    :param v2:
    :return:
    """
    try:

        info1 = v1.split('.')
        info2 = v2.split('.')
        for sub_v1, sub_v2 in zip(info1, info2):
            if int(sub_v1) != int(sub_v2):
                return False

        return len(info1) == len(info2)
    except:
        return False


# ----------------- 热开关 ------------------
def switch_is_on(switch_name):
    """
    开关控制模块, 用途：在线上环境快速开启或关闭某项功能，不依赖与代码上线流程。
    建议在功能正式启用且稳定之后，去掉开关控制。
    :return:
    """
    switch_rd = db.long_rd_cli
    switch_val = switch_rd.get(switch_name)
    if not switch_val:
        return False
    return True


def switch_manager_change(switch_name, value, ext=60*60*24*365*10):
    """
    开启或关闭开关
    :param switch_name:
    :param value: 1 开启；0 关闭
    :param ext: 过期时间
    :return:
    """
    switch_rd = db.long_rd_cli
    if value:
        switch_rd.setex(name=switch_name, value=value, time=ext)
    else:
        switch_rd.delete(switch_name)


# ----------------- 脚本性能 ------------------
def script_performance_monitor(limit_seconds=60*60):
    """
    脚本性能监控，使用方法:
        @script_performance_monitor(limit_seconds=60*60*30)
    超过时间限制会发送报警消息
    :param limit_seconds: 单次执行一次脚本的时间限制。
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args):
            start_ts = int(time.mktime(datetime.datetime.now().timetuple()))
            res = func(*args)
            end_ts = int(time.mktime(datetime.datetime.now().timetuple()))

            # 超过限制时间发送钉钉警报
            used_ts = end_ts - start_ts
            if used_ts >= limit_seconds:
                # TODO：报警
                pass
            return res
        return wrapper
    return decorator


def build_img_infos(img_infos):
    """
    构造新版图片元素
    :return:
    """
    imgs = []
    if not img_infos:
        return imgs

    for img_info in img_infos:
        if not isinstance(img_info, dict):
            continue
        img_item = build_img_infos_item(img_info)
        imgs.append(img_item)
    return imgs


def build_img_infos_item(raw_info):
    """
    构造完整的图片信息
    :return:
    """
    if not isinstance(raw_info, dict):
        return {}
    raw_info = copy.deepcopy(raw_info)
    # 原图链接
    raw_url = raw_info.get('url', '')
    if raw_url and raw_url[:4] != 'http':
        raw_url = sign_oss_image_url(raw_url)
    # 浏览图
    view_url = raw_info.get('url', '')
    if view_url and view_url[:4] != 'http':
        view_url = sign_oss_image_url(view_url, style='image/resize,w_720')
    # 缩略图
    thumb_url = raw_info.get('url', '')
    if thumb_url and thumb_url[:4] != 'http':
        thumb_url = sign_oss_image_url(thumb_url, style='image/resize,w_360')
    # 返回结果
    image = {
        'type': raw_info.get('type', const_base.IMAGE_TYPE_NORMAL),
        'url': raw_info.get('url', ''),
        'raw_url': raw_url,
        'view_url': view_url,
        'thumb_url': thumb_url,
        'w': raw_info.get('w', 0),
        'h': raw_info.get('h', 0),
    }
    return image


def sign_oss_image_url(image_url, expires=60 * 60 * 12, style=None):
    """
    签名图片
    :param image_url:
    :param expires:
    :param style:
        # 缩放 style = 'image/resize,m_fixed,w_100,h_100'
        # 裁剪 style = 'image/crop,w_100,h_100,x_100,y_100,r_1'
        # 旋转 style = 'image/rotate,90'
        # 锐化 style = 'image/sharpen,100'
        # 水印 style = 'image/watermark,text_SGVsbG8g5Zu-54mH5pyN5YqhIQ'
        # 格式转换 style = 'image/format,png'
    :return:
    """
    return ''
    # if image_url[:4] == 'http':
    #     return image_url
    #
    # params = None
    # if style:
    #     params = {'x-oss-process': style}
    #
    # image_bucket = db.get_oss_image_bucket()
    # image_sign_url = image_bucket.sign_url(method='GET', key=image_url, expires=expires, params=params)
    #
    # if image_sign_url[:7] == 'http://':
    #     image_sign_url = image_sign_url.replace('http://', 'https://')
    #
    # return image_sign_url




