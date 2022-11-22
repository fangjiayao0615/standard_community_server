# -*- coding:utf-8 -*-
"""
平滑上线要求：
1、nginx配置文件使用两份conf,
    一份指向本地/app/nginx/conf/vhost/community_server.conf.local，
    一份指向其他服务器，/app/nginx/conf/vhost/community_server.conf.remote
2、nginx加载使用的conf由软连接生成conf，重启supervisor前指向conf.remote，重启supervisor后指向conf.local

增加服务器方法：
1、修改服务器列表
2、修改任务表
3、新增每台server部署方法
4、修改总部署方法
"""

import datetime
import json

import requests
import os
from fabric.api import *
# from fabric import env
# env.hosts = ['user1@host1:port1', 'user2@host2.port2']
# env.passwords = {'user1@host1:port1': 'password1', 'user2@host2.port2': 'password2'}

project = 'community_server'
project_home = '/app/%s' % project

# ------------ 服务器列表 ------------
server01 = 'root@101.200.169.22'
# server02 = 'server02'

# ------------ 总部署方法 ------------


def deploy_main():
    """
    串行顺序上线
    :return:
    """
    # TODO: GIT拉取master分支
    # msg_prefix = 'Gitlab-CD (由 %s 触发, Git Ref: %s):' % (
    #     os.environ.get('GITLAB_USER_NAME', ''), os.environ.get('CI_COMMIT_REF_NAME', '')
    # )
    # fab_call_dingding(msg_prefix + ' behoo-server 自动上线发车')

    # 压缩代码
    local("tar --exclude=.git -czf /tmp/%s.gz ." % project)

    # 分组，组内并行，组间串行
    execute(deploy_process, hosts=[server01])

    local("rm -f /tmp/%s.gz" % project)

    # TODO 上线通知
    # fab_call_dingding(msg_prefix + ' behoo-server 自动上线完毕')


def install_python_dependencies():
    # host重启任务
    # sudo('pip3 install pyaes==1.6.1')
    # sudo('type npm && npm install qrcode.react || true')
    pass


@parallel
def deploy_process():
    """
    执行部署代码流程
    :return:
    """

    # host更新代码版本
    with cd(project_home):

        # 上传代码
        put("/tmp/%s.gz" % project, project_home)
        # 解压文件
        run('mkdir -p %s' % project)
        run('tar -xzf %s.gz -C %s' % (project, project))
        run('rm -f %s.gz' % project)

        # 更新版本名
        date = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        new_name = project + "-" + date
        run('mv %s %s ' % (project, new_name))

        # 指向最新版本
        new_release = run('ls | grep "%s-" | tail -1f' % project)
        run('ln -snf %s bin' % new_release)
        run('chmod -R 777 bin')

        # with cd('bin/web/front_ssr'):
        #     # 无条件链过来；除 web 外其他服务器不用
        #     run('ln -sf ../../../node_modules .')
        # with cd('bin/web/pc'):
        #     # 无条件链过来；除 web 外其他服务器不用
        #     run('ln -sf ../../../pc/node_modules .')

        # 只保留最近的7个版本
        all_releases = run('ls | grep "%s-"' % project).split()
        current_releases = run('ls | grep "%s-" | tail -7f' % project).split()
        for rel in all_releases:
            if rel and rel not in current_releases:
                run('rm -fr %s ' % rel)

    # TODO 切换 nginx 指向至其他server
    # if reload_nginx:
    # with cd('/app/nginx/conf/vhost'):
    #     run('ln -s -n -f community_server.conf.remote community_server.conf')
    #     run('/app/nginx/sbin/nginx -s reload')
    #     run('sleep 1')  # 等待已有请求处理完毕

    # host重启任务
    run('supervisorctl -c /etc/supervisor/supervisord.conf stop %s:*' % project)
    run('supervisorctl -c /etc/supervisor/supervisord.conf update')
    run('supervisorctl -c /etc/supervisor/supervisord.conf start %s:*' % project)

    # TODO 切回 nginx 指向本机
    # if reload_nginx:
    #     with cd('/app/nginx/conf/vhost'):
    #         run('ln -s -n -f community_server.conf.local community_server.conf')
    #         run('/app/nginx/sbin/nginx -s reload')


# def rollbehoo():
#     """
#     回滚代码
#     :return:
#     """
#     with cd('/app/web/behoo_server'):
#         lastrelease = run('ls -rtd behoo_server* |tail -2 |head -1')
#         run('unlink bin')
#         run('ln -sn %s bin' % lastrelease)
#
#     run('supervisorctl -c /app/supervisor/conf/server.conf restart all')


# def fab_call_dingding(content):
#     """
#     发送钉钉通知
#     :param content:
#     :return:
#     """
#     if len(content) > 4096:
#         content = content[:4096]
#     msg = {
#         "msgtype": "text",
#         "text": {
#             "content": content
#         },
#     }
#     data = json.dumps(msg, ensure_ascii=True)
#     requests.post(
#         'https://oapi.dingtalk.com/robot/send?access_token=aaa...',
#         data=data, headers={'Content-Type': 'application/json'},
#         timeout=10)

if __name__ == '__main__':
    deploy_main()
