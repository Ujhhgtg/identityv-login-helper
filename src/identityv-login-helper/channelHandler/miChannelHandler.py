# -*- coding: utf-8 -*-

import base64
import json
import time

from .. import channelmgr, globalvars
from ..channelHandler.miLogin.miChannel import MiLogin
from ..logutil import error, info


class MiChannel(channelmgr.Channel):
    def __init__(
        self,
        login_info: dict,
        user_info: dict = {},
        ext_info: dict = {},
        device_info: dict = {},
        create_time: int = int(time.time()),
        last_login_time: int = 0,
        name: str = "",
        oauth_data: dict = {},
        game_id: str = "",
    ) -> None:
        super().__init__(
            login_info,
            user_info,
            ext_info,
            device_info,
            create_time,
            last_login_time,
            name,
        )
        self.oAuthData = oauth_data
        info(f"created new miChannel with name {self.name} and oauthData {oauth_data}")
        self.crossGames = False
        # To DO: Use Actions to auto update game_id-app_id mapping by uploading an APK.
        # this is a temporary solution for IDV
        self.miLogin = MiLogin("2882303761517637640", self.oAuthData)
        self.game_id = game_id
        self.uniBody = None
        self.uniData = None

    def _request_user_login(self):
        self.miLogin.web_login()
        self.oAuthData = self.miLogin.oauthData
        print(self.oAuthData)
        return self.oAuthData != None

    def _get_session(self):
        try:
            data = self.miLogin.init_account_data()
        except Exception as e:
            error(f"Failed to get session data {e}")
            self.oAuthData = None
            return None
        self.last_login_time = int(time.time())
        return data

    def is_token_valid(self):
        if self.oAuthData is None:
            info(f"Token is invalid for {self.name}")
            return False
        return True

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            login_info=data.get("login_info", {}),
            user_info=data.get("user_info", {}),
            ext_info=data.get("ext_info", {}),
            device_info=data.get("device_info", {}),
            create_time=data.get("create_time", int(time.time())),
            last_login_time=data.get("last_login_time", 0),
            name=data.get("name", ""),
            oauth_data=data.get("oAuthData", None),
            game_id=data.get("game_id", ""),
        )

    def _build_extra_unisdk_data(self) -> str:
        res = {
            "SAUTH_STR": "",
            "SAUTH_JSON": "",
            "extra_data": "",
            "realname": "",
            "get_access_token": "1",
        }
        extra = json.dumps({"adv_channel": "0", "adid": "0"})
        realname = json.dumps({"realname_type": 0, "age": 18})
        json_data = {
            "extra_data": extra,
            "get_access_token": "1",
            "sdk_udid": self.oAuthData["uuid"],
            "realname": realname,
        }
        json_data.update(self.uniBody)

        str_data = json_data.copy()
        str_data.update({"username": self.uniSDKJSON["username"]})
        str_data = "&".join([f"{k}={v}" for k, v in str_data.items()])

        res["SAUTH_STR"] = base64.b64encode(str_data.encode()).decode()
        res["SAUTH_JSON"] = base64.b64encode(json.dumps(json_data).encode()).decode()
        res["extra_data"] = extra
        res["realname"] = realname
        return json.dumps(res)

    def get_unisdk_data(self):
        info(f"Get unisdk data for {self.name}")
        import channelUtils

        if not self.is_token_valid():
            self._request_user_login()
        channel_data = self._get_session()
        if channel_data is None:
            error(f"Failed to get session data for {self.name}")
            return False
        self.uniBody = channelUtils.build_sauth(
            "xiaomi_app",
            "xiaomi_app",
            str(channel_data["appAccountId"]),
            channel_data["session"],
        )
        fd = globalvars.fake_device
        self.uniData = channelUtils.post_signed_data(self.uniBody)
        info(f"Get unisdk data for {self.uniData}")
        self.uniSDKJSON = json.loads(
            base64.b64decode(self.uniData["unisdk_login_json"]).decode()
        )
        res = {
            "user_id": self.oAuthData["uuid"],
            "token": base64.b64encode(channel_data["session"].encode()).decode(),
            "login_channel": "xiaomi_app",
            "udid": fd["udid"],
            "app_channel": "xiaomi_app",
            "sdk_version": "3.0.5.002",
            "jf_game_id": self.game_id,  # maybe works for all games
            "pay_channel": "xiaomi_app",
            "extra_data": "",
            "extra_unisdk_data": self._build_extra_unisdk_data(),
            "gv": "157",
            "gvn": "1.5.80",
            "cv": "a1.5.0",
        }
        return res
