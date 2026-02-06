# -*- coding: utf-8 -*-

import datetime
import subprocess
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from cryptography.x509.oid import NameOID

from . import globalvars
from .logutil import command, error, info, warning


class CertificateManager:
    @staticmethod
    def generate_private_key(bits: int):
        return rsa.generate_private_key(public_exponent=65537, key_size=bits)

    @staticmethod
    def generate_ca(private_key):
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Los Angles"),
                x509.NameAttribute(
                    NameOID.ORGANIZATION_NAME, "Netease Login Helper CA"
                ),
                x509.NameAttribute(
                    NameOID.ORGANIZATIONAL_UNIT_NAME, "Netease Login Helper CA"
                ),
                x509.NameAttribute(NameOID.COMMON_NAME, "Netease Login Helper CA"),
            ]
        )
        return (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.UTC))
            .not_valid_after(
                datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)
            )
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .sign(private_key, hashes.SHA256())
        )

    @staticmethod
    def generate_cert(hostnames: list[str], private_key, ca_cert, ca_key):
        tmp_names = [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Los Angeles"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Netease Login Helper"),
            x509.NameAttribute(
                NameOID.ORGANIZATIONAL_UNIT_NAME, "Netease Login Helper"
            ),
        ]
        tmp_names += [x509.NameAttribute(NameOID.COMMON_NAME, i) for i in hostnames]

        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(x509.Name(tmp_names))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(i) for i in hostnames]),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )

        # send the csr to CA
        return (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(ca_cert.subject)
            .public_key(csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.UTC))
            .not_valid_after(
                datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)
            )
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(i) for i in hostnames]),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256())
        )

    @staticmethod
    def import_to_root(cert_path):
        try:
            if sys.platform.startswith("win32"):
                command("certutil -addstore Root " + cert_path)
                subprocess.check_call(["certutil", "-addstore", "Root", cert_path])

            elif sys.platform.startswith("darwin"):
                command(
                    "sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "
                    + cert_path
                )
                subprocess.check_call(
                    [
                        "sudo",
                        "security",
                        "add-trusted-cert",
                        "-d",
                        "-r",
                        "trustRoot",
                        "-k",
                        "/Library/Keychains/System.keychain",
                        cert_path,
                    ]
                )

            else:
                command(
                    "sudo cp "
                    + cert_path
                    + " "
                    + str(globalvars.system_cert_linux_path)
                )
                subprocess.check_call(
                    ["sudo", "cp", cert_path, str(globalvars.system_cert_linux_path)]
                )
                command("sudo update-ca-certificates")
                proc_1 = subprocess.run(["sudo", "update-ca-certificates"])
                if proc_1.returncode != 0:
                    warning(
                        "'update-ca-certificates' failed; trying 'update-ca-trust'..."
                    )
                    command("sudo update-ca-trust")
                    proc_2 = subprocess.run(["sudo", "update-ca-trust"])
                    if proc_2.returncode != 0:
                        error("'update-ca-trust' failed")
                        raise subprocess.CalledProcessError(1, "")

        except subprocess.CalledProcessError:
            error("could not import certificate to root")
            info("please manually import the certificate and press Enter...")
            input()

    @staticmethod
    def export_key(path, key):
        try:
            with open(path, "wb") as f:
                f.write(
                    key.private_bytes(
                        Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
                    )
                )
        except:
            error("could not export key")
            sys.exit(1)

    @staticmethod
    def export_cert(path, cert):
        try:
            with open(path, "wb") as f:
                f.write(cert.public_bytes(Encoding.PEM))
        except:
            error("could not export certificate")
            sys.exit(1)
