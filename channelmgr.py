# -*- coding: utf-8 -*-

import json
import random
import time

import requests

import globalvars
from const import manual_login_channels
from logutil import info, error


class Channel:
    def __init__(
        self,
        login_info: dict,
        user_info: dict = {},
        ext_info: dict = {},
        device_info: dict = {},
        create_time: int = int(time.time()),
        last_login_time: int = 0,
        name: str = "",
    ) -> None:
        self.login_info = login_info
        self.user_info = user_info
        self.ext_info = ext_info
        self.device_info = device_info
        self.exchange_data = {
            "device": device_info,
            "ext_info": ext_info,
            "user": user_info,
        }

        self.create_time = create_time
        self.last_login_time = last_login_time
        self.uuid = f"{login_info['login_channel']}-{login_info['code']}"
        self.channel_name = login_info["login_channel"]
        self.crossGames = True
        if name == "":
            self.name = self.uuid
        else:
            self.name = name

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
        )

    def get_unisdk_data(self):
        return {
            "user_id": self.user_info["id"],
            "token": self.user_info["token"],
            "login_channel": self.ext_info["src_app_channel2"],
            "udid": self.ext_info["src_udid"],
            "app_channel": self.ext_info["src_app_channel"],
            "sdk_version": self.ext_info["src_jf_game_id"],
            "jf_game_id": self.ext_info["src_jf_game_id"],
            "pay_channel": self.ext_info["src_pay_channel"],
            "extra_data": "",
            "extra_unisdk_data": self.ext_info["extra_unisdk_data"],
            "gv": "157",
            "gvn": "1.5.80",
            "cv": "a1.5.0",
        }

    def get_non_sensitive_data(self):
        return {
            "create_time": self.create_time,
            "last_login_time": self.last_login_time,
            "uuid": self.uuid,
            "name": self.name,
        }


class ChannelManager:
    def __init__(self):
        self.channels = []
        from channelHandler.miChannelHandler import MiChannel

        if globalvars.channels_path.is_file():
            with globalvars.channels_path.open("r") as f:
                try:
                    data = json.load(f)
                    info("resolved channel login info")
                    for item in data:
                        if "login_info" in item.keys():
                            channel_name = item["login_info"]["login_channel"]
                            if channel_name == "xiaomi_app":
                                tmp_channel: MiChannel = MiChannel.from_dict(item)
                                # if tmp_channel.is_token_valid():
                                self.channels.append(tmp_channel)
                                # else:
                                #    self.logger.error(f"渠道服登录信息失效: {tmp_channel.name}")
                            else:
                                self.channels.append(Channel.from_dict(item))
                except ValueError:
                    f.close()
                    with globalvars.channels_path.open("w") as f:
                        json.dump([], f)

        else:
            with globalvars.channels_path.open("w") as f:
                json.dump([], f)
            self.channels = []

    def save_records(self):
        with globalvars.channels_path.open("w") as file:
            old_data = [channel.__dict__.copy() for channel in self.channels]
            data = old_data.copy()
            for channel_data in data:
                to_be_deleted = []
                for key in channel_data.keys():
                    mini_data = {"data": channel_data[key]}
                    try:
                        json.dumps(mini_data)
                    except:
                        error(f"deleted unsavable data: {channel_data}-{key}")
                        to_be_deleted.append(key)
                for key in to_be_deleted:
                    del channel_data[key]
            json.dump(data, file)
        info("updated channel login info")

    def list_channels(self, game_id: str):
        return sorted(
            [channel.get_non_sensitive_data()  for channel in self.channels if channel.crossGame or (channel.game_id == game_id)],
            key=lambda x: x["last_login_time"],
            reverse=True,
        )

    def import_from_scan(self, login_info: dict, exchange_info: dict):
        tmp_channel: Channel = Channel(
            login_info,
            exchange_info["user"],
            exchange_info["ext_info"] if "ext_info" in exchange_info.keys() else {},
            exchange_info["device"] if "device" in exchange_info.keys() else {},
        )
        if login_info["login_channel"] in [i["channel"] for i in manual_login_channels]:
            error(f"channel not supported due to qrcode login: {login_info['login_channel']}")
            return False
        self.channels.append(tmp_channel)
        self.save_records()

    def manual_import(self, channel_name: str, game_id: str):
        tmp_data = {
            "code": str(random.randint(100000, 999999)),
            "src_client_type": 1,
            "login_channel": channel_name,
            "src_client_country_code": "CN",
        }
        if channel_name == "xiaomi_app":
            from channelHandler.miChannelHandler import MiChannel

            tmp_channel: MiChannel = MiChannel(tmp_data, game_id=game_id)
        try:
            tmp_channel._request_user_login()
            if tmp_channel.is_token_valid():
                self.channels.append(tmp_channel)
                self.save_records()
                return True
            else:
                error(f"could not manually import: {tmp_channel.name}")
                return False
        except:
            error(f"could not manually import")
            return False

    def login(self, uuid: str):
        for channel in self.channels:
            if channel.uuid == uuid:
                data = channel.login()
                self.save_records()
                return data
        return False

    def rename(self, uuid: str, new_name: str):
        for channel in self.channels:
            if channel.uuid == uuid:
                channel.name = new_name
                self.save_records()
                return True
        return False

    def delete(self, uuid: str):
        for i, channel in enumerate(self.channels):
            if channel.uuid == uuid:
                del self.channels[i]
                self.save_records()
                return True
        return False

    def build_query_res(self, uuid: str):
        for channel in self.channels:
            if channel.uuid == uuid:
                data = channel.login_info
                return data
        return None

    @staticmethod
    def simulate_confirm(channel: Channel, scanner_uuid: str, game_id: str):
        channel_data = channel.get_unisdk_data()
        if not channel_data:
            globalvars.channel_account = ""
            return False
        channel_data["uuid"] = scanner_uuid
        channel_data["game_id"] = game_id
        body = "&".join([f"{k}={v}" for k, v in channel_data.items()])
        r = requests.post(
            "https://service.mkey.163.com/mpay/api/qrcode/confirm_login",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            verify=False,
        )
        info(f"simulated response: {r.json()}")
        if r.status_code == 200:
            channel.last_login_time = int(time.time())
            return r.json()
        else:
            globalvars.channel_account = ""
            return False

    def simulate_scan(self, uuid: str, scanner_uuid: str, game_id: str):
        for channel in self.channels:
            if channel.uuid == uuid:
                data = {
                    "uuid": scanner_uuid,
                    "login_channel": channel.channel_name,
                    "app_channel": channel.channel_name,
                    "pay_channel": channel.channel_name,
                    "game_id": game_id,
                    "gv": "157",
                    "gvn": "1.5.80",
                    "cv": "a1.5.0",
                }
                try:
                    r = requests.get(
                        "https://service.mkey.163.com/mpay/api/qrcode/scan",
                        params=data,
                        verify=False,
                    )
                    info(f"simulated qrcode login request: {r.json()}")
                    if r.status_code == 200:
                        return ChannelManager.simulate_confirm(channel, scanner_uuid, game_id)
                    else:
                        globalvars.channel_account = ""
                        return False
                except:
                    error(f"could not simulate qrcode login request")
                    globalvars.channel_account = ""
                    return False
        return None
