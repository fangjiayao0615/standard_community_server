# coding=utf-8
"""
基础 handler、功能单一 handler
"""
from cores.const import const_err
from server_audit.handler.audit_base_handler import AuditBaseHandler
from cores.post import post_service


class AdminPostCreateHandler(AuditBaseHandler):
    """
    管理员创建帖子
    """
    _label = 'AdminPostCreateHandler'

    @AuditBaseHandler.check_permission()
    async def post(self):

        uid = self.params['uid']
        post_type = self.params['ptype']
        text = self.params.get('text', '').strip()
        title = self.params.get('title', '').strip()
        raw_imgs = self.params.get('raw_imgs', [])
        tids = self.params.get('tids', [])[:3]
        raw_articles = self.params.get('raw_articles', [])

        # 创建帖子
        pid, new_post = await post_service.create_new_post(
            uid, text, post_type, raw_imgs=raw_imgs, tids=tids,
            raw_articles=raw_articles, title=title)

        # 返回创建的帖子信息
        post_info = await post_service.get_post_detail_for_handler(pid, uid)

        ret = {'ret': const_err.CODE_SUCCESS, 'data': post_info, 'msg': ''}
        self.jsonify(ret)

