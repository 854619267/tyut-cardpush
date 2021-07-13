import datetime

import requests

r = requests.Session()


class common:
    def __init__(self, stucode) -> None:
        self.stucode = stucode

    def login_by_cookies(self, cookies):
        cookie_dict = {}
        name, value = cookies.strip(" ").split("=", 1)
        cookie_dict[name] = value
        cookiesjar = requests.utils.cookiejar_from_dict(
            cookie_dict, cookiejar=None, overwrite=True)
        r.cookies = cookiesjar

    def login_by_stucode(self, password):
        r.get("http://202.207.245.234:9090/1001.json?stucode={}&stupsw={}".format(
            self.stucode, password)).json()

    def is_login(self):
        res = r.get(
            "http://202.207.245.234:9090/0002.json?stucode={}".format(self.stucode)).json()
        return res["resultCode"] == "0000"

    def get_cookies(self):
        ret = r.cookies.get_dict()
        cookies = ""
        for key, value in ret.items():
            cookies += "{}={}".format(key, value)
        return cookies

    def get_balance(self):
        res = r.get(
            "http://202.207.245.234:9090/0002.json?stucode={}".format(self.stucode)).json()
        return res["value"][0]["balance"]

    def get_history(self):
        today = (datetime.datetime.utcnow() +
                 datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
        yesterday = (datetime.datetime.utcnow() +
                     datetime.timedelta(days=-1, hours=8)).strftime("%Y-%m-%d")
        res = r.get(
            "http://202.207.245.234:9090/0005.json?stucode={}&startdate={}&enddate={}".format(self.stucode, yesterday, today)).json()
        if res["resultCode"] == "0000":
            self.history = res["value"]

    def diff_history(self, timestr):
        """
        timestr : %Y-%m-%d %H:%M:%S
        return : time_local,body
        """
        self.get_history()
        body = []
        if timestr:
            time_local = datetime.datetime.strptime(
                timestr, '%Y-%m-%d %H:%M:%S')
        else:
            time_local = datetime.datetime.utcnow() + datetime.timedelta(hours=8, seconds=1)
        for i in self.history[::-1]:
            time_remote = datetime.datetime.strptime(
                i["ConsumeTime"], '%Y-%m-%d %H:%M:%S')
            if time_local <= time_remote:
                body.append(i)
                time_local = time_remote + datetime.timedelta(seconds=1)
        return time_local.strftime("%Y-%m-%d %H:%M:%S"), body
