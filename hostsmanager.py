# -*- coding: utf-8 -*-

import subprocess
from pathlib import Path

from logutil import warning, error, command
from python_hosts import Hosts, HostsEntry

import os
import sys

from globalvars import hosts_file_windows_path, hosts_file_macos_linux_path


class HostsManager:
    def __init__(self) -> None:
        if sys.platform.startswith("win32"):
            hosts_file_path: Path = hosts_file_windows_path
        else:
            hosts_file_path: Path = hosts_file_macos_linux_path

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
            subprocess.run(['ipconfig', '/flushdns'])

    def remove(self, name: str) -> None:
        self.hosts.remove_all_matching(name=name)
        self.hosts.write()

        if sys.platform.startswith("win32"):
            command("ipconfig /flushdns")
            subprocess.run(['ipconfig', '/flushdns'])
    
    def exists(self, name: str) -> bool :
        return self.hosts.exists(names=[name])
