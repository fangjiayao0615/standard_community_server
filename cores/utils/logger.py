# -*- coding:utf-8 -*-
import logging
import datetime

logger = None


def init_logger(service, level=logging.DEBUG):
    global logger
    if logger:
        return logger
    logger = logging.getLogger(service)
    logger.setLevel(level)

    return logger


def logout(level, infos):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lo = '%s - %s -->' % (level, now)
    lo = '%s %s' % (lo, infos)
    print(lo)


def split_msg(message):
    if len(message) > 4096:
        message = message[:4096]
    return message


def debug(message):
    message = split_msg(message)
    if logger:
        logger.debug(message)
    else:
        logout('DEBUG', message)


def info(message):
    message = split_msg(message)
    if logger:
        logger.info(message)
    else:
        logout('INFO', message)


def warn(message):
    message = split_msg(message)
    if logger:
        logger.warning(message)
    else:
        logout('WARN', message)


def error(message):
    message = split_msg(message)
    if logger:
        logger.error(message)
    else:
        logout('ERROR', message)


def critical(message):
    message = split_msg(message)
    if logger:
        logger.critical(message)
    else:
        logout('CRITICAL', message)

