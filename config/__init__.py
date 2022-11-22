# -*- coding:utf-8 -*-
import os

"""
环境变量
- 生产环境 production
- 开发环境 development (默认)
"""
ENV = os.environ.get('COMMUNITY_ENV', 'development')
print('ENV: %s' % ENV)
exec("from config import %s as config" % ENV)

# 此条件只为了解决IDE的错误提示，不影响实际代码效果
if ENV == 'development':
    from config import development as config
