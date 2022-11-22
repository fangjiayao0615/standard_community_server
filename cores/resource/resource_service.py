# -*- coding:utf-8 -*-
"""
资源文件 service 方法
"""
import hashlib
import mimetypes
import os
import io
import time
from bson import ObjectId

from cores.const import const_base
from cores.database import db
from cores.utils import logger


def local_img_2_oss(img_path):
    """
    本地图片上传至oss
    :param img_path: 图片本地路径
    :return:
    """

    result = {
        'url': "",
        'type': const_base.IMAGE_TYPE_NORMAL,
        'w': 0,
        'h': 0,
    }

    # 读取文件内容
    try:
        img_content = open(img_path, "rb").read()
    except:
        return result

    # 删除本地文件
    try:
        os.remove(img_path)
    except:
        pass

    # 构造 OSS 文件路径
    m = hashlib.md5()
    m.update(img_content)
    content_md5 = m.hexdigest()
    new_img_url = 'usr/image/%s' % content_md5
    img_postfix = img_path.split('.')[-1].lower()
    if img_postfix and img_postfix in ['png', 'jpg', 'gif', 'bmp', 'ico', 'jpeg', 'webp']:
        new_img_url += '.%s' % img_postfix
    else:
        new_img_url += '.%s' % 'jpeg'

    # 获取OSS content-type
    content_type = mimetypes.guess_type(img_path.split('?')[0])[0]
    extra_args = {'Content-Type': content_type} if content_type else None

    # 上传图片
    img_temp = img_content
    try:
        img_bucket = db.get_oss_image_bucket()
        img_bucket.put_object(data=io.BytesIO(img_temp), key=new_img_url, headers=extra_args)
    except Exception as e:
        print('local_img_2_oss img_url: %s, error: %s' % (img_path, str(e)))
        return result

    # 获取图片宽高
    width, height = get_img_width_height(img_content=img_temp)

    # 返回文件数据
    result = {
        'url': new_img_url,
        'type': const_base.IMAGE_TYPE_NORMAL,
        'w': width,
        'h': height,
    }
    return result


def get_img_width_height(img_content, img_path=None):

    if not img_path:
        img_path = '/tmp/img_%s_%s.jpg' % (int(time.time() * 1000), str(ObjectId()))
        with open(img_path, "wb") as fp:
            fp.write(img_content)

    try:
        from PIL import Image
        img = Image.open(img_path)
        width = img.size[0]
        height = img.size[1]
    except Exception as e:
        logger.info('get_img_width_height error: %s' % str(e))
        width = 0
        height = 0

    # 删除本地文件
    try:
        os.remove(img_path)
    except:
        pass

    return width, height





