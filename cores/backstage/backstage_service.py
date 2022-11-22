# -*- coding:utf-8 -*-
"""
后台服务 service 方法
"""
from config import config


def get_oss_conf():
    """
    获取oss配置信息
    :return: 
    """
    return {
        'endpoint': config.ALIYUN_OSS_ENDPOINT,
        'img_bucket': config.ALIYUN_OSS_IMAGE_BUCKET,
        'img_dir': config.ALIYUN_OSS_IMAGE_DIR,
        'video_bucket': config.ALIYUN_OSS_VIDEO_BUCKET,
        'video_dir': config.ALIYUN_OSS_VIDEO_DIR,
    }
