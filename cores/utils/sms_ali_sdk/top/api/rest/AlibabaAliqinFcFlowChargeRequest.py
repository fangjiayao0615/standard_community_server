'''
Created by auto_sdk on 2016.03.30
'''
from cores.utils.sms_ali_sdk.top.api.base import RestApi
class AlibabaAliqinFcFlowChargeRequest(RestApi):
    def __init__(self,domain='gw.api.taobao.com',port=80):
        RestApi.__init__(self,domain, port)
        self.grade = None
        self.out_recharge_id = None
        self.phone_num = None
        self.reason = None

    def getapiname(self):
        return 'alibaba.aliqin.fc.flow.charge'
