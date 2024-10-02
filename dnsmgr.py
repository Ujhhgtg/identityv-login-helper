# coding=UTF-8
"""
 Copyright (c) 2024 Alexander-Porter & fwilliamhe

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see <https://www.gnu.org/licenses/>.
 """

import random
import requests
import socket

from logutil import info

# Resource Record Types
A = 1
AAAA = 28

# DNS status codes
NOERROR = 0

UNRESERVED_CHARS = (
    "abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789-._~"
)


class InvalidHostName(Exception):
    pass


class SimulatedDNS(object):

    def __init__(self):
        self.hostname_to_ip = {}

    def get_host_by_name(self, hostname):
        """mimic functionality of socket.gethostbyname"""
        if hostname in self.hostname_to_ip:
            info(f"[SimulatedDNS] resolved {hostname} to {self.hostname_to_ip[hostname]}")
            return self.hostname_to_ip[hostname]

        try:
            ip = socket.gethostbyname(hostname)
            self.hostname_to_ip[hostname] = ip
            info(f"[SimulatedDNS] resolved {hostname} to {ip}")
            return ip
        except socket.gaierror:
            return None


class SecureDNS(object):
    def __init__(
        self,
        query_type=1,
        cd=False,
        edns_client_subnet="0.0.0.0/0",
        random_padding=True,
    ):
        self.url = "https://dns.pub/dns-query"
        self.params = {
            "type": query_type,
            "cd": cd,
            "edns_client_subnet": edns_client_subnet,
            "random_padding": random_padding,
        }
        info(f"[SecureDNS] dns server address is {self.url}")

    def get_host_by_name(self, hostname):
        """mimic functionality of socket.gethostbyname"""
        answers = self.resolve(hostname)
        if answers is not None:
            info(f"resolved {hostname} to {answers[0]}")
            return answers[0]
        return None

    def resolve(self, hostname):
        """return ip address(es) of hostname"""
        hostname = SecureDNS.prepare_hostname(hostname)
        self.params.update({"name": hostname})

        if self.params["random_padding"]:
            padding = SecureDNS.generate_padding()
            self.params.update({"random_padding": padding})

        # Disable proxy for resolving DNS
        s = requests.session()
        s.trust_env = False

        r = s.get(self.url, params=self.params, proxies=None, timeout=3)
        if r.status_code == 200:
            response = r.json()

            if response["Status"] == NOERROR:
                answers = []
                for answer in response["Answer"]:
                    name, response_type, ttl, data = map(
                        answer.get, ("name", "type", "ttl", "data")
                    )
                    if response_type in (A, AAAA):
                        answers.append(data)
                if answers == []:
                    return None
                return answers
        return None

    @staticmethod
    def prepare_hostname(hostname):
        """verify the hostname is well-formed"""
        hostname = hostname.rstrip(".")  # strip trailing dot if present

        if not (1 <= len(hostname) <= 253):  # test length of hostname
            raise InvalidHostName

        for label in hostname.split("."):  # test length of each label
            if not (1 <= len(label) <= 63):
                raise InvalidHostName
        try:
            return hostname.encode("ascii")
        except UnicodeEncodeError:
            raise InvalidHostName

    @staticmethod
    def generate_padding():
        """generate a pad using unreserved chars"""
        pad_len = random.randint(10, 50)
        return "".join(random.choice(UNRESERVED_CHARS) for _ in range(pad_len))
