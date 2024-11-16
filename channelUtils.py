import hashlib
import hmac
import json
import random
import string

import requests

import globalvars

LOG_KEY="SvShWXDcmogbZJoU3YWe3Su3Ci-mCRcw"

def _get_my_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except Exception as e:
        return "127.0.0.1"

def get_sign_src(str1, str2, str3):
    str4 = ""
    replaced = str2.replace("://", "")
    if replaced.find("/") != -1:
        str4 = replaced[replaced.find("/"):]
    return str1.upper() + str4 + str3

def calc_sign(url, method, data):
    src=get_sign_src(method,url,data)
    #sha256
    key=LOG_KEY
    return hmac.new(key.encode(), src.encode(), hashlib.sha256).hexdigest()

def build_sauth(login_channel, app_channel, uid, session):
    fake_data = globalvars.fake_device
    ip=_get_my_ip()
    data = {
        "gameid": "h55",# maybe works for all games
        "login_channel": login_channel,
        "app_channel": app_channel,
        "platform": "ad",
        "sdkuid": uid,
        "udid": fake_data["udid"],
        "sessionid": session,
        "sdk_version": "3.3.0.7",
        "is_unisdk_guest": 0,
        "ip": ip,
        "aim_info": '{"tz":"+0800","tzid":"Asia\/Shanghai","aim":"'+ip+'","country":"CN"}',
        "source_app_channel": app_channel,
        "source_platform": "ad",
        "client_login_sn": "".join(random.choices((string.hexdigits), k=16)),
        "step": "".join(random.choices(string.digits, k=10)),
        "step2": "".join(random.choices(string.digits, k=9)),
        "hostid": 0,
        "sdklog": json.dumps(fake_data),
    }
    return data


def post_signed_data(data):
    url="https://mgbsdk.matrix.netease.com/h55/sdk/uni_sauth"
    method="POST"
    headers={"X-Client-Sign":calc_sign(url, method, json.dumps(data)),
             "Content-Type":"application/json",
             "User-Agent":"Dalvik/2.1.0 (Linux; U; Android 12; M2102K1AC Build/V417IR)",}
    r=requests.post(url,data=json.dumps(data),headers=headers)
    return r.json()