# coding=utf-8
"""
web 相关 handler
"""
from server_app.handler.base_handler import BaseHandler


class WebEntryHandler(BaseHandler):
    """
    PC
    """
    _label = 'WebEntryHandler'

    async def get(self):
        try:
            user_agent = self.request.headers["User-Agent"]
        except:
            user_agent = ''
        # device = DeviceDetector(user_agent).parse()

        # if device.device_type() == 'desktop':
        #     context = {}
        #     return self.html_response('index.html', False, **context)
        # else:
        #     context = {}
        #     return self.html_response('index.html', True, **context)

        context = {}
        return self.html_response('index.html', False, **context)

