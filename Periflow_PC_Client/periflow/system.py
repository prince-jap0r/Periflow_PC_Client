from __future__ import annotations

import ctypes
import socket
import subprocess
import sys
from dataclasses import dataclass

APP_FIREWALL_RULE_PREFIX = "Periflow PC Client"


@dataclass(slots=True)
class FirewallRuleResult:
    success: bool
    message: str
    changed: bool = False


def is_running_as_admin() -> bool:
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def get_local_ipv4_addresses() -> list[str]:
    addresses: set[str] = set()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            candidate = probe.getsockname()[0]
            if candidate and not candidate.startswith("127."):
                addresses.add(candidate)
    except OSError:
        pass

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM):
            candidate = info[4][0]
            if candidate and not candidate.startswith("127."):
                addresses.add(candidate)
    except OSError:
        pass

    if not addresses:
        return ["127.0.0.1"]

    def sort_key(value: str) -> tuple[int, str]:
        if value.startswith("192.168."):
            return (0, value)
        if value.startswith("10."):
            return (1, value)
        if value.startswith("172."):
            return (2, value)
        return (3, value)

    return sorted(addresses, key=sort_key)


def resolve_preferred_local_ip() -> str:
    return get_local_ipv4_addresses()[0]


def ensure_firewall_rules(tcp_port: int, udp_port: int) -> FirewallRuleResult:
    if sys.platform != "win32":
        return FirewallRuleResult(success=False, changed=False, message="Firewall automation is only supported on Windows.")
    if not is_running_as_admin():
        return FirewallRuleResult(
            success=False,
            changed=False,
            message="Run Periflow as Administrator to add Windows Firewall rules automatically.",
        )

    rules = [
        (f"{APP_FIREWALL_RULE_PREFIX} TCP", "TCP", tcp_port),
        (f"{APP_FIREWALL_RULE_PREFIX} UDP Audio", "UDP", udp_port),
    ]

    try:
        for rule_name, protocol, port in rules:
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}"],
                check=False,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                [
                    "netsh",
                    "advfirewall",
                    "firewall",
                    "add",
                    "rule",
                    f"name={rule_name}",
                    "dir=in",
                    "action=allow",
                    f"protocol={protocol}",
                    f"localport={port}",
                    "profile=private",
                    "enable=yes",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "Unknown firewall error").strip()
                return FirewallRuleResult(success=False, changed=False, message=detail)
    except OSError as exc:
        return FirewallRuleResult(success=False, changed=False, message=str(exc))

    return FirewallRuleResult(
        success=True,
        changed=True,
        message=f"Windows Firewall now allows TCP {tcp_port} and UDP {udp_port} on private networks.",
    )
