import json
from time import sleep

import requests
from tencentcloud.common import credential
from tencentcloud.scf.v20180416 import scf_client

import common


class scf:

    def __init__(self, context) -> None:
        self.function_name = context["function_name"]
        self.region = context["tencentcloud_region"]
        self.environment = eval(context["environment"])
        self.environment.pop("SCF_NAMESPACE")

        self.secret_id = self.environment.get("secret_id", None)
        self.secret_key = self.environment.get("secret_key", None)
        self.stucode = self.environment.get("stucode", None)
        self.password = self.environment.get("password", None)
        self.cookies = self.environment.get("cookies", None)
        self.is_failure = self.environment.get("is_failure", None)
        self.last_timestrip = self.environment.get("last_timestrip", None)
        self.dingding_token = self.environment.get("dingding_token", None)

        if self.secret_id and self.secret_key and self.stucode and self.password and self.dingding_token:
            cred = credential.Credential(self.secret_id, self.secret_key)
            self.client = scf_client.ScfClient(cred, self.region)
        else:
            raise ValueError("环境变量设置不全")

    def do(self):
        self.action = common.common(self.stucode)
        if self.cookies:
            self.action.login_by_cookies(self.cookies)
        if self.action.is_login():
            self.run_tasks()
        else:
            self.action.login_by_stucode(self.password)
            self.change_env("cookies", self.action.get_cookies())
            if self.action.is_login():
                self.run_tasks()
            else:
                self.notification_push("错误:账号或密码无效")
                self.change_env("is_failure", 1)

    def change_env(self, key, value):
        self.environment.update({key: value})

    def update_env(self):
        enviro = []
        for key, value in self.environment.items():
            enviro.append({"Key": key, "Value": value})
        enviro = {"Variables": enviro}
        action = "UpdateFunctionConfiguration"
        action_params = {
            "FunctionName": self.function_name,
            "Environment": enviro
        }
        self.client.call(action, action_params)

    def run_tasks(self):
        try:
            if not self.last_timestrip:
                self.notification_push(
                    "你好🦆！\n当你看到这条通知时，程序应该可以正常运行了\n欢迎反馈与建议：https://github.com/bla58351/tyut-cardpush")
            timestrip, body = self.action.diff_history(self.last_timestrip)
            if body:
                str = self.make_notification_str(body)
                self.notification_push(str)
            self.change_env("last_timestrip", timestrip)
        except Exception as e:
            self.notification_push("签到发生错误:{}".format(e))
            self.change_env("is_failure", 1)

    def make_notification_str(self, body):
        str = "交易提醒\n\n"
        for i in body:
            str += "时间：{}\n地点：{}-{}\n{}：{}元\n\n".format(
                i["ConsumeTime"][11:], i["Area"], i["TradeBranchName"], i["GeneralOperateTypeName"], i["ConsumeAmount"][1:])
        str += "当前余额：{}元".format(self.action.get_balance())
        return str

    def notification_push(self, text=None):
        header = {
            "Content-Type": "application/json"
        }
        data = {
            "msgtype": "text",
            "text": {
                "content": "[tyut]\n" + text
            }
        }
        requests.post("https://oapi.dingtalk.com/robot/send?access_token={}".format(
            self.dingding_token), data=json.dumps(data), headers=header)


def main(event, context):
    tasks = scf(context)
    if not tasks.is_failure:
        tasks.do()
        tasks.update_env()
