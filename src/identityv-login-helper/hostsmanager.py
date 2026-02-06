# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from pathlib import Path

from python_hosts import Hosts, HostsEntry

from . import globalvars
from .logutil import command, error, warning


class HostsManager:
    def __init__(self) -> None:
        if sys.platform.startswith("win32"):
            hosts_file_path: Path = globalvars.hosts_file_windows_path
        else:
            hosts_file_path: Path = globalvars.hosts_file_macos_linux_path

        if not hosts_file_path.is_file():
            warning("hosts file does not exist; creating...")

            try:
                hosts_file_path.open("w").close()
            except:
                error("could not create hosts file")
                sys.exit(1)

        if not os.access(str(hosts_file_path), os.W_OK):
            error("hosts file is not writeable")
            sys.exit(1)

        try:
            self.hosts = Hosts()
        except IOError:
            error("could not open hosts file")
            sys.exit(1)

    def add(self, name: str, ip: str) -> None:
        self.hosts.add([HostsEntry(entry_type="ipv4", address=ip, names=[name])])
        self.hosts.write()

        if sys.platform.startswith("win32"):
            command("ipconfig /flushdns")
            subprocess.run(["ipconfig", "/flushdns"])

    def remove(self, name: str) -> None:
        self.hosts.remove_all_matching(name=name)
        self.hosts.write()

        if sys.platform.startswith("win32"):
            command("ipconfig /flushdns")
            subprocess.run(["ipconfig", "/flushdns"])

    def exists(self, name: str) -> bool:
        return self.hosts.exists(names=[name])
