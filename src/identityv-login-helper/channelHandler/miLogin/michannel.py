import hashlib
import json
import os
import random
import string
import time
import webbrowser
from urllib.parse import parse_qs, urlparse

import pyperclip as cb
import requests
from faker import Faker

from ...logutil import error
from . import utils
from .const import AES_KEY, DEVICE, DEVICE_RECORD


def generate_fake_data():
    fake = Faker()
    manufacturers = ["Samsung", "Huawei", "Xiaomi", "OPPO"]
    architectures = ["32", "64"]

    manufacturer = random.choice(manufacturers)
    model = fake.lexify(text="SM-????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    os_version = fake.lexify(
        text="??_stable_??", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )
    build_id = fake.lexify(
        text="V???IR release-keys", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )
    architecture = random.choice(architectures)
    return f"{manufacturer}|{model}|{os_version}|{build_id}|{architecture}|{model}"


def generate_md5(input_string):
    md5_hash = hashlib.md5()
    md5_hash.update(input_string.encode("utf-8"))
    return md5_hash.hexdigest()


class MiLogin:
    def __init__(self, app_id, oauth_data=None):
        self.appId = app_id
        self.oauthData = oauth_data
        if os.path.exists(DEVICE_RECORD):
            with open(DEVICE_RECORD, "r") as f:
                self.device = json.load(f)
        else:
            self.device = MiLogin.make_fake_device()
            with open(DEVICE_RECORD, "w") as f:
                json.dump(self.device, f)

    def init_account_data(self) -> object:
        if self.oauthData is None:
            self.web_login()
        params = {
            "fuid": self.oauthData["uuid"],  # 用户ID
            "devAppId": self.appId,  # apk中的appid
            "toke": self.oauthData["st"],
        }
        params.update(self.device)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "close",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; M2102K1AC Build/V417IR)",
            "Host": "account.migc.g.mi.com",
            "Accept-Encoding": "gzip",
        }
        response = requests.post(
            "http://account.migc.g.mi.com/migc-sdk-account/getLoginAppAccount_v2",
            data=utils.generate_unsign_request(params, AES_KEY),
            headers=headers,
        )
        res = utils.decrypt_response(response.text, AES_KEY)
        if res["retCode"] == 200:
            return res
        else:
            error(res)
            raise Exception("Init account data failed")

    def get_st_by_code(self, code) -> None:
        print(code + "called")
        params = {
            "accountType": 4,
            "code": code,
            "isSaveSt": "true",
            "appid": "2000202",
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "close",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; M2102K1AC Build/V417IR)",
            "Host": "account.migc.g.mi.com",
            "Accept-Encoding": "gzip",
        }
        response = requests.get(
            "http://account.migc.g.mi.com/misdk/v2/oauth",
            params=utils.generate_unsign_request(params, AES_KEY),
            headers=headers,
        )
        res = utils.decrypt_response(response.text, AES_KEY)
        if res["code"] == 0:
            self.oauthData = res
            return res
        else:
            error(res)
            raise Exception("Get ST failed")

    @staticmethod
    def clip_listener(callback):
        while True:
            if cb.paste() != "":
                current_url = cb.paste()

            def parse_url_query(url):
                parsed_url = urlparse(url)
                query_dict = parse_qs(parsed_url.query)
                return query_dict

            if "code" in parse_url_query(current_url).keys():
                code = parse_url_query(current_url)["code"][0]
                callback(code)
                break
            else:
                print("Not logged in yet, waiting for redirect...")
            time.sleep(1)

    def web_login(self):
        # app = QApplication(sys.argv)
        login_url = f"http://account.xiaomi.com/oauth2/authorize?client_id=2882303761517516898&response_type=code&scope=1%203&redirect_uri=http%3A%2F%2Fgame.xiaomi.com%2Foauthcallback%2Fmioauth&state={generate_md5(str(time.time()))[0:16]}"
        # browser_window = BrowserWindow(login_url, self.getSTbyCode)
        # browser_window.show()
        webbrowser.open(login_url)
        return MiLogin.clip_listener(self.get_st_by_code)

    @staticmethod
    def make_fake_device():
        device = DEVICE.copy()
        device["imei"] = utils.aes_encrypt(
            "".join(random.choices(string.ascii_letters + string.digits, k=8)),
            str(time.time())[0:16],
        )[0:8]
        device["imeiMd5"] = generate_md5(device["imei"])
        device["ua"] = generate_fake_data()
        return device
