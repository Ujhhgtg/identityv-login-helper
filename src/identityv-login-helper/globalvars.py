import os
import sys
from pathlib import Path

domain_target: str = "service.mkey.163.com"

working_dir: Path = None

webcert_path: Path = None
fake_device_path: Path = None
webkey_path: Path = None
cacert_path: Path = None
channels_path: Path = None
system_cert_linux_path: Path = Path(
    "/usr/share/ca-certificates/idv_login_helper_cert.pem"
)
hosts_file_windows_path: Path = Path("C:\\Windows\\System32\\drivers\\etc\\hosts")
hosts_file_macos_linux_path: Path = Path("/etc/hosts")

channel_account: str = ""
cached_qrcode_data: dict = {}
pending_login_info = None
uri_remote_ip: str = ""

channels_manager = None
fake_device: str = ""

DEBUG: bool = False


def set_paths() -> None:
    global \
        working_dir, \
        webcert_path, \
        fake_device_path, \
        webkey_path, \
        cacert_path, \
        channels_path

    if sys.platform.startswith("win32"):
        working_dir = Path.home() / ".config" / "identityv-login-helper"
    elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
        sudo_user: str = os.environ.get("SUDO_USER")
        if sudo_user != "":
            working_dir = (
                Path("/home") / sudo_user / ".config" / "identityv-login-helper"
            )
        else:
            error("cannot detect sudo user; falling back to root user directory")
            working_dir = Path.home() / ".config" / "identityv-login-helper"

    webcert_path = working_dir / "domain_cert_2.pem"
    fake_device_path = working_dir / "fakeDevice.json"
    webkey_path = working_dir / "domain_key_2.pem"
    cacert_path = working_dir / "root_ca.pem"
    channels_path = working_dir / "channels.json"
