#!/usr/bin/python
# -*- coding: utf-8 -*-

from gevent import monkey
# monkey-patch earlier
monkey.patch_all()

import ctypes
import json
import os
import random
import string
import sys

import requests
import requests.packages

import globalvars
from certificatemanager import CertificateManager
from channelmgr import ChannelManager
from hostsmanager import HostsManager
from logutil import error, info, warning
from proxymanager import ProxyManager


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except AttributeError:
        return os.geteuid() == 0

def main() -> None:
    if not is_admin():
        if sys.platform.startswith("win32"):
            error("not running with administrator privileges; trying to re-elevate...")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
        elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            error("not running with root privileges; please run this script with sudo or doas")
        else:
            error("permission not enough")

        return

    globalvars.working_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(str(globalvars.working_dir))
    info("working directory changed to " + str(globalvars.working_dir))

    host_mgr: HostsManager = HostsManager()
    globalvars.channels_manager = ChannelManager()

    requests.packages.urllib3.disable_warnings()

    if not globalvars.fake_device_path.is_file():
        udid = "".join(random.choices(string.hexdigits, k=16))
        _fake_device = {
            "device_model": "M2102K1AC",
            "os_name": "android",
            "os_ver": "12",
            "udid": udid,
            "app_ver": "157",
            "imei": "".join(random.choices(string.digits, k=15)),
            "country_code": "CN",
            "is_emulator": 0,
            "is_root": 0,
            "oaid": "",
        }
        with globalvars.fake_device_path.open("w") as f:
            json.dump(_fake_device, f)
    else:
        with globalvars.fake_device_path.open("r") as f:
            _fake_device = json.load(f)

    globalvars.fake_device = _fake_device

    if not globalvars.config_path.is_file():
        with globalvars.config_path.open("w") as f:
            json.dump({}, f)
            globalvars.config = {}
    else:
        with globalvars.config_path.open("r") as f:
            globalvars.config = json.load(f)

    if not globalvars.webcert_path.is_file() or not globalvars.webkey_path.is_file():
        warning("could not find webserver certificate or key; generating new...")

        ca_key = CertificateManager.generate_private_key(bits=2048)
        ca_cert = CertificateManager.generate_ca(ca_key)
        CertificateManager.export_cert(str(globalvars.cacert_path), ca_cert)

        srv_key = CertificateManager.generate_private_key(bits=2048)
        srv_cert = CertificateManager.generate_cert(
            [globalvars.domain_target, "localhost"], srv_key, ca_cert, ca_key
        )

        CertificateManager.import_to_root(str(globalvars.cacert_path))

        CertificateManager.export_cert(str(globalvars.webcert_path), srv_cert)
        CertificateManager.export_key(str(globalvars.webkey_path), srv_key)

        info("webserver certificate and key generated")

    if host_mgr.exists(globalvars.domain_target):
        host_mgr.remove(globalvars.domain_target)
    host_mgr.add(globalvars.domain_target, "127.0.0.1")
    info("proxy server added to hosts file")

    info("starting proxy server...")
    try:
        ProxyManager.run()
    except KeyboardInterrupt:
        warning("received Ctrl-C; quitting...")
        host_mgr.remove(globalvars.domain_target)
        info("proxy server stopped")

if __name__ == "__main__":
    main()