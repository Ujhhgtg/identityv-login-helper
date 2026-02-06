# -*- coding: utf-8 -*-

import json
import socket
import sys

import dns.resolver
import psutil
import requests
from flask import Flask, Response, jsonify, request
from gevent import pywsgi

from . import const, globalvars
from .logutil import debug, error, info, warning

app = Flask(__name__)

login_methods = [
    {
        "name": "手机账号",
        "icon_url": "",
        "text_color": "",
        "hot": True,
        "type": 7,
        "icon_url_large": "",
    },
    {
        "name": "快速游戏",
        "icon_url": "",
        "text_color": "",
        "hot": True,
        "type": 2,
        "icon_url_large": "",
    },
    {
        "login_url": "",
        "name": "网易邮箱",
        "icon_url": "",
        "text_color": "",
        "hot": True,
        "type": 1,
        "icon_url_large": "",
    },
    {
        "login_url": "",
        "name": "扫码登录",
        "icon_url": "",
        "text_color": "",
        "hot": True,
        "type": 17,
        "icon_url_large": "",
    },
]
pcInfo = {
    "extra_unisdk_data": "",
    "from_game_id": "h55",
    "src_app_channel": "netease",
    "src_client_ip": "",
    "src_client_type": 1,
    "src_jf_game_id": "h55",
    "src_pay_channel": "netease",
    "src_sdk_version": "3.15.0",
    "src_udid": "",
}

g_req = requests.session()
g_req.trust_env = False


def request_get_as_cv(request, cv):
    query = request.args.copy()
    if cv:
        query["cv"] = cv
    resp = g_req.request(
        method=request.method,
        url=globalvars.uri_remote_ip + request.path,
        params=query,
        headers=request.headers,
        cookies=request.cookies,
        allow_redirects=False,
        verify=False,
    )
    excluded_headers = [
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    ]
    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]
    return Response(resp.text, resp.status_code, headers)


def proxy(request):
    query = request.args.copy()
    new_body = request.get_data(as_text=True)
    # 向目标服务发送代理请求
    resp = requests.request(
        method=request.method,
        url=globalvars.uri_remote_ip + request.path,
        params=query,
        headers=request.headers,
        data=new_body,
        cookies=request.cookies,
        allow_redirects=False,
        verify=False,
    )
    app.logger.info(resp.url)
    # 构造代理响应
    excluded_headers = [
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    ]
    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    response = Response(resp.content, resp.status_code, headers)
    return response


def request_post_as_cv(request, cv):
    query = request.args.copy()
    if cv:
        query["cv"] = cv
    try:
        new_body = request.get_json()
        new_body["cv"] = cv
        new_body.pop("arch", None)
    except:
        new_body = dict(x.split("=") for x in request.get_data(as_text=True).split("&"))
        new_body["cv"] = cv
        new_body.pop("arch", None)
        new_body = "&".join([f"{k}={v}" for k, v in new_body.items()])

    app.logger.info(new_body)
    resp = g_req.request(
        method=request.method,
        url=globalvars.uri_remote_ip + request.path,
        params=query,
        data=new_body,
        headers=request.headers,
        cookies=request.cookies,
        allow_redirects=False,
        verify=False,
    )
    excluded_headers = [
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    ]
    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]
    return Response(resp.text, resp.status_code, headers)


@app.route("/mpay/games/<game_id>/login_methods", methods=["GET"])
def handle_login_methods(game_id):
    try:
        resp: Response = request_get_as_cv(request, "i4.7.0")
        new_login_methods = resp.get_json()
        new_login_methods["entrance"] = [(login_methods)]
        new_login_methods["select_platform"] = True
        new_login_methods["qrcode_select_platform"] = True
        for i in new_login_methods["config"]:
            new_login_methods["config"][i]["select_platforms"] = [0, 1, 2, 3, 4]
        resp.set_data(json.dumps(new_login_methods))
        return resp
    except:
        return proxy(request)


@app.route("/mpay/api/users/login/mobile/finish", methods=["POST"])
@app.route("/mpay/api/users/login/mobile/get_sms", methods=["POST"])
@app.route("/mpay/api/users/login/mobile/verify_sms", methods=["POST"])
@app.route("/mpay/games/<game_id>/devices/<device_id>/users", methods=["POST"])
def handle_first_login(game_id=None, device_id=None):
    try:
        return request_post_as_cv(request, "i4.7.0")
    except:
        return proxy(request)


@app.route("/mpay/games/<game_id>/devices/<device_id>/users/<user_id>", methods=["GET"])
def handle_login(game_id, device_id, user_id):
    try:
        resp: Response = request_get_as_cv(request, "i4.7.0")
        new_devices = resp.get_json()
        new_devices["user"]["pc_ext_info"] = pcInfo
        resp.set_data(json.dumps(new_devices))
        return resp
    except:
        return proxy(request)


@app.route("/mpay/games/pc_config", methods=["GET"])
def handle_pc_config():
    try:
        resp: Response = request_get_as_cv(request, "i4.7.0")
        new_config = resp.get_json()
        new_config["game"]["config"]["cv_review_status"] = 1
        resp.set_data(json.dumps(new_config))
        return resp
    except:
        return proxy(request)


@app.route("/mpay/api/qrcode/create_login", methods=["GET"])
def handle_create_login():
    try:
        resp: Response = proxy(request)
        channel_account = ""
        data = {"uuid": resp.get_json()["uuid"], "game_id": request.args["game_id"]}
        cached_qrcode_data = data
        pending_login_info = None
        new_config = resp.get_json()
        new_config["qrcode_scanners"][0]["url"] = (
            "https://localhost/_idv-login/index?game_id=" + request.args["game_id"]
        )
        return jsonify(new_config)
    except:
        return proxy(request)


@app.route("/_idv-login/mannualChannels", methods=["GET"])
def _manual_list():
    return jsonify(const.manual_login_channels)


@app.route("/_idv-login/list", methods=["GET"])
def _list_channels():
    try:
        body = globalvars.channels_manager.list_channels()
    except Exception as e:
        body = {"error": str(e)}
    return jsonify(body)


@app.route("/_idv-login/switch", methods=["GET"])
def _switch_channel():
    channel_account = request.args["uuid"]
    if globalvars.cached_qrcode_data:
        data = globalvars.cached_qrcode_data
        globalvars.channels_manager.simulate_scan(
            request.args["uuid"], data["uuid"], data["game_id"]
        )
    return {"current": channel_account}


@app.route("/_idv-login/del", methods=["GET"])
def _del_channel():
    resp = {"success": globalvars.channels_manager.delete(request.args["uuid"])}
    return jsonify(resp)


@app.route("/_idv-login/rename", methods=["GET"])
def _rename_channel():
    resp = {
        "success": globalvars.channels_manager.rename(
            request.args["uuid"], request.args["new_name"]
        )
    }
    return jsonify(resp)


@app.route("/_idv-login/import", methods=["GET"])
def _import_channel():
    resp = {
        "success": globalvars.channels_manager.manual_import(request.args["channel"])
    }
    return jsonify(resp)


@app.route("/_idv-login/index", methods=["GET"])
def _handle_switch_page():
    return Response(const.html)


@app.route("/mpay/api/qrcode/query", methods=["GET"])
def handle_qrcode_query():
    if globalvars.channel_account:
        return proxy(request)
    else:
        resp: Response = proxy(request)
        qr_code_status = resp.get_json()["qrcode"]["status"]
        if qr_code_status == 2 and globalvars.channel_account == "":
            globalvars.pending_login_info = resp.get_json()["login_info"]
        return resp


@app.route("/mpay/api/users/login/qrcode/exchange_token", methods=["POST"])
def handle_token_exchange():
    if globalvars.channel_account:
        info("logging in to " + globalvars.channel_account)
        return proxy(request)
    else:
        info("got channel login token")
        resp: Response = proxy(request)
        if resp.status_code == 200:
            if globalvars.pending_login_info:
                globalvars.channels_manager.import_from_scan(
                    globalvars.pending_login_info, resp.get_json()
                )
        return resp


@app.route("/mpay/api/qrcode/<path>", methods=["POST"])
@app.route("/mpay/api/reverify/<path>")
@app.route("/mpay/api/qrcode/<path>", methods=["GET"])
def handle_qrcode(path):
    info(f"UNCHANGED {request.url}")
    return proxy(request)


@app.route("/<path:path>", methods=["GET", "POST"])
def globalProxy(path):
    if request.method == "GET":
        return request_get_as_cv(request, "i4.7.0")
    else:
        return request_post_as_cv(request, "i4.7.0")


@app.before_request
def before_request_func():
    if request.method == "POST":
        debug(
            f"request: {request.method} {request.path} {request.args} {request.get_data(as_text=True)}"
        )
    else:
        debug(f"request: {request.method} {request.path} {request.args}")


@app.after_request
def after_request_func(response):
    if request.content_type == "application/json":
        debug(f"response: {response.status} {response.headers} {response.get_json()}")
    return response


class ProxyManager:
    @staticmethod
    def ensure_port_not_in_use() -> None:
        if ProxyManager.check_port_in_use(443):
            error(
                "port 443 is in use; please quit any program using the port and re-run the script"
            )
            sys.exit(1)

    @staticmethod
    def check_port_in_use(port: int) -> bool:
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return True
        return False

    @staticmethod
    def run():
        try:
            dns_answers = dns.resolver.resolve(globalvars.domain_target)
        except:
            dns_answers = []

        if len(dns_answers) == 0:
            warning("could not resolve target address; will use hardcoded value")
            target = "42.186.193.21"
        else:
            info("resolved target address")
            target = dns_answers[0].address

        globalvars.uri_remote_ip = f"https://{target}"
        info("target address: " + globalvars.uri_remote_ip)
        ProxyManager.ensure_port_not_in_use()
        server = pywsgi.WSGIServer(
            listener=("127.0.0.1", 443),
            certfile=str(globalvars.webcert_path),
            keyfile=str(globalvars.webkey_path),
            application=app,
        )

        if socket.gethostbyname(globalvars.domain_target) == "127.0.0.1":
            info("proxy server started!")
            info("you can now launch the game")
            info("DO NOT quit the server until you LOGIN INTO the game")
            server.serve_forever()
            return True
        else:
            error("proxy does not seem to work")
            error("you can still launch the game and check if it works")
            server.serve_forever()
            return False
