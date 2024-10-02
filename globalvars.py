from pathlib import Path

from channelmgr import ChannelManager

domain_target: str = "service.mkey.163.com"

working_dir: Path = Path.home() / ".config" / "identityv-login-helper"

webcert_path: Path = working_dir / "domain_cert_2.pem"
config_path: Path = working_dir / "config.json"
fake_device_path: Path = working_dir / "fakeDevice.json"
webkey_path: Path = working_dir / "domain_key_2.pem"
cacert_path: Path = working_dir / "root_ca.pem"
channels_path: Path = working_dir / "channels.json"
system_cert_linux_path: Path = Path("/usr/share/ca-certificates/idv_login_helper_cert.pem")
hosts_file_windows_path: Path = Path("C:\\Windows\\System32\\drivers\\etc\\hosts")
hosts_file_macos_linux_path: Path = Path("/etc/hosts")

channel_account: str = ""
cached_qrcode_data: dict = {}
pending_login_info = None
uri_remoteip = ""

channels_manager: ChannelManager = ChannelManager()
fake_device: str = ""
config: dict = None